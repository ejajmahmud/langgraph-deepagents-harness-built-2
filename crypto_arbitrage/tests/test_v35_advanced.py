"""Test Suite for V35.0 Triangular Arbitrage, Funding Rate Arbitrage & ML Signals
Comprehensive testing of triangular arbitrage, funding rate arbitrage,
and ML signal integration.
"""

import pytest
import time
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.auto_execution_engine import (
    AutoExecutionEngine,
    TriangularOpportunity,
    FundingArbitrage,
    MLSignal
)


class TestV35_0TriangularArbitrage:
    """Test suite for Triangular Arbitrage - V35.0"""

    @pytest.fixture
    def engine(self):
        """Create engine with triangular config"""
        config = {
            'enable_triangular': True,
            'triangular_min_profit': 0.001,
            'triangular_paths': 'BTC,ETH,SOL,BNB'
        }
        return AutoExecutionEngine(config=config)

    def test_triangular_config(self, engine):
        """Test triangular configuration"""
        assert engine.run_config.enable_triangular is True
        assert engine.run_config.triangular_min_profit == 0.001
        assert engine.run_config.triangular_paths == 'BTC,ETH,SOL,BNB'

    def test_scan_triangular(self, engine):
        """Test triangular arbitrage scanning"""
        opportunities = engine.scan_triangular_arbitrage("BTC")

        assert isinstance(opportunities, list)
        # Check each opportunity
        for opp in opportunities:
            assert opp.symbol_a != opp.symbol_b
            assert opp.symbol_b != opp.symbol_c
            assert opp.expected_profit_pct >= 0

    def test_get_triangular_opportunities(self, engine):
        """Test getting stored opportunities"""
        engine.scan_triangular_arbitrage("BTC")
        opportunities = engine.get_triangular_opportunities()

        assert isinstance(opportunities, list)

    def test_triangular_disabled(self, engine):
        """Test triangular when disabled"""
        engine.run_config.enable_triangular = False

        opportunities = engine.scan_triangular_arbitrage("BTC")
        assert len(opportunities) == 0


class TestV35_0FundingArbitrage:
    """Test suite for Funding Rate Arbitrage - V35.0"""

    @pytest.fixture
    def engine(self):
        """Create engine with funding arbitrage config"""
        config = {
            'enable_funding_arbitrage': True,
            'funding_min_diff': 0.0005,
            'funding_exchanges': 'binance,bybit,okx'
        }
        return AutoExecutionEngine(config=config)

    def test_funding_config(self, engine):
        """Test funding arbitrage configuration"""
        assert engine.run_config.enable_funding_arbitrage is True
        assert engine.run_config.funding_min_diff == 0.0005
        assert engine.run_config.funding_exchanges == 'binance,bybit,okx'

    def test_scan_funding(self, engine):
        """Test funding rate arbitrage scanning"""
        opportunities = engine.scan_funding_arbitrage("BTC/USDT")

        assert isinstance(opportunities, list)
        for arb in opportunities:
            assert arb.symbol == "BTC/USDT"
            assert arb.exchange_a != arb.exchange_b
            assert arb.rate_diff >= 0

    def test_get_funding_opportunities(self, engine):
        """Test getting stored opportunities"""
        engine.scan_funding_arbitrage("BTC/USDT")
        opportunities = engine.get_funding_arbitrage_opportunities()

        assert isinstance(opportunities, list)

    def test_funding_disabled(self, engine):
        """Test funding arbitrage when disabled"""
        engine.run_config.enable_funding_arbitrage = False

        opportunities = engine.scan_funding_arbitrage("BTC/USDT")
        assert len(opportunities) == 0


