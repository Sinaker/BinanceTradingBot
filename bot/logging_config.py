"""
Enhanced logging with structured JSON, performance metrics, and trade journal.

Features:
- Structured JSON logs for easy parsing
- Performance metrics (API latency, order fill time)
- Trade journal mode with automatic P&L tracking
- Request ID correlation for distributed tracing
"""
import json
import logging
import time
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Trade journal file for P&L tracking
TRADE_JOURNAL_PATH = LOG_DIR / "trade_journal.jsonl"


class StructuredFormatter(logging.Formatter):
    """Format logs as JSON for easy parsing and analysis."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields if present
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        if hasattr(record, "order_id"):
            log_data["order_id"] = record.order_id
        if hasattr(record, "symbol"):
            log_data["symbol"] = record.symbol
        if hasattr(record, "side"):
            log_data["side"] = record.side
        if hasattr(record, "quantity"):
            log_data["quantity"] = record.quantity
        if hasattr(record, "price"):
            log_data["price"] = record.price
        
        return json.dumps(log_data)


def setup_logging(log_level: str = "INFO", structured: bool = False) -> None:
    """
    Configure console + file logging with rotation.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        structured: If True, use JSON structured logging for file output
        
    Example:
        >>> setup_logging("INFO", structured=True)
    """
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Avoid duplicate handlers if called multiple times
    if logger.handlers:
        return

    # Console handler (human-readable)
    console_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)

    # File handler (structured JSON if requested)
    if structured:
        file_formatter = StructuredFormatter()
    else:
        file_formatter = console_formatter
        
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(
        LOG_DIR / "bot.log", maxBytes=5 * 1024 * 1024, backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)


class PerformanceTracker:
    """Track API performance metrics and latency."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.request_id = str(uuid.uuid4())[:8]
    
    @contextmanager
    def track(self, operation: str, **kwargs):
        """
        Context manager to track operation duration.
        
        Example:
            >>> tracker = PerformanceTracker()
            >>> with tracker.track("place_order", symbol="BTCUSDT"):
            ...     # API call here
            ...     pass
        """
        start = time.time()
        extra = {"request_id": self.request_id, **kwargs}
        
        try:
            self.logger.info(f"Starting {operation}", extra=extra)
            yield
        finally:
            duration_ms = (time.time() - start) * 1000
            extra["duration_ms"] = round(duration_ms, 2)
            self.logger.info(f"Completed {operation} in {duration_ms:.2f}ms", extra=extra)


class TradeJournal:
    """Automatic P&L tracking and trade history."""
    
    @staticmethod
    def log_trade(order_data: Dict[str, Any]) -> None:
        """
        Log trade to journal for P&L analysis.
        
        Args:
            order_data: Order response from Binance API
            
        Example:
            >>> TradeJournal.log_trade({
            ...     "orderId": 123456,
            ...     "symbol": "BTCUSDT",
            ...     "side": "BUY",
            ...     "executedQty": "0.001",
            ...     "avgPrice": "50000",
            ...     "status": "FILLED"
            ... })
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "order_id": order_data.get("orderId"),
            "symbol": order_data.get("symbol"),
            "side": order_data.get("side"),
            "quantity": order_data.get("executedQty", order_data.get("origQty")),
            "price": order_data.get("avgPrice", order_data.get("price")),
            "status": order_data.get("status"),
            "type": order_data.get("type"),
            "commission": order_data.get("commission", "0"),
        }
        
        with open(TRADE_JOURNAL_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
    
    @staticmethod
    def get_recent_trades(limit: int = 10) -> list:
        """
        Get recent trades from journal.
        
        Args:
            limit: Maximum number of trades to return
            
        Returns:
            List of trade entries (most recent first)
        """
        if not TRADE_JOURNAL_PATH.exists():
            return []
        
        with open(TRADE_JOURNAL_PATH, "r") as f:
            lines = f.readlines()
        
        trades = [json.loads(line) for line in lines[-limit:]]
        return list(reversed(trades))
