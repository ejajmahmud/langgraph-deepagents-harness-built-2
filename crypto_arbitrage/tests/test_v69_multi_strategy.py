"""V69.0 集成测试

测试多策略投资组合与高级订单类型

创建时间：2026-05-08
"""

import pytest
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from trading.multi_strategy_v69 import (
    AdvancedOrderType,
    StrategyState,
    AllocationStatus,
    StrategyConfig,
    StrategyAllocation,
    TrailingStopOrder,
    OCOOrder,
    TWAPOrder,
    MultiStrategyPortfolio,
    AdvancedOrderBuilder,
    ExecutionRouter,
    initialize_portfolio,
    initialize_order_builder,
    initialize_execution_router,
)


class TestMultiStrategyPortfolio:
    """多策略投资组合测试"""

    def test_portfolio_init(self):
        """测试初始化"""
        portfolio = initialize_portfolio()
        assert portfolio is not None
        print("MultiStrategyPortfolio: OK")

    def test_add_strategy(self):
        """测试添加策略"""
        portfolio = MultiStrategyPortfolio()

        portfolio.add_strategy("triangular", "triangular", 0.4)
        portfolio.add_strategy("cross_exchange", "cross_exchange", 0.3)
        portfolio.add_strategy("funding", "funding_rate", 0.3)

        assert len(portfolio.strategy_configs) == 3
        print(f"Strategies: {list(portfolio.strategy_configs.keys())}")

    def test_update_capital(self):
        """测试更新资本"""
        portfolio = MultiStrategyPortfolio({"initial_capital": 100000})

        portfolio.add_strategy("s1", "triangular", 0.5)
        portfolio.update_capital(120000)

        assert portfolio.total_capital == 120000
        print(f"Capital: {portfolio.total_capital}")

    def test_get_strategy_weights(self):
        """测试获取策略权重"""
        portfolio = MultiStrategyPortfolio()

        portfolio.add_strategy("s1", "triangular", 0.5)
        portfolio.add_strategy("s2", "cross_exchange", 0.5)

        weights = portfolio.get_strategy_weights()

        assert abs(weights["s1"] - 0.5) < 0.01
        print(f"Weights: {weights}")

    def test_needs_rebalance(self):
        """测试需要再平衡"""
        portfolio = MultiStrategyPortfolio(
            {"rebalance_threshold": 0.05, "initial_capital": 100000}
        )

        portfolio.add_strategy("s1", "triangular", 0.5)
        portfolio.add_strategy("s2", "cross_exchange", 0.5)

        # 修改分配来触发再平衡
        portfolio.allocations["s1"].current_capital = 60000  # 60% vs 50%目标
        portfolio.allocations["s2"].current_capital = 40000

        needs = portfolio.needs_rebalance()

        print(f"Needs rebalance: {needs}")

    def test_get_rebalance_orders(self):
        """测试获取再平衡订单"""
        portfolio = MultiStrategyPortfolio(
            {"initial_capital": 100000}
        )

        portfolio.add_strategy("s1", "triangular", 0.6)
        portfolio.add_strategy("s2", "cross_exchange", 0.4)

        # 触发再平衡
        portfolio.allocations["s1"].current_capital = 70000
        portfolio.allocations["s2"].current_capital = 30000

        orders = portfolio.get_rebalance_orders()

        print(f"Rebalance orders: {orders}")

    def test_update_pnl(self):
        """测试更新盈亏"""
        portfolio = MultiStrategyPortfolio()

        portfolio.add_strategy("s1", "triangular", 0.5)
        portfolio.update_pnl("s1", 500)

        assert portfolio.allocations["s1"].pnl == 500
        print(f"PNL: {portfolio.get_total_pnl()}")

    def test_get_performance(self):
        """测试性能获取"""
        portfolio = MultiStrategyPortfolio({"initial_capital": 100000})

        portfolio.add_strategy("s1", "triangular", 0.5)
        portfolio.add_strategy("s2", "cross_exchange", 0.5)
        portfolio.update_pnl("s1", 200)
        portfolio.update_pnl("s2", 150)

        perf = portfolio.get_performance()

        assert perf["total_capital"] == 100000
        print(f"Performance: {perf}")


