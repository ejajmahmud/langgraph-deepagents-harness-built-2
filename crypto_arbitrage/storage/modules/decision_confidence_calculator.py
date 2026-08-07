"""决策置信度计算器 - V5.10 Phase 2.3

实现多维度置信度评估、因子分析、动态校准和详细报告。

核心功能：
1. 多维度置信度评估
2. 置信度因子分析
3. 置信度校准
4. 置信度报告

基于：V5.10架构设计
创建时间：2026-04-19
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict
import statistics
import json

logger = logging.getLogger(__name__)


class ConfidenceLevel(Enum):
    """置信度等级"""
    VERY_HIGH = "very_high"  # 非常高 (0.9-1.0)
    HIGH = "high"  # 高 (0.8-0.9)
    MEDIUM = "medium"  # 中 (0.6-0.8)
    LOW = "low"  # 低 (0.4-0.6)
    VERY_LOW = "very_low"  # 非常低 (0.0-0.4)


class ConfidenceFactor(Enum):
    """置信度因子"""
    KNOWLEDGE_QUALITY = "knowledge_quality"  # 知识质量
    DATA_FRESHNESS = "data_freshness"  # 数据新鲜度
    MARKET_VOLATILITY = "market_volatility"  # 市场波动率
    MODEL_PERFORMANCE = "model_performance"  # 模型性能
    CONTEXT_CLARITY = "context_clarity"  # 上下文清晰度
    HISTORICAL_ACCURACY = "historical_accuracy"  # 历史准确性


@dataclass
class ConfidenceScore:
    """置信度分数"""
    overall_score: float  # 总体分数 (0-1)
    level: ConfidenceLevel
    factor_scores: Dict[str, float]
    factor_weights: Dict[str, float]
    calculated_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "overall_score": self.overall_score,
            "level": self.level.value,
            "factor_scores": self.factor_scores,
            "factor_weights": self.factor_weights,
            "calculated_at": self.calculated_at.isoformat()
        }


@dataclass
class FactorAnalysis:
    """因子分析"""
    factor: ConfidenceFactor
    score: float
    weight: float
    contribution: float  # 对总体分数的贡献
    trend: str  # "increasing", "decreasing", "stable"
    recent_history: List[float]
    recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "factor": self.factor.value,
            "score": self.score,
            "weight": self.weight,
            "contribution": self.contribution,
            "trend": self.trend,
            "recent_history": self.recent_history,
            "recommendation": self.recommendation
        }


@dataclass
class ConfidenceCalibration:
    """置信度校准"""
    original_score: float
    calibrated_score: float
    adjustment_reason: str
    calibration_factors: Dict[str, float]
    risk_adjustment: float
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "original_score": self.original_score,
            "calibrated_score": self.calibrated_score,
            "adjustment_reason": self.adjustment_reason,
            "calibration_factors": self.calibration_factors,
            "risk_adjustment": self.risk_adjustment,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class ConfidenceReport:
    """置信度报告"""
    decision_id: str
    confidence_score: ConfidenceScore
    factor_analyses: List[FactorAnalysis]
    calibration: Optional[ConfidenceCalibration]
    low_confidence_factors: List[str]
    improvement_suggestions: List[str]
    generated_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "decision_id": self.decision_id,
            "confidence_score": self.confidence_score.to_dict(),
            "factor_analyses": [fa.to_dict() for fa in self.factor_analyses],
            "calibration": self.calibration.to_dict() if self.calibration else None,
            "low_confidence_factors": self.low_confidence_factors,
            "improvement_suggestions": self.improvement_suggestions,
            "generated_at": self.generated_at.isoformat()
        }


class DecisionConfidenceCalculator:
    """决策置信度计算器

    实现6维度置信度评估、动态校准和详细报告生成。
    """

    # 默认权重
    DEFAULT_FACTOR_WEIGHTS = {
        ConfidenceFactor.KNOWLEDGE_QUALITY: 0.25,
        ConfidenceFactor.DATA_FRESHNESS: 0.20,
        ConfidenceFactor.MARKET_VOLATILITY: 0.15,
        ConfidenceFactor.MODEL_PERFORMANCE: 0.15,
        ConfidenceFactor.CONTEXT_CLARITY: 0.15,
        ConfidenceFactor.HISTORICAL_ACCURACY: 0.10
    }

    # 阈值
    VERY_HIGH_THRESHOLD = 0.9
    HIGH_THRESHOLD = 0.8
    MEDIUM_THRESHOLD = 0.6
    LOW_THRESHOLD = 0.4

    # 历史记录大小
    HISTORY_SIZE = 100

    def __init__(self, config: Dict[str, Any]):
        """初始化置信度计算器

        Args:
            config: 配置字典
        """
        self.config = config

        # 因子权重
        self.factor_weights = config.get('factor_weights', self.DEFAULT_FACTOR_WEIGHTS)

        # 风险容忍度
        self.risk_tolerance = config.get('risk_tolerance', 0.5)

        # 历史记录
        self.confidence_history: List[Dict[str, Any]] = []
        self.factor_history: Dict[str, List[float]] = defaultdict(list)

        # 统计信息
        self.stats = {
            "total_calculations": 0,
            "average_confidence": 0.0,
            "high_confidence_count": 0,
            "low_confidence_count": 0,
            "calibrations_performed": 0
        }

        logger.info("[OK] 决策置信度计算器初始化完成")

    # ========== 多维度置信度评估 ==========

    async def calculate_overall_confidence(
        self,
        decision_context: Dict[str, Any],
        knowledge_matches: List[Dict[str, Any]]
    ) -> ConfidenceScore:
        """计算总体置信度

        Args:
            decision_context: 决策上下文
            knowledge_matches: 知识匹配列表

        Returns:
            置信度分数
        """
        # 评估各个因子
        factor_scores = {}

        factor_scores[ConfidenceFactor.KNOWLEDGE_QUALITY.value] = await self.assess_knowledge_confidence(knowledge_matches)
        factor_scores[ConfidenceFactor.DATA_FRESHNESS.value] = await self.assess_data_freshness(decision_context)
        factor_scores[ConfidenceFactor.MARKET_VOLATILITY.value] = await self.assess_market_volatility(decision_context)
        factor_scores[ConfidenceFactor.MODEL_PERFORMANCE.value] = await self.assess_model_performance(decision_context)
        factor_scores[ConfidenceFactor.CONTEXT_CLARITY.value] = await self.assess_context_clarity(decision_context)
        factor_scores[ConfidenceFactor.HISTORICAL_ACCURACY.value] = await self.assess_historical_confidence(decision_context)

        # 计算加权总分
        overall_score = 0.0
        for factor, score in factor_scores.items():
            weight = self.factor_weights.get(ConfidenceFactor(factor), 0.1)
            overall_score += score * weight

        # 确定置信度等级
        level = self._determine_confidence_level(overall_score)

        # 记录历史
        self._record_confidence_history(overall_score, factor_scores)

        # 更新统计
        self._update_statistics(overall_score)

        confidence_score = ConfidenceScore(
            overall_score=overall_score,
            level=level,
            factor_scores=factor_scores,
            factor_weights={f.value: w for f, w in self.factor_weights.items()},
            calculated_at=datetime.now()
        )

        logger.info(f"计算总体置信度: {overall_score:.3f}, 等级: {level.value}")

        return confidence_score

    async def assess_knowledge_confidence(
        self,
        knowledge_matches: List[Dict[str, Any]]
    ) -> float:
        """评估知识置信度

        Args:
            knowledge_matches: 知识匹配列表

        Returns:
            知识置信度分数 (0-1)
        """
        if not knowledge_matches:
            return 0.2

        # 平均质量分数
        quality_scores = [
            k.get('quality_score', 0.5)
            for k in knowledge_matches
        ]
        avg_quality = statistics.mean(quality_scores)

        # 知识覆盖率
        coverage = min(len(knowledge_matches) / 5.0, 1.0)

        # 知识相关性
        relevance_scores = [
            k.get('relevance_score', 0.5)
            for k in knowledge_matches
        ]
        avg_relevance = statistics.mean(relevance_scores) if relevance_scores else 0.5

        # 综合分数
        knowledge_confidence = (
            avg_quality * 0.5 +
            coverage * 0.3 +
            avg_relevance * 0.2
        )

        return min(knowledge_confidence, 1.0)

    async def assess_data_freshness(
        self,
        decision_context: Dict[str, Any]
    ) -> float:
        """评估数据新鲜度

        Args:
            decision_context: 决策上下文

        Returns:
            数据新鲜度分数 (0-1)
        """
        # 检查数据时间戳
        market_data = decision_context.get('market_data', {})
        timestamp_str = market_data.get('timestamp')

        if not timestamp_str:
            return 0.5

        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            age_minutes = (datetime.now() - timestamp).total_seconds() / 60

            # 越新鲜分数越高
            if age_minutes < 1:
                return 1.0
            elif age_minutes < 5:
                return 0.9
            elif age_minutes < 15:
                return 0.7
            elif age_minutes < 30:
                return 0.5
            elif age_minutes < 60:
                return 0.3
            else:
                return 0.1

        except:
            return 0.5

    async def assess_market_volatility(
        self,
        decision_context: Dict[str, Any]
    ) -> float:
        """评估市场波动率

        Args:
            decision_context: 决策上下文

        Returns:
            市场波动率分数 (0-1)
        """
        market_data = decision_context.get('market_data', {})
        volatility = market_data.get('volatility', 0.02)

        # 波动率适中时置信度最高
        if volatility < 0.01:
            # 波动率过低，可能是流动性问题
            return 0.6
        elif 0.01 <= volatility <= 0.03:
            # 适中波动率
            return 1.0
        elif 0.03 < volatility <= 0.05:
            # 较高波动率
            return 0.7
        else:
            # 极端波动率
            return 0.4

    async def assess_model_performance(
        self,
        decision_context: Dict[str, Any]
    ) -> float:
        """评估模型性能

        Args:
            decision_context: 决策上下文

        Returns:
            模型性能分数 (0-1)
        """
        # 从历史记录计算模型性能
        if len(self.confidence_history) < 10:
            return 0.7  # 默认值

        # 计算最近的置信度趋势
        recent_confidences = [
            h['overall_score']
            for h in self.confidence_history[-20:]
        ]

        if not recent_confidences:
            return 0.7

        # 平均置信度
        avg_confidence = statistics.mean(recent_confidences)

        # 置信度稳定性
        if len(recent_confidences) > 1:
            std_confidence = statistics.stdev(recent_confidences)
            stability = max(0, 1.0 - std_confidence * 2)  # 标准差越小越稳定
        else:
            stability = 1.0

        # 综合性能分数
        model_performance = avg_confidence * 0.7 + stability * 0.3

        return min(model_performance, 1.0)

    async def assess_context_clarity(
        self,
        decision_context: Dict[str, Any]
    ) -> float:
        """评估上下文清晰度

        Args:
            decision_context: 决策上下文

        Returns:
            上下文清晰度分数 (0-1)
        """
        clarity_score = 1.0

        # 检查必要字段
        required_fields = ['market_data', 'trading_parameters', 'risk_profile']
        for field in required_fields:
            if not decision_context.get(field):
                clarity_score -= 0.2

        # 检查市场数据完整性
        market_data = decision_context.get('market_data', {})
        essential_market_fields = ['symbol', 'price', 'volume']
        for field in essential_market_fields:
            if field not in market_data:
                clarity_score -= 0.1

        return max(clarity_score, 0.0)

    async def assess_historical_confidence(
        self,
        decision_context: Dict[str, Any]
    ) -> float:
        """评估历史置信度

        Args:
            decision_context: 决策上下文

        Returns:
            历史置信度分数 (0-1)
        """
        # 基于历史决策的准确性
        if len(self.confidence_history) < 5:
            return 0.6  # 数据不足时的默认值

        # 计算历史置信度的分布
        confidences = [h['overall_score'] for h in self.confidence_history]

        # 高置信度决策的比例
        high_conf_ratio = sum(1 for c in confidences if c >= self.HIGH_THRESHOLD) / len(confidences)

        # 置信度趋势
        if len(confidences) >= 10:
            recent_avg = statistics.mean(confidences[-10:])
            earlier_avg = statistics.mean(confidences[:-10])
            trend_improvement = (recent_avg - earlier_avg) / earlier_avg if earlier_avg > 0 else 0
            historical_confidence = high_conf_ratio * 0.7 + max(0, min(1, trend_improvement + 0.5)) * 0.3
        else:
            historical_confidence = high_conf_ratio

        return min(historical_confidence, 1.0)

    # ========== 置信度因子分析 ==========

    async def analyze_knowledge_quality_factor(
        self,
        knowledge_matches: List[Dict[str, Any]]
    ) -> FactorAnalysis:
        """分析知识质量因子"""
        score = await self.assess_knowledge_confidence(knowledge_matches)
        weight = self.factor_weights[ConfidenceFactor.KNOWLEDGE_QUALITY]

        # 历史趋势
        history = self.factor_history[ConfidenceFactor.KNOWLEDGE_QUALITY.value][-10:]
        trend = self._analyze_trend(history)

        # 贡献度
        contribution = score * weight

        # 建议
        if score < 0.5:
            recommendation = "提高知识质量，增加高质量知识源"
        elif score < 0.7:
            recommendation = "优化知识筛选，提高相关性"
        else:
            recommendation = "知识质量良好，保持当前水平"

        return FactorAnalysis(
            factor=ConfidenceFactor.KNOWLEDGE_QUALITY,
            score=score,
            weight=weight,
            contribution=contribution,
            trend=trend,
            recent_history=history,
            recommendation=recommendation
        )

    async def analyze_data_freshness_factor(
        self,
        decision_context: Dict[str, Any]
    ) -> FactorAnalysis:
        """分析数据新鲜度因子"""
        score = await self.assess_data_freshness(decision_context)
        weight = self.factor_weights[ConfidenceFactor.DATA_FRESHNESS]

        # 历史趋势
        history = self.factor_history[ConfidenceFactor.DATA_FRESHNESS.value][-10:]
        trend = self._analyze_trend(history)

        # 贡献度
        contribution = score * weight

        # 建议
        if score < 0.5:
            recommendation = "优化数据更新频率，减少数据延迟"
        elif score < 0.7:
            recommendation = "数据更新频率可接受，考虑进一步优化"
        else:
            recommendation = "数据新鲜度良好，保持当前更新频率"

        return FactorAnalysis(
            factor=ConfidenceFactor.DATA_FRESHNESS,
            score=score,
            weight=weight,
            contribution=contribution,
            trend=trend,
            recent_history=history,
            recommendation=recommendation
        )

    async def analyze_market_volatility_factor(
        self,
        decision_context: Dict[str, Any]
    ) -> FactorAnalysis:
        """分析市场波动率因子"""
        score = await self.assess_market_volatility(decision_context)
        weight = self.factor_weights[ConfidenceFactor.MARKET_VOLATILITY]

        # 历史趋势
        history = self.factor_history[ConfidenceFactor.MARKET_VOLATILITY.value][-10:]
        trend = self._analyze_trend(history)

        # 贡献度
        contribution = score * weight

        # 建议
        market_data = decision_context.get('market_data', {})
        volatility = market_data.get('volatility', 0.02)

        if score < 0.5:
            recommendation = f"市场波动率{volatility:.2%}过高，降低交易规模或暂停交易"
        elif score < 0.7:
            recommendation = f"市场波动率{volatility:.2%}较高，谨慎交易"
        else:
            recommendation = f"市场波动率{volatility:.2%}适中，正常交易"

        return FactorAnalysis(
            factor=ConfidenceFactor.MARKET_VOLATILITY,
            score=score,
            weight=weight,
            contribution=contribution,
            trend=trend,
            recent_history=history,
            recommendation=recommendation
        )

    async def analyze_model_performance_factor(
        self,
        decision_context: Dict[str, Any]
    ) -> FactorAnalysis:
        """分析模型性能因子"""
        score = await self.assess_model_performance(decision_context)
        weight = self.factor_weights[ConfidenceFactor.MODEL_PERFORMANCE]

        # 历史趋势
        history = self.factor_history[ConfidenceFactor.MODEL_PERFORMANCE.value][-10:]
        trend = self._analyze_trend(history)

        # 贡献度
        contribution = score * weight

        # 建议
        if score < 0.6:
            recommendation = "模型性能不足，考虑重新训练或调整参数"
        elif score < 0.8:
            recommendation = "模型性能良好，持续监控并微调"
        else:
            recommendation = "模型性能优秀，保持当前配置"

        return FactorAnalysis(
            factor=ConfidenceFactor.MODEL_PERFORMANCE,
            score=score,
            weight=weight,
            contribution=contribution,
            trend=trend,
            recent_history=history,
            recommendation=recommendation
        )

    # ========== 置信度校准 ==========

    async def calibrate_confidence_scores(
        self,
        confidence_score: ConfidenceScore,
        decision_context: Dict[str, Any]
    ) -> ConfidenceCalibration:
        """校准置信度分数

        Args:
            confidence_score: 原始置信度分数
            decision_context: 决策上下文

        Returns:
            校准结果
        """
        original_score = confidence_score.overall_score
        calibration_factors = {}

        # 风险调整
        risk_profile = decision_context.get('risk_profile', {})
        risk_level = risk_profile.get('level', 'medium')

        if risk_level == 'high':
            risk_adjustment = -0.1  # 高风险降低置信度
        elif risk_level == 'low':
            risk_adjustment = 0.05  # 低风险提高置信度
        else:
            risk_adjustment = 0.0

        calibration_factors['risk_adjustment'] = risk_adjustment

        # 上下文完整性调整
        context_clarity = confidence_score.factor_scores.get(ConfidenceFactor.CONTEXT_CLARITY.value, 1.0)
        if context_clarity < 0.7:
            context_adjustment = -0.1
        else:
            context_adjustment = 0.0

        calibration_factors['context_adjustment'] = context_adjustment

        # 市场条件调整
        market_volatility = confidence_score.factor_scores.get(ConfidenceFactor.MARKET_VOLATILITY.value, 1.0)
        if market_volatility < 0.5:
            market_adjustment = -0.15
        else:
            market_adjustment = 0.0

        calibration_factors['market_adjustment'] = market_adjustment

        # 计算校准后分数
        total_adjustment = risk_adjustment + context_adjustment + market_adjustment
        calibrated_score = max(0.0, min(1.0, original_score + total_adjustment))

        # 生成调整原因
        adjustment_reasons = []
        if risk_adjustment != 0:
            adjustment_reasons.append(f"风险等级调整: {risk_adjustment:+.2f}")
        if context_adjustment != 0:
            adjustment_reasons.append(f"上下文调整: {context_adjustment:+.2f}")
        if market_adjustment != 0:
            adjustment_reasons.append(f"市场条件调整: {market_adjustment:+.2f}")

        adjustment_reason = "; ".join(adjustment_reasons) if adjustment_reasons else "无需调整"

        # 更新统计
        self.stats['calibrations_performed'] += 1

        calibration = ConfidenceCalibration(
            original_score=original_score,
            calibrated_score=calibrated_score,
            adjustment_reason=adjustment_reason,
            calibration_factors=calibration_factors,
            risk_adjustment=total_adjustment,
            timestamp=datetime.now()
        )

        logger.info(f"校准置信度: {original_score:.3f} -> {calibrated_score:.3f} ({adjustment_reason})")

        return calibration

    async def adjust_for_risk_tolerance(
        self,
        confidence_score: float
    ) -> float:
        """根据风险容忍度调整

        Args:
            confidence_score: 原始置信度分数

        Returns:
            调整后的置信度分数
        """
        if self.risk_tolerance < 0.3:
            # 低风险容忍，提高置信度要求
            adjusted_score = confidence_score * 0.9
        elif self.risk_tolerance > 0.7:
            # 高风险容忍，降低置信度要求
            adjusted_score = min(1.0, confidence_score * 1.1)
        else:
            # 中等风险容忍，不做调整
            adjusted_score = confidence_score

        return adjusted_score

    async def normalize_confidence_ranges(
        self,
        confidence_scores: List[float]
    ) -> List[float]:
        """归一化置信度范围

        Args:
            confidence_scores: 置信度分数列表

        Returns:
            归一化后的分数列表
        """
        if not confidence_scores:
            return []

        min_score = min(confidence_scores)
        max_score = max(confidence_scores)

        if max_score - min_score < 0.01:
            # 所有分数接近，不做归一化
            return confidence_scores

        # Min-Max归一化
        normalized = [
            (score - min_score) / (max_score - min_score)
            for score in confidence_scores
        ]

        return normalized

    # ========== 置信度报告 ==========

    async def generate_confidence_report(
        self,
        decision_id: str,
        decision_context: Dict[str, Any],
        knowledge_matches: List[Dict[str, Any]]
    ) -> ConfidenceReport:
        """生成置信度报告

        Args:
            decision_id: 决策ID
            decision_context: 决策上下文
            knowledge_matches: 知识匹配列表

        Returns:
            置信度报告
        """
        # 计算总体置信度
        confidence_score = await self.calculate_overall_confidence(
            decision_context, knowledge_matches
        )

        # 分析各个因子
        factor_analyses = []

        factor_analyses.append(
            await self.analyze_knowledge_quality_factor(knowledge_matches)
        )
        factor_analyses.append(
            await self.analyze_data_freshness_factor(decision_context)
        )
        factor_analyses.append(
            await self.analyze_market_volatility_factor(decision_context)
        )
        factor_analyses.append(
            await self.analyze_model_performance_factor(decision_context)
        )

        # 校准置信度
        calibration = await self.calibrate_confidence_scores(
            confidence_score, decision_context
        )

        # 识别低置信度因子
        low_confidence_factors = [
            fa.factor.value
            for fa in factor_analyses
            if fa.score < self.MEDIUM_THRESHOLD
        ]

        # 生成改进建议
        improvement_suggestions = []
        for fa in factor_analyses:
            if fa.score < self.MEDIUM_THRESHOLD:
                improvement_suggestions.append(fa.recommendation)

        # 如果校准后分数较低，添加建议
        if calibration.calibrated_score < self.MEDIUM_THRESHOLD:
            improvement_suggestions.append(
                f"考虑在市场条件改善后再执行决策（当前校准后置信度: {calibration.calibrated_score:.2f}）"
            )

        report = ConfidenceReport(
            decision_id=decision_id,
            confidence_score=confidence_score,
            factor_analyses=factor_analyses,
            calibration=calibration,
            low_confidence_factors=low_confidence_factors,
            improvement_suggestions=improvement_suggestions,
            generated_at=datetime.now()
        )

        logger.info(f"生成置信度报告: {decision_id}, 校准后分数: {calibration.calibrated_score:.3f}")

        return report

    async def identify_low_confidence_decisions(
        self,
        threshold: float = 0.6
    ) -> List[Dict[str, Any]]:
        """识别低置信度决策

        Args:
            threshold: 置信度阈值

        Returns:
            低置信度决策列表
        """
        low_confidence_decisions = []

        for record in self.confidence_history:
            if record['overall_score'] < threshold:
                low_confidence_decisions.append(record)

        return low_confidence_decisions

    async def suggest_confidence_improvements(
        self,
        confidence_report: ConfidenceReport
    ) -> List[str]:
        """建议置信度改进

        Args:
            confidence_report: 置信度报告

        Returns:
            改进建议列表
        """
        suggestions = []

        # 基于因子分析
        for fa in confidence_report.factor_analyses:
            if fa.score < self.MEDIUM_THRESHOLD:
                suggestions.append(fa.recommendation)

        # 基于校准结果
        if confidence_report.calibration:
            calibration = confidence_report.calibration
            if calibration.calibrated_score < self.MEDIUM_THRESHOLD:
                suggestions.append("当前市场条件不适合交易，建议等待")

        # 基于历史模式
        if len(self.confidence_history) > 10:
            recent_avg = statistics.mean(
                [h['overall_score'] for h in self.confidence_history[-10:]]
            )
            if recent_avg < self.MEDIUM_THRESHOLD:
                suggestions.append("近期整体置信度偏低，建议审查决策流程")

        return suggestions

    # ========== 辅助方法 ==========

    def _determine_confidence_level(self, score: float) -> ConfidenceLevel:
        """确定置信度等级"""
        if score >= self.VERY_HIGH_THRESHOLD:
            return ConfidenceLevel.VERY_HIGH
        elif score >= self.HIGH_THRESHOLD:
            return ConfidenceLevel.HIGH
        elif score >= self.MEDIUM_THRESHOLD:
            return ConfidenceLevel.MEDIUM
        elif score >= self.LOW_THRESHOLD:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW

    def _record_confidence_history(
        self,
        overall_score: float,
        factor_scores: Dict[str, float]
    ) -> None:
        """记录置信度历史"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "overall_score": overall_score,
            "factor_scores": factor_scores.copy()
        }

        self.confidence_history.append(record)

        # 限制历史记录大小
        if len(self.confidence_history) > self.HISTORY_SIZE:
            self.confidence_history = self.confidence_history[-self.HISTORY_SIZE:]

        # 更新因子历史
        for factor, score in factor_scores.items():
            self.factor_history[factor].append(score)
            if len(self.factor_history[factor]) > self.HISTORY_SIZE:
                self.factor_history[factor] = self.factor_history[factor][-self.HISTORY_SIZE:]

    def _update_statistics(self, confidence_score: float) -> None:
        """更新统计信息"""
        self.stats['total_calculations'] += 1

        # 更新平均置信度
        total = self.stats['average_confidence'] * (self.stats['total_calculations'] - 1)
        self.stats['average_confidence'] = (total + confidence_score) / self.stats['total_calculations']

        # 更新计数
        if confidence_score >= self.HIGH_THRESHOLD:
            self.stats['high_confidence_count'] += 1
        elif confidence_score < self.MEDIUM_THRESHOLD:
            self.stats['low_confidence_count'] += 1

    def _analyze_trend(self, history: List[float]) -> str:
        """分析趋势"""
        if len(history) < 3:
            return "stable"

        recent_avg = statistics.mean(history[-3:])
        earlier_avg = statistics.mean(history[:-3]) if len(history) > 3 else recent_avg

        if recent_avg > earlier_avg * 1.05:
            return "increasing"
        elif recent_avg < earlier_avg * 0.95:
            return "decreasing"
        else:
            return "stable"

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()

    def reset_statistics(self) -> None:
        """重置统计信息"""
        self.stats = {
            "total_calculations": 0,
            "average_confidence": 0.0,
            "high_confidence_count": 0,
            "low_confidence_count": 0,
            "calibrations_performed": 0
        }
        logger.info("统计信息已重置")

    def export_history(self, filepath: str) -> None:
        """导出历史记录"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.confidence_history, f, indent=2, ensure_ascii=False)

        logger.info(f"置信度历史已导出到: {filepath}")


def create_decision_confidence_calculator(
    config: Dict[str, Any]
) -> DecisionConfidenceCalculator:
    """创建决策置信度计算器实例

    Args:
        config: 配置字典

    Returns:
        决策置信度计算器实例
    """
    return DecisionConfidenceCalculator(config)
