"""实时监控仪表板 V3.5

提供系统的实时监控、数据聚合和可视化支持。

核心功能：
1. 实时数据收集和聚合
2. 多维度监控指标
3. 风险指标追踪
4. 交易历史管理
5. 性能统计
6. 实时告警
"""

import asyncio
import logging
import threading
import time
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class RealtimeDashboard:
    """实时监控仪表板

    收集、聚合和提供系统运行时数据，支持实时监控和可视化。
    """

    def __init__(
        self,
        window_size: int = 1000,
        update_interval: float = 2.0,
        history_limit: int = 10000
    ):
        """初始化实时监控仪表板

        Args:
            window_size: 滑动窗口大小
            update_interval: 更新间隔（秒）
            history_limit: 历史数据限制
        """
        self.window_size = window_size
        self.update_interval = update_interval
        self.history_limit = history_limit

        # 系统状态
        self.is_running = False
        self.start_time: Optional[datetime] = None
        self.uptime: float = 0.0

        # 实时数据存储（滑动窗口）
        self.metrics: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=window_size)
        )
        self.metrics_lock = threading.Lock()

        # 历史数据存储
        self.history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.history_lock = threading.Lock()

        # 系统状态数据
        self.system_status: Dict[str, Any] = {
            'status': 'idle',
            'active_strategies': [],
            'last_update': None,
            'error_count': 0,
            'warning_count': 0,
            'info_count': 0
        }

        # 风险监控数据
        self.risk_metrics: Dict[str, Any] = {
            'exposure': 0.0,
            'volatility': 0.0,
            'liquidity_score': 1.0,
            'drawdown': 0.0,
            'correlation_risk': 0.0,
            'concentration_risk': 0.0,
            'risk_level': 'LOW'
        }

        # 交易统计
        self.trade_stats: Dict[str, Any] = {
            'total_trades': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'total_profit': 0.0,
            'total_loss': 0.0,
            'win_rate': 0.0,
            'average_profit': 0.0,
            'average_loss': 0.0
        }

        # 策略执行统计
        self.strategy_stats: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                'executions': 0,
                'success': 0,
                'failed': 0,
                'profit': 0.0,
                'loss': 0.0,
                'avg_profit': 0.0,
                'avg_loss': 0.0,
                'last_execution': None
            }
        )

        # 性能指标
        self.performance_metrics: Dict[str, Any] = {
            'cpu_usage': 0.0,
            'memory_usage': 0.0,
            'disk_usage': 0.0,
            'network_io': 0.0,
            'api_latency': 0.0,
            'processing_time': 0.0
        }

        # 交易历史
        self.trade_history: List[Dict[str, Any]] = []

        # 告警列表
        self.alerts: List[Dict[str, Any]] = []

        # 数据更新监听器
        self.update_listeners: List[Callable] = []

        logger.info(
            f"RealtimeDashboard initialized: "
            f"window_size={window_size}, "
            f"update_interval={update_interval}, "
            f"history_limit={history_limit}"
        )

    def start(self) -> None:
        """启动仪表板"""
        if self.is_running:
            logger.warning("Dashboard already running")
            return

        self.is_running = True
        self.start_time = datetime.now()

        # 启动定期更新任务
        self._update_thread = threading.Thread(
            target=self._periodic_update,
            daemon=True
        )
        self._update_thread.start()

        logger.info("Dashboard started")

    def stop(self) -> None:
        """停止仪表板"""
        if not self.is_running:
            return

        self.is_running = False
        if hasattr(self, '_update_thread'):
            self._update_thread.join(timeout=5.0)

        logger.info("Dashboard stopped")

    def _periodic_update(self) -> None:
        """定期更新任务"""
        while self.is_running:
            try:
                # 更新系统状态
                self._update_system_status()

                # 更新性能指标
                self._update_performance_metrics()

                # 触发更新监听器
                self._notify_update_listeners()

            except Exception as e:
                logger.error(f"Error in periodic update: {e}")

            time.sleep(self.update_interval)

    def _update_system_status(self) -> None:
        """更新系统状态"""
        if self.start_time:
            self.uptime = (datetime.now() - self.start_time).total_seconds()

        self.system_status['last_update'] = datetime.now().isoformat()

    def _update_performance_metrics(self) -> None:
        """更新性能指标"""
        # 这里可以添加实际的性能指标收集逻辑
        # 例如：CPU、内存、磁盘、网络等
        pass

    def record_metric(
        self,
        name: str,
        value: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """记录指标

        Args:
            name: 指标名称
            value: 指标值
            metadata: 额外元数据
        """
        timestamp = datetime.now().isoformat()

        with self.metrics_lock:
            self.metrics[name].append({
                'value': value,
                'timestamp': timestamp,
                'metadata': metadata or {}
            })

        with self.history_lock:
            self.history[name].append({
                'value': value,
                'timestamp': timestamp,
                'metadata': metadata or {}
            })

            # 限制历史数据大小
            if len(self.history[name]) > self.history_limit:
                self.history[name] = self.history[name][-self.history_limit:]

        logger.debug(f"Recorded metric: {name}={value:.4f}")

    def update_risk_metrics(self, metrics: Dict[str, Any]) -> None:
        """更新风险指标

        Args:
            metrics: 风险指标字典
        """
        for key, value in metrics.items():
            if key in self.risk_metrics:
                self.risk_metrics[key] = value
                self.record_metric(f'risk_{key}', value)

        # 评估风险等级
        self._evaluate_risk_level()

        logger.debug(f"Updated risk metrics: {metrics}")

    def _evaluate_risk_level(self) -> None:
        """评估风险等级"""
        # 基于多个风险指标综合评估
        risk_score = 0.0

        # 敞口风险
        if self.risk_metrics['exposure'] > 8000:
            risk_score += 0.3
        elif self.risk_metrics['exposure'] > 5000:
            risk_score += 0.2

        # 波动率风险
        if self.risk_metrics['volatility'] > 0.05:
            risk_score += 0.2
        elif self.risk_metrics['volatility'] > 0.03:
            risk_score += 0.1

        # 流动性风险
        if self.risk_metrics['liquidity_score'] < 0.5:
            risk_score += 0.3
        elif self.risk_metrics['liquidity_score'] < 0.7:
            risk_score += 0.2

        # 回撤风险
        if self.risk_metrics['drawdown'] > 0.05:
            risk_score += 0.3
        elif self.risk_metrics['drawdown'] > 0.03:
            risk_score += 0.2

        # 确定风险等级
        if risk_score >= 0.7:
            self.risk_metrics['risk_level'] = 'CRITICAL'
        elif risk_score >= 0.4:
            self.risk_metrics['risk_level'] = 'HIGH'
        elif risk_score >= 0.2:
            self.risk_metrics['risk_level'] = 'MEDIUM'
        else:
            self.risk_metrics['risk_level'] = 'LOW'

    def record_trade(self, trade: Dict[str, Any]) -> None:
        """记录交易

        Args:
            trade: 交易信息字典
        """
        # 添加时间戳
        trade['timestamp'] = datetime.now().isoformat()

        # 添加到交易历史
        self.trade_history.append(trade)

        # 限制交易历史大小
        if len(self.trade_history) > self.history_limit:
            self.trade_history = self.trade_history[-self.history_limit:]

        # 更新交易统计
        self.trade_stats['total_trades'] += 1

        if trade.get('success', False):
            self.trade_stats['successful_trades'] += 1
            profit = trade.get('profit', 0.0)
            if profit > 0:
                self.trade_stats['total_profit'] += profit
            else:
                self.trade_stats['total_loss'] += abs(profit)
        else:
            self.trade_stats['failed_trades'] += 1

        # 更新胜率
        if self.trade_stats['total_trades'] > 0:
            self.trade_stats['win_rate'] = (
                self.trade_stats['successful_trades'] /
                self.trade_stats['total_trades']
            ) * 100

        # 更新策略统计
        strategy = trade.get('strategy', 'unknown')
        if strategy in self.strategy_stats:
            stats = self.strategy_stats[strategy]
            stats['executions'] += 1

            if trade.get('success', False):
                stats['success'] += 1
                profit = trade.get('profit', 0.0)
                if profit > 0:
                    stats['profit'] += profit
                    stats['avg_profit'] = stats['profit'] / stats['success']
                else:
                    stats['loss'] += abs(profit)
                    stats['avg_loss'] = stats['loss'] / stats['success']
            else:
                stats['failed'] += 1

            stats['last_execution'] = trade['timestamp']

        logger.info(f"Recorded trade: {strategy} - "
                    f"{'Success' if trade.get('success') else 'Failed'}")

    def add_alert(self, alert: Dict[str, Any]) -> None:
        """添加告警

        Args:
            alert: 告警信息字典
        """
        alert['timestamp'] = datetime.now().isoformat()

        # 添加到告警列表
        self.alerts.append(alert)

        # 限制告警列表大小
        if len(self.alerts) > 1000:
            self.alerts = self.alerts[-1000:]

        # 更新系统状态中的告警计数
        severity = alert.get('severity', 'info')
        if severity == 'critical':
            self.system_status['error_count'] += 1
        elif severity == 'warning':
            self.system_status['warning_count'] += 1
        else:
            self.system_status['info_count'] += 1

        logger.warning(f"Alert added: {alert.get('message')}")

    def get_overview_data(self) -> Dict[str, Any]:
        """获取总览数据

        Returns:
            总览数据字典
        """
        return {
            'system_status': self.system_status.copy(),
            'uptime': self.uptime,
            'trade_stats': self.trade_stats.copy(),
            'risk_metrics': self.risk_metrics.copy(),
            'performance_metrics': self.performance_metrics.copy()
        }

    def get_risk_data(self) -> Dict[str, Any]:
        """获取风险监控数据

        Returns:
            风险数据字典
        """
        return {
            'current_metrics': self.risk_metrics.copy(),
            'risk_history': {
                name: list(values)
                for name, values in self.history.items()
                if name.startswith('risk_')
            },
            'alerts': self.alerts[-50:]  # 最近50个告警
        }

    def get_trade_data(self) -> Dict[str, Any]:
        """获取交易数据

        Returns:
            交易数据字典
        """
        return {
            'trade_history': self.trade_history[-100:],  # 最近100笔交易
            'trade_stats': self.trade_stats.copy(),
            'strategy_stats': dict(self.strategy_stats)
        }

    def get_strategy_data(self) -> Dict[str, Any]:
        """获取策略数据

        Returns:
            策略数据字典
        """
        return {
            'active_strategies': self.system_status['active_strategies'],
            'strategy_stats': dict(self.strategy_stats),
            'strategy_performance': {
                strategy: {
                    'executions': stats['executions'],
                    'success_rate': (
                        stats['success'] / stats['executions'] * 100
                        if stats['executions'] > 0 else 0
                    ),
                    'total_profit': stats['profit'] - stats['loss'],
                    'avg_profit': stats['avg_profit'],
                    'avg_loss': stats['avg_loss'],
                    'last_execution': stats['last_execution']
                }
                for strategy, stats in self.strategy_stats.items()
            }
        }

    def get_performance_data(self) -> Dict[str, Any]:
        """获取性能数据

        Returns:
            性能数据字典
        """
        return {
            'current_metrics': self.performance_metrics.copy(),
            'metrics_history': {
                name: list(values)
                for name, values in self.metrics.items()
                if not name.startswith('risk_')
            },
            'alerts': [
                alert for alert in self.alerts
                if alert.get('category') == 'performance'
            ]
        }

    def get_metrics(
        self,
        metric_names: Optional[List[str]] = None,
        time_range: Optional[Tuple[str, str]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """获取指标数据

        Args:
            metric_names: 指标名称列表
            time_range: 时间范围 (start_time, end_time)

        Returns:
            指标数据字典
        """
        result = {}

        with self.history_lock:
            for name, values in self.history.items():
                if metric_names and name not in metric_names:
                    continue

                filtered_values = values

                # 过滤时间范围
                if time_range:
                    start_time, end_time = time_range
                    filtered_values = [
                        v for v in values
                        if start_time <= v['timestamp'] <= end_time
                    ]

                result[name] = filtered_values

        return result

    def register_update_listener(self, listener: Callable) -> None:
        """注册更新监听器

        Args:
            listener: 回调函数
        """
        if listener not in self.update_listeners:
            self.update_listeners.append(listener)
            logger.info("Update listener registered")

    def unregister_update_listener(self, listener: Callable) -> None:
        """注销更新监听器

        Args:
            listener: 回调函数
        """
        if listener in self.update_listeners:
            self.update_listeners.remove(listener)
            logger.info("Update listener unregistered")

    def _notify_update_listeners(self) -> None:
        """通知所有更新监听器"""
        for listener in self.update_listeners:
            try:
                listener()
            except Exception as e:
                logger.error(f"Error notifying listener: {e}")

    def clear_history(self) -> None:
        """清除历史数据"""
        with self.history_lock:
            self.history.clear()

        self.alerts.clear()
        self.trade_history.clear()

        # 重置统计
        self.trade_stats = {
            'total_trades': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'total_profit': 0.0,
            'total_loss': 0.0,
            'win_rate': 0.0,
            'average_profit': 0.0,
            'average_loss': 0.0
        }

        logger.info("History cleared")

    def export_data(
        self,
        data_type: str,
        format: str = 'json'
    ) -> str:
        """导出数据

        Args:
            data_type: 数据类型 (overview, risk, trade, strategy, performance)
            format: 导出格式 (json, csv)

        Returns:
            导出的数据字符串
        """
        data_map = {
            'overview': self.get_overview_data,
            'risk': self.get_risk_data,
            'trade': self.get_trade_data,
            'strategy': self.get_strategy_data,
            'performance': self.get_performance_data
        }

        if data_type not in data_map:
            raise ValueError(f"Invalid data type: {data_type}")

        data = data_map[data_type]()

        if format == 'json':
            import json
            return json.dumps(data, indent=2, default=str)
        elif format == 'csv':
            # 简化的 CSV 导出
            import csv
            import io
            output = io.StringIO()

            if data_type == 'trade':
                writer = csv.DictWriter(
                    output,
                    fieldnames=[
                        'timestamp', 'strategy', 'success', 'profit',
                        'execution_time', 'risk_level'
                    ]
                )
                writer.writeheader()
                for trade in data['trade_history']:
                    writer.writerow({
                        'timestamp': trade.get('timestamp'),
                        'strategy': trade.get('strategy'),
                        'success': trade.get('success'),
                        'profit': trade.get('profit'),
                        'execution_time': trade.get('execution_time'),
                        'risk_level': trade.get('risk_level')
                    })

            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format}")


# 全局实例
_dashboard_instance: Optional[RealtimeDashboard] = None


def get_dashboard() -> Optional[RealtimeDashboard]:
    """获取全局仪表板实例

    Returns:
        仪表板实例
    """
    return _dashboard_instance


def initialize_dashboard(
    config: Optional[Dict[str, Any]] = None
) -> RealtimeDashboard:
    """初始化全局仪表板

    Args:
        config: 配置字典

    Returns:
        仪表板实例
    """
    global _dashboard_instance

    if _dashboard_instance is None:
        config = config or {}
        _dashboard_instance = RealtimeDashboard(
            window_size=config.get('window_size', 1000),
            update_interval=config.get('update_interval', 2.0),
            history_limit=config.get('history_limit', 10000)
        )
        return _dashboard_instance


class DashboardWebServer:
    """Dashboard Web API Server - V1.0 (Phase 107新增)

    提供HTTP API服务来暴露仪表板数据:
    - RESTful API端点
    - JSON数据返回
    - HTML仪表板展示
    """

    def __init__(
        self,
        dashboard: RealtimeDashboard,
        host: str = '0.0.0.0',
        port: int = 8080
    ):
        """初始化Dashboard Web API服务器

        Args:
            dashboard: RealtimeDashboard实例
            host: 监听地址
            port: 监听端口
        """
        self.dashboard = dashboard
        self.host = host
        self.port = port
        self._server = None

        logger.info(
            f"Dashboard Web Server initialized: http://{host}:{port}"
        )

    def _create_html_dashboard(self) -> str:
        """创建HTML仪表板页面"""
        overview = self.dashboard.get_overview_data()
        trade = self.dashboard.get_trade_data()
        risk = self.dashboard.get_risk_data()

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>CryptoArbitrage Dashboard</title>
    <style>
        body {{ font-family: -apple-system; background: #0d1117; color: #c9d1d9; padding: 20px; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .header h1 {{ color: #58a6ff; font-size: 28px; }}
        .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }}
        .card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; }}
        .stat {{ display: flex; justify-content: space-between; padding: 8px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>CryptoArbitrage Dashboard</h1>
        <p>V4.0 (Phase 107)</p>
    </div>
    <div class="grid">
        <div class="card"><h3>System</h3><div class="stat"><span>Status</span><span>{overview['system_status']['status']}</span></div></div>
        <div class="card"><h3>Trades</h3><div class="stat"><span>Total</span><span>{trade['trade_stats']['total_trades']}</span></div></div>
        <div class="card"><h3>Profit</h3><div class="stat"><span>$</span><span>${trade['trade_stats']['total_profit']:.2f}</span></div></div>
        <div class="card"><h3>Risk</h3><div class="stat"><span>Level</span><span>{risk['current_metrics']['risk_level']}</span></div></div>
    </div>
</body>
</html>"""

    def create_app(self):
        """创建FastAPI应用"""
        try:
            from fastapi import FastAPI
            from fastapi.responses import JSONResponse, HTMLResponse
        except ImportError:
            logger.error("FastAPI not installed: pip install fastapi uvicorn")
            return None

        app = FastAPI(title="CryptoArbitrage Dashboard API", version="4.0")

        @app.get("/")
        async def root():
            return HTMLResponse(content=self._create_html_dashboard())

        @app.get("/api/overview")
        async def api_overview():
            return self.dashboard.get_overview_data()

        @app.get("/api/trade")
        async def api_trade():
            return self.dashboard.get_trade_data()

        @app.get("/api/risk")
        async def api_risk():
            return self.dashboard.get_risk_data()

        @app.get("/api/alerts")
        async def api_alerts():
            return {'alerts': self.dashboard.alerts[-50:], 'total': len(self.dashboard.alerts)}

        return app

    def start_background(self):
        """后台启动Web服务器"""
        import threading

        def run():
            try:
                import uvicorn
            except ImportError:
                logger.error("uvicorn not installed")
                return
            app = self.create_app()
            if app:
                uvicorn.run(app, host=self.host, port=self.port, log_level="warning")

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        logger.info(f"Dashboard Web Server started: http://{self.host}:{self.port}")


def create_dashboard_web_server(
    dashboard: RealtimeDashboard,
    host: str = '0.0.0.0',
    port: int = 8080
) -> DashboardWebServer:
    """工厂函数：创建Dashboard Web API服务器"""
    return DashboardWebServer(dashboard=dashboard, host=host, port=port)
