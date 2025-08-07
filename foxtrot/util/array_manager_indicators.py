"""
Indicator methods for ArrayManager class.
This module provides all indicator calculation methods as a mixin.
"""

import numpy as np

from .indicators import (
    calculate_apo,
    calculate_atr,
    calculate_cci,
    calculate_cmo,
    calculate_ema,
    calculate_kama,
    calculate_mom,
    calculate_natr,
    calculate_obv,
    calculate_ppo,
    calculate_roc,
    calculate_rocp,
    calculate_rocr,
    calculate_rocr_100,
    calculate_sma,
    calculate_std,
    calculate_trix,
    calculate_var,
    calculate_wma,
)
from .advanced_indicators import (
    calculate_adx,
    calculate_adxr,
    calculate_aroon,
    calculate_aroonosc,
    calculate_boll,
    calculate_donchian,
    calculate_dx,
    calculate_keltner,
    calculate_macd,
    calculate_minus_di,
    calculate_minus_dm,
    calculate_plus_di,
    calculate_plus_dm,
    calculate_rsi,
    calculate_sar,
    calculate_trange,
    calculate_ultosc,
    calculate_willr,
)


class IndicatorMixin:
    """Mixin class providing indicator calculation methods."""
    
    # These properties should be provided by the base class
    close: np.ndarray
    high: np.ndarray
    low: np.ndarray
    volume: np.ndarray

    # Moving Averages
    def sma(self, n: int, array: bool = False) -> float | np.ndarray:
        """Simple moving average."""
        return calculate_sma(self.close, n, array)

    def ema(self, n: int, array: bool = False) -> float | np.ndarray:
        """Exponential moving average."""
        return calculate_ema(self.close, n, array)

    def kama(self, n: int, array: bool = False) -> float | np.ndarray:
        """Kaufman Adaptive Moving Average."""
        return calculate_kama(self.close, n, array)

    def wma(self, n: int, array: bool = False) -> float | np.ndarray:
        """Weighted Moving Average."""
        return calculate_wma(self.close, n, array)

    # Momentum Indicators
    def apo(
        self,
        fast_period: int,
        slow_period: int,
        matype: int = 0,
        array: bool = False,
    ) -> float | np.ndarray:
        """Absolute Price Oscillator."""
        return calculate_apo(self.close, fast_period, slow_period, matype, array)

    def cmo(self, n: int, array: bool = False) -> float | np.ndarray:
        """Chande Momentum Oscillator."""
        return calculate_cmo(self.close, n, array)

    def mom(self, n: int, array: bool = False) -> float | np.ndarray:
        """Momentum."""
        return calculate_mom(self.close, n, array)

    def ppo(
        self,
        fast_period: int,
        slow_period: int,
        matype: int = 0,
        array: bool = False,
    ) -> float | np.ndarray:
        """Percentage Price Oscillator."""
        return calculate_ppo(self.close, fast_period, slow_period, matype, array)

    def roc(self, n: int, array: bool = False) -> float | np.ndarray:
        """Rate of Change."""
        return calculate_roc(self.close, n, array)

    def rocr(self, n: int, array: bool = False) -> float | np.ndarray:
        """Rate of Change Ratio."""
        return calculate_rocr(self.close, n, array)

    def rocp(self, n: int, array: bool = False) -> float | np.ndarray:
        """Rate of Change Percentage."""
        return calculate_rocp(self.close, n, array)

    def rocr_100(self, n: int, array: bool = False) -> float | np.ndarray:
        """Rate of Change Ratio 100 scale."""
        return calculate_rocr_100(self.close, n, array)

    def trix(self, n: int, array: bool = False) -> float | np.ndarray:
        """TRIX."""
        return calculate_trix(self.close, n, array)

    # Statistical Functions
    def std(self, n: int, nbdev: int = 1, array: bool = False) -> float | np.ndarray:
        """Standard deviation."""
        return calculate_std(self.close, n, nbdev, array)

    def var(self, n: int, nbdev: int = 1, array: bool = False) -> float | np.ndarray:
        """Variance."""
        return calculate_var(self.close, n, nbdev, array)

    # Volume Indicators
    def obv(self, array: bool = False) -> float | np.ndarray:
        """On Balance Volume."""
        return calculate_obv(self.close, self.volume, array)

    # Volatility Indicators
    def cci(self, n: int, array: bool = False) -> float | np.ndarray:
        """Commodity Channel Index."""
        return calculate_cci(self.high, self.low, self.close, n, array)

    def atr(self, n: int, array: bool = False) -> float | np.ndarray:
        """Average True Range."""
        return calculate_atr(self.high, self.low, self.close, n, array)

    def natr(self, n: int, array: bool = False) -> float | np.ndarray:
        """Normalized Average True Range."""
        return calculate_natr(self.high, self.low, self.close, n, array)

    # Oscillators
    def rsi(self, n: int, array: bool = False) -> float | np.ndarray:
        """Relative Strength Index."""
        return calculate_rsi(self.close, n, array)

    def macd(
        self, fast_period: int, slow_period: int, signal_period: int, array: bool = False
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray] | tuple[float, float, float]:
        """MACD."""
        return calculate_macd(self.close, fast_period, slow_period, signal_period, array)

    def willr(self, n: int, array: bool = False) -> float | np.ndarray:
        """Williams %R."""
        return calculate_willr(self.high, self.low, self.close, n, array)

    def ultosc(
        self,
        time_period1: int = 7,
        time_period2: int = 14,
        time_period3: int = 28,
        array: bool = False,
    ) -> float | np.ndarray:
        """Ultimate Oscillator."""
        return calculate_ultosc(
            self.high, self.low, self.close, time_period1, time_period2, time_period3, array
        )

    # Directional Movement
    def adx(self, n: int, array: bool = False) -> float | np.ndarray:
        """Average Directional Movement Index."""
        return calculate_adx(self.high, self.low, self.close, n, array)

    def adxr(self, n: int, array: bool = False) -> float | np.ndarray:
        """Average Directional Movement Index Rating."""
        return calculate_adxr(self.high, self.low, self.close, n, array)

    def dx(self, n: int, array: bool = False) -> float | np.ndarray:
        """Directional Movement Index."""
        return calculate_dx(self.high, self.low, self.close, n, array)

    def minus_di(self, n: int, array: bool = False) -> float | np.ndarray:
        """Minus Directional Indicator."""
        return calculate_minus_di(self.high, self.low, self.close, n, array)

    def plus_di(self, n: int, array: bool = False) -> float | np.ndarray:
        """Plus Directional Indicator."""
        return calculate_plus_di(self.high, self.low, self.close, n, array)

    def minus_dm(self, n: int, array: bool = False) -> float | np.ndarray:
        """Minus Directional Movement."""
        return calculate_minus_dm(self.high, self.low, n, array)

    def plus_dm(self, n: int, array: bool = False) -> float | np.ndarray:
        """Plus Directional Movement."""
        return calculate_plus_dm(self.high, self.low, n, array)

    # Other
    def trange(self, array: bool = False) -> float | np.ndarray:
        """True Range."""
        return calculate_trange(self.high, self.low, self.close, array)

    # Channels and Bands
    def boll(
        self, n: int, dev: float, array: bool = False
    ) -> tuple[np.ndarray, np.ndarray] | tuple[float, float]:
        """Bollinger Bands."""
        return calculate_boll(self.close, n, dev, array)

    def keltner(
        self, n: int, dev: float, array: bool = False
    ) -> tuple[np.ndarray, np.ndarray] | tuple[float, float]:
        """Keltner Channel."""
        return calculate_keltner(self.high, self.low, self.close, n, dev, array)

    def donchian(
        self, n: int, array: bool = False
    ) -> tuple[np.ndarray, np.ndarray] | tuple[float, float]:
        """Donchian Channel."""
        return calculate_donchian(self.high, self.low, n, array)

    def aroon(
        self, n: int, array: bool = False
    ) -> tuple[np.ndarray, np.ndarray] | tuple[float, float]:
        """Aroon indicator."""
        return calculate_aroon(self.high, self.low, n, array)

    def aroonosc(self, n: int, array: bool = False) -> float | np.ndarray:
        """Aroon Oscillator."""
        return calculate_aroonosc(self.high, self.low, n, array)

    def sar(self, acceleration: float, maximum: float, array: bool = False) -> float | np.ndarray:
        """Parabolic SAR."""
        return calculate_sar(self.high, self.low, acceleration, maximum, array)