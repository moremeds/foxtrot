"""
Trading-specific validators for the Foxtrot TUI.

This module provides specialized validators for trading operations,
including price validation, volume validation, symbol validation,
and order type validation with real-time market data integration.
"""

from typing import Optional, Dict, Any, List
from decimal import Decimal
from dataclasses import dataclass

from .base import FieldValidator, ValidationResult
from .utils import (
    validate_symbol_format,
    validate_price_precision,
    validate_order_quantity,
    parse_symbol_exchange,
    normalize_symbol,
    is_market_hours
)
from .errors import TradingValidationError, TradingErrorCodes, create_trading_error


@dataclass
class ContractInfo:
    """
    Contract information for validation.
    
    This would typically be populated from the contract manager
    or market data feed.
    """
    symbol: str
    exchange: str
    tick_size: Optional[Decimal] = None
    min_lot_size: Optional[Decimal] = None
    lot_size_increment: Optional[Decimal] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    is_tradeable: bool = True
    supported_order_types: List[str] = None
    
    def __post_init__(self):
        if self.supported_order_types is None:
            self.supported_order_types = ["MARKET", "LIMIT", "STOP"]


class SymbolValidator(FieldValidator):
    """
    Validator for trading symbols with contract lookup and verification.
    
    Validates symbol format, checks contract existence, and verifies
    trading permissions and market status.
    """
    
    def __init__(
        self,
        field_name: str = "symbol",
        required: bool = True,
        contract_manager = None,
        check_market_hours: bool = True
    ):
        super().__init__(field_name, required)
        self.contract_manager = contract_manager
        self.check_market_hours = check_market_hours
    
    def validate(self, value: Any) -> ValidationResult:
        """Validate trading symbol with contract verification."""
        # Check required
        required_result = self._check_required(value)
        if required_result:
            return required_result
        
        # Allow empty optional fields
        if not self.required and (value is None or value == ""):
            return ValidationResult(is_valid=True, value=None)
        
        result = ValidationResult(is_valid=True)
        
        # Normalize symbol
        symbol_str = normalize_symbol(str(value))
        
        if not symbol_str:
            result.add_error("Symbol cannot be empty")
            return result
        
        # Validate symbol format
        is_valid_format, format_error = validate_symbol_format(symbol_str)
        if not is_valid_format:
            result.add_error(format_error)
            return result
        
        # Parse symbol and exchange
        symbol, exchange = parse_symbol_exchange(symbol_str)
        
        # Contract verification (if contract manager available)
        if self.contract_manager:
            try:
                contract_info = self._get_contract_info(symbol, exchange)
                if not contract_info:
                    result.add_error(f"Symbol {symbol_str} not found")
                    return result
                
                if not contract_info.is_tradeable:
                    result.add_error(f"Symbol {symbol_str} is not tradeable")
                    return result
                
                # Store contract info for use by other validators
                result.metadata["contract_info"] = contract_info
                
                # Check market hours if required
                if self.check_market_hours and not is_market_hours(contract_info.exchange):
                    result.add_warning(f"Market for {symbol_str} is currently closed")
                
            except Exception as e:
                result.add_error(f"Unable to verify symbol {symbol_str}: {str(e)}")
                return result
        
        result.value = symbol_str
        return result
    
    def _get_contract_info(self, symbol: str, exchange: Optional[str]) -> Optional[ContractInfo]:
        """
        Get contract information from contract manager.
        
        This is a placeholder implementation - in practice, this would
        integrate with the actual contract manager system.
        """
        if not self.contract_manager:
            return None
        
        # Placeholder implementation
        # In reality, this would query the contract manager
        return ContractInfo(
            symbol=symbol,
            exchange=exchange or "UNKNOWN",
            tick_size=Decimal("0.01"),
            min_lot_size=Decimal("1"),
            lot_size_increment=Decimal("1")
        )


