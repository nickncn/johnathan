"""SQLAlchemy database models."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    DECIMAL,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()


class Instrument(Base):
    """Trading instrument model."""
    
    __tablename__ = "instruments"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    asset_class = Column(String(50), nullable=False)  # equity, crypto, fx, etc.
    currency = Column(String(10), nullable=False)
    exchange = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    prices = relationship("Price", back_populates="instrument")
    trades = relationship("Trade", back_populates="instrument")
    positions = relationship("Position", back_populates="instrument")


class Price(Base):
    """Price data model."""
    
    __tablename__ = "prices"
    
    id = Column(Integer, primary_key=True, index=True)
    instrument_id = Column(Integer, ForeignKey("instruments.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    price = Column(DECIMAL(20, 8), nullable=False)
    volume = Column(DECIMAL(20, 8), default=0)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    instrument = relationship("Instrument", back_populates="prices")
    
    # Composite index for efficient queries
    __table_args__ = (
        Index("ix_prices_instrument_timestamp", "instrument_id", "timestamp"),
    )


class Trade(Base):
    """Trade execution model."""
    
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    instrument_id = Column(Integer, ForeignKey("instruments.id"), nullable=False)
    account_id = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    side = Column(String(10), nullable=False)  # buy, sell
    quantity = Column(DECIMAL(20, 8), nullable=False)
    price = Column(DECIMAL(20, 8), nullable=False)
    fees = Column(DECIMAL(20, 8), default=0)
    trade_id = Column(String(100), unique=True)  # External trade ID
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    instrument = relationship("Instrument", back_populates="trades")


class Position(Base):
    """Current position model."""
    
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    instrument_id = Column(Integer, ForeignKey("instruments.id"), nullable=False)
    account_id = Column(String(50), nullable=False, index=True)
    quantity = Column(DECIMAL(20, 8), nullable=False)
    average_cost = Column(DECIMAL(20, 8), nullable=False)
    market_value = Column(DECIMAL(20, 8), default=0)
    unrealized_pnl = Column(DECIMAL(20, 8), default=0)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    instrument = relationship("Instrument", back_populates="positions")
    
    # Unique constraint on instrument and account
    __table_args__ = (
        Index("ix_positions_account_instrument", "account_id", "instrument_id", unique=True),
    )


class PnlTimeSeries(Base):
    """Daily P&L timeseries model."""
    
    __tablename__ = "pnl_timeseries"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(String(50), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    unrealized_pnl = Column(DECIMAL(20, 8), default=0)
    realized_pnl = Column(DECIMAL(20, 8), default=0)
    total_pnl = Column(DECIMAL(20, 8), default=0)
    portfolio_value = Column(DECIMAL(20, 8), default=0)
    created_at = Column(DateTime, default=func.now())
    
    # Composite index for efficient queries
    __table_args__ = (
        Index("ix_pnl_account_date", "account_id", "date", unique=True),
    )


class RiskMetrics(Base):
    """Risk metrics model."""
    
    __tablename__ = "risk_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(String(50), nullable=False, index=True)
    as_of_date = Column(DateTime, nullable=False, index=True)
    var_historical = Column(DECIMAL(20, 8))
    var_parametric = Column(DECIMAL(20, 8))
    var_alpha = Column(DECIMAL(5, 4), default=0.99)
    var_lookback_days = Column(Integer, default=250)
    portfolio_volatility = Column(DECIMAL(10, 6))
    max_drawdown = Column(DECIMAL(20, 8))
    sharpe_ratio = Column(DECIMAL(10, 6))
    largest_position_pct = Column(DECIMAL(5, 4))
    num_positions = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    
    # Composite index for efficient queries
    __table_args__ = (
        Index("ix_risk_metrics_account_date", "account_id", "as_of_date"),
    )


class Report(Base):
    """Risk reports model."""
    
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(String(50), nullable=False, index=True)
    as_of_date = Column(DateTime, nullable=False, index=True)
    report_type = Column(String(50), default="daily_risk")
    title = Column(String(200))
    summary_text = Column(Text)
    data_blob = Column(JSONB)  # Structured data for the report
    generated_by = Column(String(50))  # llm, system, user
    created_at = Column(DateTime, default=func.now())