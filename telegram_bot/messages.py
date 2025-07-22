"""
Message templates for the Telegram Trading Bot.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime


class MessageTemplates:
    """Message templates for the Telegram bot."""
    
    def get_welcome_message(self, first_name: str) -> str:
        """Get welcome message for new users."""
        return f"""
🎉 <b>Welcome to Trading Bot, {first_name}!</b>

I'm your personal trading assistant, designed to help you trade smarter with:

🤖 <b>Automated Trading</b>
• Multi-broker support (Deriv, Binance, MT5, IB)
• Advanced technical analysis
• Real-time market sentiment analysis

📊 <b>Smart Signals</b>
• RSI, MACD, Bollinger Bands, Stochastic
• Support/Resistance levels
• News sentiment integration

🛡️ <b>Risk Management</b>
• Configurable position sizing
• Stop-loss and take-profit automation
• Daily loss limits

🔒 <b>Security</b>
• Encrypted credential storage
• Multi-user support
• Real-time notifications

<b>Getting Started:</b>
1. Configure your broker accounts (/account)
2. Set up your risk preferences (/settings)
3. Start receiving trading signals (/signals)

Use /help for detailed instructions or choose an option below:
        """
    
    def get_returning_user_message(self, first_name: str) -> str:
        """Get welcome back message for returning users."""
        return f"""
👋 <b>Welcome back, {first_name}!</b>

Your trading assistant is ready to help you make informed trading decisions.

📊 <b>Quick Actions:</b>
• View current signals
• Check your positions
• Review trading history
• Adjust settings

Choose an option below to get started:
        """
    
    def get_help_message(self) -> str:
        """Get help message with all commands."""
        return """
📚 <b>Trading Bot Help</b>

<b>🔧 Setup Commands:</b>
/start - Start the bot and see main menu
/account - Manage broker accounts
/settings - Configure bot settings

<b>💹 Trading Commands:</b>
/trading - Trading controls and options
/signals - View current trading signals
/history - View trading history
/status - Check bot and account status

<b>📊 Features:</b>

<b>Multi-Broker Support:</b>
• Deriv (Binary Options, Forex, Indices)
• Binance (Crypto, Futures)
• MetaTrader 5 (Forex, CFDs)
• Interactive Brokers (Stocks, Options)

<b>Technical Analysis:</b>
• RSI (Relative Strength Index)
• MACD (Moving Average Convergence Divergence)
• Bollinger Bands
• Stochastic Oscillator
• Support/Resistance levels

<b>Sentiment Analysis:</b>
• News sentiment from multiple sources
• Social media sentiment tracking
• Market mood indicators

<b>Risk Management:</b>
• Position sizing based on account balance
• Automatic stop-loss and take-profit
• Maximum daily loss limits
• Emergency stop functionality

<b>🔒 Security:</b>
All your broker credentials are encrypted and stored securely. The bot never stores your passwords in plain text.

<b>💡 Tips:</b>
• Start with small position sizes
• Always set stop-losses
• Review signals before trading
• Monitor your risk exposure

Need more help? Contact support or check our documentation.
        """
    
    def get_settings_message(self, user_data: Dict) -> str:
        """Get settings overview message."""
        return f"""
⚙️ <b>Bot Settings</b>

<b>Current Configuration:</b>

🎯 <b>Risk Management:</b>
• Risk per trade: {user_data.get('risk_per_trade', 1.0)}%
• Max positions: {user_data.get('max_positions', 5)}
• Stop loss: {user_data.get('default_stop_loss', 2.0)}%
• Take profit: {user_data.get('default_take_profit', 4.0)}%

📱 <b>Notifications:</b>
• Signal alerts: {'✅' if user_data.get('signal_alerts', True) else '❌'}
• Trade alerts: {'✅' if user_data.get('trade_alerts', True) else '❌'}
• Error alerts: {'✅' if user_data.get('error_alerts', True) else '❌'}

📊 <b>Signal Settings:</b>
• Min signal strength: {user_data.get('min_signal_strength', 'Moderate')}
• Technical weight: {user_data.get('technical_weight', 70)}%
• Sentiment weight: {user_data.get('sentiment_weight', 30)}%

🤖 <b>Auto Trading:</b>
• Status: {'✅ Enabled' if user_data.get('auto_trading', False) else '❌ Disabled'}
• Strategy: {user_data.get('trading_strategy', 'Conservative')}

Choose a setting to modify:
        """
    
    def get_account_message(self, accounts: List[Dict]) -> str:
        """Get account overview message."""
        if not accounts:
            return """
💼 <b>Broker Accounts</b>

❌ <b>No accounts configured</b>

To start trading, you need to add at least one broker account.

<b>Supported Brokers:</b>
🟢 <b>Deriv</b> - Binary options, Forex, Indices
🟡 <b>Binance</b> - Cryptocurrency trading
🔵 <b>MetaTrader 5</b> - Forex and CFDs
🟣 <b>Interactive Brokers</b> - Stocks and options

