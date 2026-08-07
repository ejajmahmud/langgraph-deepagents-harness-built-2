"""缓存管理模块 V5.9 - 专注智能缓存策略和性能优化

核心职责：
1. 统一缓存管理 - 管理所有模块的缓存
2. 智能缓存策略 - LRU、TTL、大小限制等多策略
3. 缓存性能监控 - 命中率、使用率等关键指标
4. 缓存数据持久化 - 支持导出导入缓存数据

V5.9新增功能：
5. 批量操作 - 批量获取和设置缓存，减少访问次数
6. 缓存预热 - 智能预热热点数据，提升命中率
7. 异步支持 - 异步批量操作，提升并发性能

管理功能：
- 多级缓存：支持不同模块的独立缓存
- 智能清理：基于LRU和TTL的自动清理
- 性能优化：缓存命中率监控和优化建议
- 数据持久化：缓存数据的导出和导入
- 批量操作：减少高频访问的性能瓶颈

设计原则：
- 单一职责：专注缓存管理功能
- 高内聚性：所有方法都围绕缓存管理展开
- 性能优先：优化缓存命中率和响应速度
- 可观测性：详细的缓存统计和监控

基于：V5.7 Graphify架构优化分析
内聚性目标：0.50+
升级：V5.9批量操作和缓存预热
"""

