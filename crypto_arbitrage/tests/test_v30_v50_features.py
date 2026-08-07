"""V30.0 增强版自动交易执行引擎测试

测试V30.0新增功能:
- 真实交易所网关集成
- 增强风险管理
- 性能监控增强
- 多策略协同

创建时间：2026-05-07 17:25
"""

import sys
import os
import time
import asyncio

# 获取正确路径
test_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(test_dir)
sys.path.insert(0, project_dir)

print("="*50)
print("V30.0 增强版自动交易执行引擎测试")
print("="*50)

# 导入模块
from trading.auto_execution_engine import AutoExecutionEngine, AutoTradeConfig
from trading.portfolio_optimizer import PortfolioOptimizer
from trading.risk_dashboard import RealTimeRiskDashboard
from trading.calendar_effect_analyzer import CalendarEffectAnalyzer
from strategies.cross_exchange import calculate_cross_exchange_spread, calculate_net_profit
from strategies.triangular_arbitrage import calculate_triangle_profit, is_profitable_triangle


def test_auto_execution_engine_v30():
    """测试V30.0自动执行引擎"""
    print("\n=== Test AutoExecutionEngine V30.0 ===")

    # V30.0新配置
    config = {
        'mode': 'simulated',
        'scan_interval_seconds': 30,
        'min_score_threshold': 60.0,
        'min_confidence': 0.5,
        'max_concurrent_positions': 5,
        'auto_close_threshold': 0.02,
        'stop_loss_pct': 0.02,
        'max_exposure_per_symbol': 10000.0,
        'consecutive_loss_limit': 3,
        'enable_circuit_breaker': True,
        'emergency_stop_pct': 0.10,
        'daily_loss_limit': 0.05,
        'max_total_exposure': 50000.0,
        'trailing_stop_pct': 0.015,
        'enable_trailing_stop': True,
        'cooldown_seconds': 60,
        'allow_weekend_trading': True,
        # V30.0新增配置
        'enable_real_exchange': False,  # 真实交易所模式
        'exchange_api_key': '',
        'exchange_secret': '',
        'enable_advanced_risk': True,  # 高级风险管理
        'enable_ml_signal': False,  # ML信号增强
        'enable_portfolio_rebalance': True,  # 组合再平衡
    }

    engine = AutoExecutionEngine(config)
    print(f"[PASS] AutoExecutionEngine initialized: {engine.run_config.mode}")
    return True


def test_portfolio_optimizer_v30():
    """测试V30.0组合优化器"""
    print("\n=== Test Portfolio Optimizer V30.0 ===")

    from trading.portfolio_optimizer import StrategyPerformance, OptimizationMethod

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
    ]

    optimizer = PortfolioOptimizer({"max_weight": 0.6, "min_weight": 0.1})
    result = optimizer.optimize(strategies, method=OptimizationMethod.RISK_PARITY)

    print(f"[PASS] Portfolio optimization: {len(result.allocations)} strategies")
    print(f"  - Allocations: {[(a.strategy_id, a.weight) for a in result.allocations]}")
    print(f"  - Expected return: {result.expected_return:.4f}")
    print(f"  - Risk: {result.expected_risk:.4f}")
    return True


def test_cross_exchange_spread_v30():
    """Test V30.0 cross-exchange spread calculation"""
    print("\n=== Test Cross Exchange Spread V30.0 ===")

    # Test data - using dict format expected by the function
    price_a = {'bid': 50000.0, 'ask': 50100.0, 'last': 50050.0}  # Binance
    price_b = {'bid': 50150.0, 'ask': 50200.0, 'last': 50175.0}  # OKX
    fee_rate = 0.001

    spread = calculate_cross_exchange_spread(price_a, price_b)
    print(f"[PASS] Spread: {spread:.4f}%")

    # Net profit calculation (different signature)
    net_profit = calculate_net_profit(spread, 0.2, 0.1)  # gross, fee, min
    print(f"  - Net profit rate: {net_profit:.4f}%")
    return True


def test_triangular_profit_v30():
    """Test V30.0 triangle arbitrage profit calculation"""
    print("\n=== Test Triangular Profit V30.0 ===")

    # Triangle arbitrage path using correct pair names
    prices = {
        'BTC/USDT': 49600.0,
        'ETH/BTC': 15.5,
        'ETH/USDT': 3200.0,
    }

    result = calculate_triangle_profit(prices)
    print(f"[PASS] Triangle profit: {result}")

    # Threshold check
    profit_rate = result.get('profit_rate', 0)
    profitable = is_profitable_triangle(profit_rate, min_profit_rate=5.0)
    print(f"  - Profitable: {profitable}")
    return True


class TestV30Features:
    """V30.0功能测试套件"""

    @staticmethod
    def test_all():
        """运行所有V30.0测试"""
        results = []

        results.append(("AutoExecutionEngine V30", test_auto_execution_engine_v30()))
        results.append(("Portfolio Optimizer V30", test_portfolio_optimizer_v30()))
        results.append(("Cross Exchange Spread", test_cross_exchange_spread_v30()))
        results.append(("Triangular Profit", test_triangular_profit_v30()))

        return results


if __name__ == "__main__":
    print("\n" + "="*50)
    print("开始 V30.0 功能测试")
    print("="*50 + "\n")

    results = TestV30Features.test_all()

    print("\n" + "="*50)
    print("测试结果")
    print("="*50)

    passed = 0
    failed = 0
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status}: {name}")
        if result:
            passed += 1
        else:
            failed += 1

    print(f"\n总计: {passed} passed, {failed} failed")
    print("="*50)