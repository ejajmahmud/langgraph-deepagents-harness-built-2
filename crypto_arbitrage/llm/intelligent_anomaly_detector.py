"""智能异常检测和诊断系统 V3.7
利用 Memo0 的知识推理和模式识别能力，实现智能化的异常检测和诊断

核心功能:
1. 多维度异常检测 - 价格/成交量/波动率/流动性/系统性能
2. 智能异常分类 - 市场异常/系统异常/策略异常
3. 异常原因分析 - 基于知识库的智能推理
4. 自动恢复建议 - 提供针对性的恢复策略
5. 异常预测 - 基于历史模式的预测性分析
6. 异常学习 - 从异常事件中自动学习和优化
"""

import asyncio
import logging
import numpy as np
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
import json

logger = logging.getLogger(__name__)


class AnomalyType(Enum):
    """异常类型"""
    PRICE = "price_anomaly"
    VOLUME = "volume_anomaly"
    VOLATILITY = "volatility_anomaly"
    LIQUIDITY = "liquidity_anomaly"
    PERFORMANCE = "performance_anomaly"
    NETWORK = "network_anomaly"
    STRATEGY = "strategy_anomaly"
    SYSTEM = "system_anomaly"


class AnomalySeverity(Enum):
    """异常严重程度"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AnomalyCategory(Enum):
    """异常类别"""
    MARKET = "market"  # 市场异常
    SYSTEM = "system"  # 系统异常
    STRATEGY = "strategy"  # 策略异常
    OPERATION = "operation"  # 运营异常


@dataclass
class AnomalyDetectionResult:
    """异常检测结果"""
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    category: AnomalyCategory
    description: str
    confidence: float  # 0-1
    metrics: Dict[str, float]
    timestamp: datetime
    detected_by: str  # 检测算法名称


@dataclass
class AnomalyDiagnosis:
    """异常诊断结果"""
    detection_result: AnomalyDetectionResult
    root_cause: str
    impact_assessment: str
    recommended_actions: List[str]
    supporting_knowledge: List[Dict[str, Any]]
    recovery_strategy: Optional[str] = None
    predicted_duration: Optional[float] = None  # 预计恢复时间（秒）
    estimated_risk: Optional[str] = None


@dataclass
class AnomalyPrediction:
    """异常预测结果"""
    predicted_type: AnomalyType
    predicted_severity: AnomalySeverity
    probability: float
    time_window: Tuple[datetime, datetime]  # 预测时间窗口
    warning_message: str
    preventive_actions: List[str]


class StatisticalAnomalyDetector:
    """统计异常检测器 - 基于 Z-Score 和 IQR"""

    def __init__(self, config: Dict[str, Any]):
        """初始化统计异常检测器

        Args:
            config: 配置字典
        """
        self.z_score_threshold = config.get('z_score_threshold', 3.0)
        self.iqr_multiplier = config.get('iqr_multiplier', 1.5)
        self.min_samples = config.get('min_samples', 30)

        # 历史数据缓存
        self.price_history = deque(maxlen=1000)
        self.volume_history = deque(maxlen=1000)
        self.volatility_history = deque(maxlen=1000)
        self.liquidity_history = deque(maxlen=1000)

        # 统计参数
        self.price_stats = {}
        self.volume_stats = {}
        self.volatility_stats = {}
        self.liquidity_stats = {}

        logger.info("统计异常检测器初始化完成")

    def update_stats(self, market_data: Dict[str, Any]) -> None:
        """更新统计参数

        Args:
            market_data: 市场数据
        """
        # 更新历史数据
        if 'price' in market_data:
            self.price_history.append(market_data['price'])
        if 'volume' in market_data:
            self.volume_history.append(market_data['volume'])
        if 'volatility' in market_data:
            self.volatility_history.append(market_data['volatility'])
        if 'liquidity_score' in market_data:
            self.liquidity_history.append(market_data['liquidity_score'])

        # 重新计算统计参数
        if len(self.price_history) >= self.min_samples:
            self.price_stats = self._calculate_statistics(list(self.price_history))
        if len(self.volume_history) >= self.min_samples:
            self.volume_stats = self._calculate_statistics(list(self.volume_history))
        if len(self.volatility_history) >= self.min_samples:
            self.volatility_stats = self._calculate_statistics(list(self.volatility_history))
        if len(self.liquidity_history) >= self.min_samples:
            self.liquidity_stats = self._calculate_statistics(list(self.liquidity_history))

    def _calculate_statistics(self, data: List[float]) -> Dict[str, float]:
        """计算统计参数"""
        data_array = np.array(data)
        return {
            'mean': float(np.mean(data_array)),
            'std': float(np.std(data_array)),
            'q1': float(np.percentile(data_array, 25)),
            'q3': float(np.percentile(data_array, 75)),
            'iqr': float(np.percentile(data_array, 75) - np.percentile(data_array, 25)),
            'min': float(np.min(data_array)),
            'max': float(np.max(data_array))
        }

    def detect_price_anomaly(self, current_price: float) -> Optional[AnomalyDetectionResult]:
        """检测价格异常

        Args:
            current_price: 当前价格

        Returns:
            异常检测结果，如果没有异常则返回 None
        """
        if not self.price_stats:
            return None

        # Z-Score 检测
        z_score = abs(current_price - self.price_stats['mean']) / self.price_stats['std']

        # IQR 检测
        q1, q3 = self.price_stats['q1'], self.price_stats['q3']
        iqr = self.price_stats['iqr']
        lower_bound = q1 - self.iqr_multiplier * iqr
        upper_bound = q3 + self.iqr_multiplier * iqr

        # 判断是否异常
        is_z_anomaly = z_score > self.z_score_threshold
        is_iqr_anomaly = current_price < lower_bound or current_price > upper_bound

        if is_z_anomaly or is_iqr_anomaly:
            # 计算置信度
            confidence = max(z_score / self.z_score_threshold,
                          min(abs(current_price - lower_bound) / iqr if current_price < lower_bound else 0,
                              abs(current_price - upper_bound) / iqr if current_price > upper_bound else 0))
            confidence = min(confidence, 1.0)

            # 确定严重程度
            if z_score > 5.0:
                severity = AnomalySeverity.CRITICAL
            elif z_score > 4.0:
                severity = AnomalySeverity.ERROR
            elif z_score > 3.0:
                severity = AnomalySeverity.WARNING
            else:
                severity = AnomalySeverity.INFO

            return AnomalyDetectionResult(
                anomaly_type=AnomalyType.PRICE,
                severity=severity,
                category=AnomalyCategory.MARKET,
                description=f"价格异常: Z-Score={z_score:.2f}, 正常范围=[{lower_bound:.2f}, {upper_bound:.2f}]",
                confidence=confidence,
                metrics={
                    'z_score': z_score,
                    'current_price': current_price,
                    'mean': self.price_stats['mean'],
                    'std': self.price_stats['std'],
                    'lower_bound': lower_bound,
                    'upper_bound': upper_bound
                },
                timestamp=datetime.now(),
                detected_by="StatisticalDetector"
            )

        return None

    def detect_volume_anomaly(self, current_volume: float) -> Optional[AnomalyDetectionResult]:
        """检测成交量异常

        Args:
            current_volume: 当前成交量

        Returns:
            异常检测结果
        """
        if not self.volume_stats:
            return None

        # Z-Score 检测
        z_score = abs(current_volume - self.volume_stats['mean']) / self.volume_stats['std']

        if z_score > self.z_score_threshold:
            # 确定异常方向（激增或暴跌）
            direction = "激增" if current_volume > self.volume_stats['mean'] else "暴跌"

            # 严重程度
            if z_score > 5.0:
                severity = AnomalySeverity.CRITICAL
            elif z_score > 4.0:
                severity = AnomalySeverity.ERROR
            else:
                severity = AnomalySeverity.WARNING

            return AnomalyDetectionResult(
                anomaly_type=AnomalyType.VOLUME,
                severity=severity,
                category=AnomalyCategory.MARKET,
                description=f"成交量{direction}: Z-Score={z_score:.2f}, 平均={self.volume_stats['mean']:.2f}",
                confidence=min(z_score / self.z_score_threshold, 1.0),
                metrics={
                    'z_score': z_score,
                    'current_volume': current_volume,
                    'mean': self.volume_stats['mean'],
                    'std': self.volume_stats['std']
                },
                timestamp=datetime.now(),
                detected_by="StatisticalDetector"
            )

        return None

    def detect_volatility_anomaly(self, current_volatility: float) -> Optional[AnomalyDetectionResult]:
        """检测波动率异常

        Args:
            current_volatility: 当前波动率

        Returns:
            异常检测结果
        """
        if not self.volatility_stats:
            return None

        # Z-Score 检测
        z_score = (current_volatility - self.volatility_stats['mean']) / self.volatility_stats['std']

        # 波动率异常通常只关注激增
        if z_score > self.z_score_threshold:
            # 严重程度
            if z_score > 6.0:
                severity = AnomalySeverity.CRITICAL
            elif z_score > 4.0:
                severity = AnomalySeverity.ERROR
            else:
                severity = AnomalySeverity.WARNING

            return AnomalyDetectionResult(
                anomaly_type=AnomalyType.VOLATILITY,
                severity=severity,
                category=AnomalyCategory.MARKET,
                description=f"波动率激增: Z-Score={z_score:.2f}, 正常={self.volatility_stats['mean']:.2f}",
                confidence=min(z_score / self.z_score_threshold, 1.0),
                metrics={
                    'z_score': z_score,
                    'current_volatility': current_volatility,
                    'mean': self.volatility_stats['mean'],
                    'std': self.volatility_stats['std']
                },
                timestamp=datetime.now(),
                detected_by="StatisticalDetector"
            )

        return None


class PatternAnomalyDetector:
    """模式异常检测器 - 基于历史模式匹配"""

    def __init__(self, config: Dict[str, Any]):
        """初始化模式异常检测器

        Args:
            config: 配置字典
        """
        self.pattern_window = config.get('pattern_window', 100)  # 模式窗口大小
        self.similarity_threshold = config.get('similarity_threshold', 0.8)  # 相似度阈值

        # 历史模式库
        self.price_patterns = []
        self.volume_patterns = []
        self.volatility_patterns = []

        # 当前窗口
        self.current_price_window = deque(maxlen=self.pattern_window)
        self.current_volume_window = deque(maxlen=self.pattern_window)
        self.current_volatility_window = deque(maxlen=self.pattern_window)

        logger.info("模式异常检测器初始化完成")

    def update_windows(self, market_data: Dict[str, Any]) -> None:
        """更新当前窗口

        Args:
            market_data: 市场数据
        """
        if 'price' in market_data:
            self.current_price_window.append(market_data['price'])
        if 'volume' in market_data:
            self.current_volume_window.append(market_data['volume'])
        if 'volatility' in market_data:
            self.current_volatility_window.append(market_data['volatility'])

    def add_pattern(self, pattern_data: Dict[str, Any], anomaly_type: AnomalyType) -> None:
        """添加历史模式

        Args:
            pattern_data: 模式数据
            anomaly_type: 异常类型
        """
        pattern = {
            'data': pattern_data,
            'timestamp': datetime.now(),
            'type': anomaly_type
        }

        if anomaly_type == AnomalyType.PRICE:
            self.price_patterns.append(pattern)
        elif anomaly_type == AnomalyType.VOLUME:
            self.volume_patterns.append(pattern)
        elif anomaly_type == AnomalyType.VOLATILITY:
            self.volatility_patterns.append(pattern)

        # 限制模式库大小
        max_patterns = 100
        if len(self.price_patterns) > max_patterns:
            self.price_patterns = self.price_patterns[-max_patterns:]
        if len(self.volume_patterns) > max_patterns:
            self.volume_patterns = self.volume_patterns[-max_patterns:]
        if len(self.volatility_patterns) > max_patterns:
            self.volatility_patterns = self.volatility_patterns[-max_patterns:]

    def _calculate_pattern_similarity(self, pattern1: List[float], pattern2: List[float]) -> float:
        """计算模式相似度（使用归一化互相关）"""
        if len(pattern1) != len(pattern2) or len(pattern1) == 0:
            return 0.0

        # 归一化
        p1_normalized = np.array(pattern1)
        p2_normalized = np.array(pattern2)

        p1_normalized = (p1_normalized - np.mean(p1_normalized)) / (np.std(p1_normalized) + 1e-10)
        p2_normalized = (p2_normalized - np.mean(p2_normalized)) / (np.std(p2_normalized) + 1e-10)

        # 计算相关系数
        correlation = np.corrcoef(p1_normalized, p2_normalized)[0, 1]

        return float(correlation) if not np.isnan(correlation) else 0.0

    def detect_pattern_anomaly(self) -> List[AnomalyDetectionResult]:
        """检测模式异常

        Returns:
            异常检测结果列表
        """
        results = []

        # 检测价格模式异常
        if len(self.current_price_window) == self.pattern_window and self.price_patterns:
            current_pattern = list(self.current_price_window)

            for historical_pattern in self.price_patterns:
                similarity = self._calculate_pattern_similarity(
                    current_pattern,
                    list(historical_pattern['data'])
                )

                # 如果与历史异常模式高度相似
                if similarity > self.similarity_threshold:
                    results.append(AnomalyDetectionResult(
                        anomaly_type=AnomalyType.PRICE,
                        severity=AnomalySeverity.WARNING,
                        category=AnomalyCategory.MARKET,
                        description=f"检测到与历史异常模式高度相似的价格模式 (相似度: {similarity:.2%})",
                        confidence=similarity,
                        metrics={
                            'similarity': similarity,
                            'historical_pattern_time': historical_pattern['timestamp'].isoformat()
                        },
                        timestamp=datetime.now(),
                        detected_by="PatternDetector"
                    ))
                    break

        return results


class IntelligentAnomalyDetector:
    """智能异常检测和诊断系统 V3.7

    集成多种检测算法，提供智能化的异常诊断和恢复建议
    """

    def __init__(
        self,
        memo0_storage,
        config: Dict[str, Any]
    ):
        """初始化智能异常检测器

        Args:
            memo0_storage: Memo0 存储实例
            config: 配置字典
        """
        self.memo0 = memo0_storage
        self.config = config

        # 初始化检测器
        self.statistical_detector = StatisticalAnomalyDetector(config)
        self.pattern_detector = PatternAnomalyDetector(config)

        # 异常历史
        self.anomaly_history: List[AnomalyDetectionResult] = []
        self.diagnosis_history: List[AnomalyDiagnosis] = []

        # 异常统计
        self.anomaly_stats = defaultdict(lambda: {
            'count': 0,
            'last_occurrence': None,
            'avg_confidence': 0.0,
            'most_common_severity': None
        })

        # 预警回调
        self.alert_callbacks: List[Callable[[AnomalyDetectionResult], None]] = (
            config.get('alert_callbacks', [])
        )

        logger.info("智能异常检测和诊断系统 V3.7 初始化完成")

    async def detect_anomalies(
        self,
        market_data: Dict[str, Any],
        system_metrics: Optional[Dict[str, Any]] = None
    ) -> List[AnomalyDetectionResult]:
        """检测异常

        Args:
            market_data: 市场数据
            system_metrics: 系统指标（可选）

        Returns:
            检测到的异常列表
        """
        # 更新统计检测器的数据
        self.statistical_detector.update_stats(market_data)
        self.pattern_detector.update_windows(market_data)

        # 执行多种检测
        detected_anomalies = []

        # 统计检测
        price_anomaly = self.statistical_detector.detect_price_anomaly(
            market_data.get('price', 0)
        )
        if price_anomaly:
            detected_anomalies.append(price_anomaly)
            self.pattern_detector.add_pattern(
                list(self.pattern_detector.current_price_window),
                AnomalyType.PRICE
            )

        volume_anomaly = self.statistical_detector.detect_volume_anomaly(
            market_data.get('volume', 0)
        )
        if volume_anomaly:
            detected_anomalies.append(volume_anomaly)
            self.pattern_detector.add_pattern(
                list(self.pattern_detector.current_volume_window),
                AnomalyType.VOLUME
            )

        volatility_anomaly = self.statistical_detector.detect_volatility_anomaly(
            market_data.get('volatility', 0)
        )
        if volatility_anomaly:
            detected_anomalies.append(volatility_anomaly)

        # 模式检测
        pattern_anomalies = self.pattern_detector.detect_pattern_anomaly()
        detected_anomalies.extend(pattern_anomalies)

        # 系统指标检测
        if system_metrics:
            system_anomalies = await self._detect_system_anomalies(system_metrics)
            detected_anomalies.extend(system_anomalies)

        # 记录异常历史
        for anomaly in detected_anomalies:
            self.anomaly_history.append(anomaly)
            self._update_anomaly_stats(anomaly)

            # 触发预警
            for callback in self.alert_callbacks:
                try:
                    callback(anomaly)
                except Exception as e:
                    logger.error(f"异常预警回调失败: {e}")

        logger.info(f"检测到 {len(detected_anomalies)} 个异常")

        return detected_anomalies

    async def _detect_system_anomalies(
        self,
        system_metrics: Dict[str, Any]
    ) -> List[AnomalyDetectionResult]:
        """检测系统异常"""
        anomalies = []

        # 性能异常检测
        latency = system_metrics.get('latency', 0)
        if latency > 5.0:  # 超过5秒
            anomalies.append(AnomalyDetectionResult(
                anomaly_type=AnomalyType.PERFORMANCE,
                severity=AnomalySeverity.ERROR if latency > 10.0 else AnomalySeverity.WARNING,
                category=AnomalyCategory.SYSTEM,
                description=f"系统性能异常: 延迟 {latency:.2f}s",
                confidence=min(latency / 10.0, 1.0),
                metrics={'latency': latency},
                timestamp=datetime.now(),
                detected_by="SystemDetector"
            ))

        # 网络异常检测
        network_error_rate = system_metrics.get('network_error_rate', 0)
        if network_error_rate > 0.05:  # 超过5%错误率
            anomalies.append(AnomalyDetectionResult(
                anomaly_type=AnomalyType.NETWORK,
                severity=AnomalySeverity.ERROR if network_error_rate > 0.1 else AnomalySeverity.WARNING,
                category=AnomalyCategory.SYSTEM,
                description=f"网络异常: 错误率 {network_error_rate:.1%}",
                confidence=min(network_error_rate / 0.1, 1.0),
                metrics={'network_error_rate': network_error_rate},
                timestamp=datetime.now(),
                detected_by="NetworkDetector"
            ))

        return anomalies

    async def diagnose_anomaly(
        self,
        anomaly: AnomalyDetectionResult
    ) -> AnomalyDiagnosis:
        """诊断异常

        Args:
            anomaly: 异常检测结果

        Returns:
            异常诊断结果
        """
        try:
            # 1. 从 Memo0 获取相关知识
            knowledge = await self._get_relevant_knowledge(anomaly)

            # 2. 分析根本原因
            root_cause = self._analyze_root_cause(anomaly, knowledge)

            # 3. 评估影响
            impact = self._assess_impact(anomaly, knowledge)

            # 4. 生成推荐行动
            actions = self._generate_recommended_actions(anomaly, root_cause, knowledge)

            # 5. 确定恢复策略
            recovery_strategy = self._determine_recovery_strategy(anomaly, knowledge)

            # 6. 预计恢复时间
            predicted_duration = self._predict_recovery_duration(anomaly, knowledge)

            # 创建诊断结果
            diagnosis = AnomalyDiagnosis(
                detection_result=anomaly,
                root_cause=root_cause,
                impact_assessment=impact,
                recommended_actions=actions,
                supporting_knowledge=knowledge,
                recovery_strategy=recovery_strategy,
                predicted_duration=predicted_duration,
                estimated_risk=anomaly.severity.value
            )

            # 记录诊断历史
            self.diagnosis_history.append(diagnosis)

            # 将诊断结果存储到 Memo0
            await self._store_diagnosis_knowledge(diagnosis)

            logger.info(f"异常诊断完成: {anomaly.anomaly_type.value}")

            return diagnosis

        except Exception as e:
            logger.error(f"异常诊断失败: {e}")
            # 返回基本诊断
            return AnomalyDiagnosis(
                detection_result=anomaly,
                root_cause="无法确定根本原因",
                impact_assessment="影响未知",
                recommended_actions=["联系技术支持"],
                supporting_knowledge=[],
                recovery_strategy=None,
                predicted_duration=None,
                estimated_risk=anomaly.severity.value
            )

    async def _get_relevant_knowledge(
        self,
        anomaly: AnomalyDetectionResult
    ) -> List[Dict[str, Any]]:
        """获取相关知识

        Args:
            anomaly: 异常检测结果

        Returns:
            相关知识列表
        """
        try:
            # 构建查询
            query = f"{anomaly.category.value} {anomaly.anomaly_type.value} 异常处理"

            # 调用 Memo0 搜索
            search_results = self.memo0.search_memories(
                query=query,
                top_k=5
            )

            return search_results

        except Exception as e:
            logger.error(f"获取相关知识失败: {e}")
            return []

    def _analyze_root_cause(
        self,
        anomaly: AnomalyDetectionResult,
        knowledge: List[Dict[str, Any]]
    ) -> str:
        """分析根本原因"""
        cause_parts = []

        # 基于异常类型的分析
        if anomaly.category == AnomalyCategory.MARKET:
            if anomaly.anomaly_type == AnomalyType.PRICE:
                if anomaly.metrics.get('z_score', 0) > 5:
                    cause_parts.append("可能由重大市场事件、新闻或流动性冲击引起")
                else:
                    cause_parts.append("可能由短期市场波动或流动性变化引起")
            elif anomaly.anomaly_type == AnomalyType.VOLUME:
                cause_parts.append("可能由重大交易、市场情绪变化或突发事件引起")
            elif anomaly.anomaly_type == AnomalyType.VOLATILITY:
                cause_parts.append("可能由市场不确定性增加、重大新闻或政策变化引起")
            elif anomaly.anomaly_type == AnomalyType.LIQUIDITY:
                cause_parts.append("可能由市场流动性枯竭、大单冲击或交易所问题引起")

        elif anomaly.category == AnomalyCategory.SYSTEM:
            if anomaly.anomaly_type == AnomalyType.PERFORMANCE:
                cause_parts.append("可能由系统负载过高、网络延迟或资源竞争引起")
            elif anomaly.anomaly_type == AnomalyType.NETWORK:
                cause_parts.append("可能由网络连接问题、API限制或服务中断引起")

        # 基于知识的分析
        if knowledge:
            cause_parts.append(f"基于 {len(knowledge)} 条相关历史经验进行分析")

        return ". ".join(cause_parts) if cause_parts else "原因不明"

    def _assess_impact(
        self,
        anomaly: AnomalyDetectionResult,
        knowledge: List[Dict[str, Any]]
    ) -> str:
        """评估影响"""
        impact_parts = []

        # 基于严重程度的评估
        if anomaly.severity == AnomalySeverity.CRITICAL:
            impact_parts.append("严重: 可能导致系统功能完全失效、资金损失或数据错误")
        elif anomaly.severity == AnomalySeverity.ERROR:
            impact_parts.append("严重影响: 可能导致交易失败、延迟增加或准确性下降")
        elif anomaly.severity == AnomalySeverity.WARNING:
            impact_parts.append("中等影响: 可能导致性能下降或需要人工干预")
        else:
            impact_parts.append("轻微影响: 可能需要关注但不影响主要功能")

        # 基于异常类型的评估
        if anomaly.category == AnomalyCategory.MARKET:
            impact_parts.append("影响市场数据准确性和交易决策")
        elif anomaly.category == AnomalyCategory.SYSTEM:
            impact_parts.append("影响系统稳定性和交易执行")

        return ". ".join(impact_parts)

    def _generate_recommended_actions(
        self,
        anomaly: AnomalyDetectionResult,
        root_cause: str,
        knowledge: List[Dict[str, Any]]
    ) -> List[str]:
        """生成推荐行动"""
        actions = []

        # 基于异常类型的行动
        if anomaly.category == AnomalyCategory.MARKET:
            if anomaly.severity in [AnomalySeverity.ERROR, AnomalySeverity.CRITICAL]:
                actions.append("立即暂停所有自动交易")
                actions.append("关闭或降低仓位")
                actions.append("通知相关人员监控市场状况")
            actions.append("审查交易日志，评估潜在影响")
            actions.append("等待市场稳定后再恢复交易")

        elif anomaly.category == AnomalyCategory.SYSTEM:
            if anomaly.anomaly_type == AnomalyType.PERFORMANCE:
                actions.append("检查系统资源使用情况")
                actions.append("优化系统配置或增加资源")
                actions.append("监控系统性能指标")
            elif anomaly.anomaly_type == AnomalyType.NETWORK:
                actions.append("检查网络连接状态")
                actions.append("联系服务提供商确认服务状态")
                actions.append("考虑切换到备用网络")

        # 基于知识的行动
        if knowledge:
            actions.append("参考历史类似事件的处理经验")

        return actions[:5]  # 限制为最多5个行动

    def _determine_recovery_strategy(
        self,
        anomaly: AnomalyDetectionResult,
        knowledge: List[Dict[str, Any]]
    ) -> Optional[str]:
        """确定恢复策略"""
        if anomaly.category == AnomalyCategory.MARKET:
            if anomaly.severity == AnomalySeverity.CRITICAL:
                return "紧急停止 - 立即暂停所有交易，等待市场稳定"
            elif anomaly.severity == AnomalySeverity.ERROR:
                return "降级运行 - 降低交易频率和仓位大小"
            else:
                return "监控运行 - 持续监控，必要时调整参数"

        elif anomaly.category == AnomalyCategory.SYSTEM:
            if anomaly.anomaly_type == AnomalyType.PERFORMANCE:
                return "性能优化 - 优化系统配置，增加资源"
            elif anomaly.anomaly_type == AnomalyType.NETWORK:
                return "网络恢复 - 切换备用网络，联系服务提供商"

        return None

    def _predict_recovery_duration(
        self,
        anomaly: AnomalyDetectionResult,
        knowledge: List[Dict[str, Any]]
    ) -> Optional[float]:
        """预测恢复持续时间（秒）"""
        # 基于异常严重程度的简单预测
        if anomaly.severity == AnomalySeverity.CRITICAL:
            return 3600  # 1小时
        elif anomaly.severity == AnomalySeverity.ERROR:
            return 1800  # 30分钟
        elif anomaly.severity == AnomalySeverity.WARNING:
            return 600  # 10分钟
        else:
            return 300  # 5分钟

    async def _store_diagnosis_knowledge(
        self,
        diagnosis: AnomalyDiagnosis
    ) -> None:
        """将诊断结果存储到 Memo0"""
        try:
            knowledge_content = (
                f"异常诊断: {diagnosis.detection_result.anomaly_type.value} - "
                f"根本原因: {diagnosis.root_cause} - "
                f"恢复策略: {diagnosis.recovery_strategy or '未知'}"
            )

            self.memo0.add_memory_async(
                content=knowledge_content,
                infer=False
            )

        except Exception as e:
            logger.error(f"存储诊断知识失败: {e}")

    def _update_anomaly_stats(self, anomaly: AnomalyDetectionResult) -> None:
        """更新异常统计"""
        anomaly_key = f"{anomaly.category.value}_{anomaly.anomaly_type.value}"
        stats = self.anomaly_stats[anomaly_key]

        stats['count'] += 1
        stats['last_occurrence'] = anomaly.timestamp

        # 更新平均置信度
        n = stats['count']
        old_avg = stats['avg_confidence']
        stats['avg_confidence'] = (old_avg * (n - 1) + anomaly.confidence) / n

        # 更新最常见严重程度
        severity_counts = defaultdict(int)
        for hist_anomaly in self.anomaly_history:
            key = f"{hist_anomaly.category.value}_{hist_anomaly.anomaly_type.value}"
            if key == anomaly_key:
                severity_counts[hist_anomaly.severity] += 1

        if severity_counts:
            stats['most_common_severity'] = max(
                severity_counts.keys(),
                key=lambda x: severity_counts[x]
            ).value

    async def predict_anomalies(
        self,
        market_data: Dict[str, Any]
    ) -> List[AnomalyPrediction]:
        """预测异常

        Args:
            market_data: 市场数据

        Returns:
            异常预测列表
        """
        predictions = []

        try:
            # 基于历史模式的预测
            if self.anomaly_history:
                # 分析最近的异常趋势
                recent_anomalies = [
                    a for a in self.anomaly_history
                    if (datetime.now() - a.timestamp).total_seconds() < 86400  # 最近24小时
                ]

                if recent_anomalies:
                    # 统计异常类型
                    anomaly_counts = defaultdict(int)
                    for anomaly in recent_anomalies:
                        anomaly_counts[anomaly.anomaly_type] += 1

                    # 预测高频异常
                    for anomaly_type, count in anomaly_counts.items():
                        if count >= 3:  # 同类型异常出现3次以上
                            probability = min(count / len(recent_anomalies) * 2, 0.9)

                            predictions.append(AnomalyPrediction(
                                predicted_type=anomaly_type,
                                predicted_severity=AnomalySeverity.WARNING,
                                probability=probability,
                                time_window=(
                                    datetime.now(),
                                    datetime.now() + timedelta(hours=2)
                                ),
                                warning_message=f"基于历史模式，预测未来2小时内可能出现{anomaly_type.value}异常",
                                preventive_actions=self._generate_preventive_actions(anomaly_type)
                            ))

        except Exception as e:
            logger.error(f"异常预测失败: {e}")

        return predictions

    def _generate_preventive_actions(
        self,
        anomaly_type: AnomalyType
    ) -> List[str]:
        """生成预防行动"""
        if anomaly_type == AnomalyType.PRICE:
            return [
                "监控价格变动",
                "准备降低仓位",
                "设置更严格的止损"
            ]
        elif anomaly_type == AnomalyType.VOLATILITY:
            return [
                "降低杠杆",
                "增加流动性缓冲",
                "暂停高风险策略"
            ]
        elif anomaly_type == AnomalyType.LIQUIDITY:
            return [
                "分散交易所",
                "减少大额交易",
                "准备手动干预"
            ]
        else:
            return [
                "监控系统指标",
                "准备应急响应",
                "检查系统配置"
            ]

    def get_anomaly_summary(self) -> Dict[str, Any]:
        """获取异常摘要

        Returns:
            异常摘要字典
        """
        # 计算统计数据
        total_anomalies = len(self.anomaly_history)
        last_24h_anomalies = [
            a for a in self.anomaly_history
            if (datetime.now() - a.timestamp).total_seconds() < 86400
        ]

        # 按类别统计
        category_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        for anomaly in self.anomaly_history:
            category_counts[anomaly.category.value] += 1
            severity_counts[anomaly.severity.value] += 1

        return {
            'total_anomalies': total_anomalies,
            'last_24h_anomalies': len(last_24h_anomalies),
            'category_breakdown': dict(category_counts),
            'severity_breakdown': dict(severity_counts),
            'most_common_anomaly': max(
                category_counts.items(),
                key=lambda x: x[1]
            ) if category_counts else (None, 0),
            'recent_trend': 'increasing' if len(last_24h_anomalies) > total_anomalies / 7 else 'stable',
            'average_confidence': sum(a.confidence for a in self.anomaly_history) / total_anomalies if total_anomalies > 0 else 0,
            'anomaly_stats': {k: {
                'count': v['count'],
                'last_occurrence': v['last_occurrence'].isoformat() if v['last_occurrence'] else None,
                'avg_confidence': v['avg_confidence'],
                'most_common_severity': v['most_common_severity']
            } for k, v in self.anomaly_stats.items()}
        }


# 全局智能异常检测器实例
_intelligent_detector: Optional[IntelligentAnomalyDetector] = None


def initialize_intelligent_anomaly_detector(
    memo0_storage,
    config: Dict[str, Any]
) -> IntelligentAnomalyDetector:
    """初始化全局智能异常检测器

    Args:
        memo0_storage: Memo0 存储实例
        config: 配置字典

    Returns:
        智能异常检测器实例
    """
    global _intelligent_detector
    _intelligent_detector = IntelligentAnomalyDetector(memo0_storage, config)
    return _intelligent_detector


def get_intelligent_anomaly_detector() -> Optional[IntelligentAnomalyDetector]:
    """获取全局智能异常检测器

    Returns:
        智能异常检测器实例，如果未初始化则返回 None
    """
    return _intelligent_detector
