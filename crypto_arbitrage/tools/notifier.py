"""通知系统 - 多渠道告警和交易通知

支持多种通知渠道:
- Console: 控制台输出
- File: 文件日志
- Memo0: 知识库记录
- Email: 邮件通知
- Telegram: Telegram 机器人
- Webhook: 通用 Webhook
"""

import asyncio
import json
import logging
import smtplib
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


class NotificationLevel:
    """通知级别"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Notifier:
    """多渠道通知管理器"""

    def __init__(self, config: Dict[str, Any]):
        """初始化通知管理器

        Args:
            config: 通知配置，包含各渠道配置
        """
        self.config = config
        self.enabled = config.get('enabled', True)
        self.channels: List[Dict[str, Any]] = []
        self._notification_history: List[Dict] = []
        self._rate_limit: Dict[str, float] = {}  # 频率限制
        self._rate_limit_interval = config.get('rate_limit_interval', 60)  # 秒

        # 初始化渠道
        self._init_channels(config.get('channels', []))

        logger.info(f"通知系统初始化完成: {len(self.channels)} 个渠道")

    def _init_channels(self, channels_config: List[Dict]) -> None:
        """初始化通知渠道"""
        for ch in channels_config:
            if not ch.get('enabled', True):
                continue

            ch_type = ch.get('type', '')
            if ch_type in ('console', 'file', 'memo0'):
                # 内置渠道，始终可用
                self.channels.append(ch)
            elif ch_type == 'email':
                if ch.get('smtp_host') and ch.get('username'):
                    self.channels.append(ch)
                else:
                    logger.warning("邮件渠道配置不完整")
            elif ch_type == 'telegram':
                if ch.get('bot_token') and ch.get('chat_id'):
                    self.channels.append(ch)
                else:
                    logger.warning("Telegram 渠道配置不完整")
            elif ch_type == 'webhook':
                if ch.get('url'):
                    self.channels.append(ch)
                else:
                    logger.warning("Webhook 渠道配置不完整")

    def _check_rate_limit(self, channel_type: str, level: str) -> bool:
        """检查频率限制

        Args:
            channel_type: 渠道类型
            level: 通知级别

        Returns:
            是否允许发送
        """
        # CRITICAL 级别不受限制
        if level == NotificationLevel.CRITICAL:
            return True

        # INFO 级别限制更严格
        interval = self._rate_limit_interval
        if level == NotificationLevel.INFO:
            interval *= 5  # INFO 消息间隔更长

        key = f"{channel_type}_{level}"
        last_sent = self._rate_limit.get(key, 0)
        current = time.time()

        if current - last_sent < interval:
            return False

        self._rate_limit[key] = current
        return True

    async def send_alert(
        self,
        level: str,
        title: str,
        message: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """发送告警通知

        Args:
            level: 告警级别
            title: 标题
            message: 消息内容
            metadata: 额外元数据

        Returns:
            是否有渠道发送成功
        """
        if not self.enabled:
            return False

        notification = {
            'level': level,
            'title': title,
            'message': message,
            'metadata': metadata or {},
            'timestamp': datetime.now()
        }

        self._notification_history.append(notification)

        any_success = False
        for channel in self.channels:
            ch_type = channel.get('type')

            if not self._check_rate_limit(ch_type, level):
                continue

            try:
                success = await self._send_to_channel(channel, notification)
                if success:
                    any_success = True
            except Exception as e:
                logger.error(f"发送通知到 {ch_type} 失败: {e}")

        return any_success

    async def _send_to_channel(self, channel: Dict, notification: Dict) -> bool:
        """发送通知到指定渠道

        Args:
            channel: 渠道配置
            notification: 通知内容

        Returns:
            是否成功
        """
        ch_type = channel.get('type')

        if ch_type == 'console':
            return self._send_console(notification)
        elif ch_type == 'file':
            return self._send_file(notification)
        elif ch_type == 'memo0':
            return await self._send_memo0(notification)
        elif ch_type == 'email':
            return await self._send_email(channel, notification)
        elif ch_type == 'telegram':
            return await self._send_telegram(channel, notification)
        elif ch_type == 'webhook':
            return await self._send_webhook(channel, notification)
        else:
            logger.warning(f"未知通知渠道: {ch_type}")
            return False

    def _send_console(self, notification: Dict) -> bool:
        """控制台输出"""
        level = notification['level']
        title = notification['title']
        message = notification['message']
        ts = notification['timestamp'].strftime('%H:%M:%S')

        prefix = {
            NotificationLevel.CRITICAL: "🔴",
            NotificationLevel.ERROR: "🟠",
            NotificationLevel.WARNING: "🟡",
            NotificationLevel.INFO: "🟢"
        }.get(level, "⚪")

        formatted = f"{prefix} [{ts}] [{level}] {title}: {message}"
        print(formatted)
        return True

    def _send_file(self, notification: Dict) -> bool:
        """写入文件"""
        try:
            logs_dir = Path('logs')
            logs_dir.mkdir(exist_ok=True)

            date_str = notification['timestamp'].strftime('%Y%m%d')
            log_file = logs_dir / f"notifications_{date_str}.log"

            line = (
                f"[{notification['timestamp'].isoformat()}] "
                f"[{notification['level']}] {notification['title']}: "
                f"{notification['message']}\n"
            )

            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(line)

            return True
        except Exception as e:
            logger.error(f"写入通知文件失败: {e}")
            return False

    async def _send_memo0(self, notification: Dict) -> bool:
        """记录到 Memo0 知识库"""
        try:
            from storage.mem0_storage import add_trading_knowledge
            content = (
                f"通知 [{notification['level']}]: {notification['title']}\n"
                f"{notification['message']}"
            )
            return add_trading_knowledge('notification', content)
        except Exception:
            return False

    async def _send_email(self, channel: Dict, notification: Dict) -> bool:
        """发送邮件通知"""
        try:
            # 仅 ERROR 和 CRITICAL 发邮件
            if notification['level'] not in (NotificationLevel.ERROR, NotificationLevel.CRITICAL):
                return False

            smtp_host = channel.get('smtp_host')
            smtp_port = channel.get('smtp_port', 587)
            username = channel.get('username')
            password = channel.get('password')
            to_addresses = channel.get('to_addresses', [])

            if not all([smtp_host, username, password, to_addresses]):
                return False

            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[CryptoArbitrage {notification['level']}] {notification['title']}"
            msg['From'] = username
            msg['To'] = ', '.join(to_addresses)

            html = f"""
            <html><body>
            <h2>CryptoArbitrage 告警</h2>
            <table border="1" cellpadding="5">
                <tr><td><b>级别</b></td><td>{notification['level']}</td></tr>
                <tr><td><b>标题</b></td><td>{notification['title']}</td></tr>
                <tr><td><b>消息</b></td><td>{notification['message']}</td></tr>
                <tr><td><b>时间</b></td><td>{notification['timestamp'].isoformat()}</td></tr>
            </table>
            </body></html>
            """
            msg.attach(MIMEText(html, 'html', 'utf-8'))

            # BUG FIX #9: 使用 asyncio.get_running_loop() 替代废弃的 get_event_loop()
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._send_email_sync,
                                       smtp_host, smtp_port, username, password,
                                       to_addresses, msg)

            return True

        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
            return False

    @staticmethod
    def _send_email_sync(smtp_host, smtp_port, username, password, to_addresses, msg):
        """同步发送邮件"""
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(username, password)
            server.sendmail(username, to_addresses, msg.as_string())

    async def _send_telegram(self, channel: Dict, notification: Dict) -> bool:
        """发送 Telegram 通知"""
        try:
            import aiohttp

            bot_token = channel.get('bot_token')
            chat_id = channel.get('chat_id')

            text = (
                f"🔔 <b>CryptoArbitrage [{notification['level']}]</b>\n\n"
                f"📌 {notification['title']}\n"
                f"💬 {notification['message']}\n"
                f"🕐 {notification['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"
            )

            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            params = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': 'HTML'
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    return resp.status == 200

        except ImportError:
            logger.warning("aiohttp 未安装，无法发送 Telegram 通知")
            return False
        except Exception as e:
            logger.error(f"发送 Telegram 通知失败: {e}")
            return False

    async def _send_webhook(self, channel: Dict, notification: Dict) -> bool:
        """发送 Webhook 通知"""
        try:
            import aiohttp

            url = channel.get('url')
            headers = channel.get('headers', {'Content-Type': 'application/json'})

            payload = {
                'level': notification['level'],
                'title': notification['title'],
                'message': notification['message'],
                'timestamp': notification['timestamp'].isoformat(),
                'metadata': notification.get('metadata', {})
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers,
                                        timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    return resp.status == 200

        except ImportError:
            logger.warning("aiohttp 未安装，无法发送 Webhook 通知")
            return False
        except Exception as e:
            logger.error(f"发送 Webhook 通知失败: {e}")
            return False

    def get_notification_history(self, limit: int = 20) -> List[Dict]:
        """获取通知历史

        Args:
            limit: 返回数量

        Returns:
            通知历史列表
        """
        return self._notification_history[-limit:]


# 全局单例
_notifier: Optional[Notifier] = None


def initialize_notifier(config: Dict[str, Any] = None) -> Notifier:
    """初始化通知系统（全局单例）"""
    global _notifier
    if config is None:
        config = {'enabled': False, 'channels': []}
    _notifier = Notifier(config)
    return _notifier


def get_notifier() -> Optional[Notifier]:
    """获取通知系统实例（全局单例）"""
    return _notifier
