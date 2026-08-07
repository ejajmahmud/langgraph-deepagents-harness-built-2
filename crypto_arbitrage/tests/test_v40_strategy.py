"""Test Suite for V40.0 Multi-Strategy Portfolio
Comprehensive testing of multi-strategy management,
strategy performance tracking, market regime detection,
and strategy rotation.
"""

import pytest
import time
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.auto_execution_engine import (
    AutoExecutionEngine,
    StrategyPerformance,
    StrategyAllocation,
    MarketRegimeData
)


class TestV40_0MultiStrategyConfig:
    """Test suite for Multi-Strategy Config - V40.0"""

    @pytest.fixture
    def engine(self):
        """Create engine with multi-strategy config"""
        config = {
            'enable_multi_strategy': True,
            'max_active_strategies': 5,
            'rebalance_interval': 3600,
            'strategy_rotation': True
        }
        return AutoExecutionEngine(config=config)

    def test_multi_strategy_config(self, engine):
        """Test multi-strategy configuration"""
        assert engine.run_config.enable_multi_strategy is True
        assert engine.run_config.max_active_strategies == 5
        assert engine.run_config.strategy_rotation is True


class TestV40_0StrategyRegistration:
    """Test suite for Strategy Registration - V40.0"""

    @pytest.fixture
    def engine(self):
        """Create engine"""
        return AutoExecutionEngine()

    def test_register_strategy(self, engine):
        """Test registering a strategy"""
        result = engine.register_strategy(
            strategy_id="momentum_001",
            strategy_name="Momentum Strategy",
            allocation_pct=0.30
        )

        assert result is True
        assert "momentum_001" in engine._strategy_allocations

    def test_register_max_strategies(self, engine):
        """Test registering max strategies"""
        # 尝试注册超过最大数量
        for i in range(6):
            result = engine.register_strategy(
                strategy_id=f"strategy_{i}",
                strategy_name=f"Strategy {i}",
                allocation_pct=0.20
            )

        # 最后一个应该失败
        assert result is False

    def test_get_all_strategies(self, engine):
        """Test getting all strategies"""
        engine.register_strategy("strat1", "Strategy 1", 0.30)
        engine.register_strategy("strat2", "Strategy 2", 0.50)

        strategies = engine.get_all_strategies()
        assert len(strategies) == 2


class TestV40_0StrategyPerformance:
    """Test suite for Strategy Performance - V40.0"""

    @pytest.fixture
    def engine(self):
        """Create engine"""
        return AutoExecutionEngine()

    def test_update_strategy_performance(self, engine):
        """Test updating strategy performance"""
        engine.register_strategy("momentum", "Momentum", 0.30)

        result = engine.update_strategy_performance(
            strategy_id="momentum",
            total_return=0.15,
            sharpe_ratio=1.5,
            max_drawdown=0.08,
            win_rate=0.60,
            trade_count=50
        )

        assert result is True
        perf = engine.get_strategy_performance("momentum")
        assert perf.total_return == 0.15

    def test_get_strategy_performance(self, engine):
        """Test getting strategy performance"""
        engine.register_strategy("mean_rev", "Mean Reversion", 0.20)
        engine.update_strategy_performance(
            "mean_rev",
            total_return=0.10,
            sharpe_ratio=1.2,
            max_drawdown=0.05,
            win_rate=0.55,
            trade_count=30
        )

        perf = engine.get_strategy_performance("mean_rev")
        assert perf is not None
        assert perf.sharpe_ratio == 1.2


class TestV40_0MarketRegime:
    """Test suite for Market Regime Detection - V40.0"""

    @pytest.fixture
    def engine(self):
        """Create engine"""
        return AutoExecutionEngine()

    def test_detect_market_regime(self, engine):
        """Test market regime detection"""
        prices = []
        volume = []
        base_price = 45000

        for i in range(20):
            prices.append(base_price * (1 + 0.001 * i))
            volume.append(1000 * (1 + 0.1 * i))

        regime = engine.detect_market_regime_v2(prices, volume)

        assert isinstance(regime, MarketRegimeData)
        assert regime.regime in ["trending_up", "trending_down", "ranging", "volatile"]

    def test_get_market_regime(self, engine):
        """Test getting market regime"""
        prices = [45000, 45100, 45200, 45300, 45400] * 5
        volume = [1000] * 25

        engine.detect_market_regime_v2(prices, volume)
        regime = engine.get_market_regime()

        assert regime is not None


class TestV40_0StrategyRotation:
    """Test suite for Strategy Rotation - V40.0"""

    @pytest.fixture
    def engine(self):
        """Create engine"""
        config = {
            'strategy_rotation': True,
            'rebalance_interval': 1  # 1 second for testing
        }
        return AutoExecutionEngine(config=config)

    def test_should_rotate_strategies(self, engine):
        """Test checking if strategies should rotate"""
        engine._last_rebalance = time.time() - 10  # 10 seconds ago

        # Should rotate since rebalance_interval is 1 second
        result = engine.should_rotate_strategies()
        assert result is True

    def test_rotate_strategies(self, engine):
        """Test rotating strategies"""
        # Register strategies and update performance
        engine.register_strategy("strat1", "Strategy 1", 0.40)
        engine.register_strategy("strat2", "Strategy 2", 0.40)

        engine.update_strategy_performance("strat1", 0.10, 1.5, 0.05, 0.60, 20)
        engine.update_strategy_performance("strat2", 0.05, 1.0, 0.08, 0.50, 15)

        # Force time to pass for rebalance
        engine._last_rebalance = time.time() - 10

        result = engine.rotate_strategies()

        assert result['action'] == 'rotated'
        assert result['strategies_rotated'] == 2


class TestV40_0V40Summary:
    """Test suite for V40 Summary - V40.0"""

    @pytest.fixture
    def engine(self):
        """Create engine"""
        config = {'enable_multi_strategy': True}
        return AutoExecutionEngine(config=config)

    def test_v40_summary(self, engine):
        """Test V40.0 summary"""
        summary = engine.get_v40_summary()

        assert 'strategies_registered' in summary
        assert 'multi_strategy_enabled' in summary
        assert 'strategy_rotation' in summary

    def test_all_features_initialized(self, engine):
        """Test all V40.0 features are initialized"""
        assert engine._strategy_performances is not None
        assert engine._strategy_allocations is not None