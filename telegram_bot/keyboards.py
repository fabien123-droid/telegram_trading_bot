"""
Telegram keyboards module for the Trading Bot.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton


def get_main_keyboard() -> InlineKeyboardMarkup:
    """Get the main menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
            InlineKeyboardButton("💼 Accounts", callback_data="accounts")
        ],
        [
            InlineKeyboardButton("💹 Trading", callback_data="trading"),
            InlineKeyboardButton("📊 Signals", callback_data="signals")
        ],
        [
            InlineKeyboardButton("📈 History", callback_data="history"),
            InlineKeyboardButton("ℹ️ Help", callback_data="help")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Get the settings menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("🎯 Risk Management", callback_data="risk_settings"),
            InlineKeyboardButton("📱 Notifications", callback_data="notification_settings")
        ],
        [
            InlineKeyboardButton("📊 Signal Settings", callback_data="signal_settings"),
            InlineKeyboardButton("🤖 Auto Trading", callback_data="auto_trading_settings")
        ],
        [
            InlineKeyboardButton("🔒 Security", callback_data="security_settings"),
            InlineKeyboardButton("🌐 Language", callback_data="language_settings")
        ],
        [
            InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_account_keyboard() -> InlineKeyboardMarkup:
    """Get the account management keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("➕ Add Deriv Account", callback_data="setup_account_deriv"),
            InlineKeyboardButton("➕ Add Binance Account", callback_data="setup_account_binance")
        ],
        [
            InlineKeyboardButton("➕ Add MT5 Account", callback_data="setup_account_mt5"),
            InlineKeyboardButton("➕ Add IB Account", callback_data="setup_account_ib")
        ],
        [
            InlineKeyboardButton("🔄 Refresh Accounts", callback_data="refresh_accounts"),
            InlineKeyboardButton("📊 Account Status", callback_data="account_status")
        ],
        [
            InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_trading_keyboard() -> InlineKeyboardMarkup:
    """Get the trading menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("📊 View Signals", callback_data="view_signals"),
            InlineKeyboardButton("🎯 Manual Trade", callback_data="manual_trade")
        ],
        [
            InlineKeyboardButton("🤖 Auto Trading", callback_data="toggle_auto_trading"),
            InlineKeyboardButton("📈 Open Positions", callback_data="view_positions")
        ],
        [
            InlineKeyboardButton("📋 Pending Orders", callback_data="view_orders"),
            InlineKeyboardButton("💰 Account Balance", callback_data="view_balance")
        ],
        [
            InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_signals_keyboard() -> InlineKeyboardMarkup:
    """Get the signals menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("🔄 Refresh Signals", callback_data="refresh_signals"),
            InlineKeyboardButton("⚙️ Signal Settings", callback_data="signal_settings")
        ],
        [
            InlineKeyboardButton("📈 Bullish Signals", callback_data="filter_bullish"),
            InlineKeyboardButton("📉 Bearish Signals", callback_data="filter_bearish")
        ],
        [
            InlineKeyboardButton("⭐ Strong Signals", callback_data="filter_strong"),
            InlineKeyboardButton("📊 All Signals", callback_data="filter_all")
        ],
        [
            InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_history_keyboard() -> InlineKeyboardMarkup:
    """Get the history menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("📊 Detailed Report", callback_data="detailed_report"),
            InlineKeyboardButton("📈 Performance Chart", callback_data="performance_chart")
        ],
        [
            InlineKeyboardButton("💰 P&L Summary", callback_data="pnl_summary"),
            InlineKeyboardButton("📋 Trade Log", callback_data="trade_log")
        ],
        [
            InlineKeyboardButton("📅 This Week", callback_data="history_week"),
            InlineKeyboardButton("📅 This Month", callback_data="history_month")
        ],
        [
            InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_risk_settings_keyboard() -> InlineKeyboardMarkup:
    """Get the risk management settings keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("💰 Risk Per Trade", callback_data="set_risk_per_trade"),
            InlineKeyboardButton("📊 Max Positions", callback_data="set_max_positions")
        ],
        [
            InlineKeyboardButton("🛑 Stop Loss %", callback_data="set_stop_loss"),
            InlineKeyboardButton("🎯 Take Profit %", callback_data="set_take_profit")
        ],
        [
            InlineKeyboardButton("💸 Max Daily Loss", callback_data="set_max_daily_loss"),
            InlineKeyboardButton("🔒 Emergency Stop", callback_data="emergency_stop")
        ],
        [
            InlineKeyboardButton("⬅️ Back to Settings", callback_data="settings")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_notification_settings_keyboard() -> InlineKeyboardMarkup:
    """Get the notification settings keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("📊 Signal Alerts", callback_data="toggle_signal_alerts"),
            InlineKeyboardButton("💹 Trade Alerts", callback_data="toggle_trade_alerts")
        ],
        [
            InlineKeyboardButton("⚠️ Error Alerts", callback_data="toggle_error_alerts"),
            InlineKeyboardButton("📈 Daily Summary", callback_data="toggle_daily_summary")
        ],
        [
            InlineKeyboardButton("🔔 All Notifications", callback_data="toggle_all_notifications"),
            InlineKeyboardButton("🔕 Mute All", callback_data="mute_all_notifications")
        ],
        [
            InlineKeyboardButton("⬅️ Back to Settings", callback_data="settings")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_signal_settings_keyboard() -> InlineKeyboardMarkup:
    """Get the signal settings keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("📊 Indicators", callback_data="configure_indicators"),
            InlineKeyboardButton("🎯 Signal Strength", callback_data="set_signal_strength")
        ],
        [
            InlineKeyboardButton("⏰ Timeframes", callback_data="configure_timeframes"),
            InlineKeyboardButton("💱 Symbols", callback_data="configure_symbols")
        ],
        [
            InlineKeyboardButton("🧠 Sentiment Weight", callback_data="set_sentiment_weight"),
            InlineKeyboardButton("📈 Technical Weight", callback_data="set_technical_weight")
        ],
        [
            InlineKeyboardButton("⬅️ Back to Settings", callback_data="settings")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_auto_trading_keyboard() -> InlineKeyboardMarkup:
    """Get the auto trading settings keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("🤖 Enable Auto Trading", callback_data="enable_auto_trading"),
            InlineKeyboardButton("⏸️ Disable Auto Trading", callback_data="disable_auto_trading")
        ],
        [
            InlineKeyboardButton("⚙️ Trading Strategy", callback_data="configure_strategy"),
            InlineKeyboardButton("🎯 Entry Conditions", callback_data="configure_entry")
        ],
        [
            InlineKeyboardButton("🛑 Exit Conditions", callback_data="configure_exit"),
            InlineKeyboardButton("⏰ Trading Hours", callback_data="configure_hours")
        ],
        [
            InlineKeyboardButton("⬅️ Back to Settings", callback_data="settings")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_confirmation_keyboard(action: str) -> InlineKeyboardMarkup:
    """Get a confirmation keyboard for actions."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_{action}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{action}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_trade_keyboard(signal_id: str) -> InlineKeyboardMarkup:
    """Get keyboard for trade actions."""
    keyboard = [
        [
            InlineKeyboardButton("📈 Execute Trade", callback_data=f"execute_trade_{signal_id}"),
            InlineKeyboardButton("📊 View Details", callback_data=f"signal_details_{signal_id}")
        ],
        [
            InlineKeyboardButton("⚙️ Modify Signal", callback_data=f"modify_signal_{signal_id}"),
            InlineKeyboardButton("❌ Ignore Signal", callback_data=f"ignore_signal_{signal_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_position_keyboard(position_id: str) -> InlineKeyboardMarkup:
    """Get keyboard for position management."""
    keyboard = [
        [
            InlineKeyboardButton("🔒 Close Position", callback_data=f"close_position_{position_id}"),
            InlineKeyboardButton("⚙️ Modify SL/TP", callback_data=f"modify_position_{position_id}")
        ],
        [
            InlineKeyboardButton("📊 Position Details", callback_data=f"position_details_{position_id}"),
            InlineKeyboardButton("📈 Add to Position", callback_data=f"add_position_{position_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_broker_selection_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for broker selection."""
    keyboard = [
        [
            InlineKeyboardButton("🟢 Deriv", callback_data="select_broker_deriv"),
            InlineKeyboardButton("🟡 Binance", callback_data="select_broker_binance")
        ],
        [
            InlineKeyboardButton("🔵 MetaTrader 5", callback_data="select_broker_mt5"),
            InlineKeyboardButton("🟣 Interactive Brokers", callback_data="select_broker_ib")
        ],
        [
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_broker_selection")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_symbol_selection_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for symbol selection."""
    keyboard = [
        [
            InlineKeyboardButton("💱 EURUSD", callback_data="select_symbol_EURUSD"),
            InlineKeyboardButton("💱 GBPUSD", callback_data="select_symbol_GBPUSD")
        ],
        [
            InlineKeyboardButton("💱 USDJPY", callback_data="select_symbol_USDJPY"),
            InlineKeyboardButton("💱 USDCHF", callback_data="select_symbol_USDCHF")
        ],
        [
            InlineKeyboardButton("🪙 BTCUSD", callback_data="select_symbol_BTCUSD"),
            InlineKeyboardButton("🪙 ETHUSD", callback_data="select_symbol_ETHUSD")
        ],
        [
            InlineKeyboardButton("🏅 XAUUSD", callback_data="select_symbol_XAUUSD"),
            InlineKeyboardButton("📊 US30", callback_data="select_symbol_US30")
        ],
        [
            InlineKeyboardButton("➕ Add Custom", callback_data="add_custom_symbol"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_symbol_selection")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_timeframe_selection_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for timeframe selection."""
    keyboard = [
        [
            InlineKeyboardButton("1m", callback_data="select_timeframe_1m"),
            InlineKeyboardButton("5m", callback_data="select_timeframe_5m"),
            InlineKeyboardButton("15m", callback_data="select_timeframe_15m")
        ],
        [
            InlineKeyboardButton("30m", callback_data="select_timeframe_30m"),
            InlineKeyboardButton("1h", callback_data="select_timeframe_1h"),
            InlineKeyboardButton("4h", callback_data="select_timeframe_4h")
        ],
        [
            InlineKeyboardButton("1d", callback_data="select_timeframe_1d"),
            InlineKeyboardButton("1w", callback_data="select_timeframe_1w")
        ],
        [
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_timeframe_selection")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Get the admin panel keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("👥 User Stats", callback_data="admin_user_stats"),
            InlineKeyboardButton("💹 Trading Stats", callback_data="admin_trading_stats")
        ],
        [
            InlineKeyboardButton("🔧 System Status", callback_data="admin_system_status"),
            InlineKeyboardButton("📊 Performance", callback_data="admin_performance")
        ],
        [
            InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
            InlineKeyboardButton("🚨 Emergency Stop", callback_data="admin_emergency_stop")
        ],
        [
            InlineKeyboardButton("📋 Logs", callback_data="admin_logs"),
            InlineKeyboardButton("⚙️ Config", callback_data="admin_config")
        ],
        [
            InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_yes_no_keyboard(action: str) -> InlineKeyboardMarkup:
    """Get a simple yes/no keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes", callback_data=f"yes_{action}"),
            InlineKeyboardButton("❌ No", callback_data=f"no_{action}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_keyboard(destination: str = "main_menu") -> InlineKeyboardMarkup:
    """Get a simple back button keyboard."""
    keyboard = [
        [InlineKeyboardButton("⬅️ Back", callback_data=destination)]
    ]
    return InlineKeyboardMarkup(keyboard)

