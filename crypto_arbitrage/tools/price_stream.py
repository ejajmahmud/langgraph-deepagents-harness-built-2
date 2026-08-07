"""WebSocket 实时价格流管理器 V1.6.0

从交易所 WebSocket 接收实时价格数据，替代轮询模式。
支持:
- ccxt WebSocket 集成
- 多交易所并发连接
- 本地价格缓存 (用于策略快速查询)
- 价格变动回调
- 连接自动重连
- 降级到 REST 轮询 (当 WebSocket 不可用时)
"""

import asyncio
import logging
import time
from collections import defaultdict
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set

import ccxt.async_support as ccxt

logger = logging.getLogger(__name__)


class PriceTick:
    """价格数据点"""

    __slots__ = ('symbol', 'exchange', 'bid', 'ask', 'last', 'timestamp', 'volume')

    def __init__(
        self,
        symbol: str,
        exchange: str,
        bid: Optional[float],
        ask: Optional[float],
        last: Optional[float],
        timestamp: float,
        volume: Optional[float] = None,
    ) -> None:
        self.symbol = symbol
        self.exchange = exchange
        self.bid = bid
        self.ask = ask
        self.last = last
        self.timestamp = timestamp
        self.volume = volume

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'exchange': self.exchange,
            'bid': self.bid,
            'ask': self.ask,
            'last': self.last,
            'timestamp': self.timestamp,
            'volume': self.volume,
        }

    def __repr__(self) -> str:
        return (
            f"PriceTick({self.symbol}@{self.exchange} "
            f"bid={self.bid} ask={self.ask} last={self.last})"
        )


class PriceCache:
    """线程安全的本地价格缓存"""

    def __init__(self, max_history: int = 1000) -> None:
        """初始化价格缓存

        Args:
            max_history: 每个 symbol@exchange 最多保存的历史数据点数
        """
        self._latest: Dict[str, PriceTick] = {}
        self._history: Dict[str, List[PriceTick]] = defaultdict(list)
        self._max_history = max_history
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def update(self, tick: PriceTick) -> None:
        """更新价格缓存

        Args:
            tick: 价格数据点
        """
        key = f"{tick.symbol}@{tick.exchange}"
        async with self._lock:
            self._latest[key] = tick
            history = self._history[key]
            history.append(tick)
            if len(history) > self._max_history:
                self._history[key] = history[-self._max_history:]

    def get_latest(self, symbol: str, exchange: str) -> Optional[PriceTick]:
        """获取最新价格

        Args:
            symbol: 交易对
            exchange: 交易所名称

        Returns:
            最新价格数据点，如不存在返回 None
        """
        return self._latest.get(f"{symbol}@{exchange}")

    def get_all_latest(self, symbol: str) -> Dict[str, PriceTick]:
        """获取某交易对在所有交易所的最新价格

        Args:
            symbol: 交易对

        Returns:
            {exchange: PriceTick} 字典
        """
        result = {}
        for key, tick in self._latest.items():
            if tick.symbol == symbol:
                result[tick.exchange] = tick
        return result

    def get_history(
        self, symbol: str, exchange: str, limit: int = 100
    ) -> List[PriceTick]:
        """获取价格历史

        Args:
            symbol: 交易对
            exchange: 交易所名称
            limit: 最多返回条数

        Returns:
            价格历史列表
        """
        key = f"{symbol}@{exchange}"
        history = self._history.get(key, [])
        return history[-limit:]

    async def subscribe(
        self,
        symbol: str,
        exchange: str,
        callback: Callable[[PriceTick], Coroutine],
    ) -> None:
        """订阅价格变动

        Args:
            symbol: 交易对
            exchange: 交易所名称
            callback: 回调协程函数
        """
        key = f"{symbol}@{exchange}"
        self._subscribers[key].append(callback)

    async def notify_subscribers(self, tick: PriceTick) -> None:
        """通知订阅者

        Args:
            tick: 价格数据点
        """
        key = f"{tick.symbol}@{tick.exchange}"
        callbacks = self._subscribers.get(key, [])
        for cb in callbacks:
            try:
                await cb(tick)
            except Exception as e:
                logger.error(f"价格回调执行失败: {e}")

    def clear(self) -> None:
        """清空缓存"""
        self._latest.clear()
        self._history.clear()


