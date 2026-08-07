"""智能知识分类器 - V5.10 Phase 1.2

基于内容智能分类知识，自动生成多维度标签，
实现知识的自动组织和管理。

核心功能：
1. 基于内容的智能分类
2. 自动标签生成
3. 多维度标签系统
4. 类别优化和聚类

基于：V5.10架构设计
创建时间：2026-04-19
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class KnowledgeCategory(Enum):
    """知识类别枚举（扩展版）"""
    STRATEGY = "strategy"
    RISK_MANAGEMENT = "risk_management"
    MARKET_ANALYSIS = "market_analysis"
    EXECUTION = "execution"
    PERFORMANCE = "performance"
    ANOMALY = "anomaly"
    OPTIMIZATION = "optimization"
    MARKET_INSIGHT = "market_insight"
    TRADING_PATTERN = "trading_pattern"
    SYSTEM_PERFORMANCE = "system_performance"


class TagType(Enum):
    """标签类型枚举"""
    CONTENT_BASED = "content_based"
    CONTEXT_BASED = "context_based"
    TEMPORAL = "temporal"
    SYMBOL_SPECIFIC = "symbol_specific"
    STRATEGY_SPECIFIC = "strategy_specific"
    RISK_LEVEL = "risk_level"
    CONFIDENCE_LEVEL = "confidence_level"


@dataclass
class KnowledgeTag:
    """知识标签"""
    name: str
    tag_type: TagType
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "tag_type": self.tag_type.value,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class ClassifiedKnowledge:
    """分类后的知识"""
    content: str
    primary_category: KnowledgeCategory
    secondary_categories: List[KnowledgeCategory]
    tags: List[KnowledgeTag]
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    classified_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "content": self.content,
            "primary_category": self.primary_category.value,
            "secondary_categories": [cat.value for cat in self.secondary_categories],
            "tags": [tag.to_dict() for tag in self.tags],
            "confidence": self.confidence,
            "metadata": self.metadata,
            "classified_at": self.classified_at.isoformat()
        }


class IntelligentKnowledgeClassifier:
    """智能知识分类器

    基于内容和上下文智能分类知识，自动生成多维度标签。
    """

    # 类别关键词映射
    CATEGORY_KEYWORDS = {
        KnowledgeCategory.STRATEGY: [
            "策略", "strategy", "套利", "arbitrage", "交易", "trade",
            "执行", "execution", "机会", "opportunity", "方案", "plan"
        ],
        KnowledgeCategory.RISK_MANAGEMENT: [
            "风险", "risk", "控制", "control", "回撤", "drawdown",
            "止损", "stop_loss", "仓位", "position", "管理", "management"
        ],
        KnowledgeCategory.MARKET_ANALYSIS: [
            "市场", "market", "分析", "analysis", "趋势", "trend",
            "波动", "volatility", "行情", "price", "价格"
        ],
        KnowledgeCategory.EXECUTION: [
            "执行", "execution", "订单", "order", "成交", "fill",
            "滑点", "slippage", "延迟", "latency", "路径", "path"
        ],
        KnowledgeCategory.PERFORMANCE: [
            "盈利", "profit", "亏损", "loss", "收益", "return",
            "表现", "performance", "胜率", "win_rate", "结果", "result"
        ],
        KnowledgeCategory.ANOMALY: [
            "异常", "anomaly", "警告", "warning", "波动", "surge",
            "异常", "abnormal", "突发", "sudden"
        ],
        KnowledgeCategory.OPTIMIZATION: [
            "优化", "optimization", "改进", "improvement", "提升", "enhance",
            "调整", "adjust", "调优", "tuning"
        ],
        KnowledgeCategory.MARKET_INSIGHT: [
            "洞察", "insight", "观察", "observation", "发现", "discovery",
            "规律", "pattern", "特征", "feature"
        ],
        KnowledgeCategory.TRADING_PATTERN: [
            "模式", "pattern", "习惯", "habit", "行为", "behavior",
            "周期", "cycle", "频率", "frequency"
        ],
        KnowledgeCategory.SYSTEM_PERFORMANCE: [
            "系统", "system", "性能", "performance", "延迟", "latency",
            "响应", "response", "吞吐", "throughput", "资源", "resource"
        ]
    }

    def __init__(self, config: Dict[str, Any]):
        """初始化智能知识分类器

        Args:
            config: 配置字典
        """
        self.config = config

        # 分类配置
        self.enable_auto_tagging = config.get('enable_auto_tagging', True)
        self.min_category_confidence = config.get('min_category_confidence', 0.5)
        self.max_secondary_categories = config.get('max_secondary_categories', 2)
        self.enable_ml_classification = config.get('enable_ml_classification', False)

        # 标签配置
        self.max_tags_per_item = config.get('max_tags_per_item', 5)
        self.min_tag_confidence = config.get('min_tag_confidence', 0.6)

        # 类别统计
        self.category_stats = defaultdict(int)

        # 标签统计
        self.tag_stats = defaultdict(int)

        # 自定义类别规则
        self.custom_category_rules = config.get('custom_category_rules', {})

        logger.info("[OK] 智能知识分类器初始化完成")

    # ========== 核心分类方法 ==========

    async def classify_knowledge(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ClassifiedKnowledge:
        """分类知识条目

        Args:
            content: 知识内容
            metadata: 元数据

        Returns:
            分类后的知识
        """
        try:
            # 分析内容
            content_lower = content.lower()

            # 确定主要类别
            primary_category, primary_confidence = await self._determine_primary_category(
                content_lower, metadata
            )

            # 确定次要类别
            secondary_categories = await self._determine_secondary_categories(
                content_lower, metadata, primary_category
            )

            # 生成标签
            tags = []
            if self.enable_auto_tagging:
                tags = await self._auto_generate_tags(
                    content, metadata, primary_category
                )

            # 计算整体置信度
            overall_confidence = self._calculate_overall_confidence(
                primary_confidence, secondary_categories, tags
            )

            # 创建分类结果
            classified = ClassifiedKnowledge(
                content=content,
                primary_category=primary_category,
                secondary_categories=secondary_categories,
                tags=tags,
                confidence=overall_confidence,
                metadata=metadata or {}
            )

            # 更新统计
            self._update_classification_stats(classified)

            return classified

        except Exception as e:
            logger.error(f"分类知识失败: {e}")
            # 返回默认分类
            return ClassifiedKnowledge(
                content=content,
                primary_category=KnowledgeCategory.MARKET_ANALYSIS,
                secondary_categories=[],
                tags=[],
                confidence=0.3,
                metadata=metadata or {}
            )

    async def classify_batch(
        self,
        knowledge_items: List[Dict[str, Any]]
    ) -> List[ClassifiedKnowledge]:
        """批量分类知识

        Args:
            knowledge_items: 知识条目列表

        Returns:
            分类结果列表
        """
        classified_items = []

        for item in knowledge_items:
            content = item.get('content', '')
            metadata = item.get('metadata', {})

            classified = await self.classify_knowledge(content, metadata)
            classified_items.append(classified)

        logger.info(f"批量分类完成: {len(classified_items)} 条知识")
        return classified_items

    # ========== 类别确定方法 ==========

    async def _determine_primary_category(
        self,
        content_lower: str,
        metadata: Optional[Dict[str, Any]]
    ) -> tuple[KnowledgeCategory, float]:
        """确定主要类别"""
        category_scores = {}

        # 基于关键词评分
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = 0.0
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    score += 1.0

            # 归一化分数
            if keywords:
                score = score / len(keywords)

            category_scores[category] = score

        # 基于元数据调整
        if metadata:
            category_scores = self._adjust_scores_by_metadata(
                category_scores, metadata
            )

        # 应用自定义规则
        category_scores = self._apply_custom_rules(
            category_scores, content_lower, metadata
        )

        # 找出最高分类别
        if category_scores:
            primary_category = max(category_scores, key=category_scores.get)
            confidence = category_scores[primary_category]

            # 确保置信度不低于阈值
            if confidence < self.min_category_confidence:
                confidence = self.min_category_confidence

            return primary_category, min(confidence, 1.0)

        # 默认类别
        return KnowledgeCategory.MARKET_ANALYSIS, 0.5

    async def _determine_secondary_categories(
        self,
        content_lower: str,
        metadata: Optional[Dict[str, Any]],
        primary_category: KnowledgeCategory
    ) -> List[KnowledgeCategory]:
        """确定次要类别"""
        category_scores = {}

        # 计算所有类别分数
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if category == primary_category:
                continue

            score = 0.0
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    score += 1.0

            if keywords:
                score = score / len(keywords)

            if score >= self.min_category_confidence:
                category_scores[category] = score

        # 按分数排序
        sorted_categories = sorted(
            category_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # 取前N个次要类别
        secondary_categories = [
            cat for cat, score in sorted_categories[:self.max_secondary_categories]
        ]

        return secondary_categories

    def _adjust_scores_by_metadata(
        self,
        category_scores: Dict[KnowledgeCategory, float],
        metadata: Dict[str, Any]
    ) -> Dict[KnowledgeCategory, float]:
        """基于元数据调整分数"""
        # 根据元数据中的特定字段调整分数
        if 'strategy' in metadata:
            category_scores[KnowledgeCategory.STRATEGY] += 0.3

        if 'risk_level' in metadata:
            category_scores[KnowledgeCategory.RISK_MANAGEMENT] += 0.3

        if 'execution_time' in metadata or 'slippage' in metadata:
            category_scores[KnowledgeCategory.EXECUTION] += 0.2

        if 'profit' in metadata or 'profit_rate' in metadata:
            category_scores[KnowledgeCategory.PERFORMANCE] += 0.3

        if 'volatility' in metadata or 'trend' in metadata:
            category_scores[KnowledgeCategory.MARKET_ANALYSIS] += 0.2

        return category_scores

    def _apply_custom_rules(
        self,
        category_scores: Dict[KnowledgeCategory, float],
        content_lower: str,
        metadata: Optional[Dict[str, Any]]
    ) -> Dict[KnowledgeCategory, float]:
        """应用自定义规则"""
        for rule_name, rule_config in self.custom_category_rules.items():
            # 检查规则条件
            conditions = rule_config.get('conditions', {})
            matches = True

            for key, value in conditions.items():
                if key == 'keywords':
                    if not any(kw in content_lower for kw in value):
                        matches = False
                        break
                elif key == 'metadata':
                    if metadata and isinstance(value, dict):
                        for mk, mv in value.items():
                            if metadata.get(mk) != mv:
                                matches = False
                                break

            # 应用规则
            if matches:
                target_category = KnowledgeCategory(rule_config['target_category'])
                boost = rule_config.get('boost', 0.2)
                category_scores[target_category] = category_scores.get(
                    target_category, 0.0
                ) + boost

        return category_scores

    # ========== 标签生成方法 ==========

    async def _auto_generate_tags(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]],
        primary_category: KnowledgeCategory
    ) -> List[KnowledgeTag]:
        """自动生成标签"""
        tags = []
        content_lower = content.lower()

        # 1. 内容基础标签
        content_tags = self._generate_content_based_tags(
            content_lower, primary_category
        )
        tags.extend(content_tags)

        # 2. 上下文标签
        if metadata:
            context_tags = self._generate_context_based_tags(metadata)
            tags.extend(context_tags)

        # 3. 符号特定标签
        symbol_tags = self._generate_symbol_tags(metadata)
        tags.extend(symbol_tags)

        # 4. 策略特定标签
        strategy_tags = self._generate_strategy_tags(metadata)
        tags.extend(strategy_tags)

        # 5. 风险等级标签
        risk_tags = self._generate_risk_tags(metadata)
        tags.extend(risk_tags)

        # 6. 置信度等级标签
        confidence_tags = self._generate_confidence_tags(metadata)
        tags.extend(confidence_tags)

        # 限制标签数量
        tags = sorted(
            tags,
            key=lambda t: t.confidence,
            reverse=True
        )[:self.max_tags_per_item]

        # 过滤低置信度标签
        tags = [
            tag for tag in tags
            if tag.confidence >= self.min_tag_confidence
        ]

        return tags

    def _generate_content_based_tags(
        self,
        content_lower: str,
        primary_category: KnowledgeCategory
    ) -> List[KnowledgeTag]:
        """生成内容基础标签"""
        tags = []

        # 基于类别生成标签
        if primary_category == KnowledgeCategory.STRATEGY:
            if "套利" in content_lower or "arbitrage" in content_lower:
                tags.append(KnowledgeTag(
                    name="套利策略",
                    tag_type=TagType.CONTENT_BASED,
                    confidence=0.9
                ))
            if "三角" in content_lower or "triangular" in content_lower:
                tags.append(KnowledgeTag(
                    name="三角套利",
                    tag_type=TagType.CONTENT_BASED,
                    confidence=0.85
                ))

        elif primary_category == KnowledgeCategory.RISK_MANAGEMENT:
            if "止损" in content_lower or "stop_loss" in content_lower:
                tags.append(KnowledgeTag(
                    name="止损策略",
                    tag_type=TagType.CONTENT_BASED,
                    confidence=0.9
                ))
            if "仓位" in content_lower or "position" in content_lower:
                tags.append(KnowledgeTag(
                    name="仓位管理",
                    tag_type=TagType.CONTENT_BASED,
                    confidence=0.85
                ))

        elif primary_category == KnowledgeCategory.MARKET_ANALYSIS:
            if "趋势" in content_lower or "trend" in content_lower:
                tags.append(KnowledgeTag(
                    name="趋势分析",
                    tag_type=TagType.CONTENT_BASED,
                    confidence=0.9
                ))
            if "波动" in content_lower or "volatility" in content_lower:
                tags.append(KnowledgeTag(
                    name="波动性分析",
                    tag_type=TagType.CONTENT_BASED,
                    confidence=0.85
                ))

        # 通用标签
        if "优化" in content_lower or "optimization" in content_lower:
            tags.append(KnowledgeTag(
                name="优化建议",
                tag_type=TagType.CONTENT_BASED,
                confidence=0.8
            ))

        return tags

    def _generate_context_based_tags(
        self,
        metadata: Dict[str, Any]
    ) -> List[KnowledgeTag]:
        """生成上下文基础标签"""
        tags = []

        if metadata.get('source'):
            tags.append(KnowledgeTag(
                name=f"来源:{metadata['source']}",
                tag_type=TagType.CONTEXT_BASED,
                confidence=0.95
            ))

        if metadata.get('exchange'):
            tags.append(KnowledgeTag(
                name=f"交易所:{metadata['exchange']}",
                tag_type=TagType.CONTEXT_BASED,
                confidence=0.9
            ))

        return tags

    def _generate_symbol_tags(
        self,
        metadata: Optional[Dict[str, Any]]
    ) -> List[KnowledgeTag]:
        """生成符号特定标签"""
        tags = []

        if metadata:
            symbol = metadata.get('symbol')
            if symbol:
                tags.append(KnowledgeTag(
                    name=f"交易对:{symbol}",
                    tag_type=TagType.SYMBOL_SPECIFIC,
                    confidence=0.95
                ))

            symbols = metadata.get('symbols', [])
            if symbols and isinstance(symbols, list):
                for sym in symbols[:2]:  # 最多2个符号
                    tags.append(KnowledgeTag(
                        name=f"交易对:{sym}",
                        tag_type=TagType.SYMBOL_SPECIFIC,
                        confidence=0.9
                    ))

        return tags

    def _generate_strategy_tags(
        self,
        metadata: Optional[Dict[str, Any]]
    ) -> List[KnowledgeTag]:
        """生成策略特定标签"""
        tags = []

        if metadata:
            strategy = metadata.get('strategy')
            if strategy:
                tags.append(KnowledgeTag(
                    name=f"策略:{strategy}",
                    tag_type=TagType.STRATEGY_SPECIFIC,
                    confidence=0.9
                ))

            decision_type = metadata.get('decision_type')
            if decision_type:
                tags.append(KnowledgeTag(
                    name=f"决策:{decision_type}",
                    tag_type=TagType.STRATEGY_SPECIFIC,
                    confidence=0.85
                ))

        return tags

    def _generate_risk_tags(
        self,
        metadata: Optional[Dict[str, Any]]
    ) -> List[KnowledgeTag]:
        """生成风险等级标签"""
        tags = []

        if metadata:
            risk_level = metadata.get('risk_level')
            if risk_level:
                tags.append(KnowledgeTag(
                    name=f"风险等级:{risk_level}",
                    tag_type=TagType.RISK_LEVEL,
                    confidence=0.9
                ))

            max_drawdown = metadata.get('max_drawdown')
            if max_drawdown:
                if max_drawdown > 2.0:
                    tags.append(KnowledgeTag(
                        name="高风险",
                        tag_type=TagType.RISK_LEVEL,
                        confidence=0.85
                    ))
                elif max_drawdown < 1.0:
                    tags.append(KnowledgeTag(
                        name="低风险",
                        tag_type=TagType.RISK_LEVEL,
                        confidence=0.8
                    ))

        return tags

    def _generate_confidence_tags(
        self,
        metadata: Optional[Dict[str, Any]]
    ) -> List[KnowledgeTag]:
        """生成置信度等级标签"""
        tags = []

        if metadata:
            confidence = metadata.get('confidence')
            if confidence is not None:
                if confidence >= 0.8:
                    tags.append(KnowledgeTag(
                        name="高置信度",
                        tag_type=TagType.CONFIDENCE_LEVEL,
                        confidence=0.9
                    ))
                elif confidence >= 0.6:
                    tags.append(KnowledgeTag(
                        name="中置信度",
                        tag_type=TagType.CONFIDENCE_LEVEL,
                        confidence=0.85
                    ))
                else:
                    tags.append(KnowledgeTag(
                        name="低置信度",
                        tag_type=TagType.CONFIDENCE_LEVEL,
                        confidence=0.8
                    ))

        return tags

    # ========== 辅助方法 ==========

    def _calculate_overall_confidence(
        self,
        primary_confidence: float,
        secondary_categories: List[KnowledgeCategory],
        tags: List[KnowledgeTag]
    ) -> float:
        """计算整体置信度"""
        # 基础置信度来自主要类别
        confidence = primary_confidence * 0.6

        # 次要类别贡献
        if secondary_categories:
            confidence += 0.2 * (len(secondary_categories) / self.max_secondary_categories)

        # 标签贡献
        if tags:
            avg_tag_confidence = sum(t.confidence for t in tags) / len(tags)
            confidence += avg_tag_confidence * 0.2

        return min(confidence, 1.0)

    def _update_classification_stats(self, classified: ClassifiedKnowledge):
        """更新分类统计"""
        # 类别统计
        self.category_stats[classified.primary_category] += 1

        for category in classified.secondary_categories:
            self.category_stats[category] += 1

        # 标签统计
        for tag in classified.tags:
            self.tag_stats[tag.name] += 1

    # ========== 类别优化方法 ==========

    async def optimize_categories(
        self,
        min_usage_count: int = 10
    ) -> Dict[str, Any]:
        """优化类别系统

        Args:
            min_usage_count: 最小使用次数

        Returns:
            优化建议
        """
        optimization_suggestions = []

        # 识别低使用率类别
        low_usage_categories = [
            cat.value for cat, count in self.category_stats.items()
            if count < min_usage_count
        ]

        if low_usage_categories:
            optimization_suggestions.append({
                "type": "low_usage_categories",
                "categories": low_usage_categories,
                "suggestion": "考虑合并或重新定义这些类别"
            })

        # 识别高频标签
        high_frequency_tags = [
            tag for tag, count in self.tag_stats.items()
            if count > 100
        ]

        if high_frequency_tags:
            optimization_suggestions.append({
                "type": "high_frequency_tags",
                "tags": high_frequency_tags[:10],
                "suggestion": "这些标签使用频繁，可考虑作为子类别"
            })

        # 类别平衡分析
        total_classifications = sum(self.category_stats.values())
        category_distribution = {
            cat.value: count / total_classifications
            for cat, count in self.category_stats.items()
        }

        optimization_suggestions.append({
            "type": "category_distribution",
            "distribution": category_distribution,
            "suggestion": "分析类别分布是否均衡"
        })

        return {
            "optimization_suggestions": optimization_suggestions,
            "category_stats": dict(self.category_stats),
            "tag_stats": dict(self.tag_stats)
        }

    # ========== 统计和工具方法 ==========

    def get_classification_stats(self) -> Dict[str, Any]:
        """获取分类统计"""
        return {
            "category_stats": dict(self.category_stats),
            "tag_stats": dict(self.tag_stats),
            "total_classifications": sum(self.category_stats.values()),
            "total_tags": sum(self.tag_stats.values())
        }

    def get_popular_categories(self, top_n: int = 5) -> List[tuple[str, int]]:
        """获取热门类别"""
        sorted_categories = sorted(
            self.category_stats.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return [(cat.value, count) for cat, count in sorted_categories[:top_n]]

    def get_popular_tags(self, top_n: int = 10) -> List[tuple[str, int]]:
        """获取热门标签"""
        sorted_tags = sorted(
            self.tag_stats.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_tags[:top_n]

    def reset_stats(self):
        """重置统计"""
        self.category_stats.clear()
        self.tag_stats.clear()
        logger.info("分类统计已重置")


def create_intelligent_knowledge_classifier(
    config: Dict[str, Any]
) -> IntelligentKnowledgeClassifier:
    """创建智能知识分类器实例

    Args:
        config: 配置字典

    Returns:
        智能知识分类器实例
    """
    return IntelligentKnowledgeClassifier(config)
