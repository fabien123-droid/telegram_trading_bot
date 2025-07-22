"""
Binance broker integration for the Telegram Trading Bot.
"""

import asyncio
import hashlib
import hmac
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
import aiohttp

from loguru import logger

from .base_broker import (
    BaseBroker, AccountInfo, Position, Order, Trade, MarketData,
    OrderType, OrderSide, OrderStatus, PositionSide
)
from ...core.config import get_settings
from ...core.exceptions import BinanceAPIError
from ...core.utils import retry_on_exception, rate_limit


class BinanceBroker(BaseBroker):
    """Binance broker implementation."""
    
    def __init__(self, credentials: Dict[str, Any]):
        super().__init__(credentials)
        self.settings = get_settings()
        self.api_key = credentials.get('api_key')
        self.api_secret = credentials.get('api_secret')
        self.testnet = credentials.get('testnet', True)
        
        # API endpoints
        if self.testnet:
            self.base_url = "https://testnet.binance.vision/api/v3"
            self.futures_url = "https://testnet.binancefuture.com/fapi/v1"
        else:
            self.base_url = "https://api.binance.com/api/v3"
            self.futures_url = "https://fapi.binance.com/fapi/v1"
        
        self.session = None
        
        if not self.api_key or not self.api_secret:
            raise BinanceAPIError("API key and secret are required for Binance broker")
    
    async def connect(self) -> bool:
        """Connect to Binance API."""
        try:
            self.session = aiohttp.ClientSession()
            
            # Test connectivity
            test_response = await self._make_request('GET', '/ping')
            if test_response is not None:
                self.is_connected = True
                logger.info("Connected to Binance API successfully")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to connect to Binance API: {e}")
            raise BinanceAPIError(f"Connection failed: {e}")
    
    async def disconnect(self) -> bool:
        """Disconnect from Binance API."""
        try:
            if self.session:
                await self.session.close()
                self.session = None
            
            self.is_connected = False
            logger.info("Disconnected from Binance API")
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting from Binance API: {e}")
            return False
    
    def _generate_signature(self, query_string: str) -> str:
        """Generate signature for authenticated requests."""
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    async def _make_request(self, method: str, endpoint: str, params: Dict = None, 
                           signed: bool = False, futures: bool = False) -> Optional[Dict]:
        """Make HTTP request to Binance API."""
        if not self.session:
            raise BinanceAPIError("Not connected to Binance API")
        
        base_url = self.futures_url if futures else self.base_url
        url = f"{base_url}{endpoint}"
        
        if params is None:
            params = {}
        
        headers = {}
        if self.api_key:
            headers['X-MBX-APIKEY'] = self.api_key
        
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            params['signature'] = self._generate_signature(query_string)
        
        try:
            async with self.session.request(method, url, params=params, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"Binance API error {response.status}: {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Binance API request failed: {e}")
            return None
    
    @retry_on_exception(max_retries=3)
    @rate_limit(calls_per_second=10.0)
    async def get_account_info(self) -> Optional[AccountInfo]:
        """Get account information."""
        try:
            # Get spot account info
            account_data = await self._make_request('GET', '/account', signed=True)
            
            if not account_data:
                return None
            
            # Calculate balances
            total_balance = 0.0
            for balance in account_data.get('balances', []):
                if balance['asset'] == 'USDT':
                    total_balance = float(balance['free']) + float(balance['locked'])
                    break
            
            self.account_info = AccountInfo(
                account_id=str(account_data.get('accountType', '')),
                balance=total_balance,
                equity=total_balance,
                margin=0.0,
                free_margin=total_balance,
                margin_level=0.0,
                currency='USDT',
                leverage=1.0,
                profit=0.0,
                credit=0.0
            )
            
            return self.account_info
            
        except Exception as e:
            logger.error(f"Error getting Binance account info: {e}")
            return None
    
    async def get_positions(self) -> List[Position]:
        """Get all open positions (futures only)."""
        try:
            # Get futures positions
            positions_data = await self._make_request('GET', '/positionRisk', signed=True, futures=True)
            
            if not positions_data:
                return []
            
            positions = []
            for pos_data in positions_data:
                position_amt = float(pos_data.get('positionAmt', 0))
                
                if position_amt != 0:  # Only include non-zero positions
                    position = Position(
                        position_id=pos_data.get('symbol', ''),
                        symbol=pos_data.get('symbol', ''),
                        side=PositionSide.LONG if position_amt > 0 else PositionSide.SHORT,
                        size=abs(position_amt),
                        entry_price=float(pos_data.get('entryPrice', 0)),
                        current_price=float(pos_data.get('markPrice', 0)),
                        unrealized_pnl=float(pos_data.get('unRealizedProfit', 0)),
                        realized_pnl=0.0,
                        margin_required=float(pos_data.get('isolatedMargin', 0)),
                        open_time=datetime.now()  # Binance doesn't provide open time in this endpoint
                    )
                    positions.append(position)
            
            return positions
            
        except Exception as e:
            logger.error(f"Error getting Binance positions: {e}")
            return []
    
    async def get_orders(self) -> List[Order]:
        """Get all orders."""
        try:
            # Get open orders
            orders_data = await self._make_request('GET', '/openOrders', signed=True)
            
            if not orders_data:
                return []
            
            orders = []
            for order_data in orders_data:
                order = Order(
                    order_id=str(order_data.get('orderId', '')),
                    symbol=order_data.get('symbol', ''),
                    side=OrderSide.BUY if order_data.get('side') == 'BUY' else OrderSide.SELL,
                    type=self._convert_order_type(order_data.get('type', '')),
                    size=float(order_data.get('origQty', 0)),
                    price=float(order_data.get('price', 0)) if order_data.get('price') else None,
                    stop_price=float(order_data.get('stopPrice', 0)) if order_data.get('stopPrice') else None,
                    status=self._convert_order_status(order_data.get('status', '')),
                    filled_size=float(order_data.get('executedQty', 0)),
                    remaining_size=float(order_data.get('origQty', 0)) - float(order_data.get('executedQty', 0)),
                    average_fill_price=float(order_data.get('price', 0)) if order_data.get('executedQty', 0) > 0 else None,
                    created_time=datetime.fromtimestamp(order_data.get('time', 0) / 1000),
                    updated_time=datetime.fromtimestamp(order_data.get('updateTime', 0) / 1000)
                )
                orders.append(order)
            
            return orders
            
        except Exception as e:
            logger.error(f"Error getting Binance orders: {e}")
            return []
    
    def _convert_order_type(self, binance_type: str) -> OrderType:
        """Convert Binance order type to internal type."""
        mapping = {
            'MARKET': OrderType.MARKET,
            'LIMIT': OrderType.LIMIT,
            'STOP': OrderType.STOP,
            'STOP_MARKET': OrderType.STOP,
            'TAKE_PROFIT': OrderType.LIMIT,
            'TAKE_PROFIT_MARKET': OrderType.MARKET
        }
        return mapping.get(binance_type, OrderType.MARKET)
    
    def _convert_order_status(self, binance_status: str) -> OrderStatus:
        """Convert Binance order status to internal status."""
        mapping = {
            'NEW': OrderStatus.PENDING,
            'PARTIALLY_FILLED': OrderStatus.PARTIALLY_FILLED,
            'FILLED': OrderStatus.FILLED,
            'CANCELED': OrderStatus.CANCELLED,
            'REJECTED': OrderStatus.REJECTED,
            'EXPIRED': OrderStatus.CANCELLED
        }
        return mapping.get(binance_status, OrderStatus.PENDING)
    
    async def get_trades(self, start_time: Optional[datetime] = None, 
                        end_time: Optional[datetime] = None) -> List[Trade]:
        """Get trade history."""
        try:
            params = {}
            if start_time:
                params['startTime'] = int(start_time.timestamp() * 1000)
            if end_time:
                params['endTime'] = int(end_time.timestamp() * 1000)
            
            trades_data = await self._make_request('GET', '/myTrades', params=params, signed=True)
            
            if not trades_data:
                return []
            
            trades = []
            for trade_data in trades_data:
                trade = Trade(
                    trade_id=str(trade_data.get('id', '')),
                    order_id=str(trade_data.get('orderId', '')),
                    symbol=trade_data.get('symbol', ''),
                    side=OrderSide.BUY if trade_data.get('isBuyer') else OrderSide.SELL,
                    size=float(trade_data.get('qty', 0)),
                    price=float(trade_data.get('price', 0)),
                    commission=float(trade_data.get('commission', 0)),
                    timestamp=datetime.fromtimestamp(trade_data.get('time', 0) / 1000)
                )
                trades.append(trade)
            
            return trades
            
        except Exception as e:
            logger.error(f"Error getting Binance trades: {e}")
            return []
    
    async def place_order(self, symbol: str, side: OrderSide, size: float,
                         order_type: OrderType = OrderType.MARKET,
                         price: Optional[float] = None,
                         stop_loss: Optional[float] = None,
                         take_profit: Optional[float] = None) -> Optional[Order]:
        """Place a trading order."""
        try:
            # Validate parameters
            is_valid, error_msg = self.validate_order_parameters(symbol, side, size, order_type, price)
            if not is_valid:
                logger.error(f"Invalid order parameters: {error_msg}")
                return None
            
            # Prepare order parameters
            params = {
                'symbol': self.format_symbol(symbol),
                'side': 'BUY' if side == OrderSide.BUY else 'SELL',
                'type': self._convert_internal_order_type(order_type),
                'quantity': str(size)
            }
            
            if order_type == OrderType.LIMIT and price:
                params['price'] = str(price)
                params['timeInForce'] = 'GTC'  # Good Till Cancelled
            
            # Place the order
            order_data = await self._make_request('POST', '/order', params=params, signed=True)
            
            if not order_data:
                return None
            
            order = Order(
                order_id=str(order_data.get('orderId', '')),
                symbol=symbol,
                side=side,
                type=order_type,
                size=size,
                price=price,
                stop_price=None,
                status=self._convert_order_status(order_data.get('status', '')),
                filled_size=float(order_data.get('executedQty', 0)),
                remaining_size=size - float(order_data.get('executedQty', 0)),
                average_fill_price=None,
                created_time=datetime.fromtimestamp(order_data.get('transactTime', 0) / 1000),
                updated_time=datetime.fromtimestamp(order_data.get('transactTime', 0) / 1000)
            )
            
            # Place stop loss and take profit orders if specified
            if stop_loss or take_profit:
                await self._place_conditional_orders(order.order_id, symbol, side, size, stop_loss, take_profit)
            
            return order
            
        except Exception as e:
            logger.error(f"Error placing Binance order: {e}")
            return None
    
    def _convert_internal_order_type(self, order_type: OrderType) -> str:
        """Convert internal order type to Binance type."""
        mapping = {
            OrderType.MARKET: 'MARKET',
            OrderType.LIMIT: 'LIMIT',
            OrderType.STOP: 'STOP_MARKET',
            OrderType.STOP_LIMIT: 'STOP'
        }
        return mapping.get(order_type, 'MARKET')
    
    async def _place_conditional_orders(self, parent_order_id: str, symbol: str, side: OrderSide, 
                                       size: float, stop_loss: Optional[float], take_profit: Optional[float]):
        """Place stop loss and take profit orders."""
        try:
            opposite_side = OrderSide.SELL if side == OrderSide.BUY else OrderSide.BUY
            
            if stop_loss:
                sl_params = {
                    'symbol': self.format_symbol(symbol),
                    'side': 'SELL' if opposite_side == OrderSide.SELL else 'BUY',
                    'type': 'STOP_MARKET',
                    'quantity': str(size),
                    'stopPrice': str(stop_loss)
                }
                await self._make_request('POST', '/order', params=sl_params, signed=True)
            
            if take_profit:
                tp_params = {
                    'symbol': self.format_symbol(symbol),
                    'side': 'SELL' if opposite_side == OrderSide.SELL else 'BUY',
                    'type': 'TAKE_PROFIT_MARKET',
                    'quantity': str(size),
                    'stopPrice': str(take_profit)
                }
                await self._make_request('POST', '/order', params=tp_params, signed=True)
                
        except Exception as e:
            logger.error(f"Error placing conditional orders: {e}")
    
    async def modify_order(self, order_id: str, price: Optional[float] = None,
                          size: Optional[float] = None,
                          stop_loss: Optional[float] = None,
                          take_profit: Optional[float] = None) -> bool:
        """Modify an order (cancel and replace)."""
        try:
            # Get original order
            order = await self.get_order_by_id(order_id)
            if not order:
                return False
            
            # Cancel original order
            if not await self.cancel_order(order_id):
                return False
            
            # Place new order with modified parameters
            new_price = price if price is not None else order.price
            new_size = size if size is not None else order.size
            
            new_order = await self.place_order(
                order.symbol, order.side, new_size, order.type, new_price, stop_loss, take_profit
            )
            
            return new_order is not None
            
        except Exception as e:
            logger.error(f"Error modifying Binance order: {e}")
            return False
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        try:
            # Get order details first to get symbol
            order = await self.get_order_by_id(order_id)
            if not order:
                return False
            
            params = {
                'symbol': self.format_symbol(order.symbol),
                'orderId': order_id
            }
            
            result = await self._make_request('DELETE', '/order', params=params, signed=True)
            return result is not None
            
        except Exception as e:
            logger.error(f"Error cancelling Binance order: {e}")
            return False
    
    async def close_position(self, position_id: str, size: Optional[float] = None) -> bool:
        """Close a position."""
        try:
            # For spot trading, we need to place a market order in opposite direction
            position = await self.get_position_by_symbol(position_id)  # position_id is symbol for Binance
            if not position:
                return False
            
            close_side = OrderSide.SELL if position.side == PositionSide.LONG else OrderSide.BUY
            close_size = size if size is not None else position.size
            
            order = await self.place_order(position.symbol, close_side, close_size, OrderType.MARKET)
            return order is not None
            
        except Exception as e:
            logger.error(f"Error closing Binance position: {e}")
            return False
    
    async def get_market_data(self, symbol: str) -> Optional[MarketData]:
        """Get current market data."""
        try:
            params = {'symbol': self.format_symbol(symbol)}
            ticker_data = await self._make_request('GET', '/ticker/bookTicker', params=params)
            
            if not ticker_data:
                return None
            
            return MarketData(
                symbol=symbol,
                bid=float(ticker_data.get('bidPrice', 0)),
                ask=float(ticker_data.get('askPrice', 0)),
                last=float(ticker_data.get('bidPrice', 0)),  # Use bid as last price approximation
                volume=0.0,  # Would need separate call for volume
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error getting Binance market data: {e}")
            return None
    
    async def get_ohlc_data(self, symbol: str, timeframe: str, 
                           count: int = 100) -> Optional[pd.DataFrame]:
        """Get OHLC data."""
        try:
            params = {
                'symbol': self.format_symbol(symbol),
                'interval': self._convert_timeframe(timeframe),
                'limit': count
            }
            
            klines_data = await self._make_request('GET', '/klines', params=params)
            
            if not klines_data:
                return None
            
            df_data = []
            for kline in klines_data:
                df_data.append({
                    'timestamp': pd.to_datetime(kline[0], unit='ms'),
                    'open': float(kline[1]),
                    'high': float(kline[2]),
                    'low': float(kline[3]),
                    'close': float(kline[4]),
                    'volume': float(kline[5])
                })
            
            df = pd.DataFrame(df_data)
            return df
            
        except Exception as e:
            logger.error(f"Error getting Binance OHLC data: {e}")
            return None
    
    def _convert_timeframe(self, timeframe: str) -> str:
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
    
    async def get_symbols(self) -> List[str]:
        """Get available trading symbols."""
        try:
            exchange_info = await self._make_request('GET', '/exchangeInfo')
            
            if not exchange_info:
                return []
            
            symbols = []
            for symbol_info in exchange_info.get('symbols', []):
                if symbol_info.get('status') == 'TRADING':
                    symbols.append(symbol_info.get('symbol', ''))
            
            return symbols
            
        except Exception as e:
            logger.error(f"Error getting Binance symbols: {e}")
            return []
    
    def validate_symbol(self, symbol: str) -> bool:
        """Validate if symbol is tradeable."""
        # Basic validation - should be enhanced with actual symbol list
        return symbol.endswith('USDT') or symbol.endswith('BTC') or symbol.endswith('ETH')
    
    def format_symbol(self, symbol: str) -> str:
        """Format symbol for Binance API."""
        # Convert common symbols to Binance format
        symbol = symbol.upper().replace('/', '').replace('-', '')
        
        # Add USDT if not present
        if not any(symbol.endswith(quote) for quote in ['USDT', 'BTC', 'ETH', 'BNB']):
            symbol += 'USDT'
        
        return symbol
    
    def calculate_margin_required(self, symbol: str, size: float) -> float:
        """Calculate margin required."""
        # For spot trading, margin = size * price
        # This is a simplified calculation
        return size * 100  # Assuming average price of 100
    
    def get_minimum_trade_size(self, symbol: str) -> float:
        """Get minimum trade size."""
        return 0.001  # Minimum varies by symbol
    
    def get_maximum_trade_size(self, symbol: str) -> float:
        """Get maximum trade size."""
        return 1000000.0  # Maximum varies by symbol and account
    
    def get_trading_fees(self, symbol: str) -> Dict[str, float]:
        """Get trading fees."""
        return {
            'commission': 0.001,  # 0.1% default
            'spread': 0.0001,     # Varies by symbol
            'swap_long': 0.0,     # Not applicable for spot
            'swap_short': 0.0
        }

