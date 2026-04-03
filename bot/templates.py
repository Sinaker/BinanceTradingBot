"""
Order templates system for saving and loading order configurations.

Features:
- Save order configurations with custom names
- Load and execute saved templates
- List available templates
- Share templates across team
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)


class OrderTemplate:
    """Manage order templates for quick execution."""
    
    @staticmethod
    def save(
        name: str,
        order_type: str,
        symbol: str,
        side: str,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        description: str = ""
    ) -> None:
        """
        Save an order template.
        
        Args:
            name: Template name (e.g., "scalp-btc", "swing-eth")
            order_type: Order type (market, limit, stop-limit)
            symbol: Trading pair
            side: BUY or SELL
            quantity: Order quantity
            price: Limit price (if applicable)
            stop_price: Stop price (if applicable)
            description: Template description
            
        Example:
            >>> OrderTemplate.save(
            ...     "scalp-btc",
            ...     "limit",
            ...     "BTCUSDT",
            ...     "BUY",
            ...     0.001,
            ...     price=45000,
            ...     description="Quick BTC scalp entry"
            ... )
        """
        template_data = {
            "name": name,
            "order_type": order_type,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "description": description
        }
        
        if price is not None:
            template_data["price"] = price
        if stop_price is not None:
            template_data["stop_price"] = stop_price
        
        template_path = TEMPLATES_DIR / f"{name}.json"
        
        with open(template_path, "w") as f:
            json.dump(template_data, f, indent=2)
        
        logger.info(f"Saved template: {name} -> {template_path}")
    
    @staticmethod
    def load(name: str) -> Dict[str, Any]:
        """
        Load an order template.
        
        Args:
            name: Template name
            
        Returns:
            Template configuration dictionary
            
        Raises:
            FileNotFoundError: If template doesn't exist
            
        Example:
            >>> config = OrderTemplate.load("scalp-btc")
            >>> print(config["symbol"])
            'BTCUSDT'
        """
        template_path = TEMPLATES_DIR / f"{name}.json"
        
        if not template_path.exists():
            raise FileNotFoundError(
                f"Template '{name}' not found. Use 'list-templates' to see available templates."
            )
        
        with open(template_path, "r") as f:
            template_data = json.load(f)
        
        logger.info(f"Loaded template: {name}")
        return template_data
    
    @staticmethod
    def list_all() -> List[Dict[str, Any]]:
        """
        List all available templates.
        
        Returns:
            List of template configurations
            
        Example:
            >>> templates = OrderTemplate.list_all()
            >>> for t in templates:
            ...     print(f"{t['name']}: {t['description']}")
        """
        templates = []
        
        for template_file in TEMPLATES_DIR.glob("*.json"):
            try:
                with open(template_file, "r") as f:
                    template_data = json.load(f)
                    templates.append(template_data)
            except Exception as e:
                logger.warning(f"Could not load template {template_file}: {e}")
        
        return templates
    
    @staticmethod
    def delete(name: str) -> None:
        """
        Delete a template.
        
        Args:
            name: Template name
            
        Raises:
            FileNotFoundError: If template doesn't exist
        """
        template_path = TEMPLATES_DIR / f"{name}.json"
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template '{name}' not found.")
        
        template_path.unlink()
        logger.info(f"Deleted template: {name}")
