"""
Technical indicators module for the Telegram Trading Bot.
Implements various technical analysis indicators.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from decimal import Decimal

try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False
    print("TA-Lib not available, using custom implementations")

from loguru import logger
from ..core.exceptions import TechnicalIndicatorError
from ..core.utils import round_decimal


class TechnicalIndicators:
    """Technical indicators calculator."""
    
    @staticmethod
    def validate_data(data: Union[pd.Series, np.ndarray, List[float]], min_length: int = 1) -> np.ndarray:
        """Validate and convert input data to numpy array."""
        if isinstance(data, pd.Series):
            data = data.values
        elif isinstance(data, list):
            data = np.array(data)
        elif not isinstance(data, np.ndarray):
            raise TechnicalIndicatorError(f"Invalid data type: {type(data)}")
        
        if len(data) < min_length:
            raise TechnicalIndicatorError(f"Insufficient data: need at least {min_length} points, got {len(data)}")
        
        # Remove NaN values
        data = data[~np.isnan(data)]
        
        if len(data) < min_length:
            raise TechnicalIndicatorError(f"Insufficient valid data after removing NaN values")
        
        return data
    
    @staticmethod
    def sma(data: Union[pd.Series, np.ndarray, List[float]], period: int = 20) -> np.ndarray:
        """Simple Moving Average."""
        data = TechnicalIndicators.validate_data(data, period)
        
        if TALIB_AVAILABLE:
            return talib.SMA(data, timeperiod=period)
        
        # Custom implementation
        result = np.full(len(data), np.nan)
        for i in range(period - 1, len(data)):
            result[i] = np.mean(data[i - period + 1:i + 1])
        
        return result
    
    @staticmethod
    def ema(data: Union[pd.Series, np.ndarray, List[float]], period: int = 20) -> np.ndarray:
        """Exponential Moving Average."""
        data = TechnicalIndicators.validate_data(data, period)
        
        if TALIB_AVAILABLE:
            return talib.EMA(data, timeperiod=period)
        
        # Custom implementation
        alpha = 2.0 / (period + 1)
        result = np.full(len(data), np.nan)
        result[period - 1] = np.mean(data[:period])
        
        for i in range(period, len(data)):
            result[i] = alpha * data[i] + (1 - alpha) * result[i - 1]
        
        return result
    
    @staticmethod
    def rsi(data: Union[pd.Series, np.ndarray, List[float]], period: int = 14) -> np.ndarray:
        """Relative Strength Index."""
        data = TechnicalIndicators.validate_data(data, period + 1)
        
        if TALIB_AVAILABLE:
            return talib.RSI(data, timeperiod=period)
        
        # Custom implementation
        deltas = np.diff(data)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gains = np.full(len(data), np.nan)
        avg_losses = np.full(len(data), np.nan)
        
        # Initial averages
        avg_gains[period] = np.mean(gains[:period])
        avg_losses[period] = np.mean(losses[:period])
        
        # Smoothed averages
        for i in range(period + 1, len(data)):
            avg_gains[i] = (avg_gains[i - 1] * (period - 1) + gains[i - 1]) / period
            avg_losses[i] = (avg_losses[i - 1] * (period - 1) + losses[i - 1]) / period
        
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def macd(data: Union[pd.Series, np.ndarray, List[float]], 
             fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """MACD (Moving Average Convergence Divergence)."""
        data = TechnicalIndicators.validate_data(data, slow_period)
        
        if TALIB_AVAILABLE:
            macd_line, signal_line, histogram = talib.MACD(data, fastperiod=fast_period, 
                                                          slowperiod=slow_period, signalperiod=signal_period)
            return macd_line, signal_line, histogram
        
        # Custom implementation
        ema_fast = TechnicalIndicators.ema(data, fast_period)
        ema_slow = TechnicalIndicators.ema(data, slow_period)
        
        macd_line = ema_fast - ema_slow
        signal_line = TechnicalIndicators.ema(macd_line[~np.isnan(macd_line)], signal_period)
        
        # Align signal line with macd line
        aligned_signal = np.full(len(macd_line), np.nan)
        valid_macd_start = slow_period - 1
        signal_start = valid_macd_start + signal_period - 1
        
        if signal_start < len(aligned_signal):
            aligned_signal[signal_start:signal_start + len(signal_line)] = signal_line
        
        histogram = macd_line - aligned_signal
        
        return macd_line, aligned_signal, histogram
    
    @staticmethod
    def bollinger_bands(data: Union[pd.Series, np.ndarray, List[float]], 
                       period: int = 20, std_dev: float = 2.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Bollinger Bands."""
        data = TechnicalIndicators.validate_data(data, period)
        
        if TALIB_AVAILABLE:
            upper, middle, lower = talib.BBANDS(data, timeperiod=period, nbdevup=std_dev, nbdevdn=std_dev)
            return upper, middle, lower
        
        # Custom implementation
        middle = TechnicalIndicators.sma(data, period)
        
        std = np.full(len(data), np.nan)
        for i in range(period - 1, len(data)):
            std[i] = np.std(data[i - period + 1:i + 1])
        
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        return upper, middle, lower
    
    @staticmethod
    def stochastic(high: Union[pd.Series, np.ndarray, List[float]], 
                  low: Union[pd.Series, np.ndarray, List[float]], 
                  close: Union[pd.Series, np.ndarray, List[float]], 
                  k_period: int = 14, d_period: int = 3) -> Tuple[np.ndarray, np.ndarray]:
        """Stochastic Oscillator."""
        high = TechnicalIndicators.validate_data(high, k_period)
        low = TechnicalIndicators.validate_data(low, k_period)
        close = TechnicalIndicators.validate_data(close, k_period)
        
        if len(high) != len(low) or len(high) != len(close):
            raise TechnicalIndicatorError("High, low, and close data must have the same length")
        
        if TALIB_AVAILABLE:
            k_percent, d_percent = talib.STOCH(high, low, close, 
                                             fastk_period=k_period, slowk_period=d_period, slowd_period=d_period)
            return k_percent, d_percent
        
        # Custom implementation
        k_percent = np.full(len(close), np.nan)
        
        for i in range(k_period - 1, len(close)):
            highest_high = np.max(high[i - k_period + 1:i + 1])
            lowest_low = np.min(low[i - k_period + 1:i + 1])
            
            if highest_high != lowest_low:
                k_percent[i] = ((close[i] - lowest_low) / (highest_high - lowest_low)) * 100
            else:
                k_percent[i] = 50  # Neutral value when no range
        
        d_percent = TechnicalIndicators.sma(k_percent[~np.isnan(k_percent)], d_period)
        
        # Align D% with K%
        aligned_d = np.full(len(k_percent), np.nan)
        valid_k_start = k_period - 1
        d_start = valid_k_start + d_period - 1
        
        if d_start < len(aligned_d):
            aligned_d[d_start:d_start + len(d_percent)] = d_percent
        
        return k_percent, aligned_d
    
    @staticmethod
    def atr(high: Union[pd.Series, np.ndarray, List[float]], 
            low: Union[pd.Series, np.ndarray, List[float]], 
            close: Union[pd.Series, np.ndarray, List[float]], 
            period: int = 14) -> np.ndarray:
        """Average True Range."""
        high = TechnicalIndicators.validate_data(high, period + 1)
        low = TechnicalIndicators.validate_data(low, period + 1)
        close = TechnicalIndicators.validate_data(close, period + 1)
        
        if TALIB_AVAILABLE:
            return talib.ATR(high, low, close, timeperiod=period)
        
        # Custom implementation
        tr = np.full(len(close), np.nan)
        
        for i in range(1, len(close)):
            tr1 = high[i] - low[i]
            tr2 = abs(high[i] - close[i - 1])
            tr3 = abs(low[i] - close[i - 1])
            tr[i] = max(tr1, tr2, tr3)
        
        # Calculate ATR using SMA
        atr = np.full(len(close), np.nan)
        for i in range(period, len(close)):
            atr[i] = np.mean(tr[i - period + 1:i + 1])
        
        return atr
    
    @staticmethod
    def support_resistance_levels(data: Union[pd.Series, np.ndarray, List[float]], 
                                 window: int = 20, min_touches: int = 2) -> Dict[str, List[float]]:
        """Identify support and resistance levels."""
        data = TechnicalIndicators.validate_data(data, window * 2)
        
        levels = {'support': [], 'resistance': []}
        
        # Find local minima (potential support)
        for i in range(window, len(data) - window):
            if data[i] == np.min(data[i - window:i + window + 1]):
                level = data[i]
                
                # Count touches within tolerance
                tolerance = np.std(data) * 0.01  # 1% of standard deviation
                touches = np.sum(np.abs(data - level) <= tolerance)
                
                if touches >= min_touches:
                    levels['support'].append(float(level))
        
        # Find local maxima (potential resistance)
        for i in range(window, len(data) - window):
            if data[i] == np.max(data[i - window:i + window + 1]):
                level = data[i]
                
                # Count touches within tolerance
                tolerance = np.std(data) * 0.01
                touches = np.sum(np.abs(data - level) <= tolerance)
                
                if touches >= min_touches:
                    levels['resistance'].append(float(level))
        
        # Remove duplicates and sort
        levels['support'] = sorted(list(set(levels['support'])))
        levels['resistance'] = sorted(list(set(levels['resistance'])), reverse=True)
        
        return levels
    
    @staticmethod
    def calculate_all_indicators(ohlc_data: pd.DataFrame) -> Dict[str, Union[float, Dict[str, float]]]:
        """Calculate all technical indicators for given OHLC data."""
        try:
            if not isinstance(ohlc_data, pd.DataFrame):
                raise TechnicalIndicatorError("OHLC data must be a pandas DataFrame")
            
            required_columns = ['open', 'high', 'low', 'close']
            missing_columns = [col for col in required_columns if col not in ohlc_data.columns]
            if missing_columns:
                raise TechnicalIndicatorError(f"Missing required columns: {missing_columns}")
            
            if len(ohlc_data) < 50:  # Minimum data for reliable indicators
                raise TechnicalIndicatorError("Insufficient data: need at least 50 candles")
            
            close = ohlc_data['close'].values
            high = ohlc_data['high'].values
            low = ohlc_data['low'].values
            
            indicators = {}
            
            # RSI
            rsi_values = TechnicalIndicators.rsi(close, 14)
            indicators['rsi'] = float(rsi_values[-1]) if not np.isnan(rsi_values[-1]) else None
            
            # MACD
            macd_line, signal_line, histogram = TechnicalIndicators.macd(close, 12, 26, 9)
            indicators['macd'] = {
                'macd': float(macd_line[-1]) if not np.isnan(macd_line[-1]) else None,
                'signal': float(signal_line[-1]) if not np.isnan(signal_line[-1]) else None,
                'histogram': float(histogram[-1]) if not np.isnan(histogram[-1]) else None
            }
            
            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = TechnicalIndicators.bollinger_bands(close, 20, 2.0)
            indicators['bollinger_bands'] = {
                'upper': float(bb_upper[-1]) if not np.isnan(bb_upper[-1]) else None,
                'middle': float(bb_middle[-1]) if not np.isnan(bb_middle[-1]) else None,
                'lower': float(bb_lower[-1]) if not np.isnan(bb_lower[-1]) else None
            }
            
            # Stochastic
            stoch_k, stoch_d = TechnicalIndicators.stochastic(high, low, close, 14, 3)
            indicators['stochastic'] = {
                'k': float(stoch_k[-1]) if not np.isnan(stoch_k[-1]) else None,
                'd': float(stoch_d[-1]) if not np.isnan(stoch_d[-1]) else None
            }
            
            # ATR
            atr_values = TechnicalIndicators.atr(high, low, close, 14)
            indicators['atr'] = float(atr_values[-1]) if not np.isnan(atr_values[-1]) else None
            
            # Moving Averages
            sma_20 = TechnicalIndicators.sma(close, 20)
            sma_50 = TechnicalIndicators.sma(close, 50)
            ema_20 = TechnicalIndicators.ema(close, 20)
            
            indicators['moving_averages'] = {
                'sma_20': float(sma_20[-1]) if not np.isnan(sma_20[-1]) else None,
                'sma_50': float(sma_50[-1]) if not np.isnan(sma_50[-1]) else None,
                'ema_20': float(ema_20[-1]) if not np.isnan(ema_20[-1]) else None
            }
            
            # Support and Resistance
            sr_levels = TechnicalIndicators.support_resistance_levels(close, 20, 2)
            indicators['support_resistance'] = sr_levels
            
            # Current price
            indicators['current_price'] = float(close[-1])
            
            logger.info(f"Calculated technical indicators for {len(ohlc_data)} candles")
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            raise TechnicalIndicatorError(f"Failed to calculate indicators: {e}")


