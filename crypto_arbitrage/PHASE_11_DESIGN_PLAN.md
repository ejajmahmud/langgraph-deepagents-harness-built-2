# Phase 11 设计方案：实时监控与运维自动化完善

**设计时间**: 2026-04-19 20:32:00
**基于**: Phase 10生产环境部署与运维自动化完成
**状态**: 设计阶段

---

## 🎯 Phase 11目标

### 核心使命
在Phase 10生产部署架构的基础上，完善实时监控体系，实现运维自动化，构建完整的运维能力，确保系统稳定、高效、可监控地运行。

### 关键问题
1. **实时监控** - 缺少实时指标收集和监控仪表板
2. **告警管理** - 缺少智能告警机制和多渠道通知
3. **运维自动化** - 缺少自动化运维能力（扩缩容/恢复/备份）
4. **安全管理** - 缺少企业级认证和权限管理

---

## 📐 架构设计

### Phase 11模块架构

```
Phase 11 架构设计
├── monitoring/              # 实时监控模块
│   ├── metrics_collector.py       # 指标收集器 ✅
│   ├── alert_manager.py           # 告警管理器 ✅
│   ├── dashboard.py               # 监控仪表板 ✅
│   └── notification_service.py    # 通知服务 ✅
│
├── automation/              # 运维自动化模块
│   ├── auto_scaler.py            # 自动扩缩容 ✅
│   ├── auto_recovery.py          # 自动恢复 ✅
│   └── backup_manager.py          # 备份管理器 ✅
│
└── tests/                   # 测试套件
    ├── test_phase11_monitoring.py    # 监控测试
    ├── test_phase11_automation.py    # 自动化测试
    └── test_phase11_integration.py   # 集成测试
```

---

## 📊 详细设计

### 1. 实时监控模块（预估: 600行）

#### 1.1 指标收集器（~150行）

**功能特性**：
- **系统指标**: CPU、内存、磁盘、网络
- **应用指标**: 存储性能、交易性能、API响应时间
- **业务指标**: 套利机会数、交易成功率、收益率
- **指标聚合**: 实时聚合和统计

**核心类设计**：
```python
class MetricsCollector:
    """指标收集器

    实时收集系统和应用指标。
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.metrics_history = {}
        self.collection_interval = config.get('metrics_interval_seconds', 30)

    async def collect_system_metrics(self) -> Dict[str, float]:
        """收集系统指标"""
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=0.1)
        # 内存使用
        memory = psutil.virtual_memory()
        # 磁盘使用
        disk = psutil.disk_usage('.')
        # 网络流量
        network = psutil.net_io_counters()

        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_used_mb': memory.used / 1024 / 1024,
            'disk_percent': disk.percent,
            'network_sent_mb': network.bytes_sent / 1024 / 1024,
            'network_recv_mb': network.bytes_recv / 1024 / 1024,
        }

    async def collect_storage_metrics(self, storage) -> Dict[str, Any]:
        """收集存储指标"""
        # 存储性能指标
        start_time = time.perf_counter()

        # 执行测试操作
        await storage.add_knowledge("metrics_test", {'test': True})
        result = await storage.search_knowledge("metrics_test", limit=1)

        duration_ms = (time.perf_counter() - start_time) * 1000

        return {
            'operation_latency_ms': duration_ms,
            'storage_type': getattr(storage, 'storage_type', 'unknown'),
        }

    async def collect_trading_metrics(self) -> Dict[str, float]:
        """收集交易指标"""
        # 这里可以从交易日志或数据库读取
        return {
            'opportunities_found': 0,  # 从交易日志读取
            'trades_executed': 0,
            'success_rate': 0.0,
            'total_profit': 0.0,
        }

    async def collect_all_metrics(self) -> Dict[str, Any]:
        """收集所有指标"""
        timestamp = datetime.now().isoformat()

        # 收集各类指标
        system_metrics = await self.collect_system_metrics()
        # storage_metrics = await self.collect_storage_metrics(storage)
        # trading_metrics = await self.collect_trading_metrics()

        all_metrics = {
            'timestamp': timestamp,
            'system': system_metrics,
            # 'storage': storage_metrics,
            # 'trading': trading_metrics,
        }

        # 保存历史
        self._save_metrics_history(all_metrics)

        return all_metrics

    def _save_metrics_history(self, metrics: Dict[str, Any]):
        """保存指标历史"""
        for category, category_metrics in metrics.items():
            if category == 'timestamp':
                continue

            if category not in self.metrics_history:
                self.metrics_history[category] = []

            self.metrics_history[category].append({
                'timestamp': metrics['timestamp'],
                **category_metrics
            })

            # 限制历史长度
            if len(self.metrics_history[category]) > 1000:
                self.metrics_history[category] = self.metrics_history[category][-1000:]

    def get_metrics_history(
        self,
        category: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取指标历史"""
        if category not in self.metrics_history:
            return []

        history = self.metrics_history[category]
        return history[-limit:]

    def get_latest_metrics(self) -> Optional[Dict[str, Any]]:
        """获取最新指标"""
        if not self.metrics_history:
            return None

        # 获取所有类别的最新指标
        latest = {'timestamp': datetime.now().isoformat()}
        for category, history in self.metrics_history.items():
            if history:
                latest[category] = history[-1]

        return latest

    async def start_collection(self):
        """启动指标收集"""
        logger.info(f"启动指标收集，间隔: {self.collection_interval}秒")

        while True:
            try:
                await self.collect_all_metrics()
                await asyncio.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"指标收集失败: {e}")
                await asyncio.sleep(self.collection_interval)
```

