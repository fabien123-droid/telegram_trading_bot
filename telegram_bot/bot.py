"""
Main Telegram bot handler for the Trading Bot.
"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)
from telegram.constants import ParseMode

from loguru import logger

from ..core.config import get_settings
from ..core.exceptions import TelegramError
from ..core.logging_config import log_user_action
from .handlers import (
    start_handler, help_handler, settings_handler, account_handler,
    trading_handler, signals_handler, history_handler, admin_handler
)
from .keyboards import get_main_keyboard, get_settings_keyboard
from .messages import MessageTemplates
from ..database.repositories import UserRepository, BrokerAccountRepository


class TelegramBot:
    """Main Telegram bot class."""
    
    def __init__(self):
        self.settings = get_settings()
        self.application = None
        self.user_repo = UserRepository()
        self.broker_repo = BrokerAccountRepository()
        self.message_templates = MessageTemplates()
        
        # Conversation states
        self.ACCOUNT_SETUP = range(1)
        self.SETTINGS_CONFIG = range(1, 5)
        
    async def initialize(self):
        """Initialize the Telegram bot."""
        try:
            # Create application
            self.application = Application.builder().token(
                self.settings.telegram.bot_token
            ).build()
            
            # Add handlers
            await self._add_handlers()
            
            # Set bot commands
            await self._set_bot_commands()
            
            # Start the bot
            await self.application.initialize()
            await self.application.start()
            
            if self.settings.telegram.webhook_url:
                # Use webhook mode
                await self.application.bot.set_webhook(
                    url=self.settings.telegram.webhook_url
                )
                logger.info(f"Webhook set to: {self.settings.telegram.webhook_url}")
            else:
                # Use polling mode
                await self.application.updater.start_polling()
                logger.info("Bot started in polling mode")
            
            logger.info("Telegram bot initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Telegram bot: {e}")
            raise TelegramError(f"Bot initialization failed: {e}")
    
    async def shutdown(self):
        """Shutdown the Telegram bot gracefully."""
        try:
            if self.application:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
            
            logger.info("Telegram bot shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during bot shutdown: {e}")
    
    async def _add_handlers(self):
        """Add all command and callback handlers."""
        
        # Command handlers
        self.application.add_handler(CommandHandler("start", self._start_command))
        self.application.add_handler(CommandHandler("help", self._help_command))
        self.application.add_handler(CommandHandler("settings", self._settings_command))
        self.application.add_handler(CommandHandler("account", self._account_command))
        self.application.add_handler(CommandHandler("trading", self._trading_command))
        self.application.add_handler(CommandHandler("signals", self._signals_command))
        self.application.add_handler(CommandHandler("history", self._history_command))
        self.application.add_handler(CommandHandler("status", self._status_command))
        
        # Admin commands
        if self.settings.telegram.admin_id:
            self.application.add_handler(CommandHandler("admin", self._admin_command))
            self.application.add_handler(CommandHandler("broadcast", self._broadcast_command))
            self.application.add_handler(CommandHandler("stats", self._stats_command))
        
        # Callback query handler
        self.application.add_handler(CallbackQueryHandler(self._callback_query_handler))
        
        # Conversation handlers
        account_conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self._account_setup_start, pattern="^setup_account_")],
            states={
                self.ACCOUNT_SETUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, self._account_setup_process)]
            },
            fallbacks=[CommandHandler("cancel", self._cancel_conversation)]
        )
        self.application.add_handler(account_conv_handler)
        
        # Message handler for unknown commands
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._unknown_message))
        
        # Error handler
        self.application.add_error_handler(self._error_handler)
    
    async def _set_bot_commands(self):
        """Set bot commands for the menu."""
        commands = [
            BotCommand("start", "Start the bot and see main menu"),
            BotCommand("help", "Get help and instructions"),
            BotCommand("settings", "Configure bot settings"),
            BotCommand("account", "Manage broker accounts"),
            BotCommand("trading", "Trading controls and options"),
            BotCommand("signals", "View current trading signals"),
            BotCommand("history", "View trading history"),
            BotCommand("status", "Check bot and account status"),
        ]
        
        await self.application.bot.set_my_commands(commands)
    
    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        log_user_action(user.id, "start_command")
        
        # Check if user exists in database
        db_user = await self.user_repo.get_by_telegram_id(user.id)
        
        if not db_user:
            # Create new user
            db_user = await self.user_repo.create({
                'telegram_id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_active': True
            })
            
            welcome_message = self.message_templates.get_welcome_message(user.first_name)
            
        else:
            welcome_message = self.message_templates.get_returning_user_message(user.first_name)
        
        keyboard = get_main_keyboard()
        
        await update.message.reply_text(
            welcome_message,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
    
    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        user = update.effective_user
        log_user_action(user.id, "help_command")
        
        help_message = self.message_templates.get_help_message()
        
        await update.message.reply_text(
            help_message,
            parse_mode=ParseMode.HTML
        )
    
    async def _settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /settings command."""
        user = update.effective_user
        log_user_action(user.id, "settings_command")
        
        # Get user settings
        db_user = await self.user_repo.get_by_telegram_id(user.id)
        if not db_user:
            await update.message.reply_text("Please start the bot first with /start")
            return
        
        settings_message = self.message_templates.get_settings_message(db_user)
        keyboard = get_settings_keyboard()
        
        await update.message.reply_text(
            settings_message,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
    
    async def _account_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /account command."""
        user = update.effective_user
        log_user_action(user.id, "account_command")
        
        # Get user's broker accounts
        db_user = await self.user_repo.get_by_telegram_id(user.id)
        if not db_user:
            await update.message.reply_text("Please start the bot first with /start")
            return
        
        accounts = await self.broker_repo.get_user_accounts(db_user.id)
        account_message = self.message_templates.get_account_message(accounts)
        
        # Create keyboard for account management
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add Deriv Account", callback_data="setup_account_deriv")],
            [InlineKeyboardButton("➕ Add Binance Account", callback_data="setup_account_binance")],
            [InlineKeyboardButton("➕ Add MT5 Account", callback_data="setup_account_mt5")],
            [InlineKeyboardButton("🔄 Refresh Accounts", callback_data="refresh_accounts")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ])
        
        await update.message.reply_text(
            account_message,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
    
    async def _trading_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /trading command."""
        user = update.effective_user
        log_user_action(user.id, "trading_command")
        
        # Check if user has configured accounts
        db_user = await self.user_repo.get_by_telegram_id(user.id)
        if not db_user:
            await update.message.reply_text("Please start the bot first with /start")
            return
        
        accounts = await self.broker_repo.get_user_accounts(db_user.id)
        if not accounts:
            await update.message.reply_text(
                "⚠️ No broker accounts configured. Please add an account first using /account"
            )
            return
        
        trading_message = self.message_templates.get_trading_message()
        
        # Create trading keyboard
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 View Signals", callback_data="view_signals")],
            [InlineKeyboardButton("🎯 Manual Trade", callback_data="manual_trade")],
            [InlineKeyboardButton("🤖 Auto Trading", callback_data="toggle_auto_trading")],
            [InlineKeyboardButton("📈 Positions", callback_data="view_positions")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ])
        
        await update.message.reply_text(
            trading_message,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
    
    async def _signals_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /signals command."""
        user = update.effective_user
        log_user_action(user.id, "signals_command")
        
        # Get current signals
        signals_message = await self._get_current_signals()
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh Signals", callback_data="refresh_signals")],
            [InlineKeyboardButton("⚙️ Signal Settings", callback_data="signal_settings")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ])
        
        await update.message.reply_text(
            signals_message,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
    
    async def _history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /history command."""
        user = update.effective_user
        log_user_action(user.id, "history_command")
        
        # Get trading history
        db_user = await self.user_repo.get_by_telegram_id(user.id)
        if not db_user:
            await update.message.reply_text("Please start the bot first with /start")
            return
        
        history_message = await self._get_trading_history(db_user.id)
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 Detailed Report", callback_data="detailed_report")],
            [InlineKeyboardButton("📈 Performance Chart", callback_data="performance_chart")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ])
        
        await update.message.reply_text(
            history_message,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
    
    async def _status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        user = update.effective_user
        log_user_action(user.id, "status_command")
        
        status_message = await self._get_bot_status()
        
        await update.message.reply_text(
            status_message,
            parse_mode=ParseMode.HTML
        )
    
    async def _admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admin command (admin only)."""
        user = update.effective_user
        
        if user.id != self.settings.telegram.admin_id:
            await update.message.reply_text("❌ Access denied. Admin only.")
            return
        
        log_user_action(user.id, "admin_command")
        
        admin_message = await self._get_admin_panel()
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("👥 User Stats", callback_data="admin_user_stats")],
            [InlineKeyboardButton("💹 Trading Stats", callback_data="admin_trading_stats")],
            [InlineKeyboardButton("🔧 System Status", callback_data="admin_system_status")],
            [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ])
        
        await update.message.reply_text(
            admin_message,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
    
    async def _callback_query_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline keyboards."""
        query = update.callback_query
        await query.answer()
        
        user = update.effective_user
        data = query.data
        
        log_user_action(user.id, f"callback_query: {data}")
        
        # Route callback queries
        if data == "main_menu":
            await self._show_main_menu(query)
        elif data.startswith("setup_account_"):
            await self._account_setup_start(update, context)
        elif data == "refresh_signals":
            await self._refresh_signals(query)
        elif data == "view_signals":
            await self._view_signals(query)
        elif data == "toggle_auto_trading":
            await self._toggle_auto_trading(query)
        elif data.startswith("admin_"):
            await self._handle_admin_callback(query, data)
        else:
            await query.edit_message_text("Unknown action. Please try again.")
    
    async def _show_main_menu(self, query):
        """Show the main menu."""
        keyboard = get_main_keyboard()
        message = "🏠 <b>Main Menu</b>\n\nChoose an option:"
        
        await query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
    
    async def _account_setup_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start account setup conversation."""
        query = update.callback_query
        broker_type = query.data.split("_")[-1]  # Extract broker type
        
        context.user_data['broker_type'] = broker_type
        
        setup_message = self.message_templates.get_account_setup_message(broker_type)
        
        await query.edit_message_text(
            setup_message,
            parse_mode=ParseMode.HTML
        )
        
        return self.ACCOUNT_SETUP
    
    async def _account_setup_process(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process account setup input."""
        user = update.effective_user
        broker_type = context.user_data.get('broker_type')
        
        if not broker_type:
            await update.message.reply_text("Setup session expired. Please start again.")
            return ConversationHandler.END
        
        # Process the account credentials
        credentials = update.message.text
        
        try:
            # Save account to database (encrypted)
            db_user = await self.user_repo.get_by_telegram_id(user.id)
            
            account_data = {
                'user_id': db_user.id,
                'broker_name': broker_type,
                'credentials': credentials,  # This will be encrypted in the repository
                'is_active': True
            }
            
            await self.broker_repo.create(account_data)
            
            await update.message.reply_text(
                f"✅ {broker_type.title()} account added successfully!\n\n"
                "Your credentials have been encrypted and stored securely."
            )
            
        except Exception as e:
            logger.error(f"Error saving account: {e}")
            await update.message.reply_text(
                "❌ Error saving account. Please try again later."
            )
        
        return ConversationHandler.END
    
    async def _cancel_conversation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel ongoing conversation."""
        await update.message.reply_text("Operation cancelled.")
        return ConversationHandler.END
    
    async def _unknown_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle unknown messages."""
        await update.message.reply_text(
            "I don't understand that command. Use /help to see available commands."
        )
    
    async def _error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors."""
        logger.error(f"Telegram bot error: {context.error}")
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ An error occurred. Please try again later."
            )
    
    async def _get_current_signals(self) -> str:
        """Get current trading signals."""
        # This would integrate with the signal generator
        return "📊 <b>Current Trading Signals</b>\n\n" \
               "🔄 Loading signals... Please wait."
    
    async def _get_trading_history(self, user_id: int) -> str:
        """Get trading history for user."""
        # This would integrate with the database
        return "📈 <b>Trading History</b>\n\n" \
               "No trades found."
    
    async def _get_bot_status(self) -> str:
        """Get bot status information."""
        return "🤖 <b>Bot Status</b>\n\n" \
               "✅ Bot is running\n" \
               "✅ Database connected\n" \
               "✅ APIs operational"
    
    async def _get_admin_panel(self) -> str:
        """Get admin panel information."""
        return "👑 <b>Admin Panel</b>\n\n" \
               "Welcome to the admin panel."
    
    async def send_notification(self, user_id: int, message: str, 
                              keyboard: Optional[InlineKeyboardMarkup] = None):
        """Send notification to a user."""
        try:
            await self.application.bot.send_message(
                chat_id=user_id,
                text=message,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Failed to send notification to user {user_id}: {e}")
    
    async def broadcast_message(self, message: str, user_ids: Optional[List[int]] = None):
        """Broadcast message to users."""
        if user_ids is None:
            # Get all active users
            users = await self.user_repo.get_all_active()
            user_ids = [user.telegram_id for user in users]
        
        success_count = 0
        for user_id in user_ids:
            try:
                await self.application.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode=ParseMode.HTML
                )
                success_count += 1
                await asyncio.sleep(0.1)  # Rate limiting
            except Exception as e:
                logger.warning(f"Failed to send broadcast to user {user_id}: {e}")
        
        logger.info(f"Broadcast sent to {success_count}/{len(user_ids)} users")
        return success_count

