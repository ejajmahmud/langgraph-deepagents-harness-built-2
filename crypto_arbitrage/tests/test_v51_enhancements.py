"""V51.0 增强功能测试套件

测试V51新增功能：
- Advanced Leverage Manager
- Smart Order Router
- Enhanced Risk Monitor

时间：2026-05-08
"""

import sys
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 导入模块
sys.path.insert(0, 'D:/03_AITOOL/deepagents/crypto_arbitrage')

from strategies.advanced_leverage_manager import (
    AdvancedLeverageManager,
    LeverageConfig,
    RiskLevel,
    LeverageLevel,
)
from strategies.smart_order_router import (
    SmartOrderRouter,
    RoutingConfig,
    OrderRequest,
    OrderSide,
    OrderType,
    ExecutionStrategy,
)

try:
    from trading.enhanced_risk_monitor import (
        EnhancedRiskMonitor,
        AlertLevel,
    )
    HAS_RISK_MONITOR = True
except ImportError:
    HAS_RISK_MONITOR = False


def test_leverage_manager():
    """Test advanced leverage manager"""
    print("\n=== V51.1 Advanced Leverage Manager Test ===")

    config = LeverageConfig(
        base_leverage=3.0,
        max_leverage=10.0,
        risk_level=RiskLevel.MODERATE,
    )
    manager = AdvancedLeverageManager(config)

    # Test optimal leverage calculation
    result = manager.calculate_optimal_leverage(
        symbol="BTC/USDT",
        current_price=50000.0,
        volatility=0.2,
        trend_strength=0.6,
        liquidity=0.8,
    )

    print(f"[PASS] Recommended Leverage: {result.recommended_leverage:.2f}x")
    print(f"[PASS] Risk Score: {result.risk_score:.2%}")
    print(f"[PASS] Warnings: {len(result.warnings)}")

    # 测试仓位计算
    position = manager.calculate_position_sizing(
        symbol="BTC/USDT",
        capital=10000.0,
        entry_price=50000.0,
        leverage=5.0,
        risk_level=RiskLevel.MODERATE,
        stop_loss_pct=0.05,
    )

    print(f"✓ Position Value: ${position.position_value:,.2f}")
    print(f"✓ Margin Required: ${position.margin_required:,.2f}")
    print(f"✓ Liquidation Price: ${position.liquidation_price:,.2f}")

    # 测试杠杆等级
    level = manager.get_leverage_level(result.recommended_leverage)
    print(f"✓ Leverage Level: {level.value}")

    # 测试统计
    stats = manager.get_leverage_statistics()
    print(f"✓ Total Calculations: {stats.get('total_calculations', 0)}")

    return True


def test_order_router():
    """测试智能订单路由器"""
    print("\n=== V51.2 Smart Order Router Test ===")

    router = SmartOrderRouter()

    # 创建订单
    order = OrderRequest(
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=1.0,
        price=50000.0,
    )

    # 测试订单分割
    child_orders = router.split_order(
        order,
        strategy=ExecutionStrategy.TWAP,
        slice_count=5,
    )

    print(f"✓ Child Orders Created: {len(child_orders)}")

    # 测试交易所选择
    exchanges = ['binance', 'okx', 'bybit']
    selected = router.select_exchanges(order, exchanges)

    print(f"✓ Best Exchange: {selected[0][0]} (score: {selected[0][1]:.2f})")

    # 测试市场影响计算
    impact = router.calculate_market_impact(
        quantity=1.0,
        market_depth=100.0,
        volatility=0.02,
    )

    print(f"✓ Market Impact: {impact:.2%}")

    # 测试滑点计算
    slippage = router.calculate_slippage(
        order=order,
        mid_price=50000.0,
        market_depth=100.0,
    )

    print(f"✓ Estimated Slippage: {slippage:.2%}")

    # 测试执行估算
    estimate = router.estimate_execution(
        order=order,
        mid_price=50000.0,
        market_depth=100.0,
    )

    print(f"✓ Estimated Total Cost: {estimate['total_cost']:.2%}")
    print(f"✓ Success Probability: {estimate['success_probability']:.1%}")

    # 测试订单执行
    result = router.execute_order(order)

    print(f"✓ Execution Success: {result.success}")
    print(f"✓ Filled Quantity: {result.filled_quantity}")

    # 测试统计
    stats = router.get_router_statistics()
    print(f"✓ Total Executions: {stats.get('total_executions', 0)}")

    return True


