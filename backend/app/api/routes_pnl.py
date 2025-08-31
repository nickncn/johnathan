"""P&L analysis API routes."""

from datetime import datetime, timedelta
from typing import Dict, List

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, TokenData
from app.db.session import get_db
from app.services.pnl import PnlService

router = APIRouter()


class PnlTimeSeriesResponse(BaseModel):
    date: str
    unrealized_pnl: float
    realized_pnl: float
    total_pnl: float
    portfolio_value: float


class PnlSummaryResponse(BaseModel):
    unrealized_pnl: float
    realized_pnl: float
    total_pnl: float
    portfolio_value: float


@router.get("/pnl/summary", response_model=PnlSummaryResponse)
async def get_pnl_summary(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get current P&L summary."""
    pnl_service = PnlService(db)
    pnl_data = await pnl_service.calculate_portfolio_pnl(current_user.account_id)
    
    return PnlSummaryResponse(
        unrealized_pnl=float(pnl_data['unrealized_pnl']),
        realized_pnl=float(pnl_data['realized_pnl']),
        total_pnl=float(pnl_data['total_pnl']),
        portfolio_value=float(pnl_data['portfolio_value'])
    )


@router.get("/pnl/timeseries", response_model=List[PnlTimeSeriesResponse])
async def get_pnl_timeseries(
    from_date: datetime = Query(default=None),
    to_date: datetime = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get P&L time series data."""
    if not from_date:
        from_date = datetime.utcnow() - timedelta(days=90)
    if not to_date:
        to_date = datetime.utcnow()
    
    pnl_service = PnlService(db)
    pnl_data = await pnl_service.get_pnl_timeseries(
        current_user.account_id, from_date, to_date
    )
    
    return [PnlTimeSeriesResponse(**record) for record in pnl_data]


@router.get("/pnl/contributors")
async def get_pnl_contributors(
    limit: int = Query(default=10),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get top P&L contributors by position."""
    pnl_service = PnlService(db)
    contributors = await pnl_service.get_position_contributions(
        current_user.account_id, limit
    )
    
    return {"contributors": contributors}


