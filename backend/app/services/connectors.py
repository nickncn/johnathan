"""Data connectors for market data and trade feeds."""

import logging
import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Instrument, Price, Trade

logger = logging.getLogger(__name__)


class DataConnector:
    """Base class for market data connectors."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def fetch_prices(
        self, 
        symbols: List[str], 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, List[Dict]]:
        """Fetch price data for given symbols."""
        raise NotImplementedError
    
    async def fetch_latest_prices(self, symbols: List[str]) -> Dict[str, Decimal]:
        """Fetch latest prices for given symbols."""
        raise NotImplementedError


class MockDataConnector(DataConnector):
    """Mock data connector for testing and development."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self._price_cache = {}
        self._initialize_base_prices()
    
    def _initialize_base_prices(self):
        """Initialize base prices for mock data."""
        self._base_prices = {
            'AAPL': 150.0,
            'GOOGL': 2500.0,
            'TSLA': 800.0,
            'BTC': 45000.0,
            'ETH': 3000.0,
            'EUR/USD': 1.1000,
            'GBP/USD': 1.3000,
            'USD/JPY': 110.0
        }
    
    async def fetch_prices(
        self,
        symbols: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, List[Dict]]:
        """Generate mock historical price data."""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=365)
        if not end_date:
            end_date = datetime.utcnow()
        
        prices_data = {}
        
        for symbol in symbols:
            base_price = self._base_prices.get(symbol, 100.0)
            prices = []
            
            current_date = start_date
            current_price = base_price
            
            while current_date <= end_date:
                # Generate random walk with some mean reversion
                daily_return = random.gauss(0.0005, 0.02)  # Small positive drift, 2% daily vol
                current_price *= (1 + daily_return)
                
                # Add some mean reversion
                mean_reversion_factor = 0.001
                current_price += mean_reversion_factor * (base_price - current_price)
                
                prices.append({
                    'timestamp': current_date,
                    'price': round(current_price, 2),
                    'volume': random.randint(10000, 100000)
                })
                
                current_date += timedelta(days=1)
            
            prices_data[symbol] = prices
        
        return prices_data
    
    async def fetch_latest_prices(self, symbols: List[str]) -> Dict[str, Decimal]:
        """Generate mock latest prices."""
        latest_prices = {}
        
        for symbol in symbols:
            base_price = self._base_prices.get(symbol, 100.0)
            # Add small random variation
            variation = random.gauss(0, 0.01)  # 1% volatility
            current_price = base_price * (1 + variation)
            latest_prices[symbol] = Decimal(str(round(current_price, 2)))
        
        return latest_prices
    
    async def generate_live_tick(self, symbol: str) -> Dict:
        """Generate a single live price tick for WebSocket streaming."""
        base_price = self._base_prices.get(symbol, 100.0)
        variation = random.gauss(0, 0.005)  # 0.5% intraday volatility
        current_price = base_price * (1 + variation)
        
        return {
            'symbol': symbol,
            'price': round(current_price, 2),
            'timestamp': datetime.utcnow().isoformat(),
            'volume': random.randint(100, 1000)
        }


class YahooFinanceConnector(DataConnector):
    """Yahoo Finance connector for real market data."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        try:
            import yfinance as yf
            self.yf = yf
        except ImportError:
            logger.error("yfinance not installed. Install with: pip install yfinance")
            self.yf = None
    
    async def fetch_prices(
        self,
        symbols: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, List[Dict]]:
        """Fetch real price data from Yahoo Finance."""
        if not self.yf:
            logger.warning("YFinance not available, using mock data")
            mock_connector = MockDataConnector(self.db)
            return await mock_connector.fetch_prices(symbols, start_date, end_date)
        
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=365)
        if not end_date:
            end_date = datetime.utcnow()
        
        prices_data = {}
        
        for symbol in symbols:
            try:
                ticker = self.yf.Ticker(symbol)
                hist = ticker.history(start=start_date, end=end_date)
                
                prices = []
                for date, row in hist.iterrows():
                    prices.append({
                        'timestamp': date.to_pydatetime(),
                        'price': float(row['Close']),
                        'volume': int(row['Volume'])
                    })
                
                prices_data[symbol] = prices
                
            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {e}")
                # Fall back to mock data for this symbol
                mock_connector = MockDataConnector(self.db)
                mock_data = await mock_connector.fetch_prices([symbol], start_date, end_date)
                prices_data[symbol] = mock_data[symbol]
        
        return prices_data
    
    async def fetch_latest_prices(self, symbols: List[str]) -> Dict[str, Decimal]:
        """Fetch latest prices from Yahoo Finance."""
        if not self.yf:
            mock_connector = MockDataConnector(self.db)
            return await mock_connector.fetch_latest_prices(symbols)
        
        latest_prices = {}
        
        for symbol in symbols:
            try:
                ticker = self.yf.Ticker(symbol)
                info = ticker.info
                price = info.get('regularMarketPrice') or info.get('previousClose', 100.0)
                latest_prices[symbol] = Decimal(str(price))
                
            except Exception as e:
                logger.error(f"Error fetching latest price for {symbol}: {e}")
                # Fall back to mock data
                mock_connector = MockDataConnector(self.db)
                mock_prices = await mock_connector.fetch_latest_prices([symbol])
                latest_prices[symbol] = mock_prices[symbol]
        
        return latest_prices


class CryptoConnector(DataConnector):
    """Crypto data connector using CCXT."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        try:
            import ccxt
            self.exchange = ccxt.binance({
                'apiKey': '',  # Add API keys if needed
                'secret': '',
                'timeout': 30000,
                'enableRateLimit': True,
            })
        except ImportError:
            logger.error("CCXT not installed. Install with: pip install ccxt")
            self.exchange = None
    
    async def fetch_latest_prices(self, symbols: List[str]) -> Dict[str, Decimal]:
        """Fetch latest crypto prices."""
        if not self.exchange:
            mock_connector = MockDataConnector(self.db)
            return await mock_connector.fetch_latest_prices(symbols)
        
        latest_prices = {}
        
        for symbol in symbols:
            try:
                # Convert symbol format (e.g., BTC -> BTC/USDT)
                if '/' not in symbol:
                    symbol_pair = f"{symbol}/USDT"
                else:
                    symbol_pair = symbol
                
                ticker = self.exchange.fetch_ticker(symbol_pair)
                latest_prices[symbol] = Decimal(str(ticker['last']))
                
            except Exception as e:
                logger.error(f"Error fetching crypto price for {symbol}: {e}")
                # Fall back to mock
                mock_connector = MockDataConnector(self.db)
                mock_prices = await mock_connector.fetch_latest_prices([symbol])
                latest_prices[symbol] = mock_prices[symbol]
        
        return latest_prices
