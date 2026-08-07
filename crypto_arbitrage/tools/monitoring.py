"""监控和告警系统 - V1.4.0 增强版"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """告警级别"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class MonitoringSystem:
    """监控和告警系统"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.alert_methods = config.get('alert_methods', ['console'])
        self.performance_thresholds = config.get('performance_thresholds', {
            'scan_timeout': 10,
            'execution_failure_rate': 0.1,
            'low_profit_rate': 0.1,
        })
        # BUG FIX #10: 使用配置的 metrics_interval
        self.metrics_interval = config.get('metrics_interval', 60)

        self.scan_metrics: List[Dict] = []
        self.execution_metrics: List[Dict] = []
        self.performance_metrics: List[Dict] = []
        self.alerts_history: List[Dict] = []

        self._start_time = datetime.now()
        self._total_errors = 0
        self._last_scan_time = None

        logger.info("监控系统初始化完成")

    async def record_scan_metrics(self, opportunities_count: int, scan_time: float) -> None:
        if not self.enabled:
            return
        metric = {
            'timestamp': datetime.now(),
            'opportunities_count': opportunities_count,
            'scan_time': scan_time,
            'timeout': scan_time > self.performance_thresholds.get('scan_timeout', 10)
        }
        self.scan_metrics.append(metric)
        self._last_scan_time = datetime.now()
        if metric['timeout']:
            await self._send_alert(AlertLevel.WARNING, "scan_timeout", f"扫描超时: {scan_time:.2f}秒")

    async def record_execution_metrics(self, strategy_name: str, success: bool,
                                        execution_time: float, profit: Optional[float] = None) -> None:
        if not self.enabled:
            return
        metric = {
            'timestamp': datetime.now(), 'strategy': strategy_name,
            'success': success, 'execution_time': execution_time, 'profit': profit
        }
        self.execution_metrics.append(metric)
        await self._check_execution_alerts(metric)

    async def _check_execution_alerts(self, metric: Dict) -> None:
        if not metric['success']:
            self._total_errors += 1
            await self._send_alert(AlertLevel.ERROR, "execution_failed", f"{metric['strategy']} 执行失败")
        elif metric['execution_time'] > 30:
            await self._send_alert(AlertLevel.WARNING, "execution_slow",
                               f"{metric['strategy']} 执行时间过长: {metric['execution_time']:.2f}秒")

    async def record_performance_metrics(self, total_profit: float, total_trades: int,
                                          avg_profit_rate: float, win_rate: float) -> None:
        if not self.enabled:
            return
        metric = {
            'timestamp': datetime.now(), 'total_profit': total_profit,
            'total_trades': total_trades, 'avg_profit_rate': avg_profit_rate, 'win_rate': win_rate
        }
        self.performance_metrics.append(metric)
        await self._check_performance_alerts(metric)

    async def _check_performance_alerts(self, metric: Dict) -> None:
        t = self.performance_thresholds
        if metric['avg_profit_rate'] < t.get('low_profit_rate', 0.1):
            await self._send_alert(AlertLevel.WARNING, "low_profit_rate", f"平均收益率过低: {metric['avg_profit_rate']:.2f}%")
        if metric['win_rate'] < 50:
            await self._send_alert(AlertLevel.WARNING, "low_win_rate", f"胜率过低: {metric['win_rate']:.1f}%")
        if metric['total_profit'] < 0:
            await self._send_alert(AlertLevel.ERROR, "negative_profit", f"累计亏损: ${metric['total_profit']:.2f}")

    async def _send_alert(self, level: AlertLevel, alert_type: str, message: str) -> None:
        alert = {'timestamp': datetime.now(), 'level': level, 'type': alert_type, 'message': message}
        self.alerts_history.append(alert)
        logger.info(f"告警: {level.value} - {alert_type} - {message}")
        for method in self.alert_methods:
            await self._send_via_method(method, alert)

    async def _send_via_method(self, method: str, alert: Dict) -> None:
        if method == 'console':
            self._send_to_console(alert)
        elif method == 'memo0':
            await self._send_to_memo0(alert)
        elif method == 'file':
            self._send_to_file(alert)
        elif method == 'notifier':
            await self._send_to_notifier(alert)

    def _send_to_console(self, alert: Dict) -> None:
        level = alert['level']
        msg = f"[{alert['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}] {level}: {alert['message']}"
        if level in (AlertLevel.CRITICAL, AlertLevel.ERROR):
            logger.error(msg)
        elif level == AlertLevel.WARNING:
            logger.warning(msg)
        else:
            logger.info(msg)

    async def _send_to_memo0(self, alert: Dict) -> None:
        try:
            from storage.mem0_storage import add_trading_knowledge
            add_trading_knowledge('alert', f"告警: {alert['level']} - {alert['type']}\n{alert['message']}")
        except Exception as e:
            logger.error(f"发送 Memo0 告警失败: {e}")

    async def _send_to_notifier(self, alert: Dict) -> None:
        try:
            from tools.notifier import get_notifier
            notifier = get_notifier()
            if notifier:
                await notifier.send_alert(alert['level'].value, f"套利系统: {alert['type']}", alert['message'])
        except Exception:
            pass

    def _send_to_file(self, alert: Dict) -> None:
        try:
            from pathlib import Path
            logs_dir = Path('logs')
            logs_dir.mkdir(exist_ok=True)
            alert_file = logs_dir / f"alerts_{datetime.now().strftime('%Y%m%d')}.log"
            with open(alert_file, 'a', encoding='utf-8') as f:
                f.write(f"[{alert['timestamp']}] {alert['level']} - {alert['type']}: {alert['message']}\n")
        except Exception as e:
            logger.error(f"写入文件告警失败: {e}")

    def get_scan_summary(self) -> Dict[str, Any]:
        if not self.scan_metrics:
            return {}
        recent = [m for m in self.scan_metrics if (datetime.now() - m['timestamp']).total_seconds() < 3600]
        if not recent:
            return {}
        total = len(recent)
        return {
            'total_scans': total,
            'avg_opportunities': sum(m['opportunities_count'] for m in recent) / total,
            'avg_scan_time': sum(m['scan_time'] for m in recent) / total,
            'timeouts': sum(1 for m in recent if m.get('timeout', False)),
            'period': '1小时'
        }

    def get_execution_summary(self) -> Dict[str, Any]:
        if not self.execution_metrics:
            return {}
        recent = [m for m in self.execution_metrics if (datetime.now() - m['timestamp']).total_seconds() < 3600]
        if not recent:
            return {}
        total = len(recent)
        successful = sum(1 for m in recent if m['success'])
        return {
            'total_executions': total,
            'success_rate': successful / total if total > 0 else 0,
            'avg_execution_time': sum(m['execution_time'] for m in recent) / total,
            'period': '1小时'
        }

    def get_performance_summary(self) -> Dict[str, Any]:
        if not self.performance_metrics:
            return {}
        return self.performance_metrics[-1]

    def get_alert_history(self, count: int = 10) -> List[Dict]:
        return self.alerts_history[-count:]

    def get_system_health(self) -> Dict[str, Any]:
        uptime = (datetime.now() - self._start_time).total_seconds()
        return {
            'uptime_seconds': uptime, 'uptime_hours': uptime / 3600,
            'total_errors': self._total_errors,
            'last_scan_time': self._last_scan_time.isoformat() if self._last_scan_time else None,
            'alerts_count': len(self.alerts_history),
            'status': 'healthy' if self._total_errors < 10 else 'degraded'
        }


# 全局单例
_monitoring_system: Optional[MonitoringSystem] = None


def initialize_monitoring(config: Dict[str, Any] = None) -> MonitoringSystem:
    """初始化监控系统（全局单例）"""
    global _monitoring_system
    if config is None:
        config = {}
    _monitoring_system = MonitoringSystem(config)
    return _monitoring_system


def get_monitoring() -> Optional[MonitoringSystem]:
    """获取监控系统实例（全局单例）"""
    return _monitoring_system
