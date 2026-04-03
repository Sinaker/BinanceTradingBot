"""Binance Futures Trading Bot CLI with rich formatting and interactive features."""
import json
import logging
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm
from binance.exceptions import BinanceAPIException, BinanceRequestException
from bot.client import get_client
from bot.logging_config import setup_logging
from bot.orders import place_market_order, place_limit_order, place_stop_limit_order
from bot.validators import validate_symbol, validate_side, validate_quantity, validate_price, RiskValidator
from bot.alerts import AlertManager

app = typer.Typer(help="Binance Futures Testnet Trading Bot")
logger = logging.getLogger(__name__)
console = Console()


def _print_response(response: dict) -> None:
    """Print order response with rich formatting."""
    table = Table(title="Order Response", show_header=True, header_style="bold magenta")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    
    fields = [
        ("Order ID", response.get("orderId")),
        ("Status", response.get("status")),
        ("Symbol", response.get("symbol")),
        ("Side", response.get("side")),
        ("Type", response.get("type")),
        ("Executed Qty", response.get("executedQty")),
        ("Average Price", response.get("avgPrice")),
    ]
    
    for field, value in fields:
        if value is not None:
            table.add_row(field, str(value))
    
    console.print(table)


def _preview_order(symbol: str, side: str, quantity: float, price: float = None, stop_price: float = None) -> bool:
    """Show order preview and ask for confirmation.
    
    Returns:
        True if user confirms, False otherwise
    """
    order_details = [
        f"[cyan]Symbol:[/cyan] {symbol}",
        f"[cyan]Side:[/cyan] {side}",
        f"[cyan]Quantity:[/cyan] {quantity}",
    ]
    
    if price:
        order_details.append(f"[cyan]Price:[/cyan] ${price:,.2f}")
    if stop_price:
        order_details.append(f"[cyan]Stop Price:[/cyan] ${stop_price:,.2f}")
    
    preview_text = "\n".join(order_details)
    console.print(Panel(preview_text, title="Order Preview", border_style="yellow"))
    
    return Confirm.ask("Execute this order?")


@app.callback()
def main(
    log_level: str = typer.Option("INFO", help="Logging level"),
    structured: bool = typer.Option(False, "--structured", help="Use structured JSON logging")
):
    """Initialize logging configuration."""
    setup_logging(log_level=log_level, structured=structured)


