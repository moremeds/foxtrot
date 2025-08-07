"""
Account monitor filtering and data validation logic.

This module handles all filtering operations, data validation,
and filter management for the account monitor.
"""

import logging
from typing import Any, Dict, List, Optional, Set
from abc import ABC, abstractmethod

from foxtrot.util.object import AccountData
from .config import AccountDisplaySettings, AccountMonitorConfig

# Set up logging
logger = logging.getLogger(__name__)


class AccountFilter(ABC):
    """Abstract base class for account filters."""
    
    @abstractmethod
    def apply(self, account_data: AccountData) -> bool:
        """
        Apply filter to account data.
        
        Args:
            account_data: Account data to filter
            
        Returns:
            True if account passes the filter, False otherwise
        """
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Get human-readable description of the filter."""
        pass


class CurrencyFilter(AccountFilter):
    """Filter accounts by currency."""
    
    def __init__(self, currency: str):
        """
        Initialize currency filter.
        
        Args:
            currency: Currency code to filter by (e.g., "USD", "EUR")
        """
        self.currency = currency.upper()
    
    def apply(self, account_data: AccountData) -> bool:
        """Apply currency filter."""
        return account_data.currency == self.currency
    
    def get_description(self) -> str:
        """Get filter description."""
        return f"Currency: {self.currency}"


class GatewayFilter(AccountFilter):
    """Filter accounts by gateway."""
    
    def __init__(self, gateway: str):
        """
        Initialize gateway filter.
        
        Args:
            gateway: Gateway name to filter by
        """
        self.gateway = gateway
    
    def apply(self, account_data: AccountData) -> bool:
        """Apply gateway filter."""
        return account_data.gateway_name == self.gateway
    
    def get_description(self) -> str:
        """Get filter description."""
        return f"Gateway: {self.gateway}"


class MinBalanceFilter(AccountFilter):
    """Filter accounts by minimum balance threshold."""
    
    def __init__(self, min_balance: float):
        """
        Initialize minimum balance filter.
        
        Args:
            min_balance: Minimum balance threshold
        """
        self.min_balance = min_balance
    
    def apply(self, account_data: AccountData) -> bool:
        """Apply minimum balance filter."""
        return account_data.balance >= self.min_balance
    
    def get_description(self) -> str:
        """Get filter description."""
        return f"Min Balance: ${self.min_balance:,.2f}"


class ZeroBalanceFilter(AccountFilter):
    """Filter to hide zero balance accounts."""
    
    def __init__(self, hide_zero: bool = True):
        """
        Initialize zero balance filter.
        
        Args:
            hide_zero: If True, hide zero balance accounts
        """
        self.hide_zero = hide_zero
    
    def apply(self, account_data: AccountData) -> bool:
        """Apply zero balance filter."""
        if not self.hide_zero:
            return True  # Show all accounts
        
        # Hide accounts with zero balance and zero available
        return not (account_data.balance == 0 and account_data.available == 0)
    
    def get_description(self) -> str:
        """Get filter description."""
        return "Hide Zero Balances" if self.hide_zero else "Show All Balances"


class MarginAccountFilter(AccountFilter):
    """Filter to show only accounts with margin positions."""
    
    def __init__(self, min_margin: float = 0.0):
        """
        Initialize margin account filter.
        
        Args:
            min_margin: Minimum margin value to qualify
        """
        self.min_margin = min_margin
    
    def apply(self, account_data: AccountData) -> bool:
        """Apply margin account filter."""
        margin = getattr(account_data, 'margin', 0)
        return margin > self.min_margin
    
    def get_description(self) -> str:
        """Get filter description."""
        return f"Margin Accounts (>${self.min_margin:,.2f}+)"


class AccountFilterManager:
    """
    Manages multiple account filters and provides unified filtering.
    
    Features:
    - Multiple simultaneous filters
    - Filter chaining with AND logic
    - Dynamic filter addition/removal
    - Filter state management
    - Filter descriptions and summaries
    """
    
    def __init__(self, config: Optional[AccountMonitorConfig] = None, display_settings: Optional[AccountDisplaySettings] = None):
        """
        Initialize filter manager.
        
        Args:
            config: Account monitor configuration (for future use)
            display_settings: Display settings containing filter configuration
        """
        self.config = config
        self.display_settings = display_settings
        self.active_filters: List[AccountFilter] = []
        self._filter_cache: Dict[str, bool] = {}
    
    def apply_all_filters(self, account_data: AccountData) -> bool:
        """
        Apply all active filters to account data.
        
        Args:
            account_data: Account data to filter
            
        Returns:
            True if account passes all filters, False otherwise
        """
        try:
            # Create cache key for performance
            cache_key = self._create_cache_key(account_data)
            if cache_key in self._filter_cache:
                return self._filter_cache[cache_key]
            
            # Apply all filters with AND logic
            result = True
            for filter_obj in self.active_filters:
                if not filter_obj.apply(account_data):
                    result = False
                    break
            
            # Cache result
            self._filter_cache[cache_key] = result
            return result
            
        except Exception as e:
            logger.error(f"Error applying filters to account {account_data.vt_accountid}: {e}")
            return True  # Default to showing account on error
    
    def _create_cache_key(self, account_data: AccountData) -> str:
        """Create a cache key for the account data."""
        return f"{account_data.vt_accountid}_{account_data.balance}_{account_data.available}_{len(self.active_filters)}"
    
    def clear_cache(self) -> None:
        """Clear the filter cache when filters change."""
        self._filter_cache.clear()
    
    def add_currency_filter(self, currency: str) -> None:
        """
        Add or update currency filter.
        
        Args:
            currency: Currency code to filter by
        """
        # Remove existing currency filter
        self.remove_filter_by_type(CurrencyFilter)
        
        if currency:
            self.active_filters.append(CurrencyFilter(currency))
            self.display_settings.currency_filter = currency
        else:
            self.display_settings.currency_filter = None
        
        self.clear_cache()
    
    def add_gateway_filter(self, gateway: str) -> None:
        """
        Add or update gateway filter.
        
        Args:
            gateway: Gateway name to filter by
        """
        # Remove existing gateway filter
        self.remove_filter_by_type(GatewayFilter)
        
        if gateway:
            self.active_filters.append(GatewayFilter(gateway))
            self.display_settings.gateway_filter = gateway
        else:
            self.display_settings.gateway_filter = None
        
        self.clear_cache()
    
    def add_min_balance_filter(self, min_balance: float) -> None:
        """
        Add or update minimum balance filter.
        
        Args:
            min_balance: Minimum balance threshold
        """
        # Remove existing balance filter
        self.remove_filter_by_type(MinBalanceFilter)
        
        if min_balance is not None and min_balance >= 0:
            self.active_filters.append(MinBalanceFilter(min_balance))
            self.display_settings.min_balance_filter = min_balance
        else:
            self.display_settings.min_balance_filter = None
        
        self.clear_cache()
    
    def set_zero_balance_visibility(self, show_zero: bool) -> None:
        """
        Set zero balance account visibility.
        
        Args:
            show_zero: If True, show zero balance accounts
        """
        # Remove existing zero balance filter
        self.remove_filter_by_type(ZeroBalanceFilter)
        
        # Add filter to hide zero balances if requested
        if not show_zero:
            self.active_filters.append(ZeroBalanceFilter(hide_zero=True))
        
        self.display_settings.show_zero_balances = show_zero
        self.clear_cache()
    
    def add_margin_filter(self, min_margin: float = 100.0) -> None:
        """
        Add margin account filter.
        
        Args:
            min_margin: Minimum margin threshold
        """
        # Remove existing margin filter
        self.remove_filter_by_type(MarginAccountFilter)
        
        self.active_filters.append(MarginAccountFilter(min_margin))
        self.clear_cache()
    
    def remove_filter_by_type(self, filter_type: type) -> None:
        """
        Remove filters of a specific type.
        
        Args:
            filter_type: Type of filter to remove
        """
        self.active_filters = [
            f for f in self.active_filters 
            if not isinstance(f, filter_type)
        ]
        self.clear_cache()
    
    def clear_all_filters(self) -> None:
        """Clear all active filters."""
        self.active_filters.clear()
        self.display_settings.reset_filters()
        self.clear_cache()
    
    def get_active_filter_descriptions(self) -> List[str]:
        """Get descriptions of all active filters."""
        return [filter_obj.get_description() for filter_obj in self.active_filters]
    
    def get_filter_summary(self) -> str:
        """Get a summary of all active filters."""
        descriptions = self.get_active_filter_descriptions()
        return ", ".join(descriptions) if descriptions else "None"
    
    def has_active_filters(self) -> bool:
        """Check if any filters are currently active."""
        return len(self.active_filters) > 0


class AccountDataValidator:
    """
    Validates account data for consistency and completeness.
    
    Features:
    - Required field validation
    - Data type validation
    - Range validation for numeric fields
    - Cross-field validation (e.g., balance >= frozen)
    - Currency format validation
    """
    
    REQUIRED_FIELDS = {
        'vt_accountid': str,
        'balance': (int, float),
        'available': (int, float),
        'frozen': (int, float),
        'currency': str,
        'gateway_name': str
    }
    
    def __init__(self):
        """Initialize validator with default settings."""
        self.validation_errors: List[str] = []
        self.strict_mode = False  # If True, fail on any validation error
    
    def validate_account_data(self, account_data: AccountData) -> bool:
        """
        Validate account data for completeness and consistency.
        
        Args:
            account_data: Account data to validate
            
        Returns:
            True if validation passes, False otherwise
        """
        self.validation_errors.clear()
        
        try:
            # Required field validation
            if not self._validate_required_fields(account_data):
                return False
            
            # Numeric range validation
            if not self._validate_numeric_ranges(account_data):
                return False
            
            # Cross-field validation
            if not self._validate_cross_fields(account_data):
                return False
            
            # Currency format validation
            if not self._validate_currency_format(account_data):
                return False
            
            return len(self.validation_errors) == 0
            
        except Exception as e:
            logger.error(f"Error validating account data: {e}")
            self.validation_errors.append(f"Validation error: {e}")
            return False
    
    def _validate_required_fields(self, account_data: AccountData) -> bool:
        """Validate that required fields are present and of correct type."""
        valid = True
        
        for field_name, expected_type in self.REQUIRED_FIELDS.items():
            if not hasattr(account_data, field_name):
                self.validation_errors.append(f"Missing required field: {field_name}")
                valid = False
                continue
            
            field_value = getattr(account_data, field_name)
            if not isinstance(field_value, expected_type):
                self.validation_errors.append(
                    f"Field {field_name} has invalid type: expected {expected_type}, got {type(field_value)}"
                )
                valid = False
        
        return valid or not self.strict_mode
    
    def _validate_numeric_ranges(self, account_data: AccountData) -> bool:
        """Validate numeric fields are within reasonable ranges."""
        valid = True
        
        # Balance should be non-negative (allowing for some flexibility)
        if account_data.balance < -1000000:  # Allow some negative balance for margin
            self.validation_errors.append(f"Balance too negative: {account_data.balance}")
            valid = False
        
        # Available balance should be reasonable
        if account_data.available < -1000000:
            self.validation_errors.append(f"Available balance too negative: {account_data.available}")
            valid = False
        
        # Frozen should be non-negative
        if account_data.frozen < 0:
            self.validation_errors.append(f"Frozen balance cannot be negative: {account_data.frozen}")
            valid = False
        
        return valid or not self.strict_mode
    
    def _validate_cross_fields(self, account_data: AccountData) -> bool:
        """Validate relationships between fields."""
        valid = True
        
        # Available + Frozen should approximately equal Balance (with some tolerance)
        expected_balance = account_data.available + account_data.frozen
        balance_diff = abs(account_data.balance - expected_balance)
        
        # Allow 1% tolerance or $1 minimum
        tolerance = max(abs(account_data.balance) * 0.01, 1.0)
        
        if balance_diff > tolerance:
            self.validation_errors.append(
                f"Balance inconsistency: balance={account_data.balance}, "
                f"available+frozen={expected_balance}, diff={balance_diff}"
            )
            if self.strict_mode:
                valid = False
        
        return valid
    
    def _validate_currency_format(self, account_data: AccountData) -> bool:
        """Validate currency format."""
        valid = True
        
        # Currency should be 3 uppercase letters
        if len(account_data.currency) != 3:
            self.validation_errors.append(f"Invalid currency format: {account_data.currency}")
            valid = False
        
        if not account_data.currency.isupper():
            # This is more of a warning than an error
            if self.strict_mode:
                self.validation_errors.append(f"Currency should be uppercase: {account_data.currency}")
                valid = False
        
        return valid or not self.strict_mode
    
    def get_validation_errors(self) -> List[str]:
        """Get list of validation errors from last validation."""
        return self.validation_errors.copy()
    
    def set_strict_mode(self, strict: bool) -> None:
        """
        Set strict validation mode.
        
        Args:
            strict: If True, fail validation on any error
        """
        self.strict_mode = strict