<b>Security Note:</b>
All credentials are encrypted and stored securely.

Choose a broker to add your account:
            """
        
        account_list = ""
        for account in accounts:
            status = "✅ Active" if account.get('is_active') else "❌ Inactive"
            balance = account.get('balance', 'N/A')
            account_list += f"""
🔹 <b>{account['broker_name'].title()}</b>
   Status: {status}
   Balance: {balance}
   Last update: {account.get('last_update', 'Never')}
            """
        
        return f"""
💼 <b>Broker Accounts</b>

<b>Your Accounts:</b>
{account_list}

<b>Account Management:</b>
• Add new accounts
• Update existing accounts
• Check account status
• View balances

Choose an action:
        """
    
    def get_trading_message(self) -> str:
        """Get trading overview message."""
        return """
💹 <b>Trading Center</b>

<b>Available Actions:</b>

📊 <b>View Signals</b>
See current trading opportunities with technical and sentiment analysis

🎯 <b>Manual Trade</b>
Execute trades manually with custom parameters

🤖 <b>Auto Trading</b>
Enable/disable automated trading based on signals

📈 <b>Open Positions</b>
Monitor your current trades and P&L

📋 <b>Pending Orders</b>
View and manage pending orders

💰 <b>Account Balance</b>
Check your account balances across all brokers

<b>⚠️ Risk Warning:</b>
Trading involves significant risk. Never trade more than you can afford to lose.

Choose an action:
        """
    
    def get_account_setup_message(self, broker_type: str) -> str:
        """Get account setup instructions for specific broker."""
        instructions = {
            'deriv': """
🟢 <b>Deriv Account Setup</b>

To connect your Deriv account, I need your API token.

<b>How to get your Deriv API token:</b>
1. Go to app.deriv.com
2. Login to your account
3. Go to Settings → API Token
4. Create a new token with trading permissions
5. Copy the token and send it here

<b>Required permissions:</b>
• Read
• Trade
• Trading information
• Payments

<b>Security:</b>
Your API token will be encrypted and stored securely.

Please send your Deriv API token:
            """,
            'binance': """
🟡 <b>Binance Account Setup</b>

To connect your Binance account, I need your API credentials.

<b>How to get Binance API credentials:</b>
1. Go to binance.com
2. Login to your account
3. Go to API Management
4. Create a new API key
5. Enable "Enable Trading" permission
6. Send your API Key and Secret Key in this format:
   API_KEY:SECRET_KEY

<b>Security:</b>
Your credentials will be encrypted and stored securely.

Please send your Binance API credentials:
            """,
            'mt5': """
🔵 <b>MetaTrader 5 Account Setup</b>

To connect your MT5 account, I need your login credentials.

<b>Required information:</b>
• Login number
• Password
• Server name

<b>Format:</b>
LOGIN:PASSWORD:SERVER

<b>Example:</b>
12345678:mypassword:MetaQuotes-Demo

<b>Security:</b>
Your credentials will be encrypted and stored securely.

Please send your MT5 credentials:
            """,
            'ib': """
🟣 <b>Interactive Brokers Setup</b>

To connect your IB account, you need TWS or IB Gateway running.

<b>Setup steps:</b>
1. Install TWS or IB Gateway
2. Enable API connections in settings
3. Set socket port (usually 7497 for TWS, 4001 for Gateway)
4. Send your connection details in this format:
   HOST:PORT:CLIENT_ID

<b>Example:</b>
127.0.0.1:7497:1

<b>Note:</b>
Make sure TWS/Gateway is running when trading.

Please send your IB connection details:
            """
        }
        
        return instructions.get(broker_type, "Unknown broker type.")
    
    def get_signal_message(self, signal_data: Dict) -> str:
        """Format a trading signal message."""
        signal_type = signal_data.get('signal_type', 'UNKNOWN')
        symbol = signal_data.get('symbol', 'UNKNOWN')
        strength = signal_data.get('strength', 'UNKNOWN')
        confidence = signal_data.get('confidence', 0) * 100
        
        emoji = "📈" if signal_type == "BUY" else "📉" if signal_type == "SELL" else "📊"
        
        return f"""
{emoji} <b>{signal_type} Signal - {symbol}</b>

<b>Signal Details:</b>
• Strength: {strength}
• Confidence: {confidence:.1f}%
• Entry: {signal_data.get('entry_price', 'N/A')}
• Stop Loss: {signal_data.get('stop_loss', 'N/A')}
• Take Profit: {signal_data.get('take_profit', 'N/A')}
• Risk/Reward: 1:{signal_data.get('risk_reward_ratio', 'N/A')}

<b>Analysis:</b>
{self._format_signal_reasoning(signal_data.get('reasoning', []))}

