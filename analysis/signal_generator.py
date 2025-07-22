"""
Signal generation module for the Telegram Trading Bot.
Combines technical analysis and sentiment analysis to generate trading signals.
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

import pandas as pd
from loguru import logger

from .technical_indicators import TechnicalIndicators, get_indicator_signals
from .sentiment_analysis import SentimentAnalyzer, SentimentResult, get_sentiment_signal
from ..core.exceptions import AnalysisError
from ..core.utils import round_decimal


class SignalStrength(Enum):
    """Signal strength levels."""
    VERY_WEAK = 1
    WEAK = 2
    MODERATE = 3
    STRONG = 4
    VERY_STRONG = 5


class SignalType(Enum):
    """Signal types."""
    BUY = "BUY"
    SELL = "SELL"
    NEUTRAL = "NEUTRAL"


@dataclass
class TradingSignal:
    """Trading signal data structure."""
    symbol: str
    signal_type: SignalType
    strength: SignalStrength
    confidence: float  # 0 to 1
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward_ratio: float
    timestamp: datetime
    
    # Analysis components
    technical_signals: Dict[str, str]
    sentiment_result: SentimentResult
    support_resistance: Dict[str, List[float]]
    
    # Additional metadata
    timeframe: str
    reasoning: List[str]
    warnings: List[str]


class SignalGenerator:
    """Main signal generation engine."""
    
    def __init__(self):
        self.technical_indicators = TechnicalIndicators()
        self.sentiment_analyzer = SentimentAnalyzer()
    
    async def generate_signal(self, symbol: str, ohlc_data: pd.DataFrame, 
                            timeframe: str = "5m") -> Optional[TradingSignal]:
        """Generate a comprehensive trading signal."""
        try:
            if len(ohlc_data) < 100:
                logger.warning(f"Insufficient data for {symbol}: {len(ohlc_data)} candles")
                return None
            
            # Calculate technical indicators
            indicators = self.technical_indicators.calculate_all_indicators(ohlc_data)
            technical_signals = get_indicator_signals(indicators)
            
            # Analyze sentiment
            sentiment_result = await self.sentiment_analyzer.analyze_symbol_sentiment(symbol)
            sentiment_signal = get_sentiment_signal(sentiment_result)
            
            # Combine signals
            signal_type, strength, confidence = self._combine_signals(
                technical_signals, sentiment_signal, sentiment_result.confidence
            )
            
            if signal_type == SignalType.NEUTRAL:
                logger.info(f"No clear signal for {symbol}")
                return None
            
            # Calculate entry, stop loss, and take profit
            current_price = indicators['current_price']
            support_resistance = indicators['support_resistance']
            atr = indicators.get('atr', current_price * 0.01)  # Fallback to 1% if ATR not available
            
            entry_price, stop_loss, take_profit = self._calculate_levels(
                signal_type, current_price, support_resistance, atr
            )
            
            # Calculate risk-reward ratio
            if signal_type == SignalType.BUY:
                risk = entry_price - stop_loss
                reward = take_profit - entry_price
            else:  # SELL
                risk = stop_loss - entry_price
                reward = entry_price - take_profit
            
            risk_reward_ratio = reward / risk if risk > 0 else 0
            
            # Generate reasoning and warnings
            reasoning = self._generate_reasoning(technical_signals, sentiment_signal, indicators)
            warnings = self._generate_warnings(indicators, sentiment_result)
            
            signal = TradingSignal(
                symbol=symbol,
                signal_type=signal_type,
                strength=strength,
                confidence=confidence,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                risk_reward_ratio=risk_reward_ratio,
                timestamp=datetime.now(),
                technical_signals=technical_signals,
                sentiment_result=sentiment_result,
                support_resistance=support_resistance,
                timeframe=timeframe,
                reasoning=reasoning,
                warnings=warnings
            )
            
            logger.info(f"Generated {signal_type.value} signal for {symbol} "
                       f"(strength: {strength.name}, confidence: {confidence:.2f})")
            
            return signal
            
        except Exception as e:
            logger.error(f"Error generating signal for {symbol}: {e}")
            raise AnalysisError(f"Failed to generate signal: {e}")
    
    def _combine_signals(self, technical_signals: Dict[str, str], 
                        sentiment_signal: str, sentiment_confidence: float) -> Tuple[SignalType, SignalStrength, float]:
        """Combine technical and sentiment signals."""
        # Count technical signals
        buy_signals = sum(1 for signal in technical_signals.values() if signal == 'BUY')
        sell_signals = sum(1 for signal in technical_signals.values() if signal == 'SELL')
        total_signals = len(technical_signals)
        
        # Calculate technical signal strength
        if buy_signals > sell_signals:
            technical_bias = SignalType.BUY
            technical_strength = buy_signals / total_signals
        elif sell_signals > buy_signals:
            technical_bias = SignalType.SELL
            technical_strength = sell_signals / total_signals
        else:
            technical_bias = SignalType.NEUTRAL
            technical_strength = 0.5
        
        # Weight technical vs sentiment (70% technical, 30% sentiment)
        technical_weight = 0.7
        sentiment_weight = 0.3
        
        # Convert sentiment signal to numeric
        sentiment_numeric = 0
        if sentiment_signal == 'BUY':
            sentiment_numeric = 1
        elif sentiment_signal == 'SELL':
            sentiment_numeric = -1
        
        # Convert technical bias to numeric
        technical_numeric = 0
        if technical_bias == SignalType.BUY:
            technical_numeric = 1
        elif technical_bias == SignalType.SELL:
            technical_numeric = -1
        
        # Combine signals
        combined_score = (technical_numeric * technical_strength * technical_weight + 
                         sentiment_numeric * sentiment_confidence * sentiment_weight)
        
        # Determine final signal
        if combined_score > 0.3:
            signal_type = SignalType.BUY
        elif combined_score < -0.3:
            signal_type = SignalType.SELL
        else:
            signal_type = SignalType.NEUTRAL
        
        # Determine strength
        abs_score = abs(combined_score)
        if abs_score >= 0.8:
            strength = SignalStrength.VERY_STRONG
        elif abs_score >= 0.6:
            strength = SignalStrength.STRONG
        elif abs_score >= 0.4:
            strength = SignalStrength.MODERATE
        elif abs_score >= 0.2:
            strength = SignalStrength.WEAK
        else:
            strength = SignalStrength.VERY_WEAK
        
        # Calculate confidence
        confidence = min(abs_score, 1.0)
        
        return signal_type, strength, confidence
    
    def _calculate_levels(self, signal_type: SignalType, current_price: float, 
                         support_resistance: Dict[str, List[float]], atr: float) -> Tuple[float, float, float]:
        """Calculate entry, stop loss, and take profit levels."""
        entry_price = current_price
        
        if signal_type == SignalType.BUY:
            # For BUY signals
            # Stop loss: below nearest support or 2*ATR below entry
            supports = support_resistance.get('support', [])
            nearest_support = None
            
            for support in supports:
                if support < current_price:
                    if nearest_support is None or support > nearest_support:
                        nearest_support = support
            
            if nearest_support and (current_price - nearest_support) < (3 * atr):
                stop_loss = nearest_support - (atr * 0.5)  # Small buffer below support
            else:
                stop_loss = current_price - (2 * atr)
            
            # Take profit: at nearest resistance or 2:1 risk-reward
            resistances = support_resistance.get('resistance', [])
            nearest_resistance = None
            
            for resistance in resistances:
                if resistance > current_price:
                    if nearest_resistance is None or resistance < nearest_resistance:
                        nearest_resistance = resistance
            
            risk = current_price - stop_loss
            target_profit = risk * 2  # 2:1 risk-reward
            calculated_tp = current_price + target_profit
            
            if nearest_resistance and nearest_resistance < calculated_tp:
                take_profit = nearest_resistance - (atr * 0.5)  # Small buffer below resistance
            else:
                take_profit = calculated_tp
        
        else:  # SELL signal
            # Stop loss: above nearest resistance or 2*ATR above entry
            resistances = support_resistance.get('resistance', [])
            nearest_resistance = None
            
            for resistance in resistances:
                if resistance > current_price:
                    if nearest_resistance is None or resistance < nearest_resistance:
                        nearest_resistance = resistance
            
            if nearest_resistance and (nearest_resistance - current_price) < (3 * atr):
                stop_loss = nearest_resistance + (atr * 0.5)  # Small buffer above resistance
            else:
                stop_loss = current_price + (2 * atr)
            
            # Take profit: at nearest support or 2:1 risk-reward
            supports = support_resistance.get('support', [])
            nearest_support = None
            
            for support in supports:
                if support < current_price:
                    if nearest_support is None or support > nearest_support:
                        nearest_support = support
            
            risk = stop_loss - current_price
            target_profit = risk * 2  # 2:1 risk-reward
            calculated_tp = current_price - target_profit
            
            if nearest_support and nearest_support > calculated_tp:
                take_profit = nearest_support + (atr * 0.5)  # Small buffer above support
            else:
                take_profit = calculated_tp
        
        return round(entry_price, 5), round(stop_loss, 5), round(take_profit, 5)
    
    def _generate_reasoning(self, technical_signals: Dict[str, str], 
                          sentiment_signal: str, indicators: Dict) -> List[str]:
        """Generate human-readable reasoning for the signal."""
        reasoning = []
        
        # Technical analysis reasoning
        buy_indicators = [name for name, signal in technical_signals.items() if signal == 'BUY']
        sell_indicators = [name for name, signal in technical_signals.items() if signal == 'SELL']
        
        if buy_indicators:
            reasoning.append(f"Bullish technical indicators: {', '.join(buy_indicators)}")
        
        if sell_indicators:
            reasoning.append(f"Bearish technical indicators: {', '.join(sell_indicators)}")
        
        # Specific indicator details
        rsi = indicators.get('rsi')
        if rsi:
            if rsi > 70:
                reasoning.append(f"RSI overbought at {rsi:.1f}")
            elif rsi < 30:
                reasoning.append(f"RSI oversold at {rsi:.1f}")
        
        macd_data = indicators.get('macd', {})
        macd_line = macd_data.get('macd')
        signal_line = macd_data.get('signal')
        if macd_line and signal_line:
            if macd_line > signal_line:
                reasoning.append("MACD bullish crossover")
            elif macd_line < signal_line:
                reasoning.append("MACD bearish crossover")
        
        # Sentiment reasoning
        if sentiment_signal == 'BUY':
            reasoning.append("Positive market sentiment")
        elif sentiment_signal == 'SELL':
            reasoning.append("Negative market sentiment")
        
        return reasoning
    
    def _generate_warnings(self, indicators: Dict, sentiment_result: SentimentResult) -> List[str]:
        """Generate warnings about potential risks."""
        warnings = []
        
        # Low sentiment confidence
        if sentiment_result.confidence < 0.3:
            warnings.append("Low sentiment analysis confidence")
        
        # Conflicting indicators
        rsi = indicators.get('rsi')
        if rsi:
            if 30 <= rsi <= 70:
                warnings.append("RSI in neutral zone - mixed signals possible")
        
        # Low volatility warning
        atr = indicators.get('atr')
        current_price = indicators.get('current_price')
        if atr and current_price:
            atr_percentage = (atr / current_price) * 100
            if atr_percentage < 0.5:
                warnings.append("Low volatility - tight stops recommended")
        
        # Market session warning
        from ..core.utils import is_market_open, get_market_session
        if not is_market_open():
            warnings.append("Market is closed - execution may be delayed")
        
        return warnings
    
    async def batch_generate_signals(self, symbols_data: Dict[str, pd.DataFrame], 
                                   timeframe: str = "5m") -> Dict[str, Optional[TradingSignal]]:
        """Generate signals for multiple symbols."""
        signals = {}
        
        for symbol, ohlc_data in symbols_data.items():
            try:
                signal = await self.generate_signal(symbol, ohlc_data, timeframe)
                signals[symbol] = signal
            except Exception as e:
                logger.error(f"Failed to generate signal for {symbol}: {e}")
                signals[symbol] = None
        
        return signals
    
    def filter_signals_by_strength(self, signals: Dict[str, Optional[TradingSignal]], 
                                 min_strength: SignalStrength = SignalStrength.MODERATE) -> Dict[str, TradingSignal]:
        """Filter signals by minimum strength."""
        filtered = {}
        
        for symbol, signal in signals.items():
            if signal and signal.strength.value >= min_strength.value:
                filtered[symbol] = signal
        
        return filtered
    
    def rank_signals_by_quality(self, signals: Dict[str, TradingSignal]) -> List[Tuple[str, TradingSignal]]:
        """Rank signals by quality (strength + confidence + risk-reward)."""
        def signal_score(signal: TradingSignal) -> float:
            strength_score = signal.strength.value / 5.0  # Normalize to 0-1
            confidence_score = signal.confidence
            rr_score = min(signal.risk_reward_ratio / 3.0, 1.0)  # Cap at 3:1
            
            return (strength_score * 0.4 + confidence_score * 0.4 + rr_score * 0.2)
        
        ranked = [(symbol, signal) for symbol, signal in signals.items()]
        ranked.sort(key=lambda x: signal_score(x[1]), reverse=True)
        
        return ranked

