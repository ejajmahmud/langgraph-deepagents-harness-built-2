"""信号融合缓存引擎

V2.7新增：为信号融合提供智能缓存机制，避免重复计算技术指标
和风险信号，显著提升信号融合性能。

核心特性：
1. 多层缓存 - L1内存缓存 + L2磁盘缓存
2. 智能失效 - 基于时间、数据变化自动失效
3. 缓存预热 - 预计算常用信号
4. 统计追踪 - 缓存命中率、大小等指标
5. 线程安全 - 支持并发读写
"""

import hashlib
import json
import logging
import os
import pickle
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class SignalCache:
    """信号缓存引擎

    为信号融合提供高性能缓存，避免重复计算。
    """

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: int = 60,
        cache_dir: Optional[str] = None
    ):
        """初始化信号缓存

        Args:
            max_size: 最大缓存条目数
            default_ttl: 默认TTL（秒）
            cache_dir: 磁盘缓存目录
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache_dir = Path(cache_dir) if cache_dir else Path("cache/signals")

        # L1 内存缓存
        self.memory_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
        self.cache_lock = threading.RLock()

        # 统计信息
        self.stats = {
            "memory_hits": 0,
            "disk_hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_gets": 0,
            "total_sets": 0
        }

        # 确保缓存目录存在
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"SignalCache initialized: "
            f"max_size={max_size}, "
            f"default_ttl={default_ttl}s, "
            f"cache_dir={self.cache_dir}"
        )

    def get(
        self,
        signal_type: str,
        symbol: str,
        extra_key: str = "",
        ttl: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """获取缓存的信号

        Args:
            signal_type: 信号类型 (technical/arbitrage/risk)
            symbol: 交易对符号
            extra_key: 额外的键（用于区分不同的计算参数）
            ttl: 自定义TTL（秒）

        Returns:
            缓存信号或None
        """
        self.stats["total_gets"] += 1

        cache_key = self._generate_key(signal_type, symbol, extra_key)

        # 检查L1内存缓存
        cached = self._get_from_memory(cache_key, ttl or self.default_ttl)
        if cached is not None:
            self.stats["memory_hits"] += 1
            logger.debug(f"Memory cache hit: {cache_key}")
            return cached

        # 检查L2磁盘缓存
        cached = self._get_from_disk(cache_key, ttl or self.default_ttl)
        if cached is not None:
            self.stats["disk_hits"] += 1

            # 提升到L1缓存
            self._add_to_memory(cache_key, cached)

            logger.debug(f"Disk cache hit: {cache_key}")
            return cached

        # 缓存未命中
        self.stats["misses"] += 1
        logger.debug(f"Cache miss: {cache_key}")
        return None

    def set(
        self,
        signal_type: str,
        symbol: str,
        signal_data: Dict[str, Any],
        extra_key: str = "",
        ttl: Optional[int] = None
    ) -> None:
        """缓存信号

        Args:
            signal_type: 信号类型
            symbol: 交易对符号
            signal_data: 信号数据
            extra_key: 额外的键
            ttl: 自定义TTL（秒）
        """
        self.stats["total_sets"] += 1

        cache_key = self._generate_key(signal_type, symbol, extra_key)

        # 添加到L1缓存
        self._add_to_memory(cache_key, signal_data, ttl or self.default_ttl)

        # 异步写入L2缓存
        self._add_to_disk_async(cache_key, signal_data, ttl or self.default_ttl)

    def invalidate(self, signal_type: Optional[str] = None, symbol: Optional[str] = None) -> None:
        """失效缓存

        Args:
            signal_type: 信号类型（None表示全部类型）
            symbol: 交易对符号（None表示全部符号）
        """
        with self.cache_lock:
            # 计算需要失效的键
            keys_to_delete = []
            for key in self.memory_cache.keys():
                parts = key.split("|")
                key_type = parts[0] if len(parts) > 0 else None
                key_symbol = parts[1] if len(parts) > 1 else None

                if (signal_type is None or key_type == signal_type) and \
                   (symbol is None or key_symbol == symbol):
                    keys_to_delete.append(key)

            # 删除缓存项
            for key in keys_to_delete:
                del self.memory_cache[key]

            # 删除磁盘缓存
            self._invalidate_disk(signal_type, symbol)

            logger.info(
                f"Invalidated {len(keys_to_delete)} cache entries: "
                f"type={signal_type}, symbol={symbol}"
            )

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计

        Returns:
            统计信息字典
        """
        total_hits = self.stats["memory_hits"] + self.stats["disk_hits"]
        hit_rate = 0.0
        if self.stats["total_gets"] > 0:
            hit_rate = total_hits / self.stats["total_gets"]

        return {
            **self.stats,
            "hit_rate": hit_rate,
            "memory_cache_size": len(self.memory_cache),
            "disk_cache_size": self._get_disk_cache_size()
        }

    def reset_stats(self) -> None:
        """重置统计信息"""
        self.stats = {
            "memory_hits": 0,
            "disk_hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_gets": 0,
            "total_sets": 0
        }
        logger.info("Stats reset")

    def clear(self) -> None:
        """清空所有缓存"""
        with self.cache_lock:
            self.memory_cache.clear()

        self._clear_disk_cache()

        logger.info("Cache cleared")

    def _generate_key(self, signal_type: str, symbol: str, extra_key: str) -> str:
        """生成缓存键

        Args:
            signal_type: 信号类型
            symbol: 交易对符号
            extra_key: 额外的键

        Returns:
            缓存键
        """
        # 使用哈希确保键的一致性和唯一性
        key_str = f"{signal_type}|{symbol}|{extra_key}"
        key_hash = hashlib.md5(key_str.encode()).hexdigest()[:8]

        return f"{signal_type}|{symbol}|{extra_key}|{key_hash}"

    def _get_from_memory(self, cache_key: str, ttl: int) -> Optional[Dict[str, Any]]:
        """从内存缓存获取

        Args:
            cache_key: 缓存键
            ttl: TTL（秒）

        Returns:
            缓存数据或None
        """
        with self.cache_lock:
            if cache_key not in self.memory_cache:
                return None

            timestamp, data = self.memory_cache[cache_key]

            # 检查TTL
            if time.time() - timestamp < ttl:
                return data
            else:
                # 过期，删除
                del self.memory_cache[cache_key]
                return None

    def _add_to_memory(
        self,
        cache_key: str,
        data: Dict[str, Any],
        ttl: int
    ) -> None:
        """添加到内存缓存

        Args:
            cache_key: 缓存键
            data: 数据
            ttl: TTL（秒）
        """
        with self.cache_lock:
            # 检查缓存大小
            if len(self.memory_cache) >= self.max_size:
                self._evict_lru_memory_cache()

            # 添加缓存
            self.memory_cache[cache_key] = (time.time(), data)

    def _evict_lru_memory_cache(self) -> None:
        """清除最久未使用的内存缓存项"""
        if not self.memory_cache:
            return

        # 按时间戳排序，删除最旧的20%
        sorted_items = sorted(
            self.memory_cache.items(),
            key=lambda x: x[1][0]
        )
        num_to_evict = max(1, len(sorted_items) // 5)

        for key, _ in sorted_items[:num_to_evict]:
            del self.memory_cache[key]

        self.stats["evictions"] += num_to_evict
        logger.debug(f"Evicted {num_to_evict} LRU cache entries")

    def _get_from_disk(
        self,
        cache_key: str,
        ttl: int
    ) -> Optional[Dict[str, Any]]:
        """从磁盘缓存获取

        Args:
            cache_key: 缓存键
            ttl: TTL（秒）

        Returns:
            缓存数据或None
        """
        cache_file = self._get_cache_file(cache_key)

        if not cache_file.exists():
            return None

        try:
            # 读取缓存文件
            with open(cache_file, 'rb') as f:
                data = pickle.load(f)

            # 检查TTL
            timestamp = data.get("timestamp", 0)
            if time.time() - timestamp < ttl:
                return data["signal"]
            else:
                # 过期，删除
                cache_file.unlink()
                return None

        except Exception as e:
            logger.debug(f"Failed to read disk cache: {e}")
            return None

    def _add_to_disk_async(
        self,
        cache_key: str,
        signal_data: Dict[str, Any],
        ttl: int
    ) -> None:
        """异步添加到磁盘缓存

        Args:
            cache_key: 缓存键
            signal_data: 信号数据
            ttl: TTL（秒）
        """
        def _write():
            try:
                cache_file = self._get_cache_file(cache_key)

                data = {
                    "timestamp": time.time(),
                    "ttl": ttl,
                    "signal": signal_data
                }

                with open(cache_file, 'wb') as f:
                    pickle.dump(data, f)

            except Exception as e:
                logger.debug(f"Failed to write disk cache: {e}")

        # 在独立线程中写入，不阻塞主流程
        thread = threading.Thread(target=_write, daemon=True)
        thread.start()

    def _get_cache_file(self, cache_key: str) -> Path:
        """获取缓存文件路径

        Args:
            cache_key: 缓存键

        Returns:
            缓存文件路径
        """
        # 使用安全文件名
        safe_key = "".join(c if c.isalnum() or c in "-_" else "_"
                          for c in cache_key)
        return self.cache_dir / f"{safe_key}.cache"

    def _invalidate_disk(
        self,
        signal_type: Optional[str],
        symbol: Optional[str]
    ) -> None:
        """失效磁盘缓存

        Args:
            signal_type: 信号类型
            symbol: 交易对符号
        """
        try:
            for cache_file in self.cache_dir.glob("*.cache"):
                # 解析文件名中的信号类型和符号
                parts = cache_file.stem.split("|")
                file_type = parts[0] if len(parts) > 0 else None
                file_symbol = parts[1] if len(parts) > 1 else None

                if (signal_type is None or file_type == signal_type) and \
                   (symbol is None or file_symbol == symbol):
                    cache_file.unlink()

        except Exception as e:
            logger.debug(f"Failed to invalidate disk cache: {e}")

    def _get_disk_cache_size(self) -> int:
        """获取磁盘缓存大小

        Returns:
            缓存文件数量
        """
        try:
            return len(list(self.cache_dir.glob("*.cache")))
        except Exception:
            return 0

    def _clear_disk_cache(self) -> None:
        """清空磁盘缓存"""
        try:
            for cache_file in self.cache_dir.glob("*.cache"):
                cache_file.unlink()
        except Exception as e:
            logger.debug(f"Failed to clear disk cache: {e}")


class SignalFusionWithCache:
    """带缓存的信号融合

    在原有信号融合引擎基础上添加缓存层。
    """

    def __init__(
        self,
        cache_enabled: bool = True,
        cache_ttl: int = 60,
        max_cache_size: int = 1000
    ):
        """初始化带缓存的信号融合

        Args:
            cache_enabled: 是否启用缓存
            cache_ttl: 缓存TTL（秒）
            max_cache_size: 最大缓存大小
        """
        self.cache_enabled = cache_enabled

        if self.cache_enabled:
            self.cache = SignalCache(
                max_size=max_cache_size,
                default_ttl=cache_ttl
            )
            logger.info("Signal cache enabled")
        else:
            self.cache = None
            logger.info("Signal cache disabled")

        # 延迟加载信号融合引擎
        self._fusion_engine = None

    def _get_fusion_engine(self):
        """获取信号融合引擎（延迟加载）"""
        if self._fusion_engine is None:
            from llm.signal_fusion import SignalFusionEngine
            self._fusion_engine = SignalFusionEngine()

        return self._fusion_engine

    def fuse_signals_with_cache(
        self,
        llm_signal: Optional[Dict[str, Any]] = None,
        technical_signal: Optional[Dict[str, Any]] = None,
        arbitrage_signal: Optional[Dict[str, Any]] = None,
        risk_signal: Optional[Dict[str, Any]] = None,
        symbol: str = "",
        technical_indicators: Optional[Dict] = None,
        weights: Optional[Dict[str, float]] = None,
        use_dynamic_weights: bool = False
    ) -> Dict[str, Any]:
        """融合信号（带缓存）

        Args:
            llm_signal: LLM信号
            technical_signal: 技术指标信号
            arbitrage_signal: 套利信号
            risk_signal: 风险信号
            symbol: 交易对符号
            technical_indicators: 技术指标字典
            weights: 自定义权重
            use_dynamic_weights: 是否使用动态权重

        Returns:
            融合结果
        """
        fusion_engine = self._get_fusion_engine()

        # 尝试从缓存获取技术信号
        if technical_signal is None and self.cache_enabled:
            cache_key = self._generate_tech_cache_key(technical_indicators)
            cached_tech = self.cache.get(
                "technical", symbol, cache_key
            )
            if cached_tech:
                technical_signal = cached_tech

        # 尝试从缓存获取风险信号
        if risk_signal is None and self.cache_enabled:
            cache_key = self._generate_risk_cache_key(arbitrage_signal)
            cached_risk = self.cache.get(
                "risk", symbol, cache_key
            )
            if cached_risk:
                risk_signal = cached_risk

        # 融合信号
        fused = fusion_engine.fuse_signals(
            llm_signal=llm_signal,
            technical_signal=technical_signal,
            arbitrage_signal=arbitrage_signal,
            risk_signal=risk_signal,
            weights=weights,
            use_dynamic_weights=use_dynamic_weights
        )

        # 缓存计算结果
        if self.cache_enabled:
            if technical_signal:
                tech_key = self._generate_tech_cache_key(technical_indicators)
                self.cache.set("technical", symbol, technical_signal, tech_key)

            if risk_signal:
                risk_key = self._generate_risk_cache_key(arbitrage_signal)
                self.cache.set("risk", symbol, risk_signal, risk_key)

        return fused

    def _generate_tech_cache_key(self, indicators: Optional[Dict]) -> str:
        """生成技术指标缓存键"""
        if not indicators:
            return "default"

        # 使用关键指标生成键
        key_parts = [
            f"rsi_{indicators.get('rsi', 50)}",
            f"macd_{indicators.get('macd', 'neutral')}",
            f"boll_{indicators.get('bollinger', 'middle')}"
        ]

        return "_".join(key_parts)

    def _generate_risk_cache_key(self, arbitrage: Optional[Dict]) -> str:
        """生成风险信号缓存键"""
        if not arbitrage:
            return "default"

        score = arbitrage.get("_score", 50)
        volatility = arbitrage.get("volatility", 0)

        return f"score_{score}_vol_{volatility}"

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        if not self.cache:
            return {"enabled": False}

        return self.cache.get_stats()

    def clear_cache(self) -> None:
        """清空缓存"""
        if self.cache:
            self.cache.clear()


# ---------------------- 全局单例 ----------------------

_global_cache: Optional[SignalFusionWithCache] = None


def get_signal_fusion_with_cache(
    cache_enabled: bool = True,
    cache_ttl: int = 60,
    max_cache_size: int = 1000
) -> SignalFusionWithCache:
    """获取全局信号融合实例（带缓存）

    Args:
        cache_enabled: 是否启用缓存
        cache_ttl: 缓存TTL（秒）
        max_cache_size: 最大缓存大小

    Returns:
        SignalFusionWithCache实例
    """
    global _global_cache

    if _global_cache is None:
        _global_cache = SignalFusionWithCache(
            cache_enabled=cache_enabled,
            cache_ttl=cache_ttl,
            max_cache_size=max_cache_size
        )

    return _global_cache
