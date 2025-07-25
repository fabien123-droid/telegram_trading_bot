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

# DÉBOGAGE : Afficher les variables d'environnement au démarrage
print("=== DÉBOGAGE VARIABLES D'ENVIRONNEMENT ===")
print(f"TELEGRAM_BOT_TOKEN présent: {'TELEGRAM_BOT_TOKEN' in os.environ}")
if 'TELEGRAM_BOT_TOKEN' in os.environ:
    token = os.environ['TELEGRAM_BOT_TOKEN']
    print(f"TELEGRAM_BOT_TOKEN longueur: {len(token)}")
    print(f"TELEGRAM_BOT_TOKEN début: {token[:10]}...")

print(f"DERIV_APP_ID présent: {'DERIV_APP_ID' in os.environ}")
print(f"ENCRYPTION_KEY présent: {'ENCRYPTION_KEY' in os.environ}")
print(f"JWT_SECRET_KEY présent: {'JWT_SECRET_KEY' in os.environ}")
print("=======================================")


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    url: str = Field(default="sqlite:///trading_bot.db", env="DATABASE_URL")
    echo: bool = Field(default=False, env="DATABASE_ECHO")
    pool_size: int = Field(default=10, env="DATABASE_POOL_SIZE")
    max_overflow: int = Field(default=20, env="DATABASE_MAX_OVERFLOW")

    class Config:
        env_file = ".env"
        case_sensitive = False


class TelegramSettings(BaseSettings):
    """Telegram bot configuration settings."""
    
    # Lecture directe avec os.environ comme fallback
    bot_token: str = Field(
        default_factory=lambda: os.environ.get("TELEGRAM_BOT_TOKEN", ""), 
        env="TELEGRAM_BOT_TOKEN"
    )
    webhook_url: Optional[str] = Field(default=None, env="TELEGRAM_WEBHOOK_URL")
    admin_id: Optional[int] = Field(default=None, env="ADMIN_TELEGRAM_ID")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @field_validator('bot_token')
    @classmethod
    def validate_bot_token(cls, v):
        print(f"Validation bot_token reçu: '{v}' (longueur: {len(v) if v else 0})")
        if not v or v == "your_telegram_bot_token_here":
            # En production, essayer de lire directement depuis os.environ
            direct_token = os.environ.get("TELEGRAM_BOT_TOKEN")
            if direct_token:
                print(f"Token trouvé directement dans os.environ: {direct_token[:10]}...")
                return direct_token
            raise ValueError("TELEGRAM_BOT_TOKEN must be set")
        return v


class DerivSettings(BaseSettings):
    """Deriv API configuration settings."""
    
    app_id: str = Field(
        default_factory=lambda: os.environ.get("DERIV_APP_ID", ""), 
        env="DERIV_APP_ID"
    )
    api_url: str = Field(default="wss://ws.derivws.com/websockets/v3", env="DERIV_API_URL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @field_validator('app_id')
    @classmethod
    def validate_app_id(cls, v):
        if not v or v == "your_deriv_app_id_here":
            # En production, essayer de lire directement depuis os.environ
            direct_app_id = os.environ.get("DERIV_APP_ID")
            if direct_app_id:
                return direct_app_id
            raise ValueError("DERIV_APP_ID must be set")
        return v


class BinanceSettings(BaseSettings):
    """Binance API configuration settings."""
    
    api_key: Optional[str] = Field(default=None, env="BINANCE_API_KEY")
    api_secret: Optional[str] = Field(default=None, env="BINANCE_API_SECRET")
    testnet: bool = Field(default=True, env="BINANCE_TESTNET")

    class Config:
        env_file = ".env"
        case_sensitive = False


class MT5Settings(BaseSettings):
    """MetaTrader 5 configuration settings."""
    
    login: Optional[str] = Field(default=None, env="MT5_LOGIN")
    password: Optional[str] = Field(default=None, env="MT5_PASSWORD")
    server: Optional[str] = Field(default=None, env="MT5_SERVER")

    class Config:
        env_file = ".env"
        case_sensitive = False


class IBSettings(BaseSettings):
    """Interactive Brokers configuration settings."""
    
    host: str = Field(default="127.0.0.1", env="IB_HOST")
    port: int = Field(default=7497, env="IB_PORT")
    client_id: int = Field(default=1, env="IB_CLIENT_ID")

    class Config:
        env_file = ".env"
        case_sensitive = False


class SecuritySettings(BaseSettings):
    """Security configuration settings."""
    
    encryption_key: str = Field(
        default_factory=lambda: os.environ.get("ENCRYPTION_KEY", "default_encryption_key_32_characters_long!"), 
        env="ENCRYPTION_KEY"
    )
    jwt_secret_key: str = Field(
        default_factory=lambda: os.environ.get("JWT_SECRET_KEY", "default_jwt_secret_key"), 
        env="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(default=24, env="JWT_EXPIRATION_HOURS")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
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
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
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

    class Config:
        env_file = ".env"
        case_sensitive = False


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""
    
    level: str = Field(default="INFO", env="LOG_LEVEL")
    file: str = Field(default="logs/trading_bot.log", env="LOG_FILE")
    max_size: str = Field(default="10MB", env="LOG_MAX_SIZE")
    backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")

    class Config:
        env_file = ".env"
        case_sensitive = False


class APISettings(BaseSettings):
    """External API configuration settings."""
    
    alpha_vantage_key: Optional[str] = Field(default=None, env="ALPHA_VANTAGE_API_KEY")
    finnhub_key: Optional[str] = Field(default=None, env="FINNHUB_API_KEY")
    news_api_key: Optional[str] = Field(default=None, env="NEWS_API_KEY")

    class Config:
        env_file = ".env"
        case_sensitive = False


class AppSettings(BaseSettings):
    """Main application configuration settings."""
    
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # DÉCLARER LES SOUS-CONFIGURATIONS COMME CHAMPS PYDANTIC
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    telegram: TelegramSettings = Field(default_factory=TelegramSettings)
    deriv: DerivSettings = Field(default_factory=DerivSettings)
    binance: BinanceSettings = Field(default_factory=BinanceSettings)
    mt5: MT5Settings = Field(default_factory=MT5Settings)
    ib: IBSettings = Field(default_factory=IBSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    trading: TradingSettings = Field(default_factory=TradingSettings)
    scheduler: SchedulerSettings = Field(default_factory=SchedulerSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    api: APISettings = Field(default_factory=APISettings)
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance avec gestion d'erreur
try:
    settings = AppSettings()
    print("✅ Configuration chargée avec succès")
    print(f"Bot token configuré: {bool(settings.telegram.bot_token)}")
except Exception as e:
    print(f"❌ Erreur lors du chargement de la configuration: {e}")
    print("Variables d'environnement disponibles:")
    for key, value in os.environ.items():
        if any(keyword in key.upper() for keyword in ['TOKEN', 'KEY', 'SECRET', 'ID']):
            print(f"  {key}: {'***' if 'TOKEN' in key or 'SECRET' in key or 'KEY' in key else value}")
    raise


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
