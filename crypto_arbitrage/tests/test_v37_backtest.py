"""Test Suite for V37.0 Backtesting Engine
Comprehensive testing of backtesting engine,
strategy backtest, and performance metrics.
"""

import pytest
import time
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.auto_execution_engine import (
    AutoExecutionEngine,
    BacktestTrade,
    BacktestResult,
    CandleData
)


class TestV37_0BacktestingConfig:
    """Test suite for Backtesting Config - V37.0"""

    @pytest.fixture
    def engine(self):
        """Create engine with backtesting config"""
        config = {
            'enable_backtesting': True,
            'backtest_initial_capital': 10000.0,
            'backtest_fee_rate': 0.0004
        }
        return AutoExecutionEngine(config=config)

    def test_backtest_config(self, engine):
        """Test backtesting configuration"""
        assert engine.run_config.enable_backtesting is True
        assert engine.run_config.backtest_initial_capital == 10000.0
        assert engine.run_config.backtest_fee_rate == 0.0004


class TestV37_0CandleData:
    """Test suite for Candle Data - V37.0"""

    @pytest.fixture
    def engine(self):
        """Create engine"""
        return AutoExecutionEngine()

    def test_add_candle_data(self, engine):
        """Test adding candle data"""
        candle = CandleData(
            timestamp=time.time(),
            open=45000.0,
            high=45500.0,
            low=44800.0,
            close=45200.0,
            volume=100.0
        )
        engine.add_candle_data("BTC/USDT", candle)

        assert hasattr(engine, '_candle_data')
        assert "BTC/USDT" in engine._candle_data

    def test_add_candle_batch(self, engine):
        """Test batch adding candle data"""
        candles = [
            {'timestamp': 1000, 'open': 45000, 'high': 45500, 'low': 44800, 'close': 45200, 'volume': 100},
            {'timestamp': 2000, 'open': 45200, 'high': 45800, 'low': 45000, 'close': 45500, 'volume': 150}
        ]
        engine.add_candle_batch("ETH/USDT", candles)

        assert len(engine._candle_data["ETH/USDT"]) == 2


class TestV37_0BacktestTrade:
    """Test suite for Backtest Trade - V37.0"""

    @pytest.fixture
    def engine(self):
        """Create engine"""
        return AutoExecutionEngine(config={'backtest_initial_capital': 10000.0})

    def test_execute_backtest_trade(self, engine):
        """Test executing backtest trade"""
        trade = engine.execute_backtest_trade(
            symbol="BTC/USDT",
            side="buy",
            price=45000.0,
            quantity=0.1,
            timestamp=time.time()
        )

        assert trade.symbol == "BTC/USDT"
        assert trade.side == "buy"
        assert trade.quantity == 0.1

    def test_backtest_equity_update(self, engine):
        """Test equity is updated after trade"""
        initial_equity = engine._backtest_equity

        engine.execute_backtest_trade(
            symbol="BTC/USDT",
            side="buy",
            price=45000.0,
            quantity=0.1,
            timestamp=time.time()
        )

        assert engine._backtest_equity < initial_equity


class TestV37_0BacktestResult:
    """Test suite for Backtest Result - V37.0"""

    @pytest.fixture
    def engine(self):
        """Create engine"""
        return AutoExecutionEngine(config={'backtest_initial_capital': 10000.0})

    def test_calculate_backtest_result(self, engine):
        """Test calculating backtest result"""
        # Add some trades
        engine.execute_backtest_trade("BTC/USDT", "buy", 45000.0, 0.1, 1000)
        engine.execute_backtest_trade("BTC/USDT", "sell", 46000.0, 0.1, 2000)

        # Calculate result
        candles = [
            {'timestamp': 1000, 'open': 45000, 'close': 45000},
            {'timestamp': 2000, 'open': 46000, 'close': 46000}
        ]
        result = engine.calculate_backtest_result("test_strategy", "BTC/USDT", candles)

        assert result.strategy_name == "test_strategy"
        assert result.total_trades == 2

    def test_get_backtest_result(self, engine):
        """Test getting backtest result"""
        # Add some trades and calculate
        engine.execute_backtest_trade("BTC/USDT", "buy", 45000.0, 0.1, 1000)
        candles = [{'timestamp': 1000, 'open': 45000, 'close': 45000}]
        result = engine.calculate_backtest_result("momentum", "BTC/USDT", candles)
        engine._backtest_results["momentum"] = result

        retrieved = engine.get_backtest_result("momentum")
        assert retrieved is not None


