"""系统健康监控器 V3.7 - 24/7 全方位健康监控

提供生产级的系统健康监控，实时检测和报告系统状态。
核心功能：
1. 多维度健康检查 - 组件、数据、网络、资源
2. 实时健康评分 - 综合评估系统状态
3. 多级健康状态 - HEALTHY/DEGRADED/UNHEALTHY/CRITICAL
4. 自动降级检测 - 识别性能下降
5. 趋势分析 - 预测潜在问题
"""

import asyncio
import logging
import psutil
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """健康状态"""
    HEALTHY = "HEALTHY"  # 完全健康
    DEGRADED = "DEGRADED"  # 性能下降
    UNHEALTHY = "UNHEALTHY"  # 部分功能异常
    CRITICAL = "CRITICAL"  # 严重故障


class HealthCheckType(Enum):
    """健康检查类型"""
    COMPONENT = "COMPONENT"  # 组件检查
    DATABASE = "DATABASE"  # 数据库检查
    NETWORK = "NETWORK"  # 网络检查
    RESOURCE = "RESOURCE"  # 资源检查
    PERFORMANCE = "PERFORMANCE"  # 性能检查


@dataclass
class HealthCheckResult:
    """健康检查结果"""
    check_name: str
    check_type: HealthCheckType
    status: HealthStatus
    score: float  # 0-100
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    execution_time: float = 0.0
    critical: bool = False  # 是否为关键检查


@dataclass
class HealthReport:
    """健康报告"""
    overall_status: HealthStatus
    overall_score: float
    timestamp: datetime
    checks: List[HealthCheckResult]
    components: Dict[str, Any]
    recommendations: List[str]
    trends: Dict[str, Any]


class HealthCheck:
    """健康检查基类"""

    def __init__(
        self,
        name: str,
        check_type: HealthCheckType,
        critical: bool = False,
        timeout: float = 30.0
    ):
        """初始化健康检查

        Args:
            name: 检查名称
            check_type: 检查类型
            critical: 是否为关键检查
            timeout: 超时时间（秒）
        """
        self.name = name
        self.check_type = check_type
        self.critical = critical
        self.timeout = timeout

        # 历史结果
        self.history: deque = deque(maxlen=100)
        self.last_check: Optional[datetime] = None

    async def execute(self) -> HealthCheckResult:
        """执行健康检查

        Returns:
            检查结果
        """
        start_time = time.time()

        try:
            # 执行实际检查
            result = await self._check()
            result.check_name = self.name
            result.check_type = self.check_type

        except asyncio.TimeoutError:
            result = HealthCheckResult(
                check_name=self.name,
                check_type=self.check_type,
                status=HealthStatus.UNHEALTHY if not self.critical else HealthStatus.CRITICAL,
                score=0.0,
                message=f"检查超时（{self.timeout}秒）",
                execution_time=self.timeout
            )

        except Exception as e:
            result = HealthCheckResult(
                check_name=self.name,
                check_type=self.check_type,
                status=HealthStatus.UNHEALTHY if not self.critical else HealthStatus.CRITICAL,
                score=0.0,
                message=f"检查异常: {str(e)}",
                details={'exception': str(e)},
                execution_time=time.time() - start_time
            )

        result.execution_time = time.time() - start_time
        result.timestamp = datetime.now()

        # 记录历史
        self.history.append(result)
        self.last_check = result.timestamp

        return result

    async def _check(self) -> HealthCheckResult:
        """实际检查逻辑（子类实现）"""
        raise NotImplementedError