<b>Timeframe:</b> {signal_data.get('timeframe', 'N/A')}
<b>Generated:</b> {signal_data.get('timestamp', datetime.now()).strftime('%H:%M:%S')}
        """
    
    def _format_signal_reasoning(self, reasoning: List[str]) -> str:
        """Format signal reasoning list."""
        if not reasoning:
            return "No analysis available"
        
        return "\n".join([f"• {reason}" for reason in reasoning[:5]])  # Limit to 5 reasons
    
    def get_position_message(self, position_data: Dict) -> str:
        """Format a position status message."""
        return f"""
📊 <b>Position: {position_data.get('symbol', 'UNKNOWN')}</b>

<b>Position Details:</b>
• Type: {position_data.get('side', 'UNKNOWN')}
• Size: {position_data.get('size', 'N/A')}
• Entry Price: {position_data.get('entry_price', 'N/A')}
• Current Price: {position_data.get('current_price', 'N/A')}
• P&L: {position_data.get('pnl', 'N/A')}
• P&L %: {position_data.get('pnl_percentage', 'N/A')}%

<b>Risk Management:</b>
• Stop Loss: {position_data.get('stop_loss', 'N/A')}
• Take Profit: {position_data.get('take_profit', 'N/A')}

<b>Timing:</b>
• Opened: {position_data.get('open_time', 'N/A')}
• Duration: {position_data.get('duration', 'N/A')}

<b>Broker:</b> {position_data.get('broker', 'N/A')}
        """
    
    def get_trade_confirmation_message(self, trade_data: Dict) -> str:
        """Get trade confirmation message."""
        return f"""
✅ <b>Trade Executed Successfully</b>

<b>Trade Details:</b>
• Symbol: {trade_data.get('symbol', 'N/A')}
• Type: {trade_data.get('side', 'N/A')}
• Size: {trade_data.get('size', 'N/A')}
• Entry Price: {trade_data.get('entry_price', 'N/A')}
• Stop Loss: {trade_data.get('stop_loss', 'N/A')}
• Take Profit: {trade_data.get('take_profit', 'N/A')}

<b>Order ID:</b> {trade_data.get('order_id', 'N/A')}
<b>Broker:</b> {trade_data.get('broker', 'N/A')}
<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Good luck with your trade! 🍀
        """
    
    def get_error_message(self, error_type: str, details: str = "") -> str:
        """Get formatted error message."""
        error_messages = {
            'broker_connection': "🔴 Broker connection failed",
            'insufficient_funds': "💰 Insufficient funds for this trade",
            'invalid_symbol': "❌ Invalid trading symbol",
            'market_closed': "🕐 Market is currently closed",
            'api_error': "⚠️ API error occurred",
            'unknown': "❌ An unknown error occurred"
        }
        
        base_message = error_messages.get(error_type, error_messages['unknown'])
        
        if details:
            return f"{base_message}\n\n<b>Details:</b> {details}"
        
        return base_message
    
    def get_daily_summary_message(self, summary_data: Dict) -> str:
        """Get daily trading summary message."""
        return f"""
📊 <b>Daily Trading Summary</b>
<i>{datetime.now().strftime('%Y-%m-%d')}</i>

<b>Trading Activity:</b>
• Total Trades: {summary_data.get('total_trades', 0)}
• Winning Trades: {summary_data.get('winning_trades', 0)}
• Losing Trades: {summary_data.get('losing_trades', 0)}
• Win Rate: {summary_data.get('win_rate', 0):.1f}%

<b>Performance:</b>
• Total P&L: {summary_data.get('total_pnl', 0)}
• Best Trade: {summary_data.get('best_trade', 0)}
• Worst Trade: {summary_data.get('worst_trade', 0)}

<b>Signals:</b>
• Signals Generated: {summary_data.get('signals_generated', 0)}
• Signals Executed: {summary_data.get('signals_executed', 0)}
• Signal Accuracy: {summary_data.get('signal_accuracy', 0):.1f}%

<b>Risk Management:</b>
• Max Drawdown: {summary_data.get('max_drawdown', 0):.1f}%
• Risk Exposure: {summary_data.get('risk_exposure', 0):.1f}%

Keep up the good work! 📈
        """
    
    def get_maintenance_message(self) -> str:
        """Get maintenance mode message."""
        return """
🔧 <b>Maintenance Mode</b>

The trading bot is currently undergoing maintenance.

<b>What's happening:</b>
• System updates
• Performance improvements
• Security enhancements

<b>During maintenance:</b>
• New trades are paused
• Existing positions remain active
• Monitoring continues

We'll notify you when the bot is back online.

Thank you for your patience! 🙏
        """
    
    def get_emergency_stop_message(self) -> str:
        """Get emergency stop message."""
        return """
🚨 <b>EMERGENCY STOP ACTIVATED</b>

All trading activities have been immediately halted.

<b>Actions taken:</b>
• All pending orders cancelled
• Auto-trading disabled
• New signals paused
• Risk monitoring active

<b>Your positions:</b>
Existing positions remain open but are being monitored.

<b>Next steps:</b>
• Review your account
• Check for any issues
• Contact support if needed

Trading can be resumed manually when you're ready.
        """

