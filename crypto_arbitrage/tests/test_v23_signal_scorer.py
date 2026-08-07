"""V23.0集成测试 - Signal Quality Scorer 信号质量评分

测试覆盖：
1. SignalQualityScorer — 多因子评分
2. SignalRating — 信号评级
3. Historical Performance — 历史表现
4. Risk-Reward — 风险回报
5. Signal Recording — 信号记录
6. 回归 — V22/V21/V16.6测试仍然通过

创建时间：2026-05-06
"""

import os
import sys
import unittest
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestSignalQualityScorer(unittest.TestCase):
    """信号质量评分器测试"""

    def setUp(self):
        from trading.signal_quality_scorer import SignalQualityScorer
        from trading.portfolio_analytics import PortfolioAnalytics

        self.analytics = PortfolioAnalytics(
            config={'initial_equity': 10000.0}
        )

        self.scorer = SignalQualityScorer(
            config={
                'factor_weights': {
                    'historical_performance': 0.25,
                    'volatility': 0.15,
                    'liquidity': 0.15,
                    'spread': 0.10,
                    'correlation': 0.10,
                    'market_regime': 0.10,
                    'risk_reward': 0.15,
                },
                'min_confidence': 0.5,
                'min_score': 60
            },
            portfolio_analytics=self.analytics
        )

    def test_scorer_init(self):
        """测试评分器初始化"""
        self.assertIsNotNone(self.scorer)
        self.assertEqual(self.scorer.min_confidence, 0.5)
        self.assertEqual(self.scorer.min_score, 60)

    def test_score_signal_buy(self):
        """测试买入信号评分"""
        score = self.scorer.score_signal(
            symbol="BTC/USDT",
            action="buy",
            entry_price=50000.0,
            target_price=55000.0,
            stop_loss=48000.0
        )

        self.assertIsNotNone(score)
        self.assertGreater(score.total_score, 0)

    def test_score_signal_sell(self):
        """测试卖出信号评分"""
        score = self.scorer.score_signal(
            symbol="BTC/USDT",
            action="sell",
            entry_price=50000.0,
            target_price=45000.0,
            stop_loss=52000.0
        )

        self.assertIsNotNone(score.total_score)

    def test_rating_a_plus(self):
        """测试A+评级"""
        # 高分应该得到A+
        from trading.signal_quality_scorer import SignalRating

        rating = self.scorer._get_rating(95)
        self.assertEqual(rating, SignalRating.A_PLUS)

    def test_rating_a(self):
        """测试A评级"""
        from trading.signal_quality_scorer import SignalRating

        rating = self.scorer._get_rating(85)
        self.assertEqual(rating, SignalRating.A)

    def test_rating_b_plus(self):
        """测试B+评级"""
        from trading.signal_quality_scorer import SignalRating

        rating = self.scorer._get_rating(75)
        self.assertEqual(rating, SignalRating.B_PLUS)

    def test_rating_b(self):
        """测试B评级"""
        from trading.signal_quality_scorer import SignalRating

        rating = self.scorer._get_rating(65)
        self.assertEqual(rating, SignalRating.B)

    def test_rating_c(self):
        """测试C评级"""
        from trading.signal_quality_scorer import SignalRating

        rating = self.scorer._get_rating(55)
        self.assertEqual(rating, SignalRating.C)

    def test_rating_d(self):
        """测试D评级"""
        from trading.signal_quality_scorer import SignalRating

        rating = self.scorer._get_rating(30)
        self.assertEqual(rating, SignalRating.D)

    def test_historical_performance_score(self):
        """测试历史表现评分"""
        # 有历史数据
        score = self.scorer._score_historical({
            'win_rate': 0.7,
            'profit_factor': 2.0
        })
        self.assertGreater(score, 50)

    def test_historical_no_data(self):
        """测试无历史数据"""
        # 使用portfolio analytics
        self.analytics.record_trade(100.0)
        self.analytics.record_trade(50.0)

        score = self.scorer._score_historical(None)
        self.assertIsNotNone(score)

    def test_volatility_low(self):
        """测试低波动率"""
        score = self.scorer._score_volatility({
            'volatility': 0.01
        })
        self.assertGreater(score, 70)

    def test_volatility_high(self):
        """测试高波动率"""
        score = self.scorer._score_volatility({
            'volatility': 0.20
        })
        self.assertLess(score, 30)

    def test_liquidity_high(self):
        """测试高流动性"""
        score = self.scorer._score_liquidity({
            'volume_24h': 1_000_000_000
        })
        self.assertGreater(score, 80)

    def test_liquidity_low(self):
        """测试低流动性"""
        score = self.scorer._score_liquidity({
            'volume_24h': 100_000
        })
        self.assertLess(score, 50)

    def test_spread_low(self):
        """测试小价差"""
        score = self.scorer._score_spread({
            'spread_pct': 0.03
        })
        self.assertGreater(score, 80)

    def test_spread_high(self):
        """测试大价差"""
        score = self.scorer._score_spread({
            'spread_pct': 0.5
        })
        self.assertLess(score, 50)

    def test_risk_reward_excellent(self):
        """测试优秀风险回报"""
        score = self.scorer._score_risk_reward(
            entry_price=100.0,
            target_price=130.0,
            stop_loss=90.0
        )
        self.assertGreater(score, 80)

    def test_risk_reward_poor(self):
        """测试差风险回报"""
        score = self.scorer._score_risk_reward(
            entry_price=100.0,
            target_price=105.0,
            stop_loss=90.0
        )
        self.assertLess(score, 40)

    def test_weighted_score(self):
        """测试加权分数"""
        breakdown = {
            'historical_performance': 80,
            'volatility': 70,
            'liquidity': 60,
            'spread': 70,
            'correlation': 60,
            'market_regime': 70,
            'risk_reward': 80
        }

        total = self.scorer._calculate_weighted_score(breakdown)
        self.assertGreater(total, 60)

    def test_confidence_calculation(self):
        """测试置信度计算"""
        breakdown = {
            'historical_performance': 80,
            'volatility': 70,
            'liquidity': 60,
            'spread': 70,
            'correlation': 60,
            'market_regime': 70,
            'risk_reward': 80
        }

        confidence = self.scorer._calculate_confidence(70, breakdown)
        self.assertGreater(confidence, 0.5)

    def test_recommendation_execute(self):
        """测试执行推荐"""
        from trading.signal_quality_scorer import SignalRating

        rec = self.scorer._get_recommendation(80, 0.7, SignalRating.A)
        self.assertEqual(rec, "execute")

    def test_recommendation_skip(self):
        """测试跳过推荐"""
        from trading.signal_quality_scorer import SignalRating

        rec = self.scorer._get_recommendation(30, 0.3, SignalRating.D)
        self.assertEqual(rec, "skip")

    def test_signal_to_dict(self):
        """测试评分为字典"""
        score = self.scorer.score_signal(
            symbol="BTC/USDT",
            action="buy",
            entry_price=50000.0,
            target_price=55000.0,
            stop_loss=48000.0
        )

        d = score.to_dict()
        self.assertIn('rating', d)
        self.assertIn('total_score', d)
        self.assertIn('recommendation', d)