class ComponentHealthCheck(HealthCheck):
    """组件健康检查"""

    def __init__(
        self,
        name: str,
        component: Any,
        critical: bool = True
    ):
        """初始化组件检查

        Args:
            name: 检查名称
            component: 组件实例
            critical: 是否关键
        """
        super().__init__(name, HealthCheckType.COMPONENT, critical)
        self.component = component

    async def _check(self) -> HealthCheckResult:
        """检查组件状态"""
        # 检查组件是否存在
        if self.component is None:
            return HealthCheckResult(
                check_name=self.name,
                check_type=self.check_type,
                status=HealthStatus.CRITICAL if self.critical else HealthStatus.UNHEALTHY,
                score=0.0,
                message=f"组件 {self.name} 未初始化"
            )

        # 检查组件方法
        try:
            if hasattr(self.component, 'get_status'):
                status = self.component.get_status()
                if status.get('healthy', True):
                    return HealthCheckResult(
                        check_name=self.name,
                        check_type=self.check_type,
                        status=HealthStatus.HEALTHY,
                        score=100.0,
                        message=f"组件 {self.name} 正常运行",
                        details=status
                    )
                else:
                    return HealthCheckResult(
                        check_name=self.name,
                        check_type=self.check_type,
                        status=HealthStatus.DEGRADED if not self.critical else HealthStatus.UNHEALTHY,
                        score=50.0,
                        message=f"组件 {self.name} 状态异常: {status.get('message', '未知原因')}",
                        details=status
                    )

            # 如果没有 get_status 方法，检查是否可调用
            elif callable(self.component):
                # 尝试调用
                result = self.component()
                return HealthCheckResult(
                    check_name=self.name,
                    check_type=self.check_type,
                    status=HealthStatus.HEALTHY,
                    score=100.0,
                    message=f"组件 {self.name} 可用",
                    details={'result': str(result)[:100]}
                )

            else:
                return HealthCheckResult(
                    check_name=self.name,
                    check_type=self.check_type,
                    status=HealthStatus.HEALTHY,
                    score=100.0,
                    message=f"组件 {self.name} 存在但无状态方法",
                    details={'type': str(type(self.component))}
                )

        except Exception as e:
            return HealthCheckResult(
                check_name=self.name,
                check_type=self.check_type,
                status=HealthStatus.UNHEALTHY if not self.critical else HealthStatus.CRITICAL,
                score=0.0,
                message=f"组件 {self.name} 检查失败: {str(e)}",
                details={'exception': str(e)}
            )


class DatabaseHealthCheck(HealthCheck):
    """数据库健康检查"""

    def __init__(
        self,
        name: str,
        db_connection,
        critical: bool = True
    ):
        """初始化数据库检查

        Args:
            name: 检查名称
            db_connection: 数据库连接
            critical: 是否关键
        """
        super().__init__(name, HealthCheckType.DATABASE, critical)
        self.db = db_connection

    async def _check(self) -> HealthCheckResult:
        """检查数据库状态"""
        try:
            cursor = self.db.cursor()

            # 测试查询
            cursor.execute("SELECT 1")
            result = cursor.fetchone()

            # 检查数据库大小
            cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
            size_info = cursor.fetchone()
            db_size_mb = size_info[0] / (1024 * 1024) if size_info else 0

            # 检查表数量
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]

            # 计算得分（基于数据库大小）
            score = max(0, 100 - db_size_mb / 10)  # 超大数据库降低得分

            return HealthCheckResult(
                check_name=self.name,
                check_type=self.check_type,
                status=HealthStatus.HEALTHY,
                score=score,
                message=f"数据库正常 - {table_count} 个表, 大小: {db_size_mb:.2f} MB",
                details={
                    'table_count': table_count,
                    'size_mb': db_size_mb,
                    'test_query_result': result
                }
            )

        except Exception as e:
            return HealthCheckResult(
                check_name=self.name,
                check_type=self.check_type,
                status=HealthStatus.CRITICAL,
                score=0.0,
                message=f"数据库检查失败: {str(e)}",
                details={'exception': str(e)}
            )


