"""高级缓存策略与分布式监控模块 V71.0 - Phase 15

核心功能：
- LRUCache: LRU缓存实现
- DistributedCache: 分布式缓存
- CacheWarmer: 缓存预热
- DistributedMonitor: 分布式监控
- MetricsAggregator: 指标聚合
- AutoScaler: 自动扩缩容
- LoadBalancer: 负载均衡

创建时间：2026-05-08 22:35
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from collections import OrderedDict
import time
import threading
import hashlib


# ============ 枚举定义 ============

class CacheStrategy(Enum):
    """缓存策略"""
    LRU = "lru"           # 最近最少使用
    LFU = "lfu"           # 最不经常使用
    FIFO = "fifo"         # 先进先出
    TTL = "ttl"           # 时间过期


class MonitorNodeStatus(Enum):
    """监控节点状态"""
    ACTIVE = "active"
    STANDBY = "standby"
    FAILED = "failed"


class ScalingDirection(Enum):
    """扩缩容方向"""
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    STABLE = "stable"


# ============ 数据结构 ============

@dataclass
class CacheStats:
    """缓存统计"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size: int = 0
    hit_rate: float = 0.0


@dataclass
class MonitorNode:
    """监控节点"""
    node_id: str
    host: str
    port: int
    status: MonitorNodeStatus = MonitorNodeStatus.ACTIVE
    last_heartbeat: float = field(default_factory=time.time)
    metrics: Dict = field(default_factory=dict)


@dataclass
class AggregatedMetrics:
    """聚合指标"""
    timestamp: datetime = field(default_factory=datetime.now)
    node_count: int = 0
    total_requests: float = 0.0
    avg_latency: float = 0.0
    p95_latency: float = 0.0
    error_rate: float = 0.0
    throughput: float = 0.0


@dataclass
class ScalingDecision:
    """扩缩容决策"""
    direction: ScalingDirection
    reason: str
    current_instances: int = 1
    recommended_instances: int = 1
    confidence: float = 0.0


@dataclass
class LoadBalancerTarget:
    """负载均衡目标"""
    host: str
    port: int
    weight: int = 1
    active: bool = True


# ============ LRUCache ============

class LRUCache:
    """LRU缓存"""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: OrderedDict = OrderedDict()
        self._stats = CacheStats()
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        with self._lock:
            if key not in self._cache:
                self._stats.misses += 1
                return None

            # 移动到末尾(最新)
            self._cache.move_to_end(key)
            self._stats.hits += 1
            return self._cache[key]

    def set(self, key: str, value: Any):
        """设置缓存"""
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            else:
                if len(self._cache) >= self.max_size:
                    # 删除最老的
                    self._cache.popitem(last=False)
                    self._stats.evictions += 1

            self._cache[key] = value

    def delete(self, key: str) -> bool:
        """删除缓存"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._stats = CacheStats()

    def get_stats(self) -> CacheStats:
        """获取统计"""
        with self._lock:
            total = self._stats.hits + self._stats.misses
            self._stats.hit_rate = self._stats.hits / total if total > 0 else 0
            self._stats.size = len(self._cache)
            return self._stats

    def keys(self) -> List[str]:
        """获取所有键"""
        return list(self._cache.keys())


# ============ DistributedCache ============

class DistributedCache:
    """分布式缓存"""

    def __init__(self, strategy: CacheStrategy = CacheStrategy.LRU, max_size: int = 5000):
        self.strategy = strategy
        self.max_size = max_size
        self._cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, float] = {}
        self._access_counts: Dict[str, int] = {}
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        with self._lock:
            if key not in self._cache:
                return None

            if self.strategy == CacheStrategy.TTL:
                if time.time() > self._timestamps.get(key, 0):
                    del self._cache[key]
                    return None

            self._access_counts[key] = self._access_counts.get(key, 0) + 1
            return self._cache[key]

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置缓存"""
        with self._lock:
            if len(self._cache) >= self.max_size:
                self._evict()

            self._cache[key] = value
            self._timestamps[key] = time.time() + (ttl or 3600)
            self._access_counts[key] = 0

    def _evict(self):
        """淘汰条目"""
        if self.strategy == CacheStrategy.LRU:
            oldest = min(self._timestamps.items(), key=lambda x: x[1])
            del self._cache[oldest[0]]
        elif self.strategy == CacheStrategy.LFU:
            least_used = min(self._access_counts.items(), key=lambda x: x[1])
            del self._cache[least_used[0]]

    def get_stats(self) -> Dict[str, Any]:
        """获取统计"""
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "strategy": self.strategy.value,
        }


