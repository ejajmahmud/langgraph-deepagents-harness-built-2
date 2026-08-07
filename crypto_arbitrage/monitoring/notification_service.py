"""通知服务 - Phase 11核心模块

多渠道通知服务。

核心功能：
1. 多渠道通知 - 控制台/文件/邮件/Webhook
2. 通知过滤 - 按严重级别过滤
3. 通知限流 - 避免频繁通知
4. 通知历史 - 完整的通知历史记录

创建时间：2026-04-19 20:45:00
"""

import logging
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class NotificationService:
    """通知服务

    多渠道通知服务。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化通知服务

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.channels: Dict[str, Dict[str, Any]] = {}
        self.notification_history: List[Dict[str, Any]] = []
        self.rate_limits: Dict[str, float] = {}

        # 初始化通知渠道
        self._init_channels()

        logger.info(f"通知服务初始化完成，已启用 {len(self.channels)} 个渠道")

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

        # 邮件渠道（默认禁用）
        if self.config.get('email_enabled', False):
            self.channels['email'] = {
                'enabled': True,
                'smtp_host': self.config.get('smtp_host', 'smtp.gmail.com'),
                'smtp_port': self.config.get('smtp_port', 587),
                'username': self.config.get('email_username', ''),
                'password': self.config.get('email_password', ''),
                'to_addresses': self.config.get('email_to', []),
                'handler': self._send_email_notification,
            }
            logger.info("邮件通知渠道已启用")
        else:
            self.channels['email'] = {
                'enabled': False,
                'handler': self._send_email_notification,
            }

        # Webhook渠道（默认禁用）
        if self.config.get('webhook_enabled', False):
            self.channels['webhook'] = {
                'enabled': True,
                'url': self.config.get('webhook_url', ''),
                'handler': self._send_webhook_notification,
            }
            logger.info(f"Webhook通知渠道已启用: {self.config.get('webhook_url', '')}")
        else:
            self.channels['webhook'] = {
                'enabled': False,
                'handler': self._send_webhook_notification,
            }

    async def send_notification(
        self,
        notification: Dict[str, Any]
    ) -> bool:
        """发送通知

        Args:
            notification: 通知字典

        Returns:
            是否成功
        """
        notification_id = notification.get('id', str(uuid.uuid4()))

        # 检查限流
        if self._is_rate_limited(notification):
            logger.debug(f"通知被限流: {notification_id}")
            return False

        # 发送到所有启用的渠道
        success = False
        results = {}

        for channel_name, channel in self.channels.items():
            if channel['enabled']:
                try:
                    await channel['handler'](notification)
                    results[channel_name] = 'success'
                    success = True
                    logger.info(f"通知已发送到 {channel_name}: {notification_id}")
                except Exception as e:
                    results[channel_name] = f'error: {str(e)}'
                    logger.error(f"发送通知到 {channel_name} 失败: {e}")

        # 记录历史
        self.notification_history.append({
            'id': notification_id,
            **notification,
            'channels': results,
            'sent_at': datetime.now().isoformat(),
        })

        # 限制历史长度
        max_history = self.config.get('max_notification_history', 1000)
        if len(self.notification_history) > max_history:
            self.notification_history = self.notification_history[-max_history:]

        return success

    async def _send_console_notification(self, notification: Dict[str, Any]):
        """发送控制台通知

        Args:
            notification: 通知字典
        """
        severity = notification.get('severity', 'INFO')
        message = notification.get('message', '')
        title = notification.get('title', 'NOTIFICATION')

        # 格式化消息
        formatted_message = f"[{title}] {message}"

        # 根据严重级别选择日志级别
        if severity == 'CRITICAL':
            logger.critical(formatted_message)
        elif severity == 'ERROR':
            logger.error(formatted_message)
        elif severity == 'WARNING':
            logger.warning(formatted_message)
        else:
            logger.info(formatted_message)

    async def _send_file_notification(self, notification: Dict[str, Any]):
        """发送文件通知

        Args:
            notification: 通知字典
        """
        file_path = self.channels['file']['path']
        path = Path(file_path)

        # 确保目录存在
        path.parent.mkdir(parents=True, exist_ok=True)

        # 写入文件
        with open(path, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().isoformat()
            severity = notification.get('severity', 'INFO')
            message = notification.get('message', '')
            title = notification.get('title', 'NOTIFICATION')

            log_entry = f"[{timestamp}] [{severity}] [{title}] {message}\n"
            f.write(log_entry)

        logger.debug(f"通知已写入文件: {file_path}")

    async def _send_email_notification(self, notification: Dict[str, Any]):
        """发送邮件通知

        Args:
            notification: 通知字典

        Raises:
            NotImplementedError: 邮件发送功能暂未实现
        """
        # TODO: 实现邮件发送
        # 这里可以使用 smtplib 或 aiosmtplib
        raise NotImplementedError("邮件通知功能暂未实现")

    async def _send_webhook_notification(self, notification: Dict[str, Any]):
        """发送Webhook通知

        Args:
            notification: 通知字典

        Raises:
            NotImplementedError: Webhook功能暂未实现
        """
        # TODO: 实现Webhook发送
        # 这里可以使用 aiohttp 或 requests
        raise NotImplementedError("Webhook通知功能暂未实现")

    def _is_rate_limited(self, notification: Dict[str, Any]) -> bool:
        """检查是否限流

        Args:
            notification: 通知字典

        Returns:
            是否限流
        """
        # 获取限流配置
        rate_limit_interval = self.config.get('rate_limit_interval', 60)  # 秒

        # 生成限流键
        notification_type = notification.get('type', 'default')
        notification_title = notification.get('title', '')
        limit_key = f"{notification_type}:{notification_title}"

        # 检查限流
        if limit_key in self.rate_limits:
            last_sent = self.rate_limits[limit_key]
            if time.time() - last_sent < rate_limit_interval:
                return True

        # 更新最后发送时间
        self.rate_limits[limit_key] = time.time()

        return False

    async def send_alert(self, alert: Dict[str, Any]) -> bool:
        """发送告警通知

        Args:
            alert: 告警字典

        Returns:
            是否成功
        """
        notification = {
            'type': 'alert',
            'title': alert.get('name', 'ALERT'),
            'severity': alert.get('severity', 'INFO'),
            'message': alert.get('message', ''),
            'details': alert,
            'timestamp': datetime.now().isoformat(),
        }

        return await self.send_notification(notification)

    async def send_info(self, title: str, message: str) -> bool:
        """发送信息通知

        Args:
            title: 标题
            message: 消息内容

        Returns:
            是否成功
        """
        notification = {
            'type': 'info',
            'title': title,
            'severity': 'INFO',
            'message': message,
        }

        return await self.send_notification(notification)

    async def send_warning(self, title: str, message: str) -> bool:
        """发送警告通知

        Args:
            title: 标题
            message: 消息内容

        Returns:
            是否成功
        """
        notification = {
            'type': 'warning',
            'title': title,
            'severity': 'WARNING',
            'message': message,
        }

        return await self.send_notification(notification)

    async def send_error(self, title: str, message: str) -> bool:
        """发送错误通知

        Args:
            title: 标题
            message: 消息内容

        Returns:
            是否成功
        """
        notification = {
            'type': 'error',
            'title': title,
            'severity': 'ERROR',
            'message': message,
        }

        return await self.send_notification(notification)

    async def send_critical(self, title: str, message: str) -> bool:
        """发送严重错误通知

        Args:
            title: 标题
            message: 消息内容

        Returns:
            是否成功
        """
        notification = {
            'type': 'critical',
            'title': title,
            'severity': 'CRITICAL',
            'message': message,
        }

        return await self.send_notification(notification)

    def get_notification_history(
        self,
        limit: int = 100,
        severity: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取通知历史

        Args:
            limit: 返回数量限制
            severity: 严重级别过滤
            start_time: 开始时间（ISO格式）
            end_time: 结束时间（ISO格式）

        Returns:
            通知历史列表
        """
        history = self.notification_history.copy()

        # 过滤严重级别
        if severity:
            history = [n for n in history if n.get('severity') == severity]

        # 时间过滤
        if start_time:
            start_dt = datetime.fromisoformat(start_time)
            history = [n for n in history if datetime.fromisoformat(n['sent_at']) >= start_dt]

        if end_time:
            end_dt = datetime.fromisoformat(end_time)
            history = [n for n in history if datetime.fromisoformat(n['sent_at']) <= end_dt]

        # 限制数量并倒序
        history.reverse()
        return history[:limit]

    def get_notification_statistics(
        self,
        hours: int = 24
    ) -> Dict[str, Any]:
        """获取通知统计

        Args:
            hours: 统计时间范围（小时）

        Returns:
            统计信息字典
        """
        from datetime import timedelta

        cutoff_time = datetime.now() - timedelta(hours=hours)

        # 过滤时间范围内的通知
        recent_notifications = [
            n for n in self.notification_history
            if datetime.fromisoformat(n['sent_at']) >= cutoff_time
        ]

        # 统计信息
        severity_counts = {
            'INFO': 0,
            'WARNING': 0,
            'ERROR': 0,
            'CRITICAL': 0,
        }

        type_counts = {}

        channel_success_counts = {}

        for notification in recent_notifications:
            # 严重级别统计
            severity = notification.get('severity', 'INFO')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

            # 类型统计
            notif_type = notification.get('type', 'unknown')
            type_counts[notif_type] = type_counts.get(notif_type, 0) + 1

            # 渠道成功统计
            channels = notification.get('channels', {})
            for channel_name, result in channels.items():
                if channel_name not in channel_success_counts:
                    channel_success_counts[channel_name] = {'success': 0, 'error': 0}

                if result == 'success':
                    channel_success_counts[channel_name]['success'] += 1
                else:
                    channel_success_counts[channel_name]['error'] += 1

        return {
            'time_range_hours': hours,
            'total_notifications': len(recent_notifications),
            'severity_breakdown': severity_counts,
            'type_breakdown': type_counts,
            'channel_success_rates': {
                channel: {
                    'total': stats['success'] + stats['error'],
                    'success_rate': (
                        stats['success'] / (stats['success'] + stats['error']) * 100
                        if (stats['success'] + stats['error']) > 0
                        else 0
                    )
                }
                for channel, stats in channel_success_counts.items()
            },
        }

    def clear_notification_history(self, before_time: Optional[str] = None):
        """清除通知历史

        Args:
            before_time: 清除此时间之前的记录（None表示清除全部）
        """
        if before_time:
            before_dt = datetime.fromisoformat(before_time)
            self.notification_history = [
                n for n in self.notification_history
                if datetime.fromisoformat(n['sent_at']) >= before_dt
            ]
            logger.info(f"已清除 {before_time} 之前的通知历史")
        else:
            self.notification_history.clear()
            logger.info("已清除所有通知历史")

    def clear_rate_limits(self):
        """清除所有限流"""
        self.rate_limits.clear()
        logger.info("已清除所有通知限流")

    def enable_channel(self, channel_name: str) -> bool:
        """启用通知渠道

        Args:
            channel_name: 渠道名称

        Returns:
            是否成功
        """
        if channel_name in self.channels:
            self.channels[channel_name]['enabled'] = True
            logger.info(f"启用通知渠道: {channel_name}")
            return True
        return False

    def disable_channel(self, channel_name: str) -> bool:
        """禁用通知渠道

        Args:
            channel_name: 渠道名称

        Returns:
            是否成功
        """
        if channel_name in self.channels:
            self.channels[channel_name]['enabled'] = False
            logger.info(f"禁用通知渠道: {channel_name}")
            return True
        return False

    def get_channel_status(self) -> Dict[str, Dict[str, Any]]:
        """获取渠道状态

        Returns:
            渠道状态字典
        """
        return {
            name: {
                'enabled': channel['enabled'],
                'type': name,
            }
            for name, channel in self.channels.items()
        }

    def __repr__(self) -> str:
        """字符串表示

        Returns:
            字符串表示
        """
        enabled_count = sum(1 for c in self.channels.values() if c['enabled'])
        return f"NotificationService(channels={len(self.channels)}, enabled={enabled_count}, history={len(self.notification_history)})"
