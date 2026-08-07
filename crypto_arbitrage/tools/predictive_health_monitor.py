"""预测性健康监控器 (PredictiveHealthMonitor)

V3.9 迭代核心模块 - 系统健康预测和主动预防

功能：
1. 趋势分析引擎 - 性能、资源、错误率趋势分析
2. 异常预测模型 - ML 和统计异常检测
3. 主动预防机制 - 性能优化和资源清理建议
4. 智能告警系统 - 分级告警和多通道通知

核心组件：
- TrendAnalysisEngine: 趋势分析引擎
- AnomalyPredictionModel: 异常预测模型
- PreventiveActionsEngine: 主动预防引擎
- PredictiveHealthMonitor: 预测性健康监控器主类
"""

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ==================== 数据结构定义 ====================

class TrendDirection(Enum):
    """趋势方向"""
    UP = "up"
    DOWN = "down"
    STABLE = "stable"


class AlertSeverity(Enum):
    """告警严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyType(Enum):
    """异常类型"""
    PERFORMANCE_DEGRADATION = "performance_degradation"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    MEMORY_LEAK = "memory_leak"
    CONNECTION_FAILURE = "connection_failure"
    ERROR_SPIKE = "error_spike"


@dataclass
class TrendInfo:
    """趋势信息

    Attributes:
        metric_name: 指标名称
        direction: 趋势方向
        strength: 趋势强度 (0-1)
        current_value: 当前值
        predicted_value: 预测值
        confidence: 置信度 (0-1)
    """
    metric_name: str
    direction: TrendDirection
    strength: float
    current_value: float
    predicted_value: float
    confidence: float


@dataclass
class AnomalyPrediction:
    """异常预测

    Attributes:
        anomaly_type: 异常类型
        confidence: 置信度 (0-1)
        impact_level: 影响等级 (0-1)
        estimated_time: 预计发生时间（时间戳）
        recommended_action: 建议采取的行动
    """
    anomaly_type: AnomalyType
    confidence: float
    impact_level: float
    estimated_time: float
    recommended_action: str


@dataclass
class PreventiveAction:
    """预防性行动

    Attributes:
        action_type: 行动类型
        description: 描述
        priority: 优先级 (1-10, 10 最高)
        estimated_impact: 预估影响 (0-1)
        execution_time: 预估执行时间（秒）
    """
    action_type: str
    description: str
    priority: int
    estimated_impact: float
    execution_time: float


@dataclass
class HealthPrediction:
    """健康预测

    Attributes:
        overall_health_score: 整体健康分数 (0-1)
        trends: 趋势信息列表
        anomalies: 异常预测列表
        actions: 预防性行动列表
        timestamp: 时间戳
    """
    overall_health_score: float
    trends: List[TrendInfo]
    anomalies: List[AnomalyPrediction]
    actions: List[PreventiveAction]
    timestamp: float


# ==================== 趋势分析引擎 ====================

class TrendAnalysisEngine:
    """趋势分析引擎

    分析系统各项指标的趋势，预测未来变化。
    """

    # 类常量
    DEFAULT_WINDOW_SIZE: int = 50
    MIN_DATA_POINTS: int = 10
    MAX_DATA_POINTS: int = 200

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化趋势分析引擎

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.window_size = self.config.get('window_size', self.DEFAULT_WINDOW_SIZE)

        # 存储历史指标数据
        self._metrics_history: Dict[str, deque] = {}

        logger.info("✅ TrendAnalysisEngine 初始化完成")

    def analyze_metrics(self, current_metrics: Dict[str, float]) -> Dict[str, TrendInfo]:
        """分析指标趋势

        Args:
            current_metrics: 当前指标字典

        Returns:
            Dict[str, TrendInfo]: 指标趋势信息字典
        """
        trends = {}

        for metric_name, current_value in current_metrics.items():
            # 获取历史数据
            if metric_name not in self._metrics_history:
                self._metrics_history[metric_name] = deque(maxlen=self.MAX_DATA_POINTS)

            history = self._metrics_history[metric_name]
            history.append(current_value)

            # 分析趋势
            if len(history) >= self.MIN_DATA_POINTS:
                trend = self._analyze_single_trend(metric_name, list(history), current_value)
                trends[metric_name] = trend
            else:
                # 数据不足，创建默认趋势
                trends[metric_name] = TrendInfo(
                    metric_name=metric_name,
                    direction=TrendDirection.STABLE,
                    strength=0.0,
                    current_value=current_value,
                    predicted_value=current_value,
                    confidence=0.0
                )

        return trends

    def _analyze_single_trend(
        self,
        metric_name: str,
        history: List[float],
        current_value: float
    ) -> TrendInfo:
        """分析单个指标的趋势

        Args:
            metric_name: 指标名称
            history: 历史数据
            current_value: 当前值

        Returns:
            TrendInfo: 趋势信息
        """
        # 计算移动平均
        short_window = min(10, len(history))
        long_window = min(30, len(history))

        short_sma = sum(history[-short_window:]) / short_window
        long_sma = sum(history[-long_window:]) / long_window

        # 确定趋势方向（优化阈值以适应不同场景）
        if short_sma > long_sma * 1.03:  # 3% 以上差异为上升（从5%降低）
            direction = TrendDirection.UP
        elif short_sma < long_sma * 0.97:  # 3% 以下差异为下降（从5%降低）
            direction = TrendDirection.DOWN
        else:
            direction = TrendDirection.STABLE

        # 计算趋势强度
        if long_sma != 0:
            strength = abs(short_sma - long_sma) / long_sma
        else:
            strength = 0.0

        # 预测下一个值
        if direction == TrendDirection.UP:
            predicted = current_value * (1 + strength * 0.1)
        elif direction == TrendDirection.DOWN:
            predicted = current_value * (1 - strength * 0.1)
        else:
            predicted = current_value

        # 计算置信度
        confidence = min(len(history) / 30.0, 1.0)

        return TrendInfo(
            metric_name=metric_name,
            direction=direction,
            strength=min(strength, 1.0),
            current_value=current_value,
            predicted_value=predicted,
            confidence=confidence
        )

    def predict_performance_degradation(
        self,
        current_metrics: Dict[str, float]
    ) -> List[TrendInfo]:
        """预测性能降级

        Args:
            current_metrics: 当前指标

        Returns:
            List[TrendInfo]: 性能降级趋势列表
        """
        degradation_trends = []

        # 分析关键性能指标
        key_metrics = ['response_time', 'latency', 'error_rate', 'throughput']

        for metric_name in key_metrics:
            if metric_name in current_metrics:
                trend = self._metrics_history.get(metric_name)
                if trend and len(trend) >= 10:
                    # 检查是否有降级趋势
                    recent_values = list(trend)[-10:]
                    if self._is_decreasing_trend(recent_values) and metric_name in ['throughput']:
                        degradation_trends.append(
                            self._analyze_single_trend(metric_name, list(trend), current_metrics[metric_name])
                        )
                    elif self._is_increasing_trend(recent_values) and metric_name in ['response_time', 'latency', 'error_rate']:
                        degradation_trends.append(
                            self._analyze_single_trend(metric_name, list(trend), current_metrics[metric_name])
                        )

        return degradation_trends

    def _is_decreasing_trend(self, values: List[float]) -> bool:
        """判断是否为下降趋势"""
        if len(values) < 3:
            return False

        # 简单线性回归
        x = list(range(len(values)))
        y = values
        n = len(x)

        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))

        if n * sum_x2 - sum_x ** 2 == 0:
            return False

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        return slope < -0.01

    def _is_increasing_trend(self, values: List[float]) -> bool:
        """判断是否为上升趋势"""
        if len(values) < 3:
            return False

        # 简单线性回归
        x = list(range(len(values)))
        y = values
        n = len(x)

        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))

        if n * sum_x2 - sum_x ** 2 == 0:
            return False

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        return slope > 0.01


# ==================== 异常预测模型 ====================

class AnomalyPredictionModel:
    """异常预测模型

    基于统计和机器学习方法预测异常。
    """

    # 类常量
    DEFAULT_ANOMALY_THRESHOLD: float = 0.7
    MIN_HISTORY_LENGTH: int = 10  # 从20降低到10，提高检测灵敏度

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化异常预测模型

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.anomaly_threshold = self.config.get('anomaly_threshold', self.DEFAULT_ANOMALY_THRESHOLD)

        # 存储历史数据用于基线计算
        self._baseline_metrics: Dict[str, List[float]] = {}

        logger.info("✅ AnomalyPredictionModel 初始化完成")

    def predict_anomalies(
        self,
        current_metrics: Dict[str, float]
    ) -> List[AnomalyPrediction]:
        """预测异常

        Args:
            current_metrics: 当前指标

        Returns:
            List[AnomalyPrediction]: 异常预测列表
        """
        anomalies = []

        # 更新基线数据
        for metric_name, value in current_metrics.items():
            if metric_name not in self._baseline_metrics:
                self._baseline_metrics[metric_name] = []
            self._baseline_metrics[metric_name].append(value)
            if len(self._baseline_metrics[metric_name]) > 100:
                self._baseline_metrics[metric_name].pop(0)

        # 检测各种异常
        anomalies.extend(self._detect_performance_anomalies(current_metrics))
        anomalies.extend(self._detect_resource_anomalies(current_metrics))
        anomalies.extend(self._detect_error_anomalies(current_metrics))

        return anomalies

    def _detect_performance_anomalies(
        self,
        metrics: Dict[str, float]
    ) -> List[AnomalyPrediction]:
        """检测性能异常"""
        anomalies = []

        # 检查响应时间
        if 'response_time' in metrics:
            current_rt = metrics['response_time']
            if 'response_time' in self._baseline_metrics and len(self._baseline_metrics['response_time']) >= self.MIN_HISTORY_LENGTH:
                baseline = self._baseline_metrics['response_time']
                avg_rt = sum(baseline) / len(baseline)
                std_rt = (sum((x - avg_rt) ** 2 for x in baseline) / len(baseline)) ** 0.5

                if std_rt > 0 and (current_rt - avg_rt) / std_rt > 3:
                    anomalies.append(AnomalyPrediction(
                        anomaly_type=AnomalyType.PERFORMANCE_DEGRADATION,
                        confidence=min((current_rt - avg_rt) / avg_rt, 1.0),
                        impact_level=0.8,
                        estimated_time=time.time() + 300,  # 5分钟后
                        recommended_action="检查数据库查询和外部API调用"
                    ))

        # 检查延迟
        if 'latency' in metrics:
            current_latency = metrics['latency']
            if 'latency' in self._baseline_metrics and len(self._baseline_metrics['latency']) >= self.MIN_HISTORY_LENGTH:
                baseline = self._baseline_metrics['latency']
                avg_latency = sum(baseline) / len(baseline)

                if current_latency > avg_latency * 2:
                    anomalies.append(AnomalyPrediction(
                        anomaly_type=AnomalyType.PERFORMANCE_DEGRADATION,
                        confidence=min((current_latency - avg_latency) / avg_latency, 1.0),
                        impact_level=0.6,
                        estimated_time=time.time() + 600,  # 10分钟后
                        recommended_action="优化网络连接和缓存策略"
                    ))

        return anomalies

    def _detect_resource_anomalies(
        self,
        metrics: Dict[str, float]
    ) -> List[AnomalyPrediction]:
        """检测资源异常"""
        anomalies = []

        # 检查内存使用
        if 'memory_usage' in metrics:
            memory_usage = metrics['memory_usage']
            if memory_usage > 0.9:  # 超过90%
                anomalies.append(AnomalyPrediction(
                    anomaly_type=AnomalyType.MEMORY_LEAK,
                    confidence=memory_usage,
                    impact_level=0.9,
                    estimated_time=time.time() + 1800,  # 30分钟后
                    recommended_action="检查内存泄漏，考虑重启服务"
                ))

        # 检查磁盘使用
        if 'disk_usage' in metrics:
            disk_usage = metrics['disk_usage']
            if disk_usage > 0.85:  # 超过85%
                anomalies.append(AnomalyPrediction(
                    anomaly_type=AnomalyType.RESOURCE_EXHAUSTION,
                    confidence=disk_usage,
                    impact_level=0.7,
                    estimated_time=time.time() + 3600,  # 1小时后
                    recommended_action="清理日志和临时文件，扩展磁盘空间"
                ))

        return anomalies

    def _detect_error_anomalies(
        self,
        metrics: Dict[str, float]
    ) -> List[AnomalyPrediction]:
        """检测错误异常"""
        anomalies = []

        # 检查错误率
        if 'error_rate' in metrics:
            error_rate = metrics['error_rate']
            if 'error_rate' in self._baseline_metrics and len(self._baseline_metrics['error_rate']) >= self.MIN_HISTORY_LENGTH:
                baseline = self._baseline_metrics['error_rate']
                avg_error_rate = sum(baseline) / len(baseline)

                if error_rate > avg_error_rate * 3 and error_rate > 0.05:  # 错误率突增
                    anomalies.append(AnomalyPrediction(
                        anomaly_type=AnomalyType.ERROR_SPIKE,
                        confidence=min(error_rate, 1.0),
                        impact_level=0.8,
                        estimated_time=time.time() + 600,  # 10分钟后
                        recommended_action="检查日志，识别错误源头，增加重试机制"
                    ))

        return anomalies

    def detect_performance_degradation(
        self,
        performance_history: List[float]
    ) -> Optional[AnomalyPrediction]:
        """检测性能降级模式

        Args:
            performance_history: 性能历史数据

        Returns:
            Optional[AnomalyPrediction]: 性能降级预测，如果没有则返回 None
        """
        if len(performance_history) < self.MIN_HISTORY_LENGTH:
            return None

        # 计算性能降级率（动态调整窗口大小）
        data_length = len(performance_history)
        recent_window = min(10, data_length // 2)  # 动态窗口大小

        recent_performance = performance_history[-recent_window:]
        baseline_performance = sum(performance_history[:-recent_window]) / len(performance_history[:-recent_window]) if len(performance_history[:-recent_window]) > 0 else performance_history[0]
        current_performance = sum(recent_performance) / len(recent_performance)

        if baseline_performance > 0:
            degradation_rate = (baseline_performance - current_performance) / baseline_performance
        else:
            degradation_rate = 0.0

        # 性能下降超过10%（从15%降低到10%，提高检测灵敏度）
        if degradation_rate > 0.10:
            # 估算剩余时间
            if degradation_rate > 0.05:
                time_to_failure = int((current_performance / degradation_rate) * 60)  # 分钟
            else:
                time_to_failure = 60

            return AnomalyPrediction(
                anomaly_type=AnomalyType.PERFORMANCE_DEGRADATION,
                confidence=min(degradation_rate * 5, 1.0),  # 放大置信度
                impact_level=degradation_rate,
                estimated_time=time.time() + time_to_failure * 60,
                recommended_action=f"性能下降 {degradation_rate:.1%}，预计 {time_to_failure} 分钟后达到临界点"
            )

        return None


# ==================== 主动预防引擎 ====================

class PreventiveActionsEngine:
    """主动预防引擎

    基于预测结果推荐预防性行动。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化主动预防引擎

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self._action_history: List[Dict] = []

        logger.info("✅ PreventiveActionsEngine 初始化完成")

    def recommend_actions(
        self,
        predictions: List[AnomalyPrediction]
    ) -> List[PreventiveAction]:
        """推荐预防性行动

        Args:
            predictions: 异常预测列表

        Returns:
            List[PreventiveAction]: 预防性行动列表
        """
        actions = []

        for prediction in predictions:
            # 根据异常类型推荐行动
            if prediction.anomaly_type == AnomalyType.PERFORMANCE_DEGRADATION:
                actions.extend(self._get_performance_actions(prediction))
            elif prediction.anomaly_type == AnomalyType.RESOURCE_EXHAUSTION:
                actions.extend(self._get_resource_actions(prediction))
            elif prediction.anomaly_type == AnomalyType.MEMORY_LEAK:
                actions.extend(self._get_memory_actions(prediction))
            elif prediction.anomaly_type == AnomalyType.CONNECTION_FAILURE:
                actions.extend(self._get_connectivity_actions(prediction))
            elif prediction.anomaly_type == AnomalyType.ERROR_SPIKE:
                actions.extend(self._get_error_actions(prediction))

        # 按优先级排序
        actions.sort(key=lambda x: x.priority, reverse=True)

        return actions[:10]  # 返回前10个最重要的行动

    def _get_performance_actions(
        self,
        prediction: AnomalyPrediction
    ) -> List[PreventiveAction]:
        """获取性能优化行动"""
        actions = []

        actions.append(PreventiveAction(
            action_type="clear_cache",
            description="清理系统缓存，释放内存",
            priority=8,
            estimated_impact=0.6,
            execution_time=30
        ))

        actions.append(PreventiveAction(
            action_type="optimize_database",
            description="优化数据库查询和索引",
            priority=7,
            estimated_impact=0.7,
            execution_time=300
        ))

        actions.append(PreventiveAction(
            action_type="scale_resources",
            description="增加计算资源（CPU/内存）",
            priority=6,
            estimated_impact=0.8,
            execution_time=600
        ))

        return actions

    def _get_resource_actions(
        self,
        prediction: AnomalyPrediction
    ) -> List[PreventiveAction]:
        """获取资源优化行动"""
        actions = []

        actions.append(PreventiveAction(
            action_type="clean_logs",
            description="清理和压缩日志文件",
            priority=9,
            estimated_impact=0.5,
            execution_time=120
        ))

        actions.append(PreventiveAction(
            action_type="cleanup_temp_files",
            description="删除临时文件和缓存",
            priority=8,
            estimated_impact=0.4,
            execution_time=60
        ))

        actions.append(PreventiveAction(
            action_type="expand_storage",
            description="扩展磁盘存储空间",
            priority=7,
            estimated_impact=0.9,
            execution_time=1800
        ))

        return actions

    def _get_memory_actions(
        self,
        prediction: AnomalyPrediction
    ) -> List[PreventiveAction]:
        """获取内存优化行动"""
        actions = []

        actions.append(PreventiveAction(
            action_type="restart_service",
            description="重启服务以释放内存",
            priority=10,
            estimated_impact=0.9,
            execution_time=60
        ))

        actions.append(PreventiveAction(
            action_type="reduce_cache_size",
            description="减少缓存大小限制",
            priority=8,
            estimated_impact=0.6,
            execution_time=10
        ))

        actions.append(PreventiveAction(
            action_type="memory_profiling",
            description="进行内存分析，识别泄漏点",
            priority=7,
            estimated_impact=0.7,
            execution_time=600
        ))

        return actions

    def _get_connectivity_actions(
        self,
        prediction: AnomalyPrediction
    ) -> List[PreventiveAction]:
        """获取连接优化行动"""
        actions = []

        actions.append(PreventiveAction(
            action_type="check_network",
            description="检查网络连接和DNS解析",
            priority=9,
            estimated_impact=0.8,
            execution_time=30
        ))

        actions.append(PreventiveAction(
            action_type="increase_retries",
            description="增加API调用重试次数和超时时间",
            priority=7,
            estimated_impact=0.5,
            execution_time=10
        ))

        actions.append(PreventiveAction(
            action_type="enable_fallback",
            description="启用降级模式，使用本地缓存",
            priority=8,
            estimated_impact=0.7,
            execution_time=5
        ))

        return actions

    def _get_error_actions(
        self,
        prediction: AnomalyPrediction
    ) -> List[PreventiveAction]:
        """获取错误处理行动"""
        actions = []

        actions.append(PreventiveAction(
            action_type="analyze_logs",
            description="分析错误日志，识别根本原因",
            priority=9,
            estimated_impact=0.7,
            execution_time=300
        ))

        actions.append(PreventiveAction(
            action_type="enable_circuit_breaker",
            description="启用熔断器，防止级联故障",
            priority=8,
            estimated_impact=0.8,
            execution_time=10
        ))

        actions.append(PreventiveAction(
            action_type="increase_monitoring",
            description="增加监控频率，实时跟踪错误",
            priority=7,
            estimated_impact=0.5,
            execution_time=10
        ))

        return actions