def get_indicator_signals(indicators: Dict[str, Union[float, Dict[str, float]]]) -> Dict[str, str]:
    """Generate trading signals based on technical indicators."""
    signals = {}
    
    try:
        # RSI signals
        rsi = indicators.get('rsi')
        if rsi is not None:
            if rsi > 70:
                signals['rsi'] = 'SELL'  # Overbought
            elif rsi < 30:
                signals['rsi'] = 'BUY'   # Oversold
            else:
                signals['rsi'] = 'NEUTRAL'
        
        # MACD signals
        macd_data = indicators.get('macd', {})
        macd_line = macd_data.get('macd')
        signal_line = macd_data.get('signal')
        
        if macd_line is not None and signal_line is not None:
            if macd_line > signal_line:
                signals['macd'] = 'BUY'
            elif macd_line < signal_line:
                signals['macd'] = 'SELL'
            else:
                signals['macd'] = 'NEUTRAL'
        
        # Bollinger Bands signals
        bb_data = indicators.get('bollinger_bands', {})
        current_price = indicators.get('current_price')
        bb_upper = bb_data.get('upper')
        bb_lower = bb_data.get('lower')
        
        if current_price is not None and bb_upper is not None and bb_lower is not None:
            if current_price > bb_upper:
                signals['bollinger_bands'] = 'SELL'  # Price above upper band
            elif current_price < bb_lower:
                signals['bollinger_bands'] = 'BUY'   # Price below lower band
            else:
                signals['bollinger_bands'] = 'NEUTRAL'
        
        # Stochastic signals
        stoch_data = indicators.get('stochastic', {})
        stoch_k = stoch_data.get('k')
        
        if stoch_k is not None:
            if stoch_k > 80:
                signals['stochastic'] = 'SELL'  # Overbought
            elif stoch_k < 20:
                signals['stochastic'] = 'BUY'   # Oversold
            else:
                signals['stochastic'] = 'NEUTRAL'
        
        # Moving Average signals
        ma_data = indicators.get('moving_averages', {})
        sma_20 = ma_data.get('sma_20')
        sma_50 = ma_data.get('sma_50')
        
        if current_price is not None and sma_20 is not None and sma_50 is not None:
            if current_price > sma_20 > sma_50:
                signals['moving_average'] = 'BUY'   # Uptrend
            elif current_price < sma_20 < sma_50:
                signals['moving_average'] = 'SELL'  # Downtrend
            else:
                signals['moving_average'] = 'NEUTRAL'
        
        return signals
        
    except Exception as e:
        logger.error(f"Error generating indicator signals: {e}")
        return {}

