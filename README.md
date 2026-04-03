# Binance Trading Bot

## Introduction
This project is my attempt to build a simplified trading bot for the Binance Futures Testnet. As someone new to trading APIs and automated systems, this task helped me learn about concepts like placing market and limit orders, integrating Python with external APIs, and designing a user-friendly CLI tool.

## Features

### Supported Order Types
- **Market Orders**: Immediate execution at the current market price.
- **Limit Orders**: Wait for a specific target price before executing.
- **Stop-Limit Orders**: An advanced order type often used for risk management.

### Additional Features
- **Dry-run Mode**: Allows you to simulate orders without placing real trades. Useful for testing.
- **Price Alerts**: Monitors the price and alerts you when configured targets are hit.
- **Trade Journal**: Keeps a record of all trades, including timestamps and P&L tracking.
- **Risk Management**: Validates orders for price sanity and position size limits.

## Architecture
```plaintext
BinanceTradingBot/
├── bot/
│   ├── client.py          # Configures and handles Binance API calls
│   ├── orders.py          # Handles order placement and validation logic
│   ├── validators.py      # Contains comprehensive risk validation rules
│   ├── alerts.py          # Implements price alert functionality
│   ├── logging_config.py  # Centralized logging setup
├── tests                  # Unit tests for core logic and features
├── cli.py                 # CLI entry point for user interaction
└── README.md
```

The focus was on modularizing the entire bot to ensure each component had a clearly defined responsibility. This meant decoupling API logic, order handling, alerting, and user interaction.

## Example Flowchart

Below is an example flowchart illustrating how the bot processes a `market` order:

```plaintext
User
 │
 │ CLI Command: python cli.py market --symbol BTCUSDT --side BUY --quantity 0.01
 │
 ▼
 Validate Input (validators.py)
 │
 │ Valid Input → Proceed
 │
 ▼
 API Request (client.py)  ──> Binance Testnet
 │
 │ API Response
 │
 ▼
 Log Trade (logging_config.py)
 │
 ▼
 Display Result (cli.py)
```

## Lessons Learned
Writing this bot taught me a lot about:
1. **API Integration**: Dealing with authentication, timeouts, and API errors.
2. **CLI Design**: Ensuring a user-friendly experience with clear error messages.
3. **Unit Testing**: I practiced writing mock-based tests to simulate API responses.
4. **The Importance of Logs**: Structured logs make debugging and tracking trades much easier.

## Setup Instructions

### Prerequisites
- Python 3.8 or later.
- pip for dependency management.
- Binance Futures Testnet account with API keys.

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/Sinaker/BinanceTradingBot.git
   cd BinanceTradingBot
   ```
2. Create a virtual environment and activate it:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Add API credentials to `.env` file:
   ```plaintext
   BINANCE_API_KEY=your_api_key
   BINANCE_API_SECRET=your_api_secret
   ```
5. Run an example command:
   ```bash
   python cli.py market --symbol BTCUSDT --side BUY --quantity 0.01
   ```

## Future Improvements
- Add support for OCO (one-cancels-the-other) orders.
- Create a lightweight web interface for monitoring trades and alerts.
- Enhance the trade journal with visualizations.

This bot has been a great learning experience for me, and I'm excited to explore even more about automated trading systems!