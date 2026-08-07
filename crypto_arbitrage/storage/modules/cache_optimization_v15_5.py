"""缓存性能优化模块 V15.5 - 解决458个.get()调用热点

基于V15.4深度分析发现：
- 缓存.get()方法有458个连接（性能热点）
- 缓存访问模式需要优化
- 需要实现缓存预热和批量访问

V15.5优化方案：
1. 批量缓存访问 - 减少单次调用开销
2. 缓存预热 - 预加载热点数据
3. 智能缓存键设计 - 提高缓存命中率
4. 异步缓存访问 - 减少阻塞等待
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Set
from functools import wraps
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class CacheMetrics:
    """缓存性能指标"""
    total_gets: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    batch_gets: int = 0
    async_gets: int = 0
    preloaded_keys: int = 0
    avg_access_time: float = 0.0
    hit_rate: float = 0.0

    def update_hit_rate(self):
        """更新命中率"""
        if self.total_gets > 0:
            self.hit_rate = (self.cache_hits / self.total_gets) * 100

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        self.update_hit_rate()
        return {
            "total_gets": self.total_gets,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": f"{self.hit_rate:.2f}%",
            "batch_gets": self.batch_gets,
            "async_gets": self.async_gets,
            "preloaded_keys": self.preloaded_keys,
            "avg_access_time": f"{self.avg_access_time:.4f}s"
        }


class CacheOptimizationV15:
    """缓存优化器 V15.5

    解决V15.4发现的缓存性能热点问题。
    """

    def __init__(self, base_cache, config: Dict[str, Any] = None):
        """初始化缓存优化器

        Args:
            base_cache: 基础缓存实例
            config: 配置字典
        """
        self.base_cache = base_cache
        self.config = config or {}

        # 性能指标
        self.metrics = CacheMetrics()

        # V15.5: 批量访问优化
        self.enable_batch_access = self.config.get('enable_batch_access', True)
        self.batch_size = self.config.get('batch_size', 50)

        # V15.5: 异步访问优化
        self.enable_async_access = self.config.get('enable_async_access', True)
        self.max_concurrent_gets = self.config.get('max_concurrent_gets', 10)

        # V15.5: 缓存预热
        self.enable_prewarm = self.config.get('enable_prewarm', True)
        self.prewarm_keys: Set[str] = set()

        # V15.5: 智能缓存键
        self.enable_smart_keys = self.config.get('enable_smart_keys', True)
        self.key_cache: Dict[str, str] = {}

        # V15.5: 访问历史（用于分析热点）
        self.access_history: List[Dict] = []
        self.max_history_size = 1000

        # V15.5: 热点识别
        self.hot_keys: Set[str] = set()
        self.hot_threshold = 10  # 访问次数阈值

        logger.info(f"[OK] 缓存优化器V15.5初始化完成 "
                  f"(批量:{self.enable_batch_access}, "
                  f"异步:{self.enable_async_access}, "
                  f"预热:{self.enable_prewarm})")

    def get(self, key: str, default: Any = None) -> Any:
        """优化的get方法（单次访问）

        Args:
            key: 缓存键
            default: 默认值

        Returns:
            缓存值或默认值
        """
        start_time = asyncio.get_event_loop().time()

        # V15.5: 智能键处理
        optimized_key = self._optimize_key(key)

        # 记录访问历史
        self._record_access(key, start_time)

        # 调用基础缓存
        try:
            value = self.base_cache.get(optimized_key, default)
            self.metrics.cache_hits += 1
        except (KeyError, AttributeError):
            value = default
            self.metrics.cache_misses += 1

        # 更新指标
        self.metrics.total_gets += 1
        access_time = asyncio.get_event_loop().time() - start_time
        self._update_avg_access_time(access_time)

        return value

    def batch_get(self, keys: List[str]) -> Dict[str, Any]:
        """批量get方法（V15.5新增）

        Args:
            keys: 缓存键列表

        Returns:
            键值对字典
        """
        self.metrics.batch_gets += 1
        results = {}

        # 批量获取所有键
        for key in keys:
            optimized_key = self._optimize_key(key)
            try:
                value = self.base_cache.get(optimized_key)
                results[key] = value
                self.metrics.cache_hits += 1
            except (KeyError, AttributeError):
                results[key] = None
                self.metrics.cache_misses += 1

            self.metrics.total_gets += 1

        logger.debug(f"批量获取 {len(keys)} 个键")
        return results

    async def async_get(self, key: str, default: Any = None) -> Any:
        """异步get方法（V15.5新增）

        Args:
            key: 缓存键
            default: 默认值

        Returns:
            缓存值或默认值
        """
        self.metrics.async_gets += 1

        # 使用asyncio避免阻塞
        return await asyncio.to_thread_func(
            self.get, key, default
        )

    async def batch_async_get(self, keys: List[str]) -> Dict[str, Any]:
        """批量异步get方法（V15.5新增）

        Args:
            keys: 缓存键列表

        Returns:
            键值对字典
        """
        self.metrics.batch_gets += 1

        # 并发批量获取
        tasks = [self.async_get(key) for key in keys]
        results_values = await asyncio.gather(*tasks, return_exceptions=True)

        results = {}
        for key, value in zip(keys, results_values):
            results[key] = value if not isinstance(value, Exception) else None

        logger.debug(f"批量异步获取 {len(keys)} 个键")
        return results

    def _optimize_key(self, key: str) -> str:
        """优化缓存键（V15.5智能键）

        Args:
            key: 原始键

        Returns:
            优化后的键
        """
        if not self.enable_smart_keys:
            return key

        # 使用缓存避免重复计算
        if key in self.key_cache:
            return self.key_cache[key]

        # V15.5: 智能键设计
        # 1. 统一大小写
        optimized = key.lower().strip()

        # 2. 移除特殊字符
        optimized = ''.join(c for c in optimized if c.isalnum() or c in '_-')

        # 3. 限制长度（避免键过长）
        if len(optimized) > 100:
            optimized = optimized[:100] + '_' + hashlib.md5(optimized.encode()).hexdigest()[:8]

        # 4. 添加类型前缀（基于键模式）
        key_type = self._detect_key_type(key)
        if key_type:
            optimized = f"{key_type}:{optimized}"

        # 缓存优化后的键
        self.key_cache[key] = optimized

        return optimized

    def _detect_key_type(self, key: str) -> Optional[str]:
        """检测键类型（用于前缀优化）

        Args:
            key: 缓存键

        Returns:
            键类型（market, signal, risk等）
        """
        key_lower = key.lower()

        # 市场数据键
        if any(term in key_lower for term in ['price', 'ticker', 'market', 'ohlcv']):
            return 'market'

        # 信号键
        if any(term in key_lower for term in ['signal', 'analysis', 'opportunity']):
            return 'signal'

        # 风险键
        if any(term in key_lower for term in ['risk', 'position', 'exposure']):
            return 'risk'

        # 策略键
        if any(term in key_lower for term in ['strategy', 'config', 'param']):
            return 'strategy'

        return None

    def _record_access(self, key: str, timestamp: float):
        """记录访问历史（用于热点识别）

        Args:
            key: 缓存键
            timestamp: 访问时间戳
        """
        # 记录访问
        self.access_history.append({
            "key": key,
            "timestamp": timestamp
        })

        # 限制历史大小
        if len(self.access_history) > self.max_history_size:
            self.access_history.pop(0)

        # 识别热点
        self._update_hot_keys(key)

    def _update_hot_keys(self, key: str):
        """更新热点键列表

        Args:
            key: 缓存键
        """
        # 统计访问次数
        access_count = sum(1 for item in self.access_history if item["key"] == key)

        # 更新热点集合
        if access_count >= self.hot_threshold:
            self.hot_keys.add(key)

    def _update_avg_access_time(self, new_time: float):
        """更新平均访问时间

        Args:
            new_time: 新的访问时间
        """
        if self.metrics.total_gets == 1:
            self.metrics.avg_access_time = new_time
        else:
            # 指数移动平均（权重0.1）
            self.metrics.avg_access_time = (
                self.metrics.avg_access_time * 0.9 + new_time * 0.1
            )

    async def prewarm_cache(self, hot_keys: List[str], data_loader: callable):
        """预热缓存（V15.5新增）

        Args:
            hot_keys: 热点键列表
            data_loader: 数据加载函数
        """
        if not self.enable_prewarm:
            return

        logger.info(f"开始预热缓存，热点键数量: {len(hot_keys)}")

        # 批量预加载热点数据
        tasks = []
        for key in hot_keys:
            task = asyncio.create_task(self._prewarm_key(key, data_loader))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 统计成功预热
        preloaded = sum(1 for r in results if r is True)
        self.metrics.preloaded_keys = preloaded

        logger.info(f"缓存预热完成: {preloaded}/{len(hot_keys)} 成功")

    async def _prewarm_key(self, key: str, data_loader: callable) -> bool:
        """预加载单个键

        Args:
            key: 缓存键
            data_loader: 数据加载函数

        Returns:
            是否成功预加载
        """
        try:
            # 调用数据加载器
            data = await data_loader(key)

            # 存入缓存
            if data is not None:
                optimized_key = self._optimize_key(key)
                self.base_cache.set(optimized_key, data)
                self.prewarm_keys.add(key)
                return True

        except Exception as e:
            logger.debug(f"预热键 {key} 失败: {e}")
            return False

    def get_hot_keys(self, top_n: int = 50) -> List[str]:
        """获取热点键列表

        Args:
            top_n: 返回前N个热点键

        Returns:
            热点键列表（按访问次数排序）
        """
        # 统计每个键的访问次数
        access_counts = {}
        for item in self.access_history:
            key = item["key"]
            access_counts[key] = access_counts.get(key, 0) + 1

        # 按访问次数排序
        sorted_keys = sorted(
            access_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # 返回前N个
        return [key for key, count in sorted_keys[:top_n]]

    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标

        Returns:
            性能指标字典
        """
        return self.metrics.get_stats()

    def reset_metrics(self):
        """重置性能指标"""
        self.metrics = CacheMetrics()
        logger.info("缓存性能指标已重置")

    def optimize_cache(self) -> Dict[str, Any]:
        """优化缓存（分析并应用最佳实践）

        Returns:
            优化建议字典
        """
        logger.info("开始缓存优化分析...")

        # 1. 分析热点键
        hot_keys = self.get_hot_keys(top_n=20)
        self.hot_keys = set(hot_keys)

        # 2. 生成优化建议
        recommendations = {
            "hot_keys_count": len(hot_keys),
            "total_accesses": len(self.access_history),
            "recommendations": []
        }

        # 建议缓存预热
        if self.enable_prewarm and len(hot_keys) > 0:
            recommendations.append({
                "type": "prewarm",
                "description": f"发现{len(hot_keys)}个热点键，建议预加载",
                "keys": hot_keys[:10]  # 显示前10个
            })

        # 建议使用批量访问
        if self.enable_batch_access and len(hot_keys) > self.batch_size:
            recommendations.append({
                "type": "batch",
                "description": "热点键数量超过批量大小，建议使用batch_get()",
                "current_batch_size": self.batch_size,
                "recommended_batch_size": min(len(hot_keys), 100)
            })

        # 建议使用异步访问
        if self.enable_async_access:
            recommendations.append({
                "type": "async",
                "description": "高并发场景建议使用async_get()和batch_async_get()",
                "max_concurrent": self.max_concurrent_gets
            })

        logger.info(f"缓存优化分析完成，{len(recommendations['recommendations'])}条建议")
        return recommendations


def create_cache_optimization(base_cache, config: Dict = None) -> CacheOptimizationV15:
    """创建缓存优化器工厂函数

    Args:
        base_cache: 基础缓存实例
        config: 配置字典

    Returns:
        缓存优化器实例
    """
    return CacheOptimizationV15(base_cache, config)


# V15.5: 缓存访问装饰器
def optimized_cache_get(cache_optimizer: CacheOptimizationV15):
    """缓存访问装饰器（用于包装现有代码）

    Args:
        cache_optimizer: 缓存优化器实例

    Returns:
        装饰器函数
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 检测函数是否支持批量访问
            if hasattr(cache_optimizer, 'batch_get') and 'keys' in kwargs:
                # 批量访问路径
                keys = kwargs.pop('keys')
                if len(keys) > 1:
                    return cache_optimizer.batch_get(keys)

            # 单次访问路径
            return func(*args, **kwargs)
        return wrapper
    return decorator
