"""Tests for VaR calculation services."""

import pytest
import numpy as np
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from app.services.var import VarService
from app.services.pnl import PnlService


class TestVarService:
    """Test cases for VaR service."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return AsyncMock()
    
    @pytest.fixture
    def var_service(self, mock_db):
        """Create VaR service with mocked dependencies."""
        return VarService(mock_db)
    
    @pytest.fixture
    def sample_returns(self):
        """Sample returns data for testing."""
        # Generate sample returns with known statistical properties
        np.random.seed(42)  # For reproducible tests
        returns = np.random.normal(0.001, 0.02, 250)  # Mean=0.1%, Vol=2%
        return returns.tolist()
    
    async def test_calculate_historical_var(self, var_service, sample_returns):
        """Test Historical Simulation VaR calculation."""
        # Mock the returns series
        with patch.object(var_service.pnl_service, 'calculate_returns_series') as mock_returns:
            mock_returns.return_value = sample_returns
            
            # Mock portfolio P&L
            with patch.object(var_service.pnl_service, 'calculate_portfolio_pnl') as mock_pnl:
                mock_pnl.return_value = {'portfolio_value': Decimal('1000000')}
                
                result = await var_service.calculate_historical_var(
                    "test_account", alpha=0.99, lookback_days=250
                )
                
                assert result['method'] == 'historical_simulation'
                assert result['confidence_level'] == 0.99
                assert result['lookback_days'] == 250
                assert result['data_points'] == 250
                assert result['var_value'] > 0  # Should be positive (loss amount)
                assert 'portfolio_value' in result
    
    async def test_calculate_parametric_var(self, var_service, sample_returns):
        """Test Parametric VaR calculation."""
        with patch.object(var_service.pnl_service, 'calculate_returns_series') as mock_returns:
            mock_returns.return_value = sample_returns
            
            with patch.object(var_service.pnl_service, 'calculate_portfolio_pnl') as mock_pnl:
                mock_pnl.return_value = {'portfolio_value': Decimal('1000000')}
                
                result = await var_service.calculate_parametric_var(
                    "test_account", alpha=0.99, lookback_days=250
                )
                
                assert result['method'] == 'parametric'
                assert result['confidence_level'] == 0.99
                assert result['var_value'] > 0
                assert 'volatility' in result
                assert 'mean_return' in result
                assert 'z_score' in result
    
    async def test_insufficient_data_handling(self, var_service):
        """Test handling of insufficient data."""
        # Mock insufficient returns data
        with patch.object(var_service.pnl_service, 'calculate_returns_series') as mock_returns:
            mock_returns.return_value = [0.01, -0.02, 0.005]  # Only 3 data points
            
            result = await var_service.calculate_historical_var("test_account")
            
            assert result['var_value'] == 0.0
            assert result['data_points'] == 3
    
    async def test_var_monotonicity_property(self, var_service, sample_returns):
        """Property test: Higher confidence level should give higher VaR."""
        with patch.object(var_service.pnl_service, 'calculate_returns_series') as mock_returns:
            mock_returns.return_value = sample_returns
            
            with patch.object(var_service.pnl_service, 'calculate_portfolio_pnl') as mock_pnl:
                mock_pnl.return_value = {'portfolio_value': Decimal('1000000')}
                
                var_95 = await var_service.calculate_historical_var(
                    "test_account", alpha=0.95
                )
                var_99 = await var_service.calculate_historical_var(
                    "test_account", alpha=0.99
                )
                
                # 99% VaR should be higher than 95% VaR (more extreme loss)
                assert var_99['var_value'] >= var_95['var_value']
    
    @pytest.mark.hypothesis
    def test_var_scaling_property(self):
        """Property test: VaR should scale with portfolio size."""
        from hypothesis import given, strategies as st
        

