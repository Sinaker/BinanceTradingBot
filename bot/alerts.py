"""
Price alert monitoring system with configurable notifications.

Features:
- Set price alerts for symbols
- Monitor prices in background
- Trigger notifications when thresholds are hit
- Support for both above/below alerts
"""
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Literal, Optional

from binance.client import Client
from binance.exceptions import BinanceAPIException

logger = logging.getLogger(__name__)

ALERTS_DIR = Path(__file__).resolve().parent.parent / "alerts"
ALERTS_DIR.mkdir(parents=True, exist_ok=True)
ALERTS_FILE = ALERTS_DIR / "active_alerts.json"


AlertType = Literal["above", "below"]


class PriceAlert:
    """Price alert configuration."""
    
    def __init__(
        self,
        symbol: str,
        target_price: float,
        alert_type: AlertType,
        alert_id: Optional[str] = None,
        created_at: Optional[str] = None
    ):
        self.symbol = symbol
        self.target_price = target_price
        self.alert_type = alert_type
        self.alert_id = alert_id or f"{symbol}_{target_price}_{alert_type}_{int(time.time())}"
        self.created_at = created_at or datetime.utcnow().isoformat() + "Z"
    
    def to_dict(self) -> Dict:
        return {
            "alert_id": self.alert_id,
            "symbol": self.symbol,
            "target_price": self.target_price,
            "alert_type": self.alert_type,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "PriceAlert":
        return cls(
            symbol=data["symbol"],
            target_price=data["target_price"],
            alert_type=data["alert_type"],
            alert_id=data.get("alert_id"),
            created_at=data.get("created_at")
        )


class AlertManager:
    """Manage price alerts."""
    
    def __init__(self, client: Client):
        self.client = client
        self.logger = logging.getLogger(__name__)
    
    def add_alert(
        self,
        symbol: str,
        target_price: float,
        alert_type: AlertType
    ) -> PriceAlert:
        """
        Add a new price alert.
        
        Args:
            symbol: Trading pair symbol
            target_price: Price threshold
            alert_type: "above" or "below"
            
        Returns:
            Created PriceAlert
            
        Example:
            >>> manager = AlertManager(client)
            >>> alert = manager.add_alert("BTCUSDT", 50000, "above")
            >>> print(f"Alert created: {alert.alert_id}")
        """
        alert = PriceAlert(symbol, target_price, alert_type)
        
        alerts = self._load_alerts()
        alerts.append(alert)
        self._save_alerts(alerts)
        
        self.logger.info(
            f"Created alert: {symbol} {alert_type} ${target_price:,.2f}"
        )
        
        return alert
    
    def remove_alert(self, alert_id: str) -> None:
        """
        Remove a price alert.
        
        Args:
            alert_id: Alert identifier
            
        Raises:
            ValueError: If alert not found
        """
        alerts = self._load_alerts()
        
        filtered = [a for a in alerts if a.alert_id != alert_id]
        
        if len(filtered) == len(alerts):
            raise ValueError(f"Alert {alert_id} not found")
        
        self._save_alerts(filtered)
        self.logger.info(f"Removed alert: {alert_id}")
    
    def list_alerts(self) -> List[PriceAlert]:
        """
        Get all active alerts.
        
        Returns:
            List of PriceAlert objects
        """
        return self._load_alerts()
    
    def check_alerts(self, verbose: bool = False) -> List[Dict]:
        """
        Check all alerts and return triggered ones.
        
        Args:
            verbose: If True, log status for all alerts
            
        Returns:
            List of triggered alert dictionaries
            
        Example:
            >>> manager = AlertManager(client)
            >>> triggered = manager.check_alerts(verbose=True)
            >>> for alert in triggered:
            ...     print(f"🔔 Alert! {alert['symbol']} reached ${alert['current_price']}")
        """
        alerts = self._load_alerts()
        triggered = []
        
        if not alerts:
            if verbose:
                self.logger.info("No active alerts")
            return []
        
        for alert in alerts:
            try:
                ticker = self.client.futures_symbol_ticker(symbol=alert.symbol)
                current_price = float(ticker["price"])
                
                is_triggered = False
                
                if alert.alert_type == "above" and current_price >= alert.target_price:
                    is_triggered = True
                elif alert.alert_type == "below" and current_price <= alert.target_price:
                    is_triggered = True
                
                if is_triggered:
                    triggered.append({
                        "alert_id": alert.alert_id,
                        "symbol": alert.symbol,
                        "target_price": alert.target_price,
                        "current_price": current_price,
                        "alert_type": alert.alert_type,
                        "created_at": alert.created_at
                    })
                    self.logger.warning(
                        f"🔔 ALERT TRIGGERED: {alert.symbol} {alert.alert_type} "
                        f"${alert.target_price:,.2f} (current: ${current_price:,.2f})"
                    )
                elif verbose:
                    self.logger.info(
                        f"Alert OK: {alert.symbol} @ ${current_price:,.2f} "
                        f"(target: {alert.alert_type} ${alert.target_price:,.2f})"
                    )
                    
            except BinanceAPIException as e:
                self.logger.error(f"Could not check alert for {alert.symbol}: {e}")
        
        return triggered
    
    def watch(self, interval: int = 60, duration: Optional[int] = None) -> None:
        """
        Continuously monitor alerts.
        
        Args:
            interval: Check interval in seconds (default 60)
            duration: Total duration in seconds (None = run forever)
            
        Example:
            >>> manager = AlertManager(client)
            >>> manager.add_alert("BTCUSDT", 50000, "above")
            >>> manager.watch(interval=30)  # Check every 30 seconds
        """
        self.logger.info(f"Starting alert monitoring (interval: {interval}s)")
        
        start_time = time.time()
        
        try:
            while True:
                triggered = self.check_alerts(verbose=True)
                
                # Auto-remove triggered alerts
                for alert_data in triggered:
                    self.remove_alert(alert_data["alert_id"])
                    self.logger.info(f"Auto-removed triggered alert: {alert_data['alert_id']}")
                
                if duration and (time.time() - start_time) >= duration:
                    self.logger.info("Watch duration completed")
                    break
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.logger.info("Alert monitoring stopped by user")
    
    def _load_alerts(self) -> List[PriceAlert]:
        """Load alerts from disk."""
        if not ALERTS_FILE.exists():
            return []
        
        with open(ALERTS_FILE, "r") as f:
            data = json.load(f)
        
        return [PriceAlert.from_dict(item) for item in data]
    
    def _save_alerts(self, alerts: List[PriceAlert]) -> None:
        """Save alerts to disk."""
        data = [alert.to_dict() for alert in alerts]
        
        with open(ALERTS_FILE, "w") as f:
            json.dump(data, f, indent=2)
