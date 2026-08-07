"""Test Suite for V46.0 Sentiment & Correlation
Comprehensive testing of sentiment analysis,
correlation matrix, and multi-timeframe signals.
"""

import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.auto_execution_engine import (
    AutoExecutionEngine,
    SentimentData,
    CorrelationPair,
    TimeframeSignal
)


class TestV46_0Config:
    """Test suite for V46.0 Config"""

    @pytest.fixture
    def engine(self):
        config = {
            'enable_sentiment': True,
            'enable_correlation': True,
            'enable_multitimeframe': True
        }
        return AutoExecutionEngine(config=config)

    def test_v46_config(self, engine):
        assert engine.run_config.enable_sentiment is True
        assert engine.run_config.enable_correlation is True


class TestV46_0Sentiment:
    """Test suite for Sentiment Analysis"""

    @pytest.fixture
    def engine(self):
        return AutoExecutionEngine(config={'enable_sentiment': True})

    def test_update_sentiment(self, engine):
        data = engine.update_sentiment("BTC", 0.5, 100, 20, 80)
        assert isinstance(data, SentimentData)
        assert data.sentiment_score == 0.5

    def test_get_sentiment(self, engine):
        engine.update_sentiment("ETH", 0.3, 50, 10, 40)
        data = engine.get_sentiment("ETH")
        assert data is not None


class TestV46_0Correlation:
    """Test suite for Correlation"""

    @pytest.fixture
    def engine(self):
        return AutoExecutionEngine(config={'enable_correlation': True})

    def test_calculate_correlation(self, engine):
        prices_a = [100, 105, 110, 115, 120]
        prices_b = [50, 52, 55, 58, 60]
        corr = engine.calculate_correlation("A", "B", prices_a, prices_b)
        assert -1 <= corr <= 1


class TestV46_0Timeframe:
    """Test suite for Multi-Timeframe"""

    @pytest.fixture
    def engine(self):
        return AutoExecutionEngine(config={'enable_multitimeframe': True})

    def test_add_timeframe_signal(self, engine):
        sig = engine.add_timeframe_signal("BTC", "1h", "buy", 0.7)
        assert isinstance(sig, TimeframeSignal)
        assert sig.signal == "buy"

    def test_get_multiframe_signals(self, engine):
        engine.add_timeframe_signal("ETH", "1h", "buy", 0.6)
        engine.add_timeframe_signal("ETH", "4h", "sell", 0.4)
        signals = engine.get_multi_timeframe_signals("ETH")
        assert '1h' in signals


class TestV46_0Summary:
    """Test suite for V46 Summary"""

    @pytest.fixture
    def engine(self):
        return AutoExecutionEngine()

    def test_v46_summary(self, engine):
        summary = engine.get_v46_summary()
        assert 'sentiment_data' in summary
        assert 'correlation_pairs' in summary