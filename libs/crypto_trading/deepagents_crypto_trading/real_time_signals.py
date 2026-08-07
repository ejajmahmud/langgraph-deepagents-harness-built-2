"""Real-time signal generator using WebSocket data."""

import asyncio
from datetime import datetime
from enum import Enum
from typing import Optional

import pandas as pd

from deepagents_crypto_trading.types import (
    ArbitrageSignal,
    ArbitrageType,
    Exchange,
    SignalStatus,
)


class SignalSource(Enum):
    """Source of signal data."""

    WEBSOCKET = "websocket"
    REST_API = "rest_api"
    BACKTEST = "backtest"


class RealTimeSignalGenerator:
    """Real-time signal generator using WebSocket streams.

    Generates arbitrage signals from real-time price data
    with low latency for fast execution.
    """

    def __init__(
        self,
        min_profit_threshold: float = 0.001,
        min_volume_24h: float = 1000000,
        signal_timeout_seconds: int = 60,
    ) -> None:
        """Initialize real-time signal generator.

        Args:
            min_profit_threshold: Minimum profit percentage (e.g., 0.001 = 0.1%).
            min_volume_24h: Minimum 24h volume to consider.
            signal_timeout_seconds: Signal validity timeout.
        """
        self.min_profit_threshold = min_profit_threshold
        self.min_volume_24h = min_volume_24h
        self.signal_timeout_seconds = signal_timeout_seconds

        # Price cache for signal generation
        self._price_cache: dict[str, dict[str, dict]] = {}
        self._last_update: Optional[datetime] = None
        self._active_signals: list[ArbitrageSignal] = []

    async def update_price(
        self,
        exchange: Exchange,
        symbol: str,
        price: float,
        volume_24h: float,
    ) -> None:
        """Update price from WebSocket.

        Args:
            exchange: The exchange.
            symbol: Trading symbol.
            price: Current price.
            volume_24h: 24h volume.
        """
        if exchange.value not in self._price_cache:
            self._price_cache[exchange.value] = {}

        self._price_cache[exchange.value][symbol] = {
            "price": price,
            "volume_24h": volume_24h,
            "timestamp": datetime.now(),
        }
        self._last_update = datetime.now()

    def _calculate_arbitrage_opportunity(
        self,
        buy_exchange: Exchange,
        sell_exchange: Exchange,
        symbol: str,
    ) -> Optional[ArbitrageSignal]:
        """Calculate arbitrage opportunity between exchanges.

        Args:
            buy_exchange: Exchange to buy on.
            sell_exchange: Exchange to sell on.
            symbol: Trading symbol.

        Returns:
            Arbitrage signal if opportunity found.
        """
        prices = self._price_cache

        # Get prices from both exchanges
        buy_data = prices.get(buy_exchange.value, {}).get(symbol, {})
        sell_data = prices.get(sell_exchange.value, {}).get(symbol, {})

        if not buy_data or not sell_data:
            return None

        buy_price = buy_data.get("price", 0)
        sell_price = sell_data.get("price", 0)
        volume = sell_data.get("volume_24h", 0)

        # Check volume threshold
        if volume < self.min_volume_24h:
            return None

        # Calculate spread
        if buy_price <= 0:
            return None

        spread = (sell_price - buy_price) / buy_price

        # Check profitability
        if spread >= self.min_profit_threshold:
            return ArbitrageSignal(
                id=f"arb_{buy_exchange.value}_{sell_exchange.value}_{symbol}",
                arbitrage_type=ArbitrageType.CROSS_EXCHANGE,
                trading_pairs=[symbol],
                entry_price=buy_price,
                exit_price=sell_price,
                profit_percent=spread * 100,
                confidence=min(spread * 10, 1.0),
                status=SignalStatus.ACTIVE,
                source=SignalSource.WEBSOCKET.value,
                created_at=datetime.now(),
                expires_at=datetime.now(),
            )

        return None

    async def scan_cross_exchange_arbitrage(
        self,
        symbol: str,
        exchanges: list[Exchange],
    ) -> list[ArbitrageSignal]:
        """Scan for cross-exchange arbitrage opportunities.

        Args:
            symbol: Trading symbol.
            exchanges: List of exchanges to scan.

        Returns:
            List of arbitrage signals.
        """
        signals = []
        now = datetime.now()

        # Check all exchange pairs
        for i, buy_exchange in enumerate(exchanges):
            for sell_exchange in exchanges[i + 1:]:
                signal = self._calculate_arbitrage_opportunity(
                    buy_exchange, sell_exchange, symbol
                )
                if signal:
                    # Check expiration
                    if signal.expires_at and signal.expires_at > now:
                        signals.append(signal)

        # Sort by profit (highest first)
        signals.sort(key=lambda s: s.profit_percent, reverse=True)

        # Update active signals
        self._active_signals = signals

        return signals

    def get_active_signals(self) -> list[ArbitrageSignal]:
        """Get currently active signals.

        Returns:
            List of active signals.
        """
        now = datetime.now()
        valid_signals = [
            s for s in self._active_signals
            if s.expires_at and s.expires_at > now
        ]
        return valid_signals

    def get_price_data(self) -> dict[str, dict[str, dict]]:
        """Get cached price data.

        Returns:
            Dictionary of exchange to price data.
        """
        return self._price_cache.copy()

    def is_stale(self, max_age_seconds: int = 30) -> bool:
        """Check if price data is stale.

        Args:
            max_age_seconds: Maximum age in seconds.

        Returns:
            True if data is stale.
        """
        if self._last_update is None:
            return True

        age = (datetime.now() - self._last_update).total_seconds()
        return age > max_age_seconds