#### 1.2 告警管理器（~150行）

**功能特性**：
- **告警规则**: 灵活的告警规则配置
- **多级告警**: INFO/WARNING/ERROR/CRITICAL
- **告警去重**: 避免重复告警
- **告警历史**: 完整的告警历史记录

**核心类设计**：
```python
class AlertManager:
    """告警管理器

    管理系统告警。
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.alert_rules = {}
        self.alert_history = []
        self.alert_cooldowns = {}  # 告警冷却期

        # 添加默认告警规则
        self._add_default_rules()

    def _add_default_rules(self):
        """添加默认告警规则"""
        # CPU告警
        self.add_alert_rule({
            'name': 'high_cpu_usage',
            'condition': lambda metrics: metrics.get('cpu_percent', 0) > 80,
            'severity': 'WARNING',
            'message': 'CPU使用率过高',
            'cooldown': 300,  # 5分钟冷却期
        })

        # 内存告警
        self.add_alert_rule({
            'name': 'high_memory_usage',
            'condition': lambda metrics: metrics.get('memory_percent', 0) > 80,
            'severity': 'WARNING',
            'message': '内存使用率过高',
            'cooldown': 300,
        })

        # 磁盘告警
        self.add_alert_rule({
            'name': 'high_disk_usage',
            'condition': lambda metrics: metrics.get('disk_percent', 0) > 90,
            'severity': 'CRITICAL',
            'message': '磁盘使用率过高',
            'cooldown': 600,  # 10分钟冷却期
        })

    def add_alert_rule(self, rule: Dict[str, Any]) -> str:
        """添加告警规则"""
        rule_id = rule.get('name', str(uuid.uuid4()))
        self.alert_rules[rule_id] = rule
        logger.info(f"添加告警规则: {rule_id}")
        return rule_id

    def remove_alert_rule(self, rule_id: str) -> bool:
        """移除告警规则"""
        if rule_id in self.alert_rules:
            del self.alert_rules[rule_id]
            logger.info(f"移除告警规则: {rule_id}")
            return True
        return False

    async def evaluate_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """评估告警"""
        triggered_alerts = []

        for rule_id, rule in self.alert_rules.items():
            try:
                # 检查冷却期
                if self._is_in_cooldown(rule_id, rule):
                    continue

                # 评估条件
                condition = rule['condition']
                if condition(metrics):
                    # 触发告警
                    alert = self._create_alert(rule_id, rule, metrics)
                    triggered_alerts.append(alert)

                    # 更新冷却期
                    cooldown = rule.get('cooldown', 300)
                    self.alert_cooldowns[rule_id] = time.time() + cooldown

                    # 记录告警历史
                    self.alert_history.append(alert)

                    logger.warning(f"触发告警: {rule['name']} - {rule['message']}")

            except Exception as e:
                logger.error(f"评估告警规则 {rule_id} 失败: {e}")

        return triggered_alerts

    def _is_in_cooldown(self, rule_id: str, rule: Dict[str, Any]) -> bool:
        """检查是否在冷却期"""
        if rule_id not in self.alert_cooldowns:
            return False

        cooldown_time = self.alert_cooldowns[rule_id]
        return time.time() < cooldown_time

    def _create_alert(
        self,
        rule_id: str,
        rule: Dict[str, Any],
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建告警"""
        return {
            'id': str(uuid.uuid4()),
            'rule_id': rule_id,
            'name': rule['name'],
            'severity': rule['severity'],
            'message': rule['message'],
            'metrics': metrics,
            'timestamp': datetime.now().isoformat(),
        }

    def get_alert_history(
        self,
        limit: int = 100,
        severity: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取告警历史"""
        history = self.alert_history.copy()

        # 过滤严重级别
        if severity:
            history = [a for a in history if a['severity'] == severity]

        # 限制数量并倒序
        history.reverse()
        return history[:limit]

    def clear_alert_history(self):
        """清除告警历史"""
        self.alert_history.clear()
        logger.info("告警历史已清除")

    async def trigger_alert(self, alert: Dict[str, Any]) -> bool:
        """触发告警（用于外部触发）"""
        # 记录告警历史
        self.alert_history.append(alert)
        logger.warning(f"外部触发告警: {alert['name']}")

        # TODO: 发送通知
        # await self._send_alert_notification(alert)

        return True
```

