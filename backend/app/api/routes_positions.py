"""Position management API routes."""

from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, TokenData
from app.db.models import Position, Instrument
from app.db.session import get_db

router = APIRouter()


class PositionResponse(BaseModel):
    id: int
    instrument_id: int
    symbol: str
    quantity: Decimal
    average_cost: Decimal
    market_value: Decimal
    unrealized_pnl: Decimal

    class Config:
        from_attributes = True


@router.get("/positions", response_model=List[PositionResponse])
async def get_positions(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get current positions for account."""
    stmt = (
        select(Position, Instrument.symbol)
        .join(Instrument)
        .where(Position.account_id == current_user.account_id)
        .where(Position.quantity != 0)
    )
    
    result = await db.execute(stmt)
    position_data = result.all()
    
    positions = []
    for position, symbol in position_data:
        positions.append(PositionResponse(
            id=position.id,
            instrument_id=position.instrument_id,
            symbol=symbol,
            quantity=position.quantity,
            average_cost=position.average_cost,
            market_value=position.market_value or Decimal('0'),
            unrealized_pnl=position.unrealized_pnl or Decimal('0')
        ))
    
    return positions



