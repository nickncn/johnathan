"""Risk analysis API routes."""

from typing import Dict

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, TokenData
from app.core.config import get_settings
from app.db.session import get_db
from app.services.var import VarService
from app.services.exposure import ExposureService

router = APIRouter()
settings = get_settings()


class VarResponse(BaseModel):
    var_value: float
    confidence_level: float
    lookback_days: int
    method: str
    portfolio_value: float


class ExposureResponse(BaseModel):
    asset_class_exposure: list
    currency_exposure: list
    concentration_analysis: dict


@router.get("/risk/var", response_model=VarResponse)
async def calculate_var(
    alpha: float = Query(default=settings.DEFAULT_VAR_ALPHA),
    lookback: int = Query(default=settings.DEFAULT_VAR_LOOKBACK),
    method: str = Query(default="historical"),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Calculate Value at Risk for portfolio."""
    var_service = VarService(db)
    
    if method not in ['historical', 'parametric', 'ewma']:
        method = 'historical'
    
    var_result = await var_service.calculate_var(
        current_user.account_id, method, alpha, lookback
    )
    
    return VarResponse(
        var_value=var_result['var_value'],
        confidence_level=var_result['confidence_level'],
        lookback_days=var_result['lookback_days'],
        method=var_result['method'],
        portfolio_value=var_result.get('portfolio_value', 0)
    )


@router.get("/risk/exposure", response_model=ExposureResponse)
async def get_exposure_analysis(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get portfolio exposure analysis."""
    exposure_service = ExposureService(db)
    exposure_data = await exposure_service.get_exposure_summary(current_user.account_id)
    
    return ExposureResponse(
        asset_class_exposure=exposure_data['asset_class_exposure'],
        currency_exposure=exposure_data['currency_exposure'],
        concentration_analysis=exposure_data['concentration_analysis']
    )


@router.get("/risk/metrics")
async def get_risk_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get comprehensive risk metrics."""
    var_service = VarService(db)
    exposure_service = ExposureService(db)
    
    # Calculate multiple VaR measures
    var_historical = await var_service.calculate_historical_var(current_user.account_id)
    var_parametric = await var_service.calculate_parametric_var(current_user.account_id)
    var_change = await var_service.get_var_change(current_user.account_id)
    
    # Get exposure metrics
    concentration = await exposure_service.get_position_concentration(current_user.account_id)
    
    return {
        "var_metrics": {
            "historical": var_historical,
            "parametric": var_parametric,
            "change": var_change
        },
        "concentration_metrics": concentration['concentration_metrics'],
        "alert_triggered": var_historical['var_value'] > settings.VAR_ALERT_THRESHOLD
    }



