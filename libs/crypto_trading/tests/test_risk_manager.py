"""Tests for the RiskManager."""

import pandas as pd
import pytest

from deepagents_crypto_trading.risk_manager import RiskManager
from deepagents_crypto_trading.types import (
    ArbitrageOpportunity,
    ArbitrageType,
    Exchange,
    OrderSide,
    Position,
    PositionStatus,
    RiskConfig,
    TradingConfig,
    TradingPair,
)


class TestRiskManager:
    """Tests for RiskManager."""

    @pytest.fixture
    def config(self) -> TradingConfig:
        """Create test configuration."""
        return TradingConfig(initial_capital=10000.0)

    @pytest.fixture
    def risk_manager(self, config: TradingConfig) -> RiskManager:
        """Create test risk manager."""
        return RiskManager(config)

    def test_creation(self, risk_manager: RiskManager) -> None:
        """Test risk manager creation."""
        assert risk_manager.initial_capital == 10000.0
        assert risk_manager.current_capital == 10000.0

    def test_daily_reset(self, risk_manager: RiskManager) -> None:
        """Test daily reset."""
        risk_manager.daily_loss = 100.0
        risk_manager.daily_reset()
        assert risk_manager.daily_loss == 0.0

    def test_calculate_position_size(
        self, risk_manager: RiskManager
    ) -> None:
        """Test position size calculation."""
        opp = ArbitrageOpportunity(
            arbitrage_type=ArbitrageType.TRIANGULAR,
            trading_pairs=[],
            expected_profit_pct=1.0,
            required_capital=5000.0,
            estimated_duration_seconds=30,
            risk_level=0.3,
            confidence=0.8,
            exchanges=[Exchange.BINANCE],
        )
        size = risk_manager.calculate_position_size(opp)
        # Should be 10% of capital
        assert size == 1000.0

    def test_calculate_position_size_with_positions(
        self, risk_manager: RiskManager
    ) -> None:
        """Test position size with existing positions."""
        # Position that uses half the capital
        existing = Position(
            id="test-1",
            arbitrage_type=ArbitrageType.TRIANGULAR,
            trading_pairs=[],
            entry_price=67000.0,
            current_price=67000.0,
            size=5000.0,  # Uses 5000 of capital
            side=OrderSide.BUY,
            status=PositionStatus.OPEN,
            pnl=0.0,
            opened_at=pd.Timestamp.now(),
        )

        opp = ArbitrageOpportunity(
            arbitrage_type=ArbitrageType.TRIANGULAR,
            trading_pairs=[],
            expected_profit_pct=1.0,
            required_capital=5000.0,
            estimated_duration_seconds=30,
            risk_level=0.3,
            confidence=0.8,
            exchanges=[Exchange.BINANCE],
        )
        size = risk_manager.calculate_position_size(opp, [existing])
        # Available is 5000 (10000 - 5000 used), max is 10% = 500
        # So the size is 500 (10% of remaining capacity)
        assert size == 500.0

    def test_get_available_capital(self, risk_manager: RiskManager) -> None:
        """Test available capital."""
        capital = risk_manager.get_available_capital([])
        assert capital == 10000.0

    def test_set_stop_loss(self, risk_manager: RiskManager) -> None:
        """Test stop loss calculation."""
        stop_loss = risk_manager.set_stop_loss(
            Position(
                id="test",
                arbitrage_type=ArbitrageType.TRIANGULAR,
                trading_pairs=[],
                entry_price=67000.0,
                current_price=67000.0,
                size=0.1,
                side=OrderSide.BUY,
                status=PositionStatus.OPEN,
                pnl=0.0,
                opened_at=pd.Timestamp.now(),
            ),
            67000.0,
        )
        # 2% stop loss
        assert stop_loss == 65660.0

    def test_set_take_profit(self, risk_manager: RiskManager) -> None:
        """Test take profit calculation."""
        take_profit = risk_manager.set_take_profit(
            Position(
                id="test",
                arbitrage_type=ArbitrageType.TRIANGULAR,
                trading_pairs=[],
                entry_price=67000.0,
                current_price=67000.0,
                size=0.1,
                side=OrderSide.BUY,
                status=PositionStatus.OPEN,
                pnl=0.0,
                opened_at=pd.Timestamp.now(),
            ),
            67000.0,
        )
        # 5% take profit
        assert take_profit == 70350.0

    def test_check_stop_loss_triggered(self, risk_manager: RiskManager) -> None:
        """Test stop loss triggered check."""
        position = Position(
            id="test",
            arbitrage_type=ArbitrageType.TRIANGULAR,
            trading_pairs=[],
            entry_price=67000.0,
            current_price=65660.0,  # 2% loss
            size=0.1,
            side=OrderSide.BUY,
            status=PositionStatus.OPEN,
            pnl=0.0,
            opened_at=pd.Timestamp.now(),
        )
        position.stop_loss = 65660.0

        triggered = risk_manager.check_stop_loss(position, 65660.0)
        # Should trigger when hit exactly the stop loss
        assert triggered

    def test_check_stop_loss_not_triggered(self, risk_manager: RiskManager) -> None:
        """Test stop loss not triggered check."""
        position = Position(
            id="test",
            arbitrage_type=ArbitrageType.TRIANGULAR,
            trading_pairs=[],
            entry_price=67000.0,
            current_price=66500.0,  # Small loss
            size=0.1,
            side=OrderSide.BUY,
            status=PositionStatus.OPEN,
            pnl=0.0,
            opened_at=pd.Timestamp.now(),
        )
        position.stop_loss = 65660.0

        triggered = risk_manager.check_stop_loss(position, 66500.0)
        assert not triggered

    def test_check_take_profit_triggered(self, risk_manager: RiskManager) -> None:
        """Test take profit triggered check."""
        position = Position(
            id="test",
            arbitrage_type=ArbitrageType.TRIANGULAR,
            trading_pairs=[],
            entry_price=67000.0,
            current_price=70350.0,  # 5% profit
            size=0.1,
            side=OrderSide.BUY,
            status=PositionStatus.OPEN,
            pnl=0.0,
            opened_at=pd.Timestamp.now(),
        )
        position.take_profit = 70350.0

        triggered = risk_manager.check_take_profit(position, 70350.0)
        assert triggered

    def test_calculate_pnl(self, risk_manager: RiskManager) -> None:
        """Test PnL calculation."""
        position = Position(
            id="test",
            arbitrage_type=ArbitrageType.TRIANGULAR,
            trading_pairs=[],
            entry_price=67000.0,
            current_price=67000.0,
            size=1.0,
            side=OrderSide.BUY,
            status=PositionStatus.OPEN,
            pnl=0.0,
            opened_at=pd.Timestamp.now(),
        )

        pnl = risk_manager.calculate_pnl(position, 68000.0, fees=10.0)
        # (68000 - 67000) * 1 - 10 = 990
        assert pnl == 990.0

    def test_update_capital(self, risk_manager: RiskManager) -> None:
        """Test capital update."""
        risk_manager.update_capital(100.0)
        assert risk_manager.current_capital == 10100.0
        assert risk_manager.daily_loss == 100.0

    def test_get_risk_metrics(self, risk_manager: RiskManager) -> None:
        """Test risk metrics."""
        metrics = risk_manager.get_risk_metrics()
        assert "current_capital" in metrics
        assert "available_capital" in metrics
        assert "max_position_pct" in metrics

    def test_reset_capital(self, risk_manager: RiskManager) -> None:
        """Test capital reset."""
        risk_manager.current_capital = 5000.0
        risk_manager.reset_capital(20000.0)
        assert risk_manager.initial_capital == 20000.0
        assert risk_manager.current_capital == 20000.0