# ==================== 预测性健康监控器主类 ====================

class PredictiveHealthMonitor:
    """预测性健康监控器

    整合趋势分析、异常预测和主动预防，提供全面的系统健康监控。
    """

    # 类常量
    DEFAULT_CHECK_INTERVAL: int = 60  # 60秒
    HEALTH_SCORE_THRESHOLD: float = 0.7

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化预测性健康监控器

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 初始化子组件
        self.trend_engine = TrendAnalysisEngine(self.config.get('trend_analysis', {}))
        self.anomaly_model = AnomalyPredictionModel(self.config.get('anomaly_prediction', {}))
        self.preventive_engine = PreventiveActionsEngine(self.config.get('preventive_actions', {}))

        # 历史预测
        self._prediction_history: deque = deque(maxlen=100)

        logger.info("✅ PredictiveHealthMonitor 初始化完成")

    def predict_health(
        self,
        current_metrics: Dict[str, float]
    ) -> HealthPrediction:
        """预测系统健康状态

        Args:
            current_metrics: 当前系统指标

        Returns:
            HealthPrediction: 健康预测结果
        """
        # 1. 分析趋势
        trends = self.trend_engine.analyze_metrics(current_metrics)

        # 2. 预测异常
        anomalies = self.anomaly_model.predict_anomalies(current_metrics)

        # 3. 推荐预防行动
        actions = self.preventive_engine.recommend_actions(anomalies)

        # 4. 计算整体健康分数
        health_score = self._calculate_health_score(current_metrics, trends, anomalies)

        # 5. 创建预测结果
        prediction = HealthPrediction(
            overall_health_score=health_score,
            trends=list(trends.values()),
            anomalies=anomalies,
            actions=actions,
            timestamp=time.time()
        )

        # 6. 保存到历史
        self._prediction_history.append(prediction)

        return prediction

    def _calculate_health_score(
        self,
        current_metrics: Dict[str, float],
        trends: Dict[str, TrendInfo],
        anomalies: List[AnomalyPrediction]
    ) -> float:
        """计算整体健康分数

        Args:
            current_metrics: 当前指标
            trends: 趋势信息
            anomalies: 异常预测

        Returns:
            float: 健康分数 (0-1)
        """
        score = 1.0

        # 基于异常降低分数
        for anomaly in anomalies:
            score -= anomaly.impact_level * anomaly.confidence * 0.3

        # 基于趋势调整分数
        for trend in trends.values():
            if trend.direction == TrendDirection.UP and 'error' in trend.metric_name.lower():
                score -= trend.strength * 0.1
            elif trend.direction == TrendDirection.DOWN and 'performance' in trend.metric_name.lower():
                score -= trend.strength * 0.1

        # 基于当前指标调整分数
        if 'error_rate' in current_metrics:
            score -= current_metrics['error_rate'] * 0.5

        if 'memory_usage' in current_metrics:
            if current_metrics['memory_usage'] > 0.9:
                score -= 0.2
            elif current_metrics['memory_usage'] > 0.8:
                score -= 0.1

        # 确保分数在有效范围内
        return max(0.0, min(1.0, score))

    def get_prediction_summary(self) -> Dict[str, Any]:
        """获取预测摘要

        Returns:
            Dict[str, Any]: 预测摘要
        """
        if not self._prediction_history:
            return {
                "total_predictions": 0,
                "average_health_score": 0.0,
                "recent_anomalies": [],
                "recommended_actions": []
            }

        # 计算平均健康分数
        avg_health = sum(p.overall_health_score for p in self._prediction_history) / len(self._prediction_history)

        # 获取最近的异常
        recent_prediction = self._prediction_history[-1]
        recent_anomalies = [
            {
                "type": a.anomaly_type.value,
                "confidence": f"{a.confidence:.2%}",
                "impact": f"{a.impact_level:.2%}",
                "action": a.recommended_action
            }
            for a in recent_prediction.anomalies
        ]

        # 获取推荐行动
        recommended_actions = [
            {
                "type": a.action_type,
                "description": a.description,
                "priority": a.priority,
                "impact": f"{a.estimated_impact:.2%}"
            }
            for a in recent_prediction.actions[:5]  # 前5个
        ]

        return {
            "total_predictions": len(self._prediction_history),
            "average_health_score": avg_health,
            "recent_anomalies": recent_anomalies,
            "recommended_actions": recommended_actions,
            "last_prediction_time": recent_prediction.timestamp
        }
