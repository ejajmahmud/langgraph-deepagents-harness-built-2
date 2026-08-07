"""实时告警系统与多区域部署模块 V72.0 - Phase 16

核心功能：
- AlertRule: 告警规则
- RealTimeAlert: 实时告警引擎
- RegionManager: 多区域管理器
- RegionNode: 区域节点
- AnalyticsEngine: 分析引擎
- TrendAnalyzer: 趋势分析
- AnomalyDetector: 异常检测

创建时间：2026-05-08 22:50
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import time
import threading
import random


# ============ 枚举定义 ============

class AlertPriority(Enum):
    """告警优先级"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AlertState(Enum):
    """告警状态"""
    FIRED = "fired"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class RegionStatus(Enum):
    """区域状态"""
    ACTIVE = "active"
    DEGRADED = "degraded"
    INACTIVE = "inactive"


class AnalyticsPeriod(Enum):
    """分析周期"""
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    DAY_1 = "1d"


# ============ 数据结构 ============

@dataclass
class AlertRule:
    """告警规则"""
    rule_id: str
    name: str
    condition: Callable[[], bool]
    priority: AlertPriority
    enabled: bool = True
    cooldown: int = 60


@dataclass
class AlertEvent:
    """告警事件"""
    event_id: str
    rule_id: str
    priority: AlertPriority
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    state: AlertState = AlertState.FIRED
    region: str = "default"


@dataclass
class RegionNode:
    """区域节点"""
    node_id: str
    region: str
    host: str
    port: int
    status: RegionStatus = RegionStatus.ACTIVE
    priority: int = 1
    last_health_check: float = field(default_factory=time.time)


@dataclass
class AnalyticsResult:
    """分析结果"""
    period: AnalyticsPeriod
    timestamp: datetime = field(default_factory=datetime.now)
    avg_value: float = 0.0
    max_value: float = 0.0
    min_value: float = 0.0
    trend: str = "stable"
    anomaly_detected: bool = False


# ============ RealTimeAlert ============

class RealTimeAlert:
    """实时告警引擎"""

    def __init__(self):
        self._rules: Dict[str, AlertRule] = {}
        self._events: List[AlertEvent] = []
        self._last_fired: Dict[str, float] = {}
        self._lock = threading.RLock()
        self._event_counter = 0

    def add_rule(
        self,
        rule_id: str,
        name: str,
        condition: Callable[[], bool],
        priority: AlertPriority,
        cooldown: int = 60
    ):
        """添加规则"""
        with self._lock:
            self._rules[rule_id] = AlertRule(
                rule_id=rule_id,
                name=name,
                condition=condition,
                priority=priority,
                cooldown=cooldown
            )

    def remove_rule(self, rule_id: str) -> bool:
        """移除规则"""
        with self._lock:
            if rule_id in self._rules:
                del self._rules[rule_id]
                return True
            return False

    def enable_rule(self, rule_id: str, enabled: bool = True):
        """启用/禁用规则"""
        with self._lock:
            if rule_id in self._rules:
                self._rules[rule_id].enabled = enabled

    def evaluate(self) -> List[AlertEvent]:
        """评估所有规则"""
        with self._lock:
            now = time.time()
            fired_events = []

            for rule in self._rules.values():
                if not rule.enabled:
                    continue

                # 检查冷却时间
                last_fired = self._last_fired.get(rule.rule_id, 0)
                if now - last_fired < rule.cooldown:
                    continue

                try:
                    if rule.condition():
                        self._event_counter += 1
                        event = AlertEvent(
                            event_id=f"ALERT_{self._event_counter:06d}",
                            rule_id=rule.rule_id,
                            priority=rule.priority,
                            message=f"Alert: {rule.name}"
                        )
                        self._events.append(event)
                        self._last_fired[rule.rule_id] = now
                        fired_events.append(event)
                except Exception:
                    pass

            return fired_events

    def get_events(
        self,
        state: Optional[AlertState] = None,
        limit: int = 100
    ) -> List[AlertEvent]:
        """获取事件"""
        with self._lock:
            events = self._events
            if state:
                events = [e for e in events if e.state == state]
            return events[-limit:]

    def acknowledge_event(self, event_id: str) -> bool:
        """确认事件"""
        with self._lock:
            for event in self._events:
                if event.event_id == event_id:
                    event.state = AlertState.ACKNOWLEDGED
                    return True
            return False

    def resolve_event(self, event_id: str) -> bool:
        """解决事件"""
        with self._lock:
            for event in self._events:
                if event.event_id == event_id:
                    event.state = AlertState.RESOLVED
                    return True
            return False


# ============ RegionManager ============