class TestV37_0StrategyBacktest:
    """Test suite for Strategy Backtest - V37.0"""

    @pytest.fixture
    def engine(self):
        """Create engine"""
        return AutoExecutionEngine(config={'backtest_initial_capital': 10000.0})

    def test_run_simple_backtest(self, engine):
        """Test running simple strategy backtest"""
        # 简单的动量策略函数
        def momentum_strategy(candle, position):
            if position is None:
                return "buy"
            elif candle.close < position['entry_price'] * 0.95:
                return "sell"
            return "hold"

        # 生成测试K线数据
        candles = []
        base_price = 45000.0
        for i in range(20):
            candles.append({
                'timestamp': 1000 + i * 3600,
                'open': base_price,
                'high': base_price * 1.01,
                'low': base_price * 0.99,
                'close': base_price * 1.005,
                'volume': 100
            })
            base_price *= 1.005

        # 运行回测
        result = engine.run_backtest(
            strategy_name="momentum_test",
            symbol="BTC/USDT",
            candles=candles,
            strategy_func=momentum_strategy
        )

        assert result is not None
        assert result.strategy_name == "momentum_test"
        assert result.total_trades > 0


class TestV37_0PerformanceMetrics:
    """Test suite for Performance Metrics - V37.0"""

    @pytest.fixture
    def engine(self):
        """Create engine"""
        return AutoExecutionEngine(config={'backtest_initial_capital': 10000.0})

    def test_sharpe_ratio(self, engine):
        """Test Sharpe ratio calculation"""
        # 运行有正收益的回测
        def profitable_strategy(candle, position):
            if position is None:
                return "buy"
            return "sell"

        candles = [
            {'timestamp': i * 3600, 'open': 45000 + i * 100, 'close': 45050, 'volume': 100}
            for i in range(10)
        ]

        result = engine.run_backtest(
            "profitable",
            "BTC/USDT",
            candles,
            profitable_strategy
        )

        assert result.sharpe_ratio >= 0

    def test_max_drawdown(self, engine):
        """Test max drawdown calculation"""
        engine._backtest_equity = 10000.0
        engine._backtest_trades = [
            BacktestTrade(trade_id="1", pnl_pct=0.05),
            BacktestTrade(trade_id="2", pnl_pct=-0.03),
            BacktestTrade(trade_id="3", pnl_pct=0.02)
        ]

        candles = [{'timestamp': i, 'close': 45000} for i in range(3)]
        result = engine.calculate_backtest_result("dd_test", "BTC/USDT", candles)

        assert result.max_drawdown >= 0


class TestV37_0V37Summary:
    """Test suite for V37 Summary - V37.0"""

    @pytest.fixture
    def engine(self):
        """Create engine"""
        config = {
            'enable_backtesting': True,
            'backtest_initial_capital': 10000.0
        }
        return AutoExecutionEngine(config=config)

    def test_v37_summary(self, engine):
        """Test V37.0 summary"""
        summary = engine.get_v37_summary()

        assert 'backtest_results' in summary
        assert 'backtest_trades' in summary
        assert 'backtest_equity' in summary
        assert 'results' in summary

    def test_all_features_initialized(self, engine):
        """Test all V37.0 features are initialized"""
        assert engine._backtest_results is not None
        assert engine._backtest_trades is not None
        assert engine._backtest_equity > 0