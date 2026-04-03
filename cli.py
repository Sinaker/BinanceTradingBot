import json
import logging
import typer
from binance.exceptions import BinanceAPIException, BinanceRequestException
from bot.client import get_client
from bot.logging_config import setup_logging
from bot.orders import place_market_order, place_limit_order, place_stop_limit_order
from bot.validators import validate_symbol, validate_side, validate_quantity, validate_price

app = typer.Typer(help="Binance Futures Testnet Trading Bot")
logger = logging.getLogger(__name__)


def _print_response(response: dict) -> None:
    output = {
        "orderId": response.get("orderId"),
        "status": response.get("status"),
        "executedQty": response.get("executedQty"),
        "avgPrice": response.get("avgPrice"),
        "symbol": response.get("symbol"),
        "side": response.get("side"),
        "type": response.get("type"),
    }
    typer.echo(json.dumps(output, indent=2))


@app.callback()
def main(log_level: str = typer.Option("INFO", help="Logging level")):
    setup_logging(log_level=log_level)


@app.command()
def market(
    symbol: str = typer.Option(..., help="Trading symbol, e.g., BTCUSDT"),
    side: str = typer.Option(..., help="BUY or SELL"),
    quantity: float = typer.Option(..., help="Order quantity"),
):
    try:
        symbol = validate_symbol(symbol)
        side = validate_side(side)
        quantity = validate_quantity(quantity)

        client = get_client()
        response = place_market_order(client, symbol, side, quantity)
        _print_response(response)
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
    try:
        symbol = validate_symbol(symbol)
        side = validate_side(side)
        quantity = validate_quantity(quantity)
        price = validate_price(price)

        client = get_client()
        response = place_limit_order(client, symbol, side, quantity, price)
        _print_response(response)
    except (ValueError, BinanceAPIException, BinanceRequestException) as e:
        logger.error("Error: %s", e)
        typer.echo(f"Error: {e}")
        raise typer.Exit(code=1)


@app.command(name="stop-limit")
def stop_limit(
    symbol: str = typer.Option(..., help="Trading symbol, e.g., BTCUSDT"),
    side: str = typer.Option(..., help="BUY or SELL"),
    quantity: float = typer.Option(..., help="Order quantity"),
    price: float = typer.Option(..., help="Limit price"),
    stop_price: float = typer.Option(..., "--stop-price", help="Stop price"),
):
    try:
        symbol = validate_symbol(symbol)
        side = validate_side(side)
        quantity = validate_quantity(quantity)
        price = validate_price(price)
        stop_price = validate_price(stop_price, field_name="stop_price")

        client = get_client()
        response = place_stop_limit_order(client, symbol, side, quantity, price, stop_price)
        _print_response(response)
    except (ValueError, BinanceAPIException, BinanceRequestException) as e:
        logger.error("Error: %s", e)
        typer.echo(f"Error: {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
