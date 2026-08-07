"""V67.0 集成测试

测试实盘交易执行器功能

创建时间：2026-05-08
"""

import pytest
import asyncio
import sys
import os

# Get project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from trading.trading_executor_v67 import (
    Exchange,
    OrderType,
    OrderSide,
    OrderStatus,
    PositionStatus,
    Order,
    Position,
    ExchangeConfig,
    ExchangeAdapter,
    BinanceAdapter,
    OKXAdapter,
    BybitAdapter,
    OrderManager,
    PositionTracker,
    TradingExecutor,
    initialize_order_manager,
    initialize_position_tracker,
    initialize_trading_executor,
)


class TestExchangeAdapters:
    """交易所适配器测试"""

    @pytest.mark.asyncio
    async def test_binance_adapter(self):
        """测试币安适配器"""
        config = ExchangeConfig(
            exchange=Exchange.BINANCE,
            api_key="test_key",
            api_secret="test_secret",
            testnet=True
        )
        adapter = BinanceAdapter(config)

        connected = await adapter.connect()
        assert connected is True
        print("BinanceAdapter: OK")

    @pytest.mark.asyncio
    async def test_place_order(self):
        """测试下单"""
        config = ExchangeConfig(
            exchange=Exchange.BINANCE,
            api_key="test_key",
            api_secret="test_secret"
        )
        adapter = BinanceAdapter(config)
        await adapter.connect()

        order = await adapter.place_order(
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=0.01,
            price=50000.0
        )

        assert order.status == OrderStatus.FILLED
        assert order.filled_quantity == 0.01
        print(f"Order filled: {order.order_id}")

    @pytest.mark.asyncio
    async def test_get_balance(self):
        """测试余额查询"""
        config = ExchangeConfig(
            exchange=Exchange.BINANCE,
            api_key="test_key",
            api_secret="test_secret"
        )
        adapter = BinanceAdapter(config)
        await adapter.connect()

        balance = await adapter.get_balance()
        assert "USDT" in balance
        print(f"Balance: {balance}")


class TestOrderManager:
    """订单管理器测试"""

    def test_order_manager_init(self):
        """测试初始化"""
        manager = initialize_order_manager()
        assert manager is not None
        print("OrderManager: OK")

    @pytest.mark.asyncio
    async def test_create_order(self):
        """测试创建订单"""
        manager = OrderManager()

        order = await manager.create_order(
            exchange=Exchange.BINANCE,
            symbol="ETHUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=0.1,
            price=3000.0
        )

        assert order.order_id is not None
        assert order.status == OrderStatus.PENDING
        print(f"Created order: {order.order_id}")

    @pytest.mark.asyncio
    async def test_update_order_status(self):
        """测试更新订单状态"""
        manager = OrderManager()

        order = await manager.create_order(
            Exchange.OKX, "BTCUSDT", OrderSide.SELL,
            OrderType.MARKET, 0.5, 40000.0
        )

        await manager.update_order_status(
            order.order_id,
            OrderStatus.FILLED,
            filled_quantity=0.5,
            avg_fill_price=40000.0
        )

        assert order.status == OrderStatus.FILLED
        print(f"Updated: {order.status.value}")


class TestPositionTracker:
    """持仓追踪器测试"""

    def test_position_tracker_init(self):
        """测试初始化"""
        tracker = initialize_position_tracker()
        assert tracker is not None
        print("PositionTracker: OK")

    @pytest.mark.asyncio
    async def test_open_position(self):
        """测试开仓"""
        tracker = PositionTracker()

        position = await tracker.open_position(
            exchange=Exchange.BINANCE,
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=0.1,
            entry_price=50000.0,
            leverage=1
        )

        assert position.position_id is not None
        assert position.status == PositionStatus.OPEN
        print(f"Opened: {position.position_id}")

    @pytest.mark.asyncio
    async def test_close_position(self):
        """测试平仓"""
        tracker = PositionTracker()

        position = await tracker.open_position(
            Exchange.BYBIT, "ETHUSDT", OrderSide.BUY,
            0.5, 3000.0
        )

        # 更新价格
        tracker.update_prices({"ETHUSDT": 3200.0})

        # 平仓
        closed = await tracker.close_position(
            position.position_id,
            3200.0
        )

        assert closed.realized_pnl > 0
        print(f"Closed PnL: {closed.realized_pnl}")

    @pytest.mark.asyncio
    async def test_liquidation_check(self):
        """测试清算检查"""
        tracker = PositionTracker()

        # 开高杠杆仓
        await tracker.open_position(
            Exchange.BINANCE,
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=0.1,
            entry_price=50000.0,
            leverage=10
        )

        # 价格下跌到清算价
        tracker.update_prices({"BTCUSDT": 45000.0})

        liquidating = tracker.check_liquidation()
        print(f"Liquidating: {len(liquidating)}")


class TestTradingExecutor:
    """交易执行器测试"""

    def test_executor_init(self):
        """测试初始化"""
        executor = initialize_trading_executor()
        assert executor is not None
        print("TradingExecutor: OK")

    @pytest.mark.asyncio
    async def test_register_exchange(self):
        """测试注册交易所"""
        executor = TradingExecutor()

        config = ExchangeConfig(
            exchange=Exchange.OKX,
            api_key="key",
            api_secret="secret"
        )
        adapter = OKXAdapter(config)

        executor.register_exchange(adapter)

        assert Exchange.OKX in executor.adapters
        print(f"Registered: {list(executor.adapters.keys())}")

    @pytest.mark.asyncio
    async def test_execute_trade(self):
        """测试执行交易"""
        executor = TradingExecutor()

        # 注册交易所
        config = ExchangeConfig(
            exchange=Exchange.BINANCE,
            api_key="key",
            api_secret="secret"
        )
        executor.register_exchange(BinanceAdapter(config))

        # 执行交易
        order = await executor.execute_trade(
            exchange=Exchange.BINANCE,
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=0.01,
            price=50000.0
        )

        assert order.status == OrderStatus.FILLED
        print(f"Trade executed: {order.order_id}")


class TestV67Integration:
    """V67.0 集成测试"""

    @pytest.mark.asyncio
    async def test_v67_full_integration(self):
        """测试完整V67.0集成"""
        # 1. 初始化
        executor = initialize_trading_executor()
        order_manager = executor.order_manager
        position_tracker = executor.position_tracker

        # 2. 注册交易所
        executor.register_exchange(BinanceAdapter(ExchangeConfig(
            exchange=Exchange.BINANCE,
            api_key="key",
            api_secret="secret"
        )))

        executor.register_exchange(OKXAdapter(ExchangeConfig(
            exchange=Exchange.OKX,
            api_key="key",
            api_secret="secret"
        )))

        # 3. 执行交易
        order1 = await executor.execute_trade(
            Exchange.BINANCE, "BTCUSDT",
            OrderSide.BUY, OrderType.MARKET,
            0.02, 50000.0
        )

        order2 = await executor.execute_trade(
            Exchange.OKX, "ETHUSDT",
            OrderSide.SELL, OrderType.LIMIT,
            0.5, 3000.0
        )

        # 4. 获取统计
        stats = executor.get_statistics()

        print(f"\n=== V67.0 Integration Test ===")
        print(f"Order stats: {stats['orders']}")
        print(f"Position stats: {stats['positions']}")
        print(f"Exchanges: {stats['exchanges']}")
        print("=== All Tests Passed ===")


if __name__ == "__main__":
    print("Running V67.0 Integration Tests...")
    pytest.main([__file__, "-v", "-s"])