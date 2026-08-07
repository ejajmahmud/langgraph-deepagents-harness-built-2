"""Exchange API connectors for real-time market data."""

import asyncio
import os
from abc import ABC, abstractmethod
from typing import Optional

import pandas as pd

from deepagents_crypto_trading.types import Exchange, Price


class ExchangeConnector(ABC):
    """Base class for exchange connectors."""

    def __init__(self, exchange: Exchange) -> None:
        """Initialize exchange connector.

        Args:
            exchange: The exchange to connect to.
        """
        self.exchange = exchange
        self._running = False

    @abstractmethod
    async def fetch_prices(self, symbols: list[str]) -> dict[str, Price]:
        """Fetch current prices for symbols.

        Args:
            symbols: List of trading pair symbols (e.g., ['BTCUSDT', 'ETHUSDT']).

        Returns:
            Dictionary mapping symbol to Price.
        """
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if exchange API is available.

        Returns:
            True if exchange is accessible.
        """
        ...

    async def start(self) -> None:
        """Start the connector."""
        self._running = True

    async def stop(self) -> None:
        """Stop the connector."""
        self._running = False


class BinanceConnector(ExchangeConnector):
    """Binance exchange connector.

    Provides real-time price data from Binance API.
    Uses public endpoints (no authentication required for prices).
    """

    def __init__(self) -> None:
        """Initialize Binance connector."""
        super().__init__(Exchange.BINANCE)
        self._base_url = "https://api.binance.com"
        self._rate_limit_calls = 0
        self._rate_limit_reset = None

    async def fetch_prices(self, symbols: list[str]) -> dict[str, Price]:
        """Fetch current prices from Binance.

        Args:
            symbols: List of trading pair symbols.

        Returns:
            Dictionary mapping symbol to Price.
        """
        import httpx

        prices: dict[str, Price] = {}
        now = pd.Timestamp.now()

        # Fetch all prices in batch (more efficient)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self._base_url}/api/v3/ticker/24hr"
                )
                if response.status_code != 200:
                    return await self._fetch_fallback_prices(symbols, now)

                data = response.json()

                # Filter to requested symbols
                for item in data:
                    symbol = item.get("symbol", "")
                    if symbol in symbols:
                        prices[symbol] = Price(
                            symbol=symbol,
                            price=float(item.get("lastPrice", 0)),
                            volume_24h=float(item.get("volume", 0)),
                            timestamp=now,
                            exchange=self.exchange,
                        )

                # Fill missing with fallback
                missing = set(symbols) - set(prices.keys())
                if missing:
                    fallback = await self._fetch_fallback_prices(list(missing), now)
                    prices.update(fallback)

        except Exception:
            return await self._fetch_fallback_prices(symbols, now)

        return prices

    async def _fetch_fallback_prices(
        self, symbols: list[str], timestamp: pd.Timestamp
    ) -> dict[str, Price]:
        """Fetch prices using individual ticker endpoint (fallback).

        Args:
            symbols: List of symbols.
            timestamp: Current timestamp.

        Returns:
            Dictionary of prices.
        """
        import httpx

        prices: dict[str, Price] = {}

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                for symbol in symbols:
                    try:
                        response = await client.get(
                            f"{self._base_url}/api/v3/ticker/price",
                            params={"symbol": symbol},
                        )
                        if response.status_code == 200:
                            data = response.json()
                            price_value = float(data.get("price", 0))
                            if price_value > 0:
                                prices[symbol] = Price(
                                    symbol=symbol,
                                    price=price_value,
                                    volume_24h=0.0,
                                    timestamp=timestamp,
                                    exchange=self.exchange,
                                )
                    except Exception:
                        continue
        except Exception:
            pass

        return prices

    async def is_available(self) -> bool:
        """Check if Binance API is available.

        Returns:
            True if accessible.
        """
        import httpx

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self._base_url}/api/v3/ping")
                return response.status_code == 200
        except Exception:
            return False


class CoinbaseConnector(ExchangeConnector):
    """Coinbase exchange connector.

    Provides real-time price data from Coinbase API.
    """

    def __init__(self) -> None:
        """Initialize Coinbase connector."""
        super().__init__(Exchange.COINBASE)
        self._base_url = "https://api.coinbase.com"

    async def fetch_prices(self, symbols: list[str]) -> dict[str, Price]:
        """Fetch current prices from Coinbase.

        Args:
            symbols: List of trading pair symbols.

        Returns:
            Dictionary mapping symbol to Price.
        """
        import httpx

        prices: dict[str, Price] = {}
        now = pd.Timestamp.now()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                for symbol in symbols:
                    try:
                        # Convert BTCUSDT to BTC-USDT for Coinbase
                        pair = symbol.replace("USDT", "-USDT")
                        response = await client.get(
                            f"{self._base_url}/v2/prices/{pair}/spot"
                        )
                        if response.status_code == 200:
                            data = response.json()
                            price_value = float(
                                data.get("data", {}).get("amount", 0)
                            )
                            if price_value > 0:
                                prices[symbol] = Price(
                                    symbol=symbol,
                                    price=price_value,
                                    volume_24h=0.0,
                                    timestamp=now,
                                    exchange=self.exchange,
                                )
                    except Exception:
                        continue
        except Exception:
            pass

        return prices

    async def is_available(self) -> bool:
        """Check if Coinbase API is available.

        Returns:
            True if accessible.
        """
        import httpx

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self._base_url}/v2/time")
                return response.status_code == 200
        except Exception:
            return False


class MockConnector(ExchangeConnector):
    """Mock connector for testing and fallback.

    Generates realistic price movements based on base prices.
    """

    def __init__(self, exchange: Exchange) -> None:
        """Initialize mock connector.

        Args:
            exchange: The exchange to mock.
        """
        super().__init__(exchange)
        self._base_prices = {
            "BTCUSDT": 67500.0,
            "ETHUSDT": 3450.0,
            "SOLUSDT": 145.0,
            "DOGEUSDT": 0.15,
            "BNBUSDT": 580.0,
            "XRPUSDT": 0.52,
            "ADAUSDT": 0.45,
        }

    async def fetch_prices(self, symbols: list[str]) -> dict[str, Price]:
        """Fetch mock prices with slight variations.

        Args:
            symbols: List of trading pair symbols.

        Returns:
            Dictionary of prices.
        """
        import hashlib

        prices: dict[str, Price] = {}
        now = pd.Timestamp.now()

        for symbol in symbols:
            base_price = self._base_prices.get(symbol, 100.0)

            # Add slight variation based on exchange and time
            variation = (
                hash(f"{self.exchange.value}{symbol}{now.second}") % 100
            ) / 10000
            price = base_price * (1 + variation)

            prices[symbol] = Price(
                symbol=symbol,
                price=price,
                volume_24h=base_price * 10000,  # Mock volume
                timestamp=now,
                exchange=self.exchange,
            )

        return prices

    async def is_available(self) -> bool:
        """Always available for mock.

        Returns:
            True.
        """
        return True


class ExchangeConnectorManager:
    """Manages multiple exchange connectors with circuit breaker."""

    def __init__(self) -> None:
        """Initialize connector manager."""
        self._connectors: dict[Exchange, ExchangeConnector] = {}
        self._circuit_breakers: dict[Exchange, CircuitBreaker] = {}
        self._initialize_connectors()

    def _initialize_connectors(self) -> None:
        """Initialize all exchange connectors."""
        # Add real connectors
        self._connectors[Exchange.BINANCE] = BinanceConnector()
        self._connectors[Exchange.COINBASE] = CoinbaseConnector()

        # Add mock connectors for other exchanges
        for exchange in [Exchange.BYBIT, Exchange.OKX, Exchange.KRAKEN]:
            self._connectors[exchange] = MockConnector(exchange)

        # Initialize circuit breakers
        for exchange in self._connectors:
            self._circuit_breakers[exchange] = CircuitBreaker(
                failure_threshold=3, timeout_seconds=60
            )

    async def fetch_prices(
        self, exchange: Exchange, symbols: list[str]
    ) -> dict[str, Price]:
        """Fetch prices from exchange with circuit breaker.

        Args:
            exchange: The exchange to fetch from.
            symbols: List of symbols.

        Returns:
            Dictionary of prices.
        """
        connector = self._connectors.get(exchange)
        circuit_breaker = self._circuit_breakers.get(exchange)

        if not connector or not circuit_breaker:
            return {}

        # Check circuit breaker
        if not circuit_breaker.can_execute():
            # Try fallback to mock
            fallback = self._connectors.get(
                exchange, MockConnector(exchange)
            )
            return await fallback.fetch_prices(symbols)

        try:
            prices = await connector.fetch_prices(symbols)
            if prices:
                circuit_breaker.record_success()
            else:
                circuit_breaker.record_failure()
            return prices
        except Exception:
            circuit_breaker.record_failure()
            # Fallback to mock
            fallback = self._connectors.get(exchange, MockConnector(exchange))
            return await fallback.fetch_prices(symbols)

    async def check_exchange_available(self, exchange: Exchange) -> bool:
        """Check if exchange is available.

        Args:
            exchange: The exchange to check.

        Returns:
            True if available.
        """
        connector = self._connectors.get(exchange)
        if not connector:
            return False

        circuit_breaker = self._circuit_breakers.get(exchange)
        if circuit_breaker and not circuit_breaker.can_execute():
            return False

        try:
            return await connector.is_available()
        except Exception:
            if circuit_breaker:
                circuit_breaker.record_failure()
            return False

    def get_connector(self, exchange: Exchange) -> Optional[ExchangeConnector]:
        """Get connector for exchange.

        Args:
            exchange: The exchange.

        Returns:
            Connector or None.
        """
        return self._connectors.get(exchange)


class CircuitBreaker:
    """Circuit breaker pattern for API resilience.

    Prevents repeated calls to failing services.
    """

    def __init__(
        self,
        failure_threshold: int = 3,
        timeout_seconds: int = 60,
    ) -> None:
        """Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit.
            timeout_seconds: Time to wait before retrying.
        """
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self._failure_count = 0
        self._last_failure_time: Optional[pd.Timestamp] = None
        self._state = "closed"

    def can_execute(self) -> bool:
        """Check if execution is allowed.

        Returns:
            True if circuit is closed or half-open.
        """
        if self._state == "closed":
            return True

        if self._state == "open" and self._is_timeout_reached():
            self._state = "half-open"
            return True

        return self._state == "half-open"

    def record_success(self) -> None:
        """Record successful call."""
        self._failure_count = 0
        self._state = "closed"

    def record_failure(self) -> None:
        """Record failed call."""
        self._failure_count += 1
        self._last_failure_time = pd.Timestamp.now()

        if self._failure_count >= self.failure_threshold:
            self._state = "open"

    def _is_timeout_reached(self) -> bool:
        """Check if timeout has passed since last failure.

        Returns:
            True if timeout reached.
        """
        if not self._last_failure_time:
            return False

        elapsed = pd.Timestamp.now() - self._last_failure_time
        return elapsed.total_seconds() > self.timeout_seconds

    def get_state(self) -> str:
        """Get circuit breaker state.

        Returns:
            State string.
        """
        return self._state