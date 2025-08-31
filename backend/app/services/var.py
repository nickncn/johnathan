"""Value at Risk (VaR) calculation services."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import RiskMetrics
from app.services.pnl import PnlService

logger = logging.getLogger(__name__)


class VarService:
    """Service for VaR calculations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.pnl_service = PnlService(db)
    
    async def calculate_historical_var(
        self, 
        account_id: str,
        alpha: float = 0.99,
        lookback_days: int = 250
    ) -> Dict[str, float]:
        """
        Calculate Historical Simulation VaR.
        
        Args:
            account_id: Account identifier
            alpha: Confidence level (e.g., 0.99 for 99% VaR)
            lookback_days: Number of days to look back
            
        Returns:
            Dictionary with VaR value and metadata
        """
        # Get returns series
        returns = await self.pnl_service.calculate_returns_series(
            account_id, lookback_days
        )
        
        if len(returns) < 30:  # Minimum data requirement
            logger.warning(f"Insufficient data for VaR calculation: {len(returns)} returns")
            return {
                'var_value': 0.0,
                'confidence_level': alpha,
                'lookback_days': lookback_days,
                'method': 'historical_simulation',
                'data_points': len(returns)
            }
        
        # Convert to numpy array
        returns_array = np.array(returns)
        
        # Calculate percentile (VaR is the α percentile of the loss distribution)
        # For losses, we want the left tail, so we use (1 - alpha) percentile
        var_percentile = (1 - alpha) * 100
        var_value = np.percentile(returns_array, var_percentile)
        
        # Convert to dollar terms (assuming current portfolio value)
        current_pnl = await self.pnl_service.calculate_portfolio_pnl(account_id)
        portfolio_value = float(current_pnl.get('portfolio_value', 0))
        var_dollar = abs(var_value * portfolio_value)
        
        return {
            'var_value': var_dollar,
            'var_percent': var_value,
            'confidence_level': alpha,
            'lookback_days': lookback_days,
            'method': 'historical_simulation',
            'data_points': len(returns),
            'portfolio_value': portfolio_value
        }
    
    async def calculate_parametric_var(
        self, 
        account_id: str,
        alpha: float = 0.99,
        lookback_days: int = 250
    ) -> Dict[str, float]:
        """
        Calculate Parametric (Normal) VaR.
        
        Assumes returns are normally distributed.
        VaR = z_α * σ * portfolio_value
        """
        # Get returns series
        returns = await self.pnl_service.calculate_returns_series(
            account_id, lookback_days
        )
        
        if len(returns) < 30:
            logger.warning(f"Insufficient data for parametric VaR: {len(returns)} returns")
            return {
                'var_value': 0.0,
                'confidence_level': alpha,
                'lookback_days': lookback_days,
                'method': 'parametric',
                'data_points': len(returns)
            }
        
        returns_array = np.array(returns)
        
        # Calculate sample statistics
        mean_return = np.mean(returns_array)
        volatility = np.std(returns_array, ddof=1)  # Sample standard deviation
        
        # Get z-score for confidence level (left tail)
        z_alpha = stats.norm.ppf(1 - alpha)  # This gives us a negative value
        
        # Calculate VaR as a positive value (expected loss)
        var_percent = abs(z_alpha * volatility - mean_return)
        
        # Convert to dollar terms
        current_pnl = await self.pnl_service.calculate_portfolio_pnl(account_id)
        portfolio_value = float(current_pnl.get('portfolio_value', 0))
        var_dollar = var_percent * portfolio_value
        
        return {
            'var_value': var_dollar,
            'var_percent': var_percent,
            'confidence_level': alpha,
            'lookback_days': lookback_days,
            'method': 'parametric',
            'volatility': volatility,
            'mean_return': mean_return,
            'z_score': z_alpha,
            'data_points': len(returns),
            'portfolio_value': portfolio_value
        }
    
    async def calculate_ewma_var(
        self,
        account_id: str,
        alpha: float = 0.99,
        lookback_days: int = 250,
        lambda_decay: float = 0.94
    ) -> Dict[str, float]:
        """
        Calculate EWMA (Exponentially Weighted Moving Average) VaR.
        
        Uses exponential weighting to give more importance to recent observations.
        """
        returns = await self.pnl_service.calculate_returns_series(
            account_id, lookback_days
        )
        
        if len(returns) < 30:
            return {
                'var_value': 0.0,
                'confidence_level': alpha,
                'method': 'ewma',
                'data_points': len(returns)
            }
        
        returns_array = np.array(returns)
        n = len(returns_array)
        
        # Calculate EWMA variance
        weights = np.array([(1 - lambda_decay) * (lambda_decay ** i) for i in range(n)])
        weights = weights / np.sum(weights)  # Normalize weights
        
        # Reverse weights so most recent observations get highest weight
        weights = weights[::-1]
        
        # Calculate weighted mean and variance
        weighted_mean = np.average(returns_array, weights=weights)
        weighted_variance = np.average((returns_array - weighted_mean) ** 2, weights=weights)
        volatility = np.sqrt(weighted_variance)
        
        # Calculate VaR
        z_alpha = stats.norm.ppf(1 - alpha)
        var_percent = abs(z_alpha * volatility - weighted_mean)
        
        # Convert to dollar terms
        current_pnl = await self.pnl_service.calculate_portfolio_pnl(account_id)
        portfolio_value = float(current_pnl.get('portfolio_value', 0))
        var_dollar = var_percent * portfolio_value
        
        return {
            'var_value': var_dollar,
            'var_percent': var_percent,
            'confidence_level': alpha,
            'lookback_days': lookback_days,
            'method': 'ewma',
            'volatility': volatility,
            'lambda_decay': lambda_decay,
            'weighted_mean': weighted_mean,
            'data_points': len(returns),
            'portfolio_value': portfolio_value
        }
    
    async def calculate_var(
        self,
        account_id: str,
        method: str = 'historical',
        alpha: float = 0.99,
        lookback_days: int = 250
    ) -> Dict[str, float]:
        """
        Calculate VaR using specified method.
        
        Args:
            account_id: Account identifier
            method: 'historical', 'parametric', or 'ewma'
            alpha: Confidence level
            lookback_days: Lookback period
        """
        if method == 'historical':
            return await self.calculate_historical_var(account_id, alpha, lookback_days)
        elif method == 'parametric':
            return await self.calculate_parametric_var(account_id, alpha, lookback_days)
        elif method == 'ewma':
            return await self.calculate_ewma_var(account_id, alpha, lookback_days)
        else:
            raise ValueError(f"Unknown VaR method: {method}")
    
    async def save_risk_metrics(
        self,
        account_id: str,
        as_of_date: datetime,
        var_results: Dict[str, Dict[str, float]]
    ) -> None:
        """Save calculated risk metrics to database."""
        risk_metric = RiskMetrics(
            account_id=account_id,
            as_of_date=as_of_date,
            var_historical=var_results.get('historical', {}).get('var_value'),
            var_parametric=var_results.get('parametric', {}).get('var_value'),
            var_alpha=var_results.get('historical', {}).get('confidence_level', 0.99),
            var_lookback_days=var_results.get('historical', {}).get('lookback_days', 250),
            portfolio_volatility=var_results.get('parametric', {}).get('volatility')
        )
        
        self.db.add(risk_metric)
        await self.db.commit()
        logger.info(f"Saved risk metrics for account {account_id} on {as_of_date.date()}")
    
    async def get_var_change(
        self,
        account_id: str,
        method: str = 'historical',
        days_back: int = 7
    ) -> Dict[str, float]:
        """Get VaR change over specified period."""
        current_var = await self.calculate_var(account_id, method)
        
        # Get historical VaR from database
        past_date = datetime.utcnow() - timedelta(days=days_back)
        
        # For now, return mock data - in production, query historical risk_metrics
        return {
            'current_var': current_var['var_value'],
            'previous_var': current_var['var_value'] * 0.9,  # Mock 10% decrease
            'change_absolute': current_var['var_value'] * 0.1,
            'change_percent': 10.0,
            'days_back': days_back
        }



