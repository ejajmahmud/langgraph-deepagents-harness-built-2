"""Test Suite for V38.0 Risk Management
Comprehensive testing of risk management system, VaR/CVaR,
portfolio management, and risk metrics.
"""

import pytest
import time
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.auto_execution_engine import (
    AutoExecutionEngine,
    RiskMetrics,
    PortfolioPosition
)


class TestV38_0RiskConfig:
    """Test suite for Risk Management Config - V38.0"""

    @pytest.fixture
    def engine(self):
        """Create engine with risk config"""
        config = {
            'enable_risk_management': True,
            'max_var_pct': 0.02,
            'max_position_pct': 0.20,
            'var_confidence': 0.95
        }
        return AutoExecutionEngine(config=config)

    def test_risk_config(self, engine):
        """Test risk management configuration"""
        assert engine.run_config.enable_risk_management is True
        assert engine.run_config.max_var_pct == 0.02
        assert engine.run_config.var_confidence == 0.95


class TestV38_0VaR:
    """Test suite for VaR Calculation - V38.0"""

    @pytest.fixture
    def engine(self):
        """Create engine"""
        return AutoExecutionEngine()

    def test_calculate_var_historical(self, engine):
        """Test VaR calculation"""
        returns = [0.01, -0.02, 0.03, -0.01, 0.02, -0.03, 0.01, -0.02]
        var = engine.calculate_var_historical(returns, 0.95)

        assert var >= 0
        assert var <= max(abs(r) for r in returns)

    def test_calculate_cvar(self, engine):
        """Test CVaR calculation"""
        returns = [0.01, -0.02, 0.03, -0.01, 0.02, -0.03, 0.01, -0.02]
        cvar = engine.calculate_cvar(returns, 0.95)

        assert cvar >= 0
        assert cvar >= engine.calculate_var_historical(returns, 0.95)

    def test_var_empty(self, engine):
        """Test VaR with empty returns"""
        var = engine.calculate_var_historical([], 0.95)
        assert var == 0.0


class TestV38_0RiskMetrics:
    """Test suite for Risk Metrics - V38.0"""

    @pytest.fixture
    def engine(self):
        """Create engine"""
        return AutoExecutionEngine()

    def test_calculate_risk_metrics(self, engine):
        """Test risk metrics calculation"""
        prices = [45000, 45200, 44800, 45100, 45300, 44900, 45500, 45100]
        metrics = engine.calculate_risk_metrics("BTC/USDT", prices)

        assert isinstance(metrics, RiskMetrics)
        assert metrics.var_95 >= 0
        assert metrics.volatility >= 0

    def test_get_risk_metrics(self, engine):
        """Test getting risk metrics"""
        prices = [45000, 45200, 44800]
        engine.calculate_risk_metrics("ETH/USDT", prices)

        metrics = engine.get_risk_metrics("ETH/USDT")
        assert metrics is not None


class TestV38_0Portfolio:
    """Test suite for Portfolio - V38.0"""

    @pytest.fixture
    def engine(self):
        """Create engine"""
        return AutoExecutionEngine()

    def test_add_to_portfolio(self, engine):
        """Test adding to portfolio"""
        engine.add_to_portfolio(
            symbol="BTC/USDT",
            quantity=0.5,
            avg_price=45000,
            current_price=46000,
            beta=1.2
        )

        position = engine.get_portfolio_position("BTC/USDT")
        assert position is not None
        assert position.quantity == 0.5

    def test_portfolio_value(self, engine):
        """Test portfolio value"""
        engine.add_to_portfolio("BTC/USDT", 0.5, 45000, 46000)
        engine.add_to_portfolio("ETH/USDT", 2.0, 2500, 2600)

        value = engine.get_portfolio_value()
        assert value > 0

    def test_portfolio_pnl(self, engine):
        """Test portfolio PnL"""
        engine.add_to_portfolio("BTC/USDT", 0.5, 45000, 46000)

        pnl = engine.get_portfolio_pnl()
        assert pnl > 0

    def test_portfolio_summary(self, engine):
        """Test portfolio summary"""
        engine.add_to_portfolio("BTC/USDT", 0.5, 45000, 46000)

        summary = engine.get_portfolio_summary()
        assert 'total_value' in summary
        assert 'position_count' in summary


class TestV38_0PositionSizing:
    """Test suite for Risk-Based Position Sizing - V38.0"""

    @pytest.fixture
    def engine(self):
        """Create engine"""
        return AutoExecutionEngine()

    def test_calculate_position_size_risk(self, engine):
        """Test position sizing based on risk"""
        size = engine.calculate_position_size_risk(
            symbol="BTC/USDT",
            entry_price=45000,
            stop_loss_pct=0.02,
            risk_amount=1000
        )

        # risk_amount / (entry_price * stop_loss_pct)
        expected = 1000 / (45000 * 0.02)
        assert abs(size - expected) < 0.01


class TestV38_0V38Summary:
    """Test suite for V38 Summary - V38.0"""

    @pytest.fixture
    def engine(self):
        """Create engine"""
        config = {'enable_risk_management': True}
        return AutoExecutionEngine(config=config)

    def test_v38_summary(self, engine):
        """Test V38.0 summary"""
        summary = engine.get_v38_summary()

        assert 'risk_metrics_count' in summary
        assert 'portfolio_positions' in summary

    def test_all_features_initialized(self, engine):
        """Test all V38.0 features are initialized"""
        assert engine._risk_metrics is not None
        assert engine._portfolio is not None