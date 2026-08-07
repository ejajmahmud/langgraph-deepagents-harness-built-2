"""V21.0集成测试 - Portfolio Analytics 高级投资组合分析

测试覆盖：
1. PortfolioAnalytics — VaR/夏普比率/索提诺/卡尔玛比率
2. Drawdown Tracking — 回撤周期追踪
3. Win Rate/Profit Factor — 交易统计
4. 综合Metrics — 完整投资组合指标
5. 回归 — V16.6测试仍然通过

创建时间：2026-05-06
"""

import os
import sys
import unittest
from collections import deque
from datetime import datetime, timedelta
import time
import math

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPortfolioAnalytics(unittest.TestCase):
    """投资组合分析器测试"""

    def setUp(self):
        from trading.portfolio_analytics import PortfolioAnalytics

        self.analytics = PortfolioAnalytics(
            config={
                'initial_equity': 10000.0,
                'risk_free_rate': 0.02,
                'trading_periods_per_year': 252 * 24,  # 每小时交易
                'max_history_size': 1000
            }
        )

    def test_analytics_init(self):
        """测试分析器初始化"""
        self.assertIsNotNone(self.analytics)
        self.assertEqual(self.analytics.total_trades, 0)
        self.assertEqual(self.analytics.current_equity, 10000.0)
        # Peak equity starts at 0 until first trade
        self.assertEqual(self.analytics.peak_equity, 0.0)

    def test_record_first_trade(self):
        """测试记录第一笔交易"""
        self.analytics.record_trade(100.0)
        self.assertEqual(self.analytics.total_trades, 1)
        self.assertEqual(self.analytics.current_equity, 10100.0)

    def test_record_trades_multiple(self):
        """测试记录多笔交易"""
        pnl_list = [100.0, -50.0, 200.0, -30.0, 150.0]
        for pnl in pnl_list:
            self.analytics.record_trade(pnl)

        self.assertEqual(self.analytics.total_trades, 5)
        self.assertEqual(self.analytics.current_equity, 10370.0)

    def test_win_rate_calculation(self):
        """测试胜率计算"""
        pnl_list = [100.0, -50.0, 200.0, -30.0, 150.0]
        for pnl in pnl_list:
            self.analytics.record_trade(pnl)

        win_rate = self.analytics.calculate_win_rate()
        self.assertAlmostEqual(win_rate, 0.6, places=2)

    def test_profit_factor_calculation(self):
        """测试盈利因子计算"""
        pnl_list = [100.0, -50.0, 200.0, -30.0, 150.0]
        for pnl in pnl_list:
            self.analytics.record_trade(pnl)

        pf = self.analytics.calculate_profit_factor()
        # gross_profit=450, gross_loss=80, pf=450/80=5.625
        self.assertAlmostEqual(pf, 5.625, places=2)

    def test_average_win(self):
        """测试平均盈利"""
        pnl_list = [100.0, 200.0, 150.0]
        for pnl in pnl_list:
            self.analytics.record_trade(pnl)

        avg_win = self.analytics.calculate_average_win()
        self.assertAlmostEqual(avg_win, 150.0, places=2)

    def test_average_loss(self):
        """测试平均亏损"""
        pnl_list = [-50.0, -30.0, -100.0]
        for pnl in pnl_list:
            self.analytics.record_trade(pnl)

        avg_loss = self.analytics.calculate_average_loss()
        self.assertAlmostEqual(avg_loss, -60.0, places=2)

    def test_max_drawdown(self):
        """测试最大回撤"""
        # 创建权益曲线：10000 -> 11000 -> 9000 -> 12000
        self.analytics.record_trade(1000.0)  # 11000
        self.analytics.record_trade(-2000.0)  # 9000
        self.analytics.record_trade(3000.0)  # 12000

        max_dd = self.analytics.calculate_max_drawdown()
        self.assertAlmostEqual(max_dd, 2000.0, places=2)

    def test_current_drawdown(self):
        """测试当前回撤"""
        self.analytics.record_trade(1000.0)  # 11000
        self.analytics.record_trade(-500.0)  # 10500

        current_dd = self.analytics.calculate_current_drawdown()
        self.assertAlmostEqual(current_dd, 4.55, places=1)

    def test_sharpe_ratio(self):
        """测试夏普比率"""
        # 正收益序列
        pnl_list = [100.0, 150.0, 120.0, 130.0, 110.0]
        for pnl in pnl_list:
            self.analytics.record_trade(pnl)

        sharpe = self.analytics.calculate_sharpe_ratio(annualize=True)
        self.assertGreater(sharpe, 0)

    def test_var_calculation(self):
        """测试VaR计算"""
        pnl_list = [100.0, -50.0, 200.0, -30.0, 150.0, -100.0]
        for pnl in pnl_list:
            self.analytics.record_trade(pnl)

        var_95 = self.analytics.calculate_var(0.95)
        # 5%尾部应该是较小的损失
        self.assertGreaterEqual(var_95, 0)

    def test_cvar_calculation(self):
        """测试CVaR计算"""
        pnl_list = [100.0, -50.0, 200.0, -100.0]
        for pnl in pnl_list:
            self.analytics.record_trade(pnl)

        cvar = self.analytics.calculate_cvar(0.95)
        # CVaR应该大于等于VaR
        self.assertGreaterEqual(cvar, 0)

    def test_sortino_ratio(self):
        """测试索提诺比率"""
        # Include negative returns for downside deviation
        pnl_list = [100.0, 150.0, -50.0, 130.0, 110.0]
        for pnl in pnl_list:
            self.analytics.record_trade(pnl)

        sortino = self.analytics.calculate_sortino_ratio(annualize=True)
        # Should have non-zero downside to calculate
        self.assertIsNotNone(sortino)

    def test_calmar_ratio(self):
        """测试卡尔玛比率"""
        # 创建明显的回撤
        self.analytics.record_trade(500.0)  # 10500
        self.analytics.record_trade(-1000.0)  # 9500
        self.analytics.record_trade(1500.0)  # 11000

        calmar = self.analytics.calculate_calmar_ratio()
        # 取决于最大回撤
        self.assertIsNotNone(calmar)

    def test_metrics_caching(self):
        """测试指标缓存"""
        pnl_list = [100.0, 150.0, 120.0]
        for pnl in pnl_list:
            self.analytics.record_trade(pnl)

        # 第一次获取
        metrics1 = self.analytics.get_metrics()

        # 第二次获取（缓存命中）
        metrics2 = self.analytics.get_metrics()

        self.assertEqual(metrics1.total_trades, metrics2.total_trades)

    def test_metrics_force_refresh(self):
        """测试强制刷新缓存"""
        pnl_list = [100.0]
        for pnl in pnl_list:
            self.analytics.record_trade(pnl)

        # 获取初始指标
        metrics1 = self.analytics.get_metrics()

        # 添加更多交易
        self.analytics.record_trade(200.0)

        # 强制刷新
        metrics2 = self.analytics.get_metrics(force_refresh=True)

        self.assertGreater(metrics2.total_trades, metrics1.total_trades)

    def test_equity_curve(self):
        """测试权益曲线"""
        pnl_list = [100.0, -50.0, 200.0]
        for pnl in pnl_list:
            self.analytics.record_trade(pnl)

        curve = self.analytics.get_equity_curve()
        self.assertEqual(len(curve), 3)

    def test_expectancy(self):
        """测试交易期望值"""
        pnl_list = [100.0, -50.0, 200.0]
        for pnl in pnl_list:
            self.analytics.record_trade(pnl)

        expectancy = self.analytics.calculate_expectancy()
        # win_rate=2/3=0.667, avg_win= (100+200)/2=150, avg_loss=50
        # expectancy = 0.667*150 - 0.333*50 = 100 - 16.67 = 83.33
        self.assertAlmostEqual(expectancy, 83.33, places=1)


