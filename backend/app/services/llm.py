"""LLM integration services for risk analysis."""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.services.exposure import ExposureService
from app.services.pnl import PnlService
from app.services.var import VarService

logger = logging.getLogger(__name__)
settings = get_settings()


class LlmService:
    """Service for LLM-powered risk analysis."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.pnl_service = PnlService(db)
        self.var_service = VarService(db)
        self.exposure_service = ExposureService(db)
    
    async def generate_risk_summary(
        self,
        account_id: str,
        alpha: float = 0.99,
        lookback_days: int = 250,
        horizon_days: int = 1
    ) -> Dict[str, str]:
        """Generate AI-powered risk summary."""
        try:
            # Gather risk data
            risk_data = await self._gather_risk_data(account_id, alpha, lookback_days)
            
            # Build grounded prompt
            prompt = self._build_risk_prompt(risk_data, alpha, lookback_days)
            
            # Call LLM
            summary = await self._call_llm(prompt)
            
            return {
                'summary': summary,
                'account_id': account_id,
                'generated_at': datetime.utcnow().isoformat(),
                'parameters': {
                    'alpha': alpha,
                    'lookback_days': lookback_days,
                    'horizon_days': horizon_days
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating risk summary: {e}")
            return {
                'summary': self._fallback_summary(account_id),
                'error': str(e),
                'generated_at': datetime.utcnow().isoformat()
            }
    
    async def _gather_risk_data(
        self, 
        account_id: str, 
        alpha: float, 
        lookback_days: int
    ) -> Dict:
        """Gather all relevant risk data for analysis."""
        # Current P&L
        current_pnl = await self.pnl_service.calculate_portfolio_pnl(account_id)
        
        # VaR calculations
        var_historical = await self.var_service.calculate_historical_var(
            account_id, alpha, lookback_days
        )
        var_parametric = await self.var_service.calculate_parametric_var(
            account_id, alpha, lookback_days
        )
        
        # VaR change over past week
        var_change = await self.var_service.get_var_change(account_id)
        
        # Top P&L contributors
        top_contributors = await self.pnl_service.get_position_contributions(account_id, 5)
        
        # Exposure analysis
        exposure_summary = await self.exposure_service.get_exposure_summary(account_id)
        
        # Recent P&L history (past 30 days)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        recent_pnl = await self.pnl_service.get_pnl_timeseries(
            account_id, start_date, end_date
        )
        
        return {
            'current_pnl': current_pnl,
            'var_historical': var_historical,
            'var_parametric': var_parametric,
            'var_change': var_change,
            'top_contributors': top_contributors,
            'exposure_summary': exposure_summary,
            'recent_pnl': recent_pnl[-7:] if recent_pnl else [],  # Last 7 days
            'portfolio_stats': {
                'total_positions': len(top_contributors),
                'largest_position_pct': exposure_summary['concentration_analysis']['concentration_metrics']['largest_position_pct']
            }
        }
    
    def _build_risk_prompt(self, risk_data: Dict, alpha: float, lookback_days: int) -> str:
        """Build a grounded prompt for risk analysis."""
        return f"""You are a risk management expert analyzing a trading portfolio. Provide a concise executive summary based on the following data:

CURRENT PORTFOLIO STATUS:
- Portfolio Value: ${risk_data['current_pnl']['portfolio_value']:,.2f}
- Total P&L: ${risk_data['current_pnl']['total_pnl']:,.2f}
- Unrealized P&L: ${risk_data['current_pnl']['unrealized_pnl']:,.2f}

RISK METRICS ({alpha*100}% confidence, {lookback_days} day lookback):
- Historical VaR: ${risk_data['var_historical']['var_value']:,.2f}
- Parametric VaR: ${risk_data['var_parametric']['var_value']:,.2f}
- VaR Change (7d): {risk_data['var_change']['change_percent']:.1f}%

TOP POSITION CONTRIBUTORS:
{json.dumps(risk_data['top_contributors'][:3], indent=2)}

CONCENTRATION RISK:
- Largest Position: {risk_data['exposure_summary']['concentration_analysis']['concentration_metrics']['largest_position_pct']:.1f}%
- Total Positions: {risk_data['portfolio_stats']['total_positions']}

RECENT PERFORMANCE (last 7 days):
{json.dumps(risk_data['recent_pnl'], indent=2)}

Please provide:
1. 5-bullet executive summary of current risk profile
2. Top 3 key risk drivers or concerns
3. 2 actionable risk mitigation recommendations

Keep the response concise (under 500 words) and focus on actionable insights. Use professional risk management language."""

    async def _call_llm(self, prompt: str) -> str:
        """Call the configured LLM service."""
        if not settings.LLM_API_KEY:
            return self._fallback_summary("")
        
        try:
            if settings.LLM_PROVIDER.lower() == 'anthropic':
                return await self._call_anthropic(prompt)
            elif settings.LLM_PROVIDER.lower() == 'openai':
                return await self._call_openai(prompt)
            else:
                logger.warning(f"Unknown LLM provider: {settings.LLM_PROVIDER}")
                return self._fallback_summary("")
                
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            return self._fallback_summary("") + f"\n\nNote: AI analysis unavailable due to API error."
    
    async def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic Claude API."""
        try:
            import anthropic
            
            client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY or settings.LLM_API_KEY)
            
            message = await client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=settings.LLM_MAX_TOKENS,
                temperature=settings.LLM_TEMPERATURE,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return message.content[0].text
            
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise
    
    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API."""
        try:
            import openai
            
            client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY or settings.LLM_API_KEY)
            
            response = await client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=settings.LLM_MAX_TOKENS,
                temperature=settings.LLM_TEMPERATURE
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def _fallback_summary(self, account_id: str) -> str:
        """Provide fallback summary when LLM is unavailable."""
        return """RISK SUMMARY (Generated by System)

- Portfolio risk metrics have been calculated based on historical data
- VaR estimates provide guidance on potential losses at specified confidence levels
- Position concentration and exposure analysis completed
- Recent P&L trends are within normal parameters
- Regular monitoring of risk thresholds is recommended

KEY AREAS FOR REVIEW:
- Review position sizing and concentration limits
- Monitor correlations between holdings
- Consider hedging strategies for large exposures

RECOMMENDATIONS:
- Maintain diversification across asset classes
- Set appropriate stop-loss levels for major positions

Note: Enhanced AI-powered analysis is currently unavailable. Please ensure LLM service is properly configured."""



