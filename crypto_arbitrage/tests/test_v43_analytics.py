"""Test Suite for V43.0 Advanced Analytics
Comprehensive testing of performance attribution,
risk attribution, and analytics reports.
"""

import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.auto_execution_engine import (
    AutoExecutionEngine,
    PerformanceAttribution,
    TradeAttribution,
    RiskAttribution,
    AnalyticsReport
)


class TestV43_0AnalyticsConfig:
    """Test suite for Analytics Config - V43.0"""

    @pytest.fixture
    def engine(self):
        """Create engine with analytics config"""
        config = {
            'enable_analytics': True,
            'analytics_interval': 3600
        }
        return AutoExecutionEngine(config=config)

    def test_analytics_config(self, engine):
        """Test analytics configuration"""
        assert engine.run_config.enable_analytics is True
        assert engine.run_config.analytics_interval == 3600


class TestV43_0PerformanceAttribution:
    """Test suite for Performance Attribution - V43.0"""

    @pytest.fixture
    def engine(self):
        """Create engine"""
        return AutoExecutionEngine()

    def test_calculate_performance_attribution(self, engine):
        """Test calculating performance attribution"""
        returns = [0.01, 0.02, -0.01, 0.03, 0.01]
        benchmark = [0.005, 0.01, -0.005, 0.02, 0.005]

        attr = engine.calculate_performance_attribution("strategy1", returns, benchmark)

        assert isinstance(attr, PerformanceAttribution)
        assert attr.strategy_id == "strategy1"
        assert attr.total_return > 0

    def test_alpha_calculation(self, engine):
        """Test alpha calculation"""
        returns = [0.05] * 10
        benchmark = [0.02] * 10

        attr = engine.calculate_performance_attribution("test", returns, benchmark)
        assert attr.alpha > 0


class TestV43_0TradeAttribution:
    """Test suite for Trade Attribution - V43.0"""

    @pytest.fixture
    def engine(self):
        """Create engine"""
        return AutoExecutionEngine()

    def test_add_trade_attribution(self, engine):
        """Test adding trade attribution"""
        attr = engine.add_trade_attribution("trade1", "BTC/USDT", 100.0)

        assert attr.trade_id == "trade1"
        assert attr.pnl_contribution == 100.0


class TestV43_0RiskAttribution:
    """Test suite for Risk Attribution - V43.0"""

    @pytest.fixture
    def engine(self):
        """Create engine"""
        return AutoExecutionEngine()

    def test_calculate_risk_attribution(self, engine):
        """Test calculating risk attribution"""
        attr = engine.calculate_risk_attribution()

        assert isinstance(attr, RiskAttribution)
        assert attr.total_risk > 0


class TestV43_0AnalyticsReports:
    """Test suite for Analytics Reports - V43.0"""

    @pytest.fixture
    def engine(self):
        """Create engine"""
        return AutoExecutionEngine()

    def test_generate_analytics_report(self, engine):
        """Test generating analytics report"""
        report = engine.generate_analytics_report("daily")

        assert isinstance(report, AnalyticsReport)
        assert report.report_type == "daily"

    def test_get_analytics_report(self, engine):
        """Test getting analytics report"""
        report = engine.generate_analytics_report("weekly")
        report_id = report.report_id

        retrieved = engine.get_analytics_report(report_id)
        assert retrieved is not None


class TestV43_0V43Summary:
    """Test suite for V43 Summary - V43.0"""

    @pytest.fixture
    def engine(self):
        """Create engine"""
        config = {'enable_analytics': True}
        return AutoExecutionEngine(config=config)

    def test_v43_summary(self, engine):
        """Test V43.0 summary"""
        summary = engine.get_v43_summary()

        assert 'analytics_enabled' in summary
        assert 'reports_generated' in summary

    def test_all_features_initialized(self, engine):
        """Test all V43.0 features are initialized"""
        assert engine._analytics_reports is not None
        assert engine._trade_attributions is not None