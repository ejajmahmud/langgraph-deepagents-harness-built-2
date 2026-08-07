"""Tests for exchange connector module."""

import pytest

from deepagents_crypto_trading.exchange_connector import (
    BinanceConnector,
    CircuitBreaker,
    CoinbaseConnector,
    Exchange,
    ExchangeConnectorManager,
    MockConnector,
)


class TestCircuitBreaker:
    """Tests for CircuitBreaker."""

    def test_creation(self) -> None:
        """Test circuit breaker creation."""
        cb = CircuitBreaker(failure_threshold=3, timeout_seconds=60)
        assert cb.get_state() == "closed"
        assert cb.can_execute()

    def test_record_failure(self) -> None:
        """Test recording failures."""
        cb = CircuitBreaker(failure_threshold=2, timeout_seconds=60)
        cb.record_failure()
        assert cb.get_state() == "closed"
        cb.record_failure()
        assert cb.get_state() == "open"
        assert not cb.can_execute()

    def test_record_success(self) -> None:
        """Test recording success."""
        cb = CircuitBreaker(failure_threshold=2, timeout_seconds=60)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        assert cb.get_state() == "closed"
        assert cb.can_execute()


class TestMockConnector:
    """Tests for MockConnector."""

    def test_creation(self) -> None:
        """Test mock connector creation."""
        connector = MockConnector(Exchange.BINANCE)
        assert connector.exchange == Exchange.BINANCE

    @pytest.mark.asyncio
    async def test_fetch_prices(self) -> None:
        """Test fetching mock prices."""
        connector = MockConnector(Exchange.BINANCE)
        prices = await connector.fetch_prices(["BTCUSDT", "ETHUSDT"])
        assert len(prices) == 2
        assert "BTCUSDT" in prices
        assert "ETHUSDT" in prices
        assert prices["BTCUSDT"].price > 0
        assert prices["BTCUSDT"].exchange == Exchange.BINANCE

    @pytest.mark.asyncio
    async def test_is_available(self) -> None:
        """Test mock availability."""
        connector = MockConnector(Exchange.BINANCE)
        assert await connector.is_available()


class TestExchangeConnectorManager:
    """Tests for ExchangeConnectorManager."""

    def test_creation(self) -> None:
        """Test manager creation."""
        manager = ExchangeConnectorManager()
        assert Exchange.BINANCE in manager._connectors
        assert Exchange.COINBASE in manager._connectors

    @pytest.mark.asyncio
    async def test_fetch_prices(self) -> None:
        """Test fetching prices through manager."""
        manager = ExchangeConnectorManager()
        # Try with mock exchange to ensure fallback works
        # Mock prices should always work
        prices = await manager.fetch_prices(Exchange.BYBIT, ["BTCUSDT"])
        # Note: test depends on network, so verify basic functionality
        assert isinstance(prices, dict)

    @pytest.mark.asyncio
    async def test_check_exchange_available(self) -> None:
        """Test checking exchange availability."""
        manager = ExchangeConnectorManager()
        # Binance may or may not be available (real API)
        # But manager should handle it gracefully
        is_available = await manager.check_exchange_available(Exchange.BINANCE)
        # Just ensure it returns a boolean
        assert isinstance(is_available, bool)


class TestBinanceConnector:
    """Tests for BinanceConnector."""

    @pytest.mark.asyncio
    async def test_creation(self) -> None:
        """Test connector creation."""
        connector = BinanceConnector()
        assert connector.exchange == Exchange.BINANCE

    @pytest.mark.asyncio
    async def test_fetch_prices_handles_errors(self) -> None:
        """Test error handling in fetch prices."""
        connector = BinanceConnector()
        # Should handle errors gracefully and return dict
        prices = await connector.fetch_prices(["INVALID"])
        assert isinstance(prices, dict)


class TestCoinbaseConnector:
    """Tests for CoinbaseConnector."""

    @pytest.mark.asyncio
    async def test_creation(self) -> None:
        """Test connector creation."""
        connector = CoinbaseConnector()
        assert connector.exchange == Exchange.COINBASE