class RegionManager:
    """多区域管理器"""

    def __init__(self):
        self._regions: Dict[str, Dict[str, RegionNode]] = {}
        self._default_region = "us-east"
        self._lock = threading.RLock()

    def add_region(self, region: str):
        """添加区域"""
        with self._lock:
            self._regions.setdefault(region, {})

    def add_node(
        self,
        node_id: str,
        region: str,
        host: str,
        port: int,
        priority: int = 1
    ):
        """添加节点"""
        with self._lock:
            self._regions.setdefault(region, {})[node_id] = RegionNode(
                node_id=node_id,
                region=region,
                host=host,
                port=port,
                priority=priority
            )

    def remove_node(self, node_id: str, region: str) -> bool:
        """移除节点"""
        with self._lock:
            if region in self._regions:
                if node_id in self._regions[region]:
                    del self._regions[region][node_id]
                    return True
            return False

    def get_nodes(self, region: str) -> List[RegionNode]:
        """获取区域节点"""
        with self._lock:
            if region in self._regions:
                return list(self._regions[region].values())
            return []

    def get_primary_node(self, region: Optional[str] = None) -> Optional[RegionNode]:
        """获取主节点"""
        region = region or self._default_region
        with self._lock:
            if region in self._regions:
                nodes = sorted(
                    self._regions[region].values(),
                    key=lambda n: n.priority
                )
                for node in nodes:
                    if node.status == RegionStatus.ACTIVE:
                        return node
            return None

    def update_health(self, node_id: str, region: str, healthy: bool):
        """更新健康状态"""
        with self._lock:
            if region in self._regions and node_id in self._regions[region]:
                node = self._regions[region][node_id]
                node.status = RegionStatus.ACTIVE if healthy else RegionStatus.DEGRADED
                node.last_health_check = time.time()

    def get_all_regions(self) -> List[str]:
        """获取所有区域"""
        return list(self._regions.keys())


# ============ AnalyticsEngine ============

class AnalyticsEngine:
    """分析引擎"""

    def __init__(self):
        self._data: Dict[str, List[float]] = {}
        self._lock = threading.RLock()

    def record(self, metric: str, value: float):
        """记录数据点"""
        with self._lock:
            self._data.setdefault(metric, []).append(value)
            # 保留最近10000个数据点
            if len(self._data[metric]) > 10000:
                self._data[metric] = self._data[metric][-10000:]

    def get_trend(self, metric: str, period: AnalyticsPeriod = AnalyticsPeriod.HOUR_1) -> str:
        """获取趋势"""
        with self._lock:
            values = self._data.get(metric, [])
            if len(values) < 10:
                return "insufficient_data"

            # 简单趋势判断：比较前半和后半
            mid = len(values) // 2
            first_half = values[:mid]
            second_half = values[mid:]

            first_avg = sum(first_half) / len(first_half)
            second_avg = sum(second_half) / len(second_half)

            change_pct = (second_avg - first_avg) / first_avg if first_avg > 0 else 0

            if change_pct > 0.05:
                return "uptrend"
            elif change_pct < -0.05:
                return "downtrend"
            return "stable"

    def detect_anomaly(self, metric: str, threshold: float = 3.0) -> bool:
        """检测异常"""
        with self._lock:
            values = self._data.get(metric, [])
            if len(values) < 20:
                return False

            # 计算均值和标准差
            mean = sum(values) / len(values)
            variance = sum((x - mean) ** 2 for x in values) / len(values)
            std = variance ** 0.5

            if std == 0:
                return False

            # 检查最新值
            latest = values[-1]
            z_score = abs(latest - mean) / std

            return z_score > threshold

    def analyze(
        self,
        metric: str,
        period: AnalyticsPeriod = AnalyticsPeriod.HOUR_1
    ) -> AnalyticsResult:
        """完整分析"""
        with self._lock:
            values = self._data.get(metric, [])

            if not values:
                return AnalyticsResult(period=period)

            return AnalyticsResult(
                period=period,
                avg_value=sum(values) / len(values),
                max_value=max(values),
                min_value=min(values),
                trend=self.get_trend(metric, period),
                anomaly_detected=self.detect_anomaly(metric)
            )


# ============ 全局函数 ============

_real_time_alert: Optional[RealTimeAlert] = None
_region_manager: Optional[RegionManager] = None
_analytics_engine: Optional[AnalyticsEngine] = None


def get_real_time_alert() -> RealTimeAlert:
    """获取实时告警引擎"""
    global _real_time_alert
    if _real_time_alert is None:
        _real_time_alert = RealTimeAlert()
    return _real_time_alert


def initialize_real_time_alert():
    """初始化实时告警引擎"""
    global _real_time_alert
    _real_time_alert = RealTimeAlert()
    return _real_time_alert


def get_region_manager() -> RegionManager:
    """获取区域管理器"""
    global _region_manager
    if _region_manager is None:
        _region_manager = RegionManager()
    return _region_manager


def initialize_region_manager():
    """初始化区域管理器"""
    global _region_manager
    _region_manager = RegionManager()
    return _region_manager


def get_analytics_engine() -> AnalyticsEngine:
    """获取分析引擎"""
    global _analytics_engine
    if _analytics_engine is None:
        _analytics_engine = AnalyticsEngine()
    return _analytics_engine


def initialize_analytics_engine():
    """初始化分析引擎"""
    global _analytics_engine
    _analytics_engine = AnalyticsEngine()
    return _analytics_engine


def create_alert_rule(
    rule_id: str,
    name: str,
    condition,
    priority: AlertPriority,
    cooldown: int = 60
) -> AlertRule:
    """创建告警规则"""
    return AlertRule(
        rule_id=rule_id,
        name=name,
        condition=condition,
        priority=priority,
        cooldown=cooldown
    )


# ============ 版本信息 ============

__version__ = "1.8.0"
__phase__ = "Phase 16: 实时告警与多区域部署"