class TestSignalRating(unittest.TestCase):
    """信号评级枚举测试"""

    def test_rating_enum(self):
        """测试评级枚举"""
        from trading.signal_quality_scorer import SignalRating

        self.assertEqual(SignalRating.A_PLUS.value, "A+")
        self.assertEqual(SignalRating.A.value, "A")
        self.assertEqual(SignalRating.B_PLUS.value, "B+")
        self.assertEqual(SignalRating.B.value, "B")
        self.assertEqual(SignalRating.C.value, "C")
        self.assertEqual(SignalRating.D.value, "D")


class TestRegressionV22V21V16(unittest.TestCase):
    """回归测试 - V22/V21/V16.6"""

    def test_dynamic_position_sizer_still_works(self):
        """测试动态仓位管理器仍然可用"""
        from trading.dynamic_position_sizer import DynamicPositionSizer

        sizer = DynamicPositionSizer()
        self.assertIsNotNone(sizer)

    def test_portfolio_analytics_still_works(self):
        """测试投资组合分析器仍然可用"""
        from trading.portfolio_analytics import PortfolioAnalytics

        analytics = PortfolioAnalytics()
        self.assertIsNotNone(analytics)

    def test_arbitrage_pipeline_still_works(self):
        """测试管道仍然可用"""
        from trading.arbitrage_pipeline import ArbitragePipeline

        pipeline = ArbitragePipeline()
        self.assertIsNotNone(pipeline)


# 运行测试
if __name__ == '__main__':
    unittest.main(verbosity=2)