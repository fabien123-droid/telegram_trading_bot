"""
Custom exceptions for the Telegram Trading Bot.
"""


class TradingBotException(Exception):
    """Base exception for all trading bot errors."""
    
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ConfigurationError(TradingBotException):
    """Raised when there's a configuration error."""
    pass


class DatabaseError(TradingBotException):
    """Raised when there's a database error."""
    pass


class BrokerError(TradingBotException):
    """Base exception for broker-related errors."""
    pass


class DerivAPIError(BrokerError):
    """Raised when there's an error with the Deriv API."""
    pass


class BinanceAPIError(BrokerError):
    """Raised when there's an error with the Binance API."""
    pass


class MT5Error(BrokerError):
    """Raised when there's an error with MetaTrader 5."""
    pass


class IBError(BrokerError):
    """Raised when there's an error with Interactive Brokers."""
    pass


class TradingError(TradingBotException):
    """Raised when there's a trading-related error."""
    pass


class InsufficientFundsError(TradingError):
    """Raised when there are insufficient funds for a trade."""
    pass


class InvalidOrderError(TradingError):
    """Raised when an order is invalid."""
    pass


class RiskManagementError(TradingError):
    """Raised when a trade violates risk management rules."""
    pass


class AnalysisError(TradingBotException):
    """Raised when there's an error in technical analysis."""
    pass


class SentimentAnalysisError(AnalysisError):
    """Raised when there's an error in sentiment analysis."""
    pass


class TechnicalIndicatorError(AnalysisError):
    """Raised when there's an error calculating technical indicators."""
    pass


class TelegramError(TradingBotException):
    """Raised when there's a Telegram-related error."""
    pass


class UserNotFoundError(TradingBotException):
    """Raised when a user is not found."""
    pass


class UserNotAuthorizedError(TradingBotException):
    """Raised when a user is not authorized for an action."""
    pass


class AuthenticationError(TradingBotException):
    """Raised when there's an authentication error."""
    pass


class ValidationError(TradingBotException):
    """Raised when data validation fails."""
    pass


class ExternalAPIError(TradingBotException):
    """Raised when there's an error with external APIs."""
    pass


class RateLimitError(ExternalAPIError):
    """Raised when API rate limits are exceeded."""
    pass


class NetworkError(TradingBotException):
    """Raised when there's a network-related error."""
    pass


class SchedulerError(TradingBotException):
    """Raised when there's a scheduler-related error."""
    pass

