"""性能监控与指标收集系统

V2.7新增：全面监控系统性能，收集关键指标，
识别性能瓶颈，为优化提供数据支持。

核心特性：
1. 实时指标收集 - LLM分析、信号融合、交易执行等
2. 性能基准 - 设定性能基线，检测异常
3. 瓶颈识别 - 自动识别慢操作
4. 告警机制 - 性能阈值超限告警
5. 历史数据 - 性能趋势分析
"""

import json
import logging
import statistics
import threading
import time
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """性能监控器

    收集和分析系统性能指标。
    """

    def __init__(
        self,
        window_size: int = 100,
        alert_threshold: float = 2.0,
        log_dir: Optional[str] = None
    ):
        """初始化性能监控器

        Args:
            window_size: 滑动窗口大小
            alert_threshold: 告警阈值（标准差倍数）
            log_dir: 日志目录
        """
        self.window_size = window_size
        self.alert_threshold = alert_threshold
        self.log_dir = Path(log_dir) if log_dir else Path("logs/performance")

        # 性能数据存储
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        self.metrics_lock = threading.Lock()

        # 性能基线
        self.baselines: Dict[str, float] = {}

        # 告警状态
        self.alerts: List[Dict[str, Any]] = []
        self.alert_lock = threading.Lock()

        # 上下文管理器栈
        self._context_stack: List[str] = []

        # 确保日志目录存在
        self.log_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"PerformanceMonitor initialized: "
            f"window_size={window_size}, "
            f"alert_threshold={alert_threshold}, "
            f"log_dir={self.log_dir}"
        )

    def record_metric(
        self,
        name: str,
        value: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """记录性能指标

        Args:
            name: 指标名称
            value: 指标值
            metadata: 额外元数据
        """
        timestamp = time.time()

        with self.metrics_lock:
            self.metrics[name].append({
                "value": value,
                "timestamp": timestamp,
                "metadata": metadata or {}
            })

        # 检查是否需要告警
        self._check_alerts(name, value)

        logger.debug(f"Recorded metric: {name}={value:.4f}")

    def record_timing(
        self,
        name: str,
        start_time: float,
        end_time: Optional[float] = None
    ) -> None:
        """记录时间指标

        Args:
            name: 指标名称
            start_time: 开始时间
            end_time: 结束时间（None为当前时间）
        """
        if end_time is None:
            end_time = time.time()

        duration = end_time - start_time
        self.record_metric(f"{name}_duration", duration)
        self.record_metric(f"{name}_throughput", 1.0 / duration if duration > 0 else 0)

    def get_metric_stats(self, name: str) -> Optional[Dict[str, float]]:
        """获取指标统计信息

        Args:
            name: 指标名称

        Returns:
            统计信息字典
        """
        with self.metrics_lock:
            if name not in self.metrics or len(self.metrics[name]) == 0:
                return None

            values = [m["value"] for m in self.metrics[name]]

            return {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
                "p95": statistics.quantiles(values, n=20)[18] if len(values) >= 20 else max(values),
                "p99": statistics.quantiles(values, n=100)[98] if len(values) >= 100 else max(values)
            }

    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """获取所有指标的统计信息

        Returns:
            所有指标的统计
        """
        stats = {}

        with self.metrics_lock:
            for name in self.metrics:
                stats[name] = self.get_metric_stats(name)

        return stats

    def set_baseline(self, name: str, value: float) -> None:
        """设置性能基线

        Args:
            name: 指标名称
            value: 基线值
        """
        self.baselines[name] = value
        logger.info(f"Baseline set: {name}={value}")

    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告

        Returns:
            性能报告字典
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "metrics": self.get_all_stats(),
            "baselines": self.baselines.copy(),
            "alerts": self.get_recent_alerts(),
            "bottlenecks": self.identify_bottlenecks()
        }

        return report

    def identify_bottlenecks(self, threshold: float = 1.0) -> List[Dict[str, Any]]:
        """识别性能瓶颈

        Args:
            threshold: 阈值（秒），超过此时间视为瓶颈

        Returns:
            瓶颈列表
        """
        bottlenecks = []

        with self.metrics_lock:
            for name, data in self.metrics.items():
                if not name.endswith("_duration"):
                    continue

                if len(data) == 0:
                    continue

                stats = self.get_metric_stats(name)
                if stats and stats["mean"] > threshold:
                    bottlenecks.append({
                        "metric": name,
                        "mean_duration": stats["mean"],
                        "max_duration": stats["max"],
                        "count": stats["count"],
                        "severity": "high" if stats["mean"] > threshold * 2 else "medium"
                    })

        # 按平均持续时间排序
        bottlenecks.sort(key=lambda x: x["mean_duration"], reverse=True)

        return bottlenecks

    def _check_alerts(self, name: str, value: float) -> None:
        """检查是否需要告警

        Args:
            name: 指标名称
            value: 指标值
        """
        # 检查是否超过基线
        if name in self.baselines:
            baseline = self.baselines[name]
            deviation = abs(value - baseline) / baseline if baseline != 0 else 0

            if deviation > self.alert_threshold:
                alert = {
                    "timestamp": datetime.now().isoformat(),
                    "metric": name,
                    "value": value,
                    "baseline": baseline,
                    "deviation": deviation,
                    "severity": "high" if deviation > self.alert_threshold * 2 else "medium"
                }

                with self.alert_lock:
                    self.alerts.append(alert)

                logger.warning(
                    f"Performance alert: {name}={value:.4f} "
                    f"(baseline={baseline:.4f}, deviation={deviation:.2%})"
                )

    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的告警

        Args:
            limit: 返回数量限制

        Returns:
            告警列表
        """
        with self.alert_lock:
            return self.alerts[-limit:] if self.alerts else []

    def clear_alerts(self) -> None:
        """清除所有告警"""
        with self.alert_lock:
            self.alerts.clear()
        logger.info("Alerts cleared")

    def export_metrics(self, filepath: Optional[str] = None) -> str:
        """导出指标到文件

        Args:
            filepath: 文件路径（None为默认路径）

        Returns:
            文件路径
        """
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = self.log_dir / f"metrics_{timestamp}.json"

        filepath = Path(filepath)

        report = self.get_performance_report()

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"Metrics exported to {filepath}")

        return str(filepath)

    def load_metrics(self, filepath: str) -> None:
        """从文件加载指标

        Args:
            filepath: 文件路径
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"Metrics file not found: {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 恢复基线
        if "baselines" in data:
            self.baselines = data["baselines"]

        # 恢复指标
        if "metrics" in data:
            with self.metrics_lock:
                self.metrics.clear()
                for name, stats in data["metrics"].items():
                    # 恢复基线值
                    if stats:
                        self.metrics[name] = deque(maxlen=self.window_size)

        logger.info(f"Metrics loaded from {filepath}")

    def context(self, name: str):
        """上下文管理器：自动记录时间

        Args:
            name: 上下文名称

        Returns:
            上下文管理器

        Example:
            with monitor.context("llm_analysis"):
                result = llm_analyzer.analyze(symbol)
        """
        return _PerformanceContext(self, name)


