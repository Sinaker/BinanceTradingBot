"""Basic order placement functionality."""
import logging
from typing import Any, Dict

from binance.client import Client
from binance.enums import ORDER_TYPE_LIMIT, ORDER_TYPE_MARKET
from binance.exceptions import BinanceAPIException, BinanceRequestException

logger = logging.getLogger(__name__)


def place_market_order(
    client: Client,
    symbol: str,
    side: str,
    quantity: float,
) -> Dict[str, Any]:
    """Place a market order."""
    payload = {
        "symbol": symbol,
        "side": side,
        "type": ORDER_TYPE_MARKET,
        "quantity": quantity,
    }
    
    try:
        response = client.futures_create_order(**payload)
        logger.info("Market order placed: %s", response)
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
) -> Dict[str, Any]:
    """Place a limit order."""
    payload = {
        "symbol": symbol,
        "side": side,
        "type": ORDER_TYPE_LIMIT,
        "quantity": quantity,
        "price": price,
        "timeInForce": "GTC",
    }
    
    try:
        response = client.futures_create_order(**payload)
        logger.info("Limit order placed: %s", response)
        return response
    except (BinanceAPIException, BinanceRequestException) as e:
        logger.error("Binance error: %s", e)
        raise
