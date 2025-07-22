"""
Data fetcher module for the Telegram Trading Bot.
Fetches market data from various sources.
"""

import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

try:
    import finnhub
    FINNHUB_AVAILABLE = True
except ImportError:
    FINNHUB_AVAILABLE = False

from loguru import logger
from ..core.config import get_settings
from ..core.exceptions import ExternalAPIError
from ..core.utils import retry_on_exception, rate_limit


class DataFetcher:
    """Main data fetching engine."""
    
    def __init__(self):
        self.settings = get_settings()
        self.session = None
        self.finnhub_client = None
        
        if FINNHUB_AVAILABLE and self.settings.api.finnhub_key:
            self.finnhub_client = finnhub.Client(api_key=self.settings.api.finnhub_key)
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    @retry_on_exception(max_retries=3, delay=1.0)
    @rate_limit(calls_per_second=2.0)
    async def fetch_ohlc_data(self, symbol: str, timeframe: str = "5m", 
                            count: int = 100) -> Optional[pd.DataFrame]:
        """Fetch OHLC data for a symbol."""
        try:
            # Try different data sources based on symbol type
            if self._is_forex_symbol(symbol):
                return await self._fetch_forex_data(symbol, timeframe, count)
            elif self._is_crypto_symbol(symbol):
                return await self._fetch_crypto_data(symbol, timeframe, count)
            elif self._is_stock_symbol(symbol):
                return await self._fetch_stock_data(symbol, timeframe, count)
            else:
                # Try generic approach
                return await self._fetch_generic_data(symbol, timeframe, count)
                
        except Exception as e:
            logger.error(f"Error fetching OHLC data for {symbol}: {e}")
            return None
    
    def _is_forex_symbol(self, symbol: str) -> bool:
        """Check if symbol is a forex pair."""
        forex_pairs = [
            'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD',
            'EURJPY', 'GBPJPY', 'EURGBP', 'EURAUD', 'EURCHF', 'AUDCAD', 'GBPAUD',
            'GBPCAD', 'GBPCHF', 'AUDCHF', 'AUDJPY', 'CADJPY', 'CHFJPY', 'NZDJPY'
        ]
        return symbol.upper() in forex_pairs
    
    def _is_crypto_symbol(self, symbol: str) -> bool:
        """Check if symbol is a cryptocurrency."""
        crypto_symbols = [
            'BTCUSD', 'ETHUSD', 'ADAUSD', 'DOTUSD', 'LINKUSD', 'LTCUSD', 'BCHUSD',
            'XLMUSD', 'EOSUSD', 'TRXUSD', 'XRPUSD', 'BNBUSD', 'SOLUSD', 'MATICUSD'
        ]
        return symbol.upper() in crypto_symbols or 'USD' in symbol.upper()
    
    def _is_stock_symbol(self, symbol: str) -> bool:
        """Check if symbol is a stock."""
        # Simple heuristic - if it's not forex or crypto, assume it's a stock
        return not (self._is_forex_symbol(symbol) or self._is_crypto_symbol(symbol))
    
    async def _fetch_forex_data(self, symbol: str, timeframe: str, count: int) -> Optional[pd.DataFrame]:
        """Fetch forex data from Alpha Vantage or other forex providers."""
        try:
            if self.settings.api.alpha_vantage_key:
                return await self._fetch_alpha_vantage_data(symbol, timeframe, count)
            else:
                logger.warning("No Alpha Vantage API key configured for forex data")
                return await self._fetch_yahoo_data(symbol, timeframe, count)
        except Exception as e:
            logger.error(f"Error fetching forex data for {symbol}: {e}")
            return None
    
    async def _fetch_crypto_data(self, symbol: str, timeframe: str, count: int) -> Optional[pd.DataFrame]:
        """Fetch cryptocurrency data."""
        try:
            # Try Binance API first for crypto
            return await self._fetch_binance_data(symbol, timeframe, count)
        except Exception as e:
            logger.warning(f"Binance fetch failed for {symbol}, trying Yahoo Finance: {e}")
            return await self._fetch_yahoo_data(symbol, timeframe, count)
    
    async def _fetch_stock_data(self, symbol: str, timeframe: str, count: int) -> Optional[pd.DataFrame]:
        """Fetch stock data."""
        try:
            # Try Yahoo Finance for stocks
            return await self._fetch_yahoo_data(symbol, timeframe, count)
        except Exception as e:
            logger.error(f"Error fetching stock data for {symbol}: {e}")
            return None
    
    async def _fetch_generic_data(self, symbol: str, timeframe: str, count: int) -> Optional[pd.DataFrame]:
        """Fetch data using generic approach."""
        try:
            return await self._fetch_yahoo_data(symbol, timeframe, count)
        except Exception as e:
            logger.error(f"Error fetching generic data for {symbol}: {e}")
            return None
    
    async def _fetch_yahoo_data(self, symbol: str, timeframe: str, count: int) -> Optional[pd.DataFrame]:
        """Fetch data from Yahoo Finance."""
        if not YFINANCE_AVAILABLE:
            logger.error("yfinance library not available")
            return None
        
        try:
            # Convert timeframe to Yahoo Finance format
            yf_interval = self._convert_timeframe_to_yf(timeframe)
            
            # Calculate period based on count and timeframe
            period = self._calculate_period(timeframe, count)
            
            # Fetch data
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval=yf_interval)
            
            if data.empty:
                logger.warning(f"No data returned from Yahoo Finance for {symbol}")
                return None
            
            # Convert to standard format
            df = pd.DataFrame({
                'timestamp': data.index,
                'open': data['Open'].values,
                'high': data['High'].values,
                'low': data['Low'].values,
                'close': data['Close'].values,
                'volume': data['Volume'].values
            })
            
            # Take only the requested number of candles
            df = df.tail(count)
            
            logger.info(f"Fetched {len(df)} candles for {symbol} from Yahoo Finance")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching Yahoo Finance data for {symbol}: {e}")
            return None
    
    async def _fetch_alpha_vantage_data(self, symbol: str, timeframe: str, count: int) -> Optional[pd.DataFrame]:
        """Fetch data from Alpha Vantage."""
        if not self.settings.api.alpha_vantage_key:
            return None
        
        try:
            # Alpha Vantage API call
            function = self._get_alpha_vantage_function(timeframe)
            interval = self._convert_timeframe_to_av(timeframe)
            
            url = "https://www.alphavantage.co/query"
            params = {
                'function': function,
                'symbol': symbol,
                'interval': interval,
                'apikey': self.settings.api.alpha_vantage_key,
                'outputsize': 'compact'
            }
            
            async with self.session.get(url, params=params) as response:
                data = await response.json()
                
                if 'Error Message' in data:
                    logger.error(f"Alpha Vantage error: {data['Error Message']}")
                    return None
                
                if 'Note' in data:
                    logger.warning(f"Alpha Vantage rate limit: {data['Note']}")
                    return None
                
                # Parse the data
                time_series_key = f"Time Series ({interval})"
                if time_series_key not in data:
                    logger.error(f"Unexpected Alpha Vantage response format for {symbol}")
                    return None
                
                time_series = data[time_series_key]
                
                # Convert to DataFrame
                df_data = []
                for timestamp, values in time_series.items():
                    df_data.append({
                        'timestamp': pd.to_datetime(timestamp),
                        'open': float(values['1. open']),
                        'high': float(values['2. high']),
                        'low': float(values['3. low']),
                        'close': float(values['4. close']),
                        'volume': float(values['5. volume'])
                    })
                
                df = pd.DataFrame(df_data)
                df = df.sort_values('timestamp').tail(count)
                
                logger.info(f"Fetched {len(df)} candles for {symbol} from Alpha Vantage")
                return df
                
        except Exception as e:
            logger.error(f"Error fetching Alpha Vantage data for {symbol}: {e}")
            return None
    
    async def _fetch_binance_data(self, symbol: str, timeframe: str, count: int) -> Optional[pd.DataFrame]:
        """Fetch data from Binance API."""
        try:
            # Convert symbol to Binance format
            binance_symbol = self._convert_symbol_to_binance(symbol)
            
            # Convert timeframe to Binance format
            binance_interval = self._convert_timeframe_to_binance(timeframe)
            
            url = "https://api.binance.com/api/v3/klines"
            params = {
                'symbol': binance_symbol,
                'interval': binance_interval,
                'limit': count
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    logger.error(f"Binance API error: {response.status}")
                    return None
                
                data = await response.json()
                
                if not data:
                    logger.warning(f"No data returned from Binance for {symbol}")
                    return None
                
                # Convert to DataFrame
                df_data = []
                for kline in data:
                    df_data.append({
                        'timestamp': pd.to_datetime(kline[0], unit='ms'),
                        'open': float(kline[1]),
                        'high': float(kline[2]),
                        'low': float(kline[3]),
                        'close': float(kline[4]),
                        'volume': float(kline[5])
                    })
                
                df = pd.DataFrame(df_data)
                
                logger.info(f"Fetched {len(df)} candles for {symbol} from Binance")
                return df
                
        except Exception as e:
            logger.error(f"Error fetching Binance data for {symbol}: {e}")
            return None
    
    def _convert_timeframe_to_yf(self, timeframe: str) -> str:
        """Convert timeframe to Yahoo Finance format."""
        mapping = {
            '1m': '1m',
            '5m': '5m',
            '15m': '15m',
            '30m': '30m',
            '1h': '1h',
            '4h': '4h',
            '1d': '1d',
            '1w': '1wk',
            '1M': '1mo'
        }
        return mapping.get(timeframe, '5m')
    
    def _convert_timeframe_to_av(self, timeframe: str) -> str:
        """Convert timeframe to Alpha Vantage format."""
        mapping = {
            '1m': '1min',
            '5m': '5min',
            '15m': '15min',
            '30m': '30min',
            '1h': '60min',
            '1d': 'daily',
            '1w': 'weekly',
            '1M': 'monthly'
        }
        return mapping.get(timeframe, '5min')
    
    def _convert_timeframe_to_binance(self, timeframe: str) -> str:
        """Convert timeframe to Binance format."""
        mapping = {
            '1m': '1m',
            '5m': '5m',
            '15m': '15m',
            '30m': '30m',
            '1h': '1h',
            '4h': '4h',
            '1d': '1d',
            '1w': '1w',
            '1M': '1M'
        }
        return mapping.get(timeframe, '5m')
    
    def _convert_symbol_to_binance(self, symbol: str) -> str:
        """Convert symbol to Binance format."""
        # Remove common suffixes and convert to Binance format
        symbol = symbol.upper().replace('USD', 'USDT')
        
        # Handle specific cases
        if symbol == 'BTCUSDT':
            return 'BTCUSDT'
        elif symbol == 'ETHUSDT':
            return 'ETHUSDT'
        
        return symbol
    
    def _get_alpha_vantage_function(self, timeframe: str) -> str:
        """Get Alpha Vantage function based on timeframe."""
        if timeframe in ['1m', '5m', '15m', '30m', '1h']:
            return 'TIME_SERIES_INTRADAY'
        elif timeframe == '1d':
            return 'TIME_SERIES_DAILY'
        elif timeframe == '1w':
            return 'TIME_SERIES_WEEKLY'
        elif timeframe == '1M':
            return 'TIME_SERIES_MONTHLY'
        else:
            return 'TIME_SERIES_INTRADAY'
    
    def _calculate_period(self, timeframe: str, count: int) -> str:
        """Calculate period for Yahoo Finance based on timeframe and count."""
        # Convert timeframe to minutes
        timeframe_minutes = {
            '1m': 1,
            '5m': 5,
            '15m': 15,
            '30m': 30,
            '1h': 60,
            '4h': 240,
            '1d': 1440,
            '1w': 10080,
            '1M': 43200
        }
        
        minutes = timeframe_minutes.get(timeframe, 5)
        total_minutes = count * minutes
        
        # Convert to appropriate period
        if total_minutes <= 1440:  # 1 day
            return '1d'
        elif total_minutes <= 10080:  # 1 week
            return '5d'
        elif total_minutes <= 43200:  # 1 month
            return '1mo'
        elif total_minutes <= 129600:  # 3 months
            return '3mo'
        elif total_minutes <= 259200:  # 6 months
            return '6mo'
        elif total_minutes <= 525600:  # 1 year
            return '1y'
        else:
            return '2y'
    
    async def fetch_multiple_symbols(self, symbols: List[str], timeframe: str = "5m", 
                                   count: int = 100) -> Dict[str, Optional[pd.DataFrame]]:
        """Fetch OHLC data for multiple symbols concurrently."""
        tasks = [self.fetch_ohlc_data(symbol, timeframe, count) for symbol in symbols]
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            data_dict = {}
            for symbol, result in zip(symbols, results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to fetch data for {symbol}: {result}")
                    data_dict[symbol] = None
                else:
                    data_dict[symbol] = result
            
            return data_dict
            
        except Exception as e:
            logger.error(f"Error in batch data fetching: {e}")
            return {symbol: None for symbol in symbols}
    
    async def get_fundamental_data(self, symbol: str) -> Optional[Dict]:
        """Fetch fundamental data for a symbol."""
        if not self.finnhub_client:
            logger.warning("Finnhub client not available for fundamental data")
            return None
        
        try:
            # Get basic financials
            financials = self.finnhub_client.company_basic_financials(symbol, 'all')
            
            # Get company profile
            profile = self.finnhub_client.company_profile2(symbol=symbol)
            
            # Combine the data
            fundamental_data = {
                'symbol': symbol,
                'company_profile': profile,
                'financials': financials,
                'timestamp': datetime.now()
            }
            
            logger.info(f"Fetched fundamental data for {symbol}")
            return fundamental_data
            
        except Exception as e:
            logger.error(f"Error fetching fundamental data for {symbol}: {e}")
            return None
    
    def validate_ohlc_data(self, df: pd.DataFrame) -> bool:
        """Validate OHLC data quality."""
        if df is None or df.empty:
            return False
        
        required_columns = ['open', 'high', 'low', 'close']
        if not all(col in df.columns for col in required_columns):
            return False
        
        # Check for invalid OHLC relationships
        invalid_ohlc = (
            (df['high'] < df['low']) |
            (df['high'] < df['open']) |
            (df['high'] < df['close']) |
            (df['low'] > df['open']) |
            (df['low'] > df['close'])
        )
        
        if invalid_ohlc.any():
            logger.warning(f"Found {invalid_ohlc.sum()} invalid OHLC relationships")
            return False
        
        # Check for excessive gaps
        if len(df) > 1:
            price_changes = df['close'].pct_change().abs()
            excessive_gaps = price_changes > 0.5  # 50% price change
            
            if excessive_gaps.any():
                logger.warning(f"Found {excessive_gaps.sum()} excessive price gaps")
        
        return True