class TestV35_0MLSignals:
    """Test suite for ML Signal Integration - V35.0"""

    @pytest.fixture
    def engine(self):
        """Create engine with ML config"""
        config = {
            'enable_ml_signal': True,
            'ml_confidence_threshold': 0.6
        }
        return AutoExecutionEngine(config=config)

    def test_ml_config(self, engine):
        """Test ML signal configuration"""
        assert engine.run_config.enable_ml_signal is True
        assert engine.run_config.ml_confidence_threshold == 0.6

    def test_add_ml_signal_buy(self, engine):
        """Test adding buy signal"""
        result = engine.add_ml_signal("BTC/USDT", 1.0, 0.8, "model_v1")

        assert result is True
        signal = engine.get_ml_signal("BTC/USDT")
        assert signal is not None
        assert signal.prediction == 1.0
        assert signal.confidence == 0.8

    def test_add_ml_signal_sell(self, engine):
        """Test adding sell signal"""
        result = engine.add_ml_signal("ETH/USDT", -1.0, 0.7, "model_v1")

        assert result is True
        signal = engine.get_ml_signal("ETH/USDT")
        assert signal.prediction == -1.0

    def test_add_ml_signal_low_confidence(self, engine):
        """Test adding signal with low confidence"""
        result = engine.add_ml_signal("BTC/USDT", 1.0, 0.5, "model_v1")

        # Should fail due to threshold
        assert result is False

    def test_add_ml_signal_disabled(self, engine):
        """Test adding signal when disabled"""
        engine.run_config.enable_ml_signal = False

        result = engine.add_ml_signal("BTC/USDT", 1.0, 0.8, "model_v1")
        assert result is False

    def test_get_ml_signals_summary(self, engine):
        """Test getting ML signals summary"""
        engine.add_ml_signal("BTC/USDT", 1.0, 0.8, "model_v1")
        engine.add_ml_signal("ETH/USDT", -1.0, 0.7, "model_v1")
        engine.add_ml_signal("SOL/USDT", 0.0, 0.6, "model_v1")

        summary = engine.get_ml_signals_summary()

        assert summary['total_signals'] == 3
        assert summary['buy_signals'] == 1
        assert summary['sell_signals'] == 1
        assert summary['neutral_signals'] == 1
        assert summary['avg_confidence'] > 0

    def test_get_ml_signal_empty(self, engine):
        """Test getting non-existent signal"""
        signal = engine.get_ml_signal("BTC/USDT")
        assert signal is None


class TestV35_0AdvancedArbitrageSummary:
    """Test suite for Advanced Arbitrage Summary - V35.0"""

    @pytest.fixture
    def engine(self):
        """Create engine with all V35.0 features"""
        config = {
            'enable_triangular': True,
            'enable_funding_arbitrage': True,
            'enable_ml_signal': True
        }
        return AutoExecutionEngine(config=config)

    def test_advanced_summary(self, engine):
        """Test advanced arbitrage summary"""
        # Generate data
        engine.scan_triangular_arbitrage("BTC")
        engine.scan_funding_arbitrage("BTC/USDT")
        engine.add_ml_signal("BTC/USDT", 1.0, 0.8, "model_v1")

        summary = engine.get_advanced_arbitrage_summary()

        assert 'triangular_count' in summary
        assert 'funding_arbitrage_count' in summary
        assert 'ml_signals' in summary
        assert 'ml_summary' in summary


class TestV35_0Dataclasses:
    """Test V35.0 dataclasses"""

    def test_triangular_opportunity(self):
        """Test TriangularOpportunity dataclass"""
        opp = TriangularOpportunity(
            symbol_a="BTC",
            symbol_b="ETH",
            symbol_c="USDT",
            path="BTC→ETH→USDT→BTC",
            rate_a_to_b=15.0,
            rate_b_to_c=3300.0,
            rate_c_to_a=0.00002,
            expected_profit_pct=0.001,
            score=80.0,
            timestamp=time.time()
        )

        assert opp.symbol_a == "BTC"
        assert opp.expected_profit_pct > 0

    def test_funding_arbitrage(self):
        """Test FundingArbitrage dataclass"""
        arb = FundingArbitrage(
            symbol="BTC/USDT",
            exchange_a="binance",
            exchange_b="bybit",
            funding_rate_a=0.0001,
            funding_rate_b=0.0002,
            rate_diff=0.0001,
            potential_profit=10.0,
            score=50.0,
            timestamp=time.time()
        )

        assert arb.symbol == "BTC/USDT"
        assert arb.rate_diff > 0

    def test_ml_signal(self):
        """Test MLSignal dataclass"""
        signal = MLSignal(
            symbol="BTC/USDT",
            prediction=1.0,
            confidence=0.85,
            model_name="lstm_v1",
            timestamp=time.time()
        )

        assert signal.symbol == "BTC/USDT"
        assert signal.prediction == 1.0
        assert signal.confidence == 0.85


if __name__ == "__main__":
    pytest.main([__file__, "-v"])