"""
Tests for broker integrations.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import pandas as pd

from trading.brokers.base_broker import BaseBroker, OrderType, OrderSide, OrderStatus
from trading.brokers.deriv_broker import DerivBroker
from trading.brokers.binance_broker import BinanceBroker
from core.exceptions import DerivAPIError, BinanceAPIError


class TestBaseBroker:
    """Test cases for base broker functionality."""
    
    def test_calculate_position_size(self):
        """Test position size calculation."""
        # Create a mock broker
        broker = Mock(spec=BaseBroker)
        broker.calculate_position_size = BaseBroker.calculate_position_size.__get__(broker)
        
        # Test normal calculation
        account_balance = 10000.0
        risk_percentage = 2.0
        entry_price = 100.0
        stop_loss_price = 95.0
        
        position_size = broker.calculate_position_size(
            account_balance, risk_percentage, entry_price, stop_loss_price
        )
        
        expected_size = (10000 * 0.02) / (100 - 95)  # 200 / 5 = 40
        assert position_size == expected_size
        
        # Test with zero stop loss difference
        position_size_zero = broker.calculate_position_size(
            account_balance, risk_percentage, entry_price, entry_price
        )
        assert position_size_zero == 0
    
    def test_validate_order_parameters(self):
        """Test order parameter validation."""
        # Create a mock broker with required methods
        broker = Mock(spec=BaseBroker)
        broker.validate_symbol = Mock(return_value=True)
        broker.get_minimum_trade_size = Mock(return_value=0.01)
        broker.get_maximum_trade_size = Mock(return_value=1000.0)
        broker.validate_order_parameters = BaseBroker.validate_order_parameters.__get__(broker)
        
        # Test valid parameters
        is_valid, message = broker.validate_order_parameters(
            "EURUSD", OrderSide.BUY, 1.0, OrderType.MARKET
        )
        assert is_valid is True
        assert message == "Valid"
        
        # Test invalid symbol
        broker.validate_symbol.return_value = False
        is_valid, message = broker.validate_order_parameters(
            "INVALID", OrderSide.BUY, 1.0, OrderType.MARKET
        )
        assert is_valid is False
        assert "Invalid symbol" in message
        
        # Reset symbol validation
        broker.validate_symbol.return_value = True
        
        # Test size too small
        is_valid, message = broker.validate_order_parameters(
            "EURUSD", OrderSide.BUY, 0.001, OrderType.MARKET
        )
        assert is_valid is False
        assert "too small" in message
        
        # Test size too large
        is_valid, message = broker.validate_order_parameters(
            "EURUSD", OrderSide.BUY, 2000.0, OrderType.MARKET
        )
        assert is_valid is False
        assert "too large" in message
        
        # Test limit order without price
        is_valid, message = broker.validate_order_parameters(
            "EURUSD", OrderSide.BUY, 1.0, OrderType.LIMIT
        )
        assert is_valid is False
        assert "Price required" in message


class TestDerivBroker:
    """Test cases for Deriv broker."""
    
    @pytest.fixture
    def deriv_credentials(self):
        """Sample Deriv credentials."""
        return {
            'api_token': 'test_token_123'
        }
    
    def test_initialization(self, deriv_credentials):
        """Test Deriv broker initialization."""
        broker = DerivBroker(deriv_credentials)
        
        assert broker.api_token == 'test_token_123'
        assert broker.is_connected is False
        assert broker.websocket is None
    
    def test_initialization_without_token(self):
        """Test initialization without API token."""
        with pytest.raises(DerivAPIError):
            DerivBroker({})
    
    @pytest.mark.asyncio
    async def test_connect_success(self, deriv_credentials):
        """Test successful connection to Deriv."""
        broker = DerivBroker(deriv_credentials)
        
        # Mock websocket connection
        mock_websocket = AsyncMock()
        mock_websocket.send = AsyncMock()
        mock_websocket.recv = AsyncMock(return_value='{"authorize": {"loginid": "test"}}')
        
        with patch('websockets.connect', return_value=mock_websocket):
            with patch.object(broker, '_listen_for_responses'):
                result = await broker.connect()
                
                assert result is True
                assert broker.is_connected is True
                assert broker.websocket == mock_websocket
    
    @pytest.mark.asyncio
    async def test_connect_auth_failure(self, deriv_credentials):
        """Test connection with authentication failure."""
        broker = DerivBroker(deriv_credentials)
        
        # Mock websocket connection with auth error
        mock_websocket = AsyncMock()
        mock_websocket.send = AsyncMock()
        mock_websocket.recv = AsyncMock(
            return_value='{"error": {"message": "Invalid token"}}'
        )
        
        with patch('websockets.connect', return_value=mock_websocket):
            with pytest.raises(DerivAPIError):
                await broker.connect()
    
    @pytest.mark.asyncio
    async def test_send_request(self, deriv_credentials):
        """Test sending API requests."""
        broker = DerivBroker(deriv_credentials)
        broker.is_connected = True
        broker.websocket = AsyncMock()
        
        # Mock successful response
        test_response = {"balance": {"balance": 1000.0, "currency": "USD"}}
        
        async def mock_wait_for(future, timeout):
            future.set_result(test_response)
            return test_response
        
        with patch('asyncio.wait_for', side_effect=mock_wait_for):
            response = await broker._send_request({"balance": 1})
            
            assert response == test_response
            broker.websocket.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_account_info(self, deriv_credentials):
        """Test getting account information."""
        broker = DerivBroker(deriv_credentials)
        
        # Mock API responses
        balance_response = {"balance": {"balance": 1000.0, "currency": "USD"}}
        account_response = {"get_account_status": {"loginid": "test123"}}
        
        broker._send_request = AsyncMock(side_effect=[balance_response, account_response])
        
        account_info = await broker.get_account_info()
        
        assert account_info is not None
        assert account_info.balance == 1000.0
        assert account_info.currency == "USD"
        assert account_info.account_id == "test123"
    
    def test_format_symbol(self, deriv_credentials):
        """Test symbol formatting for Deriv."""
        broker = DerivBroker(deriv_credentials)
        
        # Test common forex pairs
        assert broker.format_symbol("EURUSD") == "frxEURUSD"
        assert broker.format_symbol("GBPUSD") == "frxGBPUSD"
        
        # Test unknown symbol (should return as-is)
        assert broker.format_symbol("UNKNOWN") == "UNKNOWN"
    
    def test_validate_symbol(self, deriv_credentials):
        """Test symbol validation."""
        broker = DerivBroker(deriv_credentials)
        
        # Test valid symbols
        assert broker.validate_symbol("R_10") is True
        assert broker.validate_symbol("frxEURUSD") is True
        
        # Test invalid symbol
        assert broker.validate_symbol("INVALID") is False


class TestBinanceBroker:
    """Test cases for Binance broker."""
    
    @pytest.fixture
    def binance_credentials(self):
        """Sample Binance credentials."""
        return {
            'api_key': 'test_api_key',
            'api_secret': 'test_api_secret',
            'testnet': True
        }
    
    def test_initialization(self, binance_credentials):
        """Test Binance broker initialization."""
        broker = BinanceBroker(binance_credentials)
        
        assert broker.api_key == 'test_api_key'
        assert broker.api_secret == 'test_api_secret'
        assert broker.testnet is True
        assert broker.is_connected is False
    
    def test_initialization_without_credentials(self):
        """Test initialization without credentials."""
        with pytest.raises(BinanceAPIError):
            BinanceBroker({})
    
    def test_generate_signature(self, binance_credentials):
        """Test signature generation."""
        broker = BinanceBroker(binance_credentials)
        
        query_string = "symbol=BTCUSDT&side=BUY&type=MARKET&quantity=1"
        signature = broker._generate_signature(query_string)
        
        assert isinstance(signature, str)
        assert len(signature) == 64  # SHA256 hex digest length
    
    @pytest.mark.asyncio
    async def test_make_request_success(self, binance_credentials):
        """Test successful API request."""
        broker = BinanceBroker(binance_credentials)
        
        # Mock aiohttp session
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"status": "success"})
        
        mock_session = AsyncMock()
        mock_session.request = AsyncMock(return_value=mock_response)
        broker.session = mock_session
        
        result = await broker._make_request('GET', '/test')
        
        assert result == {"status": "success"}
        mock_session.request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_make_request_error(self, binance_credentials):
        """Test API request with error."""
        broker = BinanceBroker(binance_credentials)
        
        # Mock aiohttp session with error response
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.text = AsyncMock(return_value="Bad Request")
        
        mock_session = AsyncMock()
        mock_session.request = AsyncMock(return_value=mock_response)
        broker.session = mock_session
        
        result = await broker._make_request('GET', '/test')
        
        assert result is None
    
    def test_convert_order_type(self, binance_credentials):
        """Test order type conversion."""
        broker = BinanceBroker(binance_credentials)
        
        # Test internal to Binance conversion
        assert broker._convert_internal_order_type(OrderType.MARKET) == 'MARKET'
        assert broker._convert_internal_order_type(OrderType.LIMIT) == 'LIMIT'
        assert broker._convert_internal_order_type(OrderType.STOP) == 'STOP_MARKET'
        
        # Test Binance to internal conversion
        assert broker._convert_order_type('MARKET') == OrderType.MARKET
        assert broker._convert_order_type('LIMIT') == OrderType.LIMIT
        assert broker._convert_order_type('STOP_MARKET') == OrderType.STOP
    
    def test_convert_order_status(self, binance_credentials):
        """Test order status conversion."""
        broker = BinanceBroker(binance_credentials)
        
        assert broker._convert_order_status('NEW') == OrderStatus.PENDING
        assert broker._convert_order_status('FILLED') == OrderStatus.FILLED
        assert broker._convert_order_status('CANCELED') == OrderStatus.CANCELLED
        assert broker._convert_order_status('REJECTED') == OrderStatus.REJECTED
    
    def test_format_symbol(self, binance_credentials):
        """Test symbol formatting for Binance."""
        broker = BinanceBroker(binance_credentials)
        
        # Test adding USDT suffix
        assert broker.format_symbol("BTC") == "BTCUSDT"
        assert broker.format_symbol("ETH") == "ETHUSDT"
        
        # Test symbols that already have suffix
        assert broker.format_symbol("BTCUSDT") == "BTCUSDT"
        assert broker.format_symbol("ETHBTC") == "ETHBTC"
    
    def test_validate_symbol(self, binance_credentials):
        """Test symbol validation."""
        broker = BinanceBroker(binance_credentials)
        
        # Test valid symbols
        assert broker.validate_symbol("BTCUSDT") is True
        assert broker.validate_symbol("ETHBTC") is True
        
        # Test invalid symbols
        assert broker.validate_symbol("INVALID") is False
        assert broker.validate_symbol("") is False
    
    @pytest.mark.asyncio
    async def test_get_account_info(self, binance_credentials):
        """Test getting account information."""
        broker = BinanceBroker(binance_credentials)
        
        # Mock API response
        account_data = {
            "accountType": "SPOT",
            "balances": [
                {"asset": "USDT", "free": "1000.0", "locked": "0.0"},
                {"asset": "BTC", "free": "0.1", "locked": "0.0"}
            ]
        }
        
        broker._make_request = AsyncMock(return_value=account_data)
        
        account_info = await broker.get_account_info()
        
        assert account_info is not None
        assert account_info.balance == 1000.0
        assert account_info.currency == "USDT"


class TestBrokerIntegration:
    """Integration tests for broker functionality."""
    
    @pytest.mark.asyncio
    async def test_broker_lifecycle(self):
        """Test complete broker lifecycle."""
        # This would be an integration test with actual broker APIs
        # For now, we'll test with mocks
        
        credentials = {'api_token': 'test_token'}
        broker = DerivBroker(credentials)
        
        # Mock all external dependencies
        with patch.object(broker, 'connect', return_value=True):
            with patch.object(broker, 'get_account_info') as mock_account:
                with patch.object(broker, 'disconnect', return_value=True):
                    
                    # Test connection
                    connected = await broker.connect()
                    assert connected is True
                    
                    # Test account info
                    mock_account.return_value = Mock(balance=1000.0)
                    account = await broker.get_account_info()
                    assert account.balance == 1000.0
                    
                    # Test disconnection
                    disconnected = await broker.disconnect()
                    assert disconnected is True
    
    def test_broker_factory(self):
        """Test broker factory pattern."""
        def create_broker(broker_type: str, credentials: dict):
            """Factory function for creating brokers."""
            if broker_type == 'deriv':
                return DerivBroker(credentials)
            elif broker_type == 'binance':
                return BinanceBroker(credentials)
            else:
                raise ValueError(f"Unknown broker type: {broker_type}")
        
        # Test Deriv creation
        deriv_broker = create_broker('deriv', {'api_token': 'test'})
        assert isinstance(deriv_broker, DerivBroker)
        
        # Test Binance creation
        binance_broker = create_broker('binance', {
            'api_key': 'test_key',
            'api_secret': 'test_secret'
        })
        assert isinstance(binance_broker, BinanceBroker)
        
        # Test unknown broker
        with pytest.raises(ValueError):
            create_broker('unknown', {})


if __name__ == '__main__':
    pytest.main([__file__])

