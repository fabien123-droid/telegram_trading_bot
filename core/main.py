"""
Main application entry point for the Telegram Trading Bot.
"""

import asyncio
import signal
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from loguru import logger

# Importations relatives converties en importations absolutes
from .config import get_settings, validate_required_settings
from .logging_config import setup_logging
from .exceptions import ConfigurationError

# Correction des importations relatives problématiques
try:
    from database.database import init_database, close_database
except ImportError:
    # Fallback si la structure est différente
    try:
        from src.database.database import init_database, close_database
    except ImportError:
        # Dernier fallback
        from ..database.database import init_database, close_database

try:
    from telegram_bot.bot import TelegramBot
except ImportError:
    try:
        from src.telegram_bot.bot import TelegramBot
    except ImportError:
        from ..telegram_bot.bot import TelegramBot

try:
    from scheduler.scheduler import TradingScheduler
except ImportError:
    try:
        from src.scheduler.scheduler import TradingScheduler
    except ImportError:
        from ..scheduler.scheduler import TradingScheduler


class TradingBotApplication:
    """Main application class for the Telegram Trading Bot."""
    
    def __init__(self):
        self.settings = get_settings()
        self.telegram_bot = None
        self.scheduler = None
        self.running = False
        
    async def startup(self):
        """Initialize the application."""
        try:
            # Setup logging
            setup_logging()
            logger.info("Starting Telegram Trading Bot...")
            
            # Validate configuration
            validate_required_settings()
            logger.info("Configuration validated successfully")
            
            # Initialize database
            await init_database()
            logger.info("Database initialized successfully")
            
            # Initialize Telegram bot
            self.telegram_bot = TelegramBot()
            await self.telegram_bot.initialize()
            logger.info("Telegram bot initialized successfully")
            
            # Initialize scheduler
            self.scheduler = TradingScheduler()
            await self.scheduler.start()
            logger.info("Trading scheduler started successfully")
            
            self.running = True
            logger.info("Telegram Trading Bot started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start application: {e}")
            await self.shutdown()
            raise
    
    async def shutdown(self):
        """Shutdown the application gracefully."""
        logger.info("Shutting down Telegram Trading Bot...")
        self.running = False
        
        # Stop scheduler
        if self.scheduler:
            try:
                await self.scheduler.stop()
                logger.info("Trading scheduler stopped")
            except Exception as e:
                logger.error(f"Error stopping scheduler: {e}")
        
        # Stop Telegram bot
        if self.telegram_bot:
            try:
                await self.telegram_bot.shutdown()
                logger.info("Telegram bot stopped")
            except Exception as e:
                logger.error(f"Error stopping Telegram bot: {e}")
        
        # Close database connections
        try:
            await close_database()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database: {e}")
        
        logger.info("Telegram Trading Bot shutdown complete")
    
    async def run(self):
        """Run the application."""
        try:
            await self.startup()
            
            # Keep the application running
            while self.running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Application error: {e}")
        finally:
            await self.shutdown()


@asynccontextmanager
async def lifespan() -> AsyncGenerator[None, None]:
    """Application lifespan context manager."""
    app = TradingBotApplication()
    
    try:
        await app.startup()
        yield
    finally:
        await app.shutdown()


def setup_signal_handlers(app: TradingBotApplication):
    """Setup signal handlers for graceful shutdown."""
    
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}")
        asyncio.create_task(app.shutdown())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """Main entry point."""
    app = TradingBotApplication()
    setup_signal_handlers(app)
    
    try:
        await app.run()
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
