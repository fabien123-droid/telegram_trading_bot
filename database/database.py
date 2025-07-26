"""
Database management for the Telegram Trading Bot.
"""

import asyncio
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from loguru import logger

# Imports absolus depuis la racine
try:
    from database.models import Base
    logger.info("Successfully imported database.models")
except ImportError as e:
    logger.warning(f"Failed to import database.models: {e}")
    # Fallback temporaire - créer une Base simple
    from sqlalchemy.ext.declarative import declarative_base
    Base = declarative_base()
    logger.info("Using fallback Base class")

try:
    from core.config import get_settings
    logger.info("Successfully imported core.config")
except ImportError as e:
    logger.error(f"Failed to import core.config: {e}")
    raise ImportError("Cannot import core.config - this is required")

try:
    from core.exceptions import DatabaseError
    logger.info("Successfully imported core.exceptions")
except ImportError as e:
    logger.warning(f"Failed to import core.exceptions: {e}")
    # Fallback
    class DatabaseError(Exception):
        pass


class DatabaseManager:
    """Database manager for handling connections and sessions."""
    
    def __init__(self):
        self.settings = get_settings()
        self.engine = None
        self.async_engine = None
        self.session_factory = None
        self.async_session_factory = None
        
    async def initialize(self):
        """Initialize database connections."""
        try:
            # Create engines
            database_url = getattr(self.settings, 'database_url', None)
            
            # Fallback pour une base SQLite simple si pas d'URL configurée
            if not database_url:
                database_url = "sqlite:///./trading_bot.db"
                logger.info(f"Using default SQLite database: {database_url}")
            
            # Convert SQLite URL for async if needed
            if database_url.startswith('sqlite:///'):
                async_database_url = database_url.replace('sqlite:///', 'sqlite+aiosqlite:///')
            else:
                async_database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://')
            
            # Sync engine for migrations and initial setup
            self.engine = create_engine(
                database_url,
                echo=getattr(self.settings, 'debug', False),
                pool_pre_ping=True,
                connect_args={"check_same_thread": False} if "sqlite" in database_url else {}
            )
            
            # Async engine for application use
            self.async_engine = create_async_engine(
                async_database_url,
                echo=getattr(self.settings, 'debug', False),
                pool_pre_ping=True,
                connect_args={"check_same_thread": False} if "sqlite" in async_database_url else {}
            )
            
            # Session factories
            self.session_factory = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False
            )
            
            self.async_session_factory = async_sessionmaker(
                bind=self.async_engine,
                class_=AsyncSession,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )
            
            # Create tables
            await self.create_tables()
            
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise DatabaseError(f"Database initialization failed: {e}")
    
    async def create_tables(self):
        """Create database tables."""
        try:
            # Use sync engine for table creation
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise DatabaseError(f"Table creation failed: {e}")
    
    async def close(self):
        """Close database connections."""
        try:
            if self.async_engine:
                await self.async_engine.dispose()
            
            if self.engine:
                self.engine.dispose()
            
            logger.info("Database connections closed")
            
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async database session."""
        if not self.async_session_factory:
            raise DatabaseError("Database not initialized")
        
        async with self.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {e}")
                raise
            finally:
                await session.close()
    
    def get_sync_session(self) -> Session:
        """Get sync database session."""
        if not self.session_factory:
            raise DatabaseError("Database not initialized")
        
        return self.session_factory()


# Global database manager instance
db_manager = DatabaseManager()


async def init_database():
    """Initialize the database."""
    try:
        await db_manager.initialize()
        logger.info("✅ Database initialization completed")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise


async def close_database():
    """Close database connections."""
    try:
        await db_manager.close()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"❌ Error closing database: {e}")


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session context manager."""
    async with db_manager.get_session() as session:
        yield session


def get_sync_db_session() -> Session:
    """Get sync database session."""
    return db_manager.get_sync_session()


