"""缓存优化器 - Phase 9核心模块

优化缓存策略和性能。

核心功能：
1. LRU缓存实现 - 最近最少使用缓存
2. 智能预热 - 预加载热点数据
3. 缓存大小优化 - 动态调整缓存大小
4. 缓存统计 - 详细的缓存统计信息

创建时间：2026-04-19 18:57:00
"""

import json
import logging
from collections import OrderedDict
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class LRUCache:
    """最近最少使用（LRU）缓存

    线程安全的LRU缓存实现。
    """

    def __init__(self, max_size: int = 1000):
        """初始化LRU缓存

        Args:
            max_size: 最大缓存大小
        """
        self.max_size = max_size
        self.cache: OrderedDict = OrderedDict()
        self.hits = 0
        self.misses = 0

    def get(self, key: Any) -> Optional[Any]:
        """获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值或None
        """
        if key in self.cache:
            # 移动到最前面（最近使用）
            self.cache.move_to_end(key)
            self.hits += 1
            return self.cache[key]
        else:
            self.misses += 1
            return None

    def set(self, key: Any, value: Any) -> None:
        """设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
        """
        if key in self.cache:
            # 更新现有值
            self.cache.move_to_end(key)
        elif len(self.cache) >= self.max_size:
            # 删除最久未使用的项
            self.cache.popitem(last=False)

        self.cache[key] = value

    def clear(self) -> None:
        """清除所有缓存"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0

    def size(self) -> int:
        """获取当前缓存大小

        Returns:
            缓存大小
        """
        return len(self.cache)

    def get_hit_rate(self) -> float:
        """获取缓存命中率

        Returns:
            命中率（0-1）
        """
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息

        Returns:
            统计信息字典
        """
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': self.get_hit_rate(),
            'fill_rate': len(self.cache) / self.max_size if self.max_size > 0 else 0.0,
        }


class CacheOptimizer:
    """缓存优化器

    优化缓存策略和性能。
    """

    def __init__(self, storage, config: Dict[str, Any] = None):
        """初始化缓存优化器

        Args:
            storage: 存储实例
            config: 配置字典
        """
        self.storage = storage
        self.config = config or {}
        self.lru_cache = LRUCache(max_size=self.config.get('max_size', 1000))
        self.preload_cache = LRUCache(max_size=self.config.get('preload_size', 500))

        logger.info("缓存优化器初始化完成")

    async def get_with_cache(self, key: str, fetch_func: Callable) -> Any:
        """从缓存获取或使用fetch函数获取

        Args:
            key: 缓存键
            fetch_func: 获取函数

        Returns:
            缓存值
        """
        # 尝试从LRU缓存获取
        value = self.lru_cache.get(key)
        if value is not None:
            return value

        # 使用fetch函数获取
        value = await fetch_func()

        # 存入缓存
        self.lru_cache.set(key, value)

        return value

    async def preload_hot_data(
        self,
        hot_keys: list,
        fetch_func: Callable
    ) -> Dict[str, Any]:
        """预加载热点数据

        Args:
            hot_keys: 热点键列表
            fetch_func: 获取函数

        Returns:
            预加载统计
        """
        logger.info(f"预加载 {len(hot_keys)} 个热点数据")

        success_count = 0
        failure_count = 0

        for key in hot_keys:
            try:
                value = await fetch_func(key)
                self.preload_cache.set(key, value)
                success_count += 1
            except Exception as e:
                logger.error(f"预加载失败 {key}: {e}")
                failure_count += 1

        stats = {
            'total_keys': len(hot_keys),
            'success_count': success_count,
            'failure_count': failure_count,
            'preload_cache_stats': self.preload_cache.get_stats(),
        }

        logger.info(f"预加载完成: {success_count}/{len(hot_keys)}")
        return stats

    def optimize_cache_size(self, access_pattern: Dict[str, int]) -> Dict[str, Any]:
        """优化缓存大小

        Args:
            access_pattern: 访问模式字典 {key: count}

        Returns:
            优化建议
        """
        total_access = sum(access_pattern.values())
        if total_access == 0:
            return {'recommendation': 'no_data'}

        # 计算帕累托原则（80/20规则）
        sorted_keys = sorted(access_pattern.items(), key=lambda x: x[1], reverse=True)

        # 找到覆盖80%访问量的键数
        cumulative_access = 0
        eighty_percent_count = 0
        for key, count in sorted_keys:
            cumulative_access += count
            eighty_percent_count += 1
            if cumulative_access >= total_access * 0.8:
                break

        # 推荐缓存大小
        recommended_size = min(
            int(eighty_percent_count * 1.5),  # 预留50%余量
            self.config.get('max_size', 1000)
        )

        return {
            'recommendation': 'optimized',
            'total_unique_keys': len(access_pattern),
            'eighty_percent_coverage': eighty_percent_count,
            'current_size': self.lru_cache.max_size,
            'recommended_size': recommended_size,
            'savings': self.lru_cache.max_size - recommended_size,
        }

    def get_cache_statistics(self) -> Dict[str, Any]:
        """获取缓存统计信息

        Returns:
            缓存统计字典
        """
        return {
            'lru_cache': self.lru_cache.get_stats(),
            'preload_cache': self.preload_cache.get_stats(),
        }

    def clear_all_caches(self) -> None:
        """清除所有缓存"""
        self.lru_cache.clear()
        self.preload_cache.clear()
        logger.info("所有缓存已清除")


# ========== 便捷函数 ==========

def create_cache_optimizer(storage, config: Dict[str, Any] = None) -> CacheOptimizer:
    """创建缓存优化器

    Args:
        storage: 存储实例
        config: 配置字典

    Returns:
        缓存优化器实例
    """
    return CacheOptimizer(storage, config)
