"""
Technical indicator calculations using TA-Lib.
This module provides basic technical indicators.
"""

import numpy as np
import talib


# Moving Averages
def calculate_sma(close: np.ndarray, n: int, array: bool = False) -> float | np.ndarray:
    """Simple moving average."""
    result_array: np.ndarray = talib.SMA(close, n)
    if array:
        return result_array
    return float(result_array[-1])


def calculate_ema(close: np.ndarray, n: int, array: bool = False) -> float | np.ndarray:
    """Exponential moving average."""
    result_array: np.ndarray = talib.EMA(close, n)
    if array:
        return result_array
    return float(result_array[-1])


def calculate_kama(close: np.ndarray, n: int, array: bool = False) -> float | np.ndarray:
    """Kaufman Adaptive Moving Average."""
    result_array: np.ndarray = talib.KAMA(close, n)
    if array:
        return result_array
    return float(result_array[-1])


def calculate_wma(close: np.ndarray, n: int, array: bool = False) -> float | np.ndarray:
    """Weighted Moving Average."""
    result_array: np.ndarray = talib.WMA(close, n)
    if array:
        return result_array
    return float(result_array[-1])


# Momentum Indicators
def calculate_apo(
    close: np.ndarray,
    fast_period: int,
    slow_period: int,
    matype: int = 0,
    array: bool = False,
) -> float | np.ndarray:
    """Absolute Price Oscillator."""
    result_array: np.ndarray = talib.APO(close, fast_period, slow_period, matype)  # type: ignore
    if array:
        return result_array
    return float(result_array[-1])


def calculate_cmo(close: np.ndarray, n: int, array: bool = False) -> float | np.ndarray:
    """Chande Momentum Oscillator."""
    result_array: np.ndarray = talib.CMO(close, n)
    if array:
        return result_array
    return float(result_array[-1])


def calculate_mom(close: np.ndarray, n: int, array: bool = False) -> float | np.ndarray:
    """Momentum."""
    result_array: np.ndarray = talib.MOM(close, n)
    if array:
        return result_array
    return float(result_array[-1])


def calculate_ppo(
    close: np.ndarray,
    fast_period: int,
    slow_period: int,
    matype: int = 0,
    array: bool = False,
) -> float | np.ndarray:
    """Percentage Price Oscillator."""
    result_array: np.ndarray = talib.PPO(close, fast_period, slow_period, matype)  # type: ignore
    if array:
        return result_array
    return float(result_array[-1])


def calculate_roc(close: np.ndarray, n: int, array: bool = False) -> float | np.ndarray:
    """Rate of Change."""
    result_array: np.ndarray = talib.ROC(close, n)
    if array:
        return result_array
    return float(result_array[-1])


def calculate_rocr(close: np.ndarray, n: int, array: bool = False) -> float | np.ndarray:
    """Rate of Change Ratio."""
    result_array: np.ndarray = talib.ROCR(close, n)
    if array:
        return result_array
    return float(result_array[-1])


def calculate_rocp(close: np.ndarray, n: int, array: bool = False) -> float | np.ndarray:
    """Rate of Change Percentage."""
    result_array: np.ndarray = talib.ROCP(close, n)
    if array:
        return result_array
    return float(result_array[-1])


def calculate_rocr_100(close: np.ndarray, n: int, array: bool = False) -> float | np.ndarray:
    """Rate of Change Ratio 100 scale."""
    result_array: np.ndarray = talib.ROCR100(close, n)
    if array:
        return result_array
    return float(result_array[-1])


def calculate_trix(close: np.ndarray, n: int, array: bool = False) -> float | np.ndarray:
    """1-day Rate-Of-Change (ROC) of a Triple Smooth EMA."""
    result_array: np.ndarray = talib.TRIX(close, n)
    if array:
        return result_array
    return float(result_array[-1])


# Statistical Functions
def calculate_std(close: np.ndarray, n: int, nbdev: int = 1, array: bool = False) -> float | np.ndarray:
    """Standard deviation."""
    result_array: np.ndarray = talib.STDDEV(close, n, nbdev)
    if array:
        return result_array
    return float(result_array[-1])


def calculate_var(close: np.ndarray, n: int, nbdev: int = 1, array: bool = False) -> float | np.ndarray:
    """Variance."""
    result_array: np.ndarray = talib.VAR(close, n, nbdev)
    if array:
        return result_array
    return float(result_array[-1])


# Volume Indicators
def calculate_obv(close: np.ndarray, volume: np.ndarray, array: bool = False) -> float | np.ndarray:
    """On Balance Volume."""
    result_array: np.ndarray = talib.OBV(close, volume)
    if array:
        return result_array
    return float(result_array[-1])


# Volatility Indicators
def calculate_atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, n: int, array: bool = False) -> float | np.ndarray:
    """Average True Range."""
    result_array: np.ndarray = talib.ATR(high, low, close, n)
    if array:
        return result_array
    return float(result_array[-1])


def calculate_natr(high: np.ndarray, low: np.ndarray, close: np.ndarray, n: int, array: bool = False) -> float | np.ndarray:
    """Normalized Average True Range."""
    result_array: np.ndarray = talib.NATR(high, low, close, n)
    if array:
        return result_array
    return float(result_array[-1])


def calculate_cci(high: np.ndarray, low: np.ndarray, close: np.ndarray, n: int, array: bool = False) -> float | np.ndarray:
    """Commodity Channel Index."""
    result_array: np.ndarray = talib.CCI(high, low, close, n)
    if array:
        return result_array
    return float(result_array[-1])