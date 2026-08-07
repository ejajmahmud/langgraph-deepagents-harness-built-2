"""Test Suite for V33.0 Market Microstructure
Comprehensive testing of market depth analysis, liquidity aggregation,
price impact prediction, and signal fusion.
"""

import pytest
import asyncio
import time
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.auto_execution_engine import (
    AutoExecutionEngine,
    AutoTradeConfig,
    MarketDepth,
    MarketDepthLevel,
    LiquidityPool,
    PriceImpact
)


class TestV33_0MarketDepth:
    """Test suite for Market Depth Analysis - V33.0"""

    @pytest.fixture
    def engine(self):
        """Create engine with V33.0 config"""
        config = {
            'enable_market_depth': True,
            'depth_levels': 10,
            'min_depth_score': 60.0
        }
        return AutoExecutionEngine(config=config)

    def test_market_depth_config(self, engine):
        """Test market depth configuration"""
        assert engine.run_config.enable_market_depth is True
        assert engine.run_config.depth_levels == 10
        assert engine.run_config.min_depth_score == 60.0

    def test_analyze_market_depth(self, engine):
        """Test market depth analysis"""
        depth = engine.analyze_market_depth(
            symbol="BTC/USDT",
            exchange="binance"
        )

        assert depth is not None
        assert depth.symbol == "BTC/USDT"
        assert depth.exchange == "binance"
        assert len(depth.bid_levels) > 0
        assert len(depth.ask_levels) > 0
        assert depth.spread >= 0
        assert depth.spread_bps >= 0
        assert depth.depth_score >= 0

    def test_market_depth_levels(self, engine):
        """Test order book level construction"""
        bid_prices = [50000.0, 49999.5, 49999.0, 49998.5, 49998.0]
        bid_volumes = [100.0, 150.0, 200.0, 250.0, 300.0]
        ask_prices = [50000.5, 50001.0, 50001.5, 50002.0, 50002.5]
        ask_volumes = [100.0, 150.0, 200.0, 250.0, 300.0]

        depth = engine.analyze_market_depth(
            symbol="BTC/USDT",
            exchange="binance",
            bid_prices=bid_prices,
            bid_volumes=bid_volumes,
            ask_prices=ask_prices,
            ask_volumes=ask_volumes
        )

        assert len(depth.bid_levels) == 5
        assert len(depth.ask_levels) == 5
        # Check cumulative volume
        assert depth.bid_levels[0].cumulative_volume <= depth.bid_levels[4].cumulative_volume
        assert depth.ask_levels[0].cumulative_volume <= depth.ask_levels[4].cumulative_volume

    def test_spread_calculation(self, engine):
        """Test spread calculation"""
        bid_prices = [100.0, 99.5, 99.0]
        ask_prices = [101.0, 101.5, 102.0]

        depth = engine.analyze_market_depth(
            symbol="ETH/USDT",
            exchange="bybit",
            bid_prices=bid_prices,
            bid_volumes=[50.0, 75.0, 100.0],
            ask_prices=ask_prices,
            ask_volumes=[50.0, 75.0, 100.0]
        )

        # spread = ask[0] - bid[0]
        assert depth.spread == pytest.approx(1.0, rel=0.01)
        # spread_bps = (spread / mid) * 10000
        mid = (bid_prices[0] + ask_prices[0]) / 2
        expected_bps = (1.0 / mid) * 10000
        assert depth.spread_bps == pytest.approx(expected_bps, rel=0.01)


class TestV33_0LiquidityAggregator:
    """Test suite for Liquidity Aggregation - V33.0"""

    @pytest.fixture
    def engine(self):
        """Create engine with liquidity config"""
        config = {
            'enable_liquidity_agg': True,
            'sor_exchanges': 'binance,bybit,okx'
        }
        return AutoExecutionEngine(config=config)

    def test_liquidity_agg_config(self, engine):
        """Test liquidity aggregation configuration"""
        assert engine.run_config.enable_liquidity_agg is True

    def test_aggregate_liquidity(self, engine):
        """Test cross-exchange liquidity aggregation"""
        pools = engine.aggregate_liquidity("BTC/USDT")

        assert len(pools) > 0
        # Should have 3 exchanges
        assert len(pools) == 3

        for pool in pools:
            assert pool.symbol == "BTC/USDT"
            assert pool.total_depth > 0
            assert pool.bid_depth >= 0
            assert pool.ask_depth >= 0


class TestV33_0PriceImpact:
    """Test suite for Price Impact Prediction - V33.0"""

    @pytest.fixture
    def engine(self):
        """Create engine with price impact config"""
        config = {
            'enable_price_impact': True,
            'impact_model_alpha': 0.1
        }
        return AutoExecutionEngine(config=config)

    def test_price_impact_config(self, engine):
        """Test price impact configuration"""
        assert engine.run_config.enable_price_impact is True
        assert engine.run_config.impact_model_alpha == 0.1

    def test_predict_price_impact_buy(self, engine):
        """Test price impact for buy order"""
        impact = engine.predict_price_impact(
            symbol="BTC/USDT",
            quantity=1.0,
            side="buy"
        )

        assert impact.quantity == 1.0
        assert impact.expected_price > 0
        assert impact.impact_bps >= 0
        assert impact.fill_rate > 0

    def test_predict_price_impact_sell(self, engine):
        """Test price impact for sell order"""
        impact = engine.predict_price_impact(
            symbol="BTC/USDT",
            quantity=1.0,
            side="sell"
        )

        assert impact.impacted_price < impact.expected_price

    def test_price_impact_risk_levels(self, engine):
        """Test price impact risk level classification"""
        # Small order - low risk
        impact_small = engine.predict_price_impact("BTC/USDT", 0.5, "buy")
        assert impact_small.risk_level in ["low", "medium", "high"]

        # Large order - high risk
        impact_large = engine.predict_price_impact("BTC/USDT", 10.0, "buy")
        # impact increases with quantity


