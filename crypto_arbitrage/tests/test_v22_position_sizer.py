"""V22.0集成测试 - Dynamic Position Sizer 动态仓位管理

测试覆盖：
1. DynamicPositionSizer — Kelly Criterion
2. Drawdown Factor — 回撤因子计算
3. Volatility Factor — 波动率因子
4. Performance Factor — 性能因子
5. 各策略 — fixed/kelly/adaptive等
6. 回归 — V21.0/V16.6测试仍然通过

创建时间：2026-05-06
"""

import os
import sys
import unittest
from collections import deque
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDynamicPositionSizer(unittest.TestCase):
    """动态仓位管理器测试"""

    def setUp(self):
        from trading.dynamic_position_sizer import DynamicPositionSizer
        from trading.portfolio_analytics import PortfolioAnalytics

        self.analytics = PortfolioAnalytics(
            config={'initial_equity': 10000.0}
        )

        self.sizer = DynamicPositionSizer(
            config={
                'base_position_size': 1000.0,
                'max_position_size': 10000.0,
                'min_position_size': 100.0,
                'kelly_fraction': 0.5,
                'max_kelly_pct': 0.25
            },
            portfolio_analytics=self.analytics
        )

    def test_sizer_init(self):
        """测试管理器初始化"""
        self.assertIsNotNone(self.sizer)
        self.assertEqual(self.sizer.base_position_size, 1000.0)
        self.assertEqual(self.sizer.max_position_size, 10000.0)
        self.assertEqual(self.sizer.min_position_size, 100.0)

    def test_fixed_strategy(self):
        """测试固定仓位策略"""
        result = self.sizer.calculate_position_size(
            strategy="fixed",
            confidence=1.0  # Max confidence
        )
        self.assertEqual(result.strategy, "fixed")
        self.assertEqual(result.recommended_size, 1000.0)

    def test_kelly_strategy(self):
        """测试Kelly策略"""
        # 60%胜率, avg_win=100, avg_loss=50
        result = self.sizer.calculate_position_size(
            strategy="kelly",
            win_rate=0.6,
            avg_win=100.0,
            avg_loss=50.0
        )
        self.assertGreater(result.kelly_pct, 0)
        self.assertEqual(result.strategy, "kelly")

    def test_half_kelly_strategy(self):
        """测试半Kelly策略"""
        result = self.sizer.calculate_position_size(
            strategy="half_kelly",
            win_rate=0.6,
            avg_win=100.0,
            avg_loss=50.0
        )
        self.assertEqual(result.strategy, "half_kelly")

    def test_drawdown_strategy(self):
        """测试回撤策略"""
        result = self.sizer.calculate_position_size(
            strategy="drawdown",
            current_drawdown=10.0
        )
        self.assertEqual(result.strategy, "drawdown")
        self.assertLess(result.recommended_size, 1000.0)

    def test_volatility_strategy(self):
        """测试波动率策略"""
        result = self.sizer.calculate_position_size(
            strategy="volatility",
            volatility=0.10
        )
        self.assertEqual(result.strategy, "volatility")

    def test_adaptive_strategy(self):
        """测试自适应策略"""
        result = self.sizer.calculate_position_size(
            strategy="adaptive",
            win_rate=0.6,
            avg_win=100.0,
            avg_loss=50.0,
            current_drawdown=5.0,
            volatility=0.05,
            confidence=0.8
        )
        self.assertEqual(result.strategy, "adaptive")
        self.assertIsNotNone(result.recommended_size)

    def test_kelly_calculation(self):
        """测试Kelly计算"""
        # Kelly = W - (1-W)/R = 0.6 - 0.4/2 = 0.6 - 0.2 = 0.4
        # But capped at max_kelly_pct = 0.25
        kelly = self.sizer._calculate_kelly(0.6, 100.0, 50.0)
        self.assertAlmostEqual(kelly, 0.25, places=2)  # Capped at max_kelly_pct

    def test_kelly_zero_loss(self):
        """测试Kelly零亏损"""
        kelly = self.sizer._calculate_kelly(0.6, 100.0, 0.0)
        self.assertEqual(kelly, 0.0)

    def test_kelly_negative(self):
        """测试Kelly负值情况"""
        # 高亏损低盈利 = 负Kelly
        kelly = self.sizer._calculate_kelly(0.3, 50.0, 100.0)
        self.assertLessEqual(kelly, 0.0)

    def test_drawdown_factor_low(self):
        """测试低回撤因子"""
        factor = self.sizer._calculate_drawdown_factor(2.0)
        self.assertAlmostEqual(factor, 1.0, places=2)

    def test_drawdown_factor_medium(self):
        """测试中等回撤因子"""
        factor = self.sizer._calculate_drawdown_factor(10.0)
        self.assertAlmostEqual(factor, 0.6, places=2)

    def test_drawdown_factor_high(self):
        """测试高回撤因子"""
        factor = self.sizer._calculate_drawdown_factor(20.0)
        self.assertAlmostEqual(factor, 0.2, places=2)

    def test_volatility_factor_low(self):
        """测试低波动率因子"""
        factor = self.sizer._calculate_volatility_factor(0.01)
        self.assertAlmostEqual(factor, 1.0, places=2)

    def test_volatility_factor_high(self):
        """测试高波动率因子"""
        factor = self.sizer._calculate_volatility_factor(0.15)
        self.assertAlmostEqual(factor, 0.4, places=2)

    def test_performance_factor_low_winrate(self):
        """测试低胜率性能因子"""
        factor = self.sizer._calculate_performance_factor(0.3)
        self.assertAlmostEqual(factor, 0.5, places=2)

    def test_performance_factor_high_winrate(self):
        """测试高胜率性能因子"""
        # 0.6 threshold maps to 1.0 (max in config)
        factor = self.sizer._calculate_performance_factor(0.6)
        self.assertAlmostEqual(factor, 1.0, places=2)

    def test_min_position_size(self):
        """测试最小仓位限制"""
        result = self.sizer.calculate_position_size(
            strategy="drawdown",
            current_drawdown=50.0  # 严重回撤
        )
        self.assertGreaterEqual(result.recommended_size, 100.0)

    def test_max_position_size(self):
        """测试最大仓位限制"""
        # 创建高胜率高盈利场景
        result = self.sizer.calculate_position_size(
            strategy="kelly",
            win_rate=0.9,
            avg_win=1000.0,
            avg_loss=100.0
        )
        self.assertLessEqual(result.recommended_size, 10000.0)

    def test_confidence_adjustment(self):
        """测试置信度调整"""
        result_low = self.sizer.calculate_position_size(
            strategy="fixed",
            confidence=0.2
        )
        result_high = self.sizer.calculate_position_size(
            strategy="fixed",
            confidence=0.8
        )
        self.assertLess(
            result_low.recommended_size,
            result_high.recommended_size
        )

    def test_calculation_history(self):
        """测试计算历史"""
        for i in range(5):
            self.sizer.calculate_position_size(strategy="fixed")

        self.assertEqual(self.sizer.total_calculations, 5)

    def test_average_size(self):
        """测试平均仓位"""
        self.sizer.calculate_position_size(strategy="fixed")
        self.sizer.calculate_position_size(strategy="kelly", win_rate=0.6, avg_win=100, avg_loss=50)

        avg = self.sizer.average_size
        self.assertIsNotNone(avg)


