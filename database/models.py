"""
Database models for the Telegram Trading Bot.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, JSON,
    ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    """User model for storing user information."""
    
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    
    # User settings
    is_active = Column(Boolean, default=True, nullable=False)
    is_premium = Column(Boolean, default=False, nullable=False)
    language = Column(String(10), default='en', nullable=False)
    timezone = Column(String(50), default='UTC', nullable=False)
    
    # Trading settings
    risk_per_trade = Column(Float, default=1.0, nullable=False)  # Percentage
    max_positions = Column(Integer, default=5, nullable=False)
    default_stop_loss = Column(Float, default=2.0, nullable=False)  # Percentage
    default_take_profit = Column(Float, default=4.0, nullable=False)  # Percentage
    auto_trading_enabled = Column(Boolean, default=False, nullable=False)
    
    # Notification settings
    signal_alerts = Column(Boolean, default=True, nullable=False)
    trade_alerts = Column(Boolean, default=True, nullable=False)
    error_alerts = Column(Boolean, default=True, nullable=False)
    daily_summary = Column(Boolean, default=True, nullable=False)
    
    # Signal settings
    min_signal_strength = Column(String(20), default='MODERATE', nullable=False)
    technical_weight = Column(Float, default=0.7, nullable=False)
    sentiment_weight = Column(Float, default=0.3, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    last_active_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    broker_accounts = relationship("BrokerAccount", back_populates="user", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="user", cascade="all, delete-orphan")
    signals = relationship("Signal", back_populates="user", cascade="all, delete-orphan")
    user_sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username='{self.username}')>"


class BrokerAccount(Base):
    """Broker account model for storing encrypted broker credentials."""
    
    __tablename__ = 'broker_accounts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    broker_name = Column(String(50), nullable=False)  # deriv, binance, mt5, ib
    account_name = Column(String(255), nullable=True)  # User-defined name
    
    # Encrypted credentials (JSON format)
    encrypted_credentials = Column(Text, nullable=False)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_connected = Column(Boolean, default=False, nullable=False)
    last_connection_at = Column(DateTime, nullable=True)
    connection_error = Column(Text, nullable=True)
    
    # Account info (cached)
    account_balance = Column(Float, nullable=True)
    account_currency = Column(String(10), nullable=True)
    account_leverage = Column(Float, nullable=True)
    last_balance_update = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="broker_accounts")
    trades = relationship("Trade", back_populates="broker_account")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'broker_name', 'account_name', name='unique_user_broker_account'),
        Index('idx_broker_accounts_user_broker', 'user_id', 'broker_name'),
    )
    
    def __repr__(self):
        return f"<BrokerAccount(id={self.id}, user_id={self.user_id}, broker='{self.broker_name}')>"


class Signal(Base):
    """Trading signal model."""
    
    __tablename__ = 'signals'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # Null for global signals
    
    # Signal details
    symbol = Column(String(20), nullable=False, index=True)
    signal_type = Column(String(10), nullable=False)  # BUY, SELL, NEUTRAL
    strength = Column(String(20), nullable=False)  # VERY_WEAK, WEAK, MODERATE, STRONG, VERY_STRONG
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0
    
    # Price levels
    entry_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    risk_reward_ratio = Column(Float, nullable=True)
    
    # Analysis data
    technical_signals = Column(JSON, nullable=True)  # Dict of indicator signals
    sentiment_score = Column(Float, nullable=True)
    sentiment_confidence = Column(Float, nullable=True)
    support_resistance = Column(JSON, nullable=True)  # Support/resistance levels
    
    # Metadata
    timeframe = Column(String(10), nullable=False)
    reasoning = Column(JSON, nullable=True)  # List of reasoning strings
    warnings = Column(JSON, nullable=True)  # List of warning strings
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_executed = Column(Boolean, default=False, nullable=False)
    executed_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="signals")
    trades = relationship("Trade", back_populates="signal")
    
    # Indexes
    __table_args__ = (
        Index('idx_signals_symbol_active', 'symbol', 'is_active'),
        Index('idx_signals_user_active', 'user_id', 'is_active'),
        Index('idx_signals_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Signal(id={self.id}, symbol='{self.symbol}', type='{self.signal_type}', strength='{self.strength}')>"


class Trade(Base):
    """Trade execution model."""
    
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    broker_account_id = Column(Integer, ForeignKey('broker_accounts.id'), nullable=False)
    signal_id = Column(Integer, ForeignKey('signals.id'), nullable=True)
    
    # Trade details
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)  # BUY, SELL
    size = Column(Float, nullable=False)
    
    # Execution details
    order_id = Column(String(100), nullable=True)  # Broker order ID
    entry_price = Column(Float, nullable=True)
    exit_price = Column(Float, nullable=True)
    
    # Risk management
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    
    # P&L
    realized_pnl = Column(Float, default=0.0, nullable=False)
    unrealized_pnl = Column(Float, default=0.0, nullable=False)
    commission = Column(Float, default=0.0, nullable=False)
    swap = Column(Float, default=0.0, nullable=False)
    
    # Status
    status = Column(String(20), nullable=False)  # PENDING, FILLED, CANCELLED, CLOSED
    is_manual = Column(Boolean, default=False, nullable=False)  # Manual vs automated trade
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    opened_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    
    # Additional data
    metadata = Column(JSON, nullable=True)  # Additional trade data
    notes = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="trades")
    broker_account = relationship("BrokerAccount", back_populates="trades")
    signal = relationship("Signal", back_populates="trades")
    
    # Indexes
    __table_args__ = (
        Index('idx_trades_user_symbol', 'user_id', 'symbol'),
        Index('idx_trades_status', 'status'),
        Index('idx_trades_created_at', 'created_at'),
        Index('idx_trades_broker_order', 'broker_account_id', 'order_id'),
    )
    
    def __repr__(self):
        return f"<Trade(id={self.id}, symbol='{self.symbol}', side='{self.side}', status='{self.status}')>"


class UserSession(Base):
    """User session model for tracking user activity."""
    
    __tablename__ = 'user_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    
    # Session data
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    last_activity_at = Column(DateTime, default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="user_sessions")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_sessions_user_active', 'user_id', 'is_active'),
        Index('idx_user_sessions_expires', 'expires_at'),
    )
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"


class SystemLog(Base):
    """System log model for tracking system events."""
    
    __tablename__ = 'system_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Log details
    level = Column(String(10), nullable=False, index=True)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    message = Column(Text, nullable=False)
    module = Column(String(100), nullable=True)
    function = Column(String(100), nullable=True)
    
    # Context
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    trade_id = Column(Integer, ForeignKey('trades.id'), nullable=True)
    signal_id = Column(Integer, ForeignKey('signals.id'), nullable=True)
    
    # Additional data
    metadata = Column(JSON, nullable=True)
    stack_trace = Column(Text, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_system_logs_level_created', 'level', 'created_at'),
        Index('idx_system_logs_user_created', 'user_id', 'created_at'),
        Index('idx_system_logs_module', 'module'),
    )
    
    def __repr__(self):
        return f"<SystemLog(id={self.id}, level='{self.level}', module='{self.module}')>"


class MarketData(Base):
    """Market data model for caching price data."""
    
    __tablename__ = 'market_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Symbol and timeframe
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False)
    
    # OHLCV data
    timestamp = Column(DateTime, nullable=False)
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Float, default=0.0, nullable=False)
    
    # Data source
    source = Column(String(50), nullable=False)  # yahoo, binance, deriv, etc.
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('symbol', 'timeframe', 'timestamp', 'source', name='unique_market_data'),
        Index('idx_market_data_symbol_timeframe', 'symbol', 'timeframe'),
        Index('idx_market_data_timestamp', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<MarketData(symbol='{self.symbol}', timeframe='{self.timeframe}', timestamp={self.timestamp})>"


class Configuration(Base):
    """Configuration model for storing system settings."""
    
    __tablename__ = 'configurations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    value_type = Column(String(20), default='string', nullable=False)  # string, int, float, bool, json
    description = Column(Text, nullable=True)
    
    # Metadata
    is_encrypted = Column(Boolean, default=False, nullable=False)
    is_system = Column(Boolean, default=False, nullable=False)  # System vs user configurable
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Configuration(key='{self.key}', type='{self.value_type}')>"


class Notification(Base):
    """Notification model for storing user notifications."""
    
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Notification details
    type = Column(String(50), nullable=False)  # signal, trade, error, system, etc.
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    # Status
    is_read = Column(Boolean, default=False, nullable=False)
    is_sent = Column(Boolean, default=False, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    
    # Priority
    priority = Column(String(20), default='normal', nullable=False)  # low, normal, high, urgent
    
    # Additional data
    metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_notifications_user_read', 'user_id', 'is_read'),
        Index('idx_notifications_type_created', 'type', 'created_at'),
        Index('idx_notifications_priority', 'priority'),
    )
    
    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, type='{self.type}')>"

