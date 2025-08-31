"""P&L calculation services."""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

import pandas as pd
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Position, PnlTimeSeries, Price, Trade

logger = logging.getLogger(__name__)


class PnlService:
    """Service for P&L calculations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def calculate_position_pnl(
        self, 
        position: Position, 
        current_price: Optional[Decimal] = None
    ) -> Tuple[Decimal, Decimal]:
        """
        Calculate unrealized and realized P&L for a position.
        
        Returns:
            Tuple of (unrealized_pnl, realized_pnl)
        """
        if not current_price:
            # Get latest price
            stmt = select(Price.price).where(
                Price.instrument_id == position.instrument_id
            ).order_by(Price.timestamp.desc()).limit(1)
            
            result = await self.db.execute(stmt)
            price_row = result.scalar_one_or_none()
            current_price = price_row if price_row else position.average_cost
        
        # Unrealized P&L: (current_price - avg_cost) * quantity
        unrealized_pnl = (current_price - position.average_cost) * position.quantity
        
        # For realized P&L, we'd need to track each trade execution
        # For now, return 0 as placeholder
        realized_pnl = Decimal('0')
        
        return unrealized_pnl, realized_pnl
    
    async def calculate_portfolio_pnl(
        self, 
        account_id: str, 
        as_of_date: Optional[datetime] = None
    ) -> Dict[str, Decimal]:
        """Calculate portfolio-level P&L."""
        if not as_of_date:
            as_of_date = datetime.utcnow()
        
        # Get all positions for account
        stmt = select(Position).where(Position.account_id == account_id)
        result = await self.db.execute(stmt)
        positions = result.scalars().all()
        
        total_unrealized = Decimal('0')
        total_realized = Decimal('0')
        total_market_value = Decimal('0')
        
        for position in positions:
            unrealized, realized = await self.calculate_position_pnl(position)
            total_unrealized += unrealized
            total_realized += realized
            
            # Get current price for market value
            stmt = select(Price.price).where(
                Price.instrument_id == position.instrument_id
            ).order_by(Price.timestamp.desc()).limit(1)
            
            result = await self.db.execute(stmt)
            current_price = result.scalar_one_or_none()
            if current_price:
                total_market_value += current_price * position.quantity
        
        return {
            'unrealized_pnl': total_unrealized,
            'realized_pnl': total_realized,
            'total_pnl': total_unrealized + total_realized,
            'portfolio_value': total_market_value
        }
    
    async def get_pnl_timeseries(
        self, 
        account_id: str, 
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """Get P&L time series data."""
        stmt = select(PnlTimeSeries).where(
            and_(
                PnlTimeSeries.account_id == account_id,
                PnlTimeSeries.date >= start_date,
                PnlTimeSeries.date <= end_date
            )
        ).order_by(PnlTimeSeries.date)
        
        result = await self.db.execute(stmt)
        pnl_records = result.scalars().all()
        
        return [
            {
                'date': record.date.isoformat(),
                'unrealized_pnl': float(record.unrealized_pnl or 0),
                'realized_pnl': float(record.realized_pnl or 0),
                'total_pnl': float(record.total_pnl or 0),
                'portfolio_value': float(record.portfolio_value or 0)
            }
            for record in pnl_records
        ]
    
    async def update_daily_pnl(self, account_id: str, date: datetime) -> None:
        """Update daily P&L record."""
        pnl_data = await self.calculate_portfolio_pnl(account_id, date)
        
        # Check if record exists
        stmt = select(PnlTimeSeries).where(
            and_(
                PnlTimeSeries.account_id == account_id,
                func.date(PnlTimeSeries.date) == date.date()
            )
        )
        
        result = await self.db.execute(stmt)
        existing_record = result.scalar_one_or_none()
        
        if existing_record:
            # Update existing record
            existing_record.unrealized_pnl = pnl_data['unrealized_pnl']
            existing_record.realized_pnl = pnl_data['realized_pnl']
            existing_record.total_pnl = pnl_data['total_pnl']
            existing_record.portfolio_value = pnl_data['portfolio_value']
        else:
            # Create new record
            new_record = PnlTimeSeries(
                account_id=account_id,
                date=date,
                unrealized_pnl=pnl_data['unrealized_pnl'],
                realized_pnl=pnl_data['realized_pnl'],
                total_pnl=pnl_data['total_pnl'],
                portfolio_value=pnl_data['portfolio_value']
            )
            self.db.add(new_record)
        
        await self.db.commit()
        logger.info(f"Updated daily P&L for account {account_id} on {date.date()}")
    
    async def calculate_returns_series(
        self, 
        account_id: str, 
        lookback_days: int = 250
    ) -> List[float]:
        """Calculate daily returns series for portfolio."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=lookback_days + 1)
        
        pnl_data = await self.get_pnl_timeseries(account_id, start_date, end_date)
        
        if len(pnl_data) < 2:
            return []
        
        # Convert to pandas for easier calculation
        df = pd.DataFrame(pnl_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Calculate daily returns based on portfolio value changes
        df['returns'] = df['portfolio_value'].pct_change()
        
        # Handle cases where portfolio value is 0 or negative
        returns = df['returns'].dropna().replace([float('inf'), float('-inf')], 0).tolist()
        
        return returns[-lookback_days:] if len(returns) > lookback_days else returns
    
    async def get_position_contributions(
        self, 
        account_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """Get top position contributors to P&L."""
        stmt = select(Position).where(Position.account_id == account_id).limit(limit)
        result = await self.db.execute(stmt)
        positions = result.scalars().all()
        
        contributions = []
        for position in positions:
            unrealized_pnl, _ = await self.calculate_position_pnl(position)
            
            contributions.append({
                'instrument_id': position.instrument_id,
                'symbol': position.instrument.symbol,
                'quantity': float(position.quantity),
                'unrealized_pnl': float(unrealized_pnl),
                'pnl_contribution_pct': 0.0  # Would calculate vs total portfolio
            })
        
        # Sort by absolute P&L contribution
        contributions.sort(key=lambda x: abs(x['unrealized_pnl']), reverse=True)
        
        return contributions