import logging
import time
import json
import asyncio
from typing import Any, Dict, List, Optional, Set
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class CacheManagerModule:
    """缓存管理模块 - 专注智能缓存策略和性能优化

    提供统一的缓存管理功能，支持多级缓存、智能清理、
    性能监控和数据持久化，大幅提升系统整体性能。
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化缓存管理模块

        Args:
            config: 配置字典，包含：
                - enable_cache_management: 是否启用缓存管理
                - default_ttl: 默认缓存TTL（秒）
                - max_cache_size: 默认最大缓存大小
                - enable_auto_cleanup: 是否启用自动清理
                - cleanup_interval: 清理间隔（秒）
                - persist_cache: 是否持久化缓存
                - cache_dir: 缓存目录
        """
        self.config = config
        self.enable_cache_management = config.get('enable_cache_management', True)

        # 缓存配置
        self._default_ttl = config.get('default_ttl', 300)  # 5分钟
        self._max_cache_size = config.get('max_cache_size', 1000)
        self._enable_auto_cleanup = config.get('enable_auto_cleanup', True)
        self._cleanup_interval = config.get('cleanup_interval', 60)  # 1分钟

        # 持久化配置
        self._persist_cache = config.get('persist_cache', False)
        self._cache_dir = Path(config.get('cache_dir', 'data/cache'))
        if self._persist_cache:
            self._cache_dir.mkdir(parents=True, exist_ok=True)

        # 多级缓存存储
        self._caches: Dict[str, OrderedDict] = {}
        self._cache_configs: Dict[str, Dict[str, Any]] = {}

        # 性能统计
        self._stats = {
            'total_accesses': 0,
            'total_hits': 0,
            'total_misses': 0,
            'total_evictions': 0,
            'cache_operations': {
                'get': 0,
                'set': 0,
                'delete': 0,
                'clear': 0,
                'batch_get': 0,  # V5.9新增
                'batch_set': 0,  # V5.9新增
                'batch_get_async': 0,  # V5.9新增
                'batch_set_async': 0,  # V5.9新增
                'warmup': 0  # V5.9新增
            }
        }

        # 最后清理时间
        self._last_cleanup_time = time.time()

        logger.info("[OK] 缓存管理模块 V5.8 初始化完成")

    def register_cache(
        self,
        cache_name: str,
        max_size: Optional[int] = None,
        ttl: Optional[int] = None
    ) -> None:
        """注册一个新的缓存

        Args:
            cache_name: 缓存名称
            max_size: 最大缓存大小（可选）
            ttl: 缓存TTL（可选）
        """
        if cache_name in self._caches:
            logger.warning(f"缓存 {cache_name} 已存在，将被覆盖")

        # 创建缓存
        self._caches[cache_name] = OrderedDict()

        # 保存缓存配置
        self._cache_configs[cache_name] = {
            'max_size': max_size or self._max_cache_size,
            'ttl': ttl or self._default_ttl,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        logger.info(f"缓存 {cache_name} 已注册 (max_size={self._cache_configs[cache_name]['max_size']}, ttl={self._cache_configs[cache_name]['ttl']})")

    def get(
        self,
        cache_name: str,
        key: str,
        default: Any = None
    ) -> Any:
        """从缓存获取数据

        Args:
            cache_name: 缓存名称
            key: 缓存键
            default: 默认值

        Returns:
            缓存数据或默认值
        """
        self._stats['total_accesses'] += 1
        self._stats['cache_operations']['get'] += 1

        # 检查缓存是否存在
        if cache_name not in self._caches:
            logger.debug(f"缓存 {cache_name} 不存在")
            self._stats['total_misses'] += 1
            return default

        cache = self._caches[cache_name]
        cache_config = self._cache_configs[cache_name]

        # 检查键是否存在
        if key not in cache:
            self._stats['total_misses'] += 1
            return default

        # 检查是否过期
        cached_item = cache[key]
        if time.time() - cached_item['timestamp'] > cache_config['ttl']:
            # 过期，删除
            del cache[key]
            self._stats['total_misses'] += 1
            logger.debug(f"缓存项 {cache_name}:{key} 已过期")
            return default

        # 命中，更新LRU
        cache.move_to_end(key)
        self._stats['total_hits'] += 1

        return cached_item['data']

    def set(
        self,
        cache_name: str,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """设置缓存数据

        Args:
            cache_name: 缓存名称
            key: 缓存键
            value: 缓存值
            ttl: 自定义TTL（可选）

        Returns:
            是否成功
        """
        self._stats['cache_operations']['set'] += 1

        # 检查缓存是否存在
        if cache_name not in self._caches:
            logger.warning(f"缓存 {cache_name} 不存在，自动注册")
            self.register_cache(cache_name)

        cache = self._caches[cache_name]
        cache_config = self._cache_configs[cache_name]

        # 检查缓存大小，必要时清理
        if len(cache) >= cache_config['max_size']:
            self._evict_lru(cache_name)

        # 设置缓存
        cache[key] = {
            'data': value,
            'timestamp': time.time(),
            'ttl': ttl or cache_config['ttl']
        }

        # LRU: 移动到末尾
        cache.move_to_end(key)

        return True

    def delete(self, cache_name: str, key: str) -> bool:
        """删除缓存数据

        Args:
            cache_name: 缓存名称
            key: 缓存键

        Returns:
            是否成功
        """
        self._stats['cache_operations']['delete'] += 1

        if cache_name not in self._caches:
            return False

        cache = self._caches[cache_name]

        if key in cache:
            del cache[key]
            return True

        return False

    def clear(self, cache_name: str) -> bool:
        """清空指定缓存

        Args:
            cache_name: 缓存名称

        Returns:
            是否成功
        """
        self._stats['cache_operations']['clear'] += 1

        if cache_name not in self._caches:
            return False

        self._caches[cache_name].clear()
        logger.info(f"缓存 {cache_name} 已清空")
        return True

    def clear_all(self) -> None:
        """清空所有缓存"""
        for cache_name in self._caches:
            self._caches[cache_name].clear()

        logger.info("所有缓存已清空")

    def _evict_lru(self, cache_name: str) -> None:
        """淘汰最久未使用的缓存项

        Args:
            cache_name: 缓存名称
        """
        if cache_name not in self._caches:
            return

        cache = self._caches[cache_name]

        if cache:
            # 删除最旧的项（第一个）
            cache.popitem(last=False)
            self._stats['total_evictions'] += 1
            logger.debug(f"缓存 {cache_name} LRU淘汰")

    def cleanup_expired(self, cache_name: Optional[str] = None) -> int:
        """清理过期缓存

        Args:
            cache_name: 缓存名称（可选，不指定则清理所有）

        Returns:
            清理的缓存项数量
        """
        current_time = time.time()
        total_cleaned = 0

        caches_to_clean = [cache_name] if cache_name else list(self._caches.keys())

        for name in caches_to_clean:
            if name not in self._caches:
                continue

            cache = self._caches[name]
            cache_config = self._cache_configs[name]
            ttl = cache_config['ttl']

            # 找出过期的键
            expired_keys = [
                key for key, item in cache.items()
                if current_time - item['timestamp'] > ttl
            ]

            # 删除过期键
            for key in expired_keys:
                del cache[key]
                total_cleaned += 1

            if expired_keys:
                logger.debug(f"缓存 {name} 清理了 {len(expired_keys)} 个过期项")

        self._last_cleanup_time = current_time
        return total_cleaned

    def auto_cleanup_if_needed(self) -> int:
        """如果需要，自动执行清理

        Returns:
            清理的缓存项数量
        """
        if not self._enable_auto_cleanup:
            return 0

        current_time = time.time()
        if current_time - self._last_cleanup_time >= self._cleanup_interval:
            return self.cleanup_expired()

        return 0

    def get_cache_stats(self, cache_name: str) -> Dict[str, Any]:
        """获取指定缓存的统计信息

        Args:
            cache_name: 缓存名称

        Returns:
            缓存统计信息
        """
        if cache_name not in self._caches:
            return {
                'error': f'缓存 {cache_name} 不存在'
            }

        cache = self._caches[cache_name]
        cache_config = self._cache_configs[cache_name]

        return {
            'cache_name': cache_name,
            'size': len(cache),
            'max_size': cache_config['max_size'],
            'usage': len(cache) / cache_config['max_size'] if cache_config['max_size'] > 0 else 0,
            'ttl': cache_config['ttl'],
            'created_at': cache_config.get('created_at', 'unknown')
        }

    def get_global_stats(self) -> Dict[str, Any]:
        """获取全局缓存统计信息

        Returns:
            全局统计信息
        """
        total_accesses = self._stats['total_accesses']
        hit_rate = (
            self._stats['total_hits'] / total_accesses
            if total_accesses > 0 else 0
        )

        # 聚合所有缓存的大小
        total_cache_size = sum(len(cache) for cache in self._caches.values())
        total_max_size = sum(
            config['max_size'] for config in self._cache_configs.values()
        )

        return {
            'total_accesses': total_accesses,
            'total_hits': self._stats['total_hits'],
            'total_misses': self._stats['total_misses'],
            'hit_rate': hit_rate,
            'total_evictions': self._stats['total_evictions'],
            'total_cache_size': total_cache_size,
            'total_max_size': total_max_size,
            'global_usage': total_cache_size / total_max_size if total_max_size > 0 else 0,
            'cache_count': len(self._caches),
            'operations': dict(self._stats['cache_operations']),
            'last_cleanup': datetime.fromtimestamp(self._last_cleanup_time).strftime('%Y-%m-%d %H:%M:%S')
        }

    def export_cache(self, cache_name: str, file_path: Optional[str] = None) -> bool:
        """导出缓存数据

        Args:
            cache_name: 缓存名称
            file_path: 文件路径（可选）

        Returns:
            是否成功
        """
        if cache_name not in self._caches:
            logger.error(f"缓存 {cache_name} 不存在")
            return False

        try:
            cache_data = {
                'cache_name': cache_name,
                'config': self._cache_configs[cache_name],
                'data': dict(self._caches[cache_name]),
                'export_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'stats': self.get_cache_stats(cache_name)
            }

            if file_path:
                # 导出到指定文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
                logger.info(f"缓存 {cache_name} 已导出到 {file_path}")
            else:
                # 导出到默认文件
                if self._persist_cache:
                    default_path = self._cache_dir / f"{cache_name}_cache.json"
                    with open(default_path, 'w', encoding='utf-8') as f:
                        json.dump(cache_data, f, ensure_ascii=False, indent=2)
                    logger.info(f"缓存 {cache_name} 已导出到 {default_path}")
                else:
                    logger.warning("缓存持久化未启用，无法导出")

            return True

        except Exception as e:
            logger.error(f"导出缓存失败: {e}")
            return False

    def import_cache(self, cache_name: str, file_path: str) -> bool:
        """导入缓存数据

        Args:
            cache_name: 缓存名称
            file_path: 文件路径

        Returns:
            是否成功
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            # 验证数据
            if cache_data.get('cache_name') != cache_name:
                logger.warning(f"导入的缓存名称不匹配: {cache_data.get('cache_name')} != {cache_name}")

            # 注册缓存（如果不存在）
            if cache_name not in self._caches:
                config = cache_data.get('config', {})
                self.register_cache(
                    cache_name,
                    max_size=config.get('max_size'),
                    ttl=config.get('ttl')
                )

            # 导入数据
            imported_cache = cache_data.get('data', {})
            for key, value in imported_cache.items():
                self._caches[cache_name][key] = value

            logger.info(f"缓存 {cache_name} 已从 {file_path} 导入，共 {len(imported_cache)} 项")
            return True

        except Exception as e:
            logger.error(f"导入缓存失败: {e}")
            return False

    def get_optimization_suggestions(self) -> List[str]:
        """获取缓存优化建议

        Returns:
            优化建议列表
        """
        suggestions = []
        global_stats = self.get_global_stats()

        # 命中率分析
        if global_stats['hit_rate'] < 0.5:
            suggestions.append(f"缓存命中率较低 ({global_stats['hit_rate']:.1%})，建议检查缓存策略和TTL设置")

        # 使用率分析
        if global_stats['global_usage'] > 0.9:
            suggestions.append(f"缓存使用率过高 ({global_stats['global_usage']:.1%})，建议增加缓存大小或优化清理策略")

        # 淘汰分析
        if global_stats['total_evictions'] > global_stats['total_hits']:
            suggestions.append("缓存淘汰次数过多，建议增加缓存大小或调整TTL")

        # 访问频率分析
        if global_stats['total_accesses'] == 0:
            suggestions.append("缓存未被使用，建议检查缓存调用逻辑")

        return suggestions if suggestions else ["缓存运行良好，无优化建议"]

    def reset_stats(self) -> None:
        """重置统计"""
        self._stats = {
            'total_accesses': 0,
            'total_hits': 0,
            'total_misses': 0,
            'total_evictions': 0,
            'cache_operations': {
                'get': 0,
                'set': 0,
                'delete': 0,
                'clear': 0
            }
        }
        logger.info("缓存管理统计已重置")

    # ========== V5.9新增：批量操作功能 ==========

    def batch_get(self, cache_name: str, keys: List[str]) -> Dict[str, Any]:
        """批量获取缓存数据

        Args:
            cache_name: 缓存名称
            keys: 缓存键列表

        Returns:
            缓存数据字典 {key: data}
        """
        self._stats['cache_operations']['batch_get'] = self._stats['cache_operations'].get('batch_get', 0) + 1

        if cache_name not in self._caches:
            return {}

        cache = self._caches[cache_name]
        results = {}

        for key in keys:
            data = self.get(cache_name, key)
            if data is not None:
                results[key] = data

        return results

    def batch_set(self, cache_name: str, items: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """批量设置缓存数据

        Args:
            cache_name: 缓存名称
            items: 缓存数据字典 {key: value}
            ttl: 缓存TTL（秒）

        Returns:
            是否成功
        """
        self._stats['cache_operations']['batch_set'] = self._stats['cache_operations'].get('batch_set', 0) + 1

        success = True
        for key, value in items.items():
            if not self.set(cache_name, key, value, ttl):
                success = False

        return success

    async def batch_get_async(self, cache_name: str, keys: List[str]) -> Dict[str, Any]:
        """异步批量获取缓存数据

        Args:
            cache_name: 缓存名称
            keys: 缓存键列表

        Returns:
            缓存数据字典 {key: data}
        """
        # 将批量获取任务并发执行
        tasks = [self.get(cache_name, key) for key in keys]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        data_dict = {}
        for key, result in zip(keys, results):
            if not isinstance(result, Exception) and result is not None:
                data_dict[key] = result

        return data_dict

    async def batch_set_async(self, cache_name: str, items: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """异步批量设置缓存数据

        Args:
            cache_name: 缓存名称
            items: 缓存数据字典 {key: value}
            ttl: 缓存TTL（秒）

        Returns:
            是否成功
        """
        tasks = [self.set(cache_name, key, value, ttl) for key, value in items.items()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 检查所有任务是否成功
        return all(not isinstance(result, Exception) for result in results)

    async def warmup_cache(self, cache_name: str, keys: List[str], data_loader: callable = None) -> Dict[str, Any]:
        """缓存预热

        Args:
            cache_name: 缓存名称
            keys: 需要预热的缓存键列表
            data_loader: 数据加载函数 (key) -> data

        Returns:
            预热结果字典
        """
        self._stats['cache_operations']['warmup'] = self._stats['cache_operations'].get('warmup', 0) + 1

        logger.info(f"开始缓存预热: {len(keys)} 个键")

        # 检查哪些键已经存在
        existing_keys = set()
        if cache_name in self._caches:
            existing_keys = set(self._caches[cache_name].keys())

        # 只预热不存在的键
        missing_keys = [key for key in keys if key not in existing_keys]

        if not missing_keys:
            logger.info("所有键已缓存，无需预热")
            return {"warmed_count": 0, "skipped_count": len(keys)}

        # 使用数据加载函数预热
        if data_loader:
            warmup_results = {}
            for key in missing_keys:
                try:
                    data = data_loader(key)
                    if data is not None:
                        self.set(cache_name, key, data)
                        warmup_results[key] = data
                except Exception as e:
                    logger.warning(f"预热键 {key} 失败: {e}")

            logger.info(f"缓存预热完成: {len(warmup_results)} 个键")
            return {
                "warmed_count": len(warmup_results),
                "skipped_count": len(existing_keys),
                "failed_count": len(missing_keys) - len(warmup_results)
            }
        else:
            logger.info("无数据加载函数，跳过缓存预热")
            return {"warmed_count": 0, "skipped_count": len(keys)}


def create_cache_manager_module(config: Dict[str, Any]) -> CacheManagerModule:
    """创建缓存管理模块

    Args:
        config: 配置字典

    Returns:
        缓存管理模块实例
    """
    return CacheManagerModule(config)
