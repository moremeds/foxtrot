"""
Advanced technical indicators using TA-Lib.
"""

import numpy as np
import talib


# Oscillators
def calculate_rsi(close: np.ndarray, n: int, array: bool = False) -> float | np.ndarray:
    """Relative Strength Index."""
    result_array: np.ndarray = talib.RSI(close, n)
    if array:
        return result_array
    return float(result_array[-1])


def calculate_macd(
    close: np.ndarray,
    fast_period: int,
    slow_period: int,
    signal_period: int,
    array: bool = False,
) -> tuple[np.ndarray, np.ndarray, np.ndarray] | tuple[float, float, float]:
    """MACD - Moving Average Convergence/Divergence."""
    macd, signal, hist = talib.MACD(close, fast_period, slow_period, signal_period)
    if array:
        return macd, signal, hist
    return macd[-1], signal[-1], hist[-1]


def calculate_willr(
    high: np.ndarray, low: np.ndarray, close: np.ndarray, n: int, array: bool = False
) -> float | np.ndarray:
    """Williams %R."""
    result_array: np.ndarray = talib.WILLR(high, low, close, n)
    if array:
        return result_array
    return float(result_array[-1])


def calculate_ultosc(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    time_period1: int = 7,
    time_period2: int = 14,
    time_period3: int = 28,
    array: bool = False,
) -> float | np.ndarray:
    """Ultimate Oscillator."""
    result_array: np.ndarray = talib.ULTOSC(
        high, low, close, time_period1, time_period2, time_period3
    )
    if array:
        return result_array
    return float(result_array[-1])


# Directional Movement
def calculate_adx(
    high: np.ndarray, low: np.ndarray, close: np.ndarray, n: int, array: bool = False
) -> float | np.ndarray:
    """Average Directional Movement Index."""
    result_array: np.ndarray = talib.ADX(high, low, close, n)
    if array:
        return result_array
    return float(result_array[-1])


def calculate_adxr(
    high: np.ndarray, low: np.ndarray, close: np.ndarray, n: int, array: bool = False
) -> float | np.ndarray:
    """Average Directional Movement Index Rating."""
    result_array: np.ndarray = talib.ADXR(high, low, close, n)
    if array:
        return result_array
    return float(result_array[-1])


def calculate_dx(
    high: np.ndarray, low: np.ndarray, close: np.ndarray, n: int, array: bool = False
) -> float | np.ndarray:
    """Directional Movement Index."""
    result_array: np.ndarray = talib.DX(high, low, close, n)
    if array:
        return result_array
    return float(result_array[-1])


def calculate_minus_di(
    high: np.ndarray, low: np.ndarray, close: np.ndarray, n: int, array: bool = False
) -> float | np.ndarray:
    """Minus Directional Indicator."""
    result_array: np.ndarray = talib.MINUS_DI(high, low, close, n)
    if array:
        return result_array
    return float(result_array[-1])


def calculate_plus_di(
    high: np.ndarray, low: np.ndarray, close: np.ndarray, n: int, array: bool = False
) -> float | np.ndarray:
    """Plus Directional Indicator."""
    result_array: np.ndarray = talib.PLUS_DI(high, low, close, n)
    if array:
        return result_array
    return float(result_array[-1])


def calculate_minus_dm(
    high: np.ndarray, low: np.ndarray, n: int, array: bool = False
) -> float | np.ndarray:
    """Minus Directional Movement."""
    result_array: np.ndarray = talib.MINUS_DM(high, low, n)
    if array:
        return result_array
    return float(result_array[-1])


def calculate_plus_dm(
    high: np.ndarray, low: np.ndarray, n: int, array: bool = False
) -> float | np.ndarray:
    """Plus Directional Movement."""
    result_array: np.ndarray = talib.PLUS_DM(high, low, n)
    if array:
        return result_array
    return float(result_array[-1])


# Channels and Bands
def calculate_boll(
    close: np.ndarray, n: int, dev: float, array: bool = False
) -> tuple[np.ndarray, np.ndarray] | tuple[float, float]:
    """Bollinger Bands."""
    mid_array: np.ndarray = talib.SMA(close, n)
    std_array: np.ndarray = talib.STDDEV(close, n, 1)

    if array:
        up_array: np.ndarray = mid_array + std_array * dev
        down_array: np.ndarray = mid_array - std_array * dev
        return up_array, down_array
    mid: float = mid_array[-1]
    std: float = std_array[-1]
    up: float = mid + std * dev
    down: float = mid - std * dev
    return up, down


def calculate_keltner(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    n: int,
    dev: float,
    array: bool = False,
) -> tuple[np.ndarray, np.ndarray] | tuple[float, float]:
    """Keltner Channel."""
    mid_array: np.ndarray = talib.SMA(close, n)
    atr_array: np.ndarray = talib.ATR(high, low, close, n)

    if array:
        up_array: np.ndarray = mid_array + atr_array * dev
        down_array: np.ndarray = mid_array - atr_array * dev
        return up_array, down_array
    mid: float = mid_array[-1]
    atr: float = atr_array[-1]
    up: float = mid + atr * dev
    down: float = mid - atr * dev
    return up, down


def calculate_donchian(
    high: np.ndarray, low: np.ndarray, n: int, array: bool = False
) -> tuple[np.ndarray, np.ndarray] | tuple[float, float]:
    """Donchian Channel."""
    up: np.ndarray = talib.MAX(high, n)
    down: np.ndarray = talib.MIN(low, n)

    if array:
        return up, down
    return up[-1], down[-1]


# Aroon Indicators
def calculate_aroon(
    high: np.ndarray, low: np.ndarray, n: int, array: bool = False
) -> tuple[np.ndarray, np.ndarray] | tuple[float, float]:
    """Aroon indicator."""
    aroon_down, aroon_up = talib.AROON(high, low, n)

    if array:
        return aroon_up, aroon_down
    return aroon_up[-1], aroon_down[-1]


def calculate_aroonosc(
    high: np.ndarray, low: np.ndarray, n: int, array: bool = False
) -> float | np.ndarray:
    """Aroon Oscillator."""
    result_array: np.ndarray = talib.AROONOSC(high, low, n)

    if array:
        return result_array
    return float(result_array[-1])


# Other
def calculate_trange(
    high: np.ndarray, low: np.ndarray, close: np.ndarray, array: bool = False
) -> float | np.ndarray:
    """True Range."""
    result_array: np.ndarray = talib.TRANGE(high, low, close)
    if array:
        return result_array
    return float(result_array[-1])


def calculate_sar(
    high: np.ndarray,
    low: np.ndarray,
    acceleration: float,
    maximum: float,
    array: bool = False,
) -> float | np.ndarray:
    """Parabolic SAR."""
    result_array: np.ndarray = talib.SAR(high, low, acceleration, maximum)
    if array:
        return result_array
    return float(result_array[-1])