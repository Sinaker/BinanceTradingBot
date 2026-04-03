# Binance Futures Testnet Trading Bot

🚀 Professional CLI-based trading bot for Binance USDT-M Futures Testnet with smart risk checks, price alerts, and rich formatting.

## ✨ Features

- **Order Types**: Market, Limit, Stop-Limit with smart validation
- **Risk Management**: 
  - Automatic price sanity checks (5% deviation alerts)
  - Order size vs volume validation
  - Position size calculator based on account balance
- **Price Alerts**: Set price watches with notifications
- **Rich CLI**: Interactive prompts, colored tables, order previews
- **Performance Tracking**: API latency metrics and trade journal
- **Dry-Run Mode**: Test orders without execution
- **Smart Retry**: Exponential backoff for failed orders
- **Trade Journal**: Automatic P&L tracking in JSON format

## Prerequisites
- Python 3.8+
- Binance Futures Testnet account + API key/secret
  - https://testnet.binancefuture.com

## Installation
```bash
git clone https://github.com/yourusername/BinanceTradingBot.git
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

### 📊 Account Status
View account balance and open positions:
```bash
python cli.py status
```

### 📈 Market Order
Place a market order with risk checks:
```bash
python cli.py market --symbol BTCUSDT --side BUY --quantity 0.001
```

**Options:**
- `--dry-run` - Simulate order without execution
- `--yes` / `-y` - Skip confirmation prompt
- `--retry` - Enable retry with exponential backoff
- `--no-risk-check` - Disable risk validation

Example with dry-run:
```bash
python cli.py market --symbol BTCUSDT --side BUY --quantity 0.001 --dry-run
```

### 💰 Limit Order
Place a limit order with price validation:
```bash
python cli.py limit --symbol BTCUSDT --side SELL --quantity 0.001 --price 50000
```

The bot will automatically:
- Check if price is within 5% of current market price
- Validate order size against 24h volume
- Show interactive order preview
- Request confirmation before execution

### 🛑 Stop-Limit Order
Place a stop-limit order:
```bash
python cli.py stop-limit --symbol BTCUSDT --side BUY --quantity 0.001 --price 45000 --stop-price 45500
```

### 🔔 Price Alerts
Monitor prices and get notified when targets are hit:

**Create an alert:**
```bash
python cli.py watch --symbol BTCUSDT --target-price 50000 --condition above
```

**List active alerts:**
```bash
python cli.py list-alerts
```

**Remove an alert:**
```bash
python cli.py remove-alert <alert-id>
```

**Options:**
- `--interval 30` - Check every 30 seconds (default: 60)
- `--duration 3600` - Run for 1 hour (default: forever)

### 📝 Structured Logging
Enable JSON-structured logs for analysis:
```bash
python cli.py --structured market --symbol BTCUSDT --side BUY --quantity 0.001
```

## 📁 Project Structure
```
BinanceTradingBot/
├── bot/
│   ├── __init__.py          # Package init
│   ├── client.py            # Binance client wrapper
│   ├── orders.py            # Order placement with retry & tracking
│   ├── validators.py        # Smart validation & risk checks
│   ├── alerts.py            # Price alert system
│   ├── templates.py         # Order templates
│   └── logging_config.py    # Structured logging & trade journal
├── cli.py                   # Rich CLI with interactive prompts
├── test_bot.py              # Unit tests
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── .env.example            # Template for credentials
├── logs/
│   ├── bot.log             # Application logs
│   └── trade_journal.jsonl # Trade history with P&L
└── alerts/
    └── active_alerts.json  # Active price alerts
```

## 🧪 Testing
Run unit tests:
```bash
python -m pytest test_bot.py -v
```

Test coverage includes:
- Input validation (symbol, side, quantity, price)
- Risk validation (price sanity, order size checks)
- Price alert creation and triggering
- Serialization/deserialization

## 📊 Example Outputs

**Order Response:**
```
┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Field         ┃ Value       ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ Order ID      │ 123456789   │
│ Status        │ FILLED      │
│ Symbol        │ BTCUSDT     │
│ Side          │ BUY         │
│ Type          │ MARKET      │
│ Executed Qty  │ 0.001       │
│ Average Price │ 50000.00    │
└───────────────┴─────────────┘
✅ Order filled successfully!
```

**Account Status:**
```
                Account Balance                 
┏━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Asset ┃    Balance ┃  Available ┃
┡━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ USDT  │ 10000.0000 │  9500.0000 │
└───────┴────────────┴────────────┘

                Open Positions                  
┏━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ Symbol  ┃   Size ┃ Entry Price ┃  Mark Price ┃ Unrealized PnL ┃
┡━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━┩
│ BTCUSDT │  0.001 │   $50000.00 │   $50500.00 │        $0.50   │
└─────────┴────────┴─────────────┴─────────────┴────────────────┘
```

## 🔒 Security Best Practices

- Never commit `.env` file (use `.gitignore`)
- Use testnet for development
- Rotate API keys periodically
- Use read-only keys for monitoring
- Enable IP whitelist on Binance

## ⚠️ Troubleshooting

**Missing credentials:**
```
❌ Error: API credentials not found in .env
```
→ Ensure `.env` exists with valid `BINANCE_API_KEY` and `BINANCE_API_SECRET`

**Invalid symbol:**
```
❌ Error: Invalid symbol format. Use uppercase like BTCUSDT.
```
→ Use uppercase futures symbols (BTCUSDT, ETHUSDT, etc.)

**Price deviation warning:**
```
⚠️  Price $60000.00 deviates 20.0% from current market $50000.00 (limit: 5.0%)
⚠️  Price deviation detected. Continue?
```
→ Check if price is correct. Large deviations may indicate stale data or typos.

**Large order warning:**
```
⚠️  Order size 500.0 is 15.0% of 24h volume (3333.33) - exceeds 10.0% threshold
⚠️  Large order detected. Continue?
```
→ Large orders may move the market or have slippage.

## 📚 Advanced Usage

### Position Size Calculator
Calculate recommended position based on account balance:
```python
from bot.validators import RiskValidator
from bot.client import get_client

client = get_client()
validator = RiskValidator(client)

# Risk 2% of account
size = validator.calculate_position_size(risk_percent=0.02)
print(f"Recommended position: ${size:.2f}")
```

### Trade Journal Analysis
Analyze your trade history:
```bash
cat logs/trade_journal.jsonl | jq -r '.symbol' | sort | uniq -c
```

### Batch Price Alerts
Monitor multiple symbols:
```bash
for symbol in BTCUSDT ETHUSDT BNBUSDT; do
  python cli.py watch --symbol $symbol --target-price 50000 --condition above --interval 120 &
done
```

## 🛠️ Development

**Run tests with coverage:**
```bash
pytest test_bot.py -v --cov=bot
```

**Format code:**
```bash
black bot/ cli.py test_bot.py
```

**Type checking:**
```bash
mypy bot/ cli.py
```

## 📝 License
MIT

## 🤝 Contributing
Pull requests welcome! Please ensure:
- All tests pass
- Code is formatted with black
- New features have tests
- README is updated

## ⚠️ Disclaimer
This bot is for educational purposes only. Use at your own risk. Always test on testnet before using real funds.
