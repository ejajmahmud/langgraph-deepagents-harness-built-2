"""健康检查API - V5.10 Phase 5.1

提供系统健康检查和性能监控的REST API接口。

核心功能：
1. 系统健康状态检查
2. 性能指标采集
3. 组件状态监控
4. 告警规则配置

创建时间：2026-04-19
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime

# 尝试导入FastAPI，如果不存在则使用模拟实现
try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    logging.warning("FastAPI未安装，使用模拟实现")

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """健康状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class AlertSeverity(str, Enum):
    """告警严重程度"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ComponentHealth:
    """组件健康状态"""
    name: str
    status: HealthStatus
    message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    check_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'status': self.status.value,
            'message': self.message,
            'metadata': self.metadata,
            'check_time': self.check_time,
            'check_time_iso': datetime.fromtimestamp(self.check_time).isoformat()
        }


@dataclass
class PerformanceMetric:
    """性能指标"""
    name: str
    value: float
    unit: str
    timestamp: float = 0.0
    tags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'value': self.value,
            'unit': self.unit,
            'timestamp': self.timestamp,
            'timestamp_iso': datetime.fromtimestamp(self.timestamp).isoformat(),
            'tags': self.tags
        }


@dataclass
class Alert:
    """告警信息"""
    severity: AlertSeverity
    component: str
    message: str
    timestamp: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'severity': self.severity.value,
            'component': self.component,
            'message': self.message,
            'timestamp': self.timestamp,
            'timestamp_iso': datetime.fromtimestamp(self.timestamp).isoformat(),
            'metadata': self.metadata
        }


class HealthCheckAPI:
    """健康检查API系统"""

    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        """初始化健康检查API

        Args:
            host: 监听地址
            port: 监听端口
        """
        self.host = host
        self.port = port

        # 健康检查函数注册表
        self._health_checks: Dict[str, Callable[[], ComponentHealth]] = {}

        # 性能指标历史
        self._metrics_history: Dict[str, List[PerformanceMetric]] = {}
        self._max_history_size = 1000

        # 告警规则
        self._alert_rules: List[Dict[str, Any]] = []
        self._active_alerts: List[Alert] = []

        # FastAPI应用（如果可用）
        self.app = None
        if FASTAPI_AVAILABLE:
            self._setup_fastapi()

        # 后台任务
        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False

        # 统计信息
        self._stats = {
            'total_checks': 0,
            'failed_checks': 0,
            'alerts_triggered': 0
        }

    # -------------------- FastAPI集成 --------------------

    def _setup_fastapi(self) -> None:
        """设置FastAPI应用"""
        self.app = FastAPI(
            title="CryptoArbitrage Health Check API",
            description="系统健康检查和性能监控API",
            version="1.0.0"
        )

        # 注册路由
        self.app.get("/health")(self._api_health)
        self.app.get("/health/detailed")(self._api_health_detailed)
        self.app.get("/metrics")(self._api_metrics)
        self.app.get("/alerts")(self._api_alerts)
        self.app.get("/components")(self._api_components)
        self.app.post("/alert/rules")(self._api_set_alert_rules)

        logger.info(f"FastAPI应用已设置: http://{self.host}:{self.port}")

    # -------------------- API端点 --------------------

    async def _api_health(self) -> Dict[str, Any]:
        """健康检查端点（简化版）"""
        health = await self.get_overall_health()
        status_code = 200 if health.status == HealthStatus.HEALTHY else 503
        return JSONResponse(
            status_code=status_code,
            content={
                'status': health.status.value,
                'timestamp': time.time(),
                'components_count': len(self._health_checks)
            }
        )

    async def _api_health_detailed(self) -> Dict[str, Any]:
        """详细健康检查端点"""
        components = await self.check_all_components()
        overall = await self.get_overall_health()

        return {
            'overall': overall.to_dict(),
            'components': [c.to_dict() for c in components],
            'timestamp': time.time()
        }

    async def _api_metrics(self) -> Dict[str, Any]:
        """性能指标端点"""
        return {
            'metrics': [
                m.to_dict()
                for metrics_list in self._metrics_history.values()
                for m in metrics_list[-10:]  # 返回最近10条
            ],
            'components': list(self._metrics_history.keys()),
            'timestamp': time.time()
        }

    async def _api_alerts(self) -> Dict[str, Any]:
        """告警信息端点"""
        return {
            'alerts': [a.to_dict() for a in self._active_alerts],
            'rules_count': len(self._alert_rules),
            'timestamp': time.time()
        }

    async def _api_components(self) -> Dict[str, Any]:
        """组件状态端点"""
        components = await self.check_all_components()
        return {
            'components': [c.to_dict() for c in components],
            'timestamp': time.time()
        }

    async def _api_set_alert_rules(self, rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """设置告警规则端点"""
        self.set_alert_rules(rules)
        return {
            'status': 'success',
            'rules_count': len(rules),
            'timestamp': time.time()
        }

    # -------------------- 健康检查管理 --------------------

    def register_health_check(
        self,
        name: str,
        check_func: Callable[[], ComponentHealth]
    ) -> None:
        """注册健康检查函数

        Args:
            name: 组件名称
            check_func: 健康检查函数，返回ComponentHealth对象
        """
        self._health_checks[name] = check_func
        logger.info(f"注册健康检查: {name}")

    def unregister_health_check(self, name: str) -> None:
        """取消注册健康检查函数

        Args:
            name: 组件名称
        """
        if name in self._health_checks:
            del self._health_checks[name]
            logger.info(f"取消注册健康检查: {name}")

    async def check_all_components(self) -> List[ComponentHealth]:
        """检查所有组件的健康状态

        Returns:
            组件健康状态列表
        """
        results = []

        for name, check_func in self._health_checks.items():
            try:
                start_time = time.time()
                health = check_func()
                health.check_time = time.time()

                if not isinstance(health, ComponentHealth):
                    # 同步函数
                    elapsed = time.time() - start_time
                    if elapsed > 5.0:  # 超时
                        health = ComponentHealth(
                            name=name,
                            status=HealthStatus.UNHEALTHY,
                            message=f"健康检查超时 ({elapsed:.2f}秒)",
                            metadata={'check_time': elapsed}
                        )
                    else:
                        health = ComponentHealth(
                            name=name,
                            status=HealthStatus.HEALTHY,
                            message="健康检查通过",
                            metadata={'check_time': elapsed}
                        )
                results.append(health)

                self._stats['total_checks'] += 1

            except Exception as e:
                logger.error(f"组件 {name} 健康检查失败: {e}")
                results.append(ComponentHealth(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"健康检查异常: {str(e)}",
                    metadata={'error': str(e)}
                ))
                self._stats['failed_checks'] += 1

        return results

    async def get_overall_health(self) -> ComponentHealth:
        """获取系统整体健康状态

        Returns:
            整体健康状态
        """
        components = await self.check_all_components()

        if not components:
            return ComponentHealth(
                name="system",
                status=HealthStatus.UNKNOWN,
                message="无组件可检查"
            )

        # 统计各状态数量
        healthy_count = sum(1 for c in components if c.status == HealthStatus.HEALTHY)
        degraded_count = sum(1 for c in components if c.status == HealthStatus.DEGRADED)
        unhealthy_count = sum(1 for c in components if c.status == HealthStatus.UNHEALTHY)

        # 确定整体状态
        if unhealthy_count > 0:
            status = HealthStatus.UNHEALTHY
            message = f"{unhealthy_count}个组件不健康"
        elif degraded_count > 0:
            status = HealthStatus.DEGRADED
            message = f"{degraded_count}个组件降级"
        else:
            status = HealthStatus.HEALTHY
            message = "所有组件健康"

        return ComponentHealth(
            name="system",
            status=status,
            message=message,
            metadata={
                'total_components': len(components),
                'healthy': healthy_count,
                'degraded': degraded_count,
                'unhealthy': unhealthy_count
            }
        )

    # -------------------- 性能指标采集 --------------------

    def record_metric(
        self,
        name: str,
        value: float,
        unit: str = "",
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """记录性能指标

        Args:
            name: 指标名称
            value: 指标值
            unit: 单位
            tags: 标签字典
        """
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=time.time(),
            tags=tags or {}
        )

        if name not in self._metrics_history:
            self._metrics_history[name] = []

        self._metrics_history[name].append(metric)

        # 限制历史大小
        if len(self._metrics_history[name]) > self._max_history_size:
            self._metrics_history[name] = self._metrics_history[name][-self._max_history_size:]

        logger.debug(f"记录指标: {name}={value}{unit}")

    def get_metrics(self, name: Optional[str] = None, limit: int = 100) -> List[PerformanceMetric]:
        """获取性能指标

        Args:
            name: 指标名称，如果为None则返回所有指标
            limit: 返回的最大数量

        Returns:
            性能指标列表
        """
        if name:
            metrics = self._metrics_history.get(name, [])
        else:
            # 合并所有指标
            metrics = []
            for metrics_list in self._metrics_history.values():
                metrics.extend(metrics_list)

        # 按时间排序
        metrics.sort(key=lambda m: m.timestamp, reverse=True)

        return metrics[:limit]

    def get_latest_metric(self, name: str) -> Optional[PerformanceMetric]:
        """获取最新指标

        Args:
            name: 指标名称

        Returns:
            最新的性能指标，如果不存在则返回None
        """
        metrics = self._metrics_history.get(name)
        if not metrics:
            return None
        return metrics[-1]

    # -------------------- 告警管理 --------------------

    def set_alert_rules(self, rules: List[Dict[str, Any]]) -> None:
        """设置告警规则

        Args:
            rules: 告警规则列表，每个规则包含:
                - component: 组件名称
                - metric: 指标名称
                - condition: 条件 (>, <, >=, <=, ==)
                - threshold: 阈值
                - severity: 严重程度 (info, warning, error, critical)
                - message: 告警消息模板
        """
        self._alert_rules = rules
        logger.info(f"设置告警规则: {len(rules)}条")

    def check_alerts(self) -> List[Alert]:
        """检查告警条件

        Returns:
            触发的告警列表
        """
        new_alerts = []

        for rule in self._alert_rules:
            component = rule.get('component')
            metric_name = rule.get('metric')
            condition = rule.get('condition')
            threshold = rule.get('threshold')
            severity = AlertSeverity(rule.get('severity', 'warning'))
            message_template = rule.get('message', '{component}: {metric_name} {condition} {threshold}')

            # 获取最新指标
            metric = self.get_latest_metric(metric_name)
            if not metric:
                continue

            # 检查条件
            triggered = False
            if condition == '>' and metric.value > threshold:
                triggered = True
            elif condition == '<' and metric.value < threshold:
                triggered = True
            elif condition == '>=' and metric.value >= threshold:
                triggered = True
            elif condition == '<=' and metric.value <= threshold:
                triggered = True
            elif condition == '==' and metric.value == threshold:
                triggered = True

            if triggered:
                message = message_template.format(
                    component=component,
                    metric_name=metric_name,
                    metric_value=metric.value,
                    condition=condition,
                    threshold=threshold
                )

                alert = Alert(
                    severity=severity,
                    component=component,
                    message=message,
                    timestamp=time.time(),
                    metadata={
                        'metric_name': metric_name,
                        'metric_value': metric.value,
                        'threshold': threshold,
                        'condition': condition
                    }
                )

                new_alerts.append(alert)
                self._stats['alerts_triggered'] += 1
                logger.warning(f"触发告警: {message}")

        # 合并新告警到活跃告警列表
        self._active_alerts.extend(new_alerts)

        # 清理旧告警（保留最近100条）
        if len(self._active_alerts) > 100:
            self._active_alerts = self._active_alerts[-100:]

        return new_alerts

    def clear_alerts(self, component: Optional[str] = None) -> int:
        """清除告警

        Args:
            component: 组件名称，如果为None则清除所有告警

        Returns:
            清除的告警数量
        """
        if component:
            count = len([a for a in self._active_alerts if a.component == component])
            self._active_alerts = [
                a for a in self._active_alerts if a.component != component
            ]
        else:
            count = len(self._active_alerts)
            self._active_alerts.clear()

        logger.info(f"清除告警: {count}条 (组件: {component or '所有'})")
        return count

    # -------------------- 生命周期管理 --------------------

    async def start(self) -> None:
        """启动健康检查API"""
        if self._running:
            return

        self._running = True

        # 启动FastAPI应用
        if self.app:
            import uvicorn
            uvicorn.run(
                self.app,
                host=self.host,
                port=self.port,
                log_level="info"
            )
        else:
            logger.warning("FastAPI不可用，API服务未启动")

        # 启动后台监控任务
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())

        logger.info(f"健康检查API已启动: http://{self.host}:{self.port}")

    async def stop(self) -> None:
        """停止健康检查API"""
        if not self._running:
            return

        self._running = False

        # 停止后台任务
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        logger.info("健康检查API已停止")

    async def _monitoring_loop(self) -> None:
        """后台监控循环"""
        while self._running:
            try:
                await asyncio.sleep(30)  # 每30秒检查一次

                # 检查所有组件
                components = await self.check_all_components()

                # 记录组件数量指标
                self.record_metric(
                    name="components.total",
                    value=len(components),
                    unit="count",
                    tags={'status': 'all'}
                )

                healthy_count = sum(1 for c in components if c.status == HealthStatus.HEALTHY)
                self.record_metric(
                    name="components.healthy",
                    value=healthy_count,
                    unit="count"
                )

                # 检查告警
                self.check_alerts()

                # 记录告警数量指标
                self.record_metric(
                    name="alerts.active",
                    value=len(self._active_alerts),
                    unit="count"
                )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"监控循环异常: {e}")

    # -------------------- 统计信息 --------------------

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息

        Returns:
            统计信息字典
        """
        return {
            'health_checks': {
                'total': self._stats['total_checks'],
                'failed': self._stats['failed_checks'],
                'registered': len(self._health_checks)
            },
            'alerts': {
                'active': len(self._active_alerts),
                'rules': len(self._alert_rules),
                'triggered': self._stats['alerts_triggered']
            },
            'metrics': {
                'components': list(self._metrics_history.keys()),
                'total_samples': sum(
                    len(m) for m in self._metrics_history.values()
                )
            }
        }


# 全局健康检查API实例
_global_health_api: Optional[HealthCheckAPI] = None


def get_global_health_api() -> HealthCheckAPI:
    """获取全局健康检查API实例"""
    global _global_health_api
    if _global_health_api is None:
        _global_health_api = HealthCheckAPI()
    return _global_health_api


def set_global_health_api(api: HealthCheckAPI) -> None:
    """设置全局健康检查API实例"""
    global _global_health_api
    _global_health_api = api
