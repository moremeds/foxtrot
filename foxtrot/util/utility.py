"""
General utility functions - backward compatibility module.

This module has been reorganized into several focused modules:
- file_utils.py: File and path operations
- math_utils.py: Mathematical utility functions  
- bar_generator.py: BarGenerator class for tick-to-bar conversion
- array_manager.py: ArrayManager class with indicator methods
- indicators.py: Basic technical indicators
- advanced_indicators.py: Advanced technical indicators
- decorators.py: Decorator functions
"""

# Re-export everything for backward compatibility

# From file_utils
from .file_utils import (
    TEMP_DIR,
    TRADER_DIR,
    extract_vt_symbol,
    generate_vt_symbol,
    get_file_path,
    get_folder_path,
    get_icon_path,
    load_json,
    save_json,
)

# From math_utils
from .math_utils import ceil_to, floor_to, get_digits, round_to

# From bar_generator
from .bar_generator import BarGenerator

# From array_manager
from .array_manager import ArrayManager
# Also export base classes if needed
from .base_array_manager import BaseArrayManager
from .array_manager_indicators import IndicatorMixin

# From decorators
from .decorators import virtual

# For ZoneInfo compatibility
from zoneinfo import ZoneInfo, available_timezones  # noqa

__all__ = [
    "extract_vt_symbol",
    "generate_vt_symbol",
    "get_file_path",
    "get_folder_path",
    "get_icon_path",
    "load_json",
    "save_json",
    "round_to",
    "floor_to",
    "ceil_to",
    "get_digits",
    "BarGenerator",
    "ArrayManager",
    "BaseArrayManager",
    "IndicatorMixin",
    "virtual",
    "TRADER_DIR",
    "TEMP_DIR",
    "ZoneInfo",
    "available_timezones",
]