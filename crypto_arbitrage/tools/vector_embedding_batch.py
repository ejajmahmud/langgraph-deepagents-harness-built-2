"""向量嵌入批处理优化 - V5.10 Phase 5.1

实现高效的向量嵌入生成和批量搜索，优化Memo0语义搜索性能。

核心功能：
1. 批量向量生成（减少API调用次数）
2. 向量缓存（避免重复计算）
3. 批量相似度搜索
4. 智能批处理策略

创建时间：2026-04-19
"""

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingCacheEntry:
    """向量嵌入缓存条目"""
    embedding: np.ndarray
    timestamp: float
    hash: str

    @property
    def age(self) -> float:
        """缓存年龄（秒）"""
        return time.time() - self.timestamp


@dataclass
class BatchRequest:
    """批处理请求"""
    texts: List[str]
    batch_id: int
    timestamp: float
    callback: Optional[Callable[[List[np.ndarray]], Awaitable[None]]] = None


class VectorEmbeddingBatchOptimizer:
    """向量嵌入批处理优化器"""

    def __init__(
        self,
        batch_size: int = 10,
        max_delay: float = 2.0,
        cache_ttl: float = 3600.0,
        embedding_dim: int = 1536
    ):
        """初始化批处理优化器

        Args:
            batch_size: 批处理大小（默认10条文本）
            max_delay: 最大批处理延迟（秒）
            cache_ttl: 缓存过期时间（秒），默认1小时
            embedding_dim: 向量维度，默认1536（OpenAI ada-002）
        """
        self.batch_size = batch_size
        self.max_delay = max_delay
        self.cache_ttl = cache_ttl
        self.embedding_dim = embedding_dim

        # 缓存系统
        self._cache: Dict[str, EmbeddingCacheEntry] = {}

        # 批处理队列
        self._pending_requests: List[BatchRequest] = []
        self._batch_counter = 0
        self._last_flush_time: float = 0.0

        # 统计信息
        self._stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'batch_requests': 0,
            'single_requests': 0,
            'total_texts': 0,
            'batch_avg_size': 0.0
        }

        # 后台任务
        self._batch_task: Optional[asyncio.Task] = None
        self._running = False

        # 嵌入函数（需要外部设置）
        self._embedding_func: Optional[Callable[[List[str]], Awaitable[List[np.ndarray]]]] = None

    # -------------------- 配置方法 --------------------

    def set_embedding_function(
        self,
        func: Callable[[List[str]], Awaitable[List[np.ndarray]]]
    ) -> None:
        """设置向量生成函数

        Args:
            func: 批量生成向量的异步函数，输入文本列表，返回向量列表
        """
        self._embedding_func = func
        logger.info("向量生成函数已设置")

    # -------------------- 缓存管理 --------------------

    def _make_cache_key(self, text: str) -> str:
        """生成缓存键"""
        # 使用文本的哈希值作为缓存键
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def _get_from_cache(self, text: str) -> Optional[np.ndarray]:
        """从缓存获取向量

        Args:
            text: 输入文本

        Returns:
            向量数组，如果缓存未命中则返回None
        """
        cache_key = self._make_cache_key(text)
        cached = self._cache.get(cache_key)

        if cached and cached.age < self.cache_ttl:
            cached.timestamp = time.time()  # 更新访问时间
            self._stats['cache_hits'] += 1
            return cached.embedding.copy()

        self._stats['cache_misses'] += 1
        return None

    def _save_to_cache(self, text: str, embedding: np.ndarray) -> None:
        """保存向量到缓存

        Args:
            text: 输入文本
            embedding: 向量数组
        """
        cache_key = self._make_cache_key(text)
        self._cache[cache_key] = EmbeddingCacheEntry(
            embedding=embedding.copy(),
            timestamp=time.time(),
            hash=cache_key
        )

    # -------------------- 向量生成 --------------------

    async def get_embedding(
        self,
        text: str,
        use_batch: bool = True
    ) -> Optional[np.ndarray]:
        """获取单个文本的向量嵌入

        Args:
            text: 输入文本
            use_batch: 是否使用批处理（默认True）

        Returns:
            向量数组
        """
        # 检查缓存
        cached = self._get_from_cache(text)
        if cached is not None:
            logger.debug(f"向量缓存命中: {text[:30]}...")
            return cached

        # 缓存未命中
        if use_batch and self._embedding_func is not None:
            # 使用批处理
            future = await self._add_to_batch(text)
            embedding = await future
            return embedding
        else:
            # 直接生成（单次请求）
            if self._embedding_func is None:
                logger.warning("向量生成函数未设置，返回模拟向量")
                self._stats['single_requests'] += 1  # 即使是模拟也要计数
                return np.random.rand(self.embedding_dim).astype(np.float32)

            self._stats['single_requests'] += 1
            embeddings = await self._embedding_func([text])
            if embeddings:
                embedding = embeddings[0]
                self._save_to_cache(text, embedding)
                return embedding

        return None

    async def get_embeddings_batch(
        self,
        texts: List[str],
        use_batch: bool = True
    ) -> List[Optional[np.ndarray]]:
        """批量获取向量嵌入

        Args:
            texts: 输入文本列表
            use_batch: 是否使用批处理（默认True）

        Returns:
            向量数组列表
        """
        results = []

        # 检查缓存
        cache_hits = []
        cache_misses = []

        for i, text in enumerate(texts):
            cached = self._get_from_cache(text)
            if cached is not None:
                cache_hits.append((i, cached))
            else:
                cache_misses.append((i, text))

        # 处理缓存未命中的文本
        if cache_misses:
            missed_texts = [text for _, text in cache_misses]

            if use_batch and self._embedding_func is not None:
                # 使用批处理
                batch_future = await self._add_to_batch_batch(missed_texts)
                embeddings = await batch_future

                # 保存到缓存
                for (idx, text), embedding in zip(cache_misses, embeddings):
                    self._save_to_cache(text, embedding)
                    results.append(embedding)
            else:
                # 单次请求
                if self._embedding_func is None:
                    logger.warning("向量生成函数未设置，返回模拟向量")
                    embeddings = [
                        np.random.rand(self.embedding_dim).astype(np.float32)
                        for _ in missed_texts
                    ]
                else:
                    self._stats['single_requests'] += len(missed_texts)
                    embeddings = await self._embedding_func(missed_texts)

                for (idx, text), embedding in zip(cache_misses, embeddings):
                    self._save_to_cache(text, embedding)
                    results.append(embedding)

        # 合并结果
        final_results = [None] * len(texts)
        for i, embedding in cache_hits:
            final_results[i] = embedding

        miss_idx = 0
        for idx, text in cache_misses:
            final_results[idx] = results[miss_idx]
            miss_idx += 1

        return final_results

    # -------------------- 批处理管理 --------------------

    async def _add_to_batch(self, text: str) -> asyncio.Future:
        """添加单个文本到批处理队列

        Args:
            text: 输入文本

        Returns:
            Future对象，将在向量生成完成后返回
        """
        future = asyncio.Future()
        batch_id = self._batch_counter
        self._batch_counter += 1

        request = BatchRequest(
            texts=[text],
            batch_id=batch_id,
            timestamp=time.time(),
            callback=lambda emb: future.set_result(emb[0])
        )

        self._pending_requests.append(request)
        self._stats['batch_requests'] += 1

        # 检查是否需要立即批处理
        now = time.time()
        should_flush = (
            len(self._pending_requests) >= self.batch_size or
            now - self._last_flush_time >= self.max_delay
        )

        if should_flush:
            asyncio.create_task(self._flush_batch())

        return future

    async def _add_to_batch_batch(self, texts: List[str]) -> asyncio.Future:
        """添加多个文本到批处理队列

        Args:
            texts: 输入文本列表

        Returns:
            Future对象，将在向量生成完成后返回
        """
        future = asyncio.Future()
        batch_id = self._batch_counter
        self._batch_counter += 1

        request = BatchRequest(
            texts=texts,
            batch_id=batch_id,
            timestamp=time.time(),
            callback=lambda emb: future.set_result(emb)
        )

        self._pending_requests.append(request)
        self._stats['batch_requests'] += len(texts)
        self._stats['total_texts'] += len(texts)

        # 检查是否需要立即批处理
        now = time.time()
        should_flush = (
            len(self._pending_requests) >= self.batch_size or
            now - self._last_flush_time >= self.max_delay
        )

        if should_flush:
            asyncio.create_task(self._flush_batch())

        return future

    async def _flush_batch(self) -> None:
        """执行批处理"""
        if not self._pending_requests or self._embedding_func is None:
            return

        # 获取所有待处理的文本
        all_texts = []
        for request in self._pending_requests:
            all_texts.extend(request.texts)

        if not all_texts:
            return

        try:
            # 批量生成向量
            start_time = time.time()
            all_embeddings = await self._embedding_func(all_texts)
            elapsed = time.time() - start_time

            logger.info(
                f"批量生成向量: {len(all_texts)}条文本, "
                f"耗时{elapsed:.3f}秒"
            )

            # 分发结果到各个请求
            embedding_idx = 0
            for request in self._pending_requests:
                embeddings = all_embeddings[
                    embedding_idx:embedding_idx + len(request.texts)
                ]

                if request.callback:
                    try:
                        result = request.callback(embeddings)
                        if asyncio.iscoroutine(result):
                            await result
                    except Exception as e:
                        logger.warning(f"Callback执行失败: {e}")

                embedding_idx += len(request.texts)

            # 清空队列
            self._pending_requests.clear()
            self._last_flush_time = time.time()

            # 更新统计
            avg_batch_size = self._stats['total_texts'] / max(
                self._stats['batch_requests'], 1
            )
            self._stats['batch_avg_size'] = avg_batch_size

        except Exception as e:
            logger.error(f"批量向量生成失败: {e}")
            # 清空队列，避免后续请求阻塞
            for request in self._pending_requests:
                if request.callback:
                    # 返回模拟向量作为后备
                    mock_embeddings = [
                        np.random.rand(self.embedding_dim).astype(np.float32)
                        for _ in request.texts
                    ]
                    try:
                        result = request.callback(mock_embeddings)
                        if asyncio.iscoroutine(result):
                            await result
                    except Exception:
                        pass  # 忽略future错误
            self._pending_requests.clear()
            self._last_flush_time = time.time()

    # -------------------- 相似度搜索 --------------------

    @staticmethod
    def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度

        Args:
            vec1: 向量1
            vec2: 向量2

        Returns:
            相似度值（-1到1之间）
        """
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return np.dot(vec1, vec2) / (norm1 * norm2)

    @staticmethod
    def euclidean_distance(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算欧几里得距离

        Args:
            vec1: 向量1
            vec2: 向量2

        Returns:
            距离值（0到+∞）
        """
        return np.linalg.norm(vec1 - vec2)

    async def search_similar(
        self,
        query: str,
        candidates: List[Tuple[str, Any]],
        top_k: int = 5,
        similarity_metric: str = 'cosine'
    ) -> List[Tuple[str, Any, float]]:
        """搜索最相似的候选文本

        Args:
            query: 查询文本
            candidates: 候选文本列表，每个元素为 (text, metadata)
            top_k: 返回前K个结果
            similarity_metric: 相似度度量 ('cosine' 或 'euclidean')

        Returns:
            排序后的结果列表，每个元素为 (text, metadata, score)
        """
        # 获取查询向量
        query_embedding = await self.get_embedding(query)
        if query_embedding is None:
            logger.warning("无法生成查询向量")
            return []

        # 批量获取候选向量
        candidate_texts = [text for text, _ in candidates]
        candidate_embeddings = await self.get_embeddings_batch(candidate_texts)

        # 计算相似度
        results = []
        for i, (text, metadata) in enumerate(candidates):
            embedding = candidate_embeddings[i]
            if embedding is None:
                continue

            if similarity_metric == 'cosine':
                score = self.cosine_similarity(query_embedding, embedding)
            elif similarity_metric == 'euclidean':
                distance = self.euclidean_distance(query_embedding, embedding)
                score = -distance  # 距离越小分数越高
            else:
                logger.warning(f"未知的相似度度量: {similarity_metric}")
                continue

            results.append((text, metadata, score))

        # 排序并返回前K个结果
        if similarity_metric == 'euclidean':
            # 欧几里得距离：分数越高越好（取负值）
            results.sort(key=lambda x: x[2], reverse=True)
        else:
            # 余弦相似度：分数越高越好
            results.sort(key=lambda x: x[2], reverse=True)

        return results[:top_k]

    # -------------------- 缓存管理 --------------------

    def invalidate_cache(self, text: Optional[str] = None) -> None:
        """失效缓存

        Args:
            text: 指定文本，如果为None则清空所有缓存
        """
        if text is None:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"清空所有向量缓存: {count}条")
        else:
            cache_key = self._make_cache_key(text)
            if cache_key in self._cache:
                del self._cache[cache_key]
                logger.debug(f"失效向量缓存: {text[:30]}...")

    def cleanup_expired_cache(self) -> int:
        """清理过期缓存

        Returns:
            清理的缓存条目数
        """
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.age >= self.cache_ttl
        ]

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.info(f"清理过期向量缓存: {len(expired_keys)}条")

        return len(expired_keys)

    # -------------------- 统计信息 --------------------

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息

        Returns:
            统计信息字典
        """
        cache_hit_rate = 0.0
        if self._stats['cache_hits'] + self._stats['cache_misses'] > 0:
            cache_hit_rate = self._stats['cache_hits'] / (
                self._stats['cache_hits'] + self._stats['cache_misses']
            )

        return {
            'cache': {
                'size': len(self._cache),
                'hits': self._stats['cache_hits'],
                'misses': self._stats['cache_misses'],
                'hit_rate': cache_hit_rate,
                'ttl': self.cache_ttl
            },
            'batch': {
                'pending_requests': len(self._pending_requests),
                'batch_requests': self._stats['batch_requests'],
                'single_requests': self._stats['single_requests'],
                'total_texts': self._stats['total_texts'],
                'avg_batch_size': self._stats['batch_avg_size'],
                'batch_size': self.batch_size,
                'max_delay': self.max_delay
            },
            'config': {
                'embedding_dim': self.embedding_dim
            }
        }

    # -------------------- 生命周期管理 --------------------

    async def start(self) -> None:
        """启动批处理优化器"""
        if self._running:
            return

        self._running = True
        logger.info("向量嵌入批处理优化器已启动")

    async def stop(self) -> None:
        """停止批处理优化器"""
        if not self._running:
            return

        self._running = False

        # 处理剩余的批处理请求
        if self._pending_requests:
            logger.info(f"处理剩余批处理请求: {len(self._pending_requests)}个")
            await self._flush_batch()

        logger.info("向量嵌入批处理优化器已停止")


# 全局批处理优化器实例
_global_optimizer: Optional[VectorEmbeddingBatchOptimizer] = None


def get_global_optimizer() -> VectorEmbeddingBatchOptimizer:
    """获取全局批处理优化器实例"""
    global _global_optimizer
    if _global_optimizer is None:
        _global_optimizer = VectorEmbeddingBatchOptimizer()
    return _global_optimizer


def set_global_optimizer(optimizer: VectorEmbeddingBatchOptimizer) -> None:
    """设置全局批处理优化器实例"""
    global _global_optimizer
    _global_optimizer = optimizer


# 辅助函数：模拟向量生成（用于测试）
async def mock_embedding_function(
    texts: List[str],
    dim: int = 1536
) -> List[np.ndarray]:
    """模拟向量生成函数（用于测试）

    Args:
        texts: 输入文本列表
        dim: 向量维度

    Returns:
        随机生成的向量列表
    """
    await asyncio.sleep(0.1)  # 模拟网络延迟
    return [
        np.random.rand(dim).astype(np.float32)
        for _ in texts
    ]
