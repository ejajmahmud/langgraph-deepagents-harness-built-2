"""CryptoArbitrage V2.7 测试套件

测试目标：
1. 异步LLM分析 - AsyncLLMAnalyzer
2. 信号融合缓存 - SignalCache
3. 性能监控 - PerformanceMonitor
4. 优化可视化 - OptimizedBacktestVisualization

V2.7核心：性能优化与系统完善
"""

import asyncio
import json
import time
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime

import pytest


# ==================== 异步LLM分析测试 ====================

@pytest.mark.unit
class TestAsyncLLMAnalyzer:
    """测试异步LLM分析器"""

    def test_analyzer_initialization(self):
        """测试分析器初始化"""
        from llm.async_trading_agents import AsyncLLMAnalyzer

        analyzer = AsyncLLMAnalyzer(
            max_workers=3,
            cache_ttl=300,
            timeout=120
        )

        assert analyzer.max_workers == 3
        assert analyzer.cache_ttl == 300
        assert analyzer.timeout == 120
        assert len(analyzer.cache) == 0

    def test_analyze_single_symbol(self):
        """测试单个币种分析"""
        from llm.async_trading_agents import AsyncLLMAnalyzer

        analyzer = AsyncLLMAnalyzer(max_workers=1, cache_ttl=60)

        # Mock TradingAgents包装器
        with patch('llm.async_trading_agents.TradingAgentsWrapper') as mock_wrapper_class:
            mock_wrapper = MagicMock()
            mock_wrapper.analyze_crypto.return_value = {
                "signal": "BUY",
                "score": 100,
                "confidence": 0.9,
                "success": True
            }
            mock_wrapper_class.return_value = mock_wrapper

            result = analyzer.analyze_sync("BTC", "2024-04-16", use_cache=False)

            assert result["signal"] == "BUY"
            assert result["score"] == 100
            assert result["confidence"] == 0.9
            assert result["success"] == True

    def test_cache_hit(self):
        """测试缓存命中"""
        from llm.async_trading_agents import AsyncLLMAnalyzer

        analyzer = AsyncLLMAnalyzer(cache_ttl=60)

        # Mock TradingAgents包装器
        with patch('llm.async_trading_agents.TradingAgentsWrapper') as mock_wrapper_class:
            mock_wrapper = MagicMock()
            mock_wrapper.analyze_crypto.return_value = {
                "signal": "BUY",
                "score": 100,
                "confidence": 0.9,
                "success": True
            }
            mock_wrapper_class.return_value = mock_wrapper

            # 第一次调用（缓存未命中）
            result1 = analyzer.analyze_sync("BTC", "2024-04-16", use_cache=True)
            assert analyzer.stats["cache_misses"] == 1

            # 第二次调用（缓存命中）
            result2 = analyzer.analyze_sync("BTC", "2024-04-16", use_cache=True)
            assert analyzer.stats["cache_hits"] == 1

            # 结果应该相同
            assert result1["signal"] == result2["signal"]
            assert result1["score"] == result2["score"]

    def test_stats_tracking(self):
        """测试统计追踪"""
        from llm.async_trading_agents import AsyncLLMAnalyzer

        analyzer = AsyncLLMAnalyzer()

        # 模拟一些统计数据
        analyzer.stats["total_requests"] = 10
        analyzer.stats["cache_hits"] = 6
        analyzer.stats["cache_misses"] = 4

        stats = analyzer.get_stats()

        assert stats["total_requests"] == 10
        assert stats["cache_hits"] == 6
        assert stats["cache_misses"] == 4
        assert stats["cache_hit_rate"] == 0.6


# ==================== 信号缓存测试 ====================