#### 1.3 监控仪表板（~150行）

**功能特性**：
- **实时展示**: 系统指标实时展示
- **历史趋势**: 指标历史趋势图
- **告警列表**: 实时告警列表
- **健康状态**: 系统健康状态概览

**核心类设计**：
```python
class Dashboard:
    """监控仪表板

    生成监控仪表板数据。
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.widgets = {}

    def generate_dashboard(
        self,
        metrics_collector: MetricsCollector,
        alert_manager: AlertManager,
        health_checker: HealthChecker
    ) -> Dict[str, Any]:
        """生成仪表板数据"""
        dashboard = {
            'timestamp': datetime.now().isoformat(),
            'title': '数字货币套利系统 - 监控仪表板',
            'widgets': {
                'system_metrics': self._generate_system_metrics_widget(metrics_collector),
                'alert_list': self._generate_alert_list_widget(alert_manager),
                'health_status': self._generate_health_status_widget(health_checker),
                'performance_summary': self._generate_performance_summary_widget(metrics_collector),
            },
        }

        return dashboard

    def _generate_system_metrics_widget(self, metrics_collector: MetricsCollector) -> Dict[str, Any]:
        """生成系统指标组件"""
        latest = metrics_collector.get_latest_metrics()

        if not latest:
            return {'status': 'no_data', 'message': '暂无数据'}

        system_metrics = latest.get('system', {})

        return {
            'type': 'system_metrics',
            'data': {
                'cpu': {
                    'value': system_metrics.get('cpu_percent', 0),
                    'unit': '%',
                    'status': self._get_metric_status(system_metrics.get('cpu_percent', 0), 80, 90),
                },
                'memory': {
                    'value': system_metrics.get('memory_percent', 0),
                    'unit': '%',
                    'status': self._get_metric_status(system_metrics.get('memory_percent', 0), 80, 90),
                },
                'disk': {
                    'value': system_metrics.get('disk_percent', 0),
                    'unit': '%',
                    'status': self._get_metric_status(system_metrics.get('disk_percent', 0), 80, 95),
                },
            },
            'timestamp': latest['timestamp'],
        }

    def _generate_alert_list_widget(self, alert_manager: AlertManager) -> Dict[str, Any]:
        """生成告警列表组件"""
        alerts = alert_manager.get_alert_history(limit=20)

        return {
            'type': 'alert_list',
            'data': {
                'alerts': alerts,
                'count': len(alerts),
                'severity_breakdown': self._calculate_severity_breakdown(alerts),
            },
        }

    def _generate_health_status_widget(self, health_checker: HealthChecker) -> Dict[str, Any]:
        """生成健康状态组件"""
        # 获取健康检查历史
        history = health_checker.get_check_history(limit=10)

        if not history:
            return {'status': 'no_data', 'message': '暂无健康检查数据'}

        # 获取最新检查结果
        latest_check = history[0]

        return {
            'type': 'health_status',
            'data': {
                'overall_status': latest_check.get('status', 'unknown'),
                'last_check_time': latest_check.get('timestamp'),
                'checks': latest_check.get('details', {}),
            },
        }

    def _generate_performance_summary_widget(self, metrics_collector: MetricsCollector) -> Dict[str, Any]:
        """生成性能摘要组件"""
        # 获取CPU历史
        cpu_history = metrics_collector.get_metrics_history('system', limit=100)

        if not cpu_history:
            return {'status': 'no_data', 'message': '暂无性能数据'}

        # 计算统计数据
        cpu_values = [m['cpu_percent'] for m in cpu_history]

        return {
            'type': 'performance_summary',
            'data': {
                'cpu': {
                    'avg': sum(cpu_values) / len(cpu_values),
                    'max': max(cpu_values),
                    'min': min(cpu_values),
                    'current': cpu_values[-1],
                },
                'data_points': len(cpu_values),
                'time_range': {
                    'start': cpu_history[0]['timestamp'],
                    'end': cpu_history[-1]['timestamp'],
                },
            },
        }

    def _get_metric_status(
        self,
        value: float,
        warning_threshold: float,
        critical_threshold: float
    ) -> str:
        """获取指标状态"""
        if value >= critical_threshold:
            return 'critical'
        elif value >= warning_threshold:
            return 'warning'
        else:
            return 'normal'

    def _calculate_severity_breakdown(self, alerts: List[Dict[str, Any]]) -> Dict[str, int]:
        """计算严重级别分布"""
        breakdown = {
            'INFO': 0,
            'WARNING': 0,
            'ERROR': 0,
            'CRITICAL': 0,
        }

        for alert in alerts:
            severity = alert.get('severity', 'INFO')
            if severity in breakdown:
                breakdown[severity] += 1

        return breakdown

    def export_dashboard_html(self, dashboard: Dict[str, Any]) -> str:
        """导出HTML仪表板"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>数字货币套利系统 - 监控仪表板</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            background-color: #333;
            color: white;
            padding: 20px;
            border-radius: 5px;
        }}
        .widget {{
            background-color: white;
            padding: 20px;
            margin: 10px 0;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .metric {{
            display: inline-block;
            margin: 10px;
            padding: 15px;
            background-color: #f9f9f9;
            border-radius: 5px;
            min-width: 150px;
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: bold;
        }}
        .status-normal {{ color: green; }}
        .status-warning {{ color: orange; }}
        .status-critical {{ color: red; }}
        .alert {{
            padding: 10px;
            margin: 5px 0;
            border-left: 4px solid #333;
            background-color: #f9f9f9;
        }}
        .alert-WARNING {{ border-left-color: orange; }}
        .alert-ERROR {{ border-left-color: red; }}
        .alert-CRITICAL {{ border-left-color: darkred; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{dashboard['title']}</h1>
            <p>更新时间: {dashboard['timestamp']}</p>
        </div>

        {self._generate_widgets_html(dashboard['widgets'])}
    </div>
</body>
</html>
"""
        return html

    def _generate_widgets_html(self, widgets: Dict[str, Any]) -> str:
        """生成组件HTML"""
        html = ""

        # 系统指标组件
        if 'system_metrics' in widgets:
            widget = widgets['system_metrics']
            html += f"""
<div class="widget">
    <h2>系统指标</h2>
"""
            if 'data' in widget:
                metrics = widget['data']
                html += f"""
    <div class="metric">
        <div>CPU</div>
        <div class="metric-value status-{metrics['cpu']['status']}">{metrics['cpu']['value']:.1f}%</div>
    </div>
    <div class="metric">
        <div>内存</div>
        <div class="metric-value status-{metrics['memory']['status']}">{metrics['memory']['value']:.1f}%</div>
    </div>
    <div class="metric">
        <div>磁盘</div>
        <div class="metric-value status-{metrics['disk']['status']}">{metrics['disk']['value']:.1f}%</div>
    </div>
"""
            html += "</div>"

        # 告警列表组件
        if 'alert_list' in widgets:
            widget = widgets['alert_list']
            html += """
<div class="widget">
    <h2>最近告警</h2>
"""
            if 'data' in widget and widget['data'].get('alerts'):
                for alert in widget['data']['alerts'][:10]:
                    html += f"""
    <div class="alert alert-{alert['severity']}">
        <strong>{alert['name']}</strong> - {alert['message']}
        <br/>
        <small>{alert['timestamp']}</small>
    </div>
"""
            else:
                html += "<p>暂无告警</p>"

            html += "</div>"

        # 健康状态组件
        if 'health_status' in widgets:
            widget = widgets['health_status']
            html += f"""
<div class="widget">
    <h2>系统健康状态</h2>
"""
            if 'data' in widget:
                health_data = widget['data']
                html += f"""
    <p><strong>总体状态:</strong> {health_data['overall_status']}</p>
    <p><strong>最后检查时间:</strong> {health_data['last_check_time']}</p>
"""
            html += "</div>"

        return html
```

