"""
Configuration module for the Telegram Trading Bot.
Handles environment variables and application settings.
"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    url: str = Field(default="sqlite:///trading_bot.db", env="DATABASE_URL")
    echo: bool = Field(default=False, env="DATABASE_ECHO")
    pool_size: int = Field(default=10, env="DATABASE_POOL_SIZE")
    max_overflow: int = Field(default=20, env="DATABASE_MAX_OVERFLOW")


class TelegramSettings(BaseSettings):
    """Telegram bot configuration settings."""
    
    bot_token: str = Field(..., env="TELEGRAM_BOT_TOKEN")
    webhook_url: Optional[str] = Field(default=None, env="TELEGRAM_WEBHOOK_URL")
    admin_id: Optional[int] = Field(default=None, env="ADMIN_TELEGRAM_ID")
    
    @field_validator('bot_token')
    @classmethod
    def validate_bot_token(cls, v):
        if not v or v == "your_telegram_bot_token_here":
            raise ValueError("TELEGRAM_BOT_TOKEN must be set")
        return v


class DerivSettings(BaseSettings):
    """Deriv API configuration settings."""
    
    app_id: str = Field(..., env="DERIV_APP_ID")
    api_url: str = Field(default="wss://ws.derivws.com/websockets/v3", env="DERIV_API_URL")
    
    @field_validator('app_id')
    @classmethod
    def validate_app_id(cls, v):
        if not v or v == "your_deriv_app_id_here":
            raise ValueError("DERIV_APP_ID must be set")
        return v


class BinanceSettings(BaseSettings):
    """Binance API configuration settings."""
    
    api_key: Optional[str] = Field(default=None, env="BINANCE_API_KEY")
    api_secret: Optional[str] = Field(default=None, env="BINANCE_API_SECRET")
    testnet: bool = Field(default=True, env="BINANCE_TESTNET")


class MT5Settings(BaseSettings):
    """MetaTrader 5 configuration settings."""
    
    login: Optional[str] = Field(default=None, env="MT5_LOGIN")
    password: Optional[str] = Field(default=None, env="MT5_PASSWORD")
    server: Optional[str] = Field(default=None, env="MT5_SERVER")


class IBSettings(BaseSettings):
    """Interactive Brokers configuration settings."""
    
    host: str = Field(default="127.0.0.1", env="IB_HOST")
    port: int = Field(default=7497, env="IB_PORT")
    client_id: int = Field(default=1, env="IB_CLIENT_ID")


class SecuritySettings(BaseSettings):
    """Security configuration settings."""
    
    encryption_key: str = Field(..., env="ENCRYPTION_KEY")
    jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(default=24, env="JWT_EXPIRATION_HOURS")
    
    @field_validator('encryption_key')
    @classmethod
    def validate_encryption_key(cls, v):
        if not v or len(v) < 32:
            raise ValueError("ENCRYPTION_KEY must be at least 32 characters long")
        return v


class TradingSettings(BaseSettings):
    """Trading configuration settings."""
    
    default_risk_percentage: float = Field(default=1.0, env="DEFAULT_RISK_PERCENTAGE")
    max_positions_per_user: int = Field(default=5, env="MAX_POSITIONS_PER_USER")
    min_trade_amount: float = Field(default=10.0, env="MIN_TRADE_AMOUNT")
    max_trade_amount: float = Field(default=1000.0, env="MAX_TRADE_AMOUNT")
    
    @field_validator('default_risk_percentage')
    @classmethod
    def validate_risk_percentage(cls, v):
        if v <= 0 or v > 100:
            raise ValueError("Risk percentage must be between 0 and 100")
        return v


class SchedulerSettings(BaseSettings):
    """Scheduler configuration settings."""
    
    analysis_interval_minutes: int = Field(default=5, env="ANALYSIS_INTERVAL_MINUTES")
    cleanup_interval_hours: int = Field(default=24, env="CLEANUP_INTERVAL_HOURS")
    heartbeat_interval_seconds: int = Field(default=30, env="HEARTBEAT_INTERVAL_SECONDS")


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""
    
    level: str = Field(default="INFO", env="LOG_LEVEL")
    file: str = Field(default="logs/trading_bot.log", env="LOG_FILE")
    max_size: str = Field(default="10MB", env="LOG_MAX_SIZE")
    backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")


class APISettings(BaseSettings):
    """External API configuration settings."""
    
    alpha_vantage_key: Optional[str] = Field(default=None, env="ALPHA_VANTAGE_API_KEY")
    finnhub_key: Optional[str] = Field(default=None, env="FINNHUB_API_KEY")
    news_api_key: Optional[str] = Field(default=None, env="NEWS_API_KEY")


class AppSettings(BaseSettings):
    """Main application configuration settings."""
    
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # Configuration du modèle
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialiser les sous-configurations après l'initialisation principale
        self.database = DatabaseSettings()
        self.telegram = TelegramSettings()
        self.deriv = DerivSettings()
        self.binance = BinanceSettings()
        self.mt5 = MT5Settings()
        self.ib = IBSettings()
        self.security = SecuritySettings()
        self.trading = TradingSettings()
        self.scheduler = SchedulerSettings()
        self.logging = LoggingSettings()
        self.api = APISettings()


# Global settings instance
settings = AppSettings()


def get_settings() -> AppSettings:
    """Get the application settings instance."""
    return settings


def validate_required_settings():
    """Validate that all required settings are properly configured."""
    errors = []
    
    # Check Telegram settings
    if not settings.telegram.bot_token or settings.telegram.bot_token == "your_telegram_bot_token_here":
        errors.append("TELEGRAM_BOT_TOKEN is required")
    
    # Check Deriv settings
    if not settings.deriv.app_id or settings.deriv.app_id == "your_deriv_app_id_here":
        errors.append("DERIV_APP_ID is required")
    
    # Check security settings
    if not settings.security.encryption_key or len(settings.security.encryption_key) < 32:
        errors.append("ENCRYPTION_KEY must be at least 32 characters long")
    
    if not settings.security.jwt_secret_key:
        errors.append("JWT_SECRET_KEY is required")
    
    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")
    
    return True