# ============ CacheWarmer ============

class CacheWarmer:
    """缓存预热器"""

    def __init__(self, cache: LRUCache):
        self.cache = cache
        self._warming = False
        self._lock = threading.Lock()

    def warm(self, data: Dict[str, Any], async_warm: bool = True):
        """预热缓存"""
        if async_warm:
            thread = threading.Thread(target=self._warm_async, args=(data,))
            thread.start()
        else:
            self._warm_async(data)

    def _warm_async(self, data: Dict[str, Any]):
        """异步预热"""
        with self._lock:
            self._warming = True

        try:
            for key, value in data.items():
                self.cache.set(key, value)
        finally:
            self._warming = False

    def is_warming(self) -> bool:
        """是否正在预热"""
        return self._warming


# ============ DistributedMonitor ============

class DistributedMonitor:
    """分布式监控"""

    def __init__(self, node_id: str):
        self.node_id = node_id
        self._nodes: Dict[str, MonitorNode] = {}
        self._local_metrics: Dict[str, List] = {}
        self._lock = threading.RLock()

    def register_node(self, node_id: str, host: str, port: int):
        """注册节点"""
        with self._lock:
            self._nodes[node_id] = MonitorNode(
                node_id=node_id,
                host=host,
                port=port
            )

    def update_heartbeat(self, node_id: str):
        """更新心跳"""
        with self._lock:
            if node_id in self._nodes:
                self._nodes[node_id].last_heartbeat = time.time()
                self._nodes[node_id].status = MonitorNodeStatus.ACTIVE

    def report_metrics(self, node_id: str, metrics: Dict):
        """报告指标"""
        with self._lock:
            if node_id in self._nodes:
                self._nodes[node_id].metrics = metrics

    def get_active_nodes(self) -> List[MonitorNode]:
        """获取活跃节点"""
        with self._lock:
            return [
                n for n in self._nodes.values()
                if n.status == MonitorNodeStatus.ACTIVE
            ]

    def aggregate_metrics(self) -> AggregatedMetrics:
        """聚合指标"""
        with self._lock:
            active = self.get_active_nodes()
            if not active:
                return AggregatedMetrics()

            total_requests = sum(n.metrics.get("requests", 0) for n in active)
            total_latency = sum(n.metrics.get("latency", 0) for n in active)
            total_errors = sum(n.metrics.get("errors", 0) for n in active)

            return AggregatedMetrics(
                node_count=len(active),
                total_requests=total_requests,
                avg_latency=total_latency / len(active) if active else 0,
                error_rate=total_errors / total_requests if total_requests > 0 else 0
            )


# ============ MetricsAggregator ============

class MetricsAggregator:
    """指标聚合器"""

    def __init__(self):
        self._metrics: Dict[str, List[float]] = {}
        self._lock = threading.RLock()

    def record(self, name: str, value: float):
        """记录指标"""
        with self._lock:
            self._metrics.setdefault(name, []).append(value)

    def get_percentile(self, name: str, percentile: float) -> float:
        """获取百分位"""
        with self._lock:
            values = sorted(self._metrics.get(name, []))
            if not values:
                return 0.0

            idx = int(len(values) * percentile / 100)
            return values[min(idx, len(values) - 1)]

    def get_stats(self, name: str) -> Optional[Dict[str, float]]:
        """获取统计"""
        with self._lock:
            values = self._metrics.get(name, [])
            if not values:
                return None

            return {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "p50": self.get_percentile(name, 50),
                "p95": self.get_percentile(name, 95),
                "p99": self.get_percentile(name, 99),
            }

    def clear(self):
        """清空指标"""
        with self._lock:
            self._metrics.clear()


