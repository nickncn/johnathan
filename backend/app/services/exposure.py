"""Portfolio exposure analysis services."""

import logging
from typing import Dict, List, Optional
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Position, Instrument, Price

logger = logging.getLogger(__name__)


class ExposureService:
    """Service for portfolio exposure analysis."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_asset_class_exposure(self, account_id: str) -> List[Dict]:
        """Get exposure breakdown by asset class."""
        # Join positions with instruments to get asset class info
        stmt = select(
            Instrument.asset_class,
            func.sum(Position.quantity * Position.average_cost).label('total_exposure'),
            func.count(Position.id).label('num_positions')
        ).select_from(
            Position.__table__.join(Instrument.__table__)
        ).where(
            Position.account_id == account_id
        ).group_by(Instrument.asset_class)
        
        result = await self.db.execute(stmt)
        exposures = result.all()
        
        # Calculate total portfolio value for percentages
        total_exposure = sum(float(exp.total_exposure) for exp in exposures)
        
        return [
            {
                'asset_class': exp.asset_class,
                'exposure_value': float(exp.total_exposure),
                'exposure_percent': float(exp.total_exposure) / total_exposure * 100 if total_exposure > 0 else 0,
                'num_positions': exp.num_positions
            }
            for exp in exposures
        ]
    
    async def get_currency_exposure(self, account_id: str) -> List[Dict]:
        """Get exposure breakdown by currency."""
        stmt = select(
            Instrument.currency,
            func.sum(Position.quantity * Position.average_cost).label('total_exposure'),
            func.count(Position.id).label('num_positions')
        ).select_from(
            Position.__table__.join(Instrument.__table__)
        ).where(
            Position.account_id == account_id
        ).group_by(Instrument.currency)
        
        result = await self.db.execute(stmt)
        exposures = result.all()
        
        total_exposure = sum(float(exp.total_exposure) for exp in exposures)
        
        return [
            {
                'currency': exp.currency,
                'exposure_value': float(exp.total_exposure),
                'exposure_percent': float(exp.total_exposure) / total_exposure * 100 if total_exposure > 0 else 0,
                'num_positions': exp.num_positions
            }
            for exp in exposures
        ]
    
    async def get_position_concentration(
        self, 
        account_id: str, 
        limit: int = 10
    ) -> Dict:
        """Analyze position concentration risk."""
        # Get all positions with current market values
        stmt = select(Position, Instrument.symbol).select_from(
            Position.__table__.join(Instrument.__table__)
        ).where(Position.account_id == account_id)
        
        result = await self.db.execute(stmt)
        position_data = result.all()
        
        if not position_data:
            return {
                'largest_positions': [],
                'concentration_metrics': {
                    'largest_position_pct': 0.0,
                    'top_5_positions_pct': 0.0,
                    'top_10_positions_pct': 0.0,
                    'herfindahl_index': 0.0
                }
            }
        
        # Calculate market values and sort by size
        positions_with_mv = []
        total_portfolio_value = 0
        
        for position, symbol in position_data:
            # Get current price
            price_stmt = select(Price.price).where(
                Price.instrument_id == position.instrument_id
            ).order_by(Price.timestamp.desc()).limit(1)
            
            price_result = await self.db.execute(price_stmt)
            current_price = price_result.scalar_one_or_none()
            
            if current_price:
                market_value = float(current_price * position.quantity)
            else:
                market_value = float(position.average_cost * position.quantity)
            
            total_portfolio_value += market_value
            
            positions_with_mv.append({
                'symbol': symbol,
                'quantity': float(position.quantity),
                'market_value': market_value,
                'weight': 0.0  # Will calculate after we have total
            })
        
        # Calculate weights and sort by market value
        for pos in positions_with_mv:
            pos['weight'] = pos['market_value'] / total_portfolio_value * 100 if total_portfolio_value > 0 else 0
        
        positions_with_mv.sort(key=lambda x: x['market_value'], reverse=True)
        
        # Calculate concentration metrics
        weights = [pos['weight'] / 100 for pos in positions_with_mv]  # Convert to decimals
        
        largest_position_pct = weights[0] * 100 if weights else 0
        top_5_pct = sum(weights[:5]) * 100 if len(weights) >= 5 else sum(weights) * 100
        top_10_pct = sum(weights[:10]) * 100 if len(weights) >= 10 else sum(weights) * 100
        
        # Herfindahl-Hirschman Index (sum of squared weights)
        hhi = sum(w ** 2 for w in weights)
        
        return {
            'largest_positions': positions_with_mv[:limit],
            'concentration_metrics': {
                'largest_position_pct': largest_position_pct,
                'top_5_positions_pct': top_5_pct,
                'top_10_positions_pct': top_10_pct,
                'herfindahl_index': hhi,
                'total_positions': len(positions_with_mv),
                'portfolio_value': total_portfolio_value
            }
        }
    
    async def get_sector_exposure(self, account_id: str) -> List[Dict]:
        """Get exposure by sector (if available in instrument metadata)."""
        # This would require additional sector data in the instruments table
        # For now, return mock data based on asset classes
        asset_exposures = await self.get_asset_class_exposure(account_id)
        
        # Map asset classes to pseudo-sectors
        sector_mapping = {
            'equity': 'Technology',  # Simplified mapping
            'crypto': 'Digital Assets',
            'fx': 'Foreign Exchange',
            'commodity': 'Commodities'
        }
        
        return [
            {
                'sector': sector_mapping.get(exp['asset_class'], 'Other'),
                'exposure_value': exp['exposure_value'],
                'exposure_percent': exp['exposure_percent'],
                'num_positions': exp['num_positions']
            }
            for exp in asset_exposures
        ]
    
    async def calculate_portfolio_beta(
        self, 
        account_id: str, 
        benchmark_returns: Optional[List[float]] = None
    ) -> float:
        """Calculate portfolio beta vs benchmark."""
        # This would require historical returns data and benchmark data
        # For now, return a mock beta
        return 1.2  # Mock beta indicating 20% more volatile than market
    
    async def get_exposure_summary(self, account_id: str) -> Dict:
        """Get comprehensive exposure summary."""
        asset_class_exp = await self.get_asset_class_exposure(account_id)
        currency_exp = await self.get_currency_exposure(account_id)
        concentration = await self.get_position_concentration(account_id)
        
        return {
            'asset_class_exposure': asset_class_exp,
            'currency_exposure': currency_exp,
            'concentration_analysis': concentration,
            'portfolio_beta': await self.calculate_portfolio_beta(account_id)
        }



