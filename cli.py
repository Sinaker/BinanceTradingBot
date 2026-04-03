"""Simple CLI for trading bot."""
import logging
import typer
from binance.exceptions import BinanceAPIException, BinanceRequestException
from bot.client import get_client
from bot.logging_config import setup_logging
from bot.orders import place_market_order, place_limit_order
from bot.validators import validate_symbol, validate_side, validate_quantity, validate_price

app = typer.Typer(help="Binance Futures Testnet Trading Bot")
logger = logging.getLogger(__name__)


@app.callback()
def main(log_level: str = typer.Option("INFO", help="Logging level")):
    """Initialize logging."""
    setup_logging(log_level=log_level)


@app.command()
def market(
    symbol: str = typer.Option(..., help="Trading symbol, e.g., BTCUSDT"),
    side: str = typer.Option(..., help="BUY or SELL"),
    quantity: float = typer.Option(..., help="Order quantity"),
):
    """Place a market order."""
    try:
        symbol = validate_symbol(symbol)
        side = validate_side(side)
        quantity = validate_quantity(quantity)

        client = get_client()
        response = place_market_order(client, symbol, side, quantity)
        typer.echo(f"Order placed: {response['orderId']}")
    except (ValueError, BinanceAPIException, BinanceRequestException) as e:
        logger.error("Error: %s", e)
        typer.echo(f"Error: {e}")
        raise typer.Exit(code=1)


@app.command()
def limit(
    symbol: str = typer.Option(..., help="Trading symbol, e.g., BTCUSDT"),
    side: str = typer.Option(..., help="BUY or SELL"),
    quantity: float = typer.Option(..., help="Order quantity"),
    price: float = typer.Option(..., help="Limit price"),
):
    """Place a limit order."""
    try:
        symbol = validate_symbol(symbol)
        side = validate_side(side)
        quantity = validate_quantity(quantity)
        price = validate_price(price)

        client = get_client()
        response = place_limit_order(client, symbol, side, quantity, price)
        typer.echo(f"Order placed: {response['orderId']}")
    except (ValueError, BinanceAPIException, BinanceRequestException) as e:
        logger.error("Error: %s", e)
        typer.echo(f"Error: {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
