"""Instrument management API routes."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, TokenData
from app.db.models import Instrument
from app.db.session import get_db

router = APIRouter()


class InstrumentResponse(BaseModel):
    id: int
    symbol: str
    name: str
    asset_class: str
    currency: str
    exchange: str | None
    is_active: bool

    class Config:
        from_attributes = True


class InstrumentCreate(BaseModel):
    symbol: str
    name: str
    asset_class: str
    currency: str
    exchange: str | None = None


@router.get("/instruments", response_model=List[InstrumentResponse])
async def get_instruments(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
    limit: int = 100,
    skip: int = 0
):
    """Get list of available instruments."""
    stmt = select(Instrument).where(Instrument.is_active == True).offset(skip).limit(limit)
    result = await db.execute(stmt)
    instruments = result.scalars().all()
    
    return [InstrumentResponse.model_validate(inst) for inst in instruments]


@router.post("/instruments", response_model=InstrumentResponse)
async def create_instrument(
    instrument: InstrumentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Create a new instrument."""
    # Check if instrument already exists
    stmt = select(Instrument).where(Instrument.symbol == instrument.symbol)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail="Instrument already exists")
    
    db_instrument = Instrument(**instrument.model_dump())
    db.add(db_instrument)
    await db.commit()
    await db.refresh(db_instrument)
    
    return InstrumentResponse.model_validate(db_instrument)


@router.get("/instruments/{instrument_id}", response_model=InstrumentResponse)
async def get_instrument(
    instrument_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get specific instrument by ID."""
    stmt = select(Instrument).where(Instrument.id == instrument_id)
    result = await db.execute(stmt)
    instrument = result.scalar_one_or_none()
    
    if not instrument:
        raise HTTPException(status_code=404, detail="Instrument not found")
    
    return InstrumentResponse.model_validate(instrument)



