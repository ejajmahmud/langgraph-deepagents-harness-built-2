"""智能存储工厂 - Phase 8核心模块

自动选择最佳存储后端，支持多种存储类型的无缝切换。

核心功能：
1. 智能存储选择 - 根据配置自动选择最佳后端
2. 存储健康检查 - 自动检测存储可用性
3. 故障转移 - 自动切换到备用存储
4. 配置管理 - 统一的存储配置接口
5. 性能监控 - 存储性能指标收集

创建时间：2026-04-19 17:50
"""

import asyncio
import logging
from typing import Any, Dict, Optional, Type
from enum import Enum

from storage.knowledge_storage_interface import KnowledgeStorage

logger = logging.getLogger(__name__)


class StorageType(Enum):
    """存储类型枚举"""
    MEM0 = "mem0"              # Memo0云存储（需要API密钥）
    LOCAL_VECTOR = "local_vector"  # 本地向量存储
    LOCAL_SQLITE = "local_sqlite" # 本地SQLite存储
    SIMPLE = "simple"            # 简单内存存储（测试用）


class StorageFactory:
    """智能存储工厂

    根据配置和可用性自动选择最佳存储后端。
    """

    def __init__(self):
        """初始化存储工厂"""
        self._storage_cache: Dict[str, KnowledgeStorage] = {}
        self._health_cache: Dict[str, bool] = {}
        self._performance_metrics: Dict[str, Dict] = {}

        logger.info("智能存储工厂初始化完成")

    async def create_storage(
        self,
        config: Optional[Dict[str, Any]] = None
    ) -> KnowledgeStorage:
        """创建存储实例

        Args:
            config: 配置字典
                - storage_type: 存储类型（可选，自动检测）
                - auto_fallback: 是否启用自动故障转移（默认：true）
                - preferred_order: 首选存储顺序（默认：["mem0", "local_vector", "simple"]）

        Returns:
            存储实例
        """
        if config is None:
            config = {}

        # 获取存储类型
        storage_type = config.get('storage_type')
        auto_fallback = config.get('auto_fallback', True)
        preferred_order = config.get(
            'preferred_order',
            ["mem0", "local_vector", "simple"]
        )

        # 如果指定了存储类型，尝试创建
        if storage_type:
            try:
                storage = await self._create_storage_by_type(storage_type, config)
                logger.info(f"使用指定存储类型: {storage_type}")
                return storage
            except Exception as e:
                logger.warning(f"创建存储 {storage_type} 失败: {e}")
                if not auto_fallback:
                    raise

        # 自动检测最佳存储
        for storage_name in preferred_order:
            try:
                logger.info(f"尝试创建存储: {storage_name}")

                storage = await self._create_storage_by_type(storage_name, config)

                # 验证存储健康状态
                if await self._check_storage_health(storage):
                    logger.info(f"[OK] 成功创建存储: {storage_name}")
                    self._cache_storage(storage_name, storage)
                    return storage
                else:
                    logger.warning(f"存储 {storage_name} 健康检查失败")

            except Exception as e:
                logger.warning(f"创建存储 {storage_name} 失败: {e}")
                continue

        # 所有存储都失败，使用最后的后备
        logger.error("所有存储都失败，使用最后的后备存储")
        return await self._create_fallback_storage(config)

    async def _create_storage_by_type(
        self,
        storage_type: str,
        config: Dict[str, Any]
    ) -> KnowledgeStorage:
        """根据类型创建存储

        Args:
            storage_type: 存储类型
            config: 配置字典

        Returns:
            存储实例
        """
        # Memo0存储
        if storage_type == "mem0":
            from storage.memo0_storage_impl import create_memo0_storage
            return await create_memo0_storage(config)

        # 本地向量存储
        elif storage_type == "local_vector":
            from storage.local_vector_storage import create_local_vector_storage
            return await create_local_vector_storage(config)

        # 简单存储（后备）
        elif storage_type == "simple":
            return await self._create_fallback_storage(config)

        else:
            raise ValueError(f"不支持的存储类型: {storage_type}")

    async def _create_fallback_storage(
        self,
        config: Dict[str, Any]
    ) -> KnowledgeStorage:
        """创建后备存储

        Args:
            config: 配置字典

        Returns:
            后备存储实例
        """
        logger.warning("创建后备存储（简单内存存储）")

        class FallbackStorage(KnowledgeStorage):
            """后备存储实现"""

            def __init__(self, config: Dict[str, Any]):
                super().__init__(config)
                self._data = {}
                self._stats = {'total_knowledge': 0}

            async def initialize(self):
                pass

            async def add_knowledge(self, content: str, metadata: dict = None) -> str:
                import uuid
                from storage.knowledge_storage_interface import KnowledgeItem
                knowledge_id = f"fallback_{uuid.uuid4().hex[:12]}"
                self._data[knowledge_id] = {
                    'knowledge_id': knowledge_id,
                    'content': content,
                    'metadata': metadata or {},
                    'created_at': None,  # 简化版本
                    'updated_at': None
                }
                self._stats['total_knowledge'] = len(self._data)
                return knowledge_id

            async def get_knowledge(self, knowledge_id: str):
                return self._data.get(knowledge_id)

            async def update_knowledge(self, knowledge_id: str, content: str = None, metadata: dict = None) -> bool:
                if knowledge_id not in self._data:
                    return False
                if content:
                    self._data[knowledge_id]['content'] = content
                if metadata:
                    self._data[knowledge_id]['metadata'].update(metadata)
                return True

            async def delete_knowledge(self, knowledge_id: str) -> bool:
                if knowledge_id not in self._data:
                    return False
                del self._data[knowledge_id]
                self._stats['total_knowledge'] = len(self._data)
                return True

            async def search_knowledge(self, query: str, top_k: int = 10, filters: dict = None):
                from storage.knowledge_storage_interface import SearchResult
                results = []
                for kid, kdata in self._data.items():
                    # 简单的文本匹配
                    similarity = 0.8 if query.lower() in kdata['content'].lower() else 0.3
                    results.append(SearchResult(
                        knowledge_id=kid,
                        content=kdata['content'],
                        metadata=kdata.get('metadata', {}),
                        similarity_score=similarity,
                        quality_score=0.7,
                        value_score=0.6
                    ))
                results.sort(key=lambda x: x.similarity_score, reverse=True)
                return results[:top_k]

            async def semantic_search(self, query: str, top_k: int = 10, filters: dict = None):
                return await self.search_knowledge(query, top_k, filters)

            async def list_knowledge(self, limit: int = 100, offset: int = 0):
                items = list(self._data.values())[offset:offset+limit]
                return items

            async def count_knowledge(self) -> int:
                return len(self._data)

            async def clear_all(self) -> bool:
                self._data.clear()
                self._stats['total_knowledge'] = 0
                return True

            async def close(self):
                pass

        return FallbackStorage(config)

    async def _check_storage_health(self, storage: KnowledgeStorage) -> bool:
        """检查存储健康状态

        Args:
            storage: 存储实例

        Returns:
            是否健康
        """
        try:
            # 尝试初始化
            if hasattr(storage, 'initialize'):
                await storage.initialize()

            # 尝试执行简单操作
            test_content = f"health_check_{asyncio.get_event_loop().time()}"
            test_id = await storage.add_knowledge(
                content=test_content,
                metadata={'test': True}
            )

            # 验证可以检索
            retrieved = await storage.get_knowledge(test_id)
            if not retrieved or retrieved.content != test_content:
                return False

            # 清理测试数据
            await storage.delete_knowledge(test_id)

            # 记录健康状态
            storage_name = storage.__class__.__name__
            self._health_cache[storage_name] = True

            return True

        except Exception as e:
            logger.error(f"存储健康检查失败: {e}")
            storage_name = storage.__class__.__name__
            self._health_cache[storage_name] = False
            return False

    def _cache_storage(self, name: str, storage: KnowledgeStorage) -> None:
        """缓存存储实例

        Args:
            name: 存储名称
            storage: 存储实例
        """
        self._storage_cache[name] = storage
        logger.debug(f"缓存存储实例: {name}")

    async def get_storage_health_report(self) -> Dict[str, Any]:
        """获取存储健康报告

        Returns:
            健康报告字典
        """
        report = {
            'storage_cache': list(self._storage_cache.keys()),
            'health_status': dict(self._health_cache),
            'performance_metrics': dict(self._performance_metrics)
        }

        return report

    async def close_all(self) -> None:
        """关闭所有存储"""
        for storage in self._storage_cache.values():
            try:
                if hasattr(storage, 'close'):
                    await storage.close()
            except Exception as e:
                logger.error(f"关闭存储失败: {e}")

        self._storage_cache.clear()
        self._health_cache.clear()
        logger.info("所有存储已关闭")


# ========== 全局工厂实例 ==========

_factory_instance: Optional[StorageFactory] = None


def get_storage_factory() -> StorageFactory:
    """获取存储工厂单例

    Returns:
        存储工厂实例
    """
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = StorageFactory()
    return _factory_instance


# ========== 便捷函数 ==========

async def create_auto_storage(
    config: Optional[Dict[str, Any]] = None
) -> KnowledgeStorage:
    """创建自动选择的存储实例

    Args:
        config: 配置字典

    Returns:
        存储实例
    """
    factory = get_storage_factory()
    return await factory.create_storage(config)


async def create_knowledge_storage(
    storage_type: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
) -> KnowledgeStorage:
    """创建知识存储（兼容旧版本）

    Args:
        storage_type: 存储类型（可选）
        config: 配置字典

    Returns:
        存储实例
    """
    if config is None:
        config = {}

    if storage_type:
        config['storage_type'] = storage_type

    return await create_auto_storage(config)
