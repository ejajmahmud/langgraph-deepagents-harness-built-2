"""V68.0 集成测试

测试风险分析与投资组合管理功能

创建时间：2026-05-08
"""

import pytest
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from trading.risk_analytics_v68 import (
    RiskType,
    RiskLevel,
    VaRMethod,
    RiskMetric,
    RiskReport,
    PortfolioAllocation,
    VaRCalculator,
    RiskAnalytics,
    StressTester,
    PortfolioManager,
    initialize_risk_analytics,
    initialize_portfolio_manager,
)


class TestVaRCalculator:
    """VaR计算器测试"""

    def test_var_calculator_init(self):
        """测试初始化"""
        calc = VaRCalculator()
        assert calc is not None
        print("VaRCalculator: OK")

    def test_historical_var(self):
        """测试历史VaR"""
        calc = VaRCalculator()

        returns = [0.01, 0.02, -0.01, 0.015, -0.02, 0.03, -0.005, 0.01]
        portfolio_value = 10000.0

        var = calc.calculate_historical_var(returns, portfolio_value)

        assert var > 0
        print(f"Historical VaR: {var:.2f}")

    def test_parametric_var(self):
        """测试参数VaR"""
        calc = VaRCalculator()

        mean = 0.001
        std = 0.02
        portfolio_value = 10000.0

        var = calc.calculate_parametric_var(mean, std, portfolio_value)

        assert var > 0
        print(f"Parametric VaR: {var:.2f}")

    def test_monte_carlo_var(self):
        """测试Monte Carlo VaR"""
        calc = VaRCalculator()

        returns = [0.01, 0.02, -0.01, 0.015, -0.02]
        portfolio_value = 10000.0

        var = calc.calculate_monte_carl(returns, portfolio_value)

        assert var > 0
        print(f"Monte Carlo VaR: {var:.2f}")


class TestRiskAnalytics:
    """风险分析器测试"""

    def test_risk_analytics_init(self):
        """测试初始化"""
        analyzer = initialize_risk_analytics()
        assert analyzer is not None
        print("RiskAnalytics: OK")

    def test_add_return(self):
        """测试添加收益"""
        analyzer = RiskAnalytics()

        for ret in [0.01, 0.02, -0.01, 0.015]:
            analyzer.add_return(ret)

        assert len(analyzer.returns_history) == 4
        print(f"Returns: {analyzer.returns_history}")

    def test_calculate_var(self):
        """测试VaR计算"""
        analyzer = RiskAnalytics()

        for ret in [0.01, 0.02, -0.01, 0.015, -0.02, 0.03]:
            analyzer.add_return(ret)

        var_results = analyzer.calculate_var(10000.0)

        assert "var_95" in var_results
        print(f"VaR 95%: {var_results['var_95']:.2f}")

    def test_max_drawdown(self):
        """测试最大回撤"""
        analyzer = RiskAnalytics()

        # 权益曲线: 100 -> 110 -> 90 -> 120
        for value in [10000, 11000, 9000, 12000]:
            analyzer.add_equity(value)

        dd = analyzer.calculate_max_drawdown()

        assert dd > 0
        print(f"Max Drawdown: {dd:.2%}")

    def test_sharpe_ratio(self):
        """测试夏普比率"""
        analyzer = RiskAnalytics()

        returns = [0.01, 0.02, -0.01, 0.015, -0.02, 0.03]
        for ret in returns:
            analyzer.add_return(ret)

        sharpe = analyzer.calculate_sharpe_ratio()

        print(f"Sharpe Ratio: {sharpe:.2f}")

    def test_risk_level_assessment(self):
        """���试风险等级评估"""
        analyzer = RiskAnalytics()

        level = analyzer.assess_risk_level(0.2)
        assert level == RiskLevel.LOW

        level = analyzer.assess_risk_level(0.7)
        assert level == RiskLevel.HIGH

        print(f"Risk Level: {level.value}")

    def test_generate_report(self):
        """测试风险报告生成"""
        analyzer = RiskAnalytics()

        # 添加数据
        for ret in [0.01, 0.02, -0.01, 0.015, -0.02]:
            analyzer.add_return(ret)

        for value in [10000, 10500, 9800, 11000]:
            analyzer.add_equity(value)

        report = analyzer.generate_report(10000.0)

        assert report is not None
        assert report.total_risk_score >= 0
        print(f"Report: {report.to_dict()}")