class PriceValidator(FieldValidator):
    """
    Validator for trading prices with tick size and range validation.
    
    Validates price format, checks against minimum tick size,
    and verifies price is within allowed range for the symbol.
    """
    
    def __init__(
        self,
        field_name: str = "price",
        required: bool = True,
        contract_info: Optional[ContractInfo] = None,
        order_type: Optional[str] = None
    ):
        super().__init__(field_name, required)
        self.contract_info = contract_info
        self.order_type = order_type
    
    def validate(self, value: Any) -> ValidationResult:
        """Validate trading price with tick size constraints."""
        # Check required (but allow empty for market orders)
        if self.order_type == "MARKET":
            if value is None or value == "":
                return ValidationResult(is_valid=True, value=None)
        else:
            required_result = self._check_required(value)
            if required_result:
                return required_result
        
        # Allow empty optional fields
        if not self.required and (value is None or value == ""):
            return ValidationResult(is_valid=True, value=None)
        
        result = ValidationResult(is_valid=True)
        
        # Get constraints from contract info
        tick_size = None
        min_price = None
        max_price = None
        
        if self.contract_info:
            tick_size = self.contract_info.tick_size
            min_price = self.contract_info.min_price
            max_price = self.contract_info.max_price
        
        # Validate price precision and range
        is_valid_price, decimal_price, price_error = validate_price_precision(
            value, tick_size, min_price, max_price
        )
        
        if not is_valid_price:
            result.add_error(price_error)
            return result
        
        # Additional validation based on order type
        if self.order_type == "STOP" and decimal_price <= 0:
            result.add_error("Stop price must be greater than zero")
            return result
        
        result.value = decimal_price
        return result


class VolumeValidator(FieldValidator):
    """
    Validator for order volumes with lot size and fund availability checks.
    
    Validates volume format, checks against minimum lot size,
    and verifies sufficient funds are available.
    """
    
    def __init__(
        self,
        field_name: str = "volume",
        required: bool = True,
        contract_info: Optional[ContractInfo] = None,
        account_manager = None,
        price: Optional[Decimal] = None
    ):
        super().__init__(field_name, required)
        self.contract_info = contract_info
        self.account_manager = account_manager
        self.price = price
    
    def validate(self, value: Any) -> ValidationResult:
        """Validate order volume with lot size and fund constraints."""
        # Check required
        required_result = self._check_required(value)
        if required_result:
            return required_result
        
        # Allow empty optional fields
        if not self.required and (value is None or value == ""):
            return ValidationResult(is_valid=True, value=None)
        
        result = ValidationResult(is_valid=True)
        
        # Get constraints from contract info
        min_lot_size = None
        lot_size_increment = None
        
        if self.contract_info:
            min_lot_size = self.contract_info.min_lot_size
            lot_size_increment = self.contract_info.lot_size_increment
        
        # Validate quantity
        is_valid_qty, decimal_quantity, qty_error = validate_order_quantity(
            value, min_lot_size, lot_size_increment
        )
        
        if not is_valid_qty:
            result.add_error(qty_error)
            return result
        
        # Check fund availability if account manager and price available
        if self.account_manager and self.price and decimal_quantity:
            try:
                order_value = decimal_quantity * self.price
                available_funds = self._get_available_funds()
                
                if available_funds is not None and order_value > available_funds:
                    result.add_error(
                        f"Insufficient funds. Required: {order_value:.2f}, Available: {available_funds:.2f}"
                    )
                    return result
                
            except Exception as e:
                result.add_warning(f"Unable to check fund availability: {str(e)}")
        
        result.value = decimal_quantity
        return result
    
    def _get_available_funds(self) -> Optional[Decimal]:
        """
        Get available funds from account manager.
        
        This is a placeholder implementation - in practice, this would
        integrate with the actual account manager system.
        """
        if not self.account_manager:
            return None
        
        # Placeholder implementation
        # In reality, this would query the account manager
        return Decimal("10000.00")  # Mock available funds


