"""
Order placement with performance tracking, dry-run mode, and smart retry.

Features:
- Performance metrics (API latency tracking)
- Dry-run simulation mode
- Smart retry with exponential backoff
- Trade journal logging
"""
import logging
import time
from typing import Any, Dict

from binance.client import Client
from binance.enums import ORDER_TYPE_LIMIT, ORDER_TYPE_MARKET, ORDER_TYPE_STOP
from binance.exceptions import BinanceAPIException, BinanceRequestException

from bot.logging_config import PerformanceTracker, TradeJournal

logger = logging.getLogger(__name__)


def _log_request(order_type: str, payload: Dict[str, Any]) -> None:
    """Log order request details."""
    logger.info("Placing %s order: %s", order_type, payload)
    logger.debug("Full payload: %s", payload)


def _simulate_order(order_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulate order execution for dry-run mode.
    
    Args:
        order_type: Type of order (MARKET, LIMIT, STOP_LIMIT)
        payload: Order parameters
        
    Returns:
        Simulated order response
    """
    logger.info("🔵 DRY-RUN MODE: Simulating %s order", order_type)
    
    return {
        "orderId": 999999999,  # Fake order ID
        "symbol": payload["symbol"],
        "side": payload["side"],
        "type": order_type,
        "status": "SIMULATED",
        "origQty": str(payload["quantity"]),
        "executedQty": str(payload["quantity"]),
        "price": str(payload.get("price", "0")),
        "avgPrice": str(payload.get("price", "MARKET")),
        "timeInForce": payload.get("timeInForce", "GTC"),
        "updateTime": int(time.time() * 1000),
    }


def _retry_with_backoff(
    func,
    max_retries: int = 3,
    base_delay: float = 1.0,
    **kwargs
) -> Dict[str, Any]:
    """
    Execute function with exponential backoff retry logic.
    
    Args:
        func: Function to execute
        max_retries: Maximum retry attempts
        base_delay: Base delay in seconds (doubles each retry)
        **kwargs: Arguments to pass to func
        
    Returns:
        Function result
        
    Raises:
        Exception from last retry attempt
    """
    for attempt in range(max_retries):
        try:
            return func(**kwargs)
        except (BinanceAPIException, BinanceRequestException) as e:
            if attempt == max_retries - 1:
                logger.error(f"Final retry failed: {e}")
                raise
            
            delay = base_delay * (2 ** attempt)
            logger.warning(
                f"Attempt {attempt + 1}/{max_retries} failed: {e}. "
                f"Retrying in {delay}s..."
            )
            time.sleep(delay)


def place_market_order(
    client: Client,
    symbol: str,
    side: str,
    quantity: float,
    dry_run: bool = False,
    enable_retry: bool = False
) -> Dict[str, Any]:
    """
    Place a market order with optional dry-run and retry.
    
    Args:
        client: Binance client
        symbol: Trading pair (e.g., BTCUSDT)
        side: BUY or SELL
        quantity: Order quantity
        dry_run: If True, simulate order without executing
        enable_retry: If True, retry failed orders with exponential backoff
        
    Returns:
        Order response dictionary
        
    Example:
        >>> client = get_client()
        >>> response = place_market_order(
        ...     client, "BTCUSDT", "BUY", 0.001, dry_run=True
        ... )
        >>> print(response["status"])
        'SIMULATED'
    """
    payload = {
        "symbol": symbol,
        "side": side,
        "type": ORDER_TYPE_MARKET,
        "quantity": quantity,
    }
    _log_request("MARKET", payload)
    
    if dry_run:
        return _simulate_order("MARKET", payload)
    
    tracker = PerformanceTracker()
    
    try:
        with tracker.track("place_market_order", symbol=symbol, side=side, quantity=quantity):
            if enable_retry:
                response = _retry_with_backoff(
                    client.futures_create_order,
                    **payload
                )
            else:
                response = client.futures_create_order(**payload)
                
        logger.info("Market order response: %s", response)
        TradeJournal.log_trade(response)
        return response
        
    except (BinanceAPIException, BinanceRequestException) as e:
        logger.error("Binance error: %s", e)
        raise


def place_limit_order(
    client: Client,
    symbol: str,
    side: str,
    quantity: float,
    price: float,
    dry_run: bool = False,
    enable_retry: bool = False
) -> Dict[str, Any]:
    """
    Place a limit order with optional dry-run and retry.
    
    Args:
        client: Binance client
        symbol: Trading pair (e.g., BTCUSDT)
        side: BUY or SELL
        quantity: Order quantity
        price: Limit price
        dry_run: If True, simulate order without executing
        enable_retry: If True, retry failed orders with exponential backoff
        
    Returns:
        Order response dictionary
    """
    payload = {
        "symbol": symbol,
        "side": side,
        "type": ORDER_TYPE_LIMIT,
        "quantity": quantity,
        "price": price,
        "timeInForce": "GTC",
    }
    _log_request("LIMIT", payload)
    
    if dry_run:
        return _simulate_order("LIMIT", payload)
    
    tracker = PerformanceTracker()
    
    try:
        with tracker.track("place_limit_order", symbol=symbol, side=side, quantity=quantity, price=price):
            if enable_retry:
                response = _retry_with_backoff(
                    client.futures_create_order,
                    **payload
                )
            else:
                response = client.futures_create_order(**payload)
                
        logger.info("Limit order response: %s", response)
        TradeJournal.log_trade(response)
        return response
        
    except (BinanceAPIException, BinanceRequestException) as e:
        logger.error("Binance error: %s", e)
        raise


def place_stop_limit_order(
    client: Client,
    symbol: str,
    side: str,
    quantity: float,
    price: float,
    stop_price: float,
    dry_run: bool = False,
    enable_retry: bool = False
) -> Dict[str, Any]:
    """
    Place a stop-limit order with optional dry-run and retry.
    
    Args:
        client: Binance client
        symbol: Trading pair (e.g., BTCUSDT)
        side: BUY or SELL
        quantity: Order quantity
        price: Limit price
        stop_price: Stop trigger price
        dry_run: If True, simulate order without executing
        enable_retry: If True, retry failed orders with exponential backoff
        
    Returns:
        Order response dictionary
    """
    payload = {
        "symbol": symbol,
        "side": side,
        "type": ORDER_TYPE_STOP,
        "quantity": quantity,
        "price": price,
        "stopPrice": stop_price,
        "timeInForce": "GTC",
    }
    _log_request("STOP_LIMIT", payload)
    
    if dry_run:
        return _simulate_order("STOP_LIMIT", payload)
    
    tracker = PerformanceTracker()
    
    try:
        with tracker.track(
            "place_stop_limit_order",
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            stop_price=stop_price
        ):
            if enable_retry:
                response = _retry_with_backoff(
                    client.futures_create_order,
                    **payload
                )
            else:
                response = client.futures_create_order(**payload)
                
        logger.info("Stop-limit order response: %s", response)
        TradeJournal.log_trade(response)
        return response
        
    except (BinanceAPIException, BinanceRequestException) as e:
        logger.error("Binance error: %s", e)
        raise
