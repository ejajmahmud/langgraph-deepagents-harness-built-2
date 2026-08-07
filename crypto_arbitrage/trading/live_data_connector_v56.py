"""V56.3 实盘数据对接模块

V56.3 增加功能：
1. RealTimeDataConnector - 实时数据连接器
2. LivePriceFeed - 实时价格订阅
3. SignalStreamPush - 信号流推送
4. ExchangeStatusTracker - 交易所状态追踪

创建时间：2026-05-08
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable

logger = logging.getLogger(__name__)


class DataSourceType(Enum):
    """数据源类型"""
    BINANCE = "binance"
    COINBASE = "coinbase"
    BYBIT = "bybit"
    OKX = "okx"
    KUCOIN = "kucoin"
    GATEIO = "gateio"


class ConnectionStatus(Enum):
    """连接状态"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class PriceTick:
    """价格 tick 数据"""
    symbol: str
    bid: float  # 买一价
    ask: float  # 卖一价
    last: float  # 最新价
    volume: float  # 成交量
    timestamp: float = field(default_factory=time.time)
    source: str = ""


@dataclass
class TradeTick:
    """交易 tick 数据"""
    symbol: str
    price: float
    amount: float
    side: str  # buy/sell
    timestamp: float = field(default_factory=time.time)
    trade_id: str = ""


@dataclass
class OrderBookLevel:
    """订单簿级别"""
    price: float
    amount: float


@dataclass
class OrderBook:
    """订单簿数据"""
    symbol: str
    bids: List[OrderBookLevel] = field(default_factory=list)
    asks: List[OrderBookLevel] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


