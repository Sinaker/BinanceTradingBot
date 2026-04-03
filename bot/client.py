import logging
import os
from binance.client import Client
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

TESTNET_BASE_URL = "https://testnet.binancefuture.com"


def get_client() -> Client:
    """Create Binance Futures client configured for testnet."""
    load_dotenv()
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")

    if not api_key or not api_secret:
        raise ValueError("Missing API credentials. Set BINANCE_API_KEY and BINANCE_API_SECRET in .env")

    client = Client(api_key, api_secret)
    client.FUTURES_URL = TESTNET_BASE_URL
    logger.debug("Initialized Binance client for testnet: %s", TESTNET_BASE_URL)
    return client
