"""知识质量优化器 - V5.10 Phase 1.3

智能评估知识质量，自动优化知识内容，
清理过期和低质量知识，提升知识库整体质量。

核心功能：
1. 知识质量评分系统
2. 低质量知识识别
3. 自动内容优化
4. 过期知识清理

基于：V5.10架构设计
创建时间：2026-04-19
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import re

logger = logging.getLogger(__name__)


class QualityDimension(Enum):
    """质量维度枚举"""
    COMPLETENESS = "completeness"  # 完整性
    ACCURACY = "accuracy"  # 准确性
    RELEVANCE = "relevance"  # 相关性
    FRESHNESS = "freshness"  # 新鲜度
    CLARITY = "clarity"  # 清晰度
    VERIFIABILITY = "verifiability"  # 可验证性


class QualityLevel(Enum):
    """质量等级枚举"""
    EXCELLENT = "excellent"  # 优秀 (0.9-1.0)
    GOOD = "good"  # 良好 (0.7-0.9)
    ACCEPTABLE = "acceptable"  # 可接受 (0.5-0.7)
    POOR = "poor"  # 较差 (0.3-0.5)
    VERY_POOR = "very_poor"  # 很差 (0.0-0.3)


@dataclass
class QualityScore:
    """质量分数"""
    overall_score: float
    dimension_scores: Dict[QualityDimension, float]
    quality_level: QualityLevel
    assessed_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "overall_score": self.overall_score,
            "dimension_scores": {
                dim.value: score for dim, score in self.dimension_scores.items()
            },
            "quality_level": self.quality_level.value,
            "assessed_at": self.assessed_at.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class OptimizedKnowledge:
    """优化后的知识"""
    original_content: str
    optimized_content: str
    quality_improvement: float
    optimization_actions: List[str]
    optimized_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "original_content": self.original_content,
            "optimized_content": self.optimized_content,
            "quality_improvement": self.quality_improvement,
            "optimization_actions": self.optimization_actions,
            "optimized_at": self.optimized_at.isoformat()
        }


@dataclass
class KnowledgeQualityReport:
    """知识质量报告"""
    total_knowledge: int
    quality_distribution: Dict[QualityLevel, int]
    average_quality_score: float
    low_quality_items: List[Dict[str, Any]]
    expired_items: List[Dict[str, Any]]
    optimization_suggestions: List[str]
    generated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total_knowledge": self.total_knowledge,
            "quality_distribution": {
                level.value: count for level, count in self.quality_distribution.items()
            },
            "average_quality_score": self.average_quality_score,
            "low_quality_items": self.low_quality_items,
            "expired_items": self.expired_items,
            "optimization_suggestions": self.optimization_suggestions,
            "generated_at": self.generated_at.isoformat()
        }


class KnowledgeQualityOptimizer:
    """知识质量优化器

    智能评估和优化知识质量，提升知识库整体价值。
    """

    # 质量维度权重
    DIMENSION_WEIGHTS = {
        QualityDimension.COMPLETENESS: 0.2,
        QualityDimension.ACCURACY: 0.25,
        QualityDimension.RELEVANCE: 0.2,
        QualityDimension.FRESHNESS: 0.15,
        QualityDimension.CLARITY: 0.1,
        QualityDimension.VERIFIABILITY: 0.1
    }

    # 质量等级阈值
    QUALITY_THRESHOLDS = {
        QualityLevel.VERY_POOR: 0.0,
        QualityLevel.POOR: 0.3,
        QualityLevel.ACCEPTABLE: 0.5,
        QualityLevel.GOOD: 0.7,
        QualityLevel.EXCELLENT: 0.9
    }

    def __init__(self, config: Dict[str, Any]):
        """初始化知识质量优化器

        Args:
            config: 配置字典
        """
        self.config = config

        # 质量评估配置
        self.min_quality_threshold = config.get('min_quality_threshold', 0.5)
        self.enable_auto_optimization = config.get('enable_auto_optimization', True)
        self.expiry_days = config.get('expiry_days', 30)

        # 优化配置
        self.max_optimization_iterations = config.get('max_optimization_iterations', 3)
        self.min_improvement_threshold = config.get('min_improvement_threshold', 0.1)

        # 统计信息
        self.quality_stats = {
            "total_assessments": 0,
            "total_optimizations": 0,
            "total_cleaned": 0,
            "quality_improvements": [],
            "by_quality_level": {}
        }

        # 质量历史
        self.quality_history: List[Dict[str, Any]] = []

        logger.info("[OK] 知识质量优化器初始化完成")

    # ========== 核心质量评估方法 ==========

    async def calculate_quality_score(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None
    ) -> QualityScore:
        """计算知识质量分数

        Args:
            content: 知识内容
            metadata: 元数据
            created_at: 创建时间

        Returns:
            质量分数
        """
        try:
            dimension_scores = {}

            # 评估各个维度
            dimension_scores[QualityDimension.COMPLETENESS] = \
                await self._assess_completeness(content, metadata)

            dimension_scores[QualityDimension.ACCURACY] = \
                await self._assess_accuracy(content, metadata)

            dimension_scores[QualityDimension.RELEVANCE] = \
                await self._assess_relevance(content, metadata)

            dimension_scores[QualityDimension.FRESHNESS] = \
                await self._assess_freshness(content, metadata, created_at)

            dimension_scores[QualityDimension.CLARITY] = \
                await self._assess_clarity(content)

            dimension_scores[QualityDimension.VERIFIABILITY] = \
                await self._assess_verifiability(content, metadata)

            # 计算加权总分
            overall_score = sum(
                score * self.DIMENSION_WEIGHTS[dim]
                for dim, score in dimension_scores.items()
            )

            # 确定质量等级
            quality_level = self._determine_quality_level(overall_score)

            quality_score = QualityScore(
                overall_score=overall_score,
                dimension_scores=dimension_scores,
                quality_level=quality_level,
                metadata=metadata or {}
            )

            # 更新统计
            self._update_quality_stats(quality_score)

            return quality_score

        except Exception as e:
            logger.error(f"计算质量分数失败: {e}")
            # 返回默认分数
            return QualityScore(
                overall_score=0.5,
                dimension_scores={dim: 0.5 for dim in QualityDimension},
                quality_level=QualityLevel.ACCEPTABLE,
                metadata=metadata or {}
            )

    async def assess_batch_quality(
        self,
        knowledge_items: List[Dict[str, Any]]
    ) -> List[QualityScore]:
        """批量评估知识质量

        Args:
            knowledge_items: 知识条目列表

        Returns:
            质量分数列表
        """
        quality_scores = []

        for item in knowledge_items:
            content = item.get('content', '')
            metadata = item.get('metadata', {})
            created_at_str = item.get('created_at')

            created_at = None
            if created_at_str:
                try:
                    created_at = datetime.fromisoformat(created_at_str)
                except:
                    pass

            quality_score = await self.calculate_quality_score(
                content, metadata, created_at
            )
            quality_scores.append(quality_score)

        logger.info(f"批量质量评估完成: {len(quality_scores)} 条知识")
        return quality_scores

    # ========== 维度评估方法 ==========

    async def _assess_completeness(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]]
    ) -> float:
        """评估完整性"""
        score = 0.5  # 基础分

        # 内容长度评估
        if len(content) > 50:
            score += 0.2
        if len(content) > 100:
            score += 0.1

        # 元数据完整性
        if metadata:
            required_fields = ['symbol', 'category', 'source']
            present_fields = sum(1 for field in required_fields if field in metadata)
            score += (present_fields / len(required_fields)) * 0.2

        return min(score, 1.0)

    async def _assess_accuracy(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]]
    ) -> float:
        """评估准确性"""
        score = 0.6  # 基础分

        # 检查数值合理性
        if metadata:
            profit = metadata.get('profit', 0)
            profit_rate = metadata.get('profit_rate', 0)

            # 合理的收益率范围 (-100% 到 +1000%)
            if -100 <= profit_rate <= 1000:
                score += 0.2
            else:
                score -= 0.2

            # 检查时间戳合理性
            timestamp = metadata.get('timestamp')
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp) if isinstance(timestamp, str) else timestamp
                    if datetime.now() - dt < timedelta(days=365):
                        score += 0.2
                except:
                    pass

        return max(0.0, min(score, 1.0))

    async def _assess_relevance(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]]
    ) -> float:
        """评估相关性"""
        score = 0.5  # 基础分

        # 关键词相关性
        relevant_keywords = [
            "交易", "策略", "风险", "市场", "套利", "盈利", "亏损",
            "trade", "strategy", "risk", "market", "arbitrage", "profit", "loss"
        ]

        keyword_count = sum(1 for kw in relevant_keywords if kw in content.lower())
        if keyword_count > 0:
            score += min(keyword_count * 0.1, 0.3)

        # 元数据相关性
        if metadata:
            if metadata.get('category'):
                score += 0.1
            if metadata.get('symbol'):
                score += 0.1

        return min(score, 1.0)

    async def _assess_freshness(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]],
        created_at: Optional[datetime]
    ) -> float:
        """评估新鲜度"""
        if created_at is None:
            return 0.5  # 无时间信息，给中等分

        now = datetime.now()
        age_days = (now - created_at).days

        # 新鲜度随时间衰减
        if age_days <= 1:
            return 1.0
        elif age_days <= 7:
            return 0.9
        elif age_days <= 14:
            return 0.7
        elif age_days <= 30:
            return 0.5
        elif age_days <= 90:
            return 0.3
        else:
            return 0.1

    async def _assess_clarity(self, content: str) -> float:
        """评估清晰度"""
        score = 0.5  # 基础分

        # 句子结构
        sentences = re.split(r'[。！？.!?]', content)
        if len(sentences) > 1:
            score += 0.1

        # 避免过长的句子
        avg_sentence_length = len(content) / max(len(sentences), 1)
        if avg_sentence_length < 100:
            score += 0.2

        # 避免过多的特殊字符
        special_char_ratio = len(re.findall(r'[^\w\s\u4e00-\u9fff]', content)) / max(len(content), 1)
        if special_char_ratio < 0.1:
            score += 0.2

        return min(score, 1.0)

    async def _assess_verifiability(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]]
    ) -> float:
        """评估可验证性"""
        score = 0.4  # 基础分

        # 元数据提供验证信息
        if metadata:
            if metadata.get('source'):
                score += 0.2
            if metadata.get('timestamp'):
                score += 0.2
            if metadata.get('exchange') or metadata.get('symbol'):
                score += 0.2

        # 内容包含具体数据
        if re.search(r'\d+\.?\d*%', content):  # 包含百分比
            score += 0.1
        if re.search(r'\d+\.?\d*', content):  # 包含数字
            score += 0.1

        return min(score, 1.0)

    # ========== 质量等级确定 ==========

    def _determine_quality_level(self, score: float) -> QualityLevel:
        """确定质量等级"""
        for level, threshold in sorted(
            self.QUALITY_THRESHOLDS.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            if score >= threshold:
                return level
        return QualityLevel.VERY_POOR

    # ========== 知识优化方法 ==========

    async def optimize_knowledge(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> OptimizedKnowledge:
        """优化知识内容

        Args:
            content: 原始内容
            metadata: 元数据

        Returns:
            优化后的知识
        """
        if not self.enable_auto_optimization:
            return OptimizedKnowledge(
                original_content=content,
                optimized_content=content,
                quality_improvement=0.0,
                optimization_actions=[]
            )

        original_score = await self.calculate_quality_score(content, metadata)
        optimized_content = content
        optimization_actions = []

        # 迭代优化
        for iteration in range(self.max_optimization_iterations):
            # 应用优化规则
            new_content, actions = await self._apply_optimization_rules(
                optimized_content, metadata
            )

            if actions:
                optimized_content = new_content
                optimization_actions.extend(actions)

            # 检查改进程度
            new_score = await self.calculate_quality_score(optimized_content, metadata)
            improvement = new_score.overall_score - original_score.overall_score

            if improvement < self.min_improvement_threshold:
                break  # 改进不足，停止优化

        # 计算最终改进
        final_score = await self.calculate_quality_score(optimized_content, metadata)
        quality_improvement = final_score.overall_score - original_score.overall_score

        # 更新统计
        self.quality_stats["total_optimizations"] += 1
        self.quality_stats["quality_improvements"].append(quality_improvement)

        return OptimizedKnowledge(
            original_content=content,
            optimized_content=optimized_content,
            quality_improvement=quality_improvement,
            optimization_actions=optimization_actions
        )

    async def _apply_optimization_rules(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]]
    ) -> tuple[str, List[str]]:
        """应用优化规则"""
        optimized_content = content
        actions = []

        # 规则1: 移除重复内容
        if len(content) != len(set(content.split())):
            optimized_content = ' '.join(dict.fromkeys(content.split()))
            actions.append("移除重复词语")

        # 规则2: 标准化格式
        if '...' in content:
            optimized_content = optimized_content.replace('...', '。')
            actions.append("标准化标点")

        # 规则3: 补充缺失的元数据信息
        if metadata and not metadata.get('timestamp'):
            # 这里可以添加时间戳推断逻辑
            pass

        # 规则4: 改善句子结构
        if len(optimized_content) > 0 and optimized_content[-1] not in '。！？.!?,，':
            optimized_content += '。'
            actions.append("补充句末标点")

        return optimized_content, actions

    # ========== 知识清理方法 ==========

    async def identify_low_quality(
        self,
        knowledge_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """识别低质量知识

        Args:
            knowledge_items: 知识条目列表

        Returns:
            低质量知识列表
        """
        low_quality_items = []

        for item in knowledge_items:
            content = item.get('content', '')
            metadata = item.get('metadata', {})

            quality_score = await self.calculate_quality_score(content, metadata)

            if quality_score.overall_score < self.min_quality_threshold:
                low_quality_items.append({
                    "item": item,
                    "quality_score": quality_score.to_dict(),
                    "reason": f"质量分数 {quality_score.overall_score:.2f} 低于阈值 {self.min_quality_threshold}"
                })

        logger.info(f"识别出 {len(low_quality_items)} 条低质量知识")
        return low_quality_items

    async def identify_expired_knowledge(
        self,
        knowledge_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """识别过期知识

        Args:
            knowledge_items: 知识条目列表

        Returns:
            过期知识列表
        """
        expired_items = []
        now = datetime.now()
        expiry_threshold = timedelta(days=self.expiry_days)

        for item in knowledge_items:
            created_at_str = item.get('created_at') or item.get('timestamp')

            if created_at_str:
                try:
                    created_at = datetime.fromisoformat(created_at_str) \
                        if isinstance(created_at_str, str) else created_at_str

                    if now - created_at > expiry_threshold:
                        expired_items.append({
                            "item": item,
                            "age_days": (now - created_at).days,
                            "reason": f"知识已过期 {(now - created_at).days} 天"
                        })
                except:
                    pass

        logger.info(f"识别出 {len(expired_items)} 条过期知识")
        return expired_items

    async def clean_low_quality_knowledge(
        self,
        knowledge_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """清理低质量知识

        Args:
            knowledge_items: 知识条目列表

        Returns:
            清理结果
        """
        # 识别低质量知识
        low_quality_items = await self.identify_low_quality(knowledge_items)

        # 识别过期知识
        expired_items = await self.identify_expired_knowledge(knowledge_items)

        # 合并需要清理的知识
        items_to_remove = set()
        for item_info in low_quality_items:
            items_to_remove.add(id(item_info["item"]))

        for item_info in expired_items:
            items_to_remove.add(id(item_info["item"]))

        # 保留高质量知识
        cleaned_items = [
            item for item in knowledge_items
            if id(item) not in items_to_remove
        ]

        # 更新统计
        removed_count = len(knowledge_items) - len(cleaned_items)
        self.quality_stats["total_cleaned"] += removed_count

        logger.info(f"清理完成: 移除 {removed_count} 条低质量/过期知识")

        return {
            "original_count": len(knowledge_items),
            "cleaned_count": len(cleaned_items),
            "removed_count": removed_count,
            "low_quality_count": len(low_quality_items),
            "expired_count": len(expired_items),
            "cleaned_items": cleaned_items
        }

    # ========== 质量报告生成 ==========

    async def generate_quality_report(
        self,
        knowledge_items: List[Dict[str, Any]]
    ) -> KnowledgeQualityReport:
        """生成质量报告

        Args:
            knowledge_items: 知识条目列表

        Returns:
            质量报告
        """
        # 批量评估质量
        quality_scores = await self.assess_batch_quality(knowledge_items)

        # 质量分布
        quality_distribution = {level: 0 for level in QualityLevel}
        total_score = 0.0

        for score in quality_scores:
            quality_distribution[score.quality_level] += 1
            total_score += score.overall_score

        average_quality_score = total_score / len(quality_scores) if quality_scores else 0.0

        # 识别问题知识
        low_quality_items = await self.identify_low_quality(knowledge_items)
        expired_items = await self.identify_expired_knowledge(knowledge_items)

        # 生成优化建议
        optimization_suggestions = self._generate_optimization_suggestions(
            quality_distribution, average_quality_score
        )

        # 记录质量历史
        self.quality_history.append({
            "timestamp": datetime.now().isoformat(),
            "total_knowledge": len(knowledge_items),
            "average_quality": average_quality_score,
            "quality_distribution": {
                level.value: count for level, count in quality_distribution.items()
            }
        })

        return KnowledgeQualityReport(
            total_knowledge=len(knowledge_items),
            quality_distribution=quality_distribution,
            average_quality_score=average_quality_score,
            low_quality_items=low_quality_items,
            expired_items=expired_items,
            optimization_suggestions=optimization_suggestions
        )

    def _generate_optimization_suggestions(
        self,
        quality_distribution: Dict[QualityLevel, int],
        average_quality: float
    ) -> List[str]:
        """生成优化建议"""
        suggestions = []

        # 基于平均质量
        if average_quality < 0.5:
            suggestions.append("整体知识质量较低，建议加强知识提取和验证")
        elif average_quality < 0.7:
            suggestions.append("知识质量有待提升，建议优化知识提取流程")
        else:
            suggestions.append("知识质量良好，继续保持")

        # 基于质量分布
        total = sum(quality_distribution.values())
        if total > 0:
            poor_ratio = (quality_distribution[QualityLevel.POOR] +
                         quality_distribution[QualityLevel.VERY_POOR]) / total

            if poor_ratio > 0.3:
                suggestions.append(f"低质量知识占比过高 ({poor_ratio:.1%})，建议启用自动清理")

        # 基于过期知识
        if self.quality_stats["total_cleaned"] > 10:
            suggestions.append("定期清理过期知识，保持知识库新鲜度")

        return suggestions

    # ========== 统计和工具方法 ==========

    def _update_quality_stats(self, quality_score: QualityScore):
        """更新质量统计"""
        self.quality_stats["total_assessments"] += 1

        level = quality_score.quality_level
        if level not in self.quality_stats["by_quality_level"]:
            self.quality_stats["by_quality_level"][level] = 0
        self.quality_stats["by_quality_level"][level] += 1

    def get_quality_stats(self) -> Dict[str, Any]:
        """获取质量统计"""
        stats = self.quality_stats.copy()

        # 计算平均改进
        if stats["quality_improvements"]:
            stats["average_improvement"] = sum(stats["quality_improvements"]) / len(stats["quality_improvements"])
        else:
            stats["average_improvement"] = 0.0

        return stats

    def get_quality_trend(self, days: int = 7) -> List[Dict[str, Any]]:
        """获取质量趋势

        Args:
            days: 查询天数

        Returns:
            质量趋势数据
        """
        cutoff_time = datetime.now() - timedelta(days=days)

        return [
            record for record in self.quality_history
            if datetime.fromisoformat(record["timestamp"]) >= cutoff_time
        ]

    def reset_stats(self):
        """重置统计"""
        self.quality_stats = {
            "total_assessments": 0,
            "total_optimizations": 0,
            "total_cleaned": 0,
            "quality_improvements": [],
            "by_quality_level": {}
        }
        self.quality_history.clear()
        logger.info("质量统计已重置")


def create_knowledge_quality_optimizer(
    config: Dict[str, Any]
) -> KnowledgeQualityOptimizer:
    """创建知识质量优化器实例

    Args:
        config: 配置字典

    Returns:
        知识质量优化器实例
    """
    return KnowledgeQualityOptimizer(config)
