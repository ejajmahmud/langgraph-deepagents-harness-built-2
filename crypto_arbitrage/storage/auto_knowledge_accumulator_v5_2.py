"""自动知识积累器 V5.2 - 智能学习循环版

基于Memo0深度集成的智能知识积累和学习循环系统。

V5.2核心升级：
1. 深度集成Memo0语义搜索和知识关联
2. 实现知识质量自动评估和验证
3. 增强知识有效性学习和淘汰机制
4. 优化知识图谱动态构建能力
5. 实现智能知识推荐和关联推理
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class KnowledgeQuality(Enum):
    """知识质量等级"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    INVALID = "invalid"


@dataclass
class KnowledgeEntry:
    """知识条目（V5.2增强版）"""
    content: str
    metadata: Dict[str, Any]
    quality_score: float = 0.0
    quality_level: KnowledgeQuality = KnowledgeQuality.ACCEPTABLE
    validation_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    last_validated: float = 0.0
    created_at: float = field(default_factory=datetime.now().timestamp)
    updated_at: float = field(default_factory=datetime.now().timestamp)
    embeddings: Optional[List[float]] = None


@dataclass
class KnowledgeRelation:
    """知识关联"""
    source_id: str
    target_id: str
    relation_type: str  # similar, causal, complementary, contradictory
    confidence: float
    created_at: float = field(default_factory=datetime.now().timestamp)


