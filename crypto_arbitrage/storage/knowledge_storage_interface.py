"""知识存储抽象接口 - V5.10 Phase 3

定义统一的知识存储接口，支持多种存储后端（memo0、内存、数据库等）。

核心功能：
1. 统一的CRUD接口
2. 向量搜索支持
3. 批量操作支持
4. 元数据管理

创建时间：2026-04-19
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeItem:
    """知识条目"""
    knowledge_id: str
    content: str
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    quality_score: float = 0.7
    value_score: float = 0.6

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "knowledge_id": self.knowledge_id,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "quality_score": self.quality_score,
            "value_score": self.value_score
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeItem':
        """从字典创建"""
        return cls(
            knowledge_id=data["knowledge_id"],
            content=data["content"],
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            quality_score=data.get("quality_score", 0.7),
            value_score=data.get("value_score", 0.6)
        )


@dataclass
class SearchResult:
    """搜索结果"""
    knowledge_id: str
    content: str
    metadata: Dict[str, Any]
    similarity_score: float
    quality_score: float
    value_score: float

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "knowledge_id": self.knowledge_id,
            "content": self.content,
            "metadata": self.metadata,
            "similarity_score": self.similarity_score,
            "quality_score": self.quality_score,
            "value_score": self.value_score
        }


@dataclass
class StorageStats:
    """存储统计"""
    total_knowledge: int
    total_searches: int
    total_adds: int
    total_updates: int
    total_deletes: int
    last_accessed: Optional[datetime]
    storage_type: str

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total_knowledge": self.total_knowledge,
            "total_searches": self.total_searches,
            "total_adds": self.total_adds,
            "total_updates": self.total_updates,
            "total_deletes": self.total_deletes,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "storage_type": self.storage_type
        }


class KnowledgeStorage(ABC):
    """知识存储抽象接口

    所有存储后端必须实现此接口。
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化存储

        Args:
            config: 配置字典
        """
        self.config = config
        self.stats = StorageStats(
            total_knowledge=0,
            total_searches=0,
            total_adds=0,
            total_updates=0,
            total_deletes=0,
            last_accessed=None,
            storage_type=self.__class__.__name__
        )

    # ========== 核心CRUD操作 ==========

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    # ========== 搜索和查询 ==========

    @abstractmethod
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
        pass

    @abstractmethod
    async def semantic_search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """语义搜索（向量搜索）

        Args:
            query: 查询内容
            top_k: 返回数量
            filters: 过滤条件

        Returns:
            搜索结果列表
        """
        pass

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
        # 默认实现：遍历所有知识并过滤
        all_knowledge = await self.list_knowledge(limit=10000)
        results = []

        for item in all_knowledge:
            match = True
            for key, value in filters.items():
                if item.metadata.get(key) != value:
                    match = False
                    break

            if match:
                results.append(item)

        return results[:limit]

    # ========== 批量操作 ==========

    async def add_knowledge_batch(
        self,
        items: List[Tuple[str, Optional[Dict[str, Any]]]]
    ) -> List[str]:
        """批量添加知识

        Args:
            items: (content, metadata) 列表

        Returns:
            知识ID列表
        """
        knowledge_ids = []

        for content, metadata in items:
            knowledge_id = await self.add_knowledge(content, metadata)
            knowledge_ids.append(knowledge_id)

        return knowledge_ids

    async def delete_knowledge_batch(
        self,
        knowledge_ids: List[str]
    ) -> Dict[str, bool]:
        """批量删除知识

        Args:
            knowledge_ids: 知识ID列表

        Returns:
            {knowledge_id: success} 字典
        """
        results = {}

        for knowledge_id in knowledge_ids:
            results[knowledge_id] = await self.delete_knowledge(knowledge_id)

        return results

    # ========== 列表和统计 ==========

    @abstractmethod
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
        pass

    async def count_knowledge(self) -> int:
        """统计知识数量

        Returns:
            知识总数
        """
        return self.stats.total_knowledge

    def get_storage_stats(self) -> StorageStats:
        """获取存储统计

        Returns:
            存储统计数据
        """
        return self.stats

    # ========== 维护和优化 ==========

    async def clear_all(self) -> bool:
        """清除所有知识

        Returns:
            是否成功
        """
        # 获取所有知识ID
        all_knowledge = await self.list_knowledge(limit=1000000)

        # 删除所有知识
        for item in all_knowledge:
            await self.delete_knowledge(item.knowledge_id)

        return True

    async def optimize_storage(self) -> Dict[str, Any]:
        """优化存储

        Returns:
            优化结果
        """
        return {
            "status": "completed",
            "message": "Storage optimization completed"
        }

    # ========== 生命周期 ==========

    async def initialize(self) -> None:
        """初始化存储"""
        logger.info(f"初始化存储: {self.stats.storage_type}")

    async def close(self) -> None:
        """关闭存储"""
        logger.info(f"关闭存储: {self.stats.storage_type}")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()

    # ========== 受保护的方法 ==========

    def _update_stats(
        self,
        operation: str,
        count: int = 1
    ) -> None:
        """更新统计信息

        Args:
            operation: 操作类型 [search, add, update, delete]
            count: 数量
        """
        if operation == "search":
            self.stats.total_searches += count
        elif operation == "add":
            self.stats.total_adds += count
        elif operation == "update":
            self.stats.total_updates += count
        elif operation == "delete":
            self.stats.total_deletes += count

        self.stats.last_accessed = datetime.now()


# ========== 工厂函数 ==========

def create_knowledge_storage(
    storage_type: str,
    config: Dict[str, Any]
) -> KnowledgeStorage:
    """创建知识存储实例

    Args:
        storage_type: 存储类型 [memo0, memory, sql, redis]
        config: 配置字典

    Returns:
        存储实例

    Raises:
        ValueError: 不支持的存储类型
    """
    storage_classes = {
        "memo0": "Memo0Storage",
        "memory": "InMemoryStorage",
        # 可以添加更多存储类型
    }

    if storage_type not in storage_classes:
        raise ValueError(f"不支持的存储类型: {storage_type}")

    # 动态导入
    if storage_type == "memo0":
        from storage.memo0_storage_impl import Memo0Storage
        return Memo0Storage(config)
    elif storage_type == "memory":
        from storage.memory_storage_impl import InMemoryStorage
        return InMemoryStorage(config)

    raise ValueError(f"不支持的存储类型: {storage_type}")