#### 1.4 通知服务（~150行）

**功能特性**：
- **多渠道通知**: 控制台/文件/邮件/Webhook
- **通知过滤**: 按严重级别过滤
- **通知限流**: 避免频繁通知
- **通知模板**: 可自定义通知模板

**核心类设计**：
```python
class NotificationService:
    """通知服务

    多渠道通知服务。
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.channels = {}
        self.notification_history = []
        self.rate_limits = {}

        # 初始化通知渠道
        self._init_channels()

    def _init_channels(self):
        """初始化通知渠道"""
        # 控制台渠道
        self.channels['console'] = {
            'enabled': self.config.get('console_enabled', True),
            'handler': self._send_console_notification,
        }

        # 文件渠道
        self.channels['file'] = {
            'enabled': self.config.get('file_enabled', True),
            'path': self.config.get('file_path', 'logs/notifications.log'),
            'handler': self._send_file_notification,
        }

        # 邮件渠道
        if self.config.get('email_enabled', False):
            self.channels['email'] = {
                'enabled': True,
                'handler': self._send_email_notification,
            }

    async def send_notification(
        self,
        notification: Dict[str, Any]
    ) -> bool:
        """发送通知"""
        notification_id = notification.get('id', str(uuid.uuid4()))

        # 检查限流
        if self._is_rate_limited(notification):
            logger.debug(f"通知被限流: {notification_id}")
            return False

        # 发送到所有启用的渠道
        success = False
        for channel_name, channel in self.channels.items():
            if channel['enabled']:
                try:
                    await channel['handler'](notification)
                    success = True
                    logger.info(f"通知已发送到 {channel_name}: {notification_id}")
                except Exception as e:
                    logger.error(f"发送通知到 {channel_name} 失败: {e}")

        # 记录历史
        self.notification_history.append({
            'id': notification_id,
            **notification,
            'sent_at': datetime.now().isoformat(),
        })

        return success

    async def _send_console_notification(self, notification: Dict[str, Any]):
        """发送控制台通知"""
        severity = notification.get('severity', 'INFO')
        message = notification.get('message', '')

        if severity == 'CRITICAL':
            logger.critical(f"[ALERT] {message}")
        elif severity == 'ERROR':
            logger.error(f"[ALERT] {message}")
        elif severity == 'WARNING':
            logger.warning(f"[ALERT] {message}")
        else:
            logger.info(f"[INFO] {message}")

    async def _send_file_notification(self, notification: Dict[str, Any]):
        """发送文件通知"""
        file_path = self.channels['file']['path']

        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(f"{notification}\n")

    async def _send_email_notification(self, notification: Dict[str, Any]):
        """发送邮件通知"""
        # TODO: 实现邮件发送
        pass

    def _is_rate_limited(self, notification: Dict[str, Any]) -> bool:
        """检查是否限流"""
        # 简单限流：相同类型通知1分钟内只发送一次
        notification_type = notification.get('type', 'unknown')

        if notification_type not in self.rate_limits:
            self.rate_limits[notification_type] = time.time()
            return False

        last_sent = self.rate_limits[notification_type]
        if time.time() - last_sent < 60:  # 60秒限流
            return True

        self.rate_limits[notification_type] = time.time()
        return False

    async def send_alert(self, alert: Dict[str, Any]) -> bool:
        """发送告警通知"""
        notification = {
            'type': 'alert',
            'severity': alert.get('severity', 'INFO'),
            'message': alert.get('message', ''),
            'details': alert,
        }

        return await self.send_notification(notification)

    def get_notification_history(
        self,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取通知历史"""
        history = self.notification_history.copy()
        history.reverse()
        return history[:limit]
```

