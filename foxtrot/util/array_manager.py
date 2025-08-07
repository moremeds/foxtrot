"""
Array manager for time series data and technical indicators.
"""

from .base_array_manager import BaseArrayManager
from .array_manager_indicators import IndicatorMixin


class ArrayManager(BaseArrayManager, IndicatorMixin):
    """
    Array manager that combines:
    1. time series container of bar data (from BaseArrayManager)
    2. calculating technical indicator values (from IndicatorMixin)
    
    This class provides a complete interface for managing bar data
    and calculating technical indicators on that data.
    """
    pass  # All functionality comes from base classes