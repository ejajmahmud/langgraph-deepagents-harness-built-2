"""实时数据推送系统 V3.3

提供高性能的实时数据推送功能，支持多客户端连接和数据广播。

核心功能：
1. WebSocket 连接管理
2. 实时数据流推送
3. 数据缓存和队列
4. 客户端订阅管理
5. 推送性能优化
"""

import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class DataStream:
    """数据流

    管理单个数据类型的数据流。
    """

    def __init__(
        self,
        name: str,
        max_size: int = 1000,
        retention_time: float = 3600.0
    ):
        """初始化数据流

        Args:
            name: 数据流名称
            max_size: 最大数据量
            retention_time: 数据保留时间（秒）
        """
        self.name = name
        self.max_size = max_size
        self.retention_time = retention_time

        # 数据存储（按时间排序）
        self.data: deque = deque(maxlen=max_size)

        # 订阅者列表
        self.subscribers: Set[str] = set()

        # 统计信息
        self.stats = {
            'total_published': 0,
            'total_subscribers': 0,
            'last_publish': None
        }

        logger.debug(f"DataStream '{name}' initialized")

    def publish(self, data: Dict[str, Any]) -> None:
        """发布数据

        Args:
            data: 数据字典
        """
        timestamp = datetime.now().timestamp()
        data['_timestamp'] = timestamp
        data['_stream'] = self.name

        self.data.append(data)
        self.stats['total_published'] += 1
        self.stats['last_publish'] = timestamp

        # 清理过期数据
        self._cleanup()

        logger.debug(f"Published to stream '{self.name}': {data.get('type', 'unknown')}")

    def subscribe(self, client_id: str) -> None:
        """订阅数据流

        Args:
            client_id: 客户端ID
        """
        self.subscribers.add(client_id)
        self.stats['total_subscribers'] = len(self.subscribers)
        logger.debug(f"Client {client_id} subscribed to stream '{self.name}'")

    def unsubscribe(self, client_id: str) -> None:
        """取消订阅数据流

        Args:
            client_id: 客户端ID
        """
        if client_id in self.subscribers:
            self.subscribers.remove(client_id)
            self.stats['total_subscribers'] = len(self.subscribers)
            logger.debug(f"Client {client_id} unsubscribed from stream '{self.name}'")

    def get_recent_data(self, count: int = 10) -> List[Dict[str, Any]]:
        """获取最近的数据

        Args:
            count: 数据数量

        Returns:
            数据列表
        """
        return list(self.data)[-count:]

    def _cleanup(self) -> None:
        """清理过期数据"""
        current_time = datetime.now().timestamp()
        cutoff_time = current_time - self.retention_time

        # 移除过期数据
        while self.data and self.data[0]['_timestamp'] < cutoff_time:
            self.data.popleft()


