"""
Encryption utilities for the Telegram Trading Bot.
"""

import base64
import json
import secrets
from typing import Dict, Any, Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from loguru import logger

from ..core.config import get_settings
from ..core.exceptions import EncryptionError


class EncryptionManager:
    """Manages encryption and decryption of sensitive data."""
    
    def __init__(self):
        self.settings = get_settings()
        self._fernet = None
        self._initialize_encryption()
    
    def _initialize_encryption(self):
        """Initialize encryption with the secret key."""
        try:
            # Get or generate encryption key
            secret_key = self.settings.security.secret_key
            
            if not secret_key:
                raise EncryptionError("Secret key not configured")
            
            # Derive encryption key from secret
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'telegram_trading_bot_salt',  # In production, use random salt
                iterations=100000,
            )
            
            key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))
            self._fernet = Fernet(key)
            
            logger.info("Encryption initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise EncryptionError(f"Encryption initialization failed: {e}")
    
    def encrypt(self, data: Any) -> str:
        """Encrypt data and return base64 encoded string."""
        try:
            if not self._fernet:
                raise EncryptionError("Encryption not initialized")
            
            # Convert data to JSON string
            json_data = json.dumps(data, default=str)
            
            # Encrypt the data
            encrypted_data = self._fernet.encrypt(json_data.encode())
            
            # Return base64 encoded string
            return base64.urlsafe_b64encode(encrypted_data).decode()
            
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise EncryptionError(f"Failed to encrypt data: {e}")
    
    def decrypt(self, encrypted_data: str) -> Any:
        """Decrypt base64 encoded string and return original data."""
        try:
            if not self._fernet:
                raise EncryptionError("Encryption not initialized")
            
            # Decode base64
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            
            # Decrypt the data
            decrypted_bytes = self._fernet.decrypt(encrypted_bytes)
            
            # Parse JSON
            json_data = decrypted_bytes.decode()
            return json.loads(json_data)
            
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise EncryptionError(f"Failed to decrypt data: {e}")
    
    def generate_token(self, length: int = 32) -> str:
        """Generate a secure random token."""
        return secrets.token_urlsafe(length)
    
    def hash_password(self, password: str) -> str:
        """Hash a password using a secure method."""
        # For this implementation, we'll use Fernet encryption
        # In production, consider using bcrypt or argon2
        return self.encrypt(password)
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        try:
            decrypted_password = self.decrypt(hashed_password)
            return password == decrypted_password
        except Exception:
            return False


# Global encryption manager instance
encryption_manager = EncryptionManager()


def encrypt_data(data: Any) -> str:
    """Encrypt data using the global encryption manager."""
    return encryption_manager.encrypt(data)


def decrypt_data(encrypted_data: str) -> Any:
    """Decrypt data using the global encryption manager."""
    return encryption_manager.decrypt(encrypted_data)


def generate_secure_token(length: int = 32) -> str:
    """Generate a secure random token."""
    return encryption_manager.generate_token(length)


def hash_password(password: str) -> str:
    """Hash a password."""
    return encryption_manager.hash_password(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password."""
    return encryption_manager.verify_password(password, hashed_password)


class APIKeyManager:
    """Manages API key encryption and storage."""
    
    @staticmethod
    def encrypt_api_credentials(credentials: Dict[str, Any]) -> str:
        """Encrypt API credentials."""
        try:
            # Add timestamp for tracking
            credentials['encrypted_at'] = str(datetime.utcnow())
            
            return encrypt_data(credentials)
            
        except Exception as e:
            logger.error(f"Failed to encrypt API credentials: {e}")
            raise EncryptionError(f"API credential encryption failed: {e}")
    
    @staticmethod
    def decrypt_api_credentials(encrypted_credentials: str) -> Dict[str, Any]:
        """Decrypt API credentials."""
        try:
            credentials = decrypt_data(encrypted_credentials)
            
            # Remove timestamp if present
            credentials.pop('encrypted_at', None)
            
            return credentials
            
        except Exception as e:
            logger.error(f"Failed to decrypt API credentials: {e}")
            raise EncryptionError(f"API credential decryption failed: {e}")
    
    @staticmethod
    def validate_credentials_format(broker_type: str, credentials: Dict[str, Any]) -> bool:
        """Validate credentials format for different brokers."""
        required_fields = {
            'deriv': ['api_token'],
            'binance': ['api_key', 'api_secret'],
            'mt5': ['login', 'password', 'server'],
            'ib': ['host', 'port', 'client_id']
        }
        
        if broker_type not in required_fields:
            return False
        
        required = required_fields[broker_type]
        return all(field in credentials for field in required)


class SessionManager:
    """Manages user sessions and tokens."""
    
    def __init__(self):
        self.active_sessions = {}  # In production, use Redis or database
    
    def create_session(self, user_id: int, telegram_id: int) -> str:
        """Create a new user session."""
        try:
            session_token = generate_secure_token()
            
            session_data = {
                'user_id': user_id,
                'telegram_id': telegram_id,
                'created_at': datetime.utcnow().isoformat(),
                'last_activity': datetime.utcnow().isoformat()
            }
            
            # Encrypt session data
            encrypted_session = encrypt_data(session_data)
            
            # Store in memory (use database in production)
            self.active_sessions[session_token] = encrypted_session
            
            logger.info(f"Session created for user {user_id}")
            return session_token
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise EncryptionError(f"Session creation failed: {e}")
    
    def validate_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Validate and return session data."""
        try:
            if session_token not in self.active_sessions:
                return None
            
            encrypted_session = self.active_sessions[session_token]
            session_data = decrypt_data(encrypted_session)
            
            # Check if session is expired (24 hours)
            created_at = datetime.fromisoformat(session_data['created_at'])
            if datetime.utcnow() - created_at > timedelta(hours=24):
                self.invalidate_session(session_token)
                return None
            
            # Update last activity
            session_data['last_activity'] = datetime.utcnow().isoformat()
            self.active_sessions[session_token] = encrypt_data(session_data)
            
            return session_data
            
        except Exception as e:
            logger.error(f"Session validation failed: {e}")
            return None
    
    def invalidate_session(self, session_token: str) -> bool:
        """Invalidate a session."""
        try:
            if session_token in self.active_sessions:
                del self.active_sessions[session_token]
                logger.info("Session invalidated")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Session invalidation failed: {e}")
            return False
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        try:
            current_time = datetime.utcnow()
            expired_tokens = []
            
            for token, encrypted_session in self.active_sessions.items():
                try:
                    session_data = decrypt_data(encrypted_session)
                    created_at = datetime.fromisoformat(session_data['created_at'])
                    
                    if current_time - created_at > timedelta(hours=24):
                        expired_tokens.append(token)
                        
                except Exception:
                    # If we can't decrypt, consider it expired
                    expired_tokens.append(token)
            
            for token in expired_tokens:
                del self.active_sessions[token]
            
            if expired_tokens:
                logger.info(f"Cleaned up {len(expired_tokens)} expired sessions")
                
        except Exception as e:
            logger.error(f"Session cleanup failed: {e}")


# Global session manager
session_manager = SessionManager()


def create_user_session(user_id: int, telegram_id: int) -> str:
    """Create a user session."""
    return session_manager.create_session(user_id, telegram_id)


def validate_user_session(session_token: str) -> Optional[Dict[str, Any]]:
    """Validate a user session."""
    return session_manager.validate_session(session_token)


def invalidate_user_session(session_token: str) -> bool:
    """Invalidate a user session."""
    return session_manager.invalidate_session(session_token)


class SecurityValidator:
    """Security validation utilities."""
    
    @staticmethod
    def validate_telegram_id(telegram_id: int) -> bool:
        """Validate Telegram ID format."""
        return isinstance(telegram_id, int) and telegram_id > 0
    
    @staticmethod
    def validate_symbol(symbol: str) -> bool:
        """Validate trading symbol format."""
        if not isinstance(symbol, str) or len(symbol) < 2:
            return False
        
        # Basic symbol validation
        return symbol.replace('/', '').replace('-', '').isalnum()
    
    @staticmethod
    def validate_trade_size(size: float, min_size: float = 0.001, max_size: float = 1000000) -> bool:
        """Validate trade size."""
        return isinstance(size, (int, float)) and min_size <= size <= max_size
    
    @staticmethod
    def validate_price(price: float) -> bool:
        """Validate price value."""
        return isinstance(price, (int, float)) and price > 0
    
    @staticmethod
    def sanitize_input(input_str: str, max_length: int = 1000) -> str:
        """Sanitize user input."""
        if not isinstance(input_str, str):
            return ""
        
        # Remove potentially dangerous characters
        sanitized = input_str.strip()[:max_length]
        
        # Remove HTML tags (basic)
        import re
        sanitized = re.sub(r'<[^>]+>', '', sanitized)
        
        return sanitized
    
    @staticmethod
    def validate_risk_percentage(risk_pct: float) -> bool:
        """Validate risk percentage."""
        return isinstance(risk_pct, (int, float)) and 0.1 <= risk_pct <= 10.0


# Import datetime here to avoid circular imports
from datetime import datetime, timedelta

