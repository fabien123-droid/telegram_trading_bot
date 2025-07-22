"""
Repository classes for data access in the Telegram Trading Bot.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, update, delete, and_, or_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from loguru import logger

from .models import User, BrokerAccount, Signal, Trade, UserSession, SystemLog, MarketData, Configuration, Notification
from .database import get_db_session
from ..core.exceptions import DatabaseError
from ..security.encryption import encrypt_data, decrypt_data


class BaseRepository:
    """Base repository class with common operations."""
    
    def __init__(self, model_class):
        self.model_class = model_class
    
    async def create(self, data: Dict[str, Any]) -> Any:
        """Create a new record."""
        try:
            async with get_db_session() as session:
                instance = self.model_class(**data)
                session.add(instance)
                await session.flush()
                await session.refresh(instance)
                return instance
        except Exception as e:
            logger.error(f"Error creating {self.model_class.__name__}: {e}")
            raise DatabaseError(f"Failed to create record: {e}")
    
    async def get_by_id(self, record_id: int) -> Optional[Any]:
        """Get record by ID."""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(self.model_class).where(self.model_class.id == record_id)
                )
                return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting {self.model_class.__name__} by ID: {e}")
            return None
    
    async def update(self, record_id: int, data: Dict[str, Any]) -> bool:
        """Update a record."""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    update(self.model_class)
                    .where(self.model_class.id == record_id)
                    .values(**data)
                )
                return result.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating {self.model_class.__name__}: {e}")
            return False
    
    async def delete(self, record_id: int) -> bool:
        """Delete a record."""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    delete(self.model_class).where(self.model_class.id == record_id)
                )
                return result.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting {self.model_class.__name__}: {e}")
            return False
    
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[Any]:
        """Get all records with pagination."""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(self.model_class).limit(limit).offset(offset)
                )
                return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting all {self.model_class.__name__}: {e}")
            return []


class UserRepository(BaseRepository):
    """Repository for User model."""
    
    def __init__(self):
        super().__init__(User)
    
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID."""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(User).where(User.telegram_id == telegram_id)
                )
                return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by telegram_id: {e}")
            return None
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(User).where(User.username == username)
                )
                return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by username: {e}")
            return None
    
    async def get_all_active(self) -> List[User]:
        """Get all active users."""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(User).where(User.is_active == True)
                )
                return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting active users: {e}")
            return []
    
    async def update_last_active(self, user_id: int) -> bool:
        """Update user's last active timestamp."""
        return await self.update(user_id, {'last_active_at': datetime.utcnow()})
    
    async def get_user_settings(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user settings as dictionary."""
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        return {
            'risk_per_trade': user.risk_per_trade,
            'max_positions': user.max_positions,
            'default_stop_loss': user.default_stop_loss,
            'default_take_profit': user.default_take_profit,
            'auto_trading_enabled': user.auto_trading_enabled,
            'signal_alerts': user.signal_alerts,
            'trade_alerts': user.trade_alerts,
            'error_alerts': user.error_alerts,
            'daily_summary': user.daily_summary,
            'min_signal_strength': user.min_signal_strength,
            'technical_weight': user.technical_weight,
            'sentiment_weight': user.sentiment_weight,
            'language': user.language,
            'timezone': user.timezone
        }
    
    async def update_user_settings(self, user_id: int, settings: Dict[str, Any]) -> bool:
        """Update user settings."""
        return await self.update(user_id, settings)
    
    async def get_users_with_auto_trading(self) -> List[User]:
        """Get users with auto trading enabled."""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(User).where(
                        and_(User.is_active == True, User.auto_trading_enabled == True)
                    )
                )
                return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting auto trading users: {e}")
            return []


class BrokerAccountRepository(BaseRepository):
    """Repository for BrokerAccount model."""
    
    def __init__(self):
        super().__init__(BrokerAccount)
    
    async def create(self, data: Dict[str, Any]) -> BrokerAccount:
        """Create broker account with encrypted credentials."""
        try:
            # Encrypt credentials before storing
            if 'credentials' in data:
                data['encrypted_credentials'] = encrypt_data(data.pop('credentials'))
            
            return await super().create(data)
        except Exception as e:
            logger.error(f"Error creating broker account: {e}")
            raise DatabaseError(f"Failed to create broker account: {e}")
    
    async def get_user_accounts(self, user_id: int) -> List[BrokerAccount]:
        """Get all broker accounts for a user."""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(BrokerAccount).where(BrokerAccount.user_id == user_id)
                )
                return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting user broker accounts: {e}")
            return []
    
    async def get_user_account_by_broker(self, user_id: int, broker_name: str) -> Optional[BrokerAccount]:
        """Get user's account for specific broker."""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(BrokerAccount).where(
                        and_(
                            BrokerAccount.user_id == user_id,
                            BrokerAccount.broker_name == broker_name,
                            BrokerAccount.is_active == True
                        )
                    )
                )
                return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user broker account: {e}")
            return None
    
    async def get_decrypted_credentials(self, account_id: int) -> Optional[Dict[str, Any]]:
        """Get decrypted credentials for an account."""
        try:
            account = await self.get_by_id(account_id)
            if not account or not account.encrypted_credentials:
                return None
            
            return decrypt_data(account.encrypted_credentials)
        except Exception as e:
            logger.error(f"Error decrypting credentials: {e}")
            return None
    
    async def update_connection_status(self, account_id: int, is_connected: bool, 
                                     error_message: str = None) -> bool:
        """Update account connection status."""
        data = {
            'is_connected': is_connected,
            'last_connection_at': datetime.utcnow() if is_connected else None,
            'connection_error': error_message
        }
        return await self.update(account_id, data)
    
    async def update_account_balance(self, account_id: int, balance: float, 
                                   currency: str = None) -> bool:
        """Update account balance."""
        data = {
            'account_balance': balance,
            'last_balance_update': datetime.utcnow()
        }
        if currency:
            data['account_currency'] = currency
        
        return await self.update(account_id, data)


