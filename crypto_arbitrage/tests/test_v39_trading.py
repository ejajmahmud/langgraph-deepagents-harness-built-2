"""Test Suite for V39.0 Real Trading
Comprehensive testing of real trading engine,
exchange configuration, order management,
and trade signals.
"""

import pytest
import time
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.auto_execution_engine import (
    AutoExecutionEngine,
    OrderRecord,
    ExchangeConfig,
    TradeSignal
)


class TestV39_0TradingConfig:
    """Test suite for Real Trading Config - V39.0"""

    @pytest.fixture
    def engine(self):
        """Create engine with real trading config"""
        config = {
            'enable_real_trading': True,
            'default_exchange': 'binance',
            'testnet_mode': True,
            'max_order_size': 1.0,
            'order_timeout': 30
        }
        return AutoExecutionEngine(config=config)

    def test_trading_config(self, engine):
        """Test real trading configuration"""
        assert engine.run_config.enable_real_trading is True
        assert engine.run_config.default_exchange == 'binance'
        assert engine.run_config.testnet_mode is True


class TestV39_0ExchangeConfig:
    """Test suite for Exchange Configuration - V39.0"""

    @pytest.fixture
    def engine(self):
        """Create engine"""
        return AutoExecutionEngine()

    def test_configure_exchange(self, engine):
        """Test configuring exchange"""
        result = engine.configure_exchange(
            exchange="binance",
            api_key="test_key",
            api_secret="test_secret",
            testnet=True,
            fee_tier=0.0004
        )

        assert result is True
        assert "binance" in engine._exchange_configs

    def test_get_exchange_config(self, engine):
        """Test getting exchange config"""
        engine.configure_exchange("bybit", fee_tier=0.0006)
        config = engine.get_exchange_config("bybit")

        assert config is not None
        assert config.exchange == "bybit"
        assert config.fee_tier == 0.0006


class TestV39_0OrderManagement:
    """Test suite for Order Management - V39.0"""

    @pytest.fixture
    def engine(self):
        """Create engine"""
        return AutoExecutionEngine()

    def test_create_limit_order(self, engine):
        """Test creating limit order"""
        order = engine.create_order(
            symbol="BTC/USDT",
            side="buy",
            order_type="limit",
            quantity=0.5,
            price=45000.0
        )

        assert order.symbol == "BTC/USDT"
        assert order.side == "buy"
        assert order.quantity == 0.5

    def test_create_market_order(self, engine):
        """Test creating market order"""
        order = engine.create_order(
            symbol="ETH/USDT",
            side="sell",
            order_type="market",
            quantity=1.0
        )

        assert order.order_type == "market"
        assert order.price == 0.0

    def test_simulate_fill_order(self, engine):
        """Test order filling simulation"""
        order = engine.create_order(
            symbol="BTC/USDT",
            side="buy",
            order_type="limit",
            quantity=0.1,
            price=45000
        )

        result = engine.simulate_fill_order(order.order_id, 45100.0)

        assert result is True
        assert order.status == "filled"
        assert order.avg_fill_price == 45100.0

    def test_get_order(self, engine):
        """Test getting order"""
        order = engine.create_order(
            symbol="BTC/USDT",
            side="buy",
            order_type="limit",
            quantity=0.1,
            price=45000
        )

        retrieved = engine.get_order(order.order_id)
        assert retrieved is not None

    def test_get_open_orders(self, engine):
        """Test getting open orders"""
        engine.create_order("BTC/USDT", "buy", "limit", 0.1, 45000)
        engine.create_order("ETH/USDT", "sell", "limit", 1.0, 2500)

        open_orders = engine.get_open_orders()
        assert len(open_orders) >= 2

    def test_get_order_history(self, engine):
        """Test getting order history"""
        engine.create_order("BTC/USDT", "buy", "limit", 0.1, 45000)
        engine.create_order("ETH/USDT", "sell", "limit", 1.0, 2500)

        history = engine.get_order_history(limit=10)
        assert len(history) == 2


class TestV39_0TradeSignals:
    """Test suite for Trade Signals - V39.0"""

    @pytest.fixture
    def engine(self):
        """Create engine"""
        return AutoExecutionEngine()

    def test_generate_trade_signal(self, engine):
        """Test generating trade signal"""
        signal = engine.generate_trade_signal(
            symbol="BTC/USDT",
            action="buy",
            entry_price=45000,
            stop_loss=44000,
            take_profit=47000,
            quantity=0.5,
            confidence=0.8,
            strategy="momentum"
        )

        assert signal.symbol == "BTC/USDT"
        assert signal.action == "buy"
        assert signal.strategy == "momentum"

    def test_get_trade_signals(self, engine):
        """Test getting trade signals"""
        engine.generate_trade_signal(
            symbol="BTC/USDT",
            action="buy",
            entry_price=45000,
            stop_loss=44000,
            take_profit=47000,
            quantity=0.5,
            confidence=0.8,
            strategy="mean_reversion"
        )

        signals = engine.get_trade_signals(limit=5)
        assert len(signals) >= 1


class TestV39_0V39Summary:
    """Test suite for V39 Summary - V39.0"""

    @pytest.fixture
    def engine(self):
        """Create engine"""
        config = {'enable_real_trading': True}
        return AutoExecutionEngine(config=config)

    def test_v39_summary(self, engine):
        """Test V39.0 summary"""
        summary = engine.get_v39_summary()

        assert 'exchangesConfigured' in summary
        assert 'order_records' in summary
        assert 'trade_signals' in summary

    def test_all_features_initialized(self, engine):
        """Test all V39.0 features are initialized"""
        assert engine._exchange_configs is not None
        assert engine._order_records is not None
        assert engine._trade_signals is not None