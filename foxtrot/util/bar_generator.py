"""
Bar data generator for tick-to-bar and bar aggregation.
"""

from .base_bar_generator import BaseBarGenerator
from .window_bar_generator import WindowBarGeneratorMixin


class BarGenerator(BaseBarGenerator, WindowBarGeneratorMixin):
    """
    Complete bar generator that combines:
    1. generating 1 minute bar data from tick data (from BaseBarGenerator)
    2. generating x minute bar/x hour bar data from 1 minute data (from WindowBarGeneratorMixin)
    
    Notice:
    1. for x minute bar, x must be able to divide 60: 2, 3, 5, 6, 10, 15, 20, 30
    2. for x hour bar, x can be any number
    """
    pass  # All functionality comes from base classes