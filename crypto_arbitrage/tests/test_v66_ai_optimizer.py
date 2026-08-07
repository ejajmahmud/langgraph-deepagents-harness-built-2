"""V66.0 集成测试

测试AI策略优化器功能

创建时间：2026-05-08
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategies.ai_strategy_optimizer import (
    MarketRegime,
    StrategyType,
    OptimizationGoal,
    StrategyMetrics,
    StrategyPerformance,
    OptimizationResult,
    StrategyRecommendation,
    StrategyPerformanceAnalyzer,
    AdaptiveParameterOptimizer,
    MarketRegimeDetector,
    StrategyRecommendationEngine,
    initialize_performance_analyzer,
    initialize_parameter_optimizer,
    initialize_recommendation_engine,
)


class TestStrategyPerformanceAnalyzer:
    """策略性能分析器测试"""

    def test_analyzer_init(self):
        """测试分析器初始化"""
        analyzer = initialize_performance_analyzer()
        assert analyzer is not None
        print("StrategyPerformanceAnalyzer: OK")

    def test_analyze_performance(self):
        """测试性能分析"""
        analyzer = initialize_performance_analyzer()

        # 模拟交易数据
        trades = [
            {"timestamp": 1000000, "pnl": 0.01},
            {"timestamp": 100086400, "pnl": 0.02},
            {"timestamp": 100172800, "pnl": -0.005},
            {"timestamp": 100259200, "pnl": 0.015},
            {"timestamp": 100345600, "pnl": 0.01},
        ]

        performance = analyzer.analyze_performance(
            strategy_id="test_strategy",
            strategy_type=StrategyType.TRIANGULAR,
            trades=trades,
            period_days=30
        )

        assert performance is not None
        assert performance.strategy_type == StrategyType.TRIANGULAR
        print(f"Metrics: return={performance.metrics.total_return:.4f}, sharpe={performance.metrics.sharpe_ratio:.2f}")

    def test_compare_strategies(self):
        """测试策略比较"""
        analyzer = StrategyPerformanceAnalyzer()

        p1 = StrategyPerformance(
            strategy_id="s1",
            strategy_type=StrategyType.TRIANGULAR,
            period_start=0,
            period_end=100,
            metrics=StrategyMetrics(total_return=0.1, sharpe_ratio=1.5)
        )

        p2 = StrategyPerformance(
            strategy_id="s2",
            strategy_type=StrategyType.CROSS_EXCHANGE,
            period_start=0,
            period_end=100,
            metrics=StrategyMetrics(total_return=0.08, sharpe_ratio=2.0)
        )

        sorted_perfs = analyzer.compare_strategies([p1, p2])
        assert sorted_perfs[0].strategy_id == "s2"  # sharpe更高
        print(f"Best: {sorted_perfs[0].strategy_id}")


class TestAdaptiveParameterOptimizer:
    """自适应参数优化器测试"""

    def test_optimizer_init(self):
        """测试优化器初始化"""
        optimizer = initialize_parameter_optimizer()
        assert optimizer is not None
        print("AdaptiveParameterOptimizer: OK")

    def test_parameter_optimization(self):
        """测试参数优化"""
        optimizer = AdaptiveParameterOptimizer()

        base_params = {
            "min_spread_pct": 0.3,
            "max_position_pct": 0.1,
            "stop_loss_pct": 0.05
        }

        # 模拟历史收益
        historical_returns = [0.01, 0.02, -0.005, 0.015, 0.01, 0.008, -0.002, 0.012]

        result = optimizer.optimize(
            strategy_type=StrategyType.TRIANGULAR,
            base_parameters=base_params,
            historical_returns=historical_returns
        )

        assert result is not None
        print(f"Optimization: best_score={result.best_score:.4f}, iterations={result.iterations}")

    def test_auto_adjust(self):
        """测试自动调整"""
        optimizer = AdaptiveParameterOptimizer()

        current_params = {
            "max_position_pct": 0.1,
            "stop_loss_pct": 0.05
        }

        performance = StrategyPerformance(
            strategy_id="test",
            strategy_type=StrategyType.TRIANGULAR,
            period_start=0,
            period_end=100,
            metrics=StrategyMetrics(
                max_drawdown=0.2,  # 高回撤
                win_rate=0.7,
                sharpe_ratio=1.5,
                volatility=0.03
            )
        )

        new_params = optimizer.auto_adjust(current_params, performance)

        assert new_params["max_position_pct"] < current_params["max_position_pct"]
        print(f"Adjusted: {current_params['max_position_pct']} -> {new_params['max_position_pct']}")


class TestMarketRegimeDetector:
    """市场状态检测器测试"""

    def test_detector_init(self):
        """测试检测器初始化"""
        detector = MarketRegimeDetector()
        assert detector is not None
        print("MarketRegimeDetector: OK")

    def test_detect_regime(self):
        """测试市场状态检测"""
        detector = MarketRegimeDetector()

        # 添加模拟价格数据(牛市)
        import random
        price = 100
        for _ in range(50):
            price *= 1 + random.uniform(-0.01, 0.015)
            detector.add_price(price)

        regime = detector.detect_regime()
        assert regime in [MarketRegime.BULL, MarketRegime.SIDEWAYS, MarketRegime.CALM]
        print(f"Detected regime: {regime.value}")

    def test_regime_parameters(self):
        """测试状态参数"""
        detector = MarketRegimeDetector()

        params = detector.get_regime_parameters(MarketRegime.BULL)
        assert "max_position_pct" in params
        assert params["max_position_pct"] == 0.3

        params = detector.get_regime_parameters(MarketRegime.VOLATILE)
        assert params["min_spread_pct"] == 0.8
        print(f"BULL params: {detector.get_regime_parameters(MarketRegime.BULL)}")


class TestStrategyRecommendationEngine:
    """策略推荐引擎测试"""

    def test_engine_init(self):
        """测试引擎初始化"""
        engine = initialize_recommendation_engine()
        assert engine is not None
        print("StrategyRecommendationEngine: OK")

    def test_recommend(self):
        """测试策略推荐"""
        engine = initialize_recommendation_engine()

        import random
        price = 100
        for _ in range(30):
            price *= 1 + random.uniform(-0.02, 0.025)
            engine.add_price_data(StrategyType.TRIANGULAR, price)

        recommendations = engine.recommend(
            available_strategies=[
                StrategyType.TRIANGULAR,
                StrategyType.CROSS_EXCHANGE,
                StrategyType.FUNDING_RATE
            ],
            market_data={}
        )

        assert len(recommendations) > 0
        print(f"Top recommendation: {recommendations[0].strategy_type.value} (confidence: {recommendations[0].confidence:.2f})")


class TestV66Integration:
    """V66.0 集成测试"""

    def test_v66_full_integration(self):
        """测试完整V66.0集成"""
        # 1. 初始化组件
        analyzer = initialize_performance_analyzer()
        optimizer = initialize_parameter_optimizer()
        engine = initialize_recommendation_engine()

        # 2. 模拟交易数据
        trades = [
            {"timestamp": i * 86400, "pnl": (i % 3 - 1) * 0.01}
            for i in range(30)
        ]

        # 3. 分析性能
        performance = analyzer.analyze_performance(
            strategy_id="arbitrage_v1",
            strategy_type=StrategyType.CROSS_EXCHANGE,
            trades=trades
        )

        # 4. 优化参数
        base_params = {
            "min_spread_pct": 0.3,
            "max_position_pct": 0.1,
            "stop_loss_pct": 0.05
        }

        optimization_result = optimizer.optimize(
            strategy_type=StrategyType.CROSS_EXCHANGE,
            base_parameters=base_params,
            historical_returns=[t["pnl"] for t in trades]
        )

        # 5. 推荐策略
        import random
        price = 100
        for _ in range(30):
            price *= 1 + random.uniform(-0.01, 0.015)
            engine.add_price_data(StrategyType.CROSS_EXCHANGE, price)

        recommendations = engine.recommend(
            [StrategyType.TRIANGULAR, StrategyType.CROSS_EXCHANGE],
            {}
        )

        # 6. 自动调整参数
        adjusted_params = optimizer.auto_adjust(base_params, performance)

        # 验证
        assert len(recommendations) > 0

        print(f"\n=== V66.0 Integration Test ===")
        print(f"Performance: return={performance.metrics.total_return:.4f}, sharpe={performance.metrics.sharpe_ratio:.2f}")
        print(f"Optimization: iterations={optimization_result.iterations}, convergence={optimization_result.convergence}")
        print(f"Best strategy: {recommendations[0].strategy_type.value}")
        print(f"Adjusted params: {adjusted_params}")
        print("=== All Tests Passed ===")


if __name__ == "__main__":
    print("Running V66.0 Integration Tests...")
    pytest.main([__file__, "-v", "-s"])