---

### 2. 运维自动化模块（预估: 450行）

#### 2.1 自动扩缩容（~150行）

**功能特性**：
- **自动扩容**: 资源不足时自动扩容
- **自动缩容**: 资源充足时自动缩容
- **策略配置**: 灵活的扩缩容策略
- **安全限制**: 最大最小资源限制

**核心类设计**：
```python
class AutoScaler:
    """自动扩缩容

    根据负载自动调整资源。
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.scaling_policies = {}
        self.scaling_history = []

        # 添加默认扩缩容策略
        self._add_default_policies()

    def _add_default_policies(self):
        """添加默认扩缩容策略"""
        # CPU扩容策略
        self.add_scaling_policy({
            'name': 'cpu_scale_up',
            'metric': 'cpu_percent',
            'threshold': 80,
            'direction': 'up',
            'action': 'increase_cache_size',
            'action_params': {'increment': 1000},
            'cooldown': 300,
        })

        # CPU缩容策略
        self.add_scaling_policy({
            'name': 'cpu_scale_down',
            'metric': 'cpu_percent',
            'threshold': 20,
            'direction': 'down',
            'action': 'decrease_cache_size',
            'action_params': {'decrement': 500},
            'cooldown': 600,
        })

    def add_scaling_policy(self, policy: Dict[str, Any]) -> str:
        """添加扩缩容策略"""
        policy_id = policy.get('name', str(uuid.uuid4()))
        self.scaling_policies[policy_id] = policy
        logger.info(f"添加扩缩容策略: {policy_id}")
        return policy_id

    async def evaluate_scaling(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """评估是否需要扩缩容"""
        scaling_actions = []

        for policy_id, policy in self.scaling_policies.items():
            try:
                # 检查冷却期
                if self._is_policy_in_cooldown(policy_id, policy):
                    continue

                # 评估条件
                metric_name = policy['metric']
                metric_value = self._get_metric_value(metrics, metric_name)

                if metric_value is None:
                    continue

                # 检查阈值
                threshold = policy['threshold']
                direction = policy['direction']

                if direction == 'up' and metric_value >= threshold:
                    # 需要扩容
                    action = self._create_scaling_action(policy_id, policy, metrics, 'up')
                    scaling_actions.append(action)

                elif direction == 'down' and metric_value <= threshold:
                    # 需要缩容
                    action = self._create_scaling_action(policy_id, policy, metrics, 'down')
                    scaling_actions.append(action)

            except Exception as e:
                logger.error(f"评估扩缩容策略 {policy_id} 失败: {e}")

        return scaling_actions

    def _get_metric_value(self, metrics: Dict[str, Any], metric_name: str) -> Optional[float]:
        """获取指标值"""
        # 从系统指标中获取
        if metric_name in metrics:
            return metrics[metric_name]

        # 从嵌套的system指标中获取
        if 'system' in metrics and metric_name in metrics['system']:
            return metrics['system'][metric_name]

        return None

    def _is_policy_in_cooldown(self, policy_id: str, policy: Dict[str, Any]) -> bool:
        """检查策略是否在冷却期"""
        # TODO: 实现冷却期检查
        return False

    def _create_scaling_action(
        self,
        policy_id: str,
        policy: Dict[str, Any],
        metrics: Dict[str, Any],
        direction: str
    ) -> Dict[str, Any]:
        """创建扩缩容动作"""
        return {
            'id': str(uuid.uuid4()),
            'policy_id': policy_id,
            'direction': direction,
            'action': policy['action'],
            'action_params': policy['action_params'],
            'metrics': metrics,
            'timestamp': datetime.now().isoformat(),
        }

    async def scale_up(self, target: str) -> bool:
        """扩容"""
        # TODO: 实现具体的扩容逻辑
        logger.info(f"扩容: {target}")
        return True

    async def scale_down(self, target: str) -> bool:
        """缩容"""
        # TODO: 实现具体的缩容逻辑
        logger.info(f"缩容: {target}")
        return True

    def get_scaling_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取扩缩容历史"""
        history = self.scaling_history.copy()
        history.reverse()
        return history[:limit]
```