# Database event listeners for SQLite
@event.listens_for(create_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite pragmas for better performance and reliability."""
    if 'sqlite' in str(dbapi_connection):
        cursor = dbapi_connection.cursor()
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys=ON")
        # Set journal mode to WAL for better concurrency
        cursor.execute("PRAGMA journal_mode=WAL")
        # Set synchronous mode to NORMAL for better performance
        cursor.execute("PRAGMA synchronous=NORMAL")
        # Set cache size
        cursor.execute("PRAGMA cache_size=10000")
        # Set temp store to memory
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()


class DatabaseHealthCheck:
    """Database health check utilities."""
    
    @staticmethod
    async def check_connection() -> bool:
        """Check if database connection is healthy."""
        try:
            async with get_db_session() as session:
                result = await session.execute("SELECT 1")
                return result.scalar() == 1
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    @staticmethod
    async def get_connection_info() -> dict:
        """Get database connection information."""
        try:
            info = {
                'engine_url': str(db_manager.async_engine.url) if db_manager.async_engine else None,
                'pool_size': db_manager.async_engine.pool.size() if db_manager.async_engine else None,
                'checked_out': db_manager.async_engine.pool.checkedout() if db_manager.async_engine else None,
                'overflow': db_manager.async_engine.pool.overflow() if db_manager.async_engine else None,
                'is_connected': await DatabaseHealthCheck.check_connection()
            }
            return info
        except Exception as e:
            logger.error(f"Failed to get database connection info: {e}")
            return {'error': str(e)}


class DatabaseMigration:
    """Database migration utilities."""
    
    @staticmethod
    def create_migration_table():
        """Create migration tracking table."""
        try:
            with db_manager.get_sync_session() as session:
                session.execute("""
                    CREATE TABLE IF NOT EXISTS migrations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        version VARCHAR(50) NOT NULL UNIQUE,
                        description TEXT,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                session.commit()
        except Exception as e:
            logger.error(f"Failed to create migration table: {e}")
            raise DatabaseError(f"Migration table creation failed: {e}")
    
    @staticmethod
    def get_applied_migrations() -> list:
        """Get list of applied migrations."""
        try:
            with db_manager.get_sync_session() as session:
                result = session.execute("SELECT version FROM migrations ORDER BY applied_at")
                return [row[0] for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get applied migrations: {e}")
            return []
    
    @staticmethod
    def mark_migration_applied(version: str, description: str = None):
        """Mark a migration as applied."""
        try:
            with db_manager.get_sync_session() as session:
                session.execute(
                    "INSERT INTO migrations (version, description) VALUES (?, ?)",
                    (version, description)
                )
                session.commit()
                logger.info(f"Migration {version} marked as applied")
        except Exception as e:
            logger.error(f"Failed to mark migration as applied: {e}")
            raise DatabaseError(f"Migration marking failed: {e}")


class DatabaseBackup:
    """Database backup utilities."""
    
    @staticmethod
    async def create_backup(backup_path: str) -> bool:
        """Create database backup."""
        try:
            # This is a simplified backup for SQLite
            # For production, use proper backup tools
            database_url = getattr(db_manager.settings, 'database_url', "sqlite:///./trading_bot.db")
            if 'sqlite' in database_url:
                import shutil
                db_path = database_url.replace('sqlite:///', '')
                shutil.copy2(db_path, backup_path)
                logger.info(f"Database backup created: {backup_path}")
                return True
            else:
                logger.warning("Backup not implemented for non-SQLite databases")
                return False
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return False
    
    @staticmethod
    async def restore_backup(backup_path: str) -> bool:
        """Restore database from backup."""
        try:
            # This is a simplified restore for SQLite
            database_url = getattr(db_manager.settings, 'database_url', "sqlite:///./trading_bot.db")
            if 'sqlite' in database_url:
                import shutil
                db_path = database_url.replace('sqlite:///', '')
                
                # Close connections first
                await db_manager.close()
                
                # Restore backup
                shutil.copy2(backup_path, db_path)
                
                # Reinitialize
                await db_manager.initialize()
                
                logger.info(f"Database restored from backup: {backup_path}")
                return True
            else:
                logger.warning("Restore not implemented for non-SQLite databases")
                return False
        except Exception as e:
            logger.error(f"Database restore failed: {e}")
            return False