class SignalRepository(BaseRepository):
    """Repository for Signal model."""
    
    def __init__(self):
        super().__init__(Signal)
    
    async def get_active_signals(self, user_id: int = None, symbol: str = None) -> List[Signal]:
        """Get active signals."""
        try:
            async with get_db_session() as session:
                query = select(Signal).where(Signal.is_active == True)
                
                if user_id:
                    query = query.where(or_(Signal.user_id == user_id, Signal.user_id.is_(None)))
                
                if symbol:
                    query = query.where(Signal.symbol == symbol)
                
                query = query.order_by(desc(Signal.created_at))
                
                result = await session.execute(query)
                return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting active signals: {e}")
            return []
    
    async def get_signals_by_strength(self, min_strength: str, user_id: int = None) -> List[Signal]:
        """Get signals by minimum strength."""
        strength_order = ['VERY_WEAK', 'WEAK', 'MODERATE', 'STRONG', 'VERY_STRONG']
        min_index = strength_order.index(min_strength) if min_strength in strength_order else 0
        valid_strengths = strength_order[min_index:]
        
        try:
            async with get_db_session() as session:
                query = select(Signal).where(
                    and_(
                        Signal.is_active == True,
                        Signal.strength.in_(valid_strengths)
                    )
                )
                
                if user_id:
                    query = query.where(or_(Signal.user_id == user_id, Signal.user_id.is_(None)))
                
                query = query.order_by(desc(Signal.confidence), desc(Signal.created_at))
                
                result = await session.execute(query)
                return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting signals by strength: {e}")
            return []
    
    async def mark_signal_executed(self, signal_id: int) -> bool:
        """Mark signal as executed."""
        data = {
            'is_executed': True,
            'executed_at': datetime.utcnow()
        }
        return await self.update(signal_id, data)
    
    async def expire_old_signals(self, hours: int = 24) -> int:
        """Expire old signals."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            async with get_db_session() as session:
                result = await session.execute(
                    update(Signal)
                    .where(
                        and_(
                            Signal.is_active == True,
                            Signal.created_at < cutoff_time
                        )
                    )
                    .values(is_active=False)
                )
                return result.rowcount
        except Exception as e:
            logger.error(f"Error expiring old signals: {e}")
            return 0


class TradeRepository(BaseRepository):
    """Repository for Trade model."""
    
    def __init__(self):
        super().__init__(Trade)
    
    async def get_user_trades(self, user_id: int, limit: int = 100, 
                            status: str = None) -> List[Trade]:
        """Get trades for a user."""
        try:
            async with get_db_session() as session:
                query = select(Trade).where(Trade.user_id == user_id)
                
                if status:
                    query = query.where(Trade.status == status)
                
                query = query.order_by(desc(Trade.created_at)).limit(limit)
                
                result = await session.execute(query)
                return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting user trades: {e}")
            return []
    
    async def get_open_trades(self, user_id: int = None) -> List[Trade]:
        """Get open trades."""
        try:
            async with get_db_session() as session:
                query = select(Trade).where(Trade.status.in_(['PENDING', 'FILLED']))
                
                if user_id:
                    query = query.where(Trade.user_id == user_id)
                
                result = await session.execute(query)
                return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting open trades: {e}")
            return []
    
    async def update_trade_status(self, trade_id: int, status: str, 
                                exit_price: float = None) -> bool:
        """Update trade status."""
        data = {'status': status}
        
        if status == 'CLOSED' and exit_price:
            data['exit_price'] = exit_price
            data['closed_at'] = datetime.utcnow()
        
        return await self.update(trade_id, data)
    
    async def update_trade_pnl(self, trade_id: int, realized_pnl: float = None, 
                             unrealized_pnl: float = None) -> bool:
        """Update trade P&L."""
        data = {}
        
        if realized_pnl is not None:
            data['realized_pnl'] = realized_pnl
        
        if unrealized_pnl is not None:
            data['unrealized_pnl'] = unrealized_pnl
        
        return await self.update(trade_id, data)
    
    async def get_trade_statistics(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get trade statistics for a user."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            async with get_db_session() as session:
                # Total trades
                total_result = await session.execute(
                    select(func.count(Trade.id)).where(
                        and_(Trade.user_id == user_id, Trade.created_at >= cutoff_date)
                    )
                )
                total_trades = total_result.scalar() or 0
                
                # Winning trades
                winning_result = await session.execute(
                    select(func.count(Trade.id)).where(
                        and_(
                            Trade.user_id == user_id,
                            Trade.created_at >= cutoff_date,
                            Trade.realized_pnl > 0
                        )
                    )
                )
                winning_trades = winning_result.scalar() or 0
                
                # Total P&L
                pnl_result = await session.execute(
                    select(func.sum(Trade.realized_pnl)).where(
                        and_(Trade.user_id == user_id, Trade.created_at >= cutoff_date)
                    )
                )
                total_pnl = pnl_result.scalar() or 0.0
                
                # Best and worst trades
                best_result = await session.execute(
                    select(func.max(Trade.realized_pnl)).where(
                        and_(Trade.user_id == user_id, Trade.created_at >= cutoff_date)
                    )
                )
                best_trade = best_result.scalar() or 0.0
                
                worst_result = await session.execute(
                    select(func.min(Trade.realized_pnl)).where(
                        and_(Trade.user_id == user_id, Trade.created_at >= cutoff_date)
                    )
                )
                worst_trade = worst_result.scalar() or 0.0
                
                win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
                
                return {
                    'total_trades': total_trades,
                    'winning_trades': winning_trades,
                    'losing_trades': total_trades - winning_trades,
                    'win_rate': win_rate,
                    'total_pnl': total_pnl,
                    'best_trade': best_trade,
                    'worst_trade': worst_trade
                }
                
        except Exception as e:
            logger.error(f"Error getting trade statistics: {e}")
            return {}


class NotificationRepository(BaseRepository):
    """Repository for Notification model."""
    
    def __init__(self):
        super().__init__(Notification)
    
    async def get_user_notifications(self, user_id: int, unread_only: bool = False, 
                                   limit: int = 50) -> List[Notification]:
        """Get notifications for a user."""
        try:
            async with get_db_session() as session:
                query = select(Notification).where(Notification.user_id == user_id)
                
                if unread_only:
                    query = query.where(Notification.is_read == False)
                
                query = query.order_by(desc(Notification.created_at)).limit(limit)
                
                result = await session.execute(query)
                return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting user notifications: {e}")
            return []
    
    async def mark_as_read(self, notification_id: int) -> bool:
        """Mark notification as read."""
        return await self.update(notification_id, {'is_read': True})
    
    async def mark_all_as_read(self, user_id: int) -> int:
        """Mark all notifications as read for a user."""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    update(Notification)
                    .where(
                        and_(
                            Notification.user_id == user_id,
                            Notification.is_read == False
                        )
                    )
                    .values(is_read=True)
                )
                return result.rowcount
        except Exception as e:
            logger.error(f"Error marking all notifications as read: {e}")
            return 0
    
    async def create_notification(self, user_id: int, notification_type: str, 
                                title: str, message: str, priority: str = 'normal',
                                metadata: Dict[str, Any] = None) -> Optional[Notification]:
        """Create a new notification."""
        data = {
            'user_id': user_id,
            'type': notification_type,
            'title': title,
            'message': message,
            'priority': priority,
            'metadata': metadata
        }
        return await self.create(data)


class ConfigurationRepository(BaseRepository):
    """Repository for Configuration model."""
    
    def __init__(self):
        super().__init__(Configuration)
    
    async def get_by_key(self, key: str) -> Optional[Configuration]:
        """Get configuration by key."""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(Configuration).where(Configuration.key == key)
                )
                return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting configuration by key: {e}")
            return None
    
    async def get_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value with type conversion."""
        config = await self.get_by_key(key)
        if not config:
            return default
        
        try:
            if config.value_type == 'int':
                return int(config.value)
            elif config.value_type == 'float':
                return float(config.value)
            elif config.value_type == 'bool':
                return config.value.lower() in ('true', '1', 'yes', 'on')
            elif config.value_type == 'json':
                import json
                return json.loads(config.value)
            else:
                return config.value
        except (ValueError, TypeError) as e:
            logger.error(f"Error converting configuration value: {e}")
            return default
    
    async def set_value(self, key: str, value: Any, value_type: str = 'string', 
                       description: str = None) -> bool:
        """Set configuration value."""
        try:
            # Convert value to string
            if value_type == 'json':
                import json
                str_value = json.dumps(value)
            else:
                str_value = str(value)
            
            # Check if config exists
            existing = await self.get_by_key(key)
            
            if existing:
                # Update existing
                return await self.update(existing.id, {
                    'value': str_value,
                    'value_type': value_type,
                    'description': description or existing.description
                })
            else:
                # Create new
                config = await self.create({
                    'key': key,
                    'value': str_value,
                    'value_type': value_type,
                    'description': description
                })
                return config is not None
                
        except Exception as e:
            logger.error(f"Error setting configuration value: {e}")
            return False

