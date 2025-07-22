"""
Tests for technical indicators module.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from analysis.technical_indicators import TechnicalIndicators


class TestTechnicalIndicators:
    """Test cases for technical indicators."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample OHLCV data for testing."""
        dates = pd.date_range(start='2023-01-01', periods=100, freq='1H')
        
        # Generate realistic price data
        np.random.seed(42)
        base_price = 100.0
        price_changes = np.random.normal(0, 0.02, 100)
        prices = [base_price]
        
        for change in price_changes[1:]:
            new_price = prices[-1] * (1 + change)
            prices.append(max(new_price, 1.0))  # Ensure positive prices
        
        # Create OHLCV data
        data = []
        for i, (date, price) in enumerate(zip(dates, prices)):
            high = price * (1 + abs(np.random.normal(0, 0.01)))
            low = price * (1 - abs(np.random.normal(0, 0.01)))
            open_price = prices[i-1] if i > 0 else price
            close_price = price
            volume = np.random.randint(1000, 10000)
            
            data.append({
                'timestamp': date,
                'open': open_price,
                'high': max(high, open_price, close_price),
                'low': min(low, open_price, close_price),
                'close': close_price,
                'volume': volume
            })
        
        return pd.DataFrame(data)
    
    def test_calculate_rsi(self, sample_data):
        """Test RSI calculation."""
        indicators = TechnicalIndicators()
        
        # Test with default period
        rsi = indicators.calculate_rsi(sample_data)
        
        assert isinstance(rsi, pd.Series)
        assert len(rsi) == len(sample_data)
        assert not rsi.isna().all()  # Should have some non-NaN values
        
        # RSI should be between 0 and 100
        valid_rsi = rsi.dropna()
        assert (valid_rsi >= 0).all()
        assert (valid_rsi <= 100).all()
        
        # Test with custom period
        rsi_custom = indicators.calculate_rsi(sample_data, period=21)
        assert isinstance(rsi_custom, pd.Series)
        assert len(rsi_custom) == len(sample_data)
    
    def test_calculate_macd(self, sample_data):
        """Test MACD calculation."""
        indicators = TechnicalIndicators()
        
        macd_line, signal_line, histogram = indicators.calculate_macd(sample_data)
        
        # Check return types
        assert isinstance(macd_line, pd.Series)
        assert isinstance(signal_line, pd.Series)
        assert isinstance(histogram, pd.Series)
        
        # Check lengths
        assert len(macd_line) == len(sample_data)
        assert len(signal_line) == len(sample_data)
        assert len(histogram) == len(sample_data)
        
        # Check that histogram = macd_line - signal_line (where both are not NaN)
        valid_mask = ~(macd_line.isna() | signal_line.isna())
        if valid_mask.any():
            np.testing.assert_array_almost_equal(
                histogram[valid_mask].values,
                (macd_line - signal_line)[valid_mask].values,
                decimal=10
            )
    
    def test_calculate_bollinger_bands(self, sample_data):
        """Test Bollinger Bands calculation."""
        indicators = TechnicalIndicators()
        
        upper, middle, lower = indicators.calculate_bollinger_bands(sample_data)
        
        # Check return types
        assert isinstance(upper, pd.Series)
        assert isinstance(middle, pd.Series)
        assert isinstance(lower, pd.Series)
        
        # Check lengths
        assert len(upper) == len(sample_data)
        assert len(middle) == len(sample_data)
        assert len(lower) == len(sample_data)
        
        # Check that upper > middle > lower (where all are not NaN)
        valid_mask = ~(upper.isna() | middle.isna() | lower.isna())
        if valid_mask.any():
            assert (upper[valid_mask] >= middle[valid_mask]).all()
            assert (middle[valid_mask] >= lower[valid_mask]).all()
    
    def test_calculate_stochastic(self, sample_data):
        """Test Stochastic oscillator calculation."""
        indicators = TechnicalIndicators()
        
        k_percent, d_percent = indicators.calculate_stochastic(sample_data)
        
        # Check return types
        assert isinstance(k_percent, pd.Series)
        assert isinstance(d_percent, pd.Series)
        
        # Check lengths
        assert len(k_percent) == len(sample_data)
        assert len(d_percent) == len(sample_data)
        
        # Stochastic should be between 0 and 100
        valid_k = k_percent.dropna()
        valid_d = d_percent.dropna()
        
        if len(valid_k) > 0:
            assert (valid_k >= 0).all()
            assert (valid_k <= 100).all()
        
        if len(valid_d) > 0:
            assert (valid_d >= 0).all()
            assert (valid_d <= 100).all()
    
    def test_calculate_moving_averages(self, sample_data):
        """Test moving averages calculation."""
        indicators = TechnicalIndicators()
        
        # Test SMA
        sma = indicators.calculate_sma(sample_data, period=20)
        assert isinstance(sma, pd.Series)
        assert len(sma) == len(sample_data)
        
        # Test EMA
        ema = indicators.calculate_ema(sample_data, period=20)
        assert isinstance(ema, pd.Series)
        assert len(ema) == len(sample_data)
        
        # EMA should react faster than SMA (more recent values have more weight)
        # This is hard to test directly, but we can check that they're different
        valid_mask = ~(sma.isna() | ema.isna())
        if valid_mask.sum() > 10:  # Need enough data points
            # They shouldn't be identical (except possibly for the first few values)
            assert not np.allclose(sma[valid_mask].values[-10:], ema[valid_mask].values[-10:])
    
    def test_find_support_resistance(self, sample_data):
        """Test support and resistance level detection."""
        indicators = TechnicalIndicators()
        
        support_levels, resistance_levels = indicators.find_support_resistance(sample_data)
        
        # Check return types
        assert isinstance(support_levels, list)
        assert isinstance(resistance_levels, list)
        
        # Check that levels are reasonable (within price range)
        price_min = sample_data['low'].min()
        price_max = sample_data['high'].max()
        
        for level in support_levels:
            assert price_min <= level <= price_max
        
        for level in resistance_levels:
            assert price_min <= level <= price_max
        
        # Support levels should generally be lower than resistance levels
        if support_levels and resistance_levels:
            avg_support = np.mean(support_levels)
            avg_resistance = np.mean(resistance_levels)
            assert avg_support <= avg_resistance
    
    def test_get_all_indicators(self, sample_data):
        """Test getting all indicators at once."""
        indicators = TechnicalIndicators()
        
        result = indicators.get_all_indicators(sample_data)
        
        # Check return type
        assert isinstance(result, dict)
        
        # Check that all expected indicators are present
        expected_keys = [
            'rsi', 'macd_line', 'macd_signal', 'macd_histogram',
            'bb_upper', 'bb_middle', 'bb_lower',
            'stoch_k', 'stoch_d',
            'sma_20', 'ema_20',
            'support_levels', 'resistance_levels'
        ]
        
        for key in expected_keys:
            assert key in result
        
        # Check that series have correct lengths
        for key, value in result.items():
            if isinstance(value, pd.Series):
                assert len(value) == len(sample_data)
            elif isinstance(value, list):
                assert isinstance(value, list)  # Support/resistance levels
    
    def test_generate_signals(self, sample_data):
        """Test signal generation."""
        indicators = TechnicalIndicators()
        
        signals = indicators.generate_signals(sample_data)
        
        # Check return type
        assert isinstance(signals, dict)
        
        # Check that all signal types are present
        expected_signals = ['rsi', 'macd', 'bollinger', 'stochastic', 'moving_average']
        
        for signal_type in expected_signals:
            assert signal_type in signals
            assert 'signal' in signals[signal_type]
            assert 'strength' in signals[signal_type]
            assert 'confidence' in signals[signal_type]
            
            # Check signal values
            signal = signals[signal_type]['signal']
            assert signal in ['BUY', 'SELL', 'NEUTRAL']
            
            # Check strength values
            strength = signals[signal_type]['strength']
            assert strength in ['VERY_WEAK', 'WEAK', 'MODERATE', 'STRONG', 'VERY_STRONG']
            
            # Check confidence values
            confidence = signals[signal_type]['confidence']
            assert 0.0 <= confidence <= 1.0
    
    def test_empty_data(self):
        """Test behavior with empty data."""
        indicators = TechnicalIndicators()
        empty_df = pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Should handle empty data gracefully
        rsi = indicators.calculate_rsi(empty_df)
        assert isinstance(rsi, pd.Series)
        assert len(rsi) == 0
        
        # Test with all indicators
        result = indicators.get_all_indicators(empty_df)
        assert isinstance(result, dict)
    
    def test_insufficient_data(self):
        """Test behavior with insufficient data."""
        indicators = TechnicalIndicators()
        
        # Create minimal data (less than required for most indicators)
        minimal_data = pd.DataFrame({
            'timestamp': pd.date_range(start='2023-01-01', periods=5, freq='1H'),
            'open': [100, 101, 102, 101, 100],
            'high': [101, 102, 103, 102, 101],
            'low': [99, 100, 101, 100, 99],
            'close': [100.5, 101.5, 102.5, 101.5, 100.5],
            'volume': [1000, 1100, 1200, 1100, 1000]
        })
        
        # Should handle insufficient data gracefully
        rsi = indicators.calculate_rsi(minimal_data)
        assert isinstance(rsi, pd.Series)
        assert len(rsi) == len(minimal_data)
        # Most values should be NaN due to insufficient data
        assert rsi.isna().sum() >= len(minimal_data) - 1
    
    def test_invalid_data(self):
        """Test behavior with invalid data."""
        indicators = TechnicalIndicators()
        
        # Test with missing columns
        invalid_df = pd.DataFrame({
            'timestamp': pd.date_range(start='2023-01-01', periods=10, freq='1H'),
            'price': [100] * 10  # Missing required columns
        })
        
        with pytest.raises((KeyError, ValueError)):
            indicators.calculate_rsi(invalid_df)
    
    def test_signal_strength_calculation(self, sample_data):
        """Test signal strength calculation logic."""
        indicators = TechnicalIndicators()
        
        # Test RSI signal strength
        # Extreme RSI values should give stronger signals
        rsi_values = pd.Series([10, 30, 50, 70, 90])  # Very oversold to very overbought
        
        for rsi_val in rsi_values:
            signal, strength, confidence = indicators._calculate_rsi_signal(rsi_val)
            
            assert signal in ['BUY', 'SELL', 'NEUTRAL']
            assert strength in ['VERY_WEAK', 'WEAK', 'MODERATE', 'STRONG', 'VERY_STRONG']
            assert 0.0 <= confidence <= 1.0
            
            # Extreme values should have higher confidence
            if rsi_val <= 20 or rsi_val >= 80:
                assert confidence >= 0.7
    
    def test_performance_with_large_dataset(self):
        """Test performance with large dataset."""
        indicators = TechnicalIndicators()
        
        # Create large dataset
        dates = pd.date_range(start='2020-01-01', periods=10000, freq='1H')
        np.random.seed(42)
        
        prices = [100.0]
        for _ in range(9999):
            change = np.random.normal(0, 0.01)
            new_price = prices[-1] * (1 + change)
            prices.append(max(new_price, 1.0))
        
        large_data = pd.DataFrame({
            'timestamp': dates,
            'open': prices[:-1] + [prices[-1]],
            'high': [p * 1.01 for p in prices],
            'low': [p * 0.99 for p in prices],
            'close': prices,
            'volume': np.random.randint(1000, 10000, 10000)
        })
        
        # Should complete in reasonable time
        import time
        start_time = time.time()
        
        result = indicators.get_all_indicators(large_data)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete within 10 seconds for 10k data points
        assert execution_time < 10.0
        assert isinstance(result, dict)
        assert len(result['rsi']) == len(large_data)


if __name__ == '__main__':
    pytest.main([__file__])

