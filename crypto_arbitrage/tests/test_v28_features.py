"""V28.0 新功能测试套件

测试Portfolio Optimizer、Calendar Effect Analyzer和Risk Dashboard。

创建时间：2026-05-07 14:35
"""

import sys
import os
import time
import random

# 获取正确路径
test_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(test_dir)
sys.path.insert(0, project_dir)

print("="*50)
print("V28.0 新功能测试套件")
print("="*50)

# 导入模块
from trading.portfolio_optimizer import (
    PortfolioOptimizer,
    OptimizationMethod,
    StrategyPerformance
)

from trading.calendar_effect_analyzer import CalendarEffectAnalyzer

from trading.risk_dashboard import RealTimeRiskDashboard


def test_portfolio_optimizer():
    """测试组合优化器"""
    print("\n=== 测试 Portfolio Optimizer ===")

    strategies = [
        StrategyPerformance(
            strategy_id="strat_1",
            name="Trend Following",
            return_mean=0.015,
            return_std=0.08,
            sharpe_ratio=0.1875,
            max_drawdown=0.12,
            win_rate=0.55,
            avg_profit=150.0,
            avg_loss=80.0,
            trade_count=45,
            correlation=0.3
        ),
        StrategyPerformance(
            strategy_id="strat_2",
            name="Mean Reversion",
            return_mean=0.012,
            return_std=0.05,
            sharpe_ratio=0.24,
            max_drawdown=0.08,
            win_rate=0.60,
            avg_profit=100.0,
            avg_loss=50.0,
            trade_count=60,
            correlation=0.25
        ),
        StrategyPerformance(
            strategy_id="strat_3",
            name="Breakout",
            return_mean=0.018,
            return_std=0.12,
            sharpe_ratio=0.15,
            max_drawdown=0.18,
            win_rate=0.45,
            avg_profit=200.0,
            avg_loss=120.0,
            trade_count=30,
            correlation=0.2
        ),
    ]

    optimizer = PortfolioOptimizer({"max_weight": 0.6, "min_weight": 0.1})
    result = optimizer.optimize(strategies, OptimizationMethod.MAX_SHARPE, total_capital=10000.0)

    print("方法: %s" % result.method)
    print("预期收益: %.4f" % result.expected_return)
    print("预期风险: %.4f" % result.expected_risk)
    print("夏普比率: %.4f" % result.sharpe_ratio)

    for alloc in result.allocations:
        print("  %s: %.2f%% ($%.2f)" % (alloc.name, alloc.weight * 100, alloc.capital))

    print("OK: Portfolio Optimizer passed")
    return True


def test_calendar_effect_analyzer():
    """测试日历效应分析器"""
    print("\n=== 测试 Calendar Effect Analyzer ===")

    now = time.time()
    trades = []

    for day in range(30):
        for hour in [9, 10, 14, 15, 21]:
            ts = now - (day * 86400) + (hour * 3600)
            profit = random.uniform(-50, 150)
            trades.append({
                "timestamp": ts,
                "profit": profit,
                "win": profit > 0
            })

    analyzer = CalendarEffectAnalyzer({"min_samples": 3})
    analysis = analyzer.analyze(trades)

    print("分析时段效应: %d" % len(analysis.effects))
    print("最佳交易日: %s" % analysis.best_trading_days)
    print("最佳月份: %s" % analysis.best_months)
    print("最佳时间: %s" % analysis.best_time_hours)

    recommendation = analyzer.get_recommendation()
    print("仓位调整: %.1fx" % recommendation["position_adjustment"])

    print("OK: Calendar Effect Analyzer passed")
    return True


def test_risk_dashboard():
    """测试实时风控仪表板"""
    print("\n=== 测试 Real-Time Risk Dashboard ===")

    dashboard = RealTimeRiskDashboard({
        "max_exposure": 10000,
        "max_leverage": 3.0
    })

    positions = [
        {"symbol": "BTC/USDT", "size": 0.5, "value": 5000, "exposure_pct": 0.5, "side": "long", "pnl": 150, "liq_dist": 0.35},
        {"symbol": "ETH/USDT", "size": 2.0, "value": 3000, "exposure_pct": 0.3, "side": "short", "pnl": -50, "liq_dist": 0.45}
    ]

    state = dashboard.update(
        total_exposure=8000,
        max_exposure=10000,
        utilization=0.8,
        leverage=1.5,
        position_count=2,
        daily_pnl=100,
        max_drawdown=0.05,
        win_rate=0.55,
        positions=positions
    )

    print("状态: %s" % state.status)
    print("风险等级: %s" % state.risk_level)
    print("风险评分: %.1f" % state.metrics.risk_score)
    print("暴露: $%d" % state.metrics.total_exposure)
    print("杠杆: %.2fx" % state.metrics.leverage)
    print("告警数: %d" % len(state.alerts))

    summary = dashboard.get_summary()
    print("摘要: status=%s, score=%.1f" % (summary["status"], summary["risk_score"]))

    gauge = dashboard.get_risk_gauge()
    print("风险仪表: %.1f/100" % gauge["value"])

    print("OK: Real-Time Risk Dashboard passed")
    return True


def main():
    results = []

    results.append(("Portfolio Optimizer", test_portfolio_optimizer()))
    results.append(("Calendar Effect Analyzer", test_calendar_effect_analyzer()))
    results.append(("Risk Dashboard", test_risk_dashboard()))

    print("\n" + "="*50)
    print("测试结果汇总")
    print("="*50)

    passed = 0
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print("%s: %s" % (name, status))
        if result:
            passed += 1

    print("\n通过: %d/%d" % (passed, len(results)))
    return passed == len(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)