#### 2.2 自动恢复（~150行）

**功能特性**：
- **故障检测**: 自动检测系统故障
- **自动恢复**: 自动执行恢复脚本
- **恢复脚本**: 可自定义恢复脚本
- **恢复历史**: 完整的恢复历史记录

**核心类设计**：
```python
class AutoRecovery:
    """自动恢复

    故障自动检测和恢复。
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.recovery_scripts = {}
        self.recovery_history = []

        # 添加默认恢复脚本
        self._add_default_scripts()

    def _add_default_scripts(self):
        """添加默认恢复脚本"""
        # 存储故障恢复
        self.add_recovery_script('storage_recovery', self._recover_storage)
        # 数据库故障恢复
        self.add_recovery_script('database_recovery', self._recover_database)

    def add_recovery_script(
        self,
        name: str,
        script: Callable
    ):
        """添加恢复脚本"""
        self.recovery_scripts[name] = script
        logger.info(f"添加恢复脚本: {name}")

    async def detect_failure(
        self,
        health_status: Dict[str, Any]
    ) -> List[str]:
        """检测故障"""
        failures = []

        # 检查各组件健康状态
        if health_status.get('overall_status') == 'unhealthy':
            failures.append('system')

        # 检查具体组件
        checks = health_status.get('checks', {})
        for component, check in checks.items():
            if check.get('status') == 'unhealthy':
                failures.append(component)

        return failures

    async def execute_recovery(self, failure_type: str) -> bool:
        """执行恢复"""
        logger.info(f"开始恢复: {failure_type}")

        try:
            # 查找对应的恢复脚本
            script_name = f"{failure_type}_recovery"

            if script_name not in self.recovery_scripts:
                logger.warning(f"未找到恢复脚本: {script_name}")
                return False

            # 执行恢复脚本
            script = self.recovery_scripts[script_name]
            success = await script()

            # 记录恢复历史
            self.recovery_history.append({
                'failure_type': failure_type,
                'script_name': script_name,
                'success': success,
                'timestamp': datetime.now().isoformat(),
            })

            if success:
                logger.info(f"恢复成功: {failure_type}")
            else:
                logger.error(f"恢复失败: {failure_type}")

            return success

        except Exception as e:
            logger.error(f"执行恢复脚本失败: {e}")
            return False

    async def _recover_storage(self) -> bool:
        """恢复存储"""
        logger.info("恢复存储系统...")

        try:
            # 尝试重新初始化存储
            from storage.storage_factory import create_auto_storage
            from deployment.deployment_config import DeploymentConfig

            config = DeploymentConfig(env='development')
            storage_config = config.get_storage_config()

            # 创建新存储实例
            storage = await create_auto_storage(storage_config)

            # 验证存储
            test_id = await storage.add_knowledge("recovery_test", {'test': True})
            result = await storage.get_knowledge(test_id)

            if result:
                logger.info("存储恢复成功")
                return True
            else:
                logger.error("存储恢复失败")
                return False

        except Exception as e:
            logger.error(f"存储恢复异常: {e}")
            return False

    async def _recover_database(self) -> bool:
        """恢复数据库"""
        logger.info("恢复数据库...")

        try:
            import sqlite3
            from pathlib import Path

            db_path = './local_vector_db.sqlite3'

            # 检查数据库文件
            if not Path(db_path).exists():
                logger.warning("数据库文件不存在，尝试创建...")
                # 数据库会在首次使用时自动创建
                return True

            # 尝试连接数据库
            conn = sqlite3.connect(db_path)
            conn.execute("PRAGMA integrity_check")
            conn.close()

            logger.info("数据库恢复成功")
            return True

        except Exception as e:
            logger.error(f"数据库恢复异常: {e}")
            return False

    def get_recovery_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取恢复历史"""
        history = self.recovery_history.copy()
        history.reverse()
        return history[:limit]
```