class TestStressTester:
    """压力测试器测试"""

    def test_stress_tester_init(self):
        """测试初始化"""
        tester = StressTester()
        assert tester is not None
        print("StressTester: OK")

    def test_stress_test(self):
        """测试压力测试"""
        tester = StressTester()

        positions = [
            {"symbol": "BTC", "value": 5000},
            {"symbol": "ETH", "value": 3000},
            {"symbol": "USDT", "value": 2000}
        ]

        result = tester.stress_test(10000.0, positions, "market_crash")

        assert result["loss_pct"] == 0.30
        print(f"Stress result: {result}")

    def test_run_scenarios(self):
        """测试多场景"""
        tester = StressTester()

        positions = [{"symbol": "BTC", "value": 10000}]

        results = tester.run_scenarios(10000.0, positions)

        assert len(results) == 4
        print(f"Scenarios: {[r['scenario'] for r in results]}")


class TestPortfolioManager:
    """投资组合管理器测试"""

    def test_portfolio_manager_init(self):
        """测试初始化"""
        manager = initialize_portfolio_manager()
        assert manager is not None
        print("PortfolioManager: OK")

    def test_add_allocation(self):
        """测试添加配置"""
        manager = PortfolioManager()

        manager.update_total_value(10000)
        manager.add_allocation("BTC", 0.5, 5000)
        manager.add_allocation("ETH", 0.3, 3000)
        manager.add_allocation("USDT", 0.2, 2000)

        assert len(manager.allocations) == 3
        print(f"Allocations: {manager.allocations}")

    def test_needs_rebalance(self):
        """测试需要再平衡"""
        manager = PortfolioManager(
            {"rebalance_threshold": 0.05, "target_allocations": {"BTC": 0.4, "ETH": 0.4, "USDT": 0.2}}
        )

        manager.update_total_value(10000)
        manager.add_allocation("BTC", 0.6, 6000)  # target_weight=0.4, drift = 0.2
        manager.add_allocation("ETH", 0.2, 2000)  # target_weight=0.4
        manager.add_allocation("USDT", 0.2, 2000)  # target_weight=0.2

        needs = manager.needs_rebalance()

        assert needs is True
        print(f"Needs rebalance: {needs}")

    def test_get_rebalance_orders(self):
        """测试获取再平衡订单"""
        manager = PortfolioManager(
            {"target_allocations": {"BTC": 0.5, "ETH": 0.5}}
        )

        manager.update_total_value(10000)
        manager.add_allocation("BTC", 0.7, 7000)
        manager.add_allocation("ETH", 0.3, 3000)

        orders = manager.get_rebalance_orders(["binance"])

        assert len(orders) > 0
        print(f"Orders: {orders}")

    def test_diversification_score(self):
        """测试分散化评分"""
        manager = PortfolioManager()

        manager.update_total_value(10000)
        manager.add_allocation("BTC", 0.4, 4000)
        manager.add_allocation("ETH", 0.3, 3000)
        manager.add_allocation("USDT", 0.3, 3000)

        score = manager.get_diversification_score()

        assert score > 0
        print(f"Diversification: {score:.2f}")


class TestV68Integration:
    """V68.0 集成测试"""

    def test_v68_full_integration(self):
        """测试完整V68.0集成"""
        # 1. 初始化组件
        risk = initialize_risk_analytics({"max_var_pct": 0.03})
        portfolio = initialize_portfolio_manager()
        tester = StressTester()

        # 2. 添加收益数据
        for ret in [0.01, 0.02, -0.01, 0.015, -0.02, 0.03, -0.005, 0.02]:
            risk.add_return(ret)

        # 3. 添加权益曲线
        for value in [10000, 10500, 10200, 11000, 10800, 11500]:
            risk.add_equity(value)

        # 4. 配置投资组合
        portfolio.update_total_value(10000)
        portfolio.add_allocation("BTC", 0.5, 5000)
        portfolio.add_allocation("ETH", 0.3, 3000)
        portfolio.add_allocation("USDT", 0.2, 2000)

        # 5. 运行压力测试
        positions = [
            {"symbol": "BTC", "value": 5000},
            {"symbol": "ETH", "value": 3000}
        ]
        stress_results = tester.run_scenarios(10000.0, positions)

        # 6. 生成风险报告
        report = risk.generate_report(10000.0)

        print(f"\n=== V68.0 Integration Test ===")
        print(f"Risk Level: {report.risk_level.value}")
        print(f"VaR 95%: {report.var_95:.2f}")
        print(f"Max DD: {report.max_drawdown:.2%}")
        print(f"Sharpe: {report.sharpe_ratio:.2f}")
        print(f"Recommendations: {report.recommendations}")
        print(f"Needs Rebalance: {portfolio.needs_rebalance()}")
        print(f"Stress Scenarios: {len(stress_results)}")
        print("=== All Tests Passed ===")


if __name__ == "__main__":
    print("Running V68.0 Integration Tests...")
    pytest.main([__file__, "-v", "-s"])