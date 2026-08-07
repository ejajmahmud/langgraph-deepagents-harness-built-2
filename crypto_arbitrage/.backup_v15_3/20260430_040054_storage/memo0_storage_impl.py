"""真正的Memo0存储实现 - V5.10 Phase 3

使用mem0ai包实现真正的持久化知识存储，支持向量搜索和语义检索。

核心功能：
1. 真正的持久化存储
2. 向量嵌入和语义搜索
3. 多种向量后端支持（Chroma, Pinecone等）
4. 自动知识去重和优化
5. 元数据管理

依赖：mem0ai>=0.1.0

创建时间：2026-04-19
"""

import asyncio
import hashlib
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

# 处理类型检查时的前向引用
if TYPE_CHECKING:
    from mem0.configs.base import VectorStoreConfig

# 导入抽象接口
from storage.knowledge_storage_interface import (
    KnowledgeStorage,
    KnowledgeItem,
    SearchResult,
    StorageStats
)

logger = logging.getLogger(__name__)


class Memo0Storage(KnowledgeStorage):
    """真正的Memo0存储实现

    使用mem0ai包提供持久化知识存储和向量搜索能力。
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化Memo0存储

        Args:
            config: 配置字典
                - api_key: OpenAI API密钥（用于嵌入）
                - embeddings_model: 嵌入模型名称（默认：text-embedding-ada-002）
                - vector_store: 向量存储类型 [chroma, pinecone, qdrant, local]
                - vector_store_config: 向量存储配置
                - user_id: 用户ID（默认：trading_system）
        """
        super().__init__(config)

        # 配置参数
        self.api_key = config.get('api_key', None)
        self.embeddings_model = config.get('embeddings_model', 'text-embedding-ada-002')
        # 注意：mem0ai 2.0+ 不支持 'local'，有效选项：chroma, qdrant, pinecone
        self.vector_store = config.get('vector_store', 'chroma')
        self.vector_store_config = config.get('vector_store_config', {})
        self.user_id = config.get('user_id', 'trading_system')

        # Memo0实例
        self._memory = None
        self._initialized = False

        logger.info(f"初始化Memo0存储: {self.vector_store}")

    async def initialize(self) -> None:
        """初始化Memo0存储"""
        if self._initialized:
            logger.warning("Memo0存储已初始化")
            return

        try:
            # 动态导入mem0ai 2.0
            from mem0 import Memory
            from mem0.configs.base import MemoryConfig, VectorStoreConfig, LlmConfig, EmbedderConfig

            # 配置向量存储
            vector_store_config = self._build_vector_store_config()

            # 配置嵌入器
            if self.api_key:
                embedder_config = EmbedderConfig(
                    provider='openai',
                    config={
                        'api_key': self.api_key,
                        'model': self.embeddings_model
                    }
                )
            else:
                # 如果没有API密钥，使用默认配置
                embedder_config = EmbedderConfig(
                    provider='openai',
                    config={'model': self.embeddings_model}
                )
                logger.warning("未提供API密钥，使用默认嵌入配置")

            # 配置LLM（用于某些高级功能）
            llm_config = LlmConfig(
                provider='openai',
                config={'api_key': self.api_key} if self.api_key else {}
            )

            # 创建Memory实例
            memory_config = MemoryConfig(
                vector_store=vector_store_config,
                embedder=embedder_config,
                llm=llm_config,
                history_db_path=self.vector_store_config.get('history_db_path', './.mem0/history.db')
            )

            self._memory = Memory(config=memory_config)

            self._initialized = True
            logger.info("✅ Memo0存储初始化完成")

        except ImportError as e:
            logger.error(f"mem0ai包未安装: {e}")
            raise ImportError(
                "mem0ai包未安装，请运行: pip install mem0ai>=2.0.0"
            )
        except Exception as e:
            logger.error(f"Memo0存储初始化失败: {e}")
            raise

    def _build_vector_store_config(self) -> 'VectorStoreConfig':
        """构建向量存储配置

        Returns:
            VectorStoreConfig对象
        """
        from mem0.configs.base import VectorStoreConfig

        # 构建配置字典
        store_config = {}

        # 根据存储类型添加特定配置
        if self.vector_store == "chroma":
            store_config.update({
                "collection_name": "trading_knowledge",
                "path": self.vector_store_config.get('path', './chroma_db')
            })
        elif self.vector_store == "qdrant":
            store_config.update({
                "host": self.vector_store_config.get('host', 'localhost'),
                "port": self.vector_store_config.get('port', 6333),
                "collection_name": "trading_knowledge"
            })
        elif self.vector_store == "pinecone":
            store_config.update({
                "api_key": self.vector_store_config.get('api_key'),
                "environment": self.vector_store_config.get('environment'),
                "index_name": "trading_knowledge"
            })
        else:
            # 对于qdrant（默认）
            store_config.update({
                "collection_name": "trading_knowledge"
            })

        return VectorStoreConfig(provider=self.vector_store, config=store_config)

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
        if not self._initialized:
            await self.initialize()

        try:
            # 生成知识ID
            knowledge_id = self._generate_knowledge_id(content)

            # 准备元数据
            enhanced_metadata = {
                "knowledge_id": knowledge_id,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "quality_score": 0.7,
                "value_score": 0.6,
                **(metadata or {})
            }

            # 添加到memo0
            result = await self._memory.add(
                content=content,
                metadata=enhanced_metadata,
                user_id=self.user_id
            )

            # 更新统计
            self._update_stats("add")
            self.stats.total_knowledge = await self.count_knowledge()

            logger.debug(f"添加知识: {knowledge_id}")

            return knowledge_id

        except Exception as e:
            logger.error(f"添加知识失败: {e}")
            raise

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
        if not self._initialized:
            await self.initialize()

        try:
            # 通过元数据搜索
            results = await self._memory.search(
                query="",  # 空查询
                limit=100,
                user_id=self.user_id,
                metadata_filter={"knowledge_id": knowledge_id}
            )

            if not results or len(results) == 0:
                return None

            # 返回第一个匹配项
            result = results[0]

            # 转换为KnowledgeItem
            metadata = result.get('metadata', {})

            return KnowledgeItem(
                knowledge_id=knowledge_id,
                content=result.get('content', ''),
                metadata={k: v for k, v in metadata.items()
                         if k not in ['knowledge_id', 'created_at', 'updated_at',
                                      'quality_score', 'value_score']},
                created_at=datetime.fromisoformat(
                    metadata.get('created_at', datetime.now().isoformat())
                ),
                updated_at=datetime.fromisoformat(
                    metadata.get('updated_at', datetime.now().isoformat())
                ),
                quality_score=float(metadata.get('quality_score', 0.7)),
                value_score=float(metadata.get('value_score', 0.6))
            )

        except Exception as e:
            logger.error(f"获取知识失败: {e}")
            return None

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
        if not self._initialized:
            await self.initialize()

        try:
            # 获取现有知识
            existing = await self.get_knowledge(knowledge_id)

            if not existing:
                logger.warning(f"知识不存在: {knowledge_id}")
                return False

            # 删除旧知识
            await self.delete_knowledge(knowledge_id)

            # 添加新知识
            new_content = content if content is not None else existing.content
            new_metadata = {
                **existing.metadata,
                **(metadata or {}),
                "updated_at": datetime.now().isoformat()
            }

            await self.add_knowledge(new_content, new_metadata)

            # 更新统计
            self._update_stats("update")

            logger.debug(f"更新知识: {knowledge_id}")

            return True

        except Exception as e:
            logger.error(f"更新知识失败: {e}")
            return False

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
        if not self._initialized:
            await self.initialize()

        try:
            # Memo0的删除需要先搜索
            results = await self._memory.search(
                query="",
                limit=100,
                user_id=self.user_id,
                metadata_filter={"knowledge_id": knowledge_id}
            )

            if not results:
                logger.warning(f"知识不存在: {knowledge_id}")
                return False

            # 删除第一个匹配项
            result = results[0]
            memory_id = result.get('id')

            # 使用memo0的删除功能
            await self._memory.delete(memory_id, user_id=self.user_id)

            # 更新统计
            self._update_stats("delete")
            self.stats.total_knowledge = await self.count_knowledge()

            logger.debug(f"删除知识: {knowledge_id}")

            return True

        except Exception as e:
            logger.error(f"删除知识失败: {e}")
            return False

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
        if not self._initialized:
            await self.initialize()

        try:
            # 执行语义搜索
            results = await self._memory.search(
                query=query,
                limit=top_k,
                user_id=self.user_id,
                metadata_filter=filters
            )

            # 转换为SearchResult
            search_results = []
            for result in results:
                metadata = result.get('metadata', {})

                search_results.append(SearchResult(
                    knowledge_id=metadata.get('knowledge_id', ''),
                    content=result.get('content', ''),
                    metadata={k: v for k, v in metadata.items()
                             if k not in ['knowledge_id', 'quality_score', 'value_score']},
                    similarity_score=result.get('score', 0.0),
                    quality_score=float(metadata.get('quality_score', 0.7)),
                    value_score=float(metadata.get('value_score', 0.6))
                ))

            # 更新统计
            self._update_stats("search")

            logger.debug(f"搜索: {query} -> {len(search_results)} 结果")

            return search_results

        except Exception as e:
            logger.error(f"搜索知识失败: {e}")
            return []

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
        # Memo0的search已经是语义搜索
        return await self.search_knowledge(query, top_k, filters)

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
        if not self._initialized:
            await self.initialize()

        try:
            # 搜索空查询获取所有知识
            results = await self._memory.search(
                query="",
                limit=limit + offset,
                user_id=self.user_id
            )

            # 转换为KnowledgeItem
            knowledge_items = []
            for result in results[offset:]:
                metadata = result.get('metadata', {})

                knowledge_items.append(KnowledgeItem(
                    knowledge_id=metadata.get('knowledge_id', ''),
                    content=result.get('content', ''),
                    metadata={k: v for k, v in metadata.items()
                             if k not in ['knowledge_id', 'created_at', 'updated_at',
                                          'quality_score', 'value_score']},
                    created_at=datetime.fromisoformat(
                        metadata.get('created_at', datetime.now().isoformat())
                    ),
                    updated_at=datetime.fromisoformat(
                        metadata.get('updated_at', datetime.now().isoformat())
                    ),
                    quality_score=float(metadata.get('quality_score', 0.7)),
                    value_score=float(metadata.get('value_score', 0.6))
                ))

            return knowledge_items

        except Exception as e:
            logger.error(f"列出知识失败: {e}")
            return []

    async def count_knowledge(self) -> int:
        """统计知识数量

        Returns:
            知识总数
        """
        if not self._initialized:
            await self.initialize()

        try:
            # 使用搜索获取所有知识并计数
            results = await self._memory.search(
                query="",
                limit=100000,
                user_id=self.user_id
            )

            count = len(results)
            self.stats.total_knowledge = count

            return count

        except Exception as e:
            logger.error(f"统计知识数量失败: {e}")
            return self.stats.total_knowledge

    # ========== 维护和优化 ==========

    async def clear_all(self) -> bool:
        """清除所有知识

        Returns:
            是否成功
        """
        if not self._initialized:
            await self.initialize()

        try:
            # 获取所有知识
            all_knowledge = await self.list_knowledge(limit=1000000)

            # 删除所有知识
            for item in all_knowledge:
                await self.delete_knowledge(item.knowledge_id)

            logger.info(f"清除了所有知识: {len(all_knowledge)} 条")

            return True

        except Exception as e:
            logger.error(f"清除所有知识失败: {e}")
            return False

    # ========== 工具方法 ==========

    def _generate_knowledge_id(self, content: str) -> str:
        """生成知识ID

        Args:
            content: 知识内容

        Returns:
            知识ID
        """
        # 使用MD5哈希
        content_hash = hashlib.md5(content.encode()).hexdigest()[:12]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        return f"knowledge_{content_hash}_{timestamp}"

    async def close(self) -> None:
        """关闭存储"""
        if self._memory:
            # Memo0会自动清理资源
            self._memory = None

        self._initialized = False
        logger.info("Memo0存储已关闭")


# ========== 便捷函数 ==========

async def create_memo0_storage(
    config: Optional[Dict[str, Any]] = None
) -> Memo0Storage:
    """创建Memo0存储实例

    Args:
        config: 配置字典

    Returns:
        Memo0存储实例
    """
    if config is None:
        config = {}

    storage = Memo0Storage(config)
    await storage.initialize()

    return storage


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
    async with await create_memo0_storage(config) as storage:
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
    async with await create_memo0_storage(config) as storage:
        return await storage.search_knowledge(query, top_k)
