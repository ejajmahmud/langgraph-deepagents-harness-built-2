"""仪表板生成器 - Phase 11核心模块

生成HTML监控仪表板。

核心功能：
1. 系统指标展示 - CPU/内存/磁盘实时指标
2. 告警列表展示 - 实时告警和严重级别分布
3. 健康状态展示 - 系统健康状态和组件状态
4. 性能摘要展示 - 性能统计和趋势

创建时间：2026-04-19 20:42:00
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DashboardGenerator:
    """仪表板生成器

    生成HTML监控仪表板。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化仪表板生成器

        Args:
            config: 配置字典
        """
        self.config = config or {}

        logger.info("仪表板生成器初始化完成")

    def generate_dashboard(
        self,
        metrics_data: Optional[Dict[str, Any]] = None,
        alert_data: Optional[Dict[str, Any]] = None,
        health_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """生成仪表板数据

        Args:
            metrics_data: 指标数据字典
            alert_data: 告警数据字典
            health_data: 健康数据字典

        Returns:
            仪表板数据字典
        """
        dashboard = {
            'timestamp': datetime.now().isoformat(),
            'title': '数字货币套利系统 - 监控仪表板',
            'widgets': {
                'system_metrics': self._generate_system_metrics_widget(metrics_data),
                'alert_list': self._generate_alert_list_widget(alert_data),
                'health_status': self._generate_health_status_widget(health_data),
                'performance_summary': self._generate_performance_summary_widget(metrics_data),
            },
        }

        return dashboard

    def _generate_system_metrics_widget(self, metrics_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """生成系统指标组件

        Args:
            metrics_data: 指标数据字典

        Returns:
            组件数据字典
        """
        if not metrics_data:
            return {'status': 'no_data', 'message': '暂无指标数据'}

        # 支持多种数据格式
        system_metrics = {}
        if 'system' in metrics_data:
            system_metrics = metrics_data['system']
        elif 'current_metrics' in metrics_data:
            system_metrics = metrics_data['current_metrics']
        else:
            system_metrics = metrics_data

        if not system_metrics:
            return {'status': 'no_data', 'message': '指标数据为空'}

        return {
            'type': 'system_metrics',
            'status': 'ok',
            'data': {
                'cpu': {
                    'value': system_metrics.get('cpu_percent', system_metrics.get('cpu_usage', 0)),
                    'unit': '%',
                    'status': self._get_metric_status(
                        system_metrics.get('cpu_percent', system_metrics.get('cpu_usage', 0)),
                        80, 90
                    ),
                    'process': system_metrics.get('process_cpu_percent', 0),
                },
                'memory': {
                    'value': system_metrics.get('memory_percent', system_metrics.get('memory_usage', 0)),
                    'unit': '%',
                    'status': self._get_metric_status(
                        system_metrics.get('memory_percent', system_metrics.get('memory_usage', 0)),
                        80, 90
                    ),
                    'used_mb': system_metrics.get('memory_used_mb', 0),
                    'available_mb': system_metrics.get('memory_available_mb', 0),
                },
                'disk': {
                    'value': system_metrics.get('disk_percent', system_metrics.get('disk_usage', 0)),
                    'unit': '%',
                    'status': self._get_metric_status(
                        system_metrics.get('disk_percent', system_metrics.get('disk_usage', 0)),
                        80, 95
                    ),
                    'used_gb': system_metrics.get('disk_used_gb', 0),
                    'free_gb': system_metrics.get('disk_free_gb', 0),
                    'total_gb': system_metrics.get('disk_total_gb', 0),
                },
                'network': {
                    'sent_mb': system_metrics.get('network_sent_mb', system_metrics.get('network_io', 0)),
                    'recv_mb': system_metrics.get('network_recv_mb', 0),
                },
            },
            'timestamp': datetime.now().isoformat(),
        }

    def _generate_alert_list_widget(self, alert_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """生成告警列表组件

        Args:
            alert_data: 告警数据字典

        Returns:
            组件数据字典
        """
        if not alert_data:
            return {'status': 'no_data', 'message': '暂无告警数据'}

        # 支持多种数据格式
        alerts = []
        if 'alerts' in alert_data:
            alerts = alert_data['alerts']
        elif isinstance(alert_data, list):
            alerts = alert_data

        severity_breakdown = alert_data.get('severity_breakdown', {})

        return {
            'type': 'alert_list',
            'status': 'ok',
            'data': {
                'alerts': alerts,
                'count': len(alerts),
                'severity_breakdown': severity_breakdown,
            },
        }

    def _generate_health_status_widget(self, health_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """生成健康状态组件

        Args:
            health_data: 健康数据字典

        Returns:
            组件数据字典
        """
        if not health_data:
            return {'status': 'no_data', 'message': '暂无健康检查数据'}

        # 支持多种数据格式
        overall_status = health_data.get('overall_status', 'unknown')
        checks_data = health_data.get('checks', {})

        # 兼容不同的健康检查数据格式
        if 'data' in health_data:
            health_status = health_data['data']
            overall_status = health_status.get('overall_status', overall_status)
            checks_data = health_status.get('checks', checks_data)

        return {
            'type': 'health_status',
            'status': 'ok',
            'data': {
                'overall_status': overall_status,
                'last_check_time': health_data.get('timestamp', datetime.now().isoformat()),
                'checks': checks_data,
            },
        }

    def _generate_performance_summary_widget(self, metrics_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """生成性能摘要组件

        Args:
            metrics_data: 指标数据字典

        Returns:
            组件数据字典
        """
        if not metrics_data:
            return {'status': 'no_data', 'message': '暂无性能数据'}

        # 这里使用模拟数据，实际应该从历史数据计算
        summary = {
            'data_points': metrics_data.get('data_points', 0),
            'time_range': {
                'start': metrics_data.get('start_time'),
                'end': metrics_data.get('end_time'),
            },
        }

        # 如果有历史数据，计算统计
        if 'history' in metrics_data and metrics_data['history']:
            cpu_values = [
                m.get('cpu_percent', m.get('cpu_usage', 0))
                for m in metrics_data['history']
                if 'cpu_percent' in m or 'cpu_usage' in m
            ]

            memory_values = [
                m.get('memory_percent', m.get('memory_usage', 0))
                for m in metrics_data['history']
                if 'memory_percent' in m or 'memory_usage' in m
            ]

            if cpu_values:
                summary['cpu'] = {
                    'avg': sum(cpu_values) / len(cpu_values),
                    'max': max(cpu_values),
                    'min': min(cpu_values),
                    'current': cpu_values[-1],
                }

            if memory_values:
                summary['memory'] = {
                    'avg': sum(memory_values) / len(memory_values),
                    'max': max(memory_values),
                    'min': min(memory_values),
                    'current': memory_values[-1],
                }

        return {
            'type': 'performance_summary',
            'status': 'ok',
            'data': summary,
        }

    def _get_metric_status(
        self,
        value: float,
        warning_threshold: float,
        critical_threshold: float
    ) -> str:
        """获取指标状态

        Args:
            value: 指标值
            warning_threshold: 警告阈值
            critical_threshold: 严重阈值

        Returns:
            状态字符串
        """
        if value >= critical_threshold:
            return 'critical'
        elif value >= warning_threshold:
            return 'warning'
        else:
            return 'normal'

    def export_dashboard_html(self, dashboard: Dict[str, Any]) -> str:
        """导出HTML仪表板

        Args:
            dashboard: 仪表板数据字典

        Returns:
            HTML字符串
        """
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>数字货币套利系统 - 监控仪表板</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        .header {{
            background: rgba(255, 255, 255, 0.95);
            padding: 25px;
            border-radius: 15px;
            margin-bottom: 25px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
        }}
        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 32px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .header .subtitle {{
            margin: 0;
            opacity: 0.7;
            font-size: 14px;
            color: #666;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 25px;
            margin-bottom: 25px;
        }}
        .widget {{
            background: rgba(255, 255, 255, 0.95);
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
            transition: transform 0.3s ease;
        }}
        .widget:hover {{
            transform: translateY(-5px);
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
        }}
        .widget h2 {{
            margin: 0 0 20px 0;
            font-size: 20px;
            color: #333;
            border-bottom: 3px solid;
            border-image: linear-gradient(135deg, #667eea 0%, #764ba2 100%) 1;
            padding-bottom: 12px;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 15px;
        }}
        .metric {{
            padding: 20px;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border-radius: 12px;
            text-align: center;
            transition: transform 0.3s ease;
        }}
        .metric:hover {{
            transform: scale(1.05);
        }}
        .metric-label {{
            font-size: 12px;
            color: #666;
            margin-bottom: 8px;
            font-weight: 500;
        }}
        .metric-value {{
            font-size: 32px;
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }}
        .metric-unit {{
            font-size: 14px;
            color: #666;
        }}
        .status-normal {{ color: #28a745; }}
        .status-warning {{ color: #ffc107; }}
        .status-critical {{ color: #dc3545; }}
        .alert {{
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #333;
            background-color: #f9f9f9;
            border-radius: 8px;
            transition: all 0.3s ease;
        }}
        .alert:hover {{
            transform: translateX(5px);
        }}
        .alert-WARNING {{ border-left-color: #ffc107; background-color: #fff3cd; }}
        .alert-ERROR {{ border-left-color: #dc3545; background-color: #f8d7da; }}
        .alert-CRITICAL {{ border-left-color: #721c24; background-color: #f5c6cb; }}
        .alert strong {{
            display: block;
            margin-bottom: 6px;
            font-size: 15px;
        }}
        .alert small {{
            color: #666;
            font-size: 12px;
        }}
        .no-data {{
            text-align: center;
            color: #999;
            padding: 30px;
            font-size: 16px;
        }}
        .stats-summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
            gap: 12px;
            margin-top: 20px;
        }}
        .stat-item {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            transition: transform 0.3s ease;
        }}
        .stat-item:hover {{
            transform: scale(1.05);
        }}
        .stat-label {{
            font-size: 11px;
            color: #666;
            margin-bottom: 8px;
            font-weight: 500;
        }}
        .stat-value {{
            font-size: 20px;
            font-weight: bold;
            color: #333;
        }}
        .footer {{
            text-align: center;
            padding: 25px;
            color: rgba(255, 255, 255, 0.9);
            font-size: 14px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 15px;
            margin-top: 25px;
        }}
        @media (max-width: 768px) {{
            .grid {{
                grid-template-columns: 1fr;
            }}
            .metrics-grid {{
                grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 {dashboard['title']}</h1>
            <p class="subtitle">更新时间: {dashboard['timestamp']}</p>
        </div>

        {self._generate_widgets_html(dashboard['widgets'])}

        <div class="footer">
            <p>数字货币套利系统 v5.2 - Phase 11 监控仪表板</p>
        </div>
    </div>
</body>
</html>
"""
        return html

    def _generate_widgets_html(self, widgets: Dict[str, Any]) -> str:
        """生成组件HTML

        Args:
            widgets: 组件数据字典

        Returns:
            HTML字符串
        """
        html = ""

        # 系统指标组件
        if 'system_metrics' in widgets:
            widget = widgets['system_metrics']
            html += self._generate_system_metrics_html(widget)

        # 告警列表组件
        if 'alert_list' in widgets:
            widget = widgets['alert_list']
            html += self._generate_alert_list_html(widget)

        # 健康状态组件
        if 'health_status' in widgets:
            widget = widgets['health_status']
            html += self._generate_health_status_html(widget)

        # 性能摘要组件
        if 'performance_summary' in widgets:
            widget = widgets['performance_summary']
            html += self._generate_performance_summary_html(widget)

        return html

    def _generate_system_metrics_html(self, widget: Dict[str, Any]) -> str:
        """生成系统指标HTML

        Args:
            widget: 组件数据字典

        Returns:
            HTML字符串
        """
        if widget.get('status') != 'ok':
            return f'<div class="widget"><h2>系统指标</h2><div class="no-data">{widget.get("message", "暂无数据")}</div></div>'

        data = widget['data']
        metrics_data = data.get('metrics', data)

        if not metrics_data:
            return '<div class="widget"><h2>系统指标</h2><div class="no-data">暂无数据</div></div>'

        html = '<div class="widget"><h2>📊 系统指标</h2><div class="metrics-grid">'

        # CPU指标
        if 'cpu' in metrics_data:
            cpu = metrics_data['cpu']
            html += f"""
                <div class="metric">
                    <div class="metric-label">CPU使用率</div>
                    <div class="metric-value status-{cpu['status']}">{cpu['value']:.1f}%</div>
                    <div class="metric-unit">进程: {cpu.get('process', 0):.1f}%</div>
                </div>
"""

        # 内存指标
        if 'memory' in metrics_data:
            memory = metrics_data['memory']
            html += f"""
                <div class="metric">
                    <div class="metric-label">内存使用率</div>
                    <div class="metric-value status-{memory['status']}">{memory['value']:.1f}%</div>
                    <div class="metric-unit">已用: {memory.get('used_mb', 0):.1f}MB</div>
                </div>
"""

        # 磁盘指标
        if 'disk' in metrics_data:
            disk = metrics_data['disk']
            html += f"""
                <div class="metric">
                    <div class="metric-label">磁盘使用率</div>
                    <div class="metric-value status-{disk['status']}">{disk['value']:.1f}%</div>
                    <div class="metric-unit">剩余: {disk.get('free_gb', 0):.1f}GB</div>
                </div>
"""

        html += '</div></div>'

        return html

    def _generate_alert_list_html(self, widget: Dict[str, Any]) -> str:
        """生成告警列表HTML

        Args:
            widget: 组件数据字典

        Returns:
            HTML字符串
        """
        if widget.get('status') != 'ok':
            return f'<div class="widget"><h2>最近告警</h2><div class="no-data">{widget.get("message", "暂无数据")}</div></div>'

        data = widget['data']
        alerts = data.get('alerts', [])
        severity_breakdown = data.get('severity_breakdown', {})

        html = '<div class="widget"><h2>🔔 最近告警</h2>'

        # 显示严重级别分布
        if severity_breakdown:
            total = sum(severity_breakdown.values())
            html += '<div class="stats-summary">'

            severity_colors = {
                'INFO': 'normal',
                'WARNING': 'warning',
                'ERROR': 'critical',
                'CRITICAL': 'critical'
            }

            for severity, count in severity_breakdown.items():
                if count > 0:
                    percentage = (count / total) * 100
                    color_class = severity_colors.get(severity, 'normal')
                    html += f"""
                        <div class="stat-item">
                            <div class="stat-label">{severity}</div>
                            <div class="stat-value status-{color_class}">{count} ({percentage:.1f}%)</div>
                        </div>
"""

            html += '</div>'

        # 显示告警列表
        if alerts:
            html += '<div style="margin-top: 20px;">'

            for alert in alerts[:10]:
                html += f"""
                <div class="alert alert-{alert.get('severity', 'INFO')}">
                    <strong>{alert.get('name', 'Unknown')}</strong> - {alert.get('message', '')}
                    <br/>
                    <small>{alert.get('timestamp', '')}</small>
                </div>
"""

            html += '</div>'
        else:
            html += '<div class="no-data">暂无告警 ✅</div>'

        html += '</div>'

        return html

    def _generate_health_status_html(self, widget: Dict[str, Any]) -> str:
        """生成健康状态HTML

        Args:
            widget: 组件数据字典

        Returns:
            HTML字符串
        """
        if widget.get('status') != 'ok':
            return f'<div class="widget"><h2>系统健康状态</h2><div class="no-data">{widget.get("message", "暂无数据")}</div></div>'

        data = widget['data']
        health_data = data.get('status', data)

        status = health_data.get('overall_status', 'unknown')
        status_class = f"status-{status}" if status in ['normal', 'warning', 'critical'] else ''

        html = f"""
<div class="widget">
    <h2>💚 系统健康状态</h2>
    <div class="metrics-grid">
        <div class="metric">
            <div class="metric-label">总体状态</div>
            <div class="metric-value {status_class}">{status.upper()}</div>
        </div>
        <div class="metric">
            <div class="metric-label">最后检查时间</div>
            <div class="metric-value" style="font-size: 18px;">{health_data.get('last_check_time', 'N/A')[:19]}</div>
        </div>
    </div>
"""

        # 显示各组件状态
        checks = health_data.get('checks', {})
        if checks:
            html += '<h3 style="margin: 20px 0 15px 0;">组件状态</h3>'
            html += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px;">'

            status_icons = {
                'healthy': '✅',
                'normal': '✅',
                'warning': '⚠️',
                'degraded': '⚠️',
                'unhealthy': '❌',
                'error': '❌',
                'unknown': '❓'
            }

            for component, check_info in checks.items():
                # 支持不同的数据格式
                if isinstance(check_info, dict):
                    check_status = check_info.get('status', 'unknown')
                    status_text = check_info.get('message', check_status)
                else:
                    check_status = check_info
                    status_text = str(check_info)

                icon = status_icons.get(check_status, status_icons['unknown'])

                html += f"""
                <div class="metric" style="padding: 15px;">
                    <div class="metric-label">{component}</div>
                    <div style="font-size: 20px;">{icon} {check_text}</div>
                </div>
"""

            html += '</div>'

        html += '</div>'

        return html

    def _generate_performance_summary_html(self, widget: Dict[str, Any]) -> str:
        """生成性能摘要HTML

        Args:
            widget: 组件数据字典

        Returns:
            HTML字符串
        """
        if widget.get('status') != 'ok':
            return f'<div class="widget"><h2>性能摘要</h2><div class="no-data">{widget.get("message", "暂无数据")}</div></div>'

        data = widget['data']

        html = f"""
<div class="widget">
    <h2>⚡ 性能摘要</h2>
    <p><strong>数据点数:</strong> {data.get('data_points', 0)}</p>
"""

        # 显示CPU统计
        if 'cpu' in data:
            cpu = data['cpu']
            html += f"""
    <h3>CPU性能</h3>
    <div class="stats-summary">
        <div class="stat-item">
            <div class="stat-label">平均值</div>
            <div class="stat-value">{cpu['avg']:.1f}%</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">最大值</div>
            <div class="stat-value">{cpu['max']:.1f}%</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">最小值</div>
            <div class="stat-value">{cpu['min']:.1f}%</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">当前值</div>
            <div class="stat-value">{cpu['current']:.1f}%</div>
        </div>
    </div>
"""

        # 显示内存统计
        if 'memory' in data:
            memory = data['memory']
            html += f"""
    <h3>内存性能</h3>
    <div class="stats-summary">
        <div class="stat-item">
            <div class="stat-label">平均值</div>
            <div class="stat-value">{memory['avg']:.1f}%</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">最大值</div>
            <div class="stat-value">{memory['max']:.1f}%</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">最小值</div>
            <div class="stat-value">{memory['min']:.1f}%</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">当前值</div>
            <div class="stat-value">{memory['current']:.1f}%</div>
        </div>
    </div>
"""

        html += '</div>'

        return html

    def __repr__(self) -> str:
        """字符串表示

        Returns:
            字符串表示
        """
        return f"DashboardGenerator(config={self.config})"
