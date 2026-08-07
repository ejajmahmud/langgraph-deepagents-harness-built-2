"""Memo0智能知识管理器 - V5.10 Phase 3 (真正的memo0集成)

整合AutoKnowledgeExtractor、IntelligentKnowledgeClassifier、
KnowledgeQualityOptimizer和KnowledgeTrendAnalyzer，
提供统一的智能知识管理接口。

核心改进：
1. 使用真正的memo0存储（持久化+向量搜索）
2. 支持KnowledgeStorage抽象接口
3. 自动降级到内存存储（如果memo0不可用）
4. 完整的知识生命周期管理

核心功能：
1. 统一的知识提取和导入
2. 智能分类和标签管理
3. 质量评估和自动优化
4. 趋势分析和热点识别
5. 完整的知识生命周期管理

基于：V5.10架构设计 + V5.10 Phase 3 memo0集成
创建时间：2026-04-19
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from storage.knowledge_storage_interface import (
    KnowledgeStorage,
    KnowledgeItem,
    SearchResult,
    StorageStats,
    create_knowledge_storage
)
from storage.modules.auto_knowledge_extractor import (
    AutoKnowledgeExtractor,
    ExtractedKnowledge,
    ExtractionResult,
    KnowledgeSource,
    create_auto_knowledge_extractor
)
from storage.modules.intelligent_knowledge_classifier import (
    IntelligentKnowledgeClassifier,
    ClassifiedKnowledge,
    KnowledgeCategory,
    create_intelligent_knowledge_classifier
)
from storage.modules.knowledge_quality_optimizer import (
    KnowledgeQualityOptimizer,
    QualityScore,
    OptimizedKnowledge,
    KnowledgeQualityReport,
    create_knowledge_quality_optimizer
)
from storage.modules.knowledge_trend_analyzer import (
    KnowledgeTrendAnalyzer,
    TrendAnalysis,
    HotKnowledge,
    TrendReport,
    create_knowledge_trend_analyzer
)

logger = logging.getLogger(__name__)


@dataclass
class ManagedKnowledge:
    """管理的知识条目"""
    knowledge_id: str
    content: str
    category: str
    tags: List[str]
    quality_score: float
    quality_level: str
    value_score: float
    value_tier: str
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    access_count: int = 0
    last_accessed: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "knowledge_id": self.knowledge_id,
            "content": self.content,
            "category": self.category,
            "tags": self.tags,
            "quality_score": self.quality_score,
            "quality_level": self.quality_level,
            "value_score": self.value_score,
            "value_tier": self.value_tier,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None
        }

    @classmethod
    def from_knowledge_item(
        cls,
        item: KnowledgeItem,
        category: str = "",
        tags: List[str] = None
    ) -> 'ManagedKnowledge':
        """从KnowledgeItem创建"""
        return cls(
            knowledge_id=item.knowledge_id,
            content=item.content,
            category=category or item.metadata.get('category', ''),
            tags=tags or item.metadata.get('tags', []),
            quality_score=item.quality_score,
            quality_level=_quality_score_to_level(item.quality_score),
            value_score=item.value_score,
            value_tier=_value_score_to_tier(item.value_score),
            metadata={k: v for k, v in item.metadata.items()
                      if k not in ['category', 'tags']},
            created_at=item.created_at,
            updated_at=item.updated_at
        )


def _quality_score_to_level(score: float) -> str:
    """质量分数转等级"""
    if score >= 0.9:
        return "excellent"
    elif score >= 0.7:
        return "good"
    elif score >= 0.5:
        return "acceptable"
    else:
        return "poor"


def _value_score_to_tier(score: float) -> str:
    """价值分数转层级"""
    if score >= 0.8:
        return "tier_1"
    elif score >= 0.6:
        return "tier_2"
    elif score >= 0.4:
        return "tier_3"
    else:
        return "tier_4"


class Memo0IntelligentKnowledgeManagerV2:
    """Memo0智能知识管理器 V2 (真正的memo0集成)

    整合所有智能知识管理功能，提供统一接口。
    支持真正的memo0持久化存储和向量搜索。
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化智能知识管理器

        Args:
            config: 配置字典
                - storage_type: 存储类型 [memo0, memory]
                - storage_config: 存储配置
                - auto_knowledge_extractor: 提取器配置
                - intelligent_knowledge_classifier: 分类器配置
                - knowledge_quality_optimizer: 优化器配置
                - knowledge_trend_analyzer: 分析器配置
        """
        self.config = config

        # 初始化存储
        self.storage_type = config.get('storage_type', 'memory')
        storage_config = config.get('storage_config', {})

        try:
            # 尝试创建memo0存储
            if self.storage_type == 'memo0':
                logger.info("尝试初始化Memo0存储...")
                self.storage = create_knowledge_storage('memo0', storage_config)
            else:
                logger.info("使用内存存储...")
                self.storage = create_knowledge_storage('memory', storage_config)

        except Exception as e:
            logger.warning(f"Memo0存储初始化失败，降级到内存存储: {e}")
            self.storage_type = 'memory'
            self.storage = create_knowledge_storage('memory', storage_config)

        # 初始化各个模块
        self.extractor = create_auto_knowledge_extractor(
            config.get('auto_knowledge_extractor', {})
        )

        self.classifier = create_intelligent_knowledge_classifier(
            config.get('intelligent_knowledge_classifier', {})
        )

        self.quality_optimizer = create_knowledge_quality_optimizer(
            config.get('knowledge_quality_optimizer', {})
        )

        self.trend_analyzer = create_knowledge_trend_analyzer(
            config.get('knowledge_trend_analyzer', {})
        )

        # 本地缓存（用于访问计数等）
        self._access_cache: Dict[str, int] = {}
        self._last_access_cache: Dict[str, datetime] = {}

        # 统计信息
        self.manager_stats = {
            "total_knowledge": 0,
            "total_extractions": 0,
            "total_classifications": 0,
            "total_quality_assessments": 0,
            "total_optimizations": 0,
            "total_trend_analyses": 0,
            "storage_type": self.storage_type
        }

        logger.info(f"✅ Memo0智能知识管理器V2初始化完成 (存储: {self.storage_type})")

    async def initialize(self) -> None:
        """初始化管理器"""
        await self.storage.initialize()

        # 加载现有知识
        self.manager_stats["total_knowledge"] = await self.storage.count_knowledge()

        logger.info("智能知识管理器初始化完成")

    # ========== 核心管理方法 ==========

    async def import_from_trade_data(
        self,
        trade_data: Dict[str, Any]
    ) -> List[ManagedKnowledge]:
        """从交易数据导入知识

        Args:
            trade_data: 交易数据

        Returns:
            导入的知识列表
        """
        # 提取知识
        extraction_result = await self.extractor.extract_from_trade(trade_data)

        if not extraction_result.success:
            logger.warning(f"从交易数据提取知识失败: {extraction_result.error_message}")
            return []

        # 处理提取的知识
        imported_knowledge = []
        for extracted in extraction_result.knowledge_items:
            managed = await self._process_extracted_knowledge(extracted)
            if managed:
                imported_knowledge.append(managed)

        self.manager_stats["total_extractions"] += 1
        logger.info(f"从交易数据导入 {len(imported_knowledge)} 条知识")

        return imported_knowledge

    async def import_from_market_data(
        self,
        market_data: Dict[str, Any]
    ) -> List[ManagedKnowledge]:
        """从市场数据导入知识

        Args:
            market_data: 市场数据

        Returns:
            导入的知识列表
        """
        # 提取知识
        extraction_result = await self.extractor.extract_from_market(market_data)

        if not extraction_result.success:
            logger.warning(f"从市场数据提取知识失败: {extraction_result.error_message}")
            return []

        # 处理提取的知识
        imported_knowledge = []
        for extracted in extraction_result.knowledge_items:
            managed = await self._process_extracted_knowledge(extracted)
            if managed:
                imported_knowledge.append(managed)

        self.manager_stats["total_extractions"] += 1
        logger.info(f"从市场数据导入 {len(imported_knowledge)} 条知识")

        return imported_knowledge

    async def import_from_decision_data(
        self,
        decision_data: Dict[str, Any]
    ) -> List[ManagedKnowledge]:
        """从决策数据导入知识

        Args:
            decision_data: 决策数据

        Returns:
            导入的知识列表
        """
        # 提取知识
        extraction_result = await self.extractor.extract_from_decision(decision_data)

        if not extraction_result.success:
            logger.warning(f"从决策数据提取知识失败: {extraction_result.error_message}")
            return []

        # 处理提取的知识
        imported_knowledge = []
        for extracted in extraction_result.knowledge_items:
            managed = await self._process_extracted_knowledge(extracted)
            if managed:
                imported_knowledge.append(managed)

        self.manager_stats["total_extractions"] += 1
        logger.info(f"从决策数据导入 {len(imported_knowledge)} 条知识")

        return imported_knowledge

    async def add_custom_knowledge(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ManagedKnowledge:
        """添加自定义知识

        Args:
            content: 知识内容
            metadata: 元数据

        Returns:
            管理的知识条目
        """
        # 创建提取的知识对象
        category = metadata.get('category') if metadata else None
        if isinstance(category, str):
            try:
                category = KnowledgeCategory(category)
            except ValueError:
                category = KnowledgeCategory.MARKET_ANALYSIS
        else:
            category = KnowledgeCategory.MARKET_ANALYSIS

        extracted = ExtractedKnowledge(
            content=content,
            category=category,
            source=KnowledgeSource.USER_INPUT,
            confidence=1.0,
            metadata=metadata or {}
        )

        managed = await self._process_extracted_knowledge(extracted)
        if managed:
            logger.info(f"添加自定义知识: {managed.knowledge_id}")

        return managed

    # ========== 知识处理流水线 ==========

    async def _process_extracted_knowledge(
        self,
        extracted: ExtractedKnowledge
    ) -> Optional[ManagedKnowledge]:
        """处理提取的知识（完整流水线）"""
        try:
            # 1. 分类
            classified = await self.classifier.classify_knowledge(
                extracted.content,
                extracted.metadata
            )

            # 2. 质量评估
            quality_score = await self.quality_optimizer.calculate_quality_score(
                extracted.content,
                extracted.metadata
            )

            # 3. 价值评估
            value_assessment = await self.trend_analyzer.assess_knowledge_value(
                extracted.content  # 使用内容作为临时ID
            )

            # 4. 准备元数据
            # 优先使用metadata中的category，如果没有才使用分类结果
            category = extracted.metadata.get('category') or classified.primary_category.value
            enhanced_metadata = {
                **extracted.metadata,
                'category': category,
                'tags': [tag.name for tag in classified.tags],
                'quality_score': quality_score.overall_score,
                'quality_level': quality_score.quality_level.value,
                'value_score': value_assessment.value_score,
                'value_tier': value_assessment.value_tier.value
            }

            # 5. 添加到存储
            knowledge_id = await self.storage.add_knowledge(
                extracted.content,
                enhanced_metadata
            )

            # 6. 创建管理的知识
            managed = ManagedKnowledge(
                knowledge_id=knowledge_id,
                content=extracted.content,
                category=category,  # 使用正确的category
                tags=[tag.name for tag in classified.tags],
                quality_score=quality_score.overall_score,
                quality_level=quality_score.quality_level.value,
                value_score=value_assessment.value_score,
                value_tier=value_assessment.value_tier.value,
                metadata={**extracted.metadata, **classified.metadata},
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            # 7. 记录访问（用于趋势分析）
            await self.trend_analyzer.record_access(
                knowledge_id,
                extracted.content,
                extracted.metadata
            )

            # 更新统计
            self.manager_stats["total_knowledge"] += 1
            self.manager_stats["total_classifications"] += 1
            self.manager_stats["total_quality_assessments"] += 1

            return managed

        except Exception as e:
            logger.error(f"处理提取的知识失败: {e}")
            return None

    # ========== 知识查询和检索 ==========

    async def search_knowledge(
        self,
        query: str,
        category: Optional[str] = None,
        min_quality: float = 0.5,
        limit: int = 10
    ) -> List[ManagedKnowledge]:
        """搜索知识

        Args:
            query: 查询内容
            category: 类别过滤
            min_quality: 最低质量分数
            limit: 返回数量限制

        Returns:
            匹配的知识列表
        """
        # 准备过滤条件
        filters = {}
        if category:
            filters['category'] = category

        # 使用语义搜索
        search_results = await self.storage.semantic_search(
            query=query,
            top_k=limit,
            filters=filters if filters else None
        )

        # 转换并过滤
        managed_results = []
        for result in search_results:
            # 质量过滤
            if result.quality_score < min_quality:
                continue

            # 从存储获取完整的KnowledgeItem
            item = await self.storage.get_knowledge(result.knowledge_id)
            if not item:
                continue

            # 转换为ManagedKnowledge
            managed = ManagedKnowledge.from_knowledge_item(
                item,
                category=result.metadata.get('category', ''),
                tags=result.metadata.get('tags', [])
            )

            managed_results.append(managed)

            # 记录访问
            await self._record_knowledge_access(result.knowledge_id)

        return managed_results

    async def get_knowledge_by_id(
        self,
        knowledge_id: str
    ) -> Optional[ManagedKnowledge]:
        """根据ID获取知识

        Args:
            knowledge_id: 知识ID

        Returns:
            知识条目或None
        """
        # 从存储获取
        item = await self.storage.get_knowledge(knowledge_id)

        if not item:
            return None

        # 转换为ManagedKnowledge
        managed = ManagedKnowledge.from_knowledge_item(
            item,
            category=item.metadata.get('category', ''),
            tags=item.metadata.get('tags', [])
        )

        # 记录访问
        await self._record_knowledge_access(knowledge_id)

        return managed

    async def get_knowledge_by_category(
        self,
        category: str,
        limit: int = 20
    ) -> List[ManagedKnowledge]:
        """根据类别获取知识

        Args:
            category: 类别
            limit: 返回数量限制

        Returns:
            知识列表
        """
        # 使用元数据搜索
        items = await self.storage.search_by_metadata(
            filters={'category': category},
            limit=limit
        )

        # 转换为ManagedKnowledge
        managed_list = [
            ManagedKnowledge.from_knowledge_item(
                item,
                category=item.metadata.get('category', ''),
                tags=item.metadata.get('tags', [])
            )
            for item in items
        ]

        # 记录访问
        for knowledge in managed_list:
            await self._record_knowledge_access(knowledge.knowledge_id)

        return managed_list

    # ========== 知识优化和维护 ==========

    async def optimize_all_knowledge(self) -> Dict[str, Any]:
        """优化所有知识

        Returns:
            优化结果
        """
        optimization_results = {
            "total_knowledge": 0,
            "optimized_count": 0,
            "improvements": []
        }

        # 获取所有知识
        all_items = await self.storage.list_knowledge(limit=100000)
        optimization_results["total_knowledge"] = len(all_items)

        # 逐个优化
        for item in all_items:
            try:
                # 尝试优化
                optimized = await self.quality_optimizer.optimize_knowledge(
                    item.content,
                    item.metadata
                )

                if optimized.quality_improvement > 0:
                    # 更新知识
                    await self.storage.update_knowledge(
                        item.knowledge_id,
                        content=optimized.optimized_content,
                        metadata={
                            **item.metadata,
                            'quality_score': optimized.quality_improvement
                        }
                    )

                    optimization_results["optimized_count"] += 1
                    optimization_results["improvements"].append({
                        "knowledge_id": item.knowledge_id,
                        "improvement": optimized.quality_improvement,
                        "actions": optimized.optimization_actions
                    })

                    self.manager_stats["total_optimizations"] += 1

            except Exception as e:
                logger.error(f"优化知识 {item.knowledge_id} 失败: {e}")

        logger.info(f"知识优化完成: {optimization_results['optimized_count']} 条优化")
        return optimization_results

    async def clean_low_quality_knowledge(self) -> Dict[str, Any]:
        """清理低质量知识

        Returns:
            清理结果
        """
        # 获取所有知识
        all_items = await self.storage.list_knowledge(limit=100000)

        low_quality_ids = [
            item.knowledge_id
            for item in all_items
            if item.quality_score < 0.5
        ]

        # 删除低质量知识
        for knowledge_id in low_quality_ids:
            await self.storage.delete_knowledge(knowledge_id)

        logger.info(f"清理低质量知识: 移除 {len(low_quality_ids)} 条")

        return {
            "removed_count": len(low_quality_ids),
            "removed_ids": low_quality_ids
        }

    # ========== 趋势分析和报告 ==========

    async def generate_comprehensive_report(self) -> Dict[str, Any]:
        """生成综合报告

        Returns:
            综合报告
        """
        # 趋势报告
        trend_report = await self.trend_analyzer.generate_trend_report()

        # 质量报告
        all_items = await self.storage.list_knowledge(limit=100000)
        quality_report = await self.quality_optimizer.generate_quality_report(
            [
                {
                    "content": item.content,
                    "metadata": item.metadata,
                    "created_at": item.created_at
                }
                for item in all_items
            ]
        )

        # 分类统计
        classification_stats = self.classifier.get_classification_stats()

        # 提取统计
        extraction_stats = self.extractor.get_extraction_stats()

        # 存储统计
        storage_stats = self.storage.get_storage_stats()

        # 综合报告
        comprehensive_report = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_knowledge": storage_stats.total_knowledge,
                "average_quality": quality_report.average_quality_score,
                "hot_knowledge_count": len(trend_report.hot_knowledge),
                "manager_stats": self.manager_stats,
                "storage_type": self.storage_type
            },
            "trend_analysis": trend_report.to_dict(),
            "quality_analysis": quality_report.to_dict(),
            "classification_stats": classification_stats,
            "extraction_stats": extraction_stats,
            "storage_stats": storage_stats.to_dict()
        }

        return comprehensive_report

    async def get_hot_knowledge(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取热点知识

        Args:
            limit: 返回数量限制

        Returns:
            热点知识列表
        """
        hot_knowledge_objs = await self.trend_analyzer.identify_hot_knowledge(limit)

        result = []
        for hot_knowledge in hot_knowledge_objs:
            # 从存储获取知识
            item = await self.storage.get_knowledge(hot_knowledge.knowledge_id)

            if item:
                result.append({
                    **item.to_dict(),
                    "hot_score": hot_knowledge.hot_score,
                    "recent_activity": hot_knowledge.recent_activity
                })

        return result

    # ========== 工具方法 ==========

    async def _record_knowledge_access(self, knowledge_id: str):
        """记录知识访问"""
        self._access_cache[knowledge_id] = self._access_cache.get(knowledge_id, 0) + 1
        self._last_access_cache[knowledge_id] = datetime.now()

    async def get_manager_stats(self) -> Dict[str, Any]:
        """获取管理器统计"""
        return {
            **self.manager_stats,
            "current_knowledge_count": await self.storage.count_knowledge(),
            "storage_stats": self.storage.get_storage_stats().to_dict(),
            "module_stats": {
                "extractor": self.extractor.get_extraction_stats(),
                "classifier": self.classifier.get_classification_stats(),
                "quality_optimizer": self.quality_optimizer.get_quality_stats(),
                "trend_analyzer": self.trend_analyzer.get_trend_stats()
            }
        }

    def reset_all_stats(self):
        """重置所有统计"""
        self.manager_stats = {
            "total_knowledge": 0,
            "total_extractions": 0,
            "total_classifications": 0,
            "total_quality_assessments": 0,
            "total_optimizations": 0,
            "total_trend_analyses": 0,
            "storage_type": self.storage_type
        }

        self.extractor.reset_stats()
        self.classifier.reset_stats()
        self.quality_optimizer.reset_stats()
        self.trend_analyzer.reset_stats()

        logger.info("所有统计已重置")

    async def close(self) -> None:
        """关闭管理器"""
        await self.storage.close()
        logger.info("智能知识管理器已关闭")


def create_memo0_intelligent_knowledge_manager_v2(
    config: Dict[str, Any]
) -> Memo0IntelligentKnowledgeManagerV2:
    """创建Memo0智能知识管理器V2实例

    Args:
        config: 配置字典

    Returns:
        智能知识管理器实例
    """
    return Memo0IntelligentKnowledgeManagerV2(config)
