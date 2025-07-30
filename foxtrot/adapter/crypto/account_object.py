"""
Basic data structure used for crypto account in the trading platform.
"""

from dataclasses import dataclass

from foxtrot.util.object import AccountData


@dataclass
class CryptoBalance:
    asset: str
    free: str
    locked: str


@dataclass
class CryptoUserAsset:
    asset: str
    borrowed: str
    free: str
    interest: str
    locked: str
    netAsset: str


@dataclass
class CryptoIsolatedAsset:
    asset: str
    borrowEnabled: bool
    borrowed: str
    free: str
    interest: str
    locked: str
    netAsset: str
    netAssetOfBtc: str
    repayEnabled: bool
    totalAsset: str


@dataclass
class CryptoIsolatedSymbol:
    baseAsset: CryptoIsolatedAsset
    quoteAsset: CryptoIsolatedAsset
    symbol: str
    isolatedCreated: bool
    marginLevel: str
    marginLevelStatus: str
    marginRatio: str
    indexPrice: str
    liquidatePrice: str
    liquidateRate: str
    tradeEnabled: bool
    enabled: bool


@dataclass
class CryptoFuturesAsset:
    asset: str
    walletBalance: str
    unrealizedProfit: str
    marginBalance: str
    maintMargin: str
    initialMargin: str
    positionInitialMargin: str
    openOrderInitialMargin: str
    maxWithdrawAmount: str
    crossWalletBalance: str
    crossUnPnl: str
    availableBalance: str


@dataclass
class CryptoFuturesPosition:
    symbol: str
    initialMargin: str
    maintMargin: str
    unrealizedProfit: str
    positionInitialMargin: str
    openOrderInitialMargin: str
    leverage: str
    isolated: bool
    entryPrice: str
    maxNotional: str
    positionSide: str


@dataclass
class CryptoPayBalance:
    asset: str
    free: str
    locked: str
    freeze: str
    withdrawing: str


@dataclass
class CryptoPortfolioMargin:
    asset: str
    totalWalletBalance: str
    crossMarginAsset: str
    crossMarginBorrowed: str
    crossMarginFree: str
    crossMarginInterest: str
    crossMarginLocked: str
    umWalletBalance: str
    umUnrealizedPNL: str
    cmWalletBalance: str
    cmUnrealizedPNL: str
    updateTime: int
    negativeBalance: str


@dataclass
class CryptoAccountData(AccountData):
    """
    Crypto account data contains detailed information for various account types.
    """

    makerCommission: int | None = None
    takerCommission: int | None = None
    buyerCommission: int | None = None
    sellerCommission: int | None = None
    canTrade: bool | None = None
    canWithdraw: bool | None = None
    canDeposit: bool | None = None
    updateTime: int | None = None
    accountType: str | None = None
    balances: list[CryptoBalance] | None = None
    borrowEnabled: bool | None = None
    marginLevel: str | None = None
    totalAssetOfBtc: str | None = None
    totalLiabilityOfBtc: str | None = None
    totalNetAssetOfBtc: str | None = None
    tradeEnabled: bool | None = None
    transferEnabled: bool | None = None
    userAssets: list[CryptoUserAsset] | None = None
    isolated_assets: list[CryptoIsolatedSymbol] | None = None
    feeTier: int | None = None
    totalInitialMargin: str | None = None
    totalMaintMargin: str | None = None
    totalWalletBalance: str | None = None
    totalUnrealizedProfit: str | None = None
    totalMarginBalance: str | None = None
    totalPositionInitialMargin: str | None = None
    totalOpenOrderInitialMargin: str | None = None
    totalCrossWalletBalance: str | None = None
    totalCrossUnPnl: str | None = None
    availableBalance: str | None = None
    maxWithdrawAmount: str | None = None
    futures_assets: list[CryptoFuturesAsset] | None = None
    futures_positions: list[CryptoFuturesPosition] | None = None
    pay_balances: list[CryptoPayBalance] | None = None
    portfolio_margin: list[CryptoPortfolioMargin] | None = None