@pytest.mark.unit
class TestSignalCache:
    """测试信号缓存引擎"""

    def test_cache_initialization(self):
        """测试缓存初始化"""
        from llm.signal_cache import SignalCache

        cache = SignalCache(max_size=100, default_ttl=60)

        assert cache.max_size == 100
        assert cache.default_ttl == 60
        assert len(cache.memory_cache) == 0

    def test_cache_set_and_get(self):
        """测试缓存设置和获取"""
        from llm.signal_cache import SignalCache

        cache = SignalCache()

        # 设置缓存
        signal_data = {"signal": "BUY", "score": 100, "confidence": 0.9}
        cache.set("technical", "BTC/USDT", signal_data, "rsi_30")

        # 获取缓存
        cached = cache.get("technical", "BTC/USDT", "rsi_30")

        assert cached is not None
        assert cached["signal"] == "BUY"
        assert cached["score"] == 100

    def test_cache_expiration(self):
        """测试缓存过期"""
        from llm.signal_cache import SignalCache

        cache = SignalCache(default_ttl=1)  # 1秒TTL

        signal_data = {"signal": "BUY", "score": 100}
        cache.set("technical", "BTC/USDT", signal_data)

        # 立即获取，应该命中
        cached1 = cache.get("technical", "BTC/USDT")
        assert cached1 is not None

        # 等待2秒
        time.sleep(2)

        # 缓存应该过期
        cached2 = cache.get("technical", "BTC/USDT")
        assert cached2 is None

    def test_cache_stats(self):
        """测试缓存统计"""
        from llm.signal_cache import SignalCache

        cache = SignalCache()

        # 模拟一些操作
        cache.stats["memory_hits"] = 8
        cache.stats["total_gets"] = 10

        stats = cache.get_stats()

        assert stats["total_gets"] == 10
        assert stats["memory_hits"] == 8
        assert stats["hit_rate"] == 0.8

    def test_cache_invalidation(self):
        """测试缓存失效"""
        from llm.signal_cache import SignalCache

        cache = SignalCache()

        # 添加多个缓存
        cache.set("technical", "BTC/USDT", {"signal": "BUY"})
        cache.set("technical", "ETH/USDT", {"signal": "SELL"})
        cache.set("risk", "BTC/USDT", {"signal": "HOLD"})

        # 失效BTC/USDT的技术信号
        cache.invalidate("technical", "BTC/USDT")

        # BTC/USDT技术信号应该被删除
        assert cache.get("technical", "BTC/USDT") is None

        # 其他缓存应该保留
        assert cache.get("technical", "ETH/USDT") is not None
        assert cache.get("risk", "BTC/USDT") is not None


# ==================== 性能监控测试 ====================

@pytest.mark.unit
class TestPerformanceMonitor:
    """测试性能监控器"""

    def test_monitor_initialization(self):
        """测试监控器初始化"""
        from monitoring.performance_monitor import PerformanceMonitor

        monitor = PerformanceMonitor(window_size=100, alert_threshold=2.0)

        assert monitor.window_size == 100
        assert monitor.alert_threshold == 2.0

    def test_record_metric(self):
        """测试记录指标"""
        from monitoring.performance_monitor import PerformanceMonitor

        monitor = PerformanceMonitor()

        monitor.record_metric("test_metric", 42.5)
        monitor.record_metric("test_metric", 38.2)
        monitor.record_metric("test_metric", 45.1)

        stats = monitor.get_metric_stats("test_metric")

        assert stats["count"] == 3
        assert stats["min"] == 38.2
        assert stats["max"] == 45.1
        assert abs(stats["mean"] - 41.93) < 0.1

    def test_context_manager(self):
        """测试上下文管理器"""
        from monitoring.performance_monitor import PerformanceMonitor

        monitor = PerformanceMonitor()

        with monitor.context("test_operation"):
            time.sleep(0.1)

        stats = monitor.get_metric_stats("test_operation_duration")

        assert stats is not None
        assert stats["count"] == 1
        assert stats["mean"] >= 0.1

    def test_identify_bottlenecks(self):
        """测试瓶颈识别"""
        from monitoring.performance_monitor import PerformanceMonitor

        monitor = PerformanceMonitor()

        # 添加一些慢操作
        monitor.record_metric("slow_operation_duration", 2.5)
        monitor.record_metric("slow_operation_duration", 3.0)
        monitor.record_metric("slow_operation_duration", 2.8)

        # 添加一些快操作
        monitor.record_metric("fast_operation_duration", 0.1)
        monitor.record_metric("fast_operation_duration", 0.2)

        bottlenecks = monitor.identify_bottlenecks(threshold=1.0)

        # 应该识别出慢操作
        assert len(bottlenecks) == 1
        assert bottlenecks[0]["metric"] == "slow_operation_duration"
        assert bottlenecks[0]["mean_duration"] > 2.0

    def test_performance_report(self):
        """测试性能报告"""
        from monitoring.performance_monitor import PerformanceMonitor

        monitor = PerformanceMonitor()

        monitor.record_metric("test_duration", 1.5)
        monitor.set_baseline("test_duration", 1.0)

        report = monitor.get_performance_report()

        assert "timestamp" in report
        assert "metrics" in report
        assert "baselines" in report
        assert report["baselines"]["test_duration"] == 1.0

    def test_alert_threshold(self):
        """测试告警阈值"""
        from monitoring.performance_monitor import PerformanceMonitor

        monitor = PerformanceMonitor(alert_threshold=1.5)
        monitor.set_baseline("test_metric", 10.0)

        # 正常值，不应该告警
        monitor.record_metric("test_metric", 11.0)
        assert len(monitor.get_recent_alerts()) == 0

        # 超过阈值，应该告警
        monitor.record_metric("test_metric", 25.0)
        assert len(monitor.get_recent_alerts()) > 0