class _PerformanceContext:
    """性能上下文管理器"""

    def __init__(self, monitor: PerformanceMonitor, name: str):
        self.monitor = monitor
        self.name = name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration = time.time() - self.start_time
            self.monitor.record_timing(self.name, self.start_time, time.time())

            # 记录错误
            if exc_type is not None:
                error_metric = f"{self.name}_error"
                self.monitor.record_metric(error_metric, 1)


class PerformanceDecorator:
    """性能装饰器

    用于自动监控函数执行时间。
    """

    def __init__(self, monitor: PerformanceMonitor, name: Optional[str] = None):
        """初始化装饰器

        Args:
            monitor: 性能监控器
            name: 指标名称（None为函数名）
        """
        self.monitor = monitor
        self.name = name

    def __call__(self, func: Callable) -> Callable:
        """装饰函数

        Args:
            func: 要装饰的函数

        Returns:
            装饰后的函数
        """
        metric_name = self.name or func.__name__

        def wrapper(*args, **kwargs):
            with self.monitor.context(metric_name):
                return func(*args, **kwargs)

        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__

        return wrapper


# ---------------------- 全局单例 ----------------------

_global_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor(
    window_size: int = 100,
    alert_threshold: float = 2.0,
    log_dir: Optional[str] = None
) -> PerformanceMonitor:
    """获取全局性能监控器实例

    Args:
        window_size: 滑动窗口大小
        alert_threshold: 告警阈值（标准差倍数）
        log_dir: 日志目录

    Returns:
        PerformanceMonitor实例
    """
    global _global_monitor

    if _global_monitor is None:
        _global_monitor = PerformanceMonitor(
            window_size=window_size,
            alert_threshold=alert_threshold,
            log_dir=log_dir
        )

    return _global_monitor


def monitor_performance(name: Optional[str] = None):
    """性能监控装饰器工厂

    Args:
        name: 指标名称（None为函数名）

    Returns:
        装饰器

    Example:
        @monitor_performance("llm_analysis")
        def analyze_symbol(symbol):
            # ...
    """
    def decorator(func: Callable) -> Callable:
        monitor = get_performance_monitor()
        return PerformanceDecorator(monitor, name)(func)

    return decorator


# ---------------------- 便捷函数 ----------------------

def record_llm_analysis(symbol: str, duration: float) -> None:
    """记录LLM分析性能

    Args:
        symbol: 加密货币代码
        duration: 分析持续时间（秒）
    """
    monitor = get_performance_monitor()
    monitor.record_metric("llm_analysis_duration", duration, {"symbol": symbol})


def record_signal_fusion(symbol: str, duration: float) -> None:
    """记录信号融合性能

    Args:
        symbol: 交易对符号
        duration: 融合持续时间（秒）
    """
    monitor = get_performance_monitor()
    monitor.record_metric("signal_fusion_duration", duration, {"symbol": symbol})


def record_cache_hit(cache_type: str) -> None:
    """记录缓存命中

    Args:
        cache_type: 缓存类型 (llm/signal/market)
    """
    monitor = get_performance_monitor()
    monitor.record_metric(f"cache_hit_{cache_type}", 1)


def record_cache_miss(cache_type: str) -> None:
    """记录缓存未命中

    Args:
        cache_type: 缓存类型 (llm/signal/market)
    """
    monitor = get_performance_monitor()
    monitor.record_metric(f"cache_miss_{cache_type}", 1)


def get_bottleneck_report() -> List[Dict[str, Any]]:
    """获取瓶颈报告

    Returns:
        瓶颈列表
    """
    monitor = get_performance_monitor()
    return monitor.identify_bottlenecks()


def export_performance_report(filepath: Optional[str] = None) -> str:
    """导出性能报告

    Args:
        filepath: 文件路径

    Returns:
        文件路径
    """
    monitor = get_performance_monitor()
    return monitor.export_metrics(filepath)