# ============ AutoScaler ============

class AutoScaler:
    """自动扩缩容器"""

    def __init__(self, min_instances: int = 1, max_instances: int = 10):
        self.min_instances = min_instances
        self.max_instances = max_instances
        self._metrics_history: List[AggregatedMetrics] = []
        self._lock = threading.RLock()

    def record_metrics(self, metrics: AggregatedMetrics):
        """记录指标"""
        with self._lock:
            self._metrics_history.append(metrics)
            # 保留最近100条
            self._metrics_history = self._metrics_history[-100:]

    def evaluate(self) -> ScalingDecision:
        """评估扩缩容"""
        with self._lock:
            if not self._metrics_history:
                return ScalingDecision(
                    direction=ScalingDirection.STABLE,
                    reason="No metrics available"
                )

            recent = self._metrics_history[-10:]
            avg_latency = sum(m.avg_latency for m in recent) / len(recent)
            avg_throughput = sum(m.throughput for m in recent) / len(recent)
            avg_errors = sum(m.error_rate for m in recent) / len(recent)

            # 高延迟或高错误率 -> 扩容
            if avg_latency > 1000 or avg_errors > 0.05:
                return ScalingDecision(
                    direction=ScalingDirection.SCALE_UP,
                    reason=f"High latency={avg_latency:.0f}ms or errors={avg_errors:.2%}",
                    current_instances=1,
                    recommended_instances=min(1 + 1, self.max_instances),
                    confidence=0.8
                )

            # 低延迟和低吞吐量 -> 缩容
            if avg_latency < 100 and avg_throughput < 100:
                return ScalingDecision(
                    direction=ScalingDirection.SCALE_DOWN,
                    reason=f"Low latency={avg_latency:.0f}ms and throughput={avg_throughput:.0f}",
                    current_instances=1,
                    recommended_instances=max(1 - 1, self.min_instances),
                    confidence=0.7
                )

            return ScalingDecision(
                direction=ScalingDirection.STABLE,
                reason="Metrics within normal range"
            )


# ============ LoadBalancer ============

class LoadBalancer:
    """负载均衡器"""

    def __init__(self, strategy: str = "round_robin"):
        self.strategy = strategy
        self._targets: List[LoadBalancerTarget] = []
        self._current = 0
        self._lock = threading.RLock()

    def add_target(self, host: str, port: int, weight: int = 1):
        """添加目标"""
        with self._lock:
            self._targets.append(LoadBalancerTarget(
                host=host,
                port=port,
                weight=weight
            ))

    def remove_target(self, host: str, port: int) -> bool:
        """移除目标"""
        with self._lock:
            for i, t in enumerate(self._targets):
                if t.host == host and t.port == port:
                    del self._targets[i]
                    return True
            return False

    def get_target(self) -> Optional[LoadBalancerTarget]:
        """获取目标"""
        with self._lock:
            active = [t for t in self._targets if t.active]
            if not active:
                return None

            if self.strategy == "round_robin":
                target = active[self._current % len(active)]
                self._current += 1
                return target
            elif self.strategy == "random":
                import random
                return random.choice(active)
            elif self.strategy == "weighted":
                # 权重随机
                import random
                weights = [t.weight for t in active]
                return random.choices(active, weights=weights)[0]

            return active[0]

    def set_active(self, host: str, port: int, active: bool):
        """设置目标状态"""
        with self._lock:
            for t in self._targets:
                if t.host == host and t.port == port:
                    t.active = active


# ============ 全局函数 ============

