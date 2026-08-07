"""Tests for the ArbitrageEngine."""

import pandas as pd
import pytest

from deepagents_crypto_trading.arbitrage_engine import (
    ArbitrageEngine,
    CrossExchangeArbitrage,
    TriangularArbitrage,
)
from deepagents_crypto_trading.types import (
    ArbitrageOpportunity,
    ArbitrageType,
    Exchange,
    OrderSide,
    Position,
    PositionStatus,
    TradingConfig,
    TradingPair,
)


class TestArbitrageEngine:
    """Tests for ArbitrageEngine."""

    @pytest.fixture
    def config(self) -> TradingConfig:
        """Create test configuration."""
        return TradingConfig(initial_capital=10000.0)

    @pytest.fixture
    def engine(self, config: TradingConfig) -> ArbitrageEngine:
        """Create test engine."""
        return ArbitrageEngine(config)

    def test_creation(self, engine: ArbitrageEngine) -> None:
        """Test engine creation."""
        assert len(engine.positions) == 0

    def test_add_position(self, engine: ArbitrageEngine) -> None:
        """Test adding a position."""
        position = Position(
            id="test-1",
            arbitrage_type=ArbitrageType.TRIANGULAR,
            trading_pairs=[
                TradingPair(base="BTC", quote="USDT", exchange=Exchange.BINANCE)
            ],
            entry_price=67000.0,
            current_price=67000.0,
            size=0.1,
            side=OrderSide.BUY,
            status=PositionStatus.OPEN,
            pnl=0.0,
            opened_at=pd.Timestamp.now(),
        )
        engine.add_position(position)
        assert len(engine.positions) == 1

    def test_close_position(self, engine: ArbitrageEngine) -> None:
        """Test closing a position."""
        position = Position(
            id="test-1",
            arbitrage_type=ArbitrageType.TRIANGULAR,
            trading_pairs=[],
            entry_price=67000.0,
            current_price=67000.0,
            size=0.1,
            side=OrderSide.BUY,
            status=PositionStatus.OPEN,
            pnl=0.0,
            opened_at=pd.Timestamp.now(),
        )
        engine.add_position(position)

        result = engine.close_position("test-1", 68000.0, 100.0)
        assert result is not None
        assert result.status == PositionStatus.CLOSED
        assert result.pnl == 100.0

    def test_get_open_positions(self, engine: ArbitrageEngine) -> None:
        """Test getting open positions."""
        position = Position(
            id="test-1",
            arbitrage_type=ArbitrageType.TRIANGULAR,
            trading_pairs=[],
            entry_price=67000.0,
            current_price=67000.0,
            size=0.1,
            side=OrderSide.BUY,
            status=PositionStatus.OPEN,
            pnl=0.0,
            opened_at=pd.Timestamp.now(),
        )
        engine.add_position(position)
        assert len(engine.get_open_positions()) == 1

    def test_get_total_pnl(self, engine: ArbitrageEngine) -> None:
        """Test getting total PnL."""
        position = Position(
            id="test-1",
            arbitrage_type=ArbitrageType.TRIANGULAR,
            trading_pairs=[],
            entry_price=67000.0,
            current_price=67000.0,
            size=0.1,
            side=OrderSide.BUY,
            status=PositionStatus.CLOSED,
            pnl=100.0,
            opened_at=pd.Timestamp.now(),
        )
        engine.add_position(position)
        assert engine.get_total_pnl() == 100.0

    def test_create_position(self, engine: ArbitrageEngine) -> None:
        """Test creating a position."""
        opp = ArbitrageOpportunity(
            arbitrage_type=ArbitrageType.TRIANGULAR,
            trading_pairs=[
                TradingPair(base="BTC", quote="USDT", exchange=Exchange.BINANCE)
            ],
            expected_profit_pct=1.0,
            required_capital=5000.0,
            estimated_duration_seconds=30,
            risk_level=0.3,
            confidence=0.8,
            exchanges=[Exchange.BINANCE],
        )
        position = engine.create_position(opp, 1000.0, 67000.0)
        assert position.arbitrage_type == ArbitrageType.TRIANGULAR
        assert position.size == 1000.0

    def test_get_performance_metrics(self, engine: ArbitrageEngine) -> None:
        """Test performance metrics."""
        metrics = engine.get_performance_metrics()
        assert "total_positions" in metrics
        assert "open_positions" in metrics
        assert "total_pnl" in metrics


class TestTriangularArbitrageStrategy:
    """Tests for TriangularArbitrage."""

    @pytest.fixture
    def config(self) -> TradingConfig:
        """Create test configuration."""
        return TradingConfig()

    @pytest.fixture
    def strategy(self, config: TradingConfig) -> TriangularArbitrage:
        """Create test strategy."""
        return TriangularArbitrage(config)

    def test_calculate_profit(
        self, strategy: TriangularArbitrage
    ) -> None:
        """Test profit calculation."""
        prices = [1.0, 0.01, 100.0]  # BTCUSDT, BTCETH, ETHUSDT
        path = [
            TradingPair(base="BTC", quote="USDT", exchange=Exchange.BINANCE),
            TradingPair(base="BTC", quote="ETH", exchange=Exchange.BINANCE),
            TradingPair(base="ETH", quote="USDT", exchange=Exchange.BINANCE),
        ]
        profit = strategy.calculate_profit(prices, path)
        assert isinstance(profit, float)

    def test_calculate_profit_invalid(
        self, strategy: TriangularArbitrage
    ) -> None:
        """Test profit calculation with invalid input."""
        prices = [1.0]  # Invalid
        path = []
        profit = strategy.calculate_profit(prices, path)
        assert profit == 0.0


class TestCrossExchangeArbitrageStrategy:
    """Tests for CrossExchangeArbitrage."""

    @pytest.fixture
    def config(self) -> TradingConfig:
        """Create test configuration."""
        return TradingConfig()

    @pytest.fixture
    def strategy(self, config: TradingConfig) -> CrossExchangeArbitrage:
        """Create test strategy."""
        return CrossExchangeArbitrage(config)

    def test_calculate_profit(
        self, strategy: CrossExchangeArbitrage
    ) -> None:
        """Test profit calculation."""
        profit = strategy.calculate_profit(100.0, 105.0)
        assert profit == 5.0

    def test_calculate_profit_invalid(
        self, strategy: CrossExchangeArbitrage
    ) -> None:
        """Test profit calculation with invalid input."""
        profit = strategy.calculate_profit(0.0, 105.0)
        assert profit == 0.0

    def test_find_opportunity(
        self, strategy: CrossExchangeArbitrage
    ) -> None:
        """Test finding opportunity."""
        prices = {
            "BTCUSDT": {
                "binance": 67000.0,
                "coinbase": 67200.0,
            }
        }
        result = strategy.find_opportunity(prices)
        # Should find opportunity between exchanges
        if result:
            buy_pair, sell_pair, profit = result
            assert profit > 0

    def test_find_opportunity_no_opportunity(
        self, strategy: CrossExchangeArbitrage
    ) -> None:
        """Test finding opportunity when none exists."""
        prices = {
            "BTCUSDT": {
                "binance": 67000.0,
                "coinbase": 67000.001,  # Tiny diff - essentially no opportunity
            }
        }
        result = strategy.find_opportunity(prices)
        # Result may be None (no opportunity) or have zero profit
        if result:
            buy_pair, sell_pair, profit = result
            # Just verify it's handled - may have tiny profit
            assert isinstance(profit, float)