"""
Deriv broker integration for the Telegram Trading Bot.
"""

import asyncio
import json
import websockets
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd

from loguru import logger

from .base_broker import (
    BaseBroker, AccountInfo, Position, Order, Trade, MarketData,
    OrderType, OrderSide, OrderStatus, PositionSide
)
from ...core.config import get_settings
from ...core.exceptions import DerivAPIError
from ...core.utils import generate_request_id, retry_on_exception


class DerivBroker(BaseBroker):
    """Deriv broker implementation."""
    
    def __init__(self, credentials: Dict[str, Any]):
        super().__init__(credentials)
        self.settings = get_settings()
        self.websocket = None
        self.api_token = credentials.get('api_token')
        self.app_id = self.settings.deriv.app_id
        self.api_url = self.settings.deriv.api_url
        self.request_id_counter = 0
        self.pending_requests = {}
        
        if not self.api_token:
            raise DerivAPIError("API token is required for Deriv broker")
    
    async def connect(self) -> bool:
        """Connect to Deriv WebSocket API."""
        try:
            # Connect to WebSocket
            self.websocket = await websockets.connect(
                f"{self.api_url}?app_id={self.app_id}"
            )
            
            # Authorize with API token
            auth_request = {
                "authorize": self.api_token,
                "req_id": self._get_request_id()
            }
            
            await self.websocket.send(json.dumps(auth_request))
            response = await self.websocket.recv()
            auth_response = json.loads(response)
            
            if auth_response.get('error'):
                raise DerivAPIError(f"Authorization failed: {auth_response['error']['message']}")
            
            self.is_connected = True
            logger.info("Connected to Deriv API successfully")
            
            # Start listening for responses
            asyncio.create_task(self._listen_for_responses())
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Deriv API: {e}")
            raise DerivAPIError(f"Connection failed: {e}")
    
    async def disconnect(self) -> bool:
        """Disconnect from Deriv WebSocket API."""
        try:
            if self.websocket:
                await self.websocket.close()
                self.websocket = None
            
            self.is_connected = False
            logger.info("Disconnected from Deriv API")
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting from Deriv API: {e}")
            return False
    
    async def _listen_for_responses(self):
        """Listen for WebSocket responses."""
        try:
            while self.websocket and not self.websocket.closed:
                response = await self.websocket.recv()
                data = json.loads(response)
                
                req_id = data.get('req_id')
                if req_id and req_id in self.pending_requests:
                    # Resolve pending request
                    future = self.pending_requests.pop(req_id)
                    if not future.done():
                        future.set_result(data)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info("Deriv WebSocket connection closed")
        except Exception as e:
            logger.error(f"Error in Deriv WebSocket listener: {e}")
    
    def _get_request_id(self) -> str:
        """Generate a unique request ID."""
        self.request_id_counter += 1
        return f"req_{self.request_id_counter}"
    
    async def _send_request(self, request: Dict[str, Any], timeout: float = 30.0) -> Dict[str, Any]:
        """Send a request and wait for response."""
        if not self.is_connected or not self.websocket:
            raise DerivAPIError("Not connected to Deriv API")
        
        req_id = self._get_request_id()
        request['req_id'] = req_id
        
        # Create future for response
        future = asyncio.Future()
        self.pending_requests[req_id] = future
        
        try:
            # Send request
            await self.websocket.send(json.dumps(request))
            
            # Wait for response
            response = await asyncio.wait_for(future, timeout=timeout)
            
            if response.get('error'):
                raise DerivAPIError(f"API error: {response['error']['message']}")
            
            return response
            
        except asyncio.TimeoutError:
            self.pending_requests.pop(req_id, None)
            raise DerivAPIError(f"Request timeout: {req_id}")
        except Exception as e:
            self.pending_requests.pop(req_id, None)
            raise DerivAPIError(f"Request failed: {e}")
    
    async def get_account_info(self) -> Optional[AccountInfo]:
        """Get account information."""
        try:
            # Get balance
            balance_request = {"balance": 1}
            balance_response = await self._send_request(balance_request)
            balance_data = balance_response.get('balance', {})
            
            # Get account status
            account_request = {"get_account_status": 1}
            account_response = await self._send_request(account_request)
            account_data = account_response.get('get_account_status', {})
            
            self.account_info = AccountInfo(
                account_id=account_data.get('loginid', ''),
                balance=float(balance_data.get('balance', 0)),
                equity=float(balance_data.get('balance', 0)),  # Deriv doesn't separate equity
                margin=0.0,  # Not applicable for Deriv
                free_margin=float(balance_data.get('balance', 0)),
                margin_level=0.0,  # Not applicable
                currency=balance_data.get('currency', 'USD'),
                leverage=1.0,  # Deriv uses multipliers, not leverage
                profit=0.0,  # Would need to calculate from positions
                credit=0.0
            )
            
            return self.account_info
            
        except Exception as e:
            logger.error(f"Error getting Deriv account info: {e}")
            return None
    
    async def get_positions(self) -> List[Position]:
        """Get all open positions."""
        try:
            # Get portfolio
            portfolio_request = {"portfolio": 1}
            response = await self._send_request(portfolio_request)
            portfolio_data = response.get('portfolio', {})
            
            positions = []
            contracts = portfolio_data.get('contracts', [])
            
            for contract in contracts:
                position = Position(
                    position_id=str(contract.get('contract_id', '')),
                    symbol=contract.get('symbol', ''),
                    side=PositionSide.LONG if contract.get('buy_price', 0) > 0 else PositionSide.SHORT,
                    size=float(contract.get('payout', 0)),
                    entry_price=float(contract.get('buy_price', 0)),
                    current_price=float(contract.get('current_spot', 0)),
                    unrealized_pnl=float(contract.get('profit', 0)),
                    realized_pnl=0.0,
                    margin_required=float(contract.get('buy_price', 0)),
                    open_time=datetime.fromtimestamp(contract.get('date_start', 0))
                )
                positions.append(position)
            
            return positions
            
        except Exception as e:
            logger.error(f"Error getting Deriv positions: {e}")
            return []
    
    async def get_orders(self) -> List[Order]:
        """Get all orders."""
        # Deriv doesn't have traditional pending orders like other brokers
        # Binary options are either active contracts or completed
        return []
    
    async def get_trades(self, start_time: Optional[datetime] = None, 
                        end_time: Optional[datetime] = None) -> List[Trade]:
        """Get trade history."""
        try:
            # Get profit table (trade history)
            profit_request = {
                "profit_table": 1,
                "description": 1,
                "limit": 100
            }
            
            if start_time:
                profit_request["date_from"] = int(start_time.timestamp())
            if end_time:
                profit_request["date_to"] = int(end_time.timestamp())
            
            response = await self._send_request(profit_request)
            profit_data = response.get('profit_table', {})
            
            trades = []
            transactions = profit_data.get('transactions', [])
            
            for transaction in transactions:
                trade = Trade(
                    trade_id=str(transaction.get('transaction_id', '')),
                    order_id=str(transaction.get('contract_id', '')),
                    symbol=transaction.get('symbol', ''),
                    side=OrderSide.BUY if transaction.get('action_type') == 'buy' else OrderSide.SELL,
                    size=float(transaction.get('payout', 0)),
                    price=float(transaction.get('buy_price', 0)),
                    commission=0.0,  # Deriv doesn't charge commission
                    timestamp=datetime.fromtimestamp(transaction.get('transaction_time', 0))
                )
                trades.append(trade)
            
            return trades
            
        except Exception as e:
            logger.error(f"Error getting Deriv trades: {e}")
            return []
    
    async def place_order(self, symbol: str, side: OrderSide, size: float,
                         order_type: OrderType = OrderType.MARKET,
                         price: Optional[float] = None,
                         stop_loss: Optional[float] = None,
                         take_profit: Optional[float] = None) -> Optional[Order]:
        """Place a binary options contract."""
        try:
            # For Deriv, we place binary options contracts
            # Convert parameters to Deriv format
            contract_type = "CALL" if side == OrderSide.BUY else "PUT"
            
            buy_request = {
                "buy": 1,
                "price": size,  # In Deriv, this is the stake amount
                "parameters": {
                    "contract_type": contract_type,
                    "symbol": self.format_symbol(symbol),
                    "duration": 5,  # 5 minutes default
                    "duration_unit": "m",
                    "amount": size,
                    "basis": "stake"
                }
            }
            
            response = await self._send_request(buy_request)
            buy_data = response.get('buy', {})
            
            if buy_data:
                order = Order(
                    order_id=str(buy_data.get('contract_id', '')),
                    symbol=symbol,
                    side=side,
                    type=OrderType.MARKET,
                    size=size,
                    price=float(buy_data.get('buy_price', 0)),
                    stop_price=None,
                    status=OrderStatus.FILLED,
                    filled_size=size,
                    remaining_size=0.0,
                    average_fill_price=float(buy_data.get('buy_price', 0)),
                    created_time=datetime.now(),
                    updated_time=datetime.now()
                )
                return order
            
            return None
            
        except Exception as e:
            logger.error(f"Error placing Deriv order: {e}")
            return None
    
    async def modify_order(self, order_id: str, price: Optional[float] = None,
                          size: Optional[float] = None,
                          stop_loss: Optional[float] = None,
                          take_profit: Optional[float] = None) -> bool:
        """Modify an order (not supported for binary options)."""
        logger.warning("Order modification not supported for Deriv binary options")
        return False
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order (not supported for binary options)."""
        logger.warning("Order cancellation not supported for Deriv binary options")
        return False
    
    async def close_position(self, position_id: str, size: Optional[float] = None) -> bool:
        """Close a position (sell contract)."""
        try:
            sell_request = {
                "sell": position_id,
                "price": 0  # Market price
            }
            
            response = await self._send_request(sell_request)
            sell_data = response.get('sell', {})
            
            return bool(sell_data)
            
        except Exception as e:
            logger.error(f"Error closing Deriv position: {e}")
            return False
    
    async def get_market_data(self, symbol: str) -> Optional[MarketData]:
        """Get current market data."""
        try:
            tick_request = {
                "ticks": self.format_symbol(symbol),
                "subscribe": 0  # Get single tick, don't subscribe
            }
            
            response = await self._send_request(tick_request)
            tick_data = response.get('tick', {})
            
            if tick_data:
                return MarketData(
                    symbol=symbol,
                    bid=float(tick_data.get('bid', 0)),
                    ask=float(tick_data.get('ask', 0)),
                    last=float(tick_data.get('quote', 0)),
                    volume=0.0,  # Not provided by Deriv
                    timestamp=datetime.fromtimestamp(tick_data.get('epoch', 0))
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting Deriv market data: {e}")
            return None
    
    async def get_ohlc_data(self, symbol: str, timeframe: str, 
                           count: int = 100) -> Optional[pd.DataFrame]:
        """Get OHLC data."""
        try:
            # Convert timeframe to Deriv format
            granularity = self._convert_timeframe(timeframe)
            
            # Calculate start time
            end_time = datetime.now()
            start_time = end_time - timedelta(seconds=granularity * count)
            
            candles_request = {
                "ticks_history": self.format_symbol(symbol),
                "adjust_start_time": 1,
                "count": count,
                "end": "latest",
                "start": int(start_time.timestamp()),
                "style": "candles",
                "granularity": granularity
            }
            
            response = await self._send_request(candles_request)
            candles_data = response.get('candles', [])
            
            if candles_data:
                df_data = []
                for candle in candles_data:
                    df_data.append({
                        'timestamp': pd.to_datetime(candle['epoch'], unit='s'),
                        'open': float(candle['open']),
                        'high': float(candle['high']),
                        'low': float(candle['low']),
                        'close': float(candle['close']),
                        'volume': 0.0  # Not provided by Deriv
                    })
                
                df = pd.DataFrame(df_data)
                return df
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting Deriv OHLC data: {e}")
            return None
    
    def _convert_timeframe(self, timeframe: str) -> int:
        """Convert timeframe to Deriv granularity (seconds)."""
        mapping = {
            '1m': 60,
            '5m': 300,
            '15m': 900,
            '30m': 1800,
            '1h': 3600,
            '4h': 14400,
            '1d': 86400
        }
        return mapping.get(timeframe, 300)  # Default to 5 minutes
    
    async def get_symbols(self) -> List[str]:
        """Get available trading symbols."""
        try:
            symbols_request = {"active_symbols": "brief"}
            response = await self._send_request(symbols_request)
            symbols_data = response.get('active_symbols', [])
            
            symbols = []
            for symbol_info in symbols_data:
                if symbol_info.get('exchange_is_open'):
                    symbols.append(symbol_info.get('symbol', ''))
            
            return symbols
            
        except Exception as e:
            logger.error(f"Error getting Deriv symbols: {e}")
            return []
    
    def validate_symbol(self, symbol: str) -> bool:
        """Validate if symbol is tradeable."""
        # Basic validation - should be enhanced with actual symbol list
        common_symbols = [
            'R_10', 'R_25', 'R_50', 'R_75', 'R_100',  # Volatility indices
            'frxEURUSD', 'frxGBPUSD', 'frxUSDJPY',    # Forex
            'RDBULL', 'RDBEAR',                        # Bull/Bear indices
        ]
        return symbol in common_symbols
    
    def format_symbol(self, symbol: str) -> str:
        """Format symbol for Deriv API."""
        # Convert common symbols to Deriv format
        symbol_mapping = {
            'EURUSD': 'frxEURUSD',
            'GBPUSD': 'frxGBPUSD',
            'USDJPY': 'frxUSDJPY',
            'USDCHF': 'frxUSDCHF',
            'AUDUSD': 'frxAUDUSD',
            'USDCAD': 'frxUSDCAD',
            'NZDUSD': 'frxNZDUSD'
        }
        
        return symbol_mapping.get(symbol.upper(), symbol)
    
    def calculate_margin_required(self, symbol: str, size: float) -> float:
        """Calculate margin required (stake amount for binary options)."""
        return size  # For binary options, margin = stake
    
    def get_minimum_trade_size(self, symbol: str) -> float:
        """Get minimum trade size."""
        return 1.0  # Minimum stake is usually $1
    
    def get_maximum_trade_size(self, symbol: str) -> float:
        """Get maximum trade size."""
        return 50000.0  # Maximum stake varies by account type
    
    def is_market_open(self, symbol: str) -> bool:
        """Check if market is open."""
        # Deriv markets are generally open 24/7 except weekends for some symbols
        return True
    
    def get_trading_fees(self, symbol: str) -> Dict[str, float]:
        """Get trading fees."""
        return {
            'commission': 0.0,  # No commission for binary options
            'spread': 0.0,      # Spread is built into the payout
            'swap_long': 0.0,   # No swap for binary options
            'swap_short': 0.0
        }

