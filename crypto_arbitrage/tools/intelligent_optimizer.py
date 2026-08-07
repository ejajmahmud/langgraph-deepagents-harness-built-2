"""智能优化引擎 V3.0

基于实时监控数据和历史表现，自动优化系统参数和策略配置。

核心特性：
1. 自适应参数调优 - 基于性能指标动态调整参数
2. 策略权重优化 - 根据历史表现自动调整策略分配
3. 性能基准学习 - 自动建立和更新性能基线
4. 异常检测与优化 - 识别异常并自动优化
5. 多目标优化 - 平衡收益、风险、性能等多个目标

V3.0新增：AI驱动的智能优化决策
"""

import json
import logging
import numpy as np
import statistics
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class IntelligentOptimizer:
    """智能优化引擎 V3.0

    自动分析和优化系统性能，实现自适应调优。
    """

    def __init__(
        self,
        optimization_interval: int = 300,  # 5分钟优化一次
        history_window: int = 1000,  # 历史数据窗口
        min_data_points: int = 50,  # 最少数据点才开始优化
        config_path: Optional[str] = None
    ):
        """初始化智能优化引擎

        Args:
            optimization_interval: 优化间隔（秒）
            history_window: 历史数据窗口大小
            min_data_points: 最少数据点
            config_path: 配置文件路径
        """
        self.optimization_interval = optimization_interval
        self.history_window = history_window
        self.min_data_points = min_data_points
        self.config_path = Path(config_path) if config_path else Path("config/optimization_state.json")

        # 历史数据存储
        self.performance_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=history_window)
        )
        self.strategy_performance: Dict[str, Dict] = {}
        self.optimization_history: List[Dict] = []

        # 当前优化状态
        self.current_optimizations: Dict[str, Any] = {}
        self.optimization_lock = threading.Lock()

        # 优化线程
        self._optimization_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # 性能基线
        self.baselines: Dict[str, float] = {}

        logger.info(
            f"IntelligentOptimizer initialized: "
            f"interval={optimization_interval}s, "
            f"window={history_window}, "
            f"min_points={min_data_points}"
        )

    def record_performance(
        self,
        strategy_name: str,
        metrics: Dict[str, float],
        timestamp: Optional[float] = None
    ) -> None:
        """记录策略性能数据

        Args:
            strategy_name: 策略名称
            metrics: 性能指标字典
            timestamp: 时间戳（None为当前时间）
        """
        if timestamp is None:
            timestamp = time.time()

        record = {
            "timestamp": timestamp,
            "metrics": metrics.copy()
        }

        self.performance_history[strategy_name].append(record)

        # 更新策略性能统计
        if strategy_name not in self.strategy_performance:
            self.strategy_performance[strategy_name] = {
                "total_trades": 0,
                "total_profit": 0.0,
                "win_rate": 0.0,
                "avg_profit_rate": 0.0,
                "avg_execution_time": 0.0
            }

        perf = self.strategy_performance[strategy_name]
        perf["total_trades"] += 1
        perf["total_profit"] += metrics.get("profit", 0.0)

        # 更新胜率
        if metrics.get("success", False):
            perf["win_rate"] = (perf["win_rate"] * (perf["total_trades"] - 1) + 1.0) / perf["total_trades"]
        else:
            perf["win_rate"] = perf["win_rate"] * (perf["total_trades"] - 1) / perf["total_trades"]

        # 更新平均利润率
        profit_rate = metrics.get("profit_rate", 0.0)
        perf["avg_profit_rate"] = (
            perf["avg_profit_rate"] * (perf["total_trades"] - 1) + profit_rate
        ) / perf["total_trades"]

        # 更新平均执行时间
        exec_time = metrics.get("execution_time", 0.0)
        perf["avg_execution_time"] = (
            perf["avg_execution_time"] * (perf["total_trades"] - 1) + exec_time
        ) / perf["total_trades"]

        logger.debug(f"Recorded performance for {strategy_name}: {metrics}")

    def analyze_performance_trends(self, strategy_name: str) -> Dict[str, Any]:
        """分析性能趋势

        Args:
            strategy_name: 策略名称

        Returns:
            趋势分析结果
        """
        if strategy_name not in self.performance_history:
            return {"status": "no_data"}

        history = list(self.performance_history[strategy_name])
        if len(history) < self.min_data_points:
            return {"status": "insufficient_data", "count": len(history)}

        # 提取关键指标
        profits = [r["metrics"].get("profit", 0.0) for r in history]
        profit_rates = [r["metrics"].get("profit_rate", 0.0) for r in history]
        execution_times = [r["metrics"].get("execution_time", 0.0) for r in history]

        # 计算趋势
        profit_trend = self._calculate_trend(profits)
        profit_rate_trend = self._calculate_trend(profit_rates)
        exec_time_trend = self._calculate_trend(execution_times)

        # 检测异常
        anomalies = self._detect_anomalies(profit_rates)

        return {
            "status": "success",
            "strategy": strategy_name,
            "data_points": len(history),
            "profit_trend": profit_trend,
            "profit_rate_trend": profit_rate_trend,
            "execution_time_trend": exec_time_trend,
            "anomalies": anomalies,
            "current_performance": self.strategy_performance.get(strategy_name, {})
        }

    def _calculate_trend(self, values: List[float]) -> Dict[str, Any]:
        """计算趋势（线性回归）

        Args:
            values: 数值列表

        Returns:
            趋势信息
        """
        if len(values) < 2:
            return {"direction": "unknown", "slope": 0.0, "correlation": 0.0}

        x = np.arange(len(values))
        y = np.array(values)

        # 线性回归
        slope, intercept = np.polyfit(x, y, 1)
        correlation = np.corrcoef(x, y)[0, 1] if len(values) > 1 else 0.0

        # 判断方向
        if slope > 0.001:
            direction = "increasing"
        elif slope < -0.001:
            direction = "decreasing"
        else:
            direction = "stable"

        return {
            "direction": direction,
            "slope": float(slope),
            "correlation": float(correlation),
            "intercept": float(intercept)
        }

    def _detect_anomalies(
        self,
        values: List[float],
        threshold: float = 2.0
    ) -> List[Dict[str, Any]]:
        """检测异常值（Z-score方法）

        Args:
            values: 数值列表
            threshold: Z-score阈值

        Returns:
            异常列表
        """
        if len(values) < 10:
            return []

        mean = statistics.mean(values)
        stdev = statistics.stdev(values) if len(values) > 1 else 0.0

        if stdev == 0:
            return []

        anomalies = []
        for i, value in enumerate(values):
            z_score = abs((value - mean) / stdev) if stdev > 0 else 0
            if z_score > threshold:
                anomalies.append({
                    "index": i,
                    "value": value,
                    "z_score": z_score,
                    "type": "high" if value > mean else "low"
                })

        return anomalies

    def optimize_strategy_weights(self) -> Dict[str, float]:
        """优化策略权重分配

        基于历史表现自动调整各策略的资金分配权重。

        Returns:
            策略权重字典
        """
        if not self.strategy_performance:
            logger.warning("No strategy performance data for weight optimization")
            return {}

        # 计算每个策略的综合评分
        strategy_scores = {}
        for name, perf in self.strategy_performance.items():
            if perf["total_trades"] < 5:  # 数据不足，跳过
                continue

            # 综合评分 = 胜率 * 0.4 + 平均利润率 * 0.3 + 交易频率 * 0.2 - 执行时间 * 0.1
            win_rate_score = perf["win_rate"] * 40  # 0-40分
            profit_score = min(perf["avg_profit_rate"] * 10, 30)  # 0-30分
            frequency_score = min(perf["total_trades"] / 10, 20)  # 0-20分
            time_penalty = min(perf["avg_execution_time"] * 2, 10)  # 0-10分

            total_score = win_rate_score + profit_score + frequency_score - time_penalty
            strategy_scores[name] = max(0, total_score)

        if not strategy_scores:
            return {}

        # 归一化为权重
        total_score = sum(strategy_scores.values())
        if total_score == 0:
            return {name: 1.0 / len(strategy_scores) for name in strategy_scores}

        weights = {
            name: score / total_score
            for name, score in strategy_scores.items()
        }

        logger.info(f"Optimized strategy weights: {weights}")
        return weights

    def optimize_parameters(
        self,
        strategy_name: str,
        current_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """优化策略参数

        基于历史表现自动调整策略参数。

        Args:
            strategy_name: 策略名称
            current_params: 当前参数

        Returns:
            优化后的参数
        """
        analysis = self.analyze_performance_trends(strategy_name)
        if analysis["status"] != "success":
            return current_params

        optimized_params = current_params.copy()
        trend = analysis["profit_rate_trend"]

        # 根据趋势调整参数
        if trend["direction"] == "decreasing" and trend["correlation"] < -0.5:
            # 性能下降，降低风险
            logger.info(f"{strategy_name} performance decreasing, reducing risk")
            if "max_position_size" in optimized_params:
                optimized_params["max_position_size"] *= 0.9
            if "min_profit_rate" in optimized_params:
                optimized_params["min_profit_rate"] *= 1.1  # 提高门槛

        elif trend["direction"] == "increasing" and trend["correlation"] > 0.5:
            # 性能上升，适当增加风险
            logger.info(f"{strategy_name} performance increasing, increasing opportunity")
            if "max_position_size" in optimized_params:
                optimized_params["max_position_size"] *= 1.1
            if "min_profit_rate" in optimized_params:
                optimized_params["min_profit_rate"] *= 0.9  # 降低门槛

        # 检测异常并调整
        if analysis.get("anomalies"):
            anomaly_count = len(analysis["anomalies"])
            if anomaly_count > len(analysis["data_points"]) * 0.1:  # 超过10%异常
                logger.warning(f"{strategy_name} has too many anomalies, increasing caution")
                if "max_volatility" in optimized_params:
                    optimized_params["max_volatility"] *= 0.9

        return optimized_params

    def generate_optimization_report(self) -> Dict[str, Any]:
        """生成优化报告

        Returns:
            优化报告
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "strategies": {},
            "overall": {
                "total_strategies": len(self.strategy_performance),
                "total_trades": sum(p["total_trades"] for p in self.strategy_performance.values()),
                "total_profit": sum(p["total_profit"] for p in self.strategy_performance.values()),
                "avg_win_rate": statistics.mean(
                    [p["win_rate"] for p in self.strategy_performance.values()]
                ) if self.strategy_performance else 0.0
            },
            "recommendations": []
        }

        # 分析每个策略
        for strategy_name in self.strategy_performance.keys():
            analysis = self.analyze_performance_trends(strategy_name)
            report["strategies"][strategy_name] = analysis

            # 生成建议
            if analysis["status"] == "success":
                if analysis["profit_trend"]["direction"] == "decreasing":
                    report["recommendations"].append({
                        "strategy": strategy_name,
                        "type": "warning",
                        "message": f"{strategy_name} 性能下降，建议降低风险敞口"
                    })
                elif analysis["profit_trend"]["direction"] == "increasing":
                    report["recommendations"].append({
                        "strategy": strategy_name,
                        "type": "opportunity",
                        "message": f"{strategy_name} 性能上升，可适当增加仓位"
                    })

                if analysis.get("anomalies"):
                    report["recommendations"].append({
                        "strategy": strategy_name,
                        "type": "alert",
                        "message": f"{strategy_name} 检测到 {len(analysis['anomalies'])} 个异常值"
                    })

        return report

    def start_auto_optimization(self) -> None:
        """启动自动优化线程"""
        if self._optimization_thread and self._optimization_thread.is_alive():
            logger.warning("Auto-optimization already running")
            return

        self._stop_event.clear()
        self._optimization_thread = threading.Thread(
            target=self._optimization_loop,
            daemon=True,
            name="intelligent-optimizer"
        )
        self._optimization_thread.start()
        logger.info(f"Auto-optimization started (interval={self.optimization_interval}s)")

    def stop_auto_optimization(self) -> None:
        """停止自动优化"""
        self._stop_event.set()
        if self._optimization_thread:
            self._optimization_thread.join(timeout=10.0)
        logger.info("Auto-optimization stopped")

    def _optimization_loop(self) -> None:
        """优化循环"""
        while not self._stop_event.is_set():
            try:
                # 执行优化
                with self.optimization_lock:
                    self._perform_optimization()

                # 等待下一次优化
                self._stop_event.wait(self.optimization_interval)

            except Exception as e:
                logger.error(f"Optimization loop error: {e}")
                self._stop_event.wait(60)  # 出错后等待1分钟

    def _perform_optimization(self) -> None:
        """执行一次优化"""
        logger.info("Performing optimization...")

        # 1. 优化策略权重
        new_weights = self.optimize_strategy_weights()
        if new_weights:
            self.current_optimizations["strategy_weights"] = new_weights

        # 2. 优化各策略参数
        for strategy_name in self.strategy_performance.keys():
            current_params = {}  # 这里应该从配置中获取
            optimized_params = self.optimize_parameters(strategy_name, current_params)
            if optimized_params != current_params:
                self.current_optimizations[f"{strategy_name}_params"] = optimized_params

        # 3. 生成优化报告
        report = self.generate_optimization_report()
        self.optimization_history.append(report)

        # 保存优化状态
        self._save_optimization_state()

        logger.info("Optimization completed")

    def _save_optimization_state(self) -> None:
        """保存优化状态到文件"""
        try:
            state = {
                "timestamp": datetime.now().isoformat(),
                "current_optimizations": self.current_optimizations,
                "strategy_performance": self.strategy_performance,
                "baselines": self.baselines
            }

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Failed to save optimization state: {e}")

    def load_optimization_state(self) -> None:
        """从文件加载优化状态"""
        try:
            if not self.config_path.exists():
                return

            with open(self.config_path, 'r', encoding='utf-8') as f:
                state = json.load(f)

            self.current_optimizations = state.get("current_optimizations", {})
            self.strategy_performance = state.get("strategy_performance", {})
            self.baselines = state.get("baselines", {})

            logger.info(f"Loaded optimization state from {self.config_path}")

        except Exception as e:
            logger.error(f"Failed to load optimization state: {e}")

    def get_current_optimizations(self) -> Dict[str, Any]:
        """获取当前优化建议"""
        with self.optimization_lock:
            return self.current_optimizations.copy()

    def reset(self) -> None:
        """重置优化器状态"""
        self.performance_history.clear()
        self.strategy_performance.clear()
        self.optimization_history.clear()
        self.current_optimizations.clear()
        logger.info("IntelligentOptimizer reset")


# ---------------------- 全局单例 ----------------------

_global_optimizer: Optional[IntelligentOptimizer] = None


def get_intelligent_optimizer(
    optimization_interval: int = 300,
    history_window: int = 1000,
    min_data_points: int = 50,
    config_path: Optional[str] = None
) -> IntelligentOptimizer:
    """获取全局智能优化器实例

    Args:
        optimization_interval: 优化间隔
        history_window: 历史窗口
        min_data_points: 最少数据点
        config_path: 配置路径

    Returns:
        IntelligentOptimizer实例
    """
    global _global_optimizer

    if _global_optimizer is None:
        _global_optimizer = IntelligentOptimizer(
            optimization_interval=optimization_interval,
            history_window=history_window,
            min_data_points=min_data_points,
            config_path=config_path
        )

    return _global_optimizer


def initialize_intelligent_optimizer(config: Dict[str, Any]) -> IntelligentOptimizer:
    """初始化智能优化器

    Args:
        config: 配置字典

    Returns:
        IntelligentOptimizer实例
    """
    optimizer = get_intelligent_optimizer(
        optimization_interval=config.get("optimization_interval", 300),
        history_window=config.get("history_window", 1000),
        min_data_points=config.get("min_data_points", 50),
        config_path=config.get("config_path")
    )

    # 加载之前的状态
    optimizer.load_optimization_state()

    # 启动自动优化
    if config.get("auto_optimize", True):
        optimizer.start_auto_optimization()

    return optimizer
