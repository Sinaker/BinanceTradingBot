"""Input validation for trading parameters."""
import re
from typing import Optional

SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{6,12}$")


def validate_symbol(symbol: str) -> str:
    """Validate and normalize symbol format."""
    symbol = symbol.upper()
    if not SYMBOL_PATTERN.match(symbol):
        raise ValueError("Invalid symbol format. Use uppercase like BTCUSDT.")
    return symbol


def validate_side(side: str) -> str:
    """Validate order side (BUY/SELL)."""
    side = side.upper()
    if side not in {"BUY", "SELL"}:
        raise ValueError("Side must be BUY or SELL.")
    return side


def validate_quantity(quantity: float) -> float:
    """Validate order quantity."""
    if quantity <= 0:
        raise ValueError("Quantity must be greater than 0.")
    return quantity


def validate_price(price: Optional[float], field_name: str = "price") -> float:
    """Validate price value."""
    if price is None:
        raise ValueError(f"{field_name} is required for this order type.")
    if price <= 0:
        raise ValueError(f"{field_name} must be greater than 0.")
    return price
