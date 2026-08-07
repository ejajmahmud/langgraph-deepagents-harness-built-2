"""搜索缓存系统 - V5.10 Phase 5.1

实现高性能缓存层，减少重复查询和Memo0写入开销。

核心功能：
1. 价格数据缓存（TTL=5秒）
2. 交易费用缓存（TTL=24小时）
3. 批量Memo0写入
4. 缓存命中率统计

创建时间：2026-04-19
"""

import asyncio
import hashlib
import json
import logging
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """缓存条目"""
    data: Any
    timestamp: float
    hits: int = 0

    @property
    def age(self) -> float:
        """缓存年龄（秒）"""
        return time.time() - self.timestamp


class SearchCache:
    """高性能搜索缓存系统"""

    def __init__(
        self,
        price_ttl: float = 5.0,
        fee_ttl: float = 86400.0,
        batch_size: int = 10,
        batch_max_delay: float = 5.0
    ):
        """初始化搜索缓存

        Args:
            price_ttl: 价格数据缓存过期时间（秒），默认5秒
            fee_ttl: 费用数据缓存过期时间（秒），默认24小时
            batch_size: 批量写入的记录数阈值
            batch_max_delay: 批量写入的最大延迟（秒）
        """
        self._price_cache: Dict[str, CacheEntry] = {}
        self._fee_cache: Dict[str, CacheEntry] = {}
        self._price_ttl = price_ttl
        self._fee_ttl = fee_ttl

        # 批量写入缓冲区
        self._write_buffer: List[Dict[str, Any]] = []
        self._batch_size = batch_size
        self._batch_max_delay = batch_max_delay
        self._last_flush_time: float = 0.0

        # 统计信息
        self._stats = {
            'price_hits': 0,
            'price_misses': 0,
            'fee_hits': 0,
            'fee_misses': 0,
            'batch_writes': 0,
            'single_writes': 0
        }

        # 后台任务
        self._cleanup_task: Optional[asyncio.Task] = None
        self._flush_task: Optional[asyncio.Task] = None
        self._running = False

    # -------------------- 价格缓存 --------------------

    async def get_price_cached(
        self,
        exchange: str,
        symbol: str,
        fetch_func: Callable[[], Awaitable[Dict]]
    ) -> Optional[Dict]:
        """获取价格数据（带缓存）

        Args:
            exchange: 交易所名称
            symbol: 交易对符号
            fetch_func: 获取价格数据的异步函数

        Returns:
            价格数据字典
        """
        cache_key = self._make_price_key(exchange, symbol)

        # 检查缓存
        cached = self._price_cache.get(cache_key)
        if cached and cached.age < self._price_ttl:
            cached.hits += 1
            self._stats['price_hits'] += 1
            logger.debug(f"价格缓存命中: {exchange}:{symbol} (年龄={cached.age:.2f}s)")
            return cached.data

        # 缓存未命中，获取新数据
        self._stats['price_misses'] += 1
        logger.debug(f"价格缓存未命中: {exchange}:{symbol}，查询中...")
        data = await fetch_func()

        if data:
            # 存入缓存
            self._price_cache[cache_key] = CacheEntry(
                data=data,
                timestamp=time.time(),
                hits=0
            )

        return data

    def get_price_sync(
        self,
        exchange: str,
        symbol: str,
        data: Dict
    ) -> Dict:
        """同步接口：设置或获取价格缓存

        Args:
            exchange: 交易所名称
            symbol: 交易对符号
            data: 价格数据（如果提供则设置缓存）

        Returns:
            缓存的价格数据
        """
        cache_key = self._make_price_key(exchange, symbol)

        if data:
            # 设置缓存
            self._price_cache[cache_key] = CacheEntry(
                data=data,
                timestamp=time.time(),
                hits=0
            )
            return data

        # 获取缓存
        cached = self._price_cache.get(cache_key)
        if cached and cached.age < self._price_ttl:
            cached.hits += 1
            self._stats['price_hits'] += 1
            return cached.data

        self._stats['price_misses'] += 1
        return {}

    # -------------------- 费用缓存 --------------------

    async def get_fee_cached(
        self,
        exchange: str,
        symbol: str,
        fetch_func: Callable[[], Awaitable[Dict]]
    ) -> Optional[Dict]:
        """获取交易费用（带缓存）

        Args:
            exchange: 交易所名称
            symbol: 交易对符号
            fetch_func: 获取费用数据的异步函数

        Returns:
            费用数据字典
        """
        cache_key = self._make_fee_key(exchange, symbol)

        # 检查缓存
        cached = self._fee_cache.get(cache_key)
        if cached and cached.age < self._fee_ttl:
            cached.hits += 1
            self._stats['fee_hits'] += 1
            logger.debug(f"费用缓存命中: {exchange}:{symbol} (年龄={cached.age:.2f}s)")
            return cached.data

        # 缓存未命中，获取新数据
        self._stats['fee_misses'] += 1
        logger.debug(f"费用缓存未命中: {exchange}:{symbol}，查询中...")
        data = await fetch_func()

        if data:
            # 存入缓存
            self._fee_cache[cache_key] = CacheEntry(
                data=data,
                timestamp=time.time(),
                hits=0
            )

        return data

    # -------------------- 批量写入 --------------------

    async def add_to_batch(
        self,
        record: Dict[str, Any],
        write_func: Callable[[List[Dict]], Awaitable[None]]
    ) -> None:
        """添加记录到批量写入缓冲区

        Args:
            record: 要写入的记录
            write_func: 批量写入的异步函数
        """
        self._write_buffer.append(record)

        # 检查是否需要立即写入
        now = time.time()
        should_flush = (
            len(self._write_buffer) >= self._batch_size or
            now - self._last_flush_time >= self._batch_max_delay
        )

        if should_flush:
            await self.flush_batch(write_func)

    async def flush_batch(
        self,
        write_func: Callable[[List[Dict]], Awaitable[None]]
    ) -> None:
        """立即刷新批量写入缓冲区

        Args:
            write_func: 批量写入的异步函数
        """
        if not self._write_buffer:
            return

        try:
            # 批量写入
            records = list(self._write_buffer)
            self._write_buffer.clear()

            await write_func(records)

            self._stats['batch_writes'] += 1
            self._last_flush_time = time.time()

            logger.info(f"批量写入完成: {len(records)}条记录")

        except Exception as e:
            logger.error(f"批量写入失败: {e}")
            # 写入失败，重新放回缓冲区
            self._write_buffer.extend(records)

    async def write_single(
        self,
        record: Dict[str, Any],
        write_func: Callable[[Dict], Awaitable[None]]
    ) -> None:
        """单次写入（绕过批量缓冲）

        Args:
            record: 要写入的记录
            write_func: 单次写入的异步函数
        """
        try:
            await write_func(record)
            self._stats['single_writes'] += 1
            logger.debug(f"单次写入完成")
        except Exception as e:
            logger.error(f"单次写入失败: {e}")

    # -------------------- 批量价格查询优化 --------------------

    async def get_prices_batch(
        self,
        queries: List[Tuple[str, str, Callable[[], Awaitable[Dict]]]]
    ) -> List[Dict]:
        """批量获取价格数据

        Args:
            queries: 查询列表，每个元素为 (exchange, symbol, fetch_func)

        Returns:
            价格数据列表
        """
        results = []

        # 第一轮：检查缓存
        cache_hits = []
        cache_misses = []

        for i, (exchange, symbol, fetch_func) in enumerate(queries):
            cache_key = self._make_price_key(exchange, symbol)
            cached = self._price_cache.get(cache_key)

            if cached and cached.age < self._price_ttl:
                cached.hits += 1
                self._stats['price_hits'] += 1
                cache_hits.append((i, cached.data))
            else:
                cache_misses.append((i, exchange, symbol, fetch_func))

        # 第二轮：并发查询缓存未命中的数据
        if cache_misses:
            logger.debug(f"批量查询: {len(cache_hits)}命中, {len(cache_misses)}未命中")

            tasks = [
                fetch_func()
                for _, _, _, fetch_func in cache_misses
            ]

            fetch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for (idx, exchange, symbol, _), result in zip(
                cache_misses, fetch_results
            ):
                if isinstance(result, Exception):
                    logger.error(f"批量查询失败: {exchange}:{symbol} - {result}")
                    results.append({})
                else:
                    # 存入缓存
                    cache_key = self._make_price_key(exchange, symbol)
                    self._price_cache[cache_key] = CacheEntry(
                        data=result,
                        timestamp=time.time(),
                        hits=0
                    )
                    results.append(result)
        else:
            self._stats['price_misses'] += 0  # 无未命中

        # 第三轮：合并结果
        final_results = [None] * len(queries)
        for i, data in cache_hits:
            final_results[i] = data

        miss_idx = 0
        for i, (idx, exchange, symbol, _) in enumerate(cache_misses):
            final_results[idx] = results[i]

        return final_results

    # -------------------- 缓存管理 --------------------

    def invalidate_price(self, exchange: str, symbol: str) -> None:
        """失效指定的价格缓存

        Args:
            exchange: 交易所名称
            symbol: 交易对符号
        """
        cache_key = self._make_price_key(exchange, symbol)
        if cache_key in self._price_cache:
            del self._price_cache[cache_key]
            logger.debug(f"失效价格缓存: {exchange}:{symbol}")

    def invalidate_fee(self, exchange: str, symbol: str) -> None:
        """失效指定的费用缓存

        Args:
            exchange: 交易所名称
            symbol: 交易对符号
        """
        cache_key = self._make_fee_key(exchange, symbol)
        if cache_key in self._fee_cache:
            del self._fee_cache[cache_key]
            logger.debug(f"失效费用缓存: {exchange}:{symbol}")

    def clear_all_caches(self) -> None:
        """清空所有缓存"""
        count = len(self._price_cache) + len(self._fee_cache)
        self._price_cache.clear()
        self._fee_cache.clear()
        logger.info(f"清空所有缓存: {count}条")

    # -------------------- 统计信息 --------------------

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息

        Returns:
            统计信息字典
        """
        price_hit_rate = 0.0
        if self._stats['price_hits'] + self._stats['price_misses'] > 0:
            price_hit_rate = self._stats['price_hits'] / (
                self._stats['price_hits'] + self._stats['price_misses']
            )

        fee_hit_rate = 0.0
        if self._stats['fee_hits'] + self._stats['fee_misses'] > 0:
            fee_hit_rate = self._stats['fee_hits'] / (
                self._stats['fee_hits'] + self._stats['fee_misses']
            )

        return {
            'price_cache': {
                'size': len(self._price_cache),
                'hits': self._stats['price_hits'],
                'misses': self._stats['price_misses'],
                'hit_rate': price_hit_rate,
                'ttl': self._price_ttl
            },
            'fee_cache': {
                'size': len(self._fee_cache),
                'hits': self._stats['fee_hits'],
                'misses': self._stats['fee_misses'],
                'hit_rate': fee_hit_rate,
                'ttl': self._fee_ttl
            },
            'batch_write': {
                'buffer_size': len(self._write_buffer),
                'batch_writes': self._stats['batch_writes'],
                'single_writes': self._stats['single_writes']
            }
        }

    # -------------------- 生命周期管理 --------------------

    async def start(self) -> None:
        """启动缓存系统（后台清理任务）"""
        if self._running:
            return

        self._running = True

        # 启动后台清理任务
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._flush_task = asyncio.create_task(self._flush_loop())

        logger.info("搜索缓存系统已启动")

    async def stop(self) -> None:
        """停止缓存系统"""
        if not self._running:
            return

        self._running = False

        # 取消后台任务
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass

        logger.info("搜索缓存系统已停止")

    async def _cleanup_loop(self) -> None:
        """后台清理过期缓存"""
        while self._running:
            try:
                await asyncio.sleep(60)  # 每分钟清理一次

                # 清理过期价格缓存
                expired_prices = [
                    key for key, entry in self._price_cache.items()
                    if entry.age >= self._price_ttl
                ]
                for key in expired_prices:
                    del self._price_cache[key]

                # 清理过期费用缓存
                expired_fees = [
                    key for key, entry in self._fee_cache.items()
                    if entry.age >= self._fee_ttl
                ]
                for key in expired_fees:
                    del self._fee_cache[key]

                if expired_prices or expired_fees:
                    logger.debug(
                        f"清理过期缓存: 价格{len(expired_prices)}条, "
                        f"费用{len(expired_fees)}条"
                    )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"缓存清理任务异常: {e}")

    async def _flush_loop(self) -> None:
        """后台定时刷新批量缓冲区"""
        while self._running:
            try:
                await asyncio.sleep(1)  # 每秒检查一次

                # 刷新批量写入（使用虚拟写入函数，实际使用时需要提供）
                if self._write_buffer:
                    logger.debug(
                        f"批量缓冲区状态: {len(self._write_buffer)}条记录, "
                        f"距离上次刷新{time.time() - self._last_flush_time:.2f}秒"
                    )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"批量刷新任务异常: {e}")

    # -------------------- 工具方法 --------------------

    @staticmethod
    def _make_price_key(exchange: str, symbol: str) -> str:
        """生成价格缓存键"""
        return f"price:{exchange}:{symbol}"

    @staticmethod
    def _make_fee_key(exchange: str, symbol: str) -> str:
        """生成费用缓存键"""
        return f"fee:{exchange}:{symbol}"

    @staticmethod
    def _hash_key(key: str) -> str:
        """生成缓存键的哈希值（可选）"""
        return hashlib.md5(key.encode()).hexdigest()


# 全局缓存实例
_global_cache: Optional[SearchCache] = None


def get_global_cache() -> SearchCache:
    """获取全局缓存实例"""
    global _global_cache
    if _global_cache is None:
        _global_cache = SearchCache()
    return _global_cache


def set_global_cache(cache: SearchCache) -> None:
    """设置全局缓存实例"""
    global _global_cache
    _global_cache = cache
