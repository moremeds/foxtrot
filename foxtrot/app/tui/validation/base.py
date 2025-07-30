"""
Base validation classes for the Foxtrot TUI validation framework.

This module provides the core validation infrastructure that all other
validators build upon, including result structures, error handling,
and validation chaining capabilities.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Union
import re
from decimal import Decimal, InvalidOperation


@dataclass
class ValidationResult:
    """
    Structured result of validation operations.
    
    Attributes:
        is_valid: Whether validation passed
        value: The validated/cleaned value (None if invalid)
        errors: List of error messages
        warnings: List of warning messages
        metadata: Additional validation metadata
    """
    is_valid: bool
    value: Any = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_error(self, message: str) -> None:
        """Add an error message and mark result as invalid."""
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)
    
    def merge(self, other: 'ValidationResult') -> 'ValidationResult':
        """Merge another validation result into this one."""
        return ValidationResult(
            is_valid=self.is_valid and other.is_valid,
            value=other.value if other.is_valid else self.value,
            errors=self.errors + other.errors,
            warnings=self.warnings + other.warnings,
            metadata={**self.metadata, **other.metadata}
        )


class ValidationError(Exception):
    """Base exception for validation errors."""
    
    def __init__(self, message: str, field_name: str = None):
        super().__init__(message)
        self.field_name = field_name


class FieldValidator(ABC):
    """
    Abstract base class for field validators.
    
    All field validators should inherit from this class and implement
    the validate method to provide specific validation logic.
    """
    
    def __init__(self, field_name: str, required: bool = True):
        self.field_name = field_name
        self.required = required
    
    @abstractmethod
    def validate(self, value: Any) -> ValidationResult:
        """
        Validate a field value.
        
        Args:
            value: The value to validate
            
        Returns:
            ValidationResult with validation outcome
        """
        pass
    
    def _check_required(self, value: Any) -> Optional[ValidationResult]:
        """Check if required field is present."""
        if self.required and (value is None or value == ""):
            return ValidationResult(
                is_valid=False,
                errors=[f"{self.field_name} is required"]
            )
        return None


class NumericValidator(FieldValidator):
    """
    Validator for numeric fields with range and precision constraints.
    
    Supports integer and decimal validation with configurable min/max
    values and precision requirements.
    """
    
    def __init__(
        self,
        field_name: str,
        required: bool = True,
        min_value: Optional[Union[int, float, Decimal]] = None,
        max_value: Optional[Union[int, float, Decimal]] = None,
        decimal_places: Optional[int] = None,
        allow_negative: bool = True
    ):
        super().__init__(field_name, required)
        self.min_value = min_value
        self.max_value = max_value
        self.decimal_places = decimal_places
        self.allow_negative = allow_negative
    
    def validate(self, value: Any) -> ValidationResult:
        """Validate numeric value with range and precision checks."""
        # Check required
        required_result = self._check_required(value)
        if required_result:
            return required_result
        
        # Allow empty optional fields
        if not self.required and (value is None or value == ""):
            return ValidationResult(is_valid=True, value=None)
        
        result = ValidationResult(is_valid=True)
        
        # Convert to decimal for precise calculations
        try:
            if isinstance(value, str):
                value = value.strip()
            decimal_value = Decimal(str(value))
        except (InvalidOperation, ValueError):
            result.add_error(f"{self.field_name} must be a valid number")
            return result
        
        # Check negative values
        if not self.allow_negative and decimal_value < 0:
            result.add_error(f"{self.field_name} cannot be negative")
            return result
        
        # Check range
        if self.min_value is not None and decimal_value < Decimal(str(self.min_value)):
            result.add_error(f"{self.field_name} must be at least {self.min_value}")
            return result
        
        if self.max_value is not None and decimal_value > Decimal(str(self.max_value)):
            result.add_error(f"{self.field_name} must be at most {self.max_value}")
            return result
        
        # Check decimal places
        if self.decimal_places is not None:
            if decimal_value.as_tuple().exponent < -self.decimal_places:
                result.add_error(
                    f"{self.field_name} cannot have more than {self.decimal_places} decimal places"
                )
                return result
        
        result.value = decimal_value
        return result


class RegexValidator(FieldValidator):
    """
    Validator for text fields using regular expressions.
    
    Provides pattern matching validation with customizable error messages
    and optional text cleaning/formatting.
    """
    
    def __init__(
        self,
        field_name: str,
        pattern: str,
        required: bool = True,
        error_message: Optional[str] = None,
        flags: int = 0
    ):
        super().__init__(field_name, required)
        self.pattern = re.compile(pattern, flags)
        self.error_message = error_message or f"{field_name} format is invalid"
    
    def validate(self, value: Any) -> ValidationResult:
        """Validate text value against regex pattern."""
        # Check required
        required_result = self._check_required(value)
        if required_result:
            return required_result
        
        # Allow empty optional fields
        if not self.required and (value is None or value == ""):
            return ValidationResult(is_valid=True, value=None)
        
        result = ValidationResult(is_valid=True)
        
        # Convert to string
        str_value = str(value).strip()
        
        # Check pattern
        if not self.pattern.match(str_value):
            result.add_error(self.error_message)
            return result
        
        result.value = str_value
        return result


class ChoiceValidator(FieldValidator):
    """
    Validator for fields that must be one of a set of allowed values.
    
    Supports case-insensitive matching and custom value transformation.
    """
    
    def __init__(
        self,
        field_name: str,
        choices: List[Any],
        required: bool = True,
        case_sensitive: bool = True
    ):
        super().__init__(field_name, required)
        self.choices = choices
        self.case_sensitive = case_sensitive
        
        if not case_sensitive:
            self.choice_map = {str(choice).lower(): choice for choice in choices}
    
    def validate(self, value: Any) -> ValidationResult:
        """Validate value is in allowed choices."""
        # Check required
        required_result = self._check_required(value)
        if required_result:
            return required_result
        
        # Allow empty optional fields
        if not self.required and (value is None or value == ""):
            return ValidationResult(is_valid=True, value=None)
        
        result = ValidationResult(is_valid=True)
        
        # Check choices
        if self.case_sensitive:
            if value not in self.choices:
                result.add_error(f"{self.field_name} must be one of: {', '.join(map(str, self.choices))}")
                return result
            result.value = value
        else:
            str_value = str(value).lower()
            if str_value not in self.choice_map:
                result.add_error(f"{self.field_name} must be one of: {', '.join(map(str, self.choices))}")
                return result
            result.value = self.choice_map[str_value]
        
        return result


class ValidatorChain:
    """
    Chain multiple validators together for sequential validation.
    
    Allows complex validation logic by combining multiple validators
    in a pipeline, with early termination on first failure.
    """
    
    def __init__(self, validators: List[FieldValidator]):
        self.validators = validators
    
    def validate(self, value: Any) -> ValidationResult:
        """Run all validators in sequence."""
        result = ValidationResult(is_valid=True, value=value)
        
        for validator in self.validators:
            validator_result = validator.validate(result.value)
            result = result.merge(validator_result)
            
            # Update value if validation succeeded and provided a new value
            if validator_result.is_valid and validator_result.value is not None:
                result.value = validator_result.value
            
            # Early termination on error (but continue for warnings)
            if not validator_result.is_valid:
                break
        
        return result


class FormValidator:
    """
    Validator for forms with multiple fields and cross-field validation rules.
    
    Manages validation of entire forms, including field-level validation
    and cross-field business logic validation.
    """
    
    def __init__(self):
        self.field_validators: Dict[str, FieldValidator] = {}
        self.cross_field_rules: List[Callable[[Dict[str, Any]], ValidationResult]] = []
    
    def add_field_validator(self, field_name: str, validator: FieldValidator) -> None:
        """Add a validator for a specific field."""
        self.field_validators[field_name] = validator
    
    def add_cross_field_rule(self, rule: Callable[[Dict[str, Any]], ValidationResult]) -> None:
        """Add a cross-field validation rule."""
        self.cross_field_rules.append(rule)
    
    def validate(self, data: Dict[str, Any]) -> Dict[str, ValidationResult]:
        """
        Validate form data.
        
        Args:
            data: Dictionary of field names to values
            
        Returns:
            Dictionary of field names to validation results
        """
        results = {}
        validated_data = {}
        
        # Validate individual fields
        for field_name, validator in self.field_validators.items():
            field_value = data.get(field_name)
            field_result = validator.validate(field_value)
            results[field_name] = field_result
            
            if field_result.is_valid:
                validated_data[field_name] = field_result.value
        
        # Run cross-field validation if all fields are valid
        if all(result.is_valid for result in results.values()):
            for rule in self.cross_field_rules:
                rule_result = rule(validated_data)
                if not rule_result.is_valid:
                    # Add cross-field errors to form result
                    if "_form" not in results:
                        results["_form"] = ValidationResult(is_valid=True)
                    results["_form"] = results["_form"].merge(rule_result)
        
        return results