"""告警管理器 - Phase 11核心模块

管理系统告警。

核心功能：
1. 告警规则 - 灵活的告警规则配置
2. 多级告警 - INFO/WARNING/ERROR/CRITICAL
3. 告警去重 - 避免重复告警
4. 告警历史 - 完整的告警历史记录

创建时间：2026-04-19 20:38:00
"""

import logging
import time
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class AlertManager:
    """告警管理器

    管理系统告警。
    """

    # 严重级别
    SEVERITY_INFO = 'INFO'
    SEVERITY_WARNING = 'WARNING'
    SEVERITY_ERROR = 'ERROR'
    SEVERITY_CRITICAL = 'CRITICAL'

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化告警管理器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.alert_rules: Dict[str, Dict[str, Any]] = {}
        self.alert_history: List[Dict[str, Any]] = []
        self.alert_cooldowns: Dict[str, float] = {}  # 告警冷却期

        # 添加默认告警规则
        self._add_default_rules()

        logger.info("告警管理器初始化完成")

    def _add_default_rules(self):
        """添加默认告警规则"""
        # CPU告警
        self.add_alert_rule({
            'name': 'high_cpu_usage',
            'condition': lambda metrics: metrics.get('cpu_percent', 0) > 80,
            'severity': self.SEVERITY_WARNING,
            'message': 'CPU使用率过高',
            'cooldown': 300,  # 5分钟冷却期
            'enabled': True,
        })

        # CPU严重告警
        self.add_alert_rule({
            'name': 'critical_cpu_usage',
            'condition': lambda metrics: metrics.get('cpu_percent', 0) > 95,
            'severity': self.SEVERITY_CRITICAL,
            'message': 'CPU使用率严重过高',
            'cooldown': 180,  # 3分钟冷却期
            'enabled': True,
        })

        # 内存告警
        self.add_alert_rule({
            'name': 'high_memory_usage',
            'condition': lambda metrics: metrics.get('memory_percent', 0) > 80,
            'severity': self.SEVERITY_WARNING,
            'message': '内存使用率过高',
            'cooldown': 300,
            'enabled': True,
        })

        # 内存严重告警
        self.add_alert_rule({
            'name': 'critical_memory_usage',
            'condition': lambda metrics: metrics.get('memory_percent', 0) > 95,
            'severity': self.SEVERITY_CRITICAL,
            'message': '内存使用率严重过高',
            'cooldown': 180,
            'enabled': True,
        })

        # 磁盘告警
        self.add_alert_rule({
            'name': 'high_disk_usage',
            'condition': lambda metrics: metrics.get('disk_percent', 0) > 85,
            'severity': self.SEVERITY_WARNING,
            'message': '磁盘使用率过高',
            'cooldown': 600,  # 10分钟冷却期
            'enabled': True,
        })

        # 磁盘严重告警
        self.add_alert_rule({
            'name': 'critical_disk_usage',
            'condition': lambda metrics: metrics.get('disk_percent', 0) > 95,
            'severity': self.SEVERITY_CRITICAL,
            'message': '磁盘使用率严重过高',
            'cooldown': 300,  # 5分钟冷却期
            'enabled': True,
        })

        # 存储延迟告警
        self.add_alert_rule({
            'name': 'high_storage_latency',
            'condition': lambda metrics: metrics.get('operation_latency_ms', 0) > 1000,
            'severity': self.SEVERITY_WARNING,
            'message': '存储操作延迟过高',
            'cooldown': 300,
            'enabled': True,
        })

        logger.info(f"已添加 {len(self.alert_rules)} 个默认告警规则")

    def add_alert_rule(self, rule: Dict[str, Any]) -> str:
        """添加告警规则

        Args:
            rule: 告警规则字典

        Returns:
            规则ID
        """
        rule_id = rule.get('name', str(uuid.uuid4()))

        # 验证规则
        if 'name' not in rule:
            raise ValueError("告警规则必须包含name字段")
        if 'condition' not in rule:
            raise ValueError("告警规则必须包含condition字段")
        if 'severity' not in rule:
            raise ValueError("告警规则必须包含severity字段")
        if 'message' not in rule:
            raise ValueError("告警规则必须包含message字段")

        # 设置默认值
        rule.setdefault('cooldown', 300)
        rule.setdefault('enabled', True)

        self.alert_rules[rule_id] = rule
        logger.info(f"添加告警规则: {rule_id}")

        return rule_id

    def remove_alert_rule(self, rule_id: str) -> bool:
        """移除告警规则

        Args:
            rule_id: 规则ID

        Returns:
            是否成功移除
        """
        if rule_id in self.alert_rules:
            del self.alert_rules[rule_id]
            logger.info(f"移除告警规则: {rule_id}")
            return True
        return False

    def get_alert_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """获取告警规则

        Args:
            rule_id: 规则ID

        Returns:
            告警规则字典
        """
        return self.alert_rules.get(rule_id)

    def list_alert_rules(self) -> List[Dict[str, Any]]:
        """列出所有告警规则

        Returns:
            告警规则列表
        """
        return list(self.alert_rules.values())

    async def evaluate_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """评估告警

        Args:
            metrics: 指标字典

        Returns:
            触发的告警列表
        """
        triggered_alerts = []

        for rule_id, rule in self.alert_rules.items():
            try:
                # 跳过禁用的规则
                if not rule.get('enabled', True):
                    continue

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

                    logger.warning(
                        f"触发告警: {rule['name']} - {rule['message']} "
                        f"[{rule['severity']}]"
                    )

            except Exception as e:
                logger.error(f"评估告警规则 {rule_id} 失败: {e}")

        return triggered_alerts

    def _is_in_cooldown(self, rule_id: str, rule: Dict[str, Any]) -> bool:
        """检查是否在冷却期

        Args:
            rule_id: 规则ID
            rule: 规则字典

        Returns:
            是否在冷却期
        """
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
        """创建告警

        Args:
            rule_id: 规则ID
            rule: 规则字典
            metrics: 指标字典

        Returns:
            告警字典
        """
        return {
            'id': str(uuid.uuid4()),
            'rule_id': rule_id,
            'name': rule['name'],
            'severity': rule['severity'],
            'message': rule['message'],
            'metrics': metrics.copy(),
            'rule': rule,
            'timestamp': datetime.now().isoformat(),
        }

    async def trigger_alert(self, alert: Dict[str, Any]) -> bool:
        """触发告警（用于外部触发）

        Args:
            alert: 告警字典

        Returns:
            是否成功
        """
        # 记录告警历史
        alert.setdefault('id', str(uuid.uuid4()))
        alert.setdefault('timestamp', datetime.now().isoformat())

        self.alert_history.append(alert)

        logger.warning(
            f"外部触发告警: {alert.get('name', 'unknown')} - "
            f"{alert.get('message', '')} [{alert.get('severity', 'INFO')}]"
        )

        # TODO: 发送通知
        # await self._send_alert_notification(alert)

        return True

    def get_alert_history(
        self,
        limit: int = 100,
        severity: Optional[str] = None,
        rule_name: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取告警历史

        Args:
            limit: 返回数量限制
            severity: 严重级别过滤
            rule_name: 规则名称过滤
            start_time: 开始时间（ISO格式）
            end_time: 结束时间（ISO格式）

        Returns:
            告警历史列表
        """
        history = self.alert_history.copy()

        # 过滤严重级别
        if severity:
            history = [a for a in history if a.get('severity') == severity]

        # 过滤规则名称
        if rule_name:
            history = [a for a in history if a.get('name') == rule_name]

        # 时间过滤
        if start_time:
            start_dt = datetime.fromisoformat(start_time)
            history = [a for a in history if datetime.fromisoformat(a['timestamp']) >= start_dt]

        if end_time:
            end_dt = datetime.fromisoformat(end_time)
            history = [a for a in history if datetime.fromisoformat(a['timestamp']) <= end_dt]

        # 限制数量并倒序（最新的在前）
        history.reverse()
        return history[:limit]

    def get_alert_statistics(
        self,
        hours: int = 24
    ) -> Dict[str, Any]:
        """获取告警统计

        Args:
            hours: 统计时间范围（小时）

        Returns:
            统计信息字典
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)

        # 过滤时间范围内的告警
        recent_alerts = [
            a for a in self.alert_history
            if datetime.fromisoformat(a['timestamp']) >= cutoff_time
        ]

        # 统计信息
        severity_counts = {
            self.SEVERITY_INFO: 0,
            self.SEVERITY_WARNING: 0,
            self.SEVERITY_ERROR: 0,
            self.SEVERITY_CRITICAL: 0,
        }

        rule_counts = {}

        for alert in recent_alerts:
            severity = alert.get('severity', self.SEVERITY_INFO)
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

            rule_name = alert.get('name', 'unknown')
            rule_counts[rule_name] = rule_counts.get(rule_name, 0) + 1

        return {
            'time_range_hours': hours,
            'total_alerts': len(recent_alerts),
            'severity_breakdown': severity_counts,
            'rule_breakdown': rule_counts,
            'most_triggered_rule': max(rule_counts.items(), key=lambda x: x[1])[0] if rule_counts else None,
        }

    def clear_alert_history(self, before_time: Optional[str] = None):
        """清除告警历史

        Args:
            before_time: 清除此时间之前的告警（None表示清除全部）
        """
        if before_time:
            before_dt = datetime.fromisoformat(before_time)
            self.alert_history = [
                a for a in self.alert_history
                if datetime.fromisoformat(a['timestamp']) >= before_dt
            ]
            logger.info(f"已清除 {before_time} 之前的告警历史")
        else:
            self.alert_history.clear()
            logger.info("已清除所有告警历史")

    def clear_cooldowns(self):
        """清除所有冷却期"""
        self.alert_cooldowns.clear()
        logger.info("已清除所有告警冷却期")

    def enable_alert_rule(self, rule_id: str) -> bool:
        """启用告警规则

        Args:
            rule_id: 规则ID

        Returns:
            是否成功
        """
        if rule_id in self.alert_rules:
            self.alert_rules[rule_id]['enabled'] = True
            logger.info(f"启用告警规则: {rule_id}")
            return True
        return False

    def disable_alert_rule(self, rule_id: str) -> bool:
        """禁用告警规则

        Args:
            rule_id: 规则ID

        Returns:
            是否成功
        """
        if rule_id in self.alert_rules:
            self.alert_rules[rule_id]['enabled'] = False
            logger.info(f"禁用告警规则: {rule_id}")
            return True
        return False

    def __repr__(self) -> str:
        """字符串表示

        Returns:
            字符串表示
        """
        enabled_count = sum(1 for r in self.alert_rules.values() if r.get('enabled', True))
        return f"AlertManager(rules={len(self.alert_rules)}, enabled={enabled_count}, history={len(self.alert_history)})"