#### 2.3 备份管理器（~150行）

**功能特性**：
- **自动备份**: 定期自动备份
- **备份类型**: 完整备份/增量备份
- **备份恢复**: 快速恢复备份
- **备份清理**: 自动清理过期备份

**核心类设计**：
```python
class BackupManager:
    """备份管理器

    自动化备份和恢复。
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.backup_schedule = {}
        self.backup_history = []

        # 创建备份目录
        self.backup_dir = Path('./backups')
        self.backup_dir.mkdir(exist_ok=True)

    async def create_backup(
        self,
        backup_type: str = 'full'
    ) -> str:
        """创建备份"""
        backup_id = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"开始创建备份: {backup_id} ({backup_type})")

        try:
            # 创建备份目录
            backup_path = self.backup_dir / backup_id
            backup_path.mkdir(exist_ok=True)

            # 备份数据库
            if backup_type in ['full', 'database']:
                await self._backup_database(backup_path)

            # 备份配置
            if backup_type == 'full':
                await self._backup_config(backup_path)

            # 备份日志
            if backup_type == 'full':
                await self._backup_logs(backup_path)

            # 记录备份历史
            self.backup_history.append({
                'backup_id': backup_id,
                'backup_type': backup_type,
                'backup_path': str(backup_path),
                'timestamp': datetime.now().isoformat(),
                'size_mb': self._calculate_backup_size(backup_path),
            })

            logger.info(f"备份创建成功: {backup_id}")

            return backup_id

        except Exception as e:
            logger.error(f"创建备份失败: {e}")
            raise

    async def _backup_database(self, backup_path: Path):
        """备份数据库"""
        import shutil

        db_files = [
            './local_vector_db.sqlite3',
            './crypto_arbitrage.db',
        ]

        for db_file in db_files:
            db_path = Path(db_file)
            if db_path.exists():
                shutil.copy2(db_path, backup_path / db_path.name)
                logger.info(f"数据库已备份: {db_file}")

    async def _backup_config(self, backup_path: Path):
        """备份配置"""
        import shutil

        config_file = './config/config.yaml'
        config_path = Path(config_file)

        if config_path.exists():
            shutil.copy2(config_path, backup_path / 'config.yaml')
            logger.info("配置文件已备份")

    async def _backup_logs(self, backup_path: Path):
        """备份日志"""
        import shutil

        logs_dir = Path('./logs')
        backup_logs_dir = backup_path / 'logs'

        if logs_dir.exists():
            shutil.copytree(logs_dir, backup_logs_dir)
            logger.info("日志文件已备份")

    def _calculate_backup_size(self, backup_path: Path) -> float:
        """计算备份大小"""
        total_size = 0

        for file_path in backup_path.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size

        return total_size / 1024 / 1024  # MB

    async def restore_backup(self, backup_id: str) -> bool:
        """恢复备份"""
        logger.info(f"开始恢复备份: {backup_id}")

        try:
            # 查找备份
            backup_info = None
            for info in self.backup_history:
                if info['backup_id'] == backup_id:
                    backup_info = info
                    break

            if not backup_info:
                logger.error(f"未找到备份: {backup_id}")
                return False

            backup_path = Path(backup_info['backup_path'])

            if not backup_path.exists():
                logger.error(f"备份目录不存在: {backup_path}")
                return False

            # 恢复数据库
            await self._restore_database(backup_path)

            # 恢复配置
            if backup_info['backup_type'] == 'full':
                await self._restore_config(backup_path)

            logger.info(f"备份恢复成功: {backup_id}")

            return True

        except Exception as e:
            logger.error(f"恢复备份失败: {e}")
            return False

    async def _restore_database(self, backup_path: Path):
        """恢复数据库"""
        import shutil

        db_files = ['local_vector_db.sqlite3', 'crypto_arbitrage.db']

        for db_file in db_files:
            backup_db = backup_path / db_file
            if backup_db.exists():
                shutil.copy2(backup_db, f'./{db_file}')
                logger.info(f"数据库已恢复: {db_file}")

    async def _restore_config(self, backup_path: Path):
        """恢复配置"""
        import shutil

        backup_config = backup_path / 'config.yaml'
        if backup_config.exists():
            shutil.copy2(backup_config, './config/config.yaml')
            logger.info("配置文件已恢复")

    async def list_backups(self) -> List[Dict[str, Any]]:
        """列出备份"""
        return self.backup_history.copy()

    async def cleanup_old_backups(self, keep_days: int = 30) -> int:
        """清理旧备份"""
        import shutil

        cutoff_time = datetime.now() - timedelta(days=keep_days)
        cleaned_count = 0

        for info in self.backup_history.copy():
            backup_time = datetime.fromisoformat(info['timestamp'])

            if backup_time < cutoff_time:
                backup_path = Path(info['backup_path'])

                if backup_path.exists():
                    shutil.rmtree(backup_path)
                    logger.info(f"清理旧备份: {info['backup_id']}")

                self.backup_history.remove(info)
                cleaned_count += 1

        logger.info(f"清理了 {cleaned_count} 个旧备份")

        return cleaned_count

    def get_backup_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取备份历史"""
        history = self.backup_history.copy()
        history.reverse()
        return history[:limit]
```