class SignalFilter:
    """Filter for arbitrage signals."""

    def __init__(
        self,
        min_profit: float = 0.05,
        min_confidence: float = 0.5,
        max_age_seconds: int = 60,
    ) -> None:
        """Initialize signal filter.

        Args:
            min_profit: Minimum profit percentage.
            min_confidence: Minimum confidence score.
            max_age_seconds: Maximum signal age.
        """
        self.min_profit = min_profit
        self.min_confidence = min_confidence
        self.max_age_seconds = max_age_seconds

    def filter_signals(
        self, signals: list[ArbitrageSignal]
    ) -> list[ArbitrageSignal]:
        """Filter signals by criteria.

        Args:
            signals: List of signals to filter.

        Returns:
            Filtered signals.
        """
        now = datetime.now()
        filtered = []

        for signal in signals:
            # Check age
            if signal.created_at:
                age = (now - signal.created_at).total_seconds()
                if age > self.max_age_seconds:
                    continue

            # Check profit
            if signal.profit_percent < self.min_profit:
                continue

            # Check confidence
            if signal.confidence < self.min_confidence:
                continue

            filtered.append(signal)

        return filtered


class SignalAggregator:
    """Aggregator for multiple signal sources."""

    def __init__(self) -> None:
        """Initialize signal aggregator."""
        self._generators: dict[str, RealTimeSignalGenerator] = {}

    def add_generator(
        self, name: str, generator: RealTimeSignalGenerator
    ) -> None:
        """Add a signal generator.

        Args:
            name: Generator name.
            generator: Generator instance.
        """
        self._generators[name] = generator

    async def get_all_signals(self) -> list[ArbitrageSignal]:
        """Get signals from all generators.

        Returns:
            Combined list of signals.
        """
        signals = []
        for generator in self._generators.values():
            signals.extend(generator.get_active_signals())

        # Sort by profit
        signals.sort(key=lambda s: s.profit_percent, reverse=True)
        return signals

    def get_best_signal(self) -> Optional[ArbitrageSignal]:
        """Get the best signal across all generators.

        Returns:
            Best signal or None.
        """
        signals = asyncio.get_event_loop().run_until_complete(
            self.get_all_signals()
        )
        return signals[0] if signals else None