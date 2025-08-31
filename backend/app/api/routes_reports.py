"""Risk reporting API routes."""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, TokenData
from app.db.models import Report
from app.db.session import get_db

router = APIRouter()


class ReportResponse(BaseModel):
    id: int
    account_id: str
    as_of_date: datetime
    report_type: str
    title: str | None
    summary_text: str | None
    generated_by: str | None
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/reports", response_model=List[ReportResponse])
async def get_reports(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get list of generated reports."""
    stmt = (
        select(Report)
        .where(Report.account_id == current_user.account_id)
        .order_by(Report.created_at.desc())
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    reports = result.scalars().all()
    
    return [ReportResponse.model_validate(report) for report in reports]


@router.get("/reports/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get specific report by ID."""
    stmt = select(Report).where(
        Report.id == report_id,
        Report.account_id == current_user.account_id
    )
    
    result = await db.execute(stmt)
    report = result.scalar_one_or_none()
    
    if not report:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Report not found")
    
    return ReportResponse.model_validate(report)



