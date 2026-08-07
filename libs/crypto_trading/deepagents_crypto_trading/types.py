"""Core types for the crypto trading system."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

import pandas as pd


class Exchange(str, Enum):
    """Supported cryptocurrency exchanges."""

    BINANCE = "binance"
    COINBASE = "coinbase"
    BYBIT = "bybit"
    OKX = "okx"
    KRAKEN = "kraken"


class ArbitrageType(str, Enum):
    """Types of arbitrage strategies."""

    TRIANGULAR = "triangular"  # Triangle arbitrage within single exchange
    CROSS_EXCHANGE = "cross_exchange"  # Price difference between exchanges
    FUTURES_SPOT = "futures_spot"  # Futures vs spot price differential


class OrderSide(str, Enum):
    """Order side."""

    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """Order type."""

    MARKET = "market"
    LIMIT = "limit"


class PositionStatus(str, Enum):
    """Position status."""

    OPEN = "open"
    CLOSED = "closed"
    LIQUIDATED = "liquidated"


class SignalStatus(str, Enum):
    """Signal status."""

    ACTIVE = "active"
    EXPIRED = "expired"
    EXECUTED = "executed"
    CANCELLED = "cancelled"


@dataclass
class ArbitrageSignal:
    """Arbitrage signal data."""

    id: str
    arbitrage_type: ArbitrageType
    trading_pairs: list[str]
    entry_price: float
    exit_price: float
    profit_percent: float
    confidence: float
    status: SignalStatus
    source: str  # websocket, rest_api, backtest
    created_at: datetime
    expires_at: Optional[datetime] = None


@dataclass
class Price:
    """Price data for a trading pair."""

    symbol: str
    price: float
    volume_24h: float
    timestamp: pd.Timestamp
    exchange: Exchange


@dataclass
class TradingPair:
    """Trading pair definition."""

    base: str  # e.g., BTC
    quote: str  # e.g., USDT
    exchange: Exchange

    @property
    def symbol(self) -> str:
        """Get the trading symbol."""
        return f"{self.base}{self.quote}"


@dataclass
class ArbitrageOpportunity:
    """Arbitrage opportunity data."""

    arbitrage_type: ArbitrageType
    trading_pairs: list[TradingPair]
    expected_profit_pct: float
    required_capital: float
    estimated_duration_seconds: int
    risk_level: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    exchanges: list[Exchange]


@dataclass
class Position:
    """Trading position."""

    id: str
    arbitrage_type: ArbitrageType
    trading_pairs: list[TradingPair]
    entry_price: float
    current_price: float
    size: float
    side: OrderSide
    status: PositionStatus
    pnl: float  # Profit/Loss
    opened_at: pd.Timestamp
    closed_at: Optional[pd.Timestamp] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


@dataclass
class RiskConfig:
    """Risk management configuration."""

    max_position_size_pct: float = 0.1  # Max 10% of capital per position
    max_daily_loss_pct: float = 0.05  # Max 5% daily loss
    max_exposure_pct: float = 0.25  # Max 25% total exposure
    stop_loss_pct: float = 0.02  # 2% stop loss
    take_profit_pct: float = 0.05  # 5% take profit
    min_confidence: float = 0.7  # Min 70% confidence
    min_profit_pct: float = 0.005  # Min 0.5% profit


@dataclass
class MarketData:
    """Market data snapshot."""

    prices: dict[str, Price]
    timestamp: pd.Timestamp
    volatility: dict[str, float]  # Symbol -> volatility

    def get_price(self, symbol: str, exchange: Exchange) -> Optional[Price]:
        """Get price for a specific symbol and exchange."""
        key = f"{exchange.value}:{symbol}"
        return self.prices.get(key)


@dataclass
class TradingConfig:
    """Trading system configuration."""

    initial_capital: float = 10000.0
    risk_config: RiskConfig = field(default_factory=RiskConfig)
    enabled_exchanges: list[Exchange] = field(default_factory=list)
    enabled_strategies: list[ArbitrageType] = field(default_factory=list)
    check_interval_seconds: int = 5
    memo0_enabled: bool = True

    def __post_init__(self) -> None:
        if not self.enabled_exchanges:
            self.enabled_exchanges = [
                Exchange.BINANCE,
                Exchange.COINBASE,
                Exchange.BYBIT,
            ]
        if not self.enabled_strategies:
            self.enabled_strategies = [
                ArbitrageType.TRIANGULAR,
                ArbitrageType.CROSS_EXCHANGE,
            ]