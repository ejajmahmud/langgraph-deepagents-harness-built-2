"""统一缓存管理器 V3.8
高性能、智能化的统一缓存系统
"""

import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from collections import OrderedDict
from enum import Enum
import threading

logger = logging.getLogger(__name__)


class CachePolicy(Enum):
    """缓存策略"""
    LRU = "LRU"  # 最近最少使用
    TTL = "TTL"  # 基于时间
    HYBRID = "HYBRID"  # 混合策略


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    timestamp: float
    ttl: float  # 生存时间（秒）
    access_count: int = 0
    last_access: float = 0.0
    size: int = 0

    def is_expired(self) -> bool:
        """检查是否过期"""
        return time.time() - self.timestamp > self.ttl

    def update_access(self):
        """更新访问信息"""
        self.access_count += 1
        self.last_access = time.time()


class UnifiedCacheManager:
    """统一缓存管理器 V3.8

    提供高性能、智能化的统一缓存服务，支持多种缓存策略。
    核心功能：
    1. 统一缓存接口 - 替代各模块独立缓存
    2. 智能缓存策略 - LRU/TTL/混合策略
    3. 缓存预热机制 - 提前加载热点数据
    4. 缓存监控和优化 - 实时监控命中率
    """

    def __init__(
        self,
        max_size: int = 10000,
        default_ttl: float = 300,
        cache_policy: CachePolicy = CachePolicy.HYBRID,
        enable_stats: bool = True
    ):
        """初始化统一缓存管理器

        Args:
            max_size: 最大缓存条目数
            default_ttl: 默认生存时间（秒）
            cache_policy: 缓存策略
            enable_stats: 是否启用统计
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache_policy = cache_policy
        self.enable_stats = enable_stats

        # 缓存存储
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order = OrderedDict()  # LRU 顺序
        self._lock = threading.RLock()

        # 统计信息
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_requests': 0
        }

        # 预热队列
        self._warmup_queue: List[Tuple[str, Callable]] = []

        logger.info(f"统一缓存管理器初始化完成 - 策略: {cache_policy.value}, 最大条目: {max_size}")

    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """生成缓存键

        Args:
            prefix: 键前缀
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            缓存键
        """
        # 将参数序列化为字符串
        key_parts = [prefix]

        if args:
            key_parts.extend(str(arg) for arg in args)

        if kwargs:
            # 按键排序以确保一致性
            sorted_kwargs = sorted(kwargs.items())
            key_parts.extend(f"{k}={v}" for k, v in sorted_kwargs)

        key_str = "|".join(key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()

    async def get(
        self,
        prefix: str,
        *args,
        default: Any = None,
        **kwargs
    ) -> Optional[Any]:
        """获取缓存值

        Args:
            prefix: 键前缀
            *args: 位置参数
            default: 默认值
            **kwargs: 关键字参数

        Returns:
            缓存值或默认值
        """
        if self.enable_stats:
            self._stats['total_requests'] += 1

        key = self._generate_key(prefix, *args, **kwargs)

        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                if self.enable_stats:
                    self._stats['misses'] += 1
                return default

            if entry.is_expired():
                # 过期删除
                del self._cache[key]
                if key in self._access_order:
                    del self._access_order[key]
                if self.enable_stats:
                    self._stats['misses'] += 1
                return default

            # 更新访问信息
            entry.update_access()

            # 更新 LRU 顺序
            if self.cache_policy in [CachePolicy.LRU, CachePolicy.HYBRID]:
                self._access_order.move_to_end(key)

            if self.enable_stats:
                self._stats['hits'] += 1

            return entry.value

    async def set(
        self,
        prefix: str,
        value: Any,
        *args,
        ttl: Optional[float] = None,
        **kwargs
    ) -> bool:
        """设置缓存值

        Args:
            prefix: 键前缀
            value: 缓存值
            *args: 位置参数
            ttl: 生存时间（秒）
            **kwargs: 关键字参数

        Returns:
            是否成功
        """
        key = self._generate_key(prefix, *args, **kwargs)
        actual_ttl = ttl if ttl is not None else self.default_ttl

        # 计算值大小（近似）
        value_size = len(str(value)) if value is not None else 0

        with self._lock:
            # 检查是否需要清理
            if len(self._cache) >= self.max_size:
                await self._evict()

            entry = CacheEntry(
                key=key,
                value=value,
                timestamp=time.time(),
                ttl=actual_ttl,
                size=value_size
            )

            self._cache[key] = entry
            self._access_order[key] = entry.timestamp

            logger.debug(f"缓存设置成功: {key} (TTL: {actual_ttl}s)")

        return True

    async def delete(self, prefix: str, *args, **kwargs) -> bool:
        """删除缓存值

        Args:
            prefix: 键前缀
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            是否成功
        """
        key = self._generate_key(prefix, *args, **kwargs)

        with self._lock:
            if key in self._cache:
                del self._cache[key]
                if key in self._access_order:
                    del self._access_order[key]
                return True
            return False

    async def clear(self, prefix: Optional[str] = None) -> int:
        """清理缓存

        Args:
            prefix: 键前缀，如果为 None 则清理全部

        Returns:
            清理的条目数
        """
        with self._lock:
            if prefix is None:
                # 清理全部
                count = len(self._cache)
                self._cache.clear()
                self._access_order.clear()
                logger.info(f"清理全部缓存: {count} 条目")
                return count

            # 清理指定前缀的缓存
            keys_to_delete = [k for k in self._cache.keys() if k.startswith(prefix)]
            for key in keys_to_delete:
                del self._cache[key]
                if key in self._access_order:
                    del self._access_order[key]

            logger.info(f"清理前缀 '{prefix}' 缓存: {len(keys_to_delete)} 条目")
            return len(keys_to_delete)

    async def _evict(self) -> int:
        """清理过期或最少使用的缓存

        Returns:
            清理的条目数
        """
        evicted = 0
        now = time.time()

        with self._lock:
            # 先清理过期条目
            expired_keys = [
                k for k, entry in self._cache.items()
                if entry.is_expired()
            ]

            for key in expired_keys:
                del self._cache[key]
                if key in self._access_order:
                    del self._access_order[key]
                evicted += 1

            # 如果还需要清理，按 LRU 策略清理
            if len(self._cache) >= self.max_size and evicted == 0:
                if self.cache_policy in [CachePolicy.LRU, CachePolicy.HYBRID]:
                    # 清理最少使用的
                    lru_key = next(iter(self._access_order))
                    del self._cache[lru_key]
                    del self._access_order[lru_key]
                    evicted += 1
                elif self.cache_policy == CachePolicy.TTL:
                    # 清理最早的
                    oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].timestamp)
                    del self._cache[oldest_key]
                    del self._access_order[oldest_key]
                    evicted += 1

            if evicted > 0:
                self._stats['evictions'] += evicted

        return evicted

    async def warmup(self, warmup_data: List[Tuple[str, Callable]]) -> None:
        """缓存预热

        Args:
            warmup_data: 预热数据列表，每个元素为 (key, data_loader) 元组
        """
        logger.info(f"开始缓存预热: {len(warmup_data)} 条目")

        warmup_tasks = []
        for key, data_loader in warmup_data:
            task = self._load_warmup_data(key, data_loader)
            warmup_tasks.append(task)

        await asyncio.gather(*warmup_tasks, return_exceptions=True)

        logger.info("缓存预热完成")

    async def _load_warmup_data(self, key: str, data_loader: Callable) -> None:
        """加载预热数据

        Args:
            key: 缓存键
            data_loader: 数据加载函数
        """
        try:
            data = await data_loader() if asyncio.iscoroutinefunction(data_loader) else data_loader()
            await self.set(key, data, ttl=self.default_ttl * 2)  # 预热数据使用更长 TTL
        except Exception as e:
            logger.error(f"预热数据加载失败: {key} - {e}")

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息

        Returns:
            统计信息字典
        """
        total_requests = self._stats['total_requests']
        hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0.0

        return {
            'total_entries': len(self._cache),
            'max_size': self.max_size,
            'hits': self._stats['hits'],
            'misses': self._stats['misses'],
            'evictions': self._stats['evictions'],
            'hit_rate': hit_rate,
            'total_requests': total_requests
        }

    def get_size_info(self) -> Dict[str, Any]:
        """获取缓存大小信息

        Returns:
            大小信息字典
        """
        with self._lock:
            total_size = sum(entry.size for entry in self._cache.values())
            avg_size = total_size / len(self._cache) if self._cache else 0

            return {
                'total_size': total_size,
                'average_size': avg_size,
                'usage_percentage': (len(self._cache) / self.max_size * 100) if self.max_size > 0 else 0
            }

    async def optimize_cache(self) -> None:
        """优化缓存性能

        自动清理过期条目，调整缓存策略
        """
        logger.info("开始缓存优化")

        # 清理过期条目
        await self._evict()

        # 分析命中率，调整策略
        stats = self.get_stats()
        hit_rate = stats['hit_rate']

        if hit_rate < 50:
            logger.warning(f"缓存命中率较低 ({hit_rate:.1f}%)，建议调整 TTL 或增加缓存大小")
        elif hit_rate > 90:
            logger.info(f"缓存命中率优秀 ({hit_rate:.1f}%)")

        logger.info("缓存优化完成")

    async def start_background_tasks(self, interval: float = 60.0) -> None:
        """启动后台任务

        Args:
            interval: 优化间隔（秒）
        """
        async def optimization_loop():
            while True:
                try:
                    await asyncio.sleep(interval)
                    await self.optimize_cache()
                except Exception as e:
                    logger.error(f"后台优化任务异常: {e}")

        asyncio.create_task(optimization_loop())
        logger.info(f"后台优化任务已启动 - 间隔: {interval}s")


# 创建全局统一缓存管理器实例
_global_cache_manager: Optional[UnifiedCacheManager] = None


def initialize_unified_cache(
    max_size: int = 10000,
    default_ttl: float = 300,
    cache_policy: CachePolicy = CachePolicy.HYBRID,
    enable_stats: bool = True
) -> UnifiedCacheManager:
    """初始化全局统一缓存管理器

    Args:
        max_size: 最大缓存条目数
        default_ttl: 默认生存时间（秒）
        cache_policy: 缓存策略
        enable_stats: 是否启用统计

    Returns:
        统一缓存管理器实例
    """
    global _global_cache_manager
    _global_cache_manager = UnifiedCacheManager(
        max_size=max_size,
        default_ttl=default_ttl,
        cache_policy=cache_policy,
        enable_stats=enable_stats
    )
    return _global_cache_manager


def get_unified_cache() -> Optional[UnifiedCacheManager]:
    """获取全局统一缓存管理器实例

    Returns:
        统一缓存管理器实例，如果未初始化则返回 None
    """
    return _global_cache_manager
