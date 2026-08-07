"""知识趋势分析器 - V5.10 Phase 1.4

分析知识使用趋势，识别热点知识，评估知识价值，
预测未来需求，支持知识库的智能管理。

核心功能：
1. 知识使用趋势分析
2. 热点知识识别
3. 知识价值评估
4. 未来需求预测

基于：V5.10架构设计
创建时间：2026-04-19
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import statistics

logger = logging.getLogger(__name__)


class TrendDirection(Enum):
    """趋势方向枚举"""
    RISING = "rising"  # 上升
    STABLE = "stable"  # 稳定
    DECLINING = "declining"  # 下降
    VOLATILE = "volatile"  # 波动


class KnowledgeValueTier(Enum):
    """知识价值等级"""
    CRITICAL = "critical"  # 关键 (价值 > 0.8)
    HIGH = "high"  # 高价值 (0.6-0.8)
    MEDIUM = "medium"  # 中等价值 (0.4-0.6)
    LOW = "low"  # 低价值 (0.2-0.4)
    NEGLECTED = "neglected"  # 忽视 (价值 < 0.2)


@dataclass
class KnowledgeUsageRecord:
    """知识使用记录"""
    knowledge_id: str
    content: str
    access_count: int
    last_accessed: datetime
    first_accessed: datetime
    access_frequency: float  # 每天访问次数
    recent_accesses: List[datetime] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "knowledge_id": self.knowledge_id,
            "content": self.content,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat(),
            "first_accessed": self.first_accessed.isoformat(),
            "access_frequency": self.access_frequency,
            "recent_accesses": [dt.isoformat() for dt in self.recent_accesses[-10:]]
        }


@dataclass
class TrendAnalysis:
    """趋势分析结果"""
    knowledge_id: str
    trend_direction: TrendDirection
    trend_strength: float  # 0-1，趋势强度
    change_rate: float  # 变化率
    predicted_demand: float  # 预测需求
    confidence: float  # 预测置信度
    analyzed_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "knowledge_id": self.knowledge_id,
            "trend_direction": self.trend_direction.value,
            "trend_strength": self.trend_strength,
            "change_rate": self.change_rate,
            "predicted_demand": self.predicted_demand,
            "confidence": self.confidence,
            "analyzed_at": self.analyzed_at.isoformat()
        }


@dataclass
class HotKnowledge:
    """热点知识"""
    knowledge_id: str
    content: str
    hot_score: float  # 热度分数
    access_count: int
    recent_activity: float  # 近期活动度
    value_score: float  # 价值分数
    detected_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "knowledge_id": self.knowledge_id,
            "content": self.content,
            "hot_score": self.hot_score,
            "access_count": self.access_count,
            "recent_activity": self.recent_activity,
            "value_score": self.value_score,
            "detected_at": self.detected_at.isoformat()
        }


@dataclass
class KnowledgeValueAssessment:
    """知识价值评估"""
    knowledge_id: str
    value_score: float  # 0-1
    value_tier: KnowledgeValueTier
    value_factors: Dict[str, float]
    assessment_time: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "knowledge_id": self.knowledge_id,
            "value_score": self.value_score,
            "value_tier": self.value_tier.value,
            "value_factors": self.value_factors,
            "assessment_time": self.assessment_time.isoformat()
        }


@dataclass
class TrendReport:
    """趋势报告"""
    analysis_period: Tuple[datetime, datetime]
    total_knowledge_analyzed: int
    trend_distribution: Dict[TrendDirection, int]
    top_rising_knowledge: List[Dict[str, Any]]
    top_declining_knowledge: List[Dict[str, Any]]
    hot_knowledge: List[Dict[str, Any]]
    value_distribution: Dict[KnowledgeValueTier, int]
    recommendations: List[str]
    generated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "analysis_period": {
                "start": self.analysis_period[0].isoformat(),
                "end": self.analysis_period[1].isoformat()
            },
            "total_knowledge_analyzed": self.total_knowledge_analyzed,
            "trend_distribution": {
                direction.value: count for direction, count in self.trend_distribution.items()
            },
            "top_rising_knowledge": self.top_rising_knowledge,
            "top_declining_knowledge": self.top_declining_knowledge,
            "hot_knowledge": self.hot_knowledge,
            "value_distribution": {
                tier.value: count for tier, count in self.value_distribution.items()
            },
            "recommendations": self.recommendations,
            "generated_at": self.generated_at.isoformat()
        }


class KnowledgeTrendAnalyzer:
    """知识趋势分析器

    分析知识使用趋势，识别热点和评估价值。
    """

    # 趋势分析窗口
    DEFAULT_WINDOW_DAYS = 7
    MAX_RECENT_ACCESSES = 50

    # 价值评估权重
    VALUE_WEIGHTS = {
        "usage_frequency": 0.3,
        "recency": 0.25,
        "consistency": 0.2,
        "impact": 0.15,
        "uniqueness": 0.1
    }

    def __init__(self, config: Dict[str, Any]):
        """初始化知识趋势分析器

        Args:
            config: 配置字典
        """
        self.config = config

        # 分析配置
        self.window_days = config.get('window_days', self.DEFAULT_WINDOW_DAYS)
        self.min_access_count = config.get('min_access_count', 3)
        self.hot_threshold = config.get('hot_threshold', 0.7)

        # 存储使用记录
        self.usage_records: Dict[str, KnowledgeUsageRecord] = {}

        # 访问历史（用于趋势分析）
        self.access_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=self.MAX_RECENT_ACCESSES))

        # 统计信息
        self.trend_stats = {
            "total_analyses": 0,
            "total_hot_knowledge_detected": 0,
            "trend_changes_detected": 0,
            "value_assessments": 0
        }

        logger.info("[OK] 知识趋势分析器初始化完成")

    # ========== 核心分析方法 ==========

    async def record_access(
        self,
        knowledge_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """记录知识访问

        Args:
            knowledge_id: 知识ID
            content: 知识内容
            metadata: 元数据
        """
        now = datetime.now()

        # 更新使用记录
        if knowledge_id not in self.usage_records:
            self.usage_records[knowledge_id] = KnowledgeUsageRecord(
                knowledge_id=knowledge_id,
                content=content,
                access_count=1,
                last_accessed=now,
                first_accessed=now,
                access_frequency=1.0,
                recent_accesses=[now]
            )
        else:
            record = self.usage_records[knowledge_id]
            record.access_count += 1
            record.last_accessed = now
            record.recent_accesses.append(now)

            # 计算访问频率
            days_active = (now - record.first_accessed).days + 1
            record.access_frequency = record.access_count / days_active

        # 更新访问历史
        self.access_history[knowledge_id].append(now)

    async def analyze_usage_trends(
        self,
        knowledge_id: str
    ) -> Optional[TrendAnalysis]:
        """分析知识使用趋势

        Args:
            knowledge_id: 知识ID

        Returns:
            趋势分析结果
        """
        if knowledge_id not in self.usage_records:
            logger.warning(f"知识 {knowledge_id} 没有使用记录")
            return None

        record = self.usage_records[knowledge_id]
        access_times = list(self.access_history[knowledge_id])

        if len(access_times) < 3:  # 数据不足
            return None

        try:
            # 计算趋势
            trend_direction, trend_strength = await self._calculate_trend(
                access_times
            )

            # 计算变化率
            change_rate = await self._calculate_change_rate(access_times)

            # 预测未来需求
            predicted_demand, confidence = await self._predict_future_demand(
                access_times
            )

            analysis = TrendAnalysis(
                knowledge_id=knowledge_id,
                trend_direction=trend_direction,
                trend_strength=trend_strength,
                change_rate=change_rate,
                predicted_demand=predicted_demand,
                confidence=confidence
            )

            # 更新统计
            self.trend_stats["total_analyses"] += 1

            return analysis

        except Exception as e:
            logger.error(f"分析趋势失败: {e}")
            return None

    async def identify_hot_knowledge(
        self,
        top_n: int = 10
    ) -> List[HotKnowledge]:
        """识别热点知识

        Args:
            top_n: 返回数量

        Returns:
            热点知识列表
        """
        hot_knowledge_list = []

        for knowledge_id, record in self.usage_records.items():
            if record.access_count < self.min_access_count:
                continue

            # 计算热度分数
            hot_score = await self._calculate_hot_score(record)

            if hot_score >= self.hot_threshold:
                # 评估价值
                value_assessment = await self.assess_knowledge_value(knowledge_id)

                hot_knowledge = HotKnowledge(
                    knowledge_id=knowledge_id,
                    content=record.content,
                    hot_score=hot_score,
                    access_count=record.access_count,
                    recent_activity=await self._calculate_recent_activity(record),
                    value_score=value_assessment.value_score
                )

                hot_knowledge_list.append(hot_knowledge)

        # 按热度排序
        hot_knowledge_list.sort(key=lambda x: x.hot_score, reverse=True)

        # 更新统计
        self.trend_stats["total_hot_knowledge_detected"] = len(hot_knowledge_list)

        logger.info(f"识别出 {len(hot_knowledge_list)} 条热点知识")
        return hot_knowledge_list[:top_n]

    async def assess_knowledge_value(
        self,
        knowledge_id: str
    ) -> KnowledgeValueAssessment:
        """评估知识价值

        Args:
            knowledge_id: 知识ID

        Returns:
            价值评估结果
        """
        if knowledge_id not in self.usage_records:
            # 无使用记录，给低价值
            return KnowledgeValueAssessment(
                knowledge_id=knowledge_id,
                value_score=0.1,
                value_tier=KnowledgeValueTier.NEGLECTED,
                value_factors={}
            )

        record = self.usage_records[knowledge_id]

        # 计算各价值因子
        usage_frequency_score = await self._assess_usage_frequency(record)
        recency_score = await self._assess_recency(record)
        consistency_score = await self._assess_consistency(knowledge_id)
        impact_score = await self._assess_impact(record)
        uniqueness_score = await self._assess_uniqueness(knowledge_id)

        value_factors = {
            "usage_frequency": usage_frequency_score,
            "recency": recency_score,
            "consistency": consistency_score,
            "impact": impact_score,
            "uniqueness": uniqueness_score
        }

        # 计算加权总分
        value_score = sum(
            score * self.VALUE_WEIGHTS[factor]
            for factor, score in value_factors.items()
        )

        # 确定价值等级
        value_tier = self._determine_value_tier(value_score)

        assessment = KnowledgeValueAssessment(
            knowledge_id=knowledge_id,
            value_score=value_score,
            value_tier=value_tier,
            value_factors=value_factors
        )

        # 更新统计
        self.trend_stats["value_assessments"] += 1

        return assessment

    # ========== 趋势计算方法 ==========

    async def _calculate_trend(
        self,
        access_times: List[datetime]
    ) -> Tuple[TrendDirection, float]:
        """计算趋势方向和强度"""
        if len(access_times) < 3:
            return TrendDirection.STABLE, 0.0

        # 将时间转换为相对天数
        now = datetime.now()
        days_ago = [(now - t).days for t in access_times]
        days_ago.reverse()  # 最早的时间在前

        # 计算访问间隔
        if len(days_ago) >= 2:
            intervals = [days_ago[i] - days_ago[i+1] for i in range(len(days_ago)-1)]

            if not intervals:
                return TrendDirection.STABLE, 0.0

            # 分析间隔变化
            recent_intervals = intervals[-3:] if len(intervals) >= 3 else intervals
            avg_interval = sum(intervals) / len(intervals)
            recent_avg = sum(recent_intervals) / len(recent_intervals)

            # 判断趋势
            if recent_avg < avg_interval * 0.7:  # 访问更频繁
                strength = min(1.0, (avg_interval - recent_avg) / avg_interval)
                return TrendDirection.RISING, strength
            elif recent_avg > avg_interval * 1.3:  # 访问减少
                strength = min(1.0, (recent_avg - avg_interval) / avg_interval)
                return TrendDirection.DECLINING, strength
            else:
                # 检查波动性
                if max(intervals) - min(intervals) > avg_interval:
                    return TrendDirection.VOLATILE, 0.5
                else:
                    return TrendDirection.STABLE, 0.3

        return TrendDirection.STABLE, 0.0

    async def _calculate_change_rate(
        self,
        access_times: List[datetime]
    ) -> float:
        """计算变化率"""
        if len(access_times) < 4:
            return 0.0

        now = datetime.now()

        # 分为两个时期
        mid_point = len(access_times) // 2
        early_period = access_times[:mid_point]
        recent_period = access_times[mid_point:]

        # 计算每个时期的访问频率
        if early_period and recent_period:
            early_span = (now - early_period[-1]).days + 1
            recent_span = (now - recent_period[-1]).days + 1

            early_rate = len(early_period) / max(early_span, 1)
            recent_rate = len(recent_period) / max(recent_span, 1)

            # 计算变化率
            if early_rate > 0:
                change_rate = (recent_rate - early_rate) / early_rate
                return change_rate

        return 0.0

    async def _predict_future_demand(
        self,
        access_times: List[datetime]
    ) -> Tuple[float, float]:
        """预测未来需求

        Returns:
            (预测需求, 置信度)
        """
        if len(access_times) < 5:
            return 0.0, 0.0

        try:
            now = datetime.now()
            days_ago = [(now - t).days for t in access_times]

            # 简单的线性回归预测
            # 将访问按天分组
            daily_counts = defaultdict(int)
            for day in days_ago:
                daily_counts[day] += 1

            # 获取最近的趋势
            recent_days = sorted(daily_counts.keys())[:min(7, len(daily_counts))]
            if len(recent_days) >= 3:
                recent_counts = [daily_counts[day] for day in recent_days]

                # 计算趋势
                if len(recent_counts) >= 2:
                    trend = statistics.mean(recent_counts[-3:]) if len(recent_counts) >= 3 else recent_counts[-1]

                    # 置信度基于数据量和一致性
                    data_quality = min(1.0, len(access_times) / 20.0)
                    consistency = 1.0 - (statistics.stdev(recent_counts) / (max(recent_counts) + 1)) if len(recent_counts) > 1 else 0.5

                    confidence = data_quality * consistency

                    return trend, confidence

        except Exception as e:
            logger.warning(f"预测需求失败: {e}")

        return 0.0, 0.0

    # ========== 热度计算方法 ==========

    async def _calculate_hot_score(
        self,
        record: KnowledgeUsageRecord
    ) -> float:
        """计算热度分数"""
        # 基础分数：访问次数
        base_score = min(1.0, record.access_count / 20.0)

        # 近期活动加成
        recent_activity = await self._calculate_recent_activity(record)
        activity_bonus = recent_activity * 0.3

        # 访问频率加成
        frequency_bonus = min(0.3, record.access_frequency / 10.0)

        # 持续性加成
        consistency_bonus = await self._assess_consistency(record.knowledge_id) * 0.2

        # 综合热度分数
        hot_score = (
            base_score * 0.4 +
            activity_bonus +
            frequency_bonus +
            consistency_bonus
        )

        return min(hot_score, 1.0)

    async def _calculate_recent_activity(
        self,
        record: KnowledgeUsageRecord
    ) -> float:
        """计算近期活动度"""
        now = datetime.now()
        recent_threshold = timedelta(days=3)

        recent_count = sum(
            1 for access_time in record.recent_accesses
            if now - access_time <= recent_threshold
        )

        # 归一化到0-1
        activity = min(1.0, recent_count / 10.0)

        return activity

    # ========== 价值评估方法 ==========

    async def _assess_usage_frequency(
        self,
        record: KnowledgeUsageRecord
    ) -> float:
        """评估使用频率"""
        # 归一化频率 (假设每天10次访问为高频)
        return min(1.0, record.access_frequency / 10.0)

    async def _assess_recency(
        self,
        record: KnowledgeUsageRecord
    ) -> float:
        """评估新近度"""
        now = datetime.now()
        days_since_last = (now - record.last_accessed).days

        # 最近访问得分更高
        if days_since_last <= 1:
            return 1.0
        elif days_since_last <= 3:
            return 0.8
        elif days_since_last <= 7:
            return 0.5
        elif days_since_last <= 14:
            return 0.3
        else:
            return 0.1

    async def _assess_consistency(
        self,
        knowledge_id: str
    ) -> float:
        """评估一致性"""
        access_times = list(self.access_history[knowledge_id])

        if len(access_times) < 3:
            return 0.5

        # 计算访问间隔的标准差
        intervals = []
        for i in range(1, len(access_times)):
            interval = (access_times[i] - access_times[i-1]).total_seconds() / 86400  # 转换为天
            intervals.append(interval)

        if not intervals:
            return 0.5

        try:
            std_dev = statistics.stdev(intervals)
            mean_interval = statistics.mean(intervals)

            # 一致性：标准差越小，一致性越高
            if mean_interval > 0:
                consistency = max(0.0, 1.0 - (std_dev / mean_interval))
                return consistency
        except:
            pass

        return 0.5

    async def _assess_impact(
        self,
        record: KnowledgeUsageRecord
    ) -> float:
        """评估影响力"""
        # 基于访问次数的简单评估
        # 实际应用中可以结合其他因素，如用户反馈等
        return min(1.0, record.access_count / 30.0)

    async def _assess_uniqueness(
        self,
        knowledge_id: str
    ) -> float:
        """评估独特性"""
        # 简化版本：基于内容长度和特殊特征
        if knowledge_id in self.usage_records:
            content = self.usage_records[knowledge_id].content

            # 较长的内容可能包含更多独特信息
            length_score = min(1.0, len(content) / 200.0)

            # 检查是否包含具体数据
            has_data = any(char.isdigit() for char in content)
            data_score = 0.3 if has_data else 0.0

            return (length_score + data_score) / 1.3

        return 0.5

    def _determine_value_tier(self, value_score: float) -> KnowledgeValueTier:
        """确定价值等级"""
        if value_score >= 0.8:
            return KnowledgeValueTier.CRITICAL
        elif value_score >= 0.6:
            return KnowledgeValueTier.HIGH
        elif value_score >= 0.4:
            return KnowledgeValueTier.MEDIUM
        elif value_score >= 0.2:
            return KnowledgeValueTier.LOW
        else:
            return KnowledgeValueTier.NEGLECTED

    # ========== 报告生成 ==========

    async def generate_trend_report(
        self,
        days: int = 7
    ) -> TrendReport:
        """生成趋势报告

        Args:
            days: 分析天数

        Returns:
            趋势报告
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        # 分析所有知识的趋势
        trend_analyses = []
        for knowledge_id in self.usage_records:
            analysis = await self.analyze_usage_trends(knowledge_id)
            if analysis:
                trend_analyses.append(analysis)

        # 趋势分布
        trend_distribution = defaultdict(int)
        for analysis in trend_analyses:
            trend_distribution[analysis.trend_direction] += 1

        # 识别上升和下降趋势
        rising_knowledge = [
            {
                "knowledge_id": a.knowledge_id,
                "trend_strength": a.trend_strength,
                "change_rate": a.change_rate
            }
            for a in trend_analyses
            if a.trend_direction == TrendDirection.RISING
        ]
        rising_knowledge.sort(key=lambda x: x["trend_strength"], reverse=True)

        declining_knowledge = [
            {
                "knowledge_id": a.knowledge_id,
                "trend_strength": a.trend_strength,
                "change_rate": a.change_rate
            }
            for a in trend_analyses
            if a.trend_direction == TrendDirection.DECLINING
        ]
        declining_knowledge.sort(key=lambda x: x["trend_strength"], reverse=True)

        # 获取热点知识
        hot_knowledge_objs = await self.identify_hot_knowledge(10)
        hot_knowledge = [hk.to_dict() for hk in hot_knowledge_objs]

        # 价值分布
        value_distribution = defaultdict(int)
        for knowledge_id in self.usage_records:
            assessment = await self.assess_knowledge_value(knowledge_id)
            value_distribution[assessment.value_tier] += 1

        # 生成建议
        recommendations = self._generate_recommendations(
            trend_distribution, value_distribution, rising_knowledge, declining_knowledge
        )

        return TrendReport(
            analysis_period=(start_time, end_time),
            total_knowledge_analyzed=len(self.usage_records),
            trend_distribution=trend_distribution,
            top_rising_knowledge=rising_knowledge[:5],
            top_declining_knowledge=declining_knowledge[:5],
            hot_knowledge=hot_knowledge,
            value_distribution=value_distribution,
            recommendations=recommendations
        )

    def _generate_recommendations(
        self,
        trend_distribution: Dict[TrendDirection, int],
        value_distribution: Dict[KnowledgeValueTier, int],
        rising_knowledge: List[Dict],
        declining_knowledge: List[Dict]
    ) -> List[str]:
        """生成建议"""
        recommendations = []

        total_trends = sum(trend_distribution.values())
        if total_trends > 0:
            rising_ratio = trend_distribution.get(TrendDirection.RISING, 0) / total_trends

            if rising_ratio > 0.4:
                recommendations.append("知识库活跃度较高，多个知识点使用量上升")
            elif rising_ratio < 0.2:
                recommendations.append("知识库活跃度偏低，建议关注知识推广")

        # 基于价值分布
        total_value = sum(value_distribution.values())
        if total_value > 0:
            neglected_ratio = value_distribution.get(KnowledgeValueTier.NEGLECTED, 0) / total_value

            if neglected_ratio > 0.3:
                recommendations.append(f"有 {neglected_ratio:.1%} 的知识被忽视，建议清理或优化")

        # 基于热点知识
        if rising_knowledge:
            recommendations.append(f"关注上升趋势的知识: {rising_knowledge[0]['knowledge_id']}")

        # 基于下降趋势
        if declining_knowledge:
            recommendations.append(f"部分知识使用量下降，可能需要更新: {declining_knowledge[0]['knowledge_id']}")

        return recommendations

    # ========== 统计和工具方法 ==========

    def get_trend_stats(self) -> Dict[str, Any]:
        """获取趋势统计"""
        return self.trend_stats.copy()

    def get_usage_summary(self) -> Dict[str, Any]:
        """获取使用摘要"""
        total_accesses = sum(record.access_count for record in self.usage_records.values())
        avg_frequency = statistics.mean(
            [record.access_frequency for record in self.usage_records.values()]
        ) if self.usage_records else 0.0

        return {
            "total_knowledge": len(self.usage_records),
            "total_accesses": total_accesses,
            "average_access_frequency": avg_frequency,
            "most_accessed": max(
                self.usage_records.values(),
                key=lambda x: x.access_count,
                default=None
            )
        }

    def reset_stats(self):
        """重置统计"""
        self.trend_stats = {
            "total_analyses": 0,
            "total_hot_knowledge_detected": 0,
            "trend_changes_detected": 0,
            "value_assessments": 0
        }
        logger.info("趋势统计已重置")


def create_knowledge_trend_analyzer(
    config: Dict[str, Any]
) -> KnowledgeTrendAnalyzer:
    """创建知识趋势分析器实例

    Args:
        config: 配置字典

    Returns:
        知识趋势分析器实例
    """
    return KnowledgeTrendAnalyzer(config)
