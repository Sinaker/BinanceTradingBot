# Binance Futures Testnet Trading Bot

CLI-based trading bot for Binance USDT-M Futures Testnet. Supports Market, Limit, and Stop-Limit orders with robust logging and validation.

## Prerequisites
- Python 3.8+
- Binance Futures Testnet account + API key/secret
  - https://testnet.binancefuture.com

## Installation
```bash
git clone <your-repo>
cd BinanceTradingBot
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration
Create a `.env` file from the template:
```bash
cp .env.example .env
```
Then edit `.env` and set:
```
BINANCE_API_KEY=your_testnet_api_key
BINANCE_API_SECRET=your_testnet_api_secret
```

## Usage
### Market Order
```bash
python cli.py market --symbol BTCUSDT --side BUY --quantity 0.001
```

### Limit Order
```bash
python cli.py limit --symbol BTCUSDT --side SELL --quantity 0.001 --price 50000
```

### Stop-Limit Order
```bash
python cli.py stop-limit --symbol BTCUSDT --side BUY --quantity 0.001 --price 45000 --stop-price 45500
```

### Logging
- Console output is user-friendly
- Detailed logs written to `logs/bot.log` with rotation

Example output:
```json
{
  "orderId": 123456789,
  "status": "NEW",
  "executedQty": "0",
  "avgPrice": "0",
  "symbol": "BTCUSDT",
  "side": "BUY",
  "type": "MARKET"
}
```

## Troubleshooting
- **Missing credentials**: Ensure `.env` exists and has valid keys.
- **Invalid symbol**: Use uppercase futures symbols like `BTCUSDT`.
- **API errors / rate limits**: Wait and retry; check logs for full API payloads.
- **Network errors**: Verify internet connection and testnet status.

## Assumptions & Limitations
- Designed for Binance USDT-M Futures Testnet only.
- No database or state management.
- Assumes user handles risk management and order sizing.

## Project Structure
```
BinanceTradingBot/
├── bot/
│   ├── __init__.py
│   ├── client.py
│   ├── orders.py
│   ├── validators.py
│   └── logging_config.py
├── cli.py
├── requirements.txt
├── README.md
├── .env.example
└── logs/
```
