#!/usr/bin/env python3
"""
Telegram Trading Bot - Main Entry Point

A multi-user Telegram bot for automated trading with support for multiple brokers
including Deriv, Binance, MetaTrader 5, and Interactive Brokers.

Features:
- Multi-user support with individual broker accounts
- Technical analysis with RSI, MACD, Bollinger Bands, Stochastic
- Sentiment analysis from news and social media
- Risk management with configurable position sizing
- Real-time notifications and trade confirmations
- Automated trading with customizable strategies

Usage:
    python main.py

Environment Variables:
    See .env.example for required configuration variables.

Author: Manus AI
Version: 1.0.0
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.main import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