class TestDrawdownPeriods(unittest.TestCase):
    """回撤周期测试"""

    def test_drawdown_period_properties(self):
        """测试回撤周期属性"""
        from trading.portfolio_analytics import DrawdownPeriod

        period = DrawdownPeriod(
            peak_value=10000.0,
            trough_value=8000.0,
            peak_time=1000.0,
            trough_time=2000.0
        )

        self.assertAlmostEqual(period.max_drawdown_pct, 20.0, places=2)
        self.assertFalse(period.is_recovered)

    def test_drawdown_recovery(self):
        """测试回撤恢复"""
        from trading.portfolio_analytics import DrawdownPeriod

        period = DrawdownPeriod(
            peak_value=10000.0,
            trough_value=8000.0,
            peak_time=1000.0,
            trough_time=2000.0,
            recovery_time=3000.0
        )

        self.assertTrue(period.is_recovered)


class TestMetricsDataClass(unittest.TestCase):
    """投资组合指标数据类测试"""

    def test_metrics_init(self):
        """测试指标初始化"""
        from trading.portfolio_analytics import PortfolioMetrics

        metrics = PortfolioMetrics(
            total_pnl=1000.0,
            total_trades=10,
            winning_trades=6,
            win_rate=0.6
        )

        self.assertEqual(metrics.total_pnl, 1000.0)
        self.assertEqual(metrics.total_trades, 10)
        self.assertEqual(metrics.winning_trades, 6)
        self.assertAlmostEqual(metrics.win_rate, 0.6)


class TestRegressionV16_6(unittest.TestCase):
    """回归测试 - V16.6"""

    def test_funding_rate_engine_still_works(self):
        """测试资金费率引擎仍然可用"""
        from strategies.funding_rate_engine import FundingRateEngine

        engine = FundingRateEngine()
        self.assertIsNotNone(engine)

    def test_mock_storage_still_works(self):
        """测试Mock存储仍然可用"""
        from storage.mem0_mock_storage import MockMemo0Storage

        storage = MockMemo0Storage({"user_id": "test", "agent_id": "test"})
        result = storage.add_memory("test", "test content")
        self.assertTrue(result)

    def test_portfolio_risk_manager_still_works(self):
        """测试投资组合风控仍然可用"""
        from trading.risk_manager_v2 import RiskManagerV2

        manager = RiskManagerV2()
        self.assertIsNotNone(manager)


# 运行测试
if __name__ == '__main__':
    unittest.main(verbosity=2)