class ResourceHealthCheck(HealthCheck):
    """资源健康检查"""

    def __init__(self, name: str, resource_type: str, thresholds: Dict[str, float]):
        """初始化资源检查

        Args:
            name: 检查名称
            resource_type: 资源类型 (cpu/memory/disk)
            thresholds: 阈值配置
                - warning: 警告阈值
                - critical: 严重阈值
        """
        super().__init__(name, HealthCheckType.RESOURCE, critical=True)
        self.resource_type = resource_type
        self.thresholds = thresholds

    async def _check(self) -> HealthCheckResult:
        """检查资源使用情况"""
        try:
            if self.resource_type == 'cpu':
                usage = psutil.cpu_percent(interval=1)
                unit = '%'

            elif self.resource_type == 'memory':
                mem = psutil.virtual_memory()
                usage = mem.percent
                unit = '%'

            elif self.resource_type == 'disk':
                disk = psutil.disk_usage('/')
                usage = disk.percent
                unit = '%'

            else:
                return HealthCheckResult(
                    check_name=self.name,
                    check_type=self.check_type,
                    status=HealthStatus.UNHEALTHY,
                    score=0.0,
                    message=f"未知资源类型: {self.resource_type}"
                )

            # 根据使用率确定状态
            warning_threshold = self.thresholds.get('warning', 70)
            critical_threshold = self.thresholds.get('critical', 90)

            if usage >= critical_threshold:
                status = HealthStatus.CRITICAL
                score = 0.0
                message = f"{self.resource_type.upper()} 使用率严重: {usage:.1f}{unit}"

            elif usage >= warning_threshold:
                status = HealthStatus.DEGRADED
                score = 50.0
                message = f"{self.resource_type.upper()} 使用率较高: {usage:.1f}{unit}"

            else:
                status = HealthStatus.HEALTHY
                score = 100.0 - usage * 0.5  # 使用率越低得分越高
                message = f"{self.resource_type.upper()} 使用正常: {usage:.1f}{unit}"

            return HealthCheckResult(
                check_name=self.name,
                check_type=self.check_type,
                status=status,
                score=score,
                message=message,
                details={
                    'usage': usage,
                    'unit': unit,
                    'thresholds': self.thresholds
                }
            )

        except Exception as e:
            return HealthCheckResult(
                check_name=self.name,
                check_type=self.check_type,
                status=HealthStatus.UNHEALTHY,
                score=0.0,
                message=f"资源检查失败: {str(e)}",
                details={'exception': str(e)}
            )


class PerformanceHealthCheck(HealthCheck):
    """性能健康检查"""

    def __init__(
        self,
        name: str,
        performance_monitor,
        metrics: List[str],
        thresholds: Dict[str, float]
    ):
        """初始化性能检查

        Args:
            name: 检查名称
            performance_monitor: 性能监控器
            metrics: 要检查的指标列表
            thresholds: 指标阈值
        """
        super().__init__(name, HealthCheckType.PERFORMANCE, critical=False)
        self.monitor = performance_monitor
        self.metrics = metrics
        self.thresholds = thresholds

    async def _check(self) -> HealthCheckResult:
        """检查性能指标"""
        try:
            issues = []
            total_score = 0.0

            for metric_name in self.metrics:
                # 获取指标统计
                stats = self.monitor.get_metric_stats(metric_name)

                if not stats:
                    continue

                # 检查是否超过阈值
                threshold = self.thresholds.get(metric_name)
                if threshold and stats['mean'] > threshold:
                    issues.append(f"{metric_name}: {stats['mean']:.4f} > {threshold}")
                else:
                    total_score += 100.0 / len(self.metrics)

            if issues:
                return HealthCheckResult(
                    check_name=self.name,
                    check_type=self.check_type,
                    status=HealthStatus.DEGRADED if len(issues) < 3 else HealthStatus.UNHEALTHY,
                    score=total_score,
                    message=f"发现 {len(issues)} 个性能问题",
                    details={'issues': issues}
                )
            else:
                return HealthCheckResult(
                    check_name=self.name,
                    check_type=self.check_type,
                    status=HealthStatus.HEALTHY,
                    score=100.0,
                    message="性能指标正常"
                )

        except Exception as e:
            return HealthCheckResult(
                check_name=self.name,
                check_type=self.check_type,
                status=HealthStatus.UNHEALTHY,
                score=0.0,
                message=f"性能检查失败: {str(e)}",
                details={'exception': str(e)}
            )