class TestPositionSizeResult(unittest.TestCase):
    """仓位结果数据类测试"""

    def test_result_creation(self):
        """测试结果创建"""
        from trading.dynamic_position_sizer import PositionSizeResult

        result = PositionSizeResult(
            recommended_size=800.0,
            base_size=1000.0,
            multiplier=0.8,
            strategy="drawdown",
            confidence=0.7,
            reason="Test drawdown",
            kelly_pct=0.2,
            drawdown_factor=0.8,
            volatility_factor=1.0,
            performance_factor=1.0
        )

        self.assertEqual(result.recommended_size, 800.0)
        self.assertEqual(result.strategy, "drawdown")


class TestRegressionV21_V16(unittest.TestCase):
    """回归测试 - V21.0 / V16.6"""

    def test_portfolio_analytics_still_works(self):
        """测试投资组合分析器仍然可用"""
        from trading.portfolio_analytics import PortfolioAnalytics

        analytics = PortfolioAnalytics()
        self.assertIsNotNone(analytics)

    def test_v16_6_pipeline_still_works(self):
        """测试管道仍然可用"""
        from trading.arbitrage_pipeline import ArbitragePipeline

        pipeline = ArbitragePipeline()
        self.assertIsNotNone(pipeline)


# 运行测试
if __name__ == '__main__':
    unittest.main(verbosity=2)