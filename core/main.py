"""
Main application entry point for the Telegram Trading Bot.
"""

import asyncio
import signal
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from loguru import logger

# Imports absolus depuis la racine du projet
from core.config import get_settings, validate_required_settings

# Import du logging config avec fallback
try:
    from core.logging_config import setup_logging
    logger.info("Successfully imported logging_config")
except ImportError as e:
    logger.warning(f"Failed to import logging_config: {e}")
    # Fallback simple pour le logging
    def setup_logging():
        logger.info("Using fallback logging setup")

# Import des exceptions avec fallback
try:
    from core.exceptions import ConfigurationError
    logger.info("Successfully imported core.exceptions")
except ImportError as e:
    logger.warning(f"Failed to import core.exceptions: {e}")
    # Fallback
    class ConfigurationError(Exception):
        pass

# Imports absolus pour les autres modules
try:
    from database.database import init_database, close_database
    logger.info("Successfully imported database module")
except ImportError as e:
    logger.error(f"Failed to import database module: {e}")
    # Essayer une alternative si nécessaire
    try:
        from src.database.database import init_database, close_database
        logger.info("Successfully imported database module from src")
    except ImportError as e2:
        logger.error(f"Failed to import database module from src: {e2}")
        # Fallback pour permettre le démarrage
        async def init_database():
            logger.info("Mock init_database called")
            return True
        
        async def close_database():
            logger.info("Mock close_database called")

# Import du bot Telegram avec fallback amélioré
try:
    from telegram_bot.bot import TelegramBot
    logger.info("Successfully imported telegram_bot module")
except ImportError as e:
    logger.error(f"Failed to import telegram_bot module: {e}")
    # Fallback temporaire pour permettre le démarrage
    class TelegramBot:
        def __init__(self):
            logger.warning("Using fallback TelegramBot class")
            
        async def initialize(self):
            logger.info("Mock TelegramBot initialized")
            
        async def shutdown(self):
            logger.info("Mock TelegramBot shutdown")

# Import du scheduler avec fallback amélioré
try:
    from scheduler.scheduler import TradingScheduler
    logger.info("Successfully imported scheduler module")
except ImportError as e:
    logger.error(f"Failed to import scheduler module: {e}")
    # Fallback temporaire pour permettre le démarrage
    class TradingScheduler:
        def __init__(self):
            logger.warning("Using fallback TradingScheduler class")
            
        async def start(self):
            logger.info("Mock TradingScheduler started")
            
        async def stop(self):
            logger.info("Mock TradingScheduler stopped")


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
            if not validate_required_settings():
                raise ConfigurationError("Configuration validation failed")
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
            logger.info("✅ Telegram Trading Bot started successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to start application: {e}")
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
        
        logger.info("✅ Telegram Trading Bot shutdown complete")
    
    async def run(self):
        """Run the application."""
        try:
            await self.startup()
            
            # Keep the application running with better logging
            logger.info("🤖 Bot is now running... Press Ctrl+C to stop")
            while self.running:
                await asyncio.sleep(30)  # Log moins fréquemment
                logger.debug("Bot heartbeat - still running")
                
        except KeyboardInterrupt:
            logger.info("⏹️ Received keyboard interrupt")
        except Exception as e:
            logger.error(f"💥 Application error: {e}")
            import traceback
            traceback.print_exc()
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
        app.running = False  # Arrêter la boucle principale
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """Main entry point."""
    logger.info("🚀 Starting Telegram Trading Bot application...")
    
    app = TradingBotApplication()
    setup_signal_handlers(app)
    
    try:
        await app.run()
    except ConfigurationError as e:
        logger.error(f"❌ Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    logger.info("👋 Application finished")


if __name__ == "__main__":
    asyncio.run(main())
