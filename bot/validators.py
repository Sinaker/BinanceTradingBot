"""
Advanced validators with smart risk checks and price sanity validation.

Features:
- Risk checks (order size vs typical volume)
- Price sanity checks (deviation from current market)
- Position size calculator based on account balance
- Symbol existence validation via Binance API
"""
import logging
import re
from typing import Optional, Tuple

from binance.client import Client
from binance.exceptions import BinanceAPIException

logger = logging.getLogger(__name__)

SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{6,12}$")


def validate_symbol(symbol: str) -> str:
    """
    Validate symbol format.
    
    Args:
        symbol: Trading pair symbol (e.g., BTCUSDT)
        
    Returns:
        Validated uppercase symbol
        
    Raises:
        ValueError: If symbol format is invalid
        
    Example:
        >>> validate_symbol("btcusdt")
        'BTCUSDT'
    """
    symbol = symbol.upper()
    if not SYMBOL_PATTERN.match(symbol):
        raise ValueError("Invalid symbol format. Use uppercase like BTCUSDT.")
    return symbol


def validate_side(side: str) -> str:
    """
    Validate order side.
    
    Args:
        side: Order side (BUY or SELL)
        
    Returns:
        Validated uppercase side
        
    Raises:
        ValueError: If side is not BUY or SELL
    """
    side = side.upper()
    if side not in {"BUY", "SELL"}:
        raise ValueError("Side must be BUY or SELL.")
    return side


def validate_quantity(quantity: float) -> float:
    """
    Validate order quantity.
    
    Args:
        quantity: Order quantity
        
    Returns:
        Validated quantity
        
    Raises:
        ValueError: If quantity is <= 0
    """
    if quantity <= 0:
        raise ValueError("Quantity must be greater than 0.")
    return quantity


def validate_price(price: Optional[float], field_name: str = "price") -> float:
    """
    Validate price value.
    
    Args:
        price: Price value
        field_name: Name of price field (for error messages)
        
    Returns:
        Validated price
        
    Raises:
        ValueError: If price is None or <= 0
    """
    if price is None:
        raise ValueError(f"{field_name} is required for this order type.")
    if price <= 0:
        raise ValueError(f"{field_name} must be greater than 0.")
    return price


class RiskValidator:
    """Advanced risk validation for orders."""
    
    def __init__(self, client: Client):
        self.client = client
        self.logger = logging.getLogger(__name__)
    
    def check_price_sanity(
        self, 
        symbol: str, 
        price: Optional[float], 
        max_deviation: float = 0.05
    ) -> Tuple[bool, str]:
        """
        Verify price doesn't deviate too much from current market.
        
        Args:
            symbol: Trading pair symbol
            price: Order price (None for market orders)
            max_deviation: Maximum allowed deviation (default 5%)
            
        Returns:
            Tuple of (is_valid, message)
            
        Example:
            >>> validator = RiskValidator(client)
            >>> valid, msg = validator.check_price_sanity("BTCUSDT", 50000)
            >>> if not valid:
            ...     print(f"Warning: {msg}")
        """
        if price is None:
            return True, "Market order - no price check needed"
        
        try:
            ticker = self.client.futures_symbol_ticker(symbol=symbol)
            current_price = float(ticker["price"])
            
            deviation = abs(price - current_price) / current_price
            
            if deviation > max_deviation:
                return False, (
                    f"Price ${price:,.2f} deviates {deviation:.1%} from "
                    f"current market ${current_price:,.2f} (limit: {max_deviation:.1%})"
                )
            
            return True, f"Price within acceptable range (${current_price:,.2f})"
            
        except BinanceAPIException as e:
            self.logger.warning(f"Could not fetch ticker for {symbol}: {e}")
            return True, "Price check skipped (API error)"
    
    def check_order_size_vs_volume(
        self, 
        symbol: str, 
        quantity: float,
        max_percent: float = 0.10
    ) -> Tuple[bool, str]:
        """
        Warn if order size exceeds percentage of typical volume.
        
        Args:
            symbol: Trading pair symbol
            quantity: Order quantity
            max_percent: Maximum percentage of 24h volume (default 10%)
            
        Returns:
            Tuple of (is_safe, message)
            
        Example:
            >>> validator = RiskValidator(client)
            >>> safe, msg = validator.check_order_size_vs_volume("BTCUSDT", 10.0)
            >>> if not safe:
            ...     print(f"⚠️  {msg}")
        """
        try:
            ticker = self.client.futures_ticker(symbol=symbol)
            volume_24h = float(ticker["volume"])
            
            if volume_24h == 0:
                return True, "Low liquidity - proceed with caution"
            
            percent_of_volume = quantity / volume_24h
            
            if percent_of_volume > max_percent:
                return False, (
                    f"Order size {quantity} is {percent_of_volume:.1%} of "
                    f"24h volume ({volume_24h:,.2f}) - exceeds {max_percent:.1%} threshold"
                )
            
            return True, f"Order size OK ({percent_of_volume:.2%} of 24h volume)"
            
        except BinanceAPIException as e:
            self.logger.warning(f"Could not fetch volume for {symbol}: {e}")
            return True, "Volume check skipped (API error)"
    
    def calculate_position_size(
        self,
        risk_percent: float = 0.02,
        symbol: Optional[str] = None
    ) -> float:
        """
        Calculate recommended position size based on account balance.
        
        Args:
            risk_percent: Percentage of account to risk (default 2%)
            symbol: Trading pair (optional, for price context)
            
        Returns:
            Recommended position size in USDT
            
        Example:
            >>> validator = RiskValidator(client)
            >>> size_usdt = validator.calculate_position_size(risk_percent=0.01)
            >>> print(f"Recommended position: ${size_usdt:.2f}")
        """
        try:
            account = self.client.futures_account_balance()
            
            # Find USDT balance
            usdt_balance = 0.0
            for asset in account:
                if asset["asset"] == "USDT":
                    usdt_balance = float(asset["balance"])
                    break
            
            recommended_size = usdt_balance * risk_percent
            
            self.logger.info(
                f"Account balance: ${usdt_balance:,.2f} USDT | "
                f"Recommended position ({risk_percent:.1%}): ${recommended_size:,.2f}"
            )
            
            return recommended_size
            
        except BinanceAPIException as e:
            self.logger.warning(f"Could not fetch account balance: {e}")
            return 0.0
    
    def validate_symbol_exists(self, symbol: str) -> Tuple[bool, str]:
        """
        Verify symbol exists and is tradeable on Binance Futures.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Tuple of (exists, message)
        """
        try:
            info = self.client.futures_exchange_info()
            symbols = {s["symbol"] for s in info["symbols"] if s["status"] == "TRADING"}
            
            if symbol in symbols:
                return True, f"{symbol} is valid and tradeable"
            else:
                available = ", ".join(sorted(list(symbols))[:5])
                return False, f"{symbol} not found. Available symbols include: {available}..."
                
        except BinanceAPIException as e:
            self.logger.warning(f"Could not fetch exchange info: {e}")
            return True, "Symbol validation skipped (API error)"