class RealtimePushManager:
    """实时推送管理器

    管理所有数据流和 WebSocket 连接。
    """

    def __init__(
        self,
        heartbeat_interval: float = 30.0,
        max_message_size: int = 1024 * 1024,
        compression_threshold: int = 1024
    ):
        """初始化实时推送管理器

        Args:
            heartbeat_interval: 心跳间隔（秒）
            max_message_size: 最大消息大小（字节）
            compression_threshold: 压缩阈值（字节）
        """
        self.heartbeat_interval = heartbeat_interval
        self.max_message_size = max_message_size
        self.compression_threshold = compression_threshold

        # 数据流管理
        self.streams: Dict[str, DataStream] = {}

        # WebSocket 连接管理
        self.connections: Dict[str, Dict[str, Any]] = {}
        self.connections_lock = asyncio.Lock()

        # 统计信息
        self.stats = {
            'total_connections': 0,
            'active_connections': 0,
            'total_messages_sent': 0,
            'total_bytes_sent': 0,
            'start_time': datetime.now().isoformat()
        }

        # 心跳任务
        self.heartbeat_task: Optional[asyncio.Task] = None

        logger.info(
            f"RealtimePushManager initialized: "
            f"heartbeat_interval={heartbeat_interval}, "
            f"max_message_size={max_message_size}, "
            f"compression_threshold={compression_threshold}"
        )

    def create_stream(
        self,
        name: str,
        max_size: int = 1000,
        retention_time: float = 3600.0
    ) -> DataStream:
        """创建数据流

        Args:
            name: 数据流名称
            max_size: 最大数据量
            retention_time: 数据保留时间（秒）

        Returns:
            数据流实例
        """
        if name in self.streams:
            logger.warning(f"Stream '{name}' already exists")
            return self.streams[name]

        stream = DataStream(name, max_size, retention_time)
        self.streams[name] = stream
        logger.info(f"Created data stream: {name}")

        return stream

    def get_stream(self, name: str) -> Optional[DataStream]:
        """获取数据流

        Args:
            name: 数据流名称

        Returns:
            数据流实例或 None
        """
        return self.streams.get(name)

    async def connect_client(
        self,
        client_id: str,
        websocket,
        subscriptions: Optional[List[str]] = None
    ) -> None:
        """连接客户端

        Args:
            client_id: 客户端ID
            websocket: WebSocket 连接
            subscriptions: 订阅的数据流列表
        """
        async with self.connections_lock:
            if client_id in self.connections:
                logger.warning(f"Client {client_id} already connected")
                return

            self.connections[client_id] = {
                'websocket': websocket,
                'subscriptions': set(subscriptions or []),
                'connected_at': datetime.now().isoformat(),
                'last_activity': datetime.now().timestamp(),
                'messages_sent': 0,
                'bytes_sent': 0
            }

            # 订阅指定的数据流
            for stream_name in subscriptions or []:
                if stream_name in self.streams:
                    self.streams[stream_name].subscribe(client_id)

            self.stats['total_connections'] += 1
            self.stats['active_connections'] = len(self.connections)

        logger.info(f"Client {client_id} connected with {len(subscriptions or [])} subscriptions")

    async def disconnect_client(self, client_id: str) -> None:
        """断开客户端连接

        Args:
            client_id: 客户端ID
        """
        async with self.connections_lock:
            if client_id not in self.connections:
                logger.warning(f"Client {client_id} not found")
                return

            # 取消所有订阅
            for stream_name in self.connections[client_id]['subscriptions']:
                if stream_name in self.streams:
                    self.streams[stream_name].unsubscribe(client_id)

            del self.connections[client_id]
            self.stats['active_connections'] = len(self.connections)

        logger.info(f"Client {client_id} disconnected")

    async def send_to_client(
        self,
        client_id: str,
        data: Dict[str, Any]
    ) -> bool:
        """发送数据给指定客户端

        Args:
            client_id: 客户端ID
            data: 数据字典

        Returns:
            是否发送成功
        """
        try:
            async with self.connections_lock:
                if client_id not in self.connections:
                    logger.warning(f"Client {client_id} not found")
                    return False

                connection = self.connections[client_id]
                websocket = connection['websocket']

                # 序列化数据
                message = json.dumps(data, default=str)

                # 检查消息大小
                if len(message.encode('utf-8')) > self.max_message_size:
                    logger.warning(f"Message too large for client {client_id}")
                    return False

                # 发送消息
                await websocket.send_text(message)

                # 更新统计
                connection['messages_sent'] += 1
                connection['bytes_sent'] += len(message.encode('utf-8'))
                connection['last_activity'] = datetime.now().timestamp()

                self.stats['total_messages_sent'] += 1
                self.stats['total_bytes_sent'] += len(message.encode('utf-8'))

                return True

        except Exception as e:
            logger.error(f"Error sending to client {client_id}: {e}")
            return False

    async def broadcast(self, data: Dict[str, Any], stream_name: Optional[str] = None) -> None:
        """广播数据

        Args:
            data: 数据字典
            stream_name: 数据流名称（如果指定，只发送给该流的订阅者）
        """
        # 发布数据到流
        if stream_name and stream_name in self.streams:
            self.streams[stream_name].publish(data)

        # 广播给所有相关客户端
        async with self.connections_lock:
            for client_id, connection in list(self.connections.items()):
                try:
                    # 如果指定了流，只发送给订阅者
                    if stream_name and stream_name not in connection['subscriptions']:
                        continue

                    await connection['websocket'].send_text(
                        json.dumps(data, default=str)
                    )

                except Exception as e:
                    logger.error(f"Error broadcasting to client {client_id}: {e}")
                    # 移除无效连接
                    await self.disconnect_client(client_id)

    async def subscribe_client(
        self,
        client_id: str,
        stream_name: str
    ) -> None:
        """订阅数据流

        Args:
            client_id: 客户端ID
            stream_name: 数据流名称
        """
        if stream_name not in self.streams:
            logger.warning(f"Stream '{stream_name}' not found")
            return

        self.streams[stream_name].subscribe(client_id)

        async with self.connections_lock:
            if client_id in self.connections:
                self.connections[client_id]['subscriptions'].add(stream_name)

        logger.info(f"Client {client_id} subscribed to stream '{stream_name}'")

    async def unsubscribe_client(
        self,
        client_id: str,
        stream_name: str
    ) -> None:
        """取消订阅数据流

        Args:
            client_id: 客户端ID
            stream_name: 数据流名称
        """
        if stream_name not in self.streams:
            return

        self.streams[stream_name].unsubscribe(client_id)

        async with self.connections_lock:
            if client_id in self.connections:
                self.connections[client_id]['subscriptions'].discard(stream_name)

        logger.info(f"Client {client_id} unsubscribed from stream '{stream_name}'")

    async def start_heartbeat(self) -> None:
        """启动心跳检测"""
        if self.heartbeat_task and not self.heartbeat_task.done():
            logger.warning("Heartbeat already running")
            return

        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        logger.info("Heartbeat started")

    async def stop_heartbeat(self) -> None:
        """停止心跳检测"""
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
            logger.info("Heartbeat stopped")

    async def _heartbeat_loop(self) -> None:
        """心跳循环"""
        while True:
            try:
                # 发送心跳消息给所有连接的客户端
                heartbeat_data = {
                    'type': 'heartbeat',
                    'timestamp': datetime.now().isoformat()
                }

                await self.broadcast(heartbeat_data)

                # 检查超时连接
                await self._check_timeout_connections()

                await asyncio.sleep(self.heartbeat_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(1.0)

    async def _check_timeout_connections(self) -> None:
        """检查超时连接"""
        current_time = datetime.now().timestamp()
        timeout_threshold = self.heartbeat_interval * 2

        async with self.connections_lock:
            timeout_clients = []

            for client_id, connection in self.connections.items():
                last_activity = connection.get('last_activity', 0)
                if current_time - last_activity > timeout_threshold:
                    timeout_clients.append(client_id)

            # 断开超时连接
            for client_id in timeout_clients:
                logger.warning(f"Client {client_id} timeout, disconnecting")
                await self.disconnect_client(client_id)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息

        Returns:
            统计信息字典
        """
        stream_stats = {
            name: {
                'subscribers': stream.stats['total_subscribers'],
                'total_published': stream.stats['total_published'],
                'data_size': len(stream.data)
            }
            for name, stream in self.streams.items()
        }

        return {
            **self.stats,
            'stream_stats': stream_stats,
            'active_streams': len(self.streams)
        }

    async def cleanup(self) -> None:
        """清理资源"""
        # 停止心跳
        await self.stop_heartbeat()

        # 断开所有连接
        client_ids = list(self.connections.keys())
        for client_id in client_ids:
            await self.disconnect_client(client_id)

        logger.info("RealtimePushManager cleanup complete")


# 全局实例
_push_manager: Optional[RealtimePushManager] = None


def get_push_manager() -> Optional[RealtimePushManager]:
    """获取全局推送管理器实例

    Returns:
        推送管理器实例
    """
    return _push_manager


def initialize_push_manager(
    config: Optional[Dict[str, Any]] = None
) -> RealtimePushManager:
    """初始化全局推送管理器

    Args:
        config: 配置字典

    Returns:
        推送管理器实例
    """
    global _push_manager

    if _push_manager is None:
        config = config or {}
        _push_manager = RealtimePushManager(
            heartbeat_interval=config.get('heartbeat_interval', 30.0),
            max_message_size=config.get('max_message_size', 1024 * 1024),
            compression_threshold=config.get('compression_threshold', 1024)
        )
        logger.info("Global push manager initialized")

    return _push_manager
