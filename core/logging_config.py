"""
Logging configuration for the Telegram Trading Bot.
"""

import os
import sys
from pathlib import Path
from loguru import logger

from .config import get_settings


def setup_logging():
    """Setup logging configuration."""
    settings = get_settings()
    
    # Remove default logger
    logger.remove()
    
    # Create logs directory if it doesn't exist
    log_file_path = Path(settings.logging.file)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Console logging
    logger.add(
        sys.stdout,
        level=settings.logging.level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # File logging
    logger.add(
        settings.logging.file,
        level=settings.logging.level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation=settings.logging.max_size,
        retention=f"{settings.logging.backup_count} files",
        compression="zip",
        backtrace=True,
        diagnose=True
    )
    
    # Error file logging
    error_log_file = log_file_path.parent / "error.log"
    logger.add(
        str(error_log_file),
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation="1 week",
        retention="1 month",
        compression="zip",
        backtrace=True,
        diagnose=True
    )
    
    # Trading activity logging
    trading_log_file = log_file_path.parent / "trading.log"
    logger.add(
        str(trading_log_file),
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
        filter=lambda record: "TRADE" in record["extra"],
        rotation="1 day",
        retention="3 months",
        compression="zip"
    )
    
    logger.info("Logging configuration initialized")


def get_logger(name: str):
    """Get a logger instance with the specified name."""
    return logger.bind(name=name)


def log_trade_activity(user_id: int, action: str, symbol: str, details: dict):
    """Log trading activity."""
    logger.bind(TRADE=True).info(
        f"USER:{user_id} | ACTION:{action} | SYMBOL:{symbol} | DETAILS:{details}"
    )


def log_api_call(broker: str, endpoint: str, status: str, response_time: float = None):
    """Log API calls."""
    message = f"API_CALL | BROKER:{broker} | ENDPOINT:{endpoint} | STATUS:{status}"
    if response_time:
        message += f" | RESPONSE_TIME:{response_time:.3f}s"
    
    logger.info(message)


def log_error_with_context(error: Exception, context: dict = None):
    """Log error with additional context."""
    context_str = ""
    if context:
        context_str = f" | CONTEXT:{context}"
    
    logger.error(f"ERROR:{type(error).__name__} | MESSAGE:{str(error)}{context_str}")


def log_user_action(user_id: int, action: str, details: dict = None):
    """Log user actions."""
    message = f"USER_ACTION | USER_ID:{user_id} | ACTION:{action}"
    if details:
        message += f" | DETAILS:{details}"
    
    logger.info(message)

