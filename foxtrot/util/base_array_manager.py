"""
Base array manager for time series data.
"""

import numpy as np

from .object import BarData


class BaseArrayManager:
    """
    Base class for time series container of bar data.
    Handles core array management and data updates.
    """

    def __init__(self, size: int = 100) -> None:
        """Constructor"""
        self.count: int = 0
        self.size: int = size
        self.inited: bool = False

        self.open_array: np.ndarray = np.zeros(size)
        self.high_array: np.ndarray = np.zeros(size)
        self.low_array: np.ndarray = np.zeros(size)
        self.close_array: np.ndarray = np.zeros(size)
        self.volume_array: np.ndarray = np.zeros(size)
        self.turnover_array: np.ndarray = np.zeros(size)
        self.open_interest_array: np.ndarray = np.zeros(size)

    def update_bar(self, bar: BarData) -> None:
        """
        Update new bar data into array manager.
        """
        self.count += 1
        if not self.inited and self.count >= self.size:
            self.inited = True

        self.open_array[:-1] = self.open_array[1:]
        self.high_array[:-1] = self.high_array[1:]
        self.low_array[:-1] = self.low_array[1:]
        self.close_array[:-1] = self.close_array[1:]
        self.volume_array[:-1] = self.volume_array[1:]
        self.turnover_array[:-1] = self.turnover_array[1:]
        self.open_interest_array[:-1] = self.open_interest_array[1:]

        self.open_array[-1] = bar.open_price
        self.high_array[-1] = bar.high_price
        self.low_array[-1] = bar.low_price
        self.close_array[-1] = bar.close_price
        self.volume_array[-1] = bar.volume
        self.turnover_array[-1] = bar.turnover
        self.open_interest_array[-1] = bar.open_interest

    @property
    def open(self) -> np.ndarray:
        """Get open price time series."""
        return self.open_array

    @property
    def high(self) -> np.ndarray:
        """Get high price time series."""
        return self.high_array

    @property
    def low(self) -> np.ndarray:
        """Get low price time series."""
        return self.low_array

    @property
    def close(self) -> np.ndarray:
        """Get close price time series."""
        return self.close_array

    @property
    def volume(self) -> np.ndarray:
        """Get trading volume time series."""
        return self.volume_array

    @property
    def turnover(self) -> np.ndarray:
        """Get trading turnover time series."""
        return self.turnover_array

    @property
    def open_interest(self) -> np.ndarray:
        """Get open interest time series."""
        return self.open_interest_array