---

## 🎯 性能目标

### Phase 11 性能指标

| 指标 | Phase 10 | Phase 11目标 | 提升 |
|------|----------|-------------|------|
| **监控延迟** | 基准 | <1秒 | ✅ 新增 |
| **告警响应** | 无告警 | <30秒 | ✅ 新增 |
| **监控覆盖** | 无覆盖 | 100%组件 | ✅ 新增 |
| **自动恢复** | 无自动化 | <5分钟 | ✅ 新增 |
| **备份成功率** | 手动 | >99.9% | ✅ 新增 |
| **系统可用性** | 基准 | >99.9% | ✅ 提升 |

---

## 🚀 实施计划

### Week 1: 实时监控模块
- Day 1-2: 实现指标收集器
- Day 3-4: 实现告警管理器
- Day 5-6: 实现监控仪表板
- Day 7: 集成测试

### Week 2: 运维自动化模块
- Day 1-2: 实现自动扩缩容
- Day 3-4: 实现自动恢复
- Day 5-6: 实现备份管理器
- Day 7: 集成测试

### Week 3: 完善与文档
- Day 1-2: 实现通知服务
- Day 3-4: 完整测试和优化
- Day 5-6: 文档和报告生成
- Day 7: 知识库更新

---

## 📁 交付清单

### 核心实现
- [ ] `monitoring/metrics_collector.py` (150行)
- [ ] `monitoring/alert_manager.py` (150行)
- [ ] `monitoring/dashboard.py` (150行)
- [ ] `monitoring/notification_service.py` (150行)
- [ ] `automation/auto_scaler.py` (150行)
- [ ] `automation/auto_recovery.py` (150行)
- [ ] `automation/backup_manager.py` (150行)

### 测试套件
- [ ] `tests/test_phase11_monitoring.py` (200行)
- [ ] `tests/test_phase11_automation.py` (200行)
- [ ] `tests/test_phase11_integration.py` (200行)

### 文档
- [ ] `PHASE_11_DESIGN_PLAN.md` (本文档)
- [ ] `V11_0_PHASE_11_ITERATION_REPORT.md`
- [ ] `MONITORING_GUIDE.md`
- [ ] `AUTOMATION_GUIDE.md`

---

## 🎯 成功标准

### 功能完整性
- [ ] 实时监控模块完成
- [ ] 运维自动化模块完成
- [ ] 通知服务完成
- [ ] 集成测试通过

### 性能指标
- [ ] 监控延迟 <1秒
- [ ] 告警响应 <30秒
- [ ] 监控覆盖 100%组件
- [ ] 自动恢复 <5分钟
- [ ] 备份成功率 >99.9%
- [ ] 系统可用性 >99.9%

### 代码质量
- [ ] 测试覆盖率 >90%
- [ ] 文档完整度 >90%
- [ ] 代码审查通过
- [ ] 性能测试通过

---

## 🔮 下一步

Phase 11完成后，系统将具备：
1. ✅ 完整的实时监控能力
2. ✅ 智能告警体系
3. ✅ 自动化运维能力
4. ✅ 完整的备份恢复机制

---

**设计完成**: Phase 11 实时监控与运维自动化完善
**预估代码量**: ~1,850行
**预估时间**: 3周
**风险等级**: 🟢 低（基于稳定的Phase 10）