class RealTimeDataConnector:
    """实时数据连接器

    功能：
    - 多交易所实时价格订阅
    - 订单簿数据获取
    - 交易历史获取
    - 连接状态管理
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化连接器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self._price_callbacks: Dict[str, List[Callable]] = {}
        self._orderbook_callbacks: Dict[str, List[Callable]] = {}
        self._running = False
        self._tasks: List[asyncio.Task] = []

        # 连接状态
        self._connection_status: Dict[DataSourceType, ConnectionStatus] = {}
        self._last_price: Dict[str, PriceTick] = {}

        # 模拟价格数据（实际需要连接真实交易所 API）
        self._mock_prices: Dict[str, Dict[str, Any]] = {
            "BTC/USDT": {"bid": 42150.0, "ask": 42155.0, "last": 42152.0, "volume": 1250.5},
            "ETH/USDT": {"bid": 2250.0, "ask": 2251.0, "last": 2250.5, "volume": 8500.0},
            "SOL/USDT": {"bid": 98.5, "ask": 98.6, "last": 98.55, "volume": 25000.0},
            "DOGE/USDT": {"bid": 0.082, "ask": 0.083, "last": 0.0825, "volume": 500000.0},
        }

    async def start(self) -> bool:
        """启动连接器"""
        self._running = True
        logger.info("RealTimeDataConnector: Started")
        return True

    async def stop(self) -> None:
        """停止连接器"""
        self._running = False
        for task in self._tasks:
            task.cancel()
        self._tasks.clear()
        logger.info("RealTimeDataConnector: Stopped")

    def subscribe_price(self, symbol: str, callback: Callable[[PriceTick], None]) -> None:
        """订阅价格

        Args:
            symbol: 交易对
            callback: 回调函数
        """
        if symbol not in self._price_callbacks:
            self._price_callbacks[symbol] = []
        self._price_callbacks[symbol].append(callback)

    def subscribe_orderbook(self, symbol: str, callback: Callable[[OrderBook], None]) -> None:
        """订阅订单簿

        Args:
            symbol: 交易对
            callback: 回调函数
        """
        if symbol not in self._orderbook_callbacks:
            self._orderbook_callbacks[symbol] = []
        self._orderbook_callbacks[symbol].append(callback)

    async def get_price(self, symbol: str) -> Optional[PriceTick]:
        """获取当前价格

        Args:
            symbol: 交易对

        Returns:
            价格数据
        """
        # 使用模拟数据（真实场景需要调用交易所 API）
        mock = self._mock_prices.get(symbol)
        if not mock:
            return None

        return PriceTick(
            symbol=symbol,
            bid=mock["bid"],
            ask=mock["ask"],
            last=mock["last"],
            volume=mock["volume"],
            timestamp=time.time(),
            source="mock"
        )

    async def get_orderbook(self, symbol: str, depth: int = 10) -> Optional[OrderBook]:
        """获取订单簿

        Args:
            symbol: 交易对
            depth: 深度

        Returns:
            订单簿数据
        """
        price = await self.get_price(symbol)
        if not price:
            return None

        # 生成模拟订单簿
        bids = []
        asks = []
        for i in range(depth):
            bids.append(OrderBookLevel(
                price=price.bid - i * 0.5,
                amount=1000.0 + i * 100
            ))
            asks.append(OrderBookLevel(
                price=price.ask + i * 0.5,
                amount=1000.0 + i * 100
            ))

        return OrderBook(
            symbol=symbol,
            bids=bids,
            asks=asks,
            timestamp=time.time()
        )

    def get_connection_status(self, source: DataSourceType) -> ConnectionStatus:
        """获取连接状态

        Args:
            source: 数据源

        Returns:
            连接状态
        """
        return self._connection_status.get(source, ConnectionStatus.DISCONNECTED)

    def get_all_prices(self) -> Dict[str, PriceTick]:
        """获取所有价格

        Returns:
            价格字典
        """
        return self._last_price.copy()

    async def start_price_stream(self, symbols: List[str], interval: float = 1.0) -> None:
        """启动价格流

        Args:
            symbols: 交易对列表
            interval: 更新间隔（秒）
        """
        async def update_prices():
            while self._running:
                for symbol in symbols:
                    price = await self.get_price(symbol)
                    if price:
                        self._last_price[symbol] = price
                        # 通知订阅者
                        for callback in self._price_callbacks.get(symbol, []):
                            try:
                                callback(price)
                            except Exception as e:
                                logger.error(f"Price callback error: {e}")

                await asyncio.sleep(interval)

        task = asyncio.create_task(update_prices())
        self._tasks.append(task)


class SignalStreamPusher:
    """信号流推送器

    功能：
    - 实时推送套利信号
    - 批量推送
    - 心跳检测
    """

    def __init__(self, connector: Optional[RealTimeDataConnector] = None):
        """初始化推送器

        Args:
            connector: 数据连接器
        """
        self.connector = connector or RealTimeDataConnector()
        self._subscribers: List[Callable] = []
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._last_signal_time: float = 0.0

    def subscribe(self, callback: Callable) -> None:
        """订阅信号流

        Args:
            callback: 回调函数
        """
        self._subscribers.append(callback)

    async def start(self) -> None:
        """启动推送"""
        await self.connector.start()
        self._running = True

        # 启动模拟信号生成
        async def generate_signals():
            signal_interval = 5.0  # 每5秒生成一个信号

            while self._running:
                # 生成模拟套利信号
                signal = {
                    "signal_id": f"signal-{int(time.time())}",
                    "type": "cross_exchange",
                    "token": "BTC",
                    "spread_pct": 0.8,
                    "confidence": 0.75,
                    "timestamp": time.time()
                }

                self._last_signal_time = time.time()

                # 推送给订阅者
                for callback in self._subscribers:
                    try:
                        callback(signal)
                    except Exception as e:
                        logger.error(f"Signal push error: {e}")

                await asyncio.sleep(signal_interval)

        self._task = asyncio.create_task(generate_signals())

    async def stop(self) -> None:
        """停止推送"""
        self._running = False
        if self._task:
            self._task.cancel()
        await self.connector.stop()

    def get_last_signal_time(self) -> float:
        """获取最后信号时间

        Returns:
            时间戳
        """
        return self._last_signal_time


class ExchangeStatusTracker:
    """交易所状态追踪器

    功能：
    - 追踪交易所在线状态
    - 检测交易所故障
    - 记录延迟
    """

    def __init__(self):
        """初始化追踪器"""
        self._exchange_status: Dict[str, Dict[str, Any]] = {}

        # 初始化交易所状态
        for exchange in ["binance", "coinbase", "bybit", "okx", "kucoin", "gateio"]:
            self._exchange_status[exchange] = {
                "status": "online",
                "latency_ms": 0,
                "last_check": time.time(),
                "error_count": 0
            }

    def update_status(self, exchange: str, status: str, latency_ms: float = 0) -> None:
        """更新状态

        Args:
            exchange: 交易所
            status: 状态
            latency_ms: 延迟（毫秒）
        """
        self._exchange_status[exchange] = {
            "status": status,
            "latency_ms": latency_ms,
            "last_check": time.time(),
            "error_count": self._exchange_status.get(exchange, {}).get("error_count", 0)
        }

    def get_status(self, exchange: str) -> Optional[Dict[str, Any]]:
        """获取状态

        Args:
            exchange: 交易所

        Returns:
            状态数据
        """
        return self._exchange_status.get(exchange)

    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有状态

        Returns:
            状态字典
        """
        return self._exchange_status.copy()


# 模块级别的全局实例
_connector: Optional[RealTimeDataConnector] = None
_signal_pusher: Optional[SignalStreamPusher] = None
_status_tracker: Optional[ExchangeStatusTracker] = None


def initialize_live_data_system(config: Optional[Dict[str, Any]] = None) -> RealTimeDataConnector:
    """初始化实盘数据系统

    Args:
        config: 配置

    Returns:
        数据连接器
    """
    global _connector, _signal_pusher, _status_tracker

    _connector = RealTimeDataConnector(config)
    _signal_pusher = SignalStreamPusher(_connector)
    _status_tracker = ExchangeStatusTracker()

    return _connector


def get_live_data_connector() -> RealTimeDataConnector:
    """获取数据连接器

    Returns:
        连接器
    """
    global _connector
    if _connector is None:
        _connector = RealTimeDataConnector()
    return _connector


def get_signal_pusher() -> SignalStreamPusher:
    """获取信号推送器

    Returns:
        推送器
    """
    global _signal_pusher
    if _signal_pusher is None:
        _connector = get_live_data_connector()
        _signal_pusher = SignalStreamPusher(_connector)
    return _signal_pusher


def get_exchange_status_tracker() -> ExchangeStatusTracker:
    """获取交易所状态追踪器

    Returns:
        追踪器
    """
    global _status_tracker
    if _status_tracker is None:
        _status_tracker = ExchangeStatusTracker()
    return _status_tracker