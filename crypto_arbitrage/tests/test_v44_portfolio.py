"""Test Suite for V44.0 Portfolio & Execution
Comprehensive testing of portfolio optimization,
execution algorithms, and smart routing.
"""

import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.auto_execution_engine import (
    AutoExecutionEngine,
    PortfolioOptimization,
    ExecutionAlgorithm
)


class TestV44_0Config:
    """Test suite for V44.0 Config"""

    @pytest.fixture
    def engine(self):
        config = {
            'enable_optimization': True,
            'enable_smart_routing': True
        }
        return AutoExecutionEngine(config=config)

    def test_v44_config(self, engine):
        assert engine.run_config.enable_optimization is True
        assert engine.run_config.enable_smart_routing is True


class TestV44_0PortfolioOptimization:
    """Test suite for Portfolio Optimization"""

    @pytest.fixture
    def engine(self):
        return AutoExecutionEngine(config={'enable_optimization': True})

    def test_optimize_portfolio(self, engine):
        engine.add_to_portfolio("BTC", 0.5, 45000, 46000)
        engine.add_to_portfolio("ETH", 2.0, 2500, 2600)

        opt = engine.optimize_portfolio(target_return=0.15)
        assert isinstance(opt, PortfolioOptimization)
        assert len(opt.weights) == 2


class TestV44_0ExecutionAlgorithm:
    """Test suite for Execution Algorithm"""

    @pytest.fixture
    def engine(self):
        return AutoExecutionEngine()

    def test_create_execution_algorithm(self, engine):
        algo = engine.create_execution_algorithm(
            algorithm_type="twap",
            symbol="BTC/USDT",
            quantity=1.0
        )
        assert algo.algorithm_type == "twap"
        assert algo.quantity == 1.0

    def test_execute_algo_slice(self, engine):
        algo = engine.create_execution_algorithm("vwap", "ETH/USDT", 10.0)
        result = engine.execute_algo_slice(algo.algorithm_id, 2.0, 2500.0)
        assert result is True


class TestV44_0SmartRouting:
    """Test suite for Smart Routing"""

    @pytest.fixture
    def engine(self):
        return AutoExecutionEngine(config={'enable_smart_routing': True})

    def test_smart_route_order(self, engine):
        result = engine.smart_route_order("BTC/USDT", "buy", 0.5)
        assert 'exchange' in result
        assert 'routers_checked' in result


class TestV44_0Summary:
    """Test suite for V44 Summary"""

    @pytest.fixture
    def engine(self):
        return AutoExecutionEngine(config={'enable_optimization': True})

    def test_v44_summary(self, engine):
        summary = engine.get_v44_summary()
        assert 'optimization_enabled' in summary
        assert 'execution_algorithms' in summary