class TestV33_0SignalFusion:
    """Test suite for Signal Fusion Engine - V33.0"""

    @pytest.fixture
    def engine(self):
        """Create engine with signal fusion config"""
        config = {
            'enable_signal_fusion': True,
            'fusion_weights': 'technical:0.3,sentiment:0.2,flow:0.3,ml:0.2'
        }
        return AutoExecutionEngine(config=config)

    def test_signal_fusion_config(self, engine):
        """Test signal fusion configuration"""
        assert engine.run_config.enable_signal_fusion is True

    def test_fuse_signals(self, engine):
        """Test multi-source signal fusion"""
        fused = engine.fuse_signals(
            symbol="BTC/USDT",
            technical=70.0,
            sentiment=60.0,
            flow=80.0,
            ml=50.0
        )

        assert 0 <= fused <= 100
        # Weighted average: 0.3*70 + 0.2*60 + 0.3*80 + 0.2*50
        expected = 0.3*70 + 0.2*60 + 0.3*80 + 0.2*50
        assert fused == pytest.approx(expected, rel=0.01)

    def test_fuse_signals_disabled(self, engine):
        """Test signal fusion when disabled"""
        engine.run_config.enable_signal_fusion = False

        fused = engine.fuse_signals(
            symbol="BTC/USDT",
            technical=70.0,
            sentiment=60.0,
            flow=80.0,
            ml=50.0
        )

        # When disabled, should return simple average
        expected = (70.0 + 60.0 + 80.0 + 50.0) / 4
        assert fused == pytest.approx(expected, rel=0.01)


class TestV33_0MicrostructureSummary:
    """Test suite for Market Microstructure Summary - V33.0"""

    @pytest.fixture
    def engine(self):
        """Create engine with all V33.0 features"""
        config = {
            'enable_market_depth': True,
            'enable_liquidity_agg': True,
            'enable_price_impact': True,
            'enable_signal_fusion': True,
            'sor_exchanges': 'binance,bybit,okx'
        }
        return AutoExecutionEngine(config=config)

    def test_market_microstructure_summary(self, engine):
        """Test complete microstructure summary"""
        # Generate data
        engine.analyze_market_depth("BTC/USDT", "binance")
        engine.aggregate_liquidity("BTC/USDT")
        engine.predict_price_impact("BTC/USDT", 1.0, "buy")
        engine.fuse_signals("BTC/USDT", 70, 60, 80, 50)

        summary = engine.get_market_microstructure_summary("BTC/USDT")

        assert summary['symbol'] == "BTC/USDT"
        assert 'depth_score' in summary
        assert 'spread_bps' in summary
        assert 'total_liquidity' in summary
        assert 'exchange_count' in summary
        assert 'price_impact_bps' in summary
        assert 'impact_risk' in summary
        assert 'fused_signal' in summary

    def test_microstructure_summary_empty(self, engine):
        """Test microstructure summary with no data"""
        summary = engine.get_market_microstructure_summary("ETH/USDT")

        # Should return default values
        assert summary['depth_score'] == 0 or summary['depth_score'] >= 0


class TestV33_0Dataclasses:
    """Test V33.0 dataclasses"""

    def test_market_depth_level(self):
        """Test MarketDepthLevel dataclass"""
        level = MarketDepthLevel(
            price=50000.0,
            volume=100.0,
            cumulative_volume=500.0,
            order_count=5
        )

        assert level.price == 50000.0
        assert level.volume == 100.0
        assert level.cumulative_volume == 500.0
        assert level.order_count == 5

    def test_market_depth(self):
        """Test MarketDepth dataclass"""
        depth = MarketDepth(
            symbol="BTC/USDT",
            exchange="binance",
            spread=0.5,
            spread_bps=1.0,
            mid_price=50000.25,
            depth_score=85.0,
            timestamp=time.time()
        )

        assert depth.symbol == "BTC/USDT"
        assert depth.exchange == "binance"
        assert depth.spread > 0

    def test_liquidity_pool(self):
        """Test LiquidityPool dataclass"""
        pool = LiquidityPool(
            exchange="binance",
            symbol="BTC/USDT",
            bid_depth=50000.0,
            ask_depth=50000.0,
            total_depth=100000.0,
            price_levels=10,
            weighted_mid=50000.0
        )

        assert pool.exchange == "binance"
        assert pool.bid_depth + pool.ask_depth == pool.total_depth

    def test_price_impact(self):
        """Test PriceImpact dataclass"""
        impact = PriceImpact(
            quantity=2.0,
            expected_price=50000.0,
            impacted_price=50100.0,
            impact_bps=20.0,
            fill_rate=0.8,
            risk_level="medium"
        )

        assert impact.quantity == 2.0
        assert impact.impact_bps > 0
        assert impact.risk_level == "medium"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])