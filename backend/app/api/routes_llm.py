"""LLM-powered analysis API routes."""

from datetime import datetime
from typing import Dict

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, TokenData
from app.core.config import get_settings
from app.db.models import Report
from app.db.session import get_db
from app.services.llm import LlmService

router = APIRouter()
settings = get_settings()


class SummaryRequest(BaseModel):
    alpha: float = settings.DEFAULT_VAR_ALPHA
    lookback_days: int = settings.DEFAULT_VAR_LOOKBACK
    horizon_days: int = 1
    save_report: bool = True


class SummaryResponse(BaseModel):
    summary: str
    account_id: str
    generated_at: str
    parameters: dict
    report_id: int | None = None


@router.post("/llm/summary", response_model=SummaryResponse)
async def generate_risk_summary(
    request: SummaryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Generate AI-powered risk summary."""
    llm_service = LlmService(db)
    
    # Generate summary
    summary_result = await llm_service.generate_risk_summary(
        current_user.account_id,
        request.alpha,
        request.lookback_days,
        request.horizon_days
    )
    
    report_id = None
    
    # Save as report if requested
    if request.save_report:
        report = Report(
            account_id=current_user.account_id,
            as_of_date=datetime.utcnow(),
            report_type="llm_risk_summary",
            title=f"AI Risk Analysis - {datetime.utcnow().strftime('%Y-%m-%d')}",
            summary_text=summary_result['summary'],
            data_blob=summary_result.get('parameters', {}),
            generated_by="llm"
        )
        
        db.add(report)
        await db.commit()
        await db.refresh(report)
        report_id = report.id
    
    return SummaryResponse(
        summary=summary_result['summary'],
        account_id=summary_result['account_id'],
        generated_at=summary_result['generated_at'],
        parameters=summary_result.get('parameters', {}),
        report_id=report_id
    )


@router.get("/llm/explain-var")
async def explain_var_change(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get LLM explanation of recent VaR changes."""
    llm_service = LlmService(db)
    
    # This would be a more focused prompt about VaR changes
    summary = await llm_service.generate_risk_summary(current_user.account_id)
    
    return {
        "explanation": summary['summary'],
        "focus": "var_analysis",
        "generated_at": summary['generated_at']
    }


