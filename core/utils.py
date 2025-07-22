"""
Utility functions for the Telegram Trading Bot.
"""

import hashlib
import hmac
import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from decimal import Decimal, ROUND_HALF_UP

from loguru import logger


def generate_uuid() -> str:
    """Generate a unique UUID string."""
    return str(uuid.uuid4())


def generate_request_id() -> str:
    """Generate a unique request ID for API calls."""
    timestamp = str(int(time.time() * 1000))
    random_part = str(uuid.uuid4())[:8]
    return f"{timestamp}_{random_part}"


def get_current_timestamp() -> datetime:
    """Get the current UTC timestamp."""
    return datetime.now(timezone.utc)


def timestamp_to_string(timestamp: datetime, format_str: str = "%Y-%m-%d %H:%M:%S UTC") -> str:
    """Convert timestamp to string."""
    return timestamp.strftime(format_str)


def string_to_timestamp(date_string: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """Convert string to timestamp."""
    return datetime.strptime(date_string, format_str).replace(tzinfo=timezone.utc)


def round_decimal(value: Union[float, Decimal], decimal_places: int = 2) -> Decimal:
    """Round a decimal value to specified decimal places."""
    if isinstance(value, float):
        value = Decimal(str(value))
    elif not isinstance(value, Decimal):
        value = Decimal(str(value))
    
    quantize_value = Decimal('0.1') ** decimal_places
    return value.quantize(quantize_value, rounding=ROUND_HALF_UP)


def calculate_percentage(value: Union[float, Decimal], total: Union[float, Decimal]) -> Decimal:
    """Calculate percentage of value from total."""
    if total == 0:
        return Decimal('0')
    
    value = Decimal(str(value))
    total = Decimal(str(total))
    
    return round_decimal((value / total) * 100, 2)


def calculate_pnl(entry_price: Union[float, Decimal], exit_price: Union[float, Decimal], 
                  quantity: Union[float, Decimal], side: str) -> Decimal:
    """Calculate profit and loss for a trade."""
    entry_price = Decimal(str(entry_price))
    exit_price = Decimal(str(exit_price))
    quantity = Decimal(str(quantity))
    
    if side.upper() == "BUY":
        pnl = (exit_price - entry_price) * quantity
    elif side.upper() == "SELL":
        pnl = (entry_price - exit_price) * quantity
    else:
        raise ValueError(f"Invalid side: {side}. Must be 'BUY' or 'SELL'")
    
    return round_decimal(pnl, 2)


def calculate_position_size(account_balance: Union[float, Decimal], 
                          risk_percentage: Union[float, Decimal],
                          entry_price: Union[float, Decimal],
                          stop_loss_price: Union[float, Decimal]) -> Decimal:
    """Calculate position size based on risk management."""
    account_balance = Decimal(str(account_balance))
    risk_percentage = Decimal(str(risk_percentage))
    entry_price = Decimal(str(entry_price))
    stop_loss_price = Decimal(str(stop_loss_price))
    
    # Calculate risk amount
    risk_amount = account_balance * (risk_percentage / 100)
    
    # Calculate risk per unit
    risk_per_unit = abs(entry_price - stop_loss_price)
    
    if risk_per_unit == 0:
        return Decimal('0')
    
    # Calculate position size
    position_size = risk_amount / risk_per_unit
    
    return round_decimal(position_size, 6)


def validate_email(email: str) -> bool:
    """Validate email format."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone: str) -> bool:
    """Validate phone number format."""
    import re
    # Basic international phone number validation
    pattern = r'^\+?[1-9]\d{1,14}$'
    return re.match(pattern, phone.replace(' ', '').replace('-', '')) is not None


def sanitize_symbol(symbol: str) -> str:
    """Sanitize trading symbol."""
    return symbol.upper().replace(' ', '').replace('-', '').replace('_', '')


def format_currency(amount: Union[float, Decimal], currency: str = "USD", decimal_places: int = 2) -> str:
    """Format currency amount."""
    amount = round_decimal(amount, decimal_places)
    return f"{amount} {currency}"


def format_percentage(value: Union[float, Decimal], decimal_places: int = 2) -> str:
    """Format percentage value."""
    value = round_decimal(value, decimal_places)
    return f"{value}%"


def create_signature(secret: str, message: str, algorithm: str = "sha256") -> str:
    """Create HMAC signature for API authentication."""
    if algorithm == "sha256":
        return hmac.new(
            secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    elif algorithm == "sha512":
        return hmac.new(
            secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")


def safe_json_loads(json_string: str, default: Any = None) -> Any:
    """Safely load JSON string."""
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Failed to parse JSON: {e}")
        return default


def safe_json_dumps(data: Any, default: str = "{}") -> str:
    """Safely dump data to JSON string."""
    try:
        return json.dumps(data, default=str)
    except (TypeError, ValueError) as e:
        logger.warning(f"Failed to serialize to JSON: {e}")
        return default


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split a list into chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """Flatten a nested dictionary."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def retry_on_exception(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Decorator for retrying functions on exception."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay
            
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries >= max_retries:
                        logger.error(f"Function {func.__name__} failed after {max_retries} retries: {e}")
                        raise
                    
                    logger.warning(f"Function {func.__name__} failed (attempt {retries}/{max_retries}): {e}")
                    time.sleep(current_delay)
                    current_delay *= backoff
            
        return wrapper
    return decorator


def rate_limit(calls_per_second: float = 1.0):
    """Decorator for rate limiting function calls."""
    min_interval = 1.0 / calls_per_second
    last_called = [0.0]
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        return wrapper
    return decorator


def mask_sensitive_data(data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
    """Mask sensitive data like API keys."""
    if len(data) <= visible_chars * 2:
        return mask_char * len(data)
    
    start = data[:visible_chars]
    end = data[-visible_chars:]
    middle = mask_char * (len(data) - visible_chars * 2)
    
    return f"{start}{middle}{end}"


def is_market_open(market: str = "forex") -> bool:
    """Check if market is currently open."""
    now = datetime.now(timezone.utc)
    weekday = now.weekday()  # 0 = Monday, 6 = Sunday
    hour = now.hour
    
    if market.lower() == "forex":
        # Forex market is open 24/5 (Monday 00:00 UTC to Friday 22:00 UTC)
        if weekday == 6:  # Sunday
            return hour >= 22  # Opens at 22:00 UTC Sunday
        elif weekday == 5:  # Saturday
            return hour < 22   # Closes at 22:00 UTC Friday
        else:  # Monday to Friday
            return True
    
    elif market.lower() == "crypto":
        # Crypto market is open 24/7
        return True
    
    elif market.lower() == "stock":
        # US stock market (simplified - 9:30 AM to 4:00 PM EST)
        # This is a simplified version, real implementation should consider holidays
        if weekday >= 5:  # Weekend
            return False
        # Convert to EST (UTC-5 or UTC-4 depending on DST)
        # This is simplified and doesn't account for DST properly
        est_hour = (hour - 5) % 24
        return 9 <= est_hour < 16
    
    return False


def get_market_session(market: str = "forex") -> str:
    """Get current market session."""
    now = datetime.now(timezone.utc)
    hour = now.hour
    
    if market.lower() == "forex":
        if 0 <= hour < 8:
            return "Sydney/Tokyo"
        elif 8 <= hour < 16:
            return "London"
        elif 16 <= hour < 24:
            return "New York"
        else:
            return "Closed"
    
    return "Unknown"

