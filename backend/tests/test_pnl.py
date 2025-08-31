"""Tests for P&L calculation services."""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, Instrument, Position, Price
from app.services.pnl import PnlService


@pytest.fixture
async def db_session():
    """Create test database session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=True)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    AsyncTestSession = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with AsyncTestSession() as session:
        yield session
    
    await engine.dispose()


@pytest.fixture
async def sample_instrument(db_session):
    """Create a sample instrument for testing."""
    instrument = Instrument(
        symbol="AAPL",
        name="Apple Inc.",
        asset_class="equity",
        currency="USD",
        exchange="NASDAQ"
    )
    db_session.add(instrument)
    await db_session.commit()
    await db_session.refresh(instrument)
    return instrument


@pytest.fixture
async def sample_position(db_session, sample_instrument):
    """Create a sample position for testing."""
    position = Position(
        instrument_id=sample_instrument.id,
        account_id="test_account",
        quantity=Decimal("100"),
        average_cost=Decimal("150.00")
    )
    db_session.add(position)
    await db_session.commit()
    await db_session.refresh(position)
    return position


class TestPnlService:
    """Test cases for PnL service."""
    
    async def test_calculate_position_pnl_with_price(self, db_session, sample_position):
        """Test P&L calculation with provided price."""
        pnl_service = PnlService(db_session)
        
        # Test with higher price (profit)
        current_price = Decimal("160.00")
        unrealized, realized = await pnl_service.calculate_position_pnl(
            sample_position, current_price
        )
        
        expected_unrealized = (current_price - sample_position.average_cost) * sample_position.quantity
        assert unrealized == expected_unrealized
        assert unrealized == Decimal("1000.00")  # (160 - 150) * 100
        assert realized == Decimal("0")  # No realized P&L in this simple case
    
    async def test_calculate_position_pnl_with_loss(self, db_session, sample_position):
        """Test P&L calculation with loss."""
        pnl_service = PnlService(db_session)
        
        # Test with lower price (loss)
        current_price = Decimal("140.00")
        unrealized, realized = await pnl_service.calculate_position_pnl(
            sample_position, current_price
        )
        
        expected_unrealized = (current_price - sample_position.average_cost) * sample_position.quantity
        assert unrealized == expected_unrealized
        assert unrealized == Decimal("-1000.00")  # (140 - 150) * 100
    
    async def test_calculate_position_pnl_no_price(self, db_session, sample_position, sample_instrument):
        """Test P&L calculation when no current price provided."""
        # Add a price record
        price = Price(
            instrument_id=sample_instrument.id,
            timestamp=datetime.utcnow(),
            price=Decimal("155.00")
        )
        db_session.add(price)
        await db_session.commit()
        
        pnl_service = PnlService(db_session)
        unrealized, realized = await pnl_service.calculate_position_pnl(sample_position)
        
        expected_unrealized = (Decimal("155.00") - sample_position.average_cost) * sample_position.quantity
        assert unrealized == expected_unrealized
        assert unrealized == Decimal("500.00")  # (155 - 150) * 100
    
    async def test_calculate_portfolio_pnl(self, db_session, sample_position, sample_instrument):
        """Test portfolio-level P&L calculation."""
        # Add price for market value calculation
        price = Price(
            instrument_id=sample_instrument.id,
            timestamp=datetime.utcnow(),
            price=Decimal("155.00")
        )
        db_session.add(price)
        await db_session.commit()
        
        pnl_service = PnlService(db_session)
        pnl_data = await pnl_service.calculate_portfolio_pnl("test_account")
        
        assert pnl_data['unrealized_pnl'] == Decimal("500.00")
        assert pnl_data['realized_pnl'] == Decimal("0")
        assert pnl_data['total_pnl'] == Decimal("500.00")
        assert pnl_data['portfolio_value'] == Decimal("15500.00")  # 155 * 100


# file: backend/tests/test_var.py