_lru_cache: Optional[LRUCache] = None
_distributed_cache: Optional[DistributedCache] = None
_cache_warmer: Optional[CacheWarmer] = None
_distributed_monitor: Optional[DistributedMonitor] = None
_metrics_aggregator: Optional[MetricsAggregator] = None
_auto_scaler: Optional[AutoScaler] = None
_load_balancer: Optional[LoadBalancer] = None


def get_lru_cache() -> LRUCache:
    """获取LRU缓存"""
    global _lru_cache
    if _lru_cache is None:
        _lru_cache = LRUCache()
    return _lru_cache


def initialize_lru_cache(max_size: int = 1000):
    """初始化LRU缓存"""
    global _lru_cache
    _lru_cache = LRUCache(max_size)
    return _lru_cache


def get_distributed_cache() -> DistributedCache:
    """获取分布式缓存"""
    global _distributed_cache
    if _distributed_cache is None:
        _distributed_cache = DistributedCache()
    return _distributed_cache


def initialize_distributed_cache(strategy: CacheStrategy = CacheStrategy.LRU, max_size: int = 5000):
    """初始化分布式缓存"""
    global _distributed_cache
    _distributed_cache = DistributedCache(strategy, max_size)
    return _distributed_cache


def get_cache_warmer() -> CacheWarmer:
    """获取缓存预热器"""
    global _cache_warmer
    if _cache_warmer is None:
        _cache_warmer = CacheWarmer(get_lru_cache())
    return _cache_warmer


def initialize_cache_warmer(cache: LRUCache):
    """初始化缓存预热器"""
    global _cache_warmer
    _cache_warmer = CacheWarmer(cache)
    return _cache_warmer


def get_distributed_monitor(node_id: str) -> DistributedMonitor:
    """获取分布式监控"""
    global _distributed_monitor
    if _distributed_monitor is None:
        _distributed_monitor = DistributedMonitor(node_id)
    return _distributed_monitor


def initialize_distributed_monitor(node_id: str):
    """初始化分布式监控"""
    global _distributed_monitor
    _distributed_monitor = DistributedMonitor(node_id)
    return _distributed_monitor


def get_metrics_aggregator() -> MetricsAggregator:
    """获取指标聚合器"""
    global _metrics_aggregator
    if _metrics_aggregator is None:
        _metrics_aggregator = MetricsAggregator()
    return _metrics_aggregator


def initialize_metrics_aggregator():
    """初始化指标聚合器"""
    global _metrics_aggregator
    _metrics_aggregator = MetricsAggregator()
    return _metrics_aggregator


def get_auto_scaler() -> AutoScaler:
    """获取自动扩缩容器"""
    global _auto_scaler
    if _auto_scaler is None:
        _auto_scaler = AutoScaler()
    return _auto_scaler


def initialize_auto_scaler(min_instances: int = 1, max_instances: int = 10):
    """初始化自动扩缩容器"""
    global _auto_scaler
    _auto_scaler = AutoScaler(min_instances, max_instances)
    return _auto_scaler


def get_load_balancer() -> LoadBalancer:
    """获取负载均衡器"""
    global _load_balancer
    if _load_balancer is None:
        _load_balancer = LoadBalancer()
    return _load_balancer


def initialize_load_balancer(strategy: str = "round_robin"):
    """初始化负载均衡器"""
    global _load_balancer
    _load_balancer = LoadBalancer(strategy)
    return _load_balancer


def create_lru_cache(max_size: int = 1000) -> LRUCache:
    """创建LRU缓存"""
    return LRUCache(max_size)


def create_distributed_cache(
    strategy: CacheStrategy = CacheStrategy.LRU,
    max_size: int = 5000
) -> DistributedCache:
    """创建分布式缓存"""
    return DistributedCache(strategy, max_size)


# ============ 版本信息 ============

__version__ = "1.7.0"
__phase__ = "Phase 15: 高级缓存与分布式监控"