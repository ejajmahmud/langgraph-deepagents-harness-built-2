"""Tests for the MarketAnalyzer."""

import asyncio
import pandas as pd
import pytest

from deepagents_crypto_trading.market_analyzer import MarketAnalyzer
from deepagents_crypto_trading.types import (
    ArbitrageType,
    Exchange,
    TradingConfig,
)


class TestMarketAnalyzer:
    """Tests for MarketAnalyzer."""

    @pytest.fixture
    def config(self) -> TradingConfig:
        """Create test configuration."""
        return TradingConfig(
            initial_capital=10000.0,
            enabled_exchanges=[Exchange.BINANCE, Exchange.COINBASE],
            enabled_strategies=[ArbitrageType.TRIANGULAR, ArbitrageType.CROSS_EXCHANGE],
        )

    @pytest.fixture
    def analyzer(self, config: TradingConfig) -> MarketAnalyzer:
        """Create test analyzer."""
        return MarketAnalyzer(config)

    def test_analyzer_creation(self, analyzer: MarketAnalyzer) -> None:
        """Test analyzer creation."""
        assert analyzer.latest_data is None
        assert not analyzer._running

    @pytest.mark.asyncio
    async def test_start_stop(self, analyzer: MarketAnalyzer) -> None:
        """Test start and stop."""
        await analyzer.start()
        assert analyzer._running
        await analyzer.stop()
        assert not analyzer._running

    @pytest.mark.asyncio
    async def test_fetch_exchange_prices(self, analyzer: MarketAnalyzer) -> None:
        """Test fetching exchange prices."""
        prices = await analyzer._fetch_exchange_prices(Exchange.BINANCE)
        assert "BTCUSDT" in prices
        assert "ETHUSDT" in prices
        assert prices["BTCUSDT"].exchange == Exchange.BINANCE

    @pytest.mark.asyncio
    async def test_fetch_market_data(self, analyzer: MarketAnalyzer) -> None:
        """Test fetching market data."""
        await analyzer._fetch_market_data()
        assert analyzer.latest_data is not None
        assert len(analyzer.latest_data.prices) > 0

    @pytest.mark.asyncio
    async def test_detect_opportunities(self, analyzer: MarketAnalyzer) -> None:
        """Test detecting opportunities."""
        # First fetch market data
        await analyzer._fetch_market_data()
        opportunities = analyzer.detect_opportunities()
        # Should return a list (may be empty depending on market)
        assert isinstance(opportunities, list)

    def test_calculate_volatility(self, analyzer: MarketAnalyzer) -> None:
        """Test volatility calculation."""
        # No data yet
        volatility = analyzer._calculate_volatility("BTCUSDT:BINANCE")
        assert volatility == 0.0

    def test_market_summary(self, analyzer: MarketAnalyzer) -> None:
        """Test market summary."""
        summary = analyzer.get_market_summary()
        if summary:
            assert "symbols" in summary
            assert "exchanges" in summary


class TestTriangularArbitrage:
    """Tests for triangular arbitrage detection."""

    @pytest.fixture
    def config(self) -> TradingConfig:
        """Create test configuration."""
        return TradingConfig(
            initial_capital=10000.0,
            enabled_exchanges=[Exchange.BINANCE],
            enabled_strategies=[ArbitrageType.TRIANGULAR],
        )

    @pytest.fixture
    def analyzer(self, config: TradingConfig) -> MarketAnalyzer:
        """Create test analyzer."""
        return MarketAnalyzer(config)

    @pytest.mark.asyncio
    async def test_detect_triangular(self, analyzer: MarketAnalyzer) -> None:
        """Test detecting triangular arbitrage."""
        await analyzer._fetch_market_data()
        opportunities = analyzer._detect_triangular_arbitrage(0.005, 0.7)
        assert isinstance(opportunities, list)


class TestCrossExchangeArbitrage:
    """Tests for cross-exchange arbitrage detection."""

    @pytest.fixture
    def config(self) -> TradingConfig:
        """Create test configuration."""
        return TradingConfig(
            initial_capital=10000.0,
            enabled_exchanges=[Exchange.BINANCE, Exchange.COINBASE],
            enabled_strategies=[ArbitrageType.CROSS_EXCHANGE],
        )

    @pytest.fixture
    def analyzer(self, config: TradingConfig) -> MarketAnalyzer:
        """Create test analyzer."""
        return MarketAnalyzer(config)

    @pytest.mark.asyncio
    async def test_detect_cross_exchange(self, analyzer: MarketAnalyzer) -> None:
        """Test detecting cross-exchange arbitrage."""
        await analyzer._fetch_market_data()
        opportunities = analyzer._detect_cross_exchange_arbitrage(0.005, 0.7)
        assert isinstance(opportunities, list)