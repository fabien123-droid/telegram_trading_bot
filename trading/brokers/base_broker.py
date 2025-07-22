"""
Base broker class for the Telegram Trading Bot.
Defines the interface that all broker implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import pandas as pd


class OrderType(Enum):
    """Order types."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(Enum):
    """Order sides."""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Order statuses."""
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    PARTIALLY_FILLED = "partially_filled"


class PositionSide(Enum):
    """Position sides."""
    LONG = "long"
    SHORT = "short"


@dataclass
class AccountInfo:
    """Account information."""
    account_id: str
    balance: float
    equity: float
    margin: float
    free_margin: float
    margin_level: float
    currency: str
    leverage: float
    profit: float
    credit: float


@dataclass
class Position:
    """Trading position."""
    position_id: str
    symbol: str
    side: PositionSide
    size: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float
    margin_required: float
    open_time: datetime
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


@dataclass
class Order:
    """Trading order."""
    order_id: str
    symbol: str
    side: OrderSide
    type: OrderType
    size: float
    price: Optional[float]
    stop_price: Optional[float]
    status: OrderStatus
    filled_size: float
    remaining_size: float
    average_fill_price: Optional[float]
    created_time: datetime
    updated_time: datetime
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


@dataclass
class Trade:
    """Executed trade."""
    trade_id: str
    order_id: str
    symbol: str
    side: OrderSide
    size: float
    price: float
    commission: float
    timestamp: datetime


@dataclass
class MarketData:
    """Market data."""
    symbol: str
    bid: float
    ask: float
    last: float
    volume: float
    timestamp: datetime


class BaseBroker(ABC):
    """Base broker class that all broker implementations must inherit from."""
    
    def __init__(self, credentials: Dict[str, Any]):
        """Initialize the broker with credentials."""
        self.credentials = credentials
        self.is_connected = False
        self.account_info = None
        
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the broker API."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from the broker API."""
        pass
    
    @abstractmethod
    async def get_account_info(self) -> Optional[AccountInfo]:
        """Get account information."""
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """Get all open positions."""
        pass
    
    @abstractmethod
    async def get_orders(self) -> List[Order]:
        """Get all orders (pending, filled, cancelled)."""
        pass
    
    @abstractmethod
    async def get_trades(self, start_time: Optional[datetime] = None, 
                        end_time: Optional[datetime] = None) -> List[Trade]:
        """Get trade history."""
        pass
    
    @abstractmethod
    async def place_order(self, symbol: str, side: OrderSide, size: float,
                         order_type: OrderType = OrderType.MARKET,
                         price: Optional[float] = None,
                         stop_loss: Optional[float] = None,
                         take_profit: Optional[float] = None) -> Optional[Order]:
        """Place a trading order."""
        pass
    
    @abstractmethod
    async def modify_order(self, order_id: str, price: Optional[float] = None,
                          size: Optional[float] = None,
                          stop_loss: Optional[float] = None,
                          take_profit: Optional[float] = None) -> bool:
        """Modify an existing order."""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        pass
    
    @abstractmethod
    async def close_position(self, position_id: str, size: Optional[float] = None) -> bool:
        """Close a position (partially or fully)."""
        pass
    
    @abstractmethod
    async def get_market_data(self, symbol: str) -> Optional[MarketData]:
        """Get current market data for a symbol."""
        pass
    
    @abstractmethod
    async def get_ohlc_data(self, symbol: str, timeframe: str, 
                           count: int = 100) -> Optional[pd.DataFrame]:
        """Get OHLC data for a symbol."""
        pass
    
    @abstractmethod
    async def get_symbols(self) -> List[str]:
        """Get list of available trading symbols."""
        pass
    
    @abstractmethod
    def validate_symbol(self, symbol: str) -> bool:
        """Validate if a symbol is tradeable."""
        pass
    
    @abstractmethod
    def calculate_margin_required(self, symbol: str, size: float) -> float:
        """Calculate margin required for a trade."""
        pass
    
    @abstractmethod
    def get_minimum_trade_size(self, symbol: str) -> float:
        """Get minimum trade size for a symbol."""
        pass
    
    @abstractmethod
    def get_maximum_trade_size(self, symbol: str) -> float:
        """Get maximum trade size for a symbol."""
        pass
    
    # Helper methods that can be overridden by specific implementations
    
    def format_symbol(self, symbol: str) -> str:
        """Format symbol for the broker's API."""
        return symbol.upper()
    
    def calculate_position_size(self, account_balance: float, risk_percentage: float,
                              entry_price: float, stop_loss_price: float) -> float:
        """Calculate position size based on risk management."""
        if stop_loss_price == 0 or entry_price == stop_loss_price:
            return 0
        
        risk_amount = account_balance * (risk_percentage / 100)
        risk_per_unit = abs(entry_price - stop_loss_price)
        
        return risk_amount / risk_per_unit
    
    def validate_order_parameters(self, symbol: str, side: OrderSide, size: float,
                                 order_type: OrderType, price: Optional[float] = None) -> Tuple[bool, str]:
        """Validate order parameters."""
        # Check symbol
        if not self.validate_symbol(symbol):
            return False, f"Invalid symbol: {symbol}"
        
        # Check size
        min_size = self.get_minimum_trade_size(symbol)
        max_size = self.get_maximum_trade_size(symbol)
        
        if size < min_size:
            return False, f"Size too small. Minimum: {min_size}"
        
        if size > max_size:
            return False, f"Size too large. Maximum: {max_size}"
        
        # Check price for limit orders
        if order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT] and price is None:
            return False, "Price required for limit orders"
        
        return True, "Valid"
    
    async def get_position_by_symbol(self, symbol: str) -> Optional[Position]:
        """Get position for a specific symbol."""
        positions = await self.get_positions()
        for position in positions:
            if position.symbol == symbol:
                return position
        return None
    
    async def get_order_by_id(self, order_id: str) -> Optional[Order]:
        """Get order by ID."""
        orders = await self.get_orders()
        for order in orders:
            if order.order_id == order_id:
                return order
        return None
    
    async def cancel_all_orders(self, symbol: Optional[str] = None) -> int:
        """Cancel all orders, optionally filtered by symbol."""
        orders = await self.get_orders()
        cancelled_count = 0
        
        for order in orders:
            if order.status == OrderStatus.PENDING:
                if symbol is None or order.symbol == symbol:
                    if await self.cancel_order(order.order_id):
                        cancelled_count += 1
        
        return cancelled_count
    
    async def close_all_positions(self, symbol: Optional[str] = None) -> int:
        """Close all positions, optionally filtered by symbol."""
        positions = await self.get_positions()
        closed_count = 0
        
        for position in positions:
            if symbol is None or position.symbol == symbol:
                if await self.close_position(position.position_id):
                    closed_count += 1
        
        return closed_count
    
    def get_broker_name(self) -> str:
        """Get the broker name."""
        return self.__class__.__name__.replace('Broker', '')
    
    def is_market_open(self, symbol: str) -> bool:
        """Check if market is open for trading."""
        # Default implementation - should be overridden by specific brokers
        return True
    
    def get_trading_fees(self, symbol: str) -> Dict[str, float]:
        """Get trading fees for a symbol."""
        # Default implementation - should be overridden by specific brokers
        return {
            'commission': 0.0,
            'spread': 0.0,
            'swap_long': 0.0,
            'swap_short': 0.0
        }

