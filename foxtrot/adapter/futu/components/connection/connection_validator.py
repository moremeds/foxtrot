"""
Futu connection validator for settings and RSA key validation.

This module provides comprehensive validation for Futu OpenD connection
settings, RSA key files, and configuration parameters.
"""

import os
from typing import Any, Dict, List, Tuple, Union

from .validation_utils import (
    validate_boolean_settings,
    validate_numeric_settings, 
    validate_rsa_file_format,
    validate_string_settings
)


class FutuConnectionValidator:
    """Static validator for Futu connection settings and RSA keys."""

    @staticmethod
    def validate_settings(settings: Dict[str, Any]) -> Tuple[bool, str]:
        """Comprehensive validation of connection settings."""
        if not isinstance(settings, dict):
            return False, "Settings must be a dictionary"

        # Required settings validation
        required_keys: List[str] = ["Host", "Port", "RSA Key File"]
        for key in required_keys:
            if key not in settings:
                return False, f"Required setting missing: {key}"

        # Host validation
        host = settings.get("Host")
        if not isinstance(host, str) or not host.strip():
            return False, "Host must be a non-empty string"

        # Port validation
        port = settings.get("Port")
        if not isinstance(port, int) or not (1 <= port <= 65535):
            return False, "Port must be an integer between 1 and 65535"

        # Delegate to utility validators
        for validator in [validate_numeric_settings, validate_boolean_settings, validate_string_settings]:
            is_valid, message = validator(settings)
            if not is_valid:
                return False, message

        # Market access validation - at least one market must be enabled
        market_access: List[bool] = [
            settings.get("HK Market Access", False),
            settings.get("US Market Access", False),
            settings.get("CN Market Access", False)
        ]

        if not any(market_access):
            return False, "At least one market access must be enabled"

        return True, "Settings validation successful"

    @staticmethod
    def validate_rsa_key(rsa_file: str) -> Tuple[bool, str]:
        """Validate RSA key file exists, is readable, and has proper format."""
        if not rsa_file or not isinstance(rsa_file, str):
            return False, "RSA key file path is empty or invalid"

        if not os.path.exists(rsa_file):
            return False, f"RSA key file not found: {rsa_file}"

        if not os.access(rsa_file, os.R_OK):
            return False, f"RSA key file not readable: {rsa_file}"

        return validate_rsa_file_format(rsa_file)

    @staticmethod
    def validate_connection_parameters(host: str, port: int) -> Tuple[bool, str]:
        """Validate basic connection parameters."""
        # Host validation
        if not isinstance(host, str) or not host.strip():
            return False, "Host must be a non-empty string"
            
        host = host.strip()
        if len(host) > 255:
            return False, "Host address too long (>255 characters)"
            
        # Port validation
        if not isinstance(port, int):
            return False, "Port must be an integer"
            
        if not (1 <= port <= 65535):
            return False, "Port must be between 1 and 65535"
            
        return True, "Connection parameters valid"

    @staticmethod
    def validate_market_access(settings: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate market access configuration."""
        market_flags = {
            "HK Market Access": settings.get("HK Market Access", False),
            "US Market Access": settings.get("US Market Access", False), 
            "CN Market Access": settings.get("CN Market Access", False)
        }
        
        # Validate each flag is boolean
        for flag_name, flag_value in market_flags.items():
            if not isinstance(flag_value, bool):
                return False, f"{flag_name} must be a boolean value"
        
        # At least one market must be enabled
        if not any(market_flags.values()):
            return False, "At least one market access must be enabled"
            
        return True, "Market access configuration valid"

    @staticmethod
    def validate_trading_environment(settings: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate trading environment settings."""
        # Paper trading validation
        if "Paper Trading" in settings:
            paper_trading = settings["Paper Trading"]
            if not isinstance(paper_trading, bool):
                return False, "Paper Trading must be a boolean value"
        
        # Environment validation
        if "Environment" in settings:
            environment = settings["Environment"]
            if not isinstance(environment, str):
                return False, "Environment must be a string"
            if environment not in ["REAL", "SIMULATE"]:
                return False, "Environment must be 'REAL' or 'SIMULATE'"
        
        # Trading password validation (if provided)
        if "Trading Password" in settings:
            password = settings["Trading Password"]
            if not isinstance(password, str):
                return False, "Trading Password must be a string"
            if len(password) > 100:
                return False, "Trading Password too long (>100 characters)"
        
        return True, "Trading environment settings valid"

    @staticmethod
    def get_validation_summary(settings: Dict[str, Any]) -> Dict[str, Union[Dict[str, Union[bool, str]], Dict[str, Union[bool, int]]]]:
        """Get comprehensive validation summary for settings."""
        results = {}
        
        # Overall settings validation
        is_valid, message = FutuConnectionValidator.validate_settings(settings)
        results["overall"] = {"valid": is_valid, "message": message}
        
        # RSA key validation
        if "RSA Key File" in settings:
            is_valid, message = FutuConnectionValidator.validate_rsa_key(settings["RSA Key File"])
            results["rsa_key"] = {"valid": is_valid, "message": message}
        
        # Connection parameters
        if "Host" in settings and "Port" in settings:
            is_valid, message = FutuConnectionValidator.validate_connection_parameters(
                settings["Host"], settings["Port"]
            )
            results["connection"] = {"valid": is_valid, "message": message}
        
        # Market access
        is_valid, message = FutuConnectionValidator.validate_market_access(settings)
        results["market_access"] = {"valid": is_valid, "message": message}
        
        # Trading environment
        is_valid, message = FutuConnectionValidator.validate_trading_environment(settings)
        results["trading_environment"] = {"valid": is_valid, "message": message}
        
        # Summary
        all_valid = all(result.get("valid", False) for result in results.values())
        results["summary"] = {
            "all_valid": all_valid,
            "categories_checked": len(results) - 1,  # Exclude summary itself
            "validation_passed": sum(1 for result in results.values() 
                                   if result != results["summary"] and result.get("valid", False))
        }
        
        return results