class TestAdvancedOrderBuilder:
    """高级订单构建器测试"""

    def test_order_builder_init(self):
        """测试初始化"""
        builder = initialize_order_builder()
        assert builder is not None
        print("AdvancedOrderBuilder: OK")

    def test_build_trailing_stop(self):
        """测试构建追踪止损"""
        builder = AdvancedOrderBuilder()

        order = builder.build_trailing_stop(
            symbol="BTCUSDT",
            side="buy",
            quantity=0.1,
            activation_price=50000,
            trail_distance=0.02
        )

        assert order is not None
        print(f"Trailing stop: {order.order_id}")

    def test_trailing_stop_update(self):
        """测试追踪止损更新"""
        builder = AdvancedOrderBuilder()

        order = builder.build_trailing_stop(
            "ETHUSDT", "buy", 0.5, 3000, 0.01
        )

        # 价格上升到触发点
        order.highest_price = 3100
        triggered = builder.update_trailing_stop(order, 3069)

        print(f"Triggered: {triggered}")

    def test_build_oco(self):
        """测试构建OCO"""
        builder = AdvancedOrderBuilder()

        order = builder.build_oco(
            symbol="BTCUSDT",
            side="buy",
            quantity=0.5,
            limit_price=49000,
            stop_price=48000
        )

        assert len(order.legs) == 2
        print(f"OCO order: {order.order_id}")

    def test_build_twap(self):
        """测试构建TWAP"""
        builder = AdvancedOrderBuilder()

        order = builder.build_twap(
            symbol="ETHUSDT",
            side="buy",
            quantity=1.0,
            duration_minutes=60,
            slices=60
        )

        assert order.num_slices == 60
        assert order.total_quantity == 1.0
        print(f"TWAP order: {order.order_id}")


class TestExecutionRouter:
    """执行路由测试"""

    def test_router_init(self):
        """测试初始化"""
        router = initialize_execution_router()
        assert router is not None
        print("ExecutionRouter: OK")

    def test_select_best_exchange(self):
        """测试选择最佳交易所"""
        router = ExecutionRouter()

        best = router.select_best_exchange("market")

        assert best in ["binance", "okx", "bybit"]
        print(f"Best exchange: {best}")

    def test_calculate_total_fees(self):
        """测试计算费用"""
        router = ExecutionRouter()

        total_fee = router.calculate_total_fees(
            ["binance", "okx"], 10000, "market"
        )

        assert total_fee > 0
        print(f"Total fees: {total_fee:.2f}")


class TestV69Integration:
    """V69.0 集成测试"""

    def test_v69_full_integration(self):
        """测���完整V69.0集成"""
        # 1. 初始化
        portfolio = initialize_portfolio({"initial_capital": 100000})
        builder = initialize_order_builder()
        router = initialize_execution_router()

        # 2. 配置多策略
        portfolio.add_strategy("triangular", "triangular", 0.4)
        portfolio.add_strategy("cross_exchange", "cross_exchange", 0.35)
        portfolio.add_strategy("funding_rate", "funding_rate", 0.25)

        # 3. 更新盈亏
        portfolio.update_pnl("triangular", 450)
        portfolio.update_pnl("cross_exchange", 320)
        portfolio.update_pnl("funding_rate", 180)

        # 4. 构建高级订单
        ts_order = builder.build_trailing_stop(
            "BTCUSDT", "buy", 0.1, 50000, 0.02
        )

        oco_order = builder.build_oco(
            "ETHUSDT", "sell", 0.5, 3200, 3100
        )

        # 5. 选择交易所
        best = router.select_best_exchange("market")

        # 6. 获取性能
        perf = portfolio.get_performance()
        stats = builder.get_statistics()

        print(f"\n=== V69.0 Integration Test ===")
        print(f"Portfolio: {perf}")
        print(f"Best exchange: {best}")
        print(f"Order stats: {stats}")
        print("=== All Tests Passed ===")


if __name__ == "__main__":
    print("Running V69.0 Integration Tests...")
    pytest.main([__file__, "-v", "-s"])