@app.command()
def market(
    symbol: str = typer.Option(..., help="Trading symbol, e.g., BTCUSDT"),
    side: str = typer.Option(..., help="BUY or SELL"),
    quantity: float = typer.Option(..., help="Order quantity"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate order without execution"),
    skip_confirmation: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    enable_retry: bool = typer.Option(False, "--retry", help="Enable retry with exponential backoff"),
    risk_check: bool = typer.Option(True, "--risk-check/--no-risk-check", help="Perform risk validation"),
):
    """Place a market order."""
    try:
        symbol = validate_symbol(symbol)
        side = validate_side(side)
        quantity = validate_quantity(quantity)

        client = get_client()
        
        # Risk validation
        if risk_check:
            validator = RiskValidator(client)
            
            # Check order size vs volume
            safe, msg = validator.check_order_size_vs_volume(symbol, quantity)
            console.print(f"[{'green' if safe else 'yellow'}]📊 Volume Check:[/] {msg}")
            
            if not safe and not dry_run:
                if not Confirm.ask("[yellow]⚠️  Large order detected. Continue?[/]"):
                    console.print("[red]Order cancelled by user[/]")
                    raise typer.Exit(code=0)
        
        # Preview and confirm
        if not skip_confirmation:
            if not _preview_order(symbol, side, quantity):
                console.print("[red]Order cancelled by user[/]")
                raise typer.Exit(code=0)
        
        if dry_run:
            console.print("[blue]🔵 DRY-RUN MODE - Order will be simulated[/]")
        
        response = place_market_order(client, symbol, side, quantity, dry_run=dry_run, enable_retry=enable_retry)
        _print_response(response)
        
        if response.get("status") == "FILLED":
            console.print("[green]✅ Order filled successfully![/]")
        elif response.get("status") == "SIMULATED":
            console.print("[blue]✅ Order simulated successfully![/]")
            
    except (ValueError, BinanceAPIException, BinanceRequestException) as e:
        logger.error("Error: %s", e)
        console.print(f"[red]❌ Error: {e}[/]")
        raise typer.Exit(code=1)


@app.command()
def limit(
    symbol: str = typer.Option(..., help="Trading symbol, e.g., BTCUSDT"),
    side: str = typer.Option(..., help="BUY or SELL"),
    quantity: float = typer.Option(..., help="Order quantity"),
    price: float = typer.Option(..., help="Limit price"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate order without execution"),
    skip_confirmation: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    enable_retry: bool = typer.Option(False, "--retry", help="Enable retry with exponential backoff"),
    risk_check: bool = typer.Option(True, "--risk-check/--no-risk-check", help="Perform risk validation"),
):
    """Place a limit order."""
    try:
        symbol = validate_symbol(symbol)
        side = validate_side(side)
        quantity = validate_quantity(quantity)
        price = validate_price(price)

        client = get_client()
        
        # Risk validation
        if risk_check:
            validator = RiskValidator(client)
            
            # Check price sanity (within 5% of market)
            valid, msg = validator.check_price_sanity(symbol, price)
            console.print(f"[{'green' if valid else 'yellow'}]💰 Price Check:[/] {msg}")
            
            if not valid and not dry_run:
                if not Confirm.ask("[yellow]⚠️  Price deviation detected. Continue?[/]"):
                    console.print("[red]Order cancelled by user[/]")
                    raise typer.Exit(code=0)
            
            # Check order size
            safe, msg = validator.check_order_size_vs_volume(symbol, quantity)
            console.print(f"[{'green' if safe else 'yellow'}]📊 Volume Check:[/] {msg}")
        
        # Preview and confirm
        if not skip_confirmation:
            if not _preview_order(symbol, side, quantity, price=price):
                console.print("[red]Order cancelled by user[/]")
                raise typer.Exit(code=0)
        
        if dry_run:
            console.print("[blue]🔵 DRY-RUN MODE - Order will be simulated[/]")
        
        response = place_limit_order(client, symbol, side, quantity, price, dry_run=dry_run, enable_retry=enable_retry)
        _print_response(response)
        
        if response.get("status") == "FILLED":
            console.print("[green]✅ Order filled successfully![/]")
        elif response.get("status") == "NEW":
            console.print("[yellow]🕒 Order placed, waiting for fill...[/]")
        elif response.get("status") == "SIMULATED":
            console.print("[blue]✅ Order simulated successfully![/]")
            
    except (ValueError, BinanceAPIException, BinanceRequestException) as e:
        logger.error("Error: %s", e)
        console.print(f"[red]❌ Error: {e}[/]")
        raise typer.Exit(code=1)


@app.command(name="stop-limit")
def stop_limit(
    symbol: str = typer.Option(..., help="Trading symbol, e.g., BTCUSDT"),
    side: str = typer.Option(..., help="BUY or SELL"),
    quantity: float = typer.Option(..., help="Order quantity"),
    price: float = typer.Option(..., help="Limit price"),
    stop_price: float = typer.Option(..., "--stop-price", help="Stop price"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate order without execution"),
    skip_confirmation: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    enable_retry: bool = typer.Option(False, "--retry", help="Enable retry with exponential backoff"),
    risk_check: bool = typer.Option(True, "--risk-check/--no-risk-check", help="Perform risk validation"),
):
    """Place a stop-limit order."""
    try:
        symbol = validate_symbol(symbol)
        side = validate_side(side)
        quantity = validate_quantity(quantity)
        price = validate_price(price)
        stop_price = validate_price(stop_price, field_name="stop_price")

        client = get_client()
        
        # Risk validation
        if risk_check:
            validator = RiskValidator(client)
            
            # Check both prices
            valid_limit, msg_limit = validator.check_price_sanity(symbol, price)
            console.print(f"[{'green' if valid_limit else 'yellow'}]💰 Limit Price:[/] {msg_limit}")
            
            valid_stop, msg_stop = validator.check_price_sanity(symbol, stop_price)
            console.print(f"[{'green' if valid_stop else 'yellow'}]🛑 Stop Price:[/] {msg_stop}")
            
            # Check order size
            safe, msg = validator.check_order_size_vs_volume(symbol, quantity)
            console.print(f"[{'green' if safe else 'yellow'}]📊 Volume Check:[/] {msg}")
        
        # Preview and confirm
        if not skip_confirmation:
            if not _preview_order(symbol, side, quantity, price=price, stop_price=stop_price):
                console.print("[red]Order cancelled by user[/]")
                raise typer.Exit(code=0)
        
        if dry_run:
            console.print("[blue]🔵 DRY-RUN MODE - Order will be simulated[/]")
        
        response = place_stop_limit_order(
            client, symbol, side, quantity, price, stop_price, dry_run=dry_run, enable_retry=enable_retry
        )
        _print_response(response)
        
        if response.get("status") == "NEW":
            console.print("[yellow]🕒 Stop-limit order placed, waiting for trigger...[/]")
        elif response.get("status") == "SIMULATED":
            console.print("[blue]✅ Order simulated successfully![/]")
            
    except (ValueError, BinanceAPIException, BinanceRequestException) as e:
        logger.error("Error: %s", e)
        console.print(f"[red]❌ Error: {e}[/]")
        raise typer.Exit(code=1)


@app.command()
def status():
    """Show account balance and open positions."""
    try:
        client = get_client()
        
        # Get account balance
        balance = client.futures_account_balance()
        
        # Create balance table
        balance_table = Table(title="Account Balance", show_header=True, header_style="bold cyan")
        balance_table.add_column("Asset", style="yellow")
        balance_table.add_column("Balance", justify="right", style="green")
        balance_table.add_column("Available", justify="right", style="cyan")
        
        for asset in balance:
            bal = float(asset["balance"])
            if bal > 0:  # Only show non-zero balances
                balance_table.add_row(
                    asset["asset"],
                    f"{bal:,.8f}",
                    f"{float(asset.get('availableBalance', bal)):,.8f}"
                )
        
        console.print(balance_table)
        
        # Get open positions
        positions = client.futures_position_information()
        
        # Filter to positions with non-zero size
        active_positions = [p for p in positions if float(p.get("positionAmt", 0)) != 0]
        
        if active_positions:
            pos_table = Table(title="Open Positions", show_header=True, header_style="bold magenta")
            pos_table.add_column("Symbol", style="cyan")
            pos_table.add_column("Size", justify="right")
            pos_table.add_column("Entry Price", justify="right")
            pos_table.add_column("Mark Price", justify="right")
            pos_table.add_column("Unrealized PnL", justify="right")
            
            for pos in active_positions:
                size = float(pos["positionAmt"])
                entry = float(pos["entryPrice"])
                mark = float(pos["markPrice"])
                pnl = float(pos["unRealizedProfit"])
                
                pnl_color = "green" if pnl >= 0 else "red"
                
                pos_table.add_row(
                    pos["symbol"],
                    f"{size:,.8f}",
                    f"${entry:,.2f}",
                    f"${mark:,.2f}",
                    f"[{pnl_color}]${pnl:,.2f}[/]"
                )
            
            console.print(pos_table)
        else:
            console.print("[yellow]No open positions[/]")
        
    except (BinanceAPIException, BinanceRequestException) as e:
        logger.error("Error: %s", e)
        console.print(f"[red]❌ Error: {e}[/]")
        raise typer.Exit(code=1)


@app.command()
def watch(
    symbol: str = typer.Option(..., help="Trading symbol, e.g., BTCUSDT"),
    target_price: float = typer.Option(..., "--target-price", help="Target price to watch for"),
    condition: str = typer.Option(..., "--condition", help="Condition: 'above' or 'below'"),
    interval: int = typer.Option(60, "--interval", help="Check interval in seconds"),
    duration: int = typer.Option(None, "--duration", help="Total duration in seconds (None = forever)"),
):
    """Monitor price and alert when target is reached."""
    try:
        symbol = validate_symbol(symbol)
        
        if condition.lower() not in ["above", "below"]:
            console.print("[red]❌ Condition must be 'above' or 'below'[/]")
            raise typer.Exit(code=1)
        
        client = get_client()
        alert_manager = AlertManager(client)
        
        # Add alert
        alert = alert_manager.add_alert(symbol, target_price, condition.lower())
        
        console.print(Panel(
            f"[cyan]Symbol:[/] {symbol}\n"
            f"[cyan]Target Price:[/] ${target_price:,.2f}\n"
            f"[cyan]Condition:[/] {condition.upper()}\n"
            f"[cyan]Check Interval:[/] {interval}s\n"
            f"[cyan]Alert ID:[/] {alert.alert_id}",
            title="🔔 Price Alert Created",
            border_style="green"
        ))
        
        console.print("[yellow]Starting price monitoring... Press Ctrl+C to stop[/]")
        
        # Start monitoring
        alert_manager.watch(interval=interval, duration=duration)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Monitoring stopped by user[/]")
    except (ValueError, BinanceAPIException, BinanceRequestException) as e:
        logger.error("Error: %s", e)
        console.print(f"[red]❌ Error: {e}[/]")
        raise typer.Exit(code=1)


@app.command(name="list-alerts")
def list_alerts():
    """List all active price alerts."""
    try:
        client = get_client()
        alert_manager = AlertManager(client)
        
        alerts = alert_manager.list_alerts()
        
        if not alerts:
            console.print("[yellow]No active alerts[/]")
            return
        
        table = Table(title="Active Price Alerts", show_header=True, header_style="bold cyan")
        table.add_column("Alert ID", style="dim")
        table.add_column("Symbol", style="cyan")
        table.add_column("Target Price", justify="right")
        table.add_column("Condition", style="yellow")
        table.add_column("Created", style="dim")
        
        for alert in alerts:
            table.add_row(
                alert.alert_id[:12] + "...",
                alert.symbol,
                f"${alert.target_price:,.2f}",
                alert.alert_type.upper(),
                alert.created_at[:19]
            )
        
        console.print(table)
        
    except (BinanceAPIException, BinanceRequestException) as e:
        logger.error("Error: %s", e)
        console.print(f"[red]❌ Error: {e}[/]")
        raise typer.Exit(code=1)


@app.command(name="remove-alert")
def remove_alert(
    alert_id: str = typer.Argument(..., help="Alert ID to remove")
):
    """Remove a price alert by ID."""
    try:
        client = get_client()
        alert_manager = AlertManager(client)
        
        alert_manager.remove_alert(alert_id)
        console.print(f"[green]✅ Alert {alert_id} removed successfully![/]")
        
    except ValueError as e:
        console.print(f"[red]❌ {e}[/]")
        raise typer.Exit(code=1)
    except (BinanceAPIException, BinanceRequestException) as e:
        logger.error("Error: %s", e)
        console.print(f"[red]❌ Error: {e}[/]")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