class SystemHealthMonitor:
    """系统健康监控器 V3.7

    提供24/7全方位的系统健康监控。
    """

    def __init__(
        self,
        config: Dict[str, Any],
        alert_callback: Optional[Callable] = None
    ):
        """初始化系统健康监控器

        Args:
            config: 配置字典
            alert_callback: 告警回调函数
        """
        self.config = config
        self.alert_callback = alert_callback

        # 健康检查集合
        self.checks: List[HealthCheck] = []

        # 健康历史
        self.history: deque = deque(maxlen=1000)
        self.trends: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))

        # 运行状态
        self.is_running = False
        self.start_time: Optional[datetime] = None

        # 统计信息
        self.stats = {
            'total_checks': 0,
            'healthy_count': 0,
            'degraded_count': 0,
            'unhealthy_count': 0,
            'critical_count': 0
        }

        logger.info("系统健康监控器初始化完成")

    def register_check(self, check: HealthCheck) -> None:
        """注册健康检查

        Args:
            check: 健康检查对象
        """
        self.checks.append(check)
        logger.info(f"注册健康检查: {check.name} ({check.check_type.value})")

    async def run_checks(self) -> HealthReport:
        """运行所有健康检查

        Returns:
            健康报告
        """
        logger.info("开始健康检查...")

        # 并发执行所有检查
        tasks = [check.execute() for check in self.checks]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常
        check_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"健康检查 {self.checks[i].name} 异常: {result}")
                continue
            check_results.append(result)

        # 计算整体状态
        overall_status, overall_score = self._calculate_overall_status(check_results)

        # 生成建议
        recommendations = self._generate_recommendations(check_results)

        # 分析趋势
        trends = self._analyze_trends(check_results)

        # 生成报告
        report = HealthReport(
            overall_status=overall_status,
            overall_score=overall_score,
            timestamp=datetime.now(),
            checks=check_results,
            components={r.check_name: r.details for r in check_results},
            recommendations=recommendations,
            trends=trends
        )

        # 记录历史
        self.history.append(report)

        # 更新统计
        self._update_stats(report)

        # 触发告警（如果需要）
        if self.alert_callback:
            await self._trigger_alerts(report)

        logger.info(f"健康检查完成 - 状态: {overall_status.value}, 得分: {overall_score:.1f}")

        return report

    def _calculate_overall_status(
        self,
        results: List[HealthCheckResult]
    ) -> Tuple[HealthStatus, float]:
        """计算整体健康状态

        Args:
            results: 检查结果列表

        Returns:
            (状态, 得分)
        """
        if not results:
            return HealthStatus.UNHEALTHY, 0.0

        # 检查关键检查
        critical_checks = [r for r in results if r.critical]
        if critical_checks:
            critical_failed = [r for r in critical_checks
                             if r.status == HealthStatus.CRITICAL or r.status == HealthStatus.UNHEALTHY]
            if critical_failed:
                return HealthStatus.CRITICAL, 0.0

        # 计算平均得分
        avg_score = sum(r.score for r in results) / len(results)

        # 根据得分确定状态
        if avg_score >= 80:
            status = HealthStatus.HEALTHY
        elif avg_score >= 60:
            status = HealthStatus.DEGRADED
        elif avg_score >= 40:
            status = HealthStatus.UNHEALTHY
        else:
            status = HealthStatus.CRITICAL

        return status, avg_score

    def _generate_recommendations(
        self,
        results: List[HealthCheckResult]
    ) -> List[str]:
        """生成健康建议

        Args:
            results: 检查结果列表

        Returns:
            建议列表
        """
        recommendations = []

        for result in results:
            if result.status == HealthStatus.CRITICAL:
                recommendations.append(f"紧急: {result.message}")
            elif result.status == HealthStatus.UNHEALTHY:
                recommendations.append(f"警告: {result.message}")
            elif result.status == HealthStatus.DEGRADED:
                recommendations.append(f"注意: {result.message}")

        return recommendations[:5]  # 最多返回5条建议

    def _analyze_trends(
        self,
        results: List[HealthCheckResult]
    ) -> Dict[str, Any]:
        """分析健康趋势

        Args:
            results: 检查结果列表

        Returns:
            趋势分析
        """
        trends = {}

        for result in results:
            check_name = result.check_name

            # 记录趋势
            self.trends[check_name].append(result.score)

            # 如果有足够的历史数据，计算趋势
            if len(self.trends[check_name]) >= 10:
                recent_scores = list(self.trends[check_name])[-10:]
                avg_score = sum(recent_scores) / len(recent_scores)

                # 比较最近和历史
                old_score = sum(recent_scores[:5]) / 5
                new_score = sum(recent_scores[5:]) / 5

                change = new_score - old_score

                if change > 10:
                    trend = "improving"
                elif change < -10:
                    trend = "degrading"
                else:
                    trend = "stable"

                trends[check_name] = {
                    'current_score': result.score,
                    'avg_score': avg_score,
                    'trend': trend,
                    'change': change
                }

        return trends

    def _update_stats(self, report: HealthReport) -> None:
        """更新统计信息

        Args:
            report: 健康报告
        """
        self.stats['total_checks'] += len(report.checks)

        for check in report.checks:
            status = check.status.value
            if status == 'HEALTHY':
                self.stats['healthy_count'] += 1
            elif status == 'DEGRADED':
                self.stats['degraded_count'] += 1
            elif status == 'UNHEALTHY':
                self.stats['unhealthy_count'] += 1
            elif status == 'CRITICAL':
                self.stats['critical_count'] += 1

    async def _trigger_alerts(self, report: HealthReport) -> None:
        """触发告警

        Args:
            report: 健康报告
        """
        # 只对关键状态触发告警
        if report.overall_status in [HealthStatus.UNHEALTHY, HealthStatus.CRITICAL]:
            if self.alert_callback:
                await self.alert_callback({
                    'type': 'health_alert',
                    'severity': report.overall_status.value,
                    'score': report.overall_score,
                    'timestamp': report.timestamp.isoformat(),
                    'recommendations': report.recommendations
                })

    async def start_monitoring(self, interval: float = 60.0) -> None:
        """启动持续监控

        Args:
            interval: 检查间隔（秒）
        """
        if self.is_running:
            logger.warning("监控已在运行")
            return

        self.is_running = True
        self.start_time = datetime.now()

        logger.info(f"启动系统健康监控 - 间隔: {interval}秒")

        while self.is_running:
            try:
                await self.run_checks()
                await asyncio.sleep(interval)

            except Exception as e:
                logger.error(f"健康监控异常: {e}")
                await asyncio.sleep(5)  # 等待后重试

    def stop_monitoring(self) -> None:
        """停止监控"""
        self.is_running = False
        logger.info("系统健康监控已停止")

    def get_health_summary(self) -> Dict[str, Any]:
        """获取健康摘要

        Returns:
            健康摘要
        """
        if not self.history:
            return {'status': 'no_data'}

        latest_report = self.history[-1]

        return {
            'overall_status': latest_report.overall_status.value,
            'overall_score': latest_report.overall_score,
            'timestamp': latest_report.timestamp.isoformat(),
            'check_count': len(latest_report.checks),
            'critical_issues': sum(1 for r in latest_report.checks if r.status == HealthStatus.CRITICAL),
            'degraded_checks': sum(1 for r in latest_report.checks if r.status == HealthStatus.DEGRADED),
            'recommendations': latest_report.recommendations[:3],
            'stats': self.stats.copy()
        }

    def get_detailed_report(self) -> HealthReport:
        """获取详细报告

        Returns:
            最新健康报告
        """
        if not self.history:
            raise ValueError("没有可用的健康报告")

        return self.history[-1]


# 便捷函数
def create_system_health_monitor(
    config: Dict[str, Any],
    alert_callback: Optional[Callable] = None
) -> SystemHealthMonitor:
    """创建系统健康监控器实例

    Args:
        config: 配置字典
        alert_callback: 告警回调函数

    Returns:
        系统健康监控器实例
    """
    return SystemHealthMonitor(config, alert_callback)
