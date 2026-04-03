"""Unit tests for trading bot validators and order functions."""
import pytest
from bot.validators import validate_symbol, validate_side, validate_quantity, validate_price


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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
