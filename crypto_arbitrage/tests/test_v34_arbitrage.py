"""Test Suite for V34.0 Cross-Exchange Arbitrage & Margin Optimization
Comprehensive testing of arbitrage detection, margin pool management,
execution priority queue, and real-time P&L dashboard.
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
    ArbitrageOpportunity,
    MarginPosition,
    ExecutionTask,
    ProfitLoss
)


class TestV34_0Arbitrage:
    """Test suite for Cross-Exchange Arbitrage - V34.0"""

    @pytest.fixture
    def engine(self):
        """Create engine with arbitrage config"""
        config = {
            'enable_arbitrage': True,
            'arbitrage_min_spread': 0.002,
            'arbitrage_exchanges': 'binance,bybit,okx'
        }
        return AutoExecutionEngine(config=config)

    def test_arbitrage_config(self, engine):
        """Test arbitrage configuration"""
        assert engine.run_config.enable_arbitrage is True
        assert engine.run_config.arbitrage_min_spread == 0.002
        assert engine.run_config.arbitrage_exchanges == 'binance,bybit,okx'

    def test_scan_arbitrage(self, engine):
        """Test arbitrage scanning"""
        opportunities = engine.scan_cross_exchange_arbitrage("BTC/USDT")

        # Should return potential opportunities
        assert isinstance(opportunities, list)
        # Check if opportunities exist (depends on simulated prices)
        for opp in opportunities:
            assert opp.symbol == "BTC/USDT"
            assert opp.buy_exchange != opp.sell_exchange
            assert opp.spread_pct >= 0
            assert opp.score >= 0

    def test_get_arbitrage_opportunities(self, engine):
        """Test getting stored opportunities"""
        engine.scan_cross_exchange_arbitrage("BTC/USDT")
        opportunities = engine.get_arbitrage_opportunities()

        assert isinstance(opportunities, list)

    def test_arbitrage_disabled(self, engine):
        """Test arbitrage when disabled"""
        engine.run_config.enable_arbitrage = False

        opportunities = engine.scan_cross_exchange_arbitrage("BTC/USDT")
        assert len(opportunities) == 0


class TestV34_0MarginPool:
    """Test suite for Margin Pool Manager - V34.0"""

    @pytest.fixture
    def engine(self):
        """Create engine with margin pool config"""
        config = {
            'enable_margin_pool': True,
            'margin_pool_size': 100000.0,
            'margin_buffer_ratio': 0.2
        }
        return AutoExecutionEngine(config=config)

    def test_margin_pool_config(self, engine):
        """Test margin pool configuration"""
        assert engine.run_config.enable_margin_pool is True
        assert engine.run_config.margin_pool_size == 100000.0
        assert engine.run_config.margin_buffer_ratio == 0.2

    def test_init_margin_pool(self, engine):
        """Test margin pool initialization"""
        result = engine.init_margin_pool()

        assert result is True
        assert engine._margin_pool_available == 100000.0

    def test_init_margin_pool_disabled(self, engine):
        """Test margin pool when disabled"""
        engine.run_config.enable_margin_pool = False

        result = engine.init_margin_pool()
        assert result is False

    def test_allocate_margin(self, engine):
        """Test margin allocation"""
        engine.init_margin_pool()

        result = engine.allocate_margin("BTC/USDT", 10000.0)

        assert result is True
        assert engine._margin_pool_available == 90000.0
        assert "BTC/USDT" in engine._margin_positions

    def test_allocate_margin_insufficient(self, engine):
        """Test margin allocation with insufficient funds"""
        engine.init_margin_pool()

        # Try to allocate more than available (minus buffer)
        result = engine.allocate_margin("BTC/USDT", 90000.0)

        # Should fail because 20% buffer is required
        assert result is False

    def test_release_margin(self, engine):
        """Test margin release"""
        engine.init_margin_pool()
        engine.allocate_margin("BTC/USDT", 10000.0)

        released = engine.release_margin("BTC/USDT")

        assert released == 10000.0
        assert engine._margin_pool_available == 100000.0
        assert "BTC/USDT" not in engine._margin_positions

    def test_get_margin_pool_status(self, engine):
        """Test margin pool status"""
        engine.init_margin_pool()
        engine.allocate_margin("BTC/USDT", 10000.0)

        status = engine.get_margin_pool_status()

        assert status['total_pool'] == 100000.0
        assert status['used'] == 10000.0
        assert status['available'] == 90000.0
        assert status['position_count'] == 1
        assert 0 <= status['utilization'] <= 1


class TestV34_0ExecutionQueue:
    """Test suite for Execution Priority Queue - V34.0"""

    @pytest.fixture
    def engine(self):
        """Create engine with queue config"""
        config = {
            'enable_priority_queue': True,
            'max_queue_size': 10
        }
        return AutoExecutionEngine(config=config)

    def test_queue_config(self, engine):
        """Test queue configuration"""
        assert engine.run_config.enable_priority_queue is True
        assert engine.run_config.max_queue_size == 10

    def test_add_to_queue(self, engine):
        """Test adding task to queue"""
        result = engine.add_to_execution_queue(
            opportunity_id="opp_1",
            symbol="BTC/USDT",
            side="buy",
            quantity=1.0,
            score=80.0
        )

        assert result is True
        assert len(engine._execution_queue) == 1

    def test_add_to_queue_full(self, engine):
        """Test adding to full queue"""
        # Fill the queue
        for i in range(10):
            engine.add_to_execution_queue(
                opportunity_id=f"opp_{i}",
                symbol="BTC/USDT",
                side="buy",
                quantity=1.0,
                score=50.0
            )

        # Try to add one more
        result = engine.add_to_execution_queue(
            opportunity_id="opp_new",
            symbol="BTC/USDT",
            side="buy",
            quantity=1.0,
            score=50.0
        )

        assert result is False

    def test_priority_ordering(self, engine):
        """Test priority ordering"""
        # Add tasks with different priorities
        engine.add_to_execution_queue("opp_low", "BTC/USDT", "buy", 1.0, 30.0)
        engine.add_to_execution_queue("opp_high", "ETH/USDT", "buy", 1.0, 90.0)
        engine.add_to_execution_queue("opp_mid", "SOL/USDT", "buy", 1.0, 60.0)

        # First should be highest priority (90/10 = priority 9)
        next_task = engine.get_next_execution()
        assert next_task.symbol == "ETH/USDT"
        assert next_task.priority == 9

    def test_get_next_execution(self, engine):
        """Test getting next execution"""
        engine.add_to_execution_queue("opp_1", "BTC/USDT", "buy", 1.0, 70.0)

        task = engine.get_next_execution()

        assert task is not None
        assert task.symbol == "BTC/USDT"
        assert len(engine._execution_queue) == 0

    def test_get_queue_status(self, engine):
        """Test getting queue status"""
        engine.add_to_execution_queue("opp_1", "BTC/USDT", "buy", 1.0, 70.0)
        engine.add_to_execution_queue("opp_2", "ETH/USDT", "sell", 2.0, 50.0)

        status = engine.get_queue_status()

        assert status['queue_size'] == 2
        assert status['max_size'] == 10
        assert len(status['tasks']) == 2


class TestV34_0PnLDashboard:
    """Test suite for Real-Time P&L Dashboard - V34.0"""

    @pytest.fixture
    def engine(self):
        """Create engine with P&L dashboard config"""
        config = {
            'enable_pnl_dashboard': True,
            'pnl_update_interval': 5
        }
        return AutoExecutionEngine(config=config)

    def test_pnl_config(self, engine):
        """Test P&L configuration"""
        assert engine.run_config.enable_pnl_dashboard is True
        assert engine.run_config.pnl_update_interval == 5

    def test_update_pnl(self, engine):
        """Test P&L update"""
        engine.update_pnl(realized=100.0)

        assert engine._total_realized_pnl == 100.0
        assert engine._daily_pnl == 100.0

    def test_update_pnl_loss(self, engine):
        """Test P&L update with loss"""
        engine.update_pnl(realized=-50.0)

        assert engine._total_realized_pnl == -50.0
        assert engine._win_count == 0  # No win

    def test_win_count(self, engine):
        """Test win counting"""
        engine.update_pnl(realized=100.0)
        engine.update_pnl(realized=-50.0)
        engine.update_pnl(realized=200.0)

        assert engine._win_count == 2
        assert engine._trade_count == 3

    def test_get_pnl_summary(self, engine):
        """Test getting P&L summary"""
        engine.update_pnl(realized=500.0)

        summary = engine.get_pnl_summary()

        assert summary.realized_pnl == 500.0
        assert summary.total_pnl == 500.0  # realized only
        assert summary.daily_pnl == 500.0
        assert summary.trade_count == 1

    def test_win_rate(self, engine):
        """Test win rate calculation"""
        engine.update_pnl(realized=100.0)  # win
        engine.update_pnl(realized=-50.0)  # loss
        engine.update_pnl(realized=200.0)  # win

        summary = engine.get_pnl_summary()

        assert summary.win_rate == pytest.approx(2/3, rel=0.01)

    def test_commission(self, engine):
        """Test commission calculation"""
        # Make some trades
        for _ in range(5):
            engine.update_pnl(realized=10.0)

        summary = engine.get_pnl_summary()

        # 5 trades * $2 = $10 commission
        assert summary.commission == 10.0
        assert summary.net_pnl == 40.0  # 50 - 10


class TestV34_0Dataclasses:
    """Test V34.0 dataclasses"""

    def test_arbitrage_opportunity(self):
        """Test ArbitrageOpportunity dataclass"""
        opp = ArbitrageOpportunity(
            symbol="BTC/USDT",
            buy_exchange="binance",
            sell_exchange="bybit",
            buy_price=50000.0,
            sell_price=50100.0,
            spread_pct=0.002,
            potential_profit=20.0,
            score=80.0,
            timestamp=time.time()
        )

        assert opp.symbol == "BTC/USDT"
        assert opp.buy_exchange == "binance"
        assert opp.spread_pct > 0

    def test_margin_position(self):
        """Test MarginPosition dataclass"""
        pos = MarginPosition(
            symbol="BTC/USDT",
            exchange="binance",
            position_size=1.0,
            margin_used=1000.0,
            margin_ratio=0.1,
            timestamp=time.time()
        )

        assert pos.symbol == "BTC/USDT"
        assert pos.margin_used == 1000.0

    def test_execution_task(self):
        """Test ExecutionTask dataclass"""
        task = ExecutionTask(
            task_id="task_1",
            opportunity_id="opp_1",
            symbol="BTC/USDT",
            side="buy",
            quantity=1.0,
            priority=8,
            score=80.0,
            created_at=time.time()
        )

        assert task.task_id == "task_1"
        assert task.priority == 8

    def test_profit_loss(self):
        """Test ProfitLoss dataclass"""
        pnl = ProfitLoss(
            realized_pnl=500.0,
            unrealized_pnl=100.0,
            total_pnl=600.0,
            daily_pnl=500.0,
            commission=10.0,
            net_pnl=590.0,
            win_rate=0.66,
            trade_count=10,
            timestamp=time.time()
        )

        assert pnl.realized_pnl == 500.0
        assert pnl.net_pnl == 590.0
        assert pnl.trade_count == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])