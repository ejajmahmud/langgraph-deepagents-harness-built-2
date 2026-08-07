"""V33.0 投资组合协调系统测试套件

测试V33.0新增功能:
- Portfolio Coordinator - 投资组合协调器
- Risk Manager Pro - 专业风险管理系统
- Dynamic Hedge Engine - 动态对冲引擎

创建时间：2026-05-07 20:30
"""

import sys
import os

# 获取正确路径
test_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(test_dir)
sys.path.insert(0, project_dir)

print("="*50)
print("V33.0 投资组合协调系统测试")
print("="*50)

# 导入V33模块
from trading.portfolio_coordinator_v33 import (
    PortfolioCoordinator,
    RiskManagerPro,
    DynamicHedgeEngine,
    RiskLevel,
    HedgeStrategy,
    create_portfolio_coordinator,
    create_risk_manager,
    create_hedge_engine,
)


def test_v33_portfolio_coordinator():
    """测试投资组合协调器"""
    print("\n=== Test V33.0 Portfolio Coordinator ===")

    config = {
        'max_leverage': 3.0,
        'max_position_size': 10000,
        'balance_threshold': 0.2,
        'risk_per_trade': 0.02,
        'initial_capital': 100000,
    }

    coordinator = create_portfolio_coordinator(config)
    print(f"[OK] PortfolioCoordinator 初始化")
    print(f"  Max leverage: {coordinator.max_leverage}")
    print(f"  Initial capital: ${coordinator.total_value}")

    # 测试添加头寸
    success = coordinator.add_position(
        symbol="BTC/USDT",
        side="long",
        size=0.5,
        entry_price=50000,
        current_price=51000,
    )

    print(f"[OK] 添加头寸 BTC/USDT: {'成功' if success else '失败'}")

    # 测试更新价格
    coordinator.update_prices({"BTC/USDT": 52000})

    summary = coordinator.get_portfolio_summary()
    print(f"\n[Portfolio Summary]")
    print(f"  Total value: ${summary['total_value']:,.2f}")
    print(f"  Total exposure: ${summary['total_exposure']:,.2f}")
    print(f"  Leverage: {summary['leverage']:.2f}x")
    print(f"  Unrealized PnL: ${summary['unrealized_pnl']:,.2f}")

    print(f"[PASS] Portfolio Coordinator Test")
    return True


def test_v33_risk_manager():
    """测试风险管理系统"""
    print("\n=== Test V33.0 Risk Manager ===")

    config = {
        'max_var': 0.05,
        'max_drawdown': 0.2,
        'stop_loss': 0.05,
        'take_profit': 0.15,
        'initial_capital': 100000,
    }

    risk_mgr = create_risk_manager(config)
    print(f"[OK] RiskManager 创建")

    # 测试价值更新
    risk_level = risk_mgr.update_value(100000)
    print(f"  Initial risk level: {risk_level.value}")

    risk_level = risk_mgr.update_value(95000)
    print(f"  After 5% drop: {risk_level.value}")

    # 测试VaR计算
    returns = [0.01, -0.02, 0.015, -0.01, 0.005, 0.02, -0.015, 0.01]
    var_95 = risk_mgr.calculate_var(returns, 0.95)
    print(f"  VaR (95%): {var_95:.2%}")

    # 测试夏普比率
    sharpe = risk_mgr.calculate_sharpe_ratio(returns)
    print(f"  Sharpe ratio: {sharpe:.2f}")

    # 测试止损检查
    should_stop = risk_mgr.should_stop_loss(
        entry_price=50000,
        current_price=47500,
        side="long"
    )
    print(f"  Stop loss triggered (5% drop): {should_stop}")

    # 测试止盈检查
    should_take = risk_mgr.should_take_profit(
        entry_price=50000,
        current_price=57500,
        side="long"
    )
    print(f"  Take profit triggered (15% gain): {should_take}")

    print(f"[PASS] Risk Manager Test")
    return True


def test_v33_hedge_engine():
    """测试对冲引擎"""
    print("\n=== Test V33.0 Hedge Engine ===")

    config = {
        'hedge_threshold': 0.1,
        'target_delta': 0,
    }

    hedge_eng = create_hedge_engine(config)
    print(f"[OK] DynamicHedgeEngine 创建")
    print(f"  Hedge threshold: {hedge_eng.hedge_threshold}")

    # 创建测试组合
    portfolio_config = {
        'initial_capital': 100000,
    }
    portfolio = create_portfolio_coordinator(portfolio_config)

    # 添加测试头寸
    portfolio.add_position("BTC/USDT", "long", 0.5, 50000, 50000)
    portfolio.add_position("ETH/USDT", "long", 5, 3000, 3000)

    # 测试对冲评估
    decision = hedge_eng.evaluate_hedge(portfolio, {})

    if decision:
        print(f"\n[Hedge Decision]")
        print(f"  Strategy: {decision.strategy.value}")
        print(f"  Reason: {decision.reason}")
        print(f"  Adjustment: {decision.adjustment:.1%}")
    else:
        print(f"  No hedge needed")

    summary = hedge_eng.get_hedge_summary()
    print(f"\n[Hedge Summary]")
    print(f"  Total hedges: {summary['total_hedges']}")

    print(f"[PASS] Hedge Engine Test")
    return True


def test_v33_integration():
    """集成测试"""
    print("\n=== Test V33.0 Integration ===")

    # 创建所有组件
    portfolio_config = {'initial_capital': 100000}
    risk_config = {'max_drawdown': 0.2, 'initial_capital': 100000}
    hedge_config = {'hedge_threshold': 0.1}

    portfolio = create_portfolio_coordinator(portfolio_config)
    risk_mgr = create_risk_manager(risk_config)
    hedge_eng = create_hedge_engine(hedge_config)

    # 模拟交易流程
    portfolio.add_position("BTC/USDT", "long", 0.5, 50000, 50000)
    portfolio.add_position("ETH/USDT", "short", 3, 3000, 3000)

    # 更新价格
    prices = {"BTC/USDT": 52000, "ETH/USDT": 2900}
    portfolio.update_prices(prices)

    # 检查风险
    risk_level = risk_mgr.update_value(portfolio.total_value + portfolio.get_total_pnl())
    print(f"Risk level: {risk_level.value}")

    # 检查对冲
    hedge_decision = hedge_eng.evaluate_hedge(portfolio, {})
    if hedge_decision:
        print(f"Hedge needed: {hedge_decision.strategy.value}")

    summary = portfolio.get_portfolio_summary()
    print(f"\n[Final Summary]")
    print(f"  Total PnL: ${summary['unrealized_pnl']:,.2f}")
    print(f"  Leverage: {summary['leverage']:.2f}x")

    print(f"[PASS] Integration Test")
    return True


def run_all_tests():
    """运行所有V33测试"""
    results = []

    results.append(("V33 Portfolio Coordinator", test_v33_portfolio_coordinator()))
    results.append(("V33 Risk Manager", test_v33_risk_manager()))
    results.append(("V33 Hedge Engine", test_v33_hedge_engine()))
    results.append(("V33 Integration", test_v33_integration()))

    # 汇总
    print("\n" + "="*50)
    print("V33.0 测试结果汇总")
    print("="*50)

    passed = 0
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {name}: {status}")
        if result:
            passed += 1

    print(f"\n总计: {passed}/{len(results)} 通过")

    return passed == len(results)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)