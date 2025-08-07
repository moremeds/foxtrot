"""Validation utilities for Futu connection settings."""

import os
from typing import Any, Dict, List, Tuple


def validate_numeric_settings(settings: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate numeric settings with ranges."""
    numeric_settings = {
        "Max Reconnect Attempts": (1, 20),
        "Reconnect Interval": (1, 300),
        "Connect Timeout": (5, 300),
        "Keep Alive Interval": (10, 3600),
        "Max Subscriptions": (1, 1000),
    }

    for setting_name, (min_val, max_val) in numeric_settings.items():
        if setting_name in settings:
            value = settings[setting_name]
            if not isinstance(value, (int, float)) or not (min_val <= value <= max_val):
                return False, f"{setting_name} must be between {min_val} and {max_val}"
    
    return True, "Numeric settings valid"


def validate_boolean_settings(settings: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate boolean settings."""
    boolean_settings = [
        "Paper Trading", "HK Market Access", "US Market Access",
        "CN Market Access", "Enable Push"
    ]

    for setting_name in boolean_settings:
        if setting_name in settings:
            value = settings[setting_name]
            if not isinstance(value, bool):
                return False, f"{setting_name} must be a boolean value"
    
    return True, "Boolean settings valid"


def validate_string_settings(settings: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate string settings with constraints."""
    string_settings = {
        "Connection ID": (0, 50),
        "Environment": ["REAL", "SIMULATE"],
        "Trading Password": (0, 100),
        "Market Data Level": ["L1", "L2"],
    }

    for setting_name, constraint in string_settings.items():
        if setting_name in settings:
            value = settings[setting_name]
            if not isinstance(value, str):
                return False, f"{setting_name} must be a string"

            if isinstance(constraint, tuple):  # Length constraint
                min_len, max_len = constraint
                if not (min_len <= len(value) <= max_len):
                    return False, f"{setting_name} length must be between {min_len} and {max_len}"
            elif isinstance(constraint, list):  # Enum constraint
                if value not in constraint:
                    return False, f"{setting_name} must be one of: {constraint}"

    return True, "String settings valid"


def validate_rsa_file_format(rsa_file: str) -> Tuple[bool, str]:
    """Validate RSA key file format and content."""
    try:
        file_stat = os.stat(rsa_file)
        if file_stat.st_size == 0:
            return False, f"RSA key file is empty: {rsa_file}"

        if file_stat.st_size > 10240:  # 10KB limit for RSA key files
            return False, f"RSA key file too large (>10KB): {rsa_file}"

        with open(rsa_file, encoding='utf-8') as f:
            content = f.read().strip()

            # Validate RSA key format markers
            has_begin_end = "-----BEGIN" in content and "-----END" in content
            has_rsa_markers = ("-----BEGIN RSA PRIVATE KEY-----" in content and 
                             "-----END RSA PRIVATE KEY-----" in content)
            
            if not (has_begin_end or has_rsa_markers):
                return False, f"Invalid RSA key format in: {rsa_file}"

            # Check for minimum key content
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            if len(lines) < 3:  # Header, content, footer minimum
                return False, f"RSA key file appears incomplete: {rsa_file}"

    except OSError as e:
        return False, f"OS error reading RSA key file {rsa_file}: {e}"
    except UnicodeDecodeError as e:
        return False, f"RSA key file encoding error {rsa_file}: {e}"
    except Exception as e:
        return False, f"Unexpected error reading RSA key file {rsa_file}: {e}"

    return True, "RSA key format validation successful"