"""Tests for V58.0 Order Management System."""

import pytest
import asyncio

from deepagents_crypto_trading import (
    OrderManager,
    OrderExecutionSimulator,
    OrderStatus,
    OrderTimeInForce,
    CryptoTradingSystem,
    TradingConfig,
)


class TestOrderManager:
    """Tests for OrderManager."""

    def test_create_market_order(self) -> None:
        """Test creating a market order."""
        om = OrderManager()
        order = om.create_market_order(
            symbol="BTCUSDT", side="buy", quantity=0.1
        )

        assert order.symbol == "BTCUSDT"
        assert order.side == "buy"
        assert order.quantity == 0.1
        assert order.order_type == "market"
        assert order.status == OrderStatus.PENDING

    def test_create_limit_order(self) -> None:
        """Test creating a limit order."""
        om = OrderManager()
        order = om.create_limit_order(
            symbol="ETHUSDT",
            side="sell",
            quantity=1.0,
            price=2000.0,
            time_in_force=OrderTimeInForce.GTC,
        )

        assert order.symbol == "ETHUSDT"
        assert order.side == "sell"
        assert order.quantity == 1.0
        assert order.price == 2000.0
        assert order.order_type == "limit"
        assert order.status == OrderStatus.PENDING

    def test_get_order(self) -> None:
        """Test getting an order by ID."""
        om = OrderManager()
        order = om.create_market_order(
            symbol="BTCUSDT", side="buy", quantity=0.1
        )

        retrieved = om.get_order(order.id)
        assert retrieved is not None
        assert retrieved.id == order.id

    def test_cancel_order(self) -> None:
        """Test canceling an order."""
        om = OrderManager()
        order = om.create_market_order(
            symbol="BTCUSDT", side="buy", quantity=0.1
        )

        result = om.cancel_order(order.id)
        assert result is True
        assert om.get_order(order.id).status == OrderStatus.CANCELLED

    def test_get_pending_orders(self) -> None:
        """Test getting pending orders."""
        om = OrderManager()
        om.create_market_order(symbol="BTCUSDT", side="buy", quantity=0.1)
        om.create_market_order(symbol="ETHUSDT", side="buy", quantity=1.0)

        pending = om.get_pending_orders()
        assert len(pending) == 2

    def test_order_statistics(self) -> None:
        """Test getting order statistics."""
        om = OrderManager()

        # Create and fill some orders
        order1 = om.create_market_order(symbol="BTCUSDT", side="buy", quantity=0.1)
        order2 = om.create_market_order(symbol="ETHUSDT", side="buy", quantity=1.0)

        # Update one as filled
        om.update_order(
            order1.id,
            filled_quantity=0.1,
            average_fill_price=50000.0,
            status=OrderStatus.FILLED,
        )

        stats = om.get_order_statistics()
        assert stats["total_orders"] == 2
        assert stats["filled_orders"] == 1
        assert stats["pending_orders"] == 1


class TestOrderExecutionSimulator:
    """Tests for OrderExecutionSimulator."""

    @pytest.mark.asyncio
    async def test_execute_market_order(self) -> None:
        """Test executing a market order."""
        om = OrderManager()
        simulator = OrderExecutionSimulator(om)

        order = om.create_market_order(
            symbol="BTCUSDT", side="buy", quantity=0.1
        )

        result = await simulator.execute_market_order(
            order_id=order.id,
            fill_price=50000.0,
            fee_pct=0.001,
        )

        assert result is True
        filled_order = om.get_order(order.id)
        assert filled_order is not None
        assert filled_order.status == OrderStatus.FILLED
        assert filled_order.average_fill_price == 50000.0


class TestCryptoTradingSystemV58:
    """Tests for V58.0 CryptoTradingSystem integration."""

    @pytest.mark.asyncio
    async def test_order_execution(self) -> None:
        """Test executing an order through the system."""
        system = CryptoTradingSystem()

        order_id = await system.execute_order(
            symbol="BTCUSDT",
            side="buy",
            quantity=0.1,
            order_type="market",
        )

        assert order_id is not None
        assert order_id.startswith("ord_")

    @pytest.mark.asyncio
    async def test_system_status_with_orders(self) -> None:
        """Test system status includes orders."""
        system = CryptoTradingSystem()

        await system.execute_order(
            symbol="BTCUSDT", side="buy", quantity=0.1
        )

        status = system.get_status()
        assert "orders" in status
        assert status["version"] == "0.4.0"

    @pytest.mark.asyncio
    async def test_memo_order_storage(self) -> None:
        """Test memo0 order storage."""
        config = TradingConfig(memo0_enabled=True)
        system = CryptoTradingSystem(config)

        order_id = await system.execute_order(
            symbol="BTCUSDT", side="buy", quantity=0.1
        )

        # Check memo0 stats
        stats = system.memo_client.get_stats()
        assert "total_orders" in stats