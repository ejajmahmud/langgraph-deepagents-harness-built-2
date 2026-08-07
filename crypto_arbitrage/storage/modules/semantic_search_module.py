"""语义搜索模块 V5.8 - 专注多维度知识检索

核心职责：
1. 多维度语义搜索 - 支持strategy/risk/market/execution四个维度
2. 智能缓存管理 - LRU缓存策略，提升搜索性能
3. 结果去重排序 - 基于内容相似度和相关性分数
4. 搜索历史跟踪 - 记录搜索模式，优化搜索策略

设计原则：
- 单一职责：专注语义搜索功能
- 高内聚性：所有方法都围绕搜索展开
- 可测试性：每个方法都可独立测试
- 性能优先：缓存和去重优化

基于：V5.7 Graphify架构优化分析
内聚性目标：0.45+
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional
from collections import OrderedDict
from datetime import datetime

logger = logging.getLogger(__name__)


class SemanticSearchModule:
    """语义搜索模块 - 专注多维度知识检索

    提供高效的多维度语义搜索功能，支持智能缓存、
    结果去重和相关性排序，大幅提升知识检索质量。
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化语义搜索模块

        Args:
            config: 配置字典，包含：
                - enable_semantic_search: 是否启用语义搜索
                - cache_ttl: 缓存TTL（秒）
                - max_cache_size: 最大缓存条目数
                - max_history: 最大搜索历史记录数
                - default_dimensions: 默认搜索维度
        """
        self.config = config
        self.enable_semantic_search = config.get('enable_semantic_search', True)

        # 缓存配置
        self._cache_ttl = config.get('cache_ttl', 300)  # 5分钟
        self._max_cache_size = config.get('max_cache_size', 100)

        # 使用OrderedDict实现LRU缓存
        self._knowledge_cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()

        # 搜索历史
        self._search_history: List[Dict[str, Any]] = []
        self._max_history = config.get('max_history', 100)

        # 默认搜索维度
        self._default_dimensions = config.get('default_dimensions', ['strategy', 'risk', 'market', 'execution'])

        # 性能统计
        self._stats = {
            'total_searches': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'avg_search_time': 0.0,
            'total_results': 0
        }

        logger.info("[OK] 语义搜索模块 V5.8 初始化完成")

    async def semantic_search(
        self,
        query: str,
        dimensions: Optional[List[str]] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """语义搜索 - 多维度知识检索

        Args:
            query: 查询内容
            dimensions: 搜索维度列表 [strategy, risk, market, execution]
            top_k: 返回结果数量

        Returns:
            知识结果列表，按相关性排序
        """
        start_time = time.time()

        # 更新统计
        self._stats['total_searches'] += 1

        # 检查是否启用语义搜索
        if not self.enable_semantic_search:
            results = await self._basic_search(query, top_k)
        else:
            # 使用默认维度或指定维度
            search_dimensions = dimensions or self._default_dimensions
            results = await self._multi_dimension_search(query, search_dimensions, top_k)

        # 更新统计
        search_time = time.time() - start_time
        self._update_search_stats(search_time, len(results))

        # 记录搜索历史
        self._record_search(query, results, search_time)

        logger.debug(f"语义搜索: {query} -> {len(results)} 结果 ({search_time:.3f}s)")
        return results

    async def _multi_dimension_search(
        self,
        query: str,
        dimensions: List[str],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """多维度搜索

        Args:
            query: 查询内容
            dimensions: 搜索维度列表
            top_k: 返回结果数量

        Returns:
            知识结果列表
        """
        all_results = []

        # 并行执行多维度搜索
        search_tasks = []
        for dimension in dimensions:
            dimension_query = f"{dimension} {query}"
            task = self._search_with_cache(dimension_query, top_k)
            search_tasks.append(task)

        # 等待所有搜索完成
        dimension_results = await asyncio.gather(*search_tasks, return_exceptions=True)

        # 收集有效结果
        for results in dimension_results:
            if isinstance(results, list):
                all_results.extend(results)
            elif isinstance(results, Exception):
                logger.error(f"维度搜索失败: {results}")

        # 去重和排序
        unique_results = self._deduplicate_results(all_results)
        ranked_results = self._rank_results(unique_results, query)

        return ranked_results[:top_k]

    async def _search_with_cache(
        self,
        query: str,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """带缓存的搜索

        Args:
            query: 查询内容
            top_k: 返回结果数量

        Returns:
            知识结果列表
        """
        cache_key = f"{query}:{top_k}"

        # 检查缓存
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            self._stats['cache_hits'] += 1
            logger.debug(f"缓存命中: {query}")
            return cached['results']

        # 缓存未命中，执行搜索
        self._stats['cache_misses'] += 1
        results = await self._execute_search(query, top_k)

        # 更新缓存
        if results:
            self._update_cache(cache_key, {
                'results': results,
                'timestamp': time.time()
            })

        return results

    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """从缓存获取数据

        Args:
            cache_key: 缓存键

        Returns:
            缓存数据或None
        """
        if cache_key not in self._knowledge_cache:
            return None

        cached = self._knowledge_cache[cache_key]

        # 检查是否过期
        if time.time() - cached['timestamp'] > self._cache_ttl:
            del self._knowledge_cache[cache_key]
            return None

        # LRU: 移动到末尾
        self._knowledge_cache.move_to_end(cache_key)
        return cached

    def _update_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """更新缓存

        Args:
            cache_key: 缓存键
            data: 要缓存的数据
        """
        # 如果缓存已满，删除最旧的条目
        if len(self._knowledge_cache) >= self._max_cache_size:
            self._knowledge_cache.popitem(last=False)

        # 添加新缓存
        self._knowledge_cache[cache_key] = data

        # LRU: 移动到末尾
        self._knowledge_cache.move_to_end(cache_key)

    async def _execute_search(
        self,
        query: str,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """执行实际搜索

        Args:
            query: 查询内容
            top_k: 返回结果数量

        Returns:
            知识结果列表
        """
        try:
            from storage.mem0_storage import search_trading_knowledge
            results = search_trading_knowledge(query, top_k=top_k)
            return results if results else []
        except Exception as e:
            logger.error(f"搜索执行失败: {e}")
            return []

    async def _basic_search(
        self,
        query: str,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """基础搜索（不使用多维度）

        Args:
            query: 查询内容
            top_k: 返回结果数量

        Returns:
            知识结果列表
        """
        return await self._execute_search(query, top_k)

    def _deduplicate_results(
        self,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """去重知识结果

        Args:
            results: 原始结果列表

        Returns:
            去重后的结果列表
        """
        seen_contents = set()
        unique_results = []

        for result in results:
            content = result.get('content', '')
            if content and content not in seen_contents:
                seen_contents.add(content)
                unique_results.append(result)

        return unique_results

    def _rank_results(
        self,
        results: List[Dict[str, Any]],
        query: str
    ) -> List[Dict[str, Any]]:
        """排序知识结果

        Args:
            results: 知识结果列表
            query: 原始查询

        Returns:
            排序后的结果列表
        """
        # 按相关性分数排序
        return sorted(
            results,
            key=lambda x: x.get('score', 0),
            reverse=True
        )

    def _record_search(
        self,
        query: str,
        results: List[Dict[str, Any]],
        search_time: float
    ) -> None:
        """记录搜索历史

        Args:
            query: 查询内容
            results: 搜索结果
            search_time: 搜索耗时
        """
        record = {
            'query': query,
            'result_count': len(results),
            'search_time': search_time,
            'timestamp': time.time(),
            'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        self._search_history.append(record)

        # 限制历史大小
        if len(self._search_history) > self._max_history:
            self._search_history = self._search_history[-self._max_history:]

    def _update_search_stats(self, search_time: float, result_count: int) -> None:
        """更新搜索统计

        Args:
            search_time: 搜索耗时
            result_count: 结果数量
        """
        # 更新平均搜索时间
        total_searches = self._stats['total_searches']
        current_avg = self._stats['avg_search_time']
        self._stats['avg_search_time'] = (
            (current_avg * (total_searches - 1) + search_time) / total_searches
        )

        # 更新总结果数
        self._stats['total_results'] += result_count

    def clear_cache(self) -> None:
        """清除缓存"""
        self._knowledge_cache.clear()
        logger.info("语义搜索缓存已清除")

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计

        Returns:
            缓存统计数据
        """
        return {
            'cache_size': len(self._knowledge_cache),
            'max_cache_size': self._max_cache_size,
            'cache_ttl': self._cache_ttl,
            'cache_usage': len(self._knowledge_cache) / self._max_cache_size if self._max_cache_size > 0 else 0
        }

    def get_search_stats(self) -> Dict[str, Any]:
        """获取搜索统计

        Returns:
            搜索统计数据
        """
        total_requests = self._stats['cache_hits'] + self._stats['cache_misses']
        cache_hit_rate = (
            self._stats['cache_hits'] / total_requests
            if total_requests > 0 else 0
        )

        return {
            'total_searches': self._stats['total_searches'],
            'cache_hits': self._stats['cache_hits'],
            'cache_misses': self._stats['cache_misses'],
            'cache_hit_rate': cache_hit_rate,
            'avg_search_time': self._stats['avg_search_time'],
            'avg_results_per_search': (
                self._stats['total_results'] / self._stats['total_searches']
                if self._stats['total_searches'] > 0 else 0
            ),
            'total_results': self._stats['total_results']
        }

    def get_search_history(
        self,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取搜索历史

        Args:
            limit: 返回记录数量

        Returns:
            搜索历史记录
        """
        return self._search_history[-limit:]

    def export_cache(self) -> Dict[str, Any]:
        """导出缓存

        Returns:
            缓存数据字典
        """
        return {
            'cache': dict(self._knowledge_cache),
            'search_history': self._search_history,
            'stats': self._stats,
            'timestamp': time.time()
        }

    def import_cache(self, data: Dict[str, Any]) -> None:
        """导入缓存

        Args:
            data: 缓存数据字典
        """
        if 'cache' in data:
            self._knowledge_cache = OrderedDict(data['cache'])
        if 'search_history' in data:
            self._search_history = data['search_history']
        if 'stats' in data:
            self._stats = data['stats']

        logger.info("语义搜索缓存数据已导入")

    def reset_stats(self) -> None:
        """重置统计"""
        self._stats = {
            'total_searches': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'avg_search_time': 0.0,
            'total_results': 0
        }
        logger.info("语义搜索统计已重置")


def create_semantic_search_module(config: Dict[str, Any]) -> SemanticSearchModule:
    """创建语义搜索模块

    Args:
        config: 配置字典

    Returns:
        语义搜索模块实例
    """
    return SemanticSearchModule(config)
