#!/usr/bin/env python3
"""
Configuration du bot de trading Telegram
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Configuration de l'application"""
    
    # Telegram Bot - REQUIS
    telegram_bot_token: str
    
    # Database
    database_url: str = "sqlite:///./trading_bot.db"
    
    # API Keys pour les différents services
    alpha_vantage_api_key: Optional[str] = None
    finnhub_api_key: Optional[str] = None
    binance_api_key: Optional[str] = None
    binance_secret_key: Optional[str] = None
    deriv_api_token: Optional[str] = None
    ib_host: str = "127.0.0.1"
    ib_port: int = 7497
    ib_client_id: int = 1
    
    # Configuration générale
    debug: bool = False
    log_level: str = "INFO"
    max_users: int = 100
    
    # Configuration de trading
    default_risk_percentage: float = 2.0
    max_risk_percentage: float = 10.0
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Instance globale des paramètres
_settings: Optional[Settings] = None

def get_settings() -> Settings:
    """
    Récupère l'instance de configuration (singleton)
    
    Returns:
        Settings: Instance de configuration
    """
    global _settings
    if _settings is None:
        try:
            _settings = Settings()
        except Exception as e:
            print(f"❌ Erreur lors du chargement de la configuration: {e}")
            raise
    return _settings

def validate_required_settings() -> bool:
    """
    Valide que tous les paramètres requis sont présents
    
    Returns:
        bool: True si la configuration est valide
    """
    try:
        settings = get_settings()
        
        # Vérification du token Telegram (requis)
        if not settings.telegram_bot_token:
            print("❌ TELEGRAM_BOT_TOKEN est requis mais manquant")
            print("   Ajoutez TELEGRAM_BOT_TOKEN=your_token dans votre fichier .env")
            return False
        
        if settings.telegram_bot_token == "your_telegram_bot_token_here":
            print("❌ TELEGRAM_BOT_TOKEN utilise encore la valeur par défaut")
            print("   Remplacez par votre vrai token de bot Telegram")
            return False
            
        print("✅ Configuration validée avec succès")
        print(f"   📊 Database: {settings.database_url}")
        print(f"   🔧 Debug mode: {settings.debug}")
        print(f"   📝 Log level: {settings.log_level}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la validation de la configuration: {e}")
        return False

# Fonction utilitaire pour récupérer une variable d'environnement
def get_env_var(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Récupère une variable d'environnement
    
    Args:
        key: Nom de la variable
        default: Valeur par défaut si la variable n'existe pas
        
    Returns:
        str: Valeur de la variable ou default
    """
    return os.getenv(key, default)