class PriceStreamManager:
    """WebSocket 实时价格流管理器

    用法:
        manager = PriceStreamManager(exchange_config)
        await manager.start()
        tick = manager.cache.get_latest('BTC/USDT', 'binance')
        await manager.stop()
    """

    def __init__(
        self,
        exchange_config: Dict[str, Any],
        symbols: Optional[List[str]] = None,
        poll_interval: float = 5.0,
    ) -> None:
        """初始化价格流管理器

        Args:
            exchange_config: 交易所配置（同 ExchangeManager）
            symbols: 要监控的交易对列表
            poll_interval: REST 轮询降级间隔（秒）
        """
        self.exchange_config = exchange_config
        self.symbols = symbols or ['BTC/USDT', 'ETH/USDT']
        self.poll_interval = poll_interval

        self.cache = PriceCache()
        self._running = False
        self._ws_tasks: List[asyncio.Task] = []
        self._poll_task: Optional[asyncio.Task] = None
        self._exchanges: Dict[str, ccxt.Exchange] = {}

        # 连接状态
        self._ws_connected: Set[str] = set()
        self._connection_errors: Dict[str, int] = defaultdict(int)
        self._max_reconnect_delay = 60.0

        # 统计
        self._total_ticks_received = 0
        self._last_tick_time: float = 0.0

        logger.info(f"PriceStreamManager 初始化: {len(self.symbols)} 个交易对")

    async def start(self) -> None:
        """启动价格流（WebSocket + REST 降级）"""
        if self._running:
            return

        self._running = True
        logger.info("PriceStreamManager 启动中...")

        # 尝试为每个交易所建立 WebSocket 连接
        for exchange_name, ex_config in self.exchange_config.items():
            if not ex_config.get('enabled', True):
                continue
            task = asyncio.create_task(
                self._run_ws_connection(exchange_name, ex_config),
                name=f"ws-{exchange_name}",
            )
            self._ws_tasks.append(task)

        # 启动 REST 轮询作为补充/降级
        self._poll_task = asyncio.create_task(
            self._poll_loop(), name="price-poll"
        )

        logger.info(
            f"PriceStreamManager 已启动: "
            f"{len(self._ws_tasks)} 个 WS 任务, 1 个轮询任务"
        )

    async def stop(self) -> None:
        """停止价格流"""
        self._running = False

        for task in self._ws_tasks:
            task.cancel()
        for task in self._ws_tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._ws_tasks.clear()

        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
            self._poll_task = None

        # 关闭交易所连接
        for ex_name, exchange in self._exchanges.items():
            try:
                await exchange.close()
            except Exception as e:
                logger.error(f"关闭 {ex_name} 连接失败: {e}")
        self._exchanges.clear()

        logger.info("PriceStreamManager 已停止")

    async def _run_ws_connection(
        self, exchange_name: str, ex_config: Dict[str, Any]
    ) -> None:
        """为单个交易所维护 WebSocket 连接（带重连）"""
        reconnect_delay = 1.0

        while self._running:
            try:
                # 创建交易所实例
                exchange_class = getattr(ccxt, exchange_name, None)
                if not exchange_class:
                    logger.warning(f"不支持交易所: {exchange_name}")
                    break

                exchange = exchange_class({
                    'apiKey': ex_config.get('api_key'),
                    'secret': ex_config.get('secret'),
                    'enableRateLimit': True,
                    'options': ex_config.get('options', {}),
                })
                self._exchanges[exchange_name] = exchange

                # 检查是否支持 watch_ticker
                if not hasattr(exchange, 'watch_ticker'):
                    logger.info(
                        f"{exchange_name} 不支持 WebSocket, 将使用 REST 轮询"
                    )
                    break

                self._ws_connected.add(exchange_name)
                logger.info(f"{exchange_name} WebSocket 连接成功")

                # 订阅所有交易对
                while self._running:
                    for symbol in self.symbols:
                        try:
                            ticker = await asyncio.wait_for(
                                exchange.watch_ticker(symbol),
                                timeout=30,
                            )
                            tick = PriceTick(
                                symbol=symbol,
                                exchange=exchange_name,
                                bid=ticker.get('bid'),
                                ask=ticker.get('ask'),
                                last=ticker.get('last'),
                                timestamp=ticker.get('timestamp', time.time() * 1000) / 1000,
                                volume=ticker.get('baseVolume'),
                            )
                            await self.cache.update(tick)
                            await self.cache.notify_subscribers(tick)
                            self._total_ticks_received += 1
                            self._last_tick_time = time.time()

                        except asyncio.TimeoutError:
                            logger.debug(f"{exchange_name} {symbol} WS 超时，继续")
                        except Exception as e:
                            logger.debug(f"{exchange_name} {symbol} WS 错误: {e}")

                    self._connection_errors[exchange_name] = 0

            except Exception as e:
                self._ws_connected.discard(exchange_name)
                self._connection_errors[exchange_name] += 1
                logger.warning(
                    f"{exchange_name} WebSocket 连接失败 "
                    f"(第{self._connection_errors[exchange_name]}次): {e}"
                )

            if not self._running:
                break

            # 指数退避重连
            await asyncio.sleep(reconnect_delay)
            reconnect_delay = min(reconnect_delay * 2, self._max_reconnect_delay)

    async def _poll_loop(self) -> None:
        """REST 轮询循环 - 作为 WebSocket 的补充或降级方案"""
        poll_interval = self.poll_interval

        while self._running:
            try:
                for exchange_name, ex_config in self.exchange_config.items():
                    if not ex_config.get('enabled', True):
                        continue
                    # 如果已有 WS 连接，降低轮询频率
                    if exchange_name in self._ws_connected:
                        continue

                    exchange = self._exchanges.get(exchange_name)
                    if not exchange:
                        continue

                    for symbol in self.symbols:
                        try:
                            ticker = await exchange.fetch_ticker(symbol)
                            tick = PriceTick(
                                symbol=symbol,
                                exchange=exchange_name,
                                bid=ticker.get('bid'),
                                ask=ticker.get('ask'),
                                last=ticker.get('last'),
                                timestamp=ticker.get('timestamp', time.time() * 1000) / 1000,
                                volume=ticker.get('baseVolume'),
                            )
                            await self.cache.update(tick)
                            await self.cache.notify_subscribers(tick)
                            self._total_ticks_received += 1
                            self._last_tick_time = time.time()
                        except Exception as e:
                            logger.debug(f"轮询 {exchange_name} {symbol} 失败: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"轮询循环异常: {e}")

            await asyncio.sleep(poll_interval)

    def get_price(
        self, symbol: str, exchange: str, price_type: str = 'last'
    ) -> Optional[float]:
        """快速获取价格（同步方法）

        Args:
            symbol: 交易对
            exchange: 交易所名称
            price_type: 价格类型 ('bid', 'ask', 'last')

        Returns:
            价格或 None
        """
        tick = self.cache.get_latest(symbol, exchange)
        if not tick:
            return None

        if price_type == 'bid':
            return tick.bid
        elif price_type == 'ask':
            return tick.ask
        return tick.last

    def get_spread(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取跨交易所价差

        Args:
            symbol: 交易对

        Returns:
            {
                'best_bid_exchange': str,
                'best_bid': float,
                'best_ask_exchange': str,
                'best_ask': float,
                'spread': float,
                'spread_rate': float,
            }
        """
        all_prices = self.cache.get_all_latest(symbol)
        if not all_prices:
            return None

        best_bid_exchange = None
        best_bid = 0.0
        best_ask_exchange = None
        best_ask = float('inf')

        for ex_name, tick in all_prices.items():
            if tick.bid and tick.bid > best_bid:
                best_bid = tick.bid
                best_bid_exchange = ex_name
            if tick.ask and tick.ask < best_ask:
                best_ask = tick.ask
                best_ask_exchange = ex_name

        if not best_bid or best_ask == float('inf'):
            return None

        spread = best_bid - best_ask
        spread_rate = (spread / best_ask) * 100 if best_ask > 0 else 0

        return {
            'symbol': symbol,
            'best_bid_exchange': best_bid_exchange,
            'best_bid': best_bid,
            'best_ask_exchange': best_ask_exchange,
            'best_ask': best_ask,
            'spread': spread,
            'spread_rate': spread_rate,
            'timestamp': time.time(),
        }

    def get_status(self) -> Dict[str, Any]:
        """获取价格流状态"""
        return {
            'running': self._running,
            'ws_connected': list(self._ws_connected),
            'polling_exchanges': [
                name for name in self.exchange_config
                if name not in self._ws_connected
            ],
            'symbols_count': len(self.symbols),
            'total_ticks_received': self._total_ticks_received,
            'last_tick_time': self._last_tick_time,
            'connection_errors': dict(self._connection_errors),
        }


# 全局实例
_price_stream: Optional[PriceStreamManager] = None


def initialize_price_stream(
    exchange_config: Dict[str, Any],
    symbols: Optional[List[str]] = None,
) -> PriceStreamManager:
    """初始化全局价格流管理器

    Args:
        exchange_config: 交易所配置
        symbols: 监控的交易对列表

    Returns:
        PriceStreamManager 实例
    """
    global _price_stream
    _price_stream = PriceStreamManager(exchange_config, symbols)
    return _price_stream


def get_price_stream() -> Optional[PriceStreamManager]:
    """获取全局价格流管理器

    Returns:
        PriceStreamManager 实例或 None
    """
    return _price_stream