class OrderTypeValidator(FieldValidator):
    """
    Validator for order types with symbol-specific support checks.
    
    Validates order type format and checks if the order type
    is supported for the specific symbol/exchange combination.
    """
    
    def __init__(
        self,
        field_name: str = "order_type",
        required: bool = True,
        contract_info: Optional[ContractInfo] = None,
        allowed_types: Optional[List[str]] = None
    ):
        super().__init__(field_name, required)
        self.contract_info = contract_info
        self.allowed_types = allowed_types or ["MARKET", "LIMIT", "STOP", "STOP_LIMIT"]
    
    def validate(self, value: Any) -> ValidationResult:
        """Validate order type with symbol-specific support."""
        # Check required
        required_result = self._check_required(value)
        if required_result:
            return required_result
        
        # Allow empty optional fields
        if not self.required and (value is None or value == ""):
            return ValidationResult(is_valid=True, value="MARKET")  # Default to market
        
        result = ValidationResult(is_valid=True)
        
        # Normalize order type
        order_type = str(value).strip().upper()
        
        # Check if order type is in allowed list
        if order_type not in self.allowed_types:
            result.add_error(f"Order type must be one of: {', '.join(self.allowed_types)}")
            return result
        
        # Check symbol-specific support
        if self.contract_info and self.contract_info.supported_order_types:
            if order_type not in self.contract_info.supported_order_types:
                result.add_error(
                    f"Order type {order_type} not supported for this symbol. "
                    f"Supported types: {', '.join(self.contract_info.supported_order_types)}"
                )
                return result
        
        result.value = order_type
        return result


class DirectionValidator(FieldValidator):
    """
    Validator for order direction (BUY/SELL).
    
    Simple validator to ensure direction is one of the allowed values.
    """
    
    def __init__(self, field_name: str = "direction", required: bool = True):
        super().__init__(field_name, required)
        self.allowed_directions = ["BUY", "SELL"]
    
    def validate(self, value: Any) -> ValidationResult:
        """Validate order direction."""
        # Check required
        required_result = self._check_required(value)
        if required_result:
            return required_result
        
        # Allow empty optional fields
        if not self.required and (value is None or value == ""):
            return ValidationResult(is_valid=True, value="BUY")  # Default to buy
        
        result = ValidationResult(is_valid=True)
        
        # Normalize direction
        direction = str(value).strip().upper()
        
        # Check if direction is valid
        if direction not in self.allowed_directions:
            result.add_error(f"Direction must be one of: {', '.join(self.allowed_directions)}")
            return result
        
        result.value = direction
        return result


class ExchangeValidator(FieldValidator):
    """
    Validator for exchange identifiers.
    
    Validates exchange format and optionally checks if the exchange
    is supported by the current adapter configuration.
    """
    
    def __init__(
        self,
        field_name: str = "exchange",
        required: bool = False,
        supported_exchanges: Optional[List[str]] = None
    ):
        super().__init__(field_name, required)
        self.supported_exchanges = supported_exchanges or [
            "SMART", "NASDAQ", "NYSE", "BINANCE", "COINBASE"
        ]
    
    def validate(self, value: Any) -> ValidationResult:
        """Validate exchange identifier."""
        # Check required
        required_result = self._check_required(value)
        if required_result:
            return required_result
        
        # Allow empty optional fields
        if not self.required and (value is None or value == ""):
            return ValidationResult(is_valid=True, value=None)
        
        result = ValidationResult(is_valid=True)
        
        # Normalize exchange
        exchange = str(value).strip().upper()
        
        if not exchange:
            if self.required:
                result.add_error("Exchange cannot be empty")
                return result
            else:
                return ValidationResult(is_valid=True, value=None)
        
        # Check if exchange is supported
        if exchange not in self.supported_exchanges:
            result.add_warning(
                f"Exchange {exchange} may not be supported. "
                f"Supported exchanges: {', '.join(self.supported_exchanges)}"
            )
        
        result.value = exchange
        return result