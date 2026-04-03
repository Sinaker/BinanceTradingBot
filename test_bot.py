"""Unit tests for trading bot validators and order functions."""
import pytest
from unittest.mock import Mock, patch
from bot.validators import (
    validate_symbol,
    validate_side,
    validate_quantity,
    validate_price,
    RiskValidator
)
from bot.alerts import PriceAlert, AlertManager


class TestValidators:
    """Test input validation functions."""
    
    def test_validate_symbol_uppercase(self):
        """Test symbol normalization to uppercase."""
        assert validate_symbol("btcusdt") == "BTCUSDT"
        assert validate_symbol("ETHUSDT") == "ETHUSDT"
    
    def test_validate_symbol_invalid_format(self):
        """Test invalid symbol format raises ValueError."""
        with pytest.raises(ValueError):
            validate_symbol("BTC")  # Too short
        with pytest.raises(ValueError):
            validate_symbol("btc-usdt")  # Invalid characters
    
    def test_validate_side_uppercase(self):
        """Test side normalization to uppercase."""
        assert validate_side("buy") == "BUY"
        assert validate_side("SELL") == "SELL"
    
    def test_validate_side_invalid(self):
        """Test invalid side raises ValueError."""
        with pytest.raises(ValueError):
            validate_side("HOLD")
    
    def test_validate_quantity_positive(self):
        """Test quantity must be positive."""
        assert validate_quantity(1.5) == 1.5
        with pytest.raises(ValueError):
            validate_quantity(0)
        with pytest.raises(ValueError):
            validate_quantity(-1)
    
    def test_validate_price_positive(self):
        """Test price must be positive."""
        assert validate_price(50000.0) == 50000.0
        with pytest.raises(ValueError):
            validate_price(None)
        with pytest.raises(ValueError):
            validate_price(0)
        with pytest.raises(ValueError):
            validate_price(-100)


class TestRiskValidator:
    """Test risk validation logic."""
    
    @patch('bot.validators.Client')
    def test_price_sanity_within_range(self, mock_client):
        """Test price sanity check passes for prices within 5% deviation."""
        mock_client.futures_symbol_ticker.return_value = {"price": "50000.00"}
        
        validator = RiskValidator(mock_client)
        valid, msg = validator.check_price_sanity("BTCUSDT", 51000.0, max_deviation=0.05)
        
        assert valid is True
        assert "within acceptable range" in msg
    
    @patch('bot.validators.Client')
    def test_price_sanity_exceeds_range(self, mock_client):
        """Test price sanity check fails for prices beyond 5% deviation."""
        mock_client.futures_symbol_ticker.return_value = {"price": "50000.00"}
        
        validator = RiskValidator(mock_client)
        valid, msg = validator.check_price_sanity("BTCUSDT", 60000.0, max_deviation=0.05)
        
        assert valid is False
        assert "deviates" in msg
    
    @patch('bot.validators.Client')
    def test_order_size_check_safe(self, mock_client):
        """Test order size check passes for reasonable order sizes."""
        mock_client.futures_ticker.return_value = {"volume": "10000.0"}
        
        validator = RiskValidator(mock_client)
        safe, msg = validator.check_order_size_vs_volume("BTCUSDT", 500.0, max_percent=0.10)
        
        assert safe is True
        assert "OK" in msg
    
    @patch('bot.validators.Client')
    def test_order_size_check_large(self, mock_client):
        """Test order size check warns for large orders."""
        mock_client.futures_ticker.return_value = {"volume": "1000.0"}
        
        validator = RiskValidator(mock_client)
        safe, msg = validator.check_order_size_vs_volume("BTCUSDT", 200.0, max_percent=0.10)
        
        assert safe is False
        assert "exceeds" in msg


class TestPriceAlerts:
    """Test price alert functionality."""
    
    def test_price_alert_creation(self):
        """Test PriceAlert object creation."""
        alert = PriceAlert("BTCUSDT", 50000.0, "above")
        
        assert alert.symbol == "BTCUSDT"
        assert alert.target_price == 50000.0
        assert alert.alert_type == "above"
        assert alert.alert_id is not None
    
    def test_price_alert_serialization(self):
        """Test PriceAlert to_dict and from_dict."""
        original = PriceAlert("ETHUSDT", 3000.0, "below", alert_id="test123")
        data = original.to_dict()
        
        restored = PriceAlert.from_dict(data)
        
        assert restored.symbol == original.symbol
        assert restored.target_price == original.target_price
        assert restored.alert_type == original.alert_type
        assert restored.alert_id == original.alert_id
    
    @patch('bot.alerts.Client')
    def test_alert_trigger_above(self, mock_client):
        """Test alert triggers when price goes above target."""
        mock_client.futures_symbol_ticker.return_value = {"price": "51000.00"}
        
        manager = AlertManager(mock_client)
        manager.add_alert("BTCUSDT", 50000.0, "above")
        
        triggered = manager.check_alerts()
        
        assert len(triggered) == 1
        assert triggered[0]["symbol"] == "BTCUSDT"
    
    @patch('bot.alerts.Client')
    def test_alert_trigger_below(self, mock_client):
        """Test alert triggers when price goes below target."""
        mock_client.futures_symbol_ticker.return_value = {"price": "2900.00"}
        
        manager = AlertManager(mock_client)
        manager.add_alert("ETHUSDT", 3000.0, "below")
        
        triggered = manager.check_alerts()
        
        assert len(triggered) == 1
        assert triggered[0]["symbol"] == "ETHUSDT"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