# ==================== 优化可视化测试 ====================

@pytest.mark.unit
class TestOptimizedVisualization:
    """测试优化可视化"""

    def test_sampler_initialization(self):
        """测试采样器初始化"""
        from visualization.optimized_viz import DataSampler

        sampler = DataSampler()

        # 测试时间序列采样
        data = [(i, i * i) for i in range(100)]
        sampled = sampler.sample_time_series(data, max_points=20)

        assert len(sampled) == 20

    def test_time_series_sampling(self):
        """测试时间序列采样"""
        from visualization.optimized_viz import DataSampler

        sampler = DataSampler()

        # 创建测试数据
        data = [(i, i * i) for i in range(100)]

        # 采样到20个点
        sampled = sampler.sample_time_series(data, max_points=20)

        # 应该保留首尾点
        assert sampled[0] == data[0]
        assert sampled[-1] == data[-1]

        # 中间点数量正确
        assert len(sampled) == 20

    def test_heatmap_sampling(self):
        """测试热力图采样"""
        from visualization.optimized_viz import DataSampler
        import numpy as np

        sampler = DataSampler()

        # 创建测试热力图数据
        data = np.random.rand(100, 100)

        # 采样到50x50
        sampled = sampler.sample_heatmap(data, max_cells=2500)

        # 应该被采样
        assert sampled.size <= 2500
        assert sampled.shape[0] < 100
        assert sampled.shape[1] < 100

    def test_visualization_cache(self):
        """测试可视化缓存"""
        from visualization.optimized_viz import VisualizationCache

        cache = VisualizationCache(max_size=10)

        # 设置缓存
        chart_data = {"data": [], "layout": {}}
        cache.set("chart1", chart_data)

        # 获取缓存
        cached = cache.get("chart1")

        assert cached is not None
        assert cached == chart_data

        # 检查统计
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 0

    def test_cache_eviction(self):
        """测试缓存淘汰"""
        from visualization.optimized_viz import VisualizationCache

        cache = VisualizationCache(max_size=3)

        # 添加3个条目（达到上限）
        for i in range(3):
            cache.set(f"chart{i}", {"data": i})

        # 添加第4个条目，应该淘汰最旧的
        cache.set("chart3", {"data": 3})

        # 最旧的条目应该被淘汰
        assert cache.get("chart0") is None

        # 其他条目应该保留
        assert cache.get("chart1") is not None
        assert cache.get("chart2") is not None
        assert cache.get("chart3") is not None

    def test_optimized_equity_curve(self):
        """测试优化版权益曲线"""
        from visualization.optimized_viz import OptimizedBacktestVisualization

        viz = OptimizedBacktestVisualization(max_points=50)

        # 创建测试数据
        dates = [datetime(2024, 1, i).strftime("%Y-%m-%d") for i in range(1, 32)]
        equity = [10000 + i * 100 for i in range(31)]

        backtest_results = {
            "dates": dates,
            "equity_curve": equity,
            "benchmark": [10000 + i * 50 for i in range(31)]
        }

        # 生成图表
        chart = viz.generate_optimized_equity_curve(backtest_results)

        assert "data" in chart
        assert "layout" in chart
        assert len(chart["data"]) == 3  # 权益、基准、初始资金

    def test_large_dataset_sampling(self):
        """测试大数据集采样"""
        from visualization.optimized_viz import OptimizedBacktestVisualization

        viz = OptimizedBacktestVisualization(max_points=100)

        # 创建大数据集（1000个点）
        dates = [datetime(2024, 1, 1 + i // 24).strftime("%Y-%m-%d") for i in range(1000)]
        equity = [10000 + i * 10 for i in range(1000)]

        backtest_results = {
            "dates": dates,
            "equity_curve": equity
        }

        # 生成图表
        chart = viz.generate_optimized_equity_curve(backtest_results)

        # 数据应该被采样到100个点
        assert len(chart["data"]) > 0
        assert len(chart["data"][0]["x"]) <= 100

    def test_cache_hit_in_viz(self):
        """测试可视化缓存命中"""
        from visualization.optimized_viz import OptimizedBacktestVisualization

        viz = OptimizedBacktestVisualization()

        backtest_results = {
            "dates": ["2024-01-01", "2024-01-02"],
            "equity_curve": [10000, 10100]
        }

        # 第一次调用（缓存未命中）
        chart1 = viz.generate_optimized_equity_curve(backtest_results, use_cache=True)
        stats1 = viz.get_cache_stats()

        assert stats1["misses"] == 1

        # 第二次调用（缓存命中）
        chart2 = viz.generate_optimized_equity_curve(backtest_results, use_cache=True)
        stats2 = viz.get_cache_stats()

        assert stats2["hits"] == 1
        assert stats2["hit_rate"] > 0


# ==================== 集成测试 ====================

@pytest.mark.integration
class TestV27Integration:
    """V2.7集成测试"""

    def test_async_analysis_with_cache(self):
        """测试异步分析与缓存集成"""
        from llm.async_trading_agents import AsyncLLMAnalyzer
        from llm.signal_cache import SignalCache

        analyzer = AsyncLLMAnalyzer(max_workers=2, cache_ttl=60)
        cache = SignalCache()

        # Mock TradingAgents
        with patch('llm.async_trading_agents.TradingAgentsWrapper') as mock_wrapper_class:
            mock_wrapper = MagicMock()
            mock_wrapper.analyze_crypto.return_value = {
                "signal": "BUY",
                "score": 100,
                "confidence": 0.9,
                "success": True
            }
            mock_wrapper_class.return_value = mock_wrapper

            # 分析并缓存
            result = analyzer.analyze_sync("BTC", "2024-04-16", use_cache=True)

            # 缓存技术信号
            tech_signal = {"signal": "BUY", "score": 90, "confidence": 0.8}
            cache.set("technical", "BTC/USDT", tech_signal)

            # 从缓存获取
            cached = cache.get("technical", "BTC/USDT")

            assert cached is not None
            assert cached["signal"] == "BUY"

    def test_performance_monitoring_pipeline(self):
        """测试性能监控流程"""
        from monitoring.performance_monitor import PerformanceMonitor

        monitor = PerformanceMonitor()

        # 模拟完整的交易流程
        with monitor.context("market_scan"):
            time.sleep(0.01)

        with monitor.context("opportunity_detection"):
            time.sleep(0.02)

        with monitor.context("signal_fusion"):
            time.sleep(0.015)

        with monitor.context("trade_execution"):
            time.sleep(0.005)

        # 获取统计
        stats = monitor.get_all_stats()

        # 应该有4个指标
        assert len(stats) == 4

        # 检查瓶颈
        bottlenecks = monitor.identify_bottlenecks(threshold=0.01)

        # 应该识别出慢操作
        assert len(bottlenecks) >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
