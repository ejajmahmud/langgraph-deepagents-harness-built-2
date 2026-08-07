"""内存存储实现 - V5.10 Phase 3

使用内存字典实现知识存储，用于测试和开发环境。

核心功能：
1. 基于内存的知识存储
2. 简单的关键词搜索
3. 快速响应
4. 不支持持久化

创建时间：2026-04-19
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

# 导入抽象接口
from storage.knowledge_storage_interface import (
    KnowledgeStorage,
    KnowledgeItem,
    SearchResult,
    StorageStats
)

logger = logging.getLogger(__name__)


class InMemoryStorage(KnowledgeStorage):
    """内存存储实现

    使用字典在内存中存储知识，适用于测试和开发环境。
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化内存存储

        Args:
            config: 配置字典（内存存储不需要特殊配置）
        """
        super().__init__(config)

        # 内存存储
        self._knowledge_store: Dict[str, KnowledgeItem] = {}
        self._initialized = True

        logger.info("初始化内存存储")

    # ========== 核心CRUD操作 ==========

    async def add_knowledge(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """添加知识

        Args:
            content: 知识内容
            metadata: 元数据

        Returns:
            知识ID
        """
        # 生成知识ID
        knowledge_id = self._generate_knowledge_id(content)

        # 创建知识条目
        now = datetime.now()

        knowledge_item = KnowledgeItem(
            knowledge_id=knowledge_id,
            content=content,
            metadata=metadata or {},
            created_at=now,
            updated_at=now,
            quality_score=0.7,
            value_score=0.6
        )

        # 添加到存储
        self._knowledge_store[knowledge_id] = knowledge_item

        # 更新统计
        self._update_stats("add")
        self.stats.total_knowledge = len(self._knowledge_store)

        logger.debug(f"添加知识: {knowledge_id}")

        return knowledge_id

    async def get_knowledge(
        self,
        knowledge_id: str
    ) -> Optional[KnowledgeItem]:
        """获取知识

        Args:
            knowledge_id: 知识ID

        Returns:
            知识条目或None
        """
        return self._knowledge_store.get(knowledge_id)

    async def update_knowledge(
        self,
        knowledge_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """更新知识

        Args:
            knowledge_id: 知识ID
            content: 新内容（可选）
            metadata: 新元数据（可选）

        Returns:
            是否成功
        """
        existing = self._knowledge_store.get(knowledge_id)

        if not existing:
            logger.warning(f"知识不存在: {knowledge_id}")
            return False

        # 更新内容
        if content is not None:
            existing.content = content

        # 更新元数据
        if metadata is not None:
            existing.metadata.update(metadata)

        # 更新时间戳
        existing.updated_at = datetime.now()

        # 更新统计
        self._update_stats("update")

        logger.debug(f"更新知识: {knowledge_id}")

        return True

    async def delete_knowledge(
        self,
        knowledge_id: str
    ) -> bool:
        """删除知识

        Args:
            knowledge_id: 知识ID

        Returns:
            是否成功
        """
        if knowledge_id not in self._knowledge_store:
            logger.warning(f"知识不存在: {knowledge_id}")
            return False

        # 从存储中删除
        del self._knowledge_store[knowledge_id]

        # 更新统计
        self._update_stats("delete")
        self.stats.total_knowledge = len(self._knowledge_store)

        logger.debug(f"删除知识: {knowledge_id}")

        return True

    # ========== 搜索和查询 ==========

    async def search_knowledge(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """搜索知识

        Args:
            query: 查询内容
            top_k: 返回数量
            filters: 过滤条件

        Returns:
            搜索结果列表
        """
        query_lower = query.lower()
        results = []

        # 遍历所有知识
        for item in self._knowledge_store.values():
            # 应用过滤条件
            if filters:
                match = True
                for key, value in filters.items():
                    if item.metadata.get(key) != value:
                        match = False
                        break

                if not match:
                    continue

            # 内容匹配
            if query_lower in item.content.lower():
                # 计算相似度分数（简单的字符串包含）
                similarity = self._calculate_similarity(query, item.content)

                results.append(SearchResult(
                    knowledge_id=item.knowledge_id,
                    content=item.content,
                    metadata=item.metadata,
                    similarity_score=similarity,
                    quality_score=item.quality_score,
                    value_score=item.value_score
                ))

        # 按相似度排序
        results.sort(key=lambda x: x.similarity_score, reverse=True)

        # 限制返回数量
        results = results[:top_k]

        # 更新统计
        self._update_stats("search")

        logger.debug(f"搜索: {query} -> {len(results)} 结果")

        return results

    async def semantic_search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """语义搜索（向量搜索）

        注意：内存存储不支持真正的语义搜索，退化为关键词搜索

        Args:
            query: 查询内容
            top_k: 返回数量
            filters: 过滤条件

        Returns:
            搜索结果列表
        """
        logger.warning("内存存储不支持真正的语义搜索，使用关键词搜索")
        return await self.search_knowledge(query, top_k, filters)

    async def search_by_metadata(
        self,
        filters: Dict[str, Any],
        limit: int = 100
    ) -> List[KnowledgeItem]:
        """按元数据搜索

        Args:
            filters: 过滤条件
            limit: 返回数量限制

        Returns:
            知识条目列表
        """
        results = []

        for item in self._knowledge_store.values():
            match = True
            for key, value in filters.items():
                if item.metadata.get(key) != value:
                    match = False
                    break

            if match:
                results.append(item)

            if len(results) >= limit:
                break

        return results

    # ========== 列表和统计 ==========

    async def list_knowledge(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[KnowledgeItem]:
        """列出知识

        Args:
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            知识条目列表
        """
        all_items = list(self._knowledge_store.values())

        # 按创建时间倒序排序
        all_items.sort(key=lambda x: x.created_at, reverse=True)

        # 应用偏移和限制
        return all_items[offset:offset + limit]

    async def clear_all(self) -> bool:
        """清除所有知识

        Returns:
            是否成功
        """
        count = len(self._knowledge_store)
        self._knowledge_store.clear()
        self.stats.total_knowledge = 0

        logger.info(f"清除了所有知识: {count} 条")

        return True

    # ========== 工具方法 ==========

    def _generate_knowledge_id(self, content: str) -> str:
        """生成知识ID

        Args:
            content: 知识内容

        Returns:
            知识ID
        """
        import hashlib

        # 使用MD5哈希
        content_hash = hashlib.md5(content.encode()).hexdigest()[:12]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        return f"knowledge_{content_hash}_{timestamp}"

    def _calculate_similarity(
        self,
        query: str,
        content: str
    ) -> float:
        """计算相似度分数

        Args:
            query: 查询字符串
            content: 内容字符串

        Returns:
            相似度分数 (0-1)
        """
        query_lower = query.lower()
        content_lower = content.lower()

        # 简单的字符串包含分数
        if query_lower in content_lower:
            # 根据匹配的字符数计算分数
            match_ratio = len(query_lower) / max(len(content_lower), 1)
            return min(1.0, match_ratio * 2)

        return 0.0


# ========== 便捷函数 ==========

async def create_memory_storage(
    config: Optional[Dict[str, Any]] = None
) -> InMemoryStorage:
    """创建内存存储实例

    Args:
        config: 配置字典

    Returns:
        内存存储实例
    """
    if config is None:
        config = {}

    return InMemoryStorage(config)


async def quick_add_knowledge(
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None
) -> str:
    """快速添加知识

    Args:
        content: 知识内容
        metadata: 元数据
        config: 配置字典

    Returns:
        知识ID
    """
    storage = await create_memory_storage(config)
    return await storage.add_knowledge(content, metadata)


async def quick_search_knowledge(
    query: str,
    top_k: int = 10,
    config: Optional[Dict[str, Any]] = None
) -> List[SearchResult]:
    """快速搜索知识

    Args:
        query: 查询内容
        top_k: 返回数量
        config: 配置字典

    Returns:
        搜索结果列表
    """
    storage = await create_memory_storage(config)
    return await storage.search_knowledge(query, top_k)
