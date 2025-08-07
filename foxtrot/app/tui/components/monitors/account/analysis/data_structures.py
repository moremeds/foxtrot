"""
Account analysis data structures.

Defines the data classes and structures used for account
and portfolio analysis results.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class AccountSummary:
    """Summary data structure for account analysis."""
    account_id: str
    currency: str
    gateway: str
    current_balance: float
    available_balance: float
    frozen_balance: float
    net_pnl: float
    margin_used: float
    last_updated: datetime
    risk_level: str
    performance_score: float


@dataclass
class PortfolioSummary:
    """Portfolio-level summary data structure."""
    total_accounts: int
    total_balance: float
    total_available: float
    total_equity: float
    total_pnl: float
    currencies: List[str]
    gateways: List[str]
    risk_level: str
    diversification_score: float
    performance_metrics: Dict[str, float]


@dataclass
class CurrencyBreakdown:
    """Currency-specific breakdown data."""
    balance: float
    available: float
    frozen: float
    pnl: float
    account_count: int
    avg_balance: float
    weight: float


@dataclass
class GatewayBreakdown:
    """Gateway-specific breakdown data."""
    balance: float
    available: float
    pnl: float
    account_count: int
    currency_count: int
    avg_balance: float
    weight: float


@dataclass
class RiskMetrics:
    """Risk assessment metrics for an account."""
    available_ratio: float
    margin_ratio: float
    pnl_impact: float
    risk_level: str
    risk_score: float


@dataclass
class PerformanceMetrics:
    """Performance metrics for accounts or portfolios."""
    return_on_equity: float
    return_on_equity_pct: float
    risk_adjusted_return: float
    profit_factor: float
    performance_score: float


@dataclass
class HistoricalEntry:
    """Historical data point for account tracking."""
    timestamp: datetime
    balance: float
    available: float
    frozen: float
    pnl: float
    margin: float