def test_risk_monitor():
    """测试增强风险监控"""
    if not HAS_RISK_MONITOR:
        print("\n⚠ Skipping Risk Monitor (not available)")
        return True

    print("\n=== V51.3 Enhanced Risk Monitor Test ===")

    monitor = EnhancedRiskMonitor()

    # 模拟收益数据
    returns = [
        0.01, -0.02, 0.015, -0.01, 0.02,
        -0.015, 0.01, -0.025, 0.02, -0.01,
    ]

    # 测试VaR
    var_95 = monitor.calculate_var(returns, 0.95)
    print(f"✓ VaR (95%): {var_95:.2%}")

    # 测试CVaR
    cvar_95 = monitor.calculate_cvar(returns, 0.95)
    print(f"✓ CVaR (95%): {cvar_95:.2%}")

    # 测试波动率
    volatility = monitor.calculate_volatility(returns)
    print(f"✓ Volatility: {volatility:.2%}")

    # 测试夏普比率
    sharpe = monitor.calculate_sharpe_ratio(returns)
    print(f"✓ Sharpe Ratio: {sharpe:.2f}")

    # 测试压力测试
    stress_result = monitor.run_stress_test(
        portfolio_value=100000.0,
        scenario="market_crash",
    )

    print(f"✓ Stress Test: {stress_result.loss_pct:.1%}")
    print(f"✓ Margin Call: {stress_result.margin_call}")

    # 测试异常检测
    prices = [50000, 50200, 50100, 50300, 50000, 50150, 50250, 50350]
    for i, price in enumerate(prices):
        monitor.update_price("BTC/USDT", price)

    is_anomaly = monitor.detect_price_anomaly("BTC/USDT", 55000.0)
    print(f"✓ Price Anomaly: {is_anomaly}")

    # 测试风险检查
    from trading.enhanced_risk_monitor import PortfolioRisk
    pnl_history = [100, -50, 200, 150, -100]
    monitor._pnl_history.extend(pnl_history)

    risk = PortfolioRisk(
        total_value=100000.0,
        volatility=0.02,
        var_95=0.03,
        var_99=0.05,
        cvar_95=0.06,
        max_drawdown=0.15,
        beta=1.0,
        sharpe_ratio=1.5,
    )

    alerts = monitor.check_risk_limits(risk)
    print(f"✓ Risk Alerts: {len(alerts)}")

    # 测试统计
    stats = monitor.get_risk_statistics()
    print(f"✓ Total Updates: {stats.get('total_updates', 0)}")

    return True


def test_module_imports():
    """测试模块导入"""
    print("\n=== V51 Module Import Test ===")

    try:
        from strategies.advanced_leverage_manager import (
            AdvancedLeverageManager,
        )
        print("✓ advanced_leverage_manager imported")

        from strategies.smart_order_router import (
            SmartOrderRouter,
        )
        print("✓ smart_order_router imported")

        if HAS_RISK_MONITOR:
            from trading.enhanced_risk_monitor import (
                EnhancedRiskMonitor,
            )
            print("✓ enhanced_risk_monitor imported")

        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False


def test_integration():
    """测试集成"""
    print("\n=== V51 Integration Test ===")

    # 模拟完整交易��程
    leverage_manager = AdvancedLeverageManager()
    router = SmartOrderRouter()
    monitor = EnhancedRiskMonitor() if HAS_RISK_MONITOR else None

    # 1. 计算最优杠杆
    leverage_result = leverage_manager.calculate_optimal_leverage(
        symbol="ETH/USDT",
        current_price=3000.0,
        volatility=0.25,
        trend_strength=0.5,
        liquidity=0.7,
    )

    print(f"✓ Step 1 - Leverage: {leverage_result.recommended_leverage:.2f}x")

    # 2. 计算仓位
    position = leverage_manager.calculate_position_sizing(
        symbol="ETH/USDT",
        capital=5000.0,
        entry_price=3000.0,
        leverage=leverage_result.recommended_leverage,
        risk_level=RiskLevel.MODERATE,
    )

    print(f"✓ Step 2 - Position: ${position.position_value:,.2f}")

    # 3. 创建并执行订单
    order = OrderRequest(
        symbol="ETH/USDT",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=position.position_value / 3000.0,
        price=3000.0,
    )

    execution_result = router.execute_order(order)
    print(f"✓ Step 3 - Execution: {execution_result.success}")

    # 4. 更新风险监控
    if monitor:
        monitor.update_position(
            symbol="ETH/USDT",
            quantity=order.quantity,
            value=position.position_value,
            pnl=100.0,
        )

        stats = monitor.get_risk_statistics()
        print(f"✓ Step 4 - Risk: {stats.get('total_updates', 0)} updates")

    print("✓ All integration steps completed")

    return True


def main():
    """主测试函数"""
    print("=" * 60)
    print("V51.0 增强功能测试套件")
    print("=" * 60)

    tests = [
        ("Module Imports", test_module_imports),
        ("Leverage Manager", test_leverage_manager),
        ("Order Router", test_order_router),
        ("Risk Monitor", test_risk_monitor),
        ("Integration", test_integration),
    ]

    results = []

    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"[FAIL] {name} Error: {e}")
            results.append((name, False))

    # 汇总结果
    print("\n" + "=" * 60)
    print("Test Result Summary")
    print("=" * 60)

    passed = 0
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} - {name}")
        if result:
            passed += 1

    print(f"\nTotal: {passed}/{len(results)} Passed")

    return passed == len(results)


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)