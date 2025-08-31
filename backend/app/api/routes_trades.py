"""Trade execution API routes."""

from datetime import datetime
from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, TokenData
from app.db.models import Instrument, Trade
from app.db.session import get_db

router = APIRouter()


class TradeResponse(BaseModel):
    id: int
    instrument_id: int
    account_id: str
    timestamp: datetime
    side: str
    quantity: Decimal
    price: Decimal
    fees: Decimal
    trade_id: str | None

    class Config:
        from_attributes = True


class TradeCreate(BaseModel):
    instrument_id: int
    side: str  # 'buy' or 'sell'
    quantity: Decimal
    price: Decimal
    fees: Decimal = Decimal('0')
    trade_id: str | None = None
    timestamp: datetime | None = None


@router.post("/trades", response_model=TradeResponse)
async def create_trade(
    trade: TradeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Record a new trade execution."""
    # Validate instrument exists
    stmt = select(Instrument).where(Instrument.id == trade.instrument_id)
    result = await db.execute(stmt)
    instrument = result.scalar_one_or_none()
    
    if not instrument:
        raise HTTPException(status_code=404, detail="Instrument not found")
    
    if trade.side not in ['buy', 'sell']:
        raise HTTPException(status_code=400, detail="Side must be 'buy' or 'sell'")
    
    # Create trade record
    db_trade = Trade(
        instrument_id=trade.instrument_id,
        account_id=current_user.account_id,
        timestamp=trade.timestamp or datetime.utcnow(),
        side=trade.side,
        quantity=trade.quantity,
        price=trade.price,
        fees=trade.fees,
        trade_id=trade.trade_id
    )
    
    db.add(db_trade)
    await db.commit()
    await db.refresh(db_trade)
    
    # TODO: Update positions table based on this trade
    # This would involve complex position tracking logic
    
    return TradeResponse.model_validate(db_trade)


@router.get("/trades", response_model=List[TradeResponse])
async def get_trades(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
    limit: int = 100,
    skip: int = 0
):
    """Get trade history for account."""
    stmt = (
        select(Trade)
        .where(Trade.account_id == current_user.account_id)
        .order_by(Trade.timestamp.desc())
        .offset(skip)
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    trades = result.scalars().all()
    
    return [TradeResponse.model_validate(trade) for trade in trades]