class AutoKnowledgeAccumulatorV52:
    """自动知识积累器 V5.2 - 智能学习循环版

    基于Memo0深度集成的智能知识积累和学习循环。
    """

    def __init__(self, mem0_storage, fallback_storage=None):
        """初始化V5.2自动知识积累器

        Args:
            mem0_storage: Memo0存储实例（必须）
            fallback_storage: 降级存储实例（可选）
        """
        self.mem0_storage = mem0_storage
        self.fallback_storage = fallback_storage

        # 知识缓存
        self._knowledge_cache: Dict[str, KnowledgeEntry] = {}
        self._relation_cache: List[KnowledgeRelation] = []

        # V5.3: 缓存大小限制，防止内存泄漏
        self._max_relation_cache_size = 10000  # 最大缓存10000个关系
        self._relation_cache_hits: Dict[str, int] = {}  # 关系使用频率统计

        # 质量评估模型参数
        self.quality_thresholds = {
            KnowledgeQuality.EXCELLENT: 0.85,
            KnowledgeQuality.GOOD: 0.70,
            KnowledgeQuality.ACCEPTABLE: 0.50,
            KnowledgeQuality.POOR: 0.30
        }

        # 学习统计
        self.learning_stats = {
            "total_knowledge_added": 0,
            "total_knowledge_validated": 0,
            "total_relations_built": 0,
            "total_knowledge_retired": 0,
            "quality_improvements": 0
        }

        # 检查Memo0可用性
        self._mem0_available = self._check_mem0_available()

        if self._mem0_available:
            logger.info("[OK] V5.2 自动知识积累器初始化成功 (Memo0智能学习循环)")
        else:
            logger.warning("[WARNING] V5.2 自动知识积累器运行在降级模式")
            if fallback_storage:
                logger.info("[OK] 降级存储已配置")

    def _check_mem0_available(self) -> bool:
        """检查Memo0是否可用"""
        if self.mem0_storage is None:
            return False

        try:
            if hasattr(self.mem0_storage, 'add_knowledge'):
                return True
            return False
        except Exception as e:
            logger.warning(f"Memo0可用性检查失败: {e}")
            return False

    # ---------------------- 知识添加和质量评估 ----------------------

    async def add_knowledge(
        self,
        content: str,
        metadata: Dict[str, Any],
        validate_quality: bool = True
    ) -> str:
        """添加知识条目（V5.2增强版 + V5.3内存管理）

        Args:
            content: 知识内容
            metadata: 元数据
            validate_quality: 是否验证质量

        Returns:
            知识ID
        """
        self.learning_stats["total_knowledge_added"] += 1

        # V5.3: 定期执行知识清理，防止内存泄漏
        if len(self._knowledge_cache) > 5000:
            retired = self._prune_low_quality_knowledges()
            if retired > 0:
                logger.info(f"🧹 自动清理: 淘汰 {retired} 个低质量知识")

        # 构建知识条目
        knowledge_id = self._generate_knowledge_id(content, metadata)

        # 质量评估
        if validate_quality:
            quality_score, quality_level = await self._assess_knowledge_quality(
                content, metadata
            )
        else:
            quality_score = 0.5
            quality_level = KnowledgeQuality.ACCEPTABLE

        # 创建知识条目
        knowledge_entry = KnowledgeEntry(
            content=content,
            metadata=metadata,
            quality_score=quality_score,
            quality_level=quality_level,
            created_at=datetime.now().timestamp(),
            updated_at=datetime.now().timestamp()
        )

        # 添加到Memo0
        if self._mem0_available:
            try:
                await self.mem0_storage.add_knowledge({
                    "content": content,
                    "metadata": {
                        **metadata,
                        "quality_score": quality_score,
                        "quality_level": quality_level.value,
                        "knowledge_id": knowledge_id,
                        "created_at": datetime.now().isoformat()
                    }
                })

                # 缓存知识条目
                self._knowledge_cache[knowledge_id] = knowledge_entry

                logger.info(f"[OK] 知识已添加: {knowledge_id} (质量: {quality_level.value})")
                return knowledge_id

            except Exception as e:
                logger.error(f"[FAIL] 知识添加失败: {e}，使用本地缓存")
                # 即使Memo0失败，也缓存知识并返回ID
                self._knowledge_cache[knowledge_id] = knowledge_entry
                return knowledge_id
        else:
            # 降级到本地存储或缓存
            fallback_id = await self._fallback_add_knowledge(knowledge_entry)
            # 如果降级存储也失败，至少缓存到本地
            if not fallback_id:
                self._knowledge_cache[knowledge_id] = knowledge_entry
                logger.info(f"[OK] 知识已缓存到本地: {knowledge_id} (质量: {quality_level.value})")
                return knowledge_id
            return fallback_id

    def _generate_knowledge_id(self, content: str, metadata: Dict) -> str:
        """生成知识ID"""
        data = f"{content}:{json.dumps(metadata, sort_keys=True)}"
        return hashlib.md5(data.encode()).hexdigest()[:16]

    async def _assess_knowledge_quality(
        self,
        content: str,
        metadata: Dict[str, Any]
    ) -> Tuple[float, KnowledgeQuality]:
        """评估知识质量（V5.2多维度评估）"""
        quality_scores = {}

        # 1. 内容完整性评分
        content_length = len(content)
        if content_length > 200:
            quality_scores["content_completeness"] = 1.0
        elif content_length > 100:
            quality_scores["content_completeness"] = 0.7
        elif content_length > 50:
            quality_scores["content_completeness"] = 0.4
        else:
            quality_scores["content_completeness"] = 0.1

        # 2. 元数据完整性评分
        required_fields = ["type", "timestamp"]
        metadata_completeness = sum(
            1 for field in required_fields if field in metadata
        ) / len(required_fields)
        quality_scores["metadata_completeness"] = metadata_completeness

        # 3. 时效性评分
        timestamp = metadata.get("timestamp", metadata.get("created_at", ""))
        if timestamp:
            try:
                if isinstance(timestamp, str):
                    knowledge_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                else:
                    knowledge_time = datetime.fromtimestamp(timestamp)

                age_days = (datetime.now() - knowledge_time).days
                if age_days < 7:
                    quality_scores["freshness"] = 1.0
                elif age_days < 30:
                    quality_scores["freshness"] = 0.8
                elif age_days < 90:
                    quality_scores["freshness"] = 0.5
                else:
                    quality_scores["freshness"] = 0.2
            except:
                quality_scores["freshness"] = 0.5
        else:
            quality_scores["freshness"] = 0.3

        # 4. 逻辑一致性评分
        consistency_score = await self._check_logical_consistency(content, metadata)
        quality_scores["logical_consistency"] = consistency_score

        # 5. 实用性评分
        utility_score = await self._assess_utility(content, metadata)
        quality_scores["utility"] = utility_score

        # 计算综合质量分数
        weights = {
            "content_completeness": 0.25,
            "metadata_completeness": 0.15,
            "freshness": 0.20,
            "logical_consistency": 0.20,
            "utility": 0.20
        }

        total_score = sum(
            quality_scores[key] * weights[key]
            for key in quality_scores.keys()
        )

        # 确定质量等级
        if total_score >= self.quality_thresholds[KnowledgeQuality.EXCELLENT]:
            quality_level = KnowledgeQuality.EXCELLENT
        elif total_score >= self.quality_thresholds[KnowledgeQuality.GOOD]:
            quality_level = KnowledgeQuality.GOOD
        elif total_score >= self.quality_thresholds[KnowledgeQuality.ACCEPTABLE]:
            quality_level = KnowledgeQuality.ACCEPTABLE
        elif total_score >= self.quality_thresholds[KnowledgeQuality.POOR]:
            quality_level = KnowledgeQuality.POOR
        else:
            quality_level = KnowledgeQuality.INVALID

        logger.debug(f"知识质量评估: {total_score:.2f} ({quality_level.value})")
        return total_score, quality_level

    async def _check_logical_consistency(
        self,
        content: str,
        metadata: Dict
    ) -> float:
        """检查逻辑一致性"""
        # 简化实现：基于内容长度和关键词检查
        consistency_indicators = []

        # 检查是否有明确的结论
        if any(word in content for word in ["结论", "因此", "所以", "结果", "成功", "失败"]):
            consistency_indicators.append(1.0)
        else:
            consistency_indicators.append(0.5)

        # 检查是否有数据支持
        if any(word in content for word in ["数据", "统计", "分析", "测试", "验证"]):
            consistency_indicators.append(1.0)
        else:
            consistency_indicators.append(0.6)

        # 检查元数据类型是否一致
        knowledge_type = metadata.get("type", "")
        if knowledge_type:
            consistency_indicators.append(1.0)
        else:
            consistency_indicators.append(0.3)

        return sum(consistency_indicators) / len(consistency_indicators)

    async def _assess_utility(
        self,
        content: str,
        metadata: Dict
    ) -> float:
        """评估知识实用性"""
        utility_score = 0.0

        # 检查是否包含可操作的建议
        if any(word in content for word in ["建议", "推荐", "应该", "可以", "策略", "方法"]):
            utility_score += 0.3

        # 检查是否包含具体数据
        if any(char.isdigit() for char in content):
            utility_score += 0.2

        # 检查是否是经验总结
        if metadata.get("type") in ["trading_execution", "strategy_optimization", "risk_event"]:
            utility_score += 0.3

        # 检查是否链接到其他知识
        if "references" in metadata or "related_knowledge" in metadata:
            utility_score += 0.2

        return min(1.0, utility_score)

    async def _fallback_add_knowledge(self, knowledge: KnowledgeEntry) -> str:
        """降级存储添加知识"""
        if self.fallback_storage is None:
            logger.warning("降级存储不可用")
            return ""

        try:
            # 这里假设fallback_storage有add_knowledge方法
            if hasattr(self.fallback_storage, 'add_knowledge'):
                return self.fallback_storage.add_knowledge(
                    knowledge.content,
                    knowledge.metadata
                )
            elif hasattr(self.fallback_storage, 'add_entry'):
                return self.fallback_storage.add_entry(
                    content=knowledge.content,
                    metadata=knowledge.metadata
                )
            else:
                logger.warning("降级存储不支持添加知识")
                return ""
        except Exception as e:
            logger.error(f"降级存储添加知识失败: {e}")
            return ""

    # ---------------------- 知识验证和学习循环 ----------------------

    async def validate_knowledge(
        self,
        knowledge_id: str,
        validation_result: bool,
        feedback: Optional[str] = None
    ):
        """验证知识有效性（V5.2增强版）"""
        self.learning_stats["total_knowledge_validated"] += 1

        if knowledge_id not in self._knowledge_cache:
            # 尝试从Memo0加载
            await self._load_knowledge_to_cache(knowledge_id)

        if knowledge_id not in self._knowledge_cache:
            logger.warning(f"知识 {knowledge_id} 不在缓存中")
            return

        knowledge = self._knowledge_cache[knowledge_id]

        # 更新验证统计
        knowledge.validation_count += 1
        if validation_result:
            knowledge.success_count += 1
        else:
            knowledge.failure_count += 1

        knowledge.last_validated = datetime.now().timestamp()

        # 重新计算质量分数
        new_quality_score = await self._recalculate_quality(knowledge)
        if new_quality_score != knowledge.quality_score:
            old_quality = knowledge.quality_level
            knowledge.quality_score = new_quality_score
            knowledge.quality_level = self._determine_quality_level(new_quality_score)

            if knowledge.quality_level.value > old_quality.value:
                self.learning_stats["quality_improvements"] += 1
                logger.info(f"[OK] 知识质量提升: {knowledge_id} {old_quality.value} → {knowledge.quality_level.value}")

        # 更新到Memo0
        if self._mem0_available:
            try:
                await self._update_knowledge_in_memo0(knowledge_id, knowledge)
            except Exception as e:
                logger.error(f"更新知识失败: {e}")

    async def _load_knowledge_to_cache(self, knowledge_id: str):
        """加载知识到缓存"""
        if not self._mem0_available:
            return

        try:
            # 从Memo0搜索知识
            results = await self.mem0_storage.search_knowledge(
                knowledge_id,
                top_k=1
            )

            if results:
                result = results[0]
                metadata = result.get("metadata", {})

                knowledge_entry = KnowledgeEntry(
                    content=result.get("content", ""),
                    metadata=metadata,
                    quality_score=metadata.get("quality_score", 0.5),
                    quality_level=KnowledgeQuality(
                        metadata.get("quality_level", "acceptable")
                    ),
                    validation_count=metadata.get("validation_count", 0),
                    success_count=metadata.get("success_count", 0),
                    failure_count=metadata.get("failure_count", 0),
                    last_validated=metadata.get("last_validated", 0),
                    created_at=metadata.get("created_at", datetime.now().timestamp()),
                    updated_at=metadata.get("updated_at", datetime.now().timestamp())
                )

                self._knowledge_cache[knowledge_id] = knowledge_entry

        except Exception as e:
            logger.error(f"加载知识到缓存失败: {e}")

    async def _recalculate_quality(self, knowledge: KnowledgeEntry) -> float:
        """重新计算知识质量"""
        if knowledge.validation_count == 0:
            return knowledge.quality_score

        # 基于验证结果调整质量
        success_rate = knowledge.success_count / knowledge.validation_count

        # 原始质量分数权重70%，验证结果权重30%
        adjusted_score = (
            knowledge.quality_score * 0.7 +
            success_rate * 0.3
        )

        return adjusted_score

    def _determine_quality_level(self, score: float) -> KnowledgeQuality:
        """确定质量等级"""
        if score >= self.quality_thresholds[KnowledgeQuality.EXCELLENT]:
            return KnowledgeQuality.EXCELLENT
        elif score >= self.quality_thresholds[KnowledgeQuality.GOOD]:
            return KnowledgeQuality.GOOD
        elif score >= self.quality_thresholds[KnowledgeQuality.ACCEPTABLE]:
            return KnowledgeQuality.ACCEPTABLE
        elif score >= self.quality_thresholds[KnowledgeQuality.POOR]:
            return KnowledgeQuality.POOR
        else:
            return KnowledgeQuality.INVALID

    async def _update_knowledge_in_memo0(
        self,
        knowledge_id: str,
        knowledge: KnowledgeEntry
    ):
        """更新Memo0中的知识"""
        if not self._mem0_available:
            return

        try:
            # Memo0可能不支持直接更新，需要重新添加
            await self.mem0_storage.add_knowledge({
                "content": knowledge.content,
                "metadata": {
                    **knowledge.metadata,
                    "quality_score": knowledge.quality_score,
                    "quality_level": knowledge.quality_level.value,
                    "validation_count": knowledge.validation_count,
                    "success_count": knowledge.success_count,
                    "failure_count": knowledge.failure_count,
                    "last_validated": knowledge.last_validated,
                    "updated_at": datetime.now().isoformat()
                }
            })

            logger.debug(f"知识已更新: {knowledge_id}")

        except Exception as e:
            logger.error(f"更新知识到Memo0失败: {e}")

    # ---------------------- 知识关联和图谱构建 ----------------------

    async def build_knowledge_relations(
        self,
        knowledge_id: str,
        max_relations: int = 5
    ):
        """构建知识关联（V5.2新增）"""
        if knowledge_id not in self._knowledge_cache:
            await self._load_knowledge_to_cache(knowledge_id)

        if knowledge_id not in self._knowledge_cache:
            return

        knowledge = self._knowledge_cache[knowledge_id]

        # 搜索相似知识
        similar_knowledges = await self._find_similar_knowledges(
            knowledge.content,
            exclude_id=knowledge_id,
            top_k=max_relations
        )

        # 构建关联
        for similar in similar_knowledges:
            relation = await self._determine_relation_type(knowledge, similar)
            if relation:
                self._relation_cache.append(relation)
                self.learning_stats["total_relations_built"] += 1

                # V5.3: 定期清理关系缓存，防止内存泄漏
                if len(self._relation_cache) > self._max_relation_cache_size:
                    self._prune_relation_cache()

        logger.info(f"[OK] 为知识 {knowledge_id} 构建了 {len(similar_knowledges)} 个关联")

    async def _find_similar_knowledges(
        self,
        content: str,
        exclude_id: str,
        top_k: int = 5
    ) -> List[Dict]:
        """查找相似知识"""
        if self._mem0_available:
            try:
                results = await self.mem0_storage.search_knowledge(
                    content,
                    top_k=top_k + 1  # 多取1个以排除自己
                )

                # 排除自己
                filtered_results = [
                    r for r in results
                    if r.get("metadata", {}).get("knowledge_id") != exclude_id
                ][:top_k]

                return filtered_results

            except Exception as e:
                logger.error(f"搜索相似知识失败: {e}")
                return []
        return []

    async def _determine_relation_type(
        self,
        knowledge1: KnowledgeEntry,
        knowledge2: Dict
    ) -> Optional[KnowledgeRelation]:
        """确定关联类型"""
        metadata2 = knowledge2.get("metadata", {})
        knowledge2_id = metadata2.get("knowledge_id", "")
        content2 = knowledge2.get("content", "")

        if not knowledge2_id:
            return None

        # 基于内容相似度确定关联类型
        content_similarity = self._calculate_content_similarity(
            knowledge1.content, content2
        )

        # 基于元数据确定关联类型
        type1 = knowledge1.metadata.get("type", "")
        type2 = metadata2.get("type", "")

        relation_type = "similar"
        confidence = content_similarity

        if type1 == type2:
            relation_type = "similar"
            confidence = min(1.0, confidence + 0.2)
        elif type1 in ["risk_event"] and type2 in ["trading_execution"]:
            relation_type = "causal"
            confidence = min(1.0, confidence + 0.1)
        elif type1 in ["trading_execution"] and type2 in ["strategy_optimization"]:
            relation_type = "complementary"
            confidence = min(1.0, confidence + 0.1)

        # 只有高置信度的关联才保存
        if confidence < 0.5:
            return None

        return KnowledgeRelation(
            source_id=knowledge1.metadata.get("knowledge_id", ""),
            target_id=knowledge2_id,
            relation_type=relation_type,
            confidence=confidence
        )

    def _calculate_content_similarity(
        self,
        content1: str,
        content2: str
    ) -> float:
        """计算内容相似度（简化实现）"""
        # 使用关键词重叠度作为相似度
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0

    # ---------------------- 知识淘汰和清理 ----------------------

    async def retire_invalid_knowledge(self, max_age_days: int = 90):
        """淘汰无效知识（V5.2新增）"""
        retired_count = 0

        for knowledge_id, knowledge in list(self._knowledge_cache.items()):
            # 检查年龄
            age_days = (datetime.now().timestamp() - knowledge.created_at) / 86400

            # 检查质量等级
            if knowledge.quality_level == KnowledgeQuality.INVALID:
                should_retire = True
                reason = "质量等级为无效"
            # 检查验证失败率
            elif knowledge.validation_count > 5:
                failure_rate = knowledge.failure_count / knowledge.validation_count
                if failure_rate > 0.7:  # 失败率>70%
                    should_retire = True
                    reason = f"验证失败率过高 ({failure_rate:.1%})"
                else:
                    should_retire = False
                    reason = ""
            # 检查年龄
            elif age_days > max_age_days:
                should_retire = True
                reason = f"知识过期 ({age_days:.0f}天)"
            else:
                should_retire = False
                reason = ""

            if should_retire:
                # 从缓存中移除
                del self._knowledge_cache[knowledge_id]
                retired_count += 1
                logger.info(f"🗑️ 淘汰知识: {knowledge_id} - {reason}")

        self.learning_stats["total_knowledge_retired"] += retired_count
        return retired_count

    def _prune_relation_cache(self) -> int:
        """清理关系缓存（V5.3新增，防止内存泄漏）

        Returns:
            清理的关系数量
        """
        original_size = len(self._relation_cache)

        # 1. 移除超过大小限制的最旧关系
        if len(self._relation_cache) > self._max_relation_cache_size:
            # 按创建时间排序，移除最旧的20%
            sorted_relations = sorted(
                self._relation_cache,
                key=lambda r: r.created_at
            )
            remove_count = len(self._relation_cache) - int(self._max_relation_cache_size * 0.8)
            self._relation_cache = sorted_relations[remove_count:]

            logger.info(
                f"🗑️ 清理关系缓存: 移除 {remove_count} 个最旧关系 "
                f"(保留 {len(self._relation_cache)}/{self._max_relation_cache_size})"
            )

        # 2. 清理指向已淘汰知识的关联
        if self._knowledge_cache:
            valid_knowledge_ids = set(self._knowledge_cache.keys())
            original_relation_count = len(self._relation_cache)

            self._relation_cache = [
                relation for relation in self._relation_cache
                if relation.source_id in valid_knowledge_ids and
                   relation.target_id in valid_knowledge_ids
            ]

            removed_count = original_relation_count - len(self._relation_cache)
            if removed_count > 0:
                logger.info(
                    f"🗑️ 清理无效关系: 移除 {removed_count} 个指向无效知识的关联"
                )

        # 3. 清理使用频率统计
        if len(self._relation_cache_hits) > 10000:
            # 保留最近使用的1000个
            sorted_hits = sorted(
                self._relation_cache_hits.items(),
                key=lambda x: x[1],
                reverse=True
            )
            self._relation_cache_hits = dict(sorted_hits[:1000])

        return original_size - len(self._relation_cache)

    # ---------------------- 统计信息 ----------------------

    def get_learning_statistics(self) -> Dict[str, Any]:
        """获取学习统计信息"""
        return {
            **self.learning_stats,
            "knowledge_cache_size": len(self._knowledge_cache),
            "relation_cache_size": len(self._relation_cache),
            "mem0_available": self._mem0_available,
            "quality_distribution": self._get_quality_distribution()
        }

    def _get_quality_distribution(self) -> Dict[str, int]:
        """获取质量分布"""
        distribution = {level.value: 0 for level in KnowledgeQuality}

        for knowledge in self._knowledge_cache.values():
            distribution[knowledge.quality_level.value] += 1

        return distribution


# ======================= 工厂函数 =======================

def create_auto_knowledge_accumulator_v5_2(
    mem0_storage,
    fallback_storage=None
) -> AutoKnowledgeAccumulatorV52:
    """创建V5.2自动知识积累器实例

    Args:
        mem0_storage: Memo0存储实例
        fallback_storage: 降级存储实例（可选）

    Returns:
        AutoKnowledgeAccumulatorV52实例
    """
    return AutoKnowledgeAccumulatorV52(
        mem0_storage=mem0_storage,
        fallback_storage=fallback_storage
    )