class TestRiskChecks:
    """Tests for risk check functions."""

    @pytest.fixture
    def config(self) -> TradingConfig:
        """Create test configuration."""
        return TradingConfig(initial_capital=10000.0)

    @pytest.fixture
    def risk_manager(self, config: TradingConfig) -> RiskManager:
        """Create test risk manager."""
        return RiskManager(config)

    def test_check_opportunity_confidence_too_low(
        self, risk_manager: RiskManager
    ) -> None:
        """Test check opportunity with low confidence."""
        opp = ArbitrageOpportunity(
            arbitrage_type=ArbitrageType.TRIANGULAR,
            trading_pairs=[],
            expected_profit_pct=1.0,
            required_capital=5000.0,
            estimated_duration_seconds=30,
            risk_level=0.3,
            confidence=0.5,  # Below min_confidence
            exchanges=[Exchange.BINANCE],
        )
        result = risk_manager.check_opportunity(opp, [])
        assert not result

    def test_check_opportunity_profit_too_low(
        self, risk_manager: RiskManager
    ) -> None:
        """Test check opportunity with low profit."""
        opp = ArbitrageOpportunity(
            arbitrage_type=ArbitrageType.TRIANGULAR,
            trading_pairs=[],
            expected_profit_pct=0.1,  # Below min_profit_pct
            required_capital=5000.0,
            estimated_duration_seconds=30,
            risk_level=0.3,
            confidence=0.8,
            exchanges=[Exchange.BINANCE],
        )
        result = risk_manager.check_opportunity(opp, [])
        assert not result

    def test_check_opportunity_risk_too_high(
        self, risk_manager: RiskManager
    ) -> None:
        """Test check opportunity with high risk."""
        opp = ArbitrageOpportunity(
            arbitrage_type=ArbitrageType.TRIANGULAR,
            trading_pairs=[],
            expected_profit_pct=1.0,
            required_capital=5000.0,
            estimated_duration_seconds=30,
            risk_level=0.8,  # Above 0.5 threshold
            confidence=0.8,
            exchanges=[Exchange.BINANCE],
        )
        result = risk_manager.check_opportunity(opp, [])
        assert not result

    def test_check_opportunity_passes(
        self, risk_manager: RiskManager
    ) -> None:
        """Test check opportunity that passes."""
        opp = ArbitrageOpportunity(
            arbitrage_type=ArbitrageType.TRIANGULAR,
            trading_pairs=[],
            expected_profit_pct=1.0,
            required_capital=5000.0,
            estimated_duration_seconds=30,
            risk_level=0.3,
            confidence=0.8,
            exchanges=[Exchange.BINANCE],
        )
        result = risk_manager.check_opportunity(opp, [])
        assert result