"""Test Suite for V45.0 Advanced Orders
Comprehensive testing of conditional orders, iceberg orders,
TWAP orders, and position snapshots.
"""

import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.auto_execution_engine import (
    AutoExecutionEngine,
    ConditionalOrder,
    IcebergOrder,
    TWAPOrder,
    PositionSnapshot
)


class TestV45_0Config:
    """Test suite for V45.0 Config"""

    @pytest.fixture
    def engine(self):
        config = {
            'enable_conditional_orders': True,
            'enable_iceberg': True,
            'enable_twap': True
        }
        return AutoExecutionEngine(config=config)

    def test_v45_config(self, engine):
        assert engine.run_config.enable_conditional_orders is True
        assert engine.run_config.enable_iceberg is True
        assert engine.run_config.enable_twap is True


class TestV45_0ConditionalOrders:
    """Test suite for Conditional Orders"""

    @pytest.fixture
    def engine(self):
        return AutoExecutionEngine(config={'enable_conditional_orders': True})

    def test_create_conditional_order(self, engine):
        order = engine.create_conditional_order(
            parent_order_id="parent1",
            condition_type="stop_loss",
            trigger_price=44000.0,
            side="sell",
            quantity=0.5
        )
        assert isinstance(order, ConditionalOrder)
        assert order.condition_type == "stop_loss"

    def test_check_conditional_trigger(self, engine):
        engine.create_conditional_order("p1", "stop_loss", 44000, "sell", 0.5)
        triggered = engine.check_conditional_trigger(43500)
        assert len(triggered) > 0


class TestV45_0IcebergOrders:
    """Test suite for Iceberg Orders"""

    @pytest.fixture
    def engine(self):
        return AutoExecutionEngine(config={'enable_iceberg': True})

    def test_create_iceberg_order(self, engine):
        order = engine.create_iceberg_order("BTC/USDT", "buy", 10.0, 1.0, 45000)
        assert isinstance(order, IcebergOrder)
        assert order.total_quantity == 10.0


class TestV45_0TWAPOrders:
    """Test suite for TWAP Orders"""

    @pytest.fixture
    def engine(self):
        return AutoExecutionEngine(config={'enable_twap': True})

    def test_create_twap_order(self, engine):
        order = engine.create_twap_order("BTC/USDT", "buy", 5.0, 10, 60)
        assert isinstance(order, TWAPOrder)
        assert order.slice_count == 10


class TestV45_0PositionSnapshots:
    """Test suite for Position Snapshots"""

    @pytest.fixture
    def engine(self):
        return AutoExecutionEngine()

    def test_take_snapshot(self, engine):
        engine.add_to_portfolio("BTC", 0.5, 45000, 46000)
        snapshot = engine.take_position_snapshot("BTC")
        assert isinstance(snapshot, PositionSnapshot)
        assert snapshot.pnl > 0


class TestV45_0Summary:
    """Test suite for V45 Summary"""

    @pytest.fixture
    def engine(self):
        return AutoExecutionEngine()

    def test_v45_summary(self, engine):
        summary = engine.get_v45_summary()
        assert 'conditional_orders' in summary
        assert 'iceberg_orders' in summary