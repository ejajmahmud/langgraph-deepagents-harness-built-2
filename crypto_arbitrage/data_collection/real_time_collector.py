"""实时数据采集器 V15.9 Phase 3

实时采集市场数据,为知识提取引擎提供数据源。

核心功能：
1. 多交易所数据采集 - 支持多个交易所的实时数据
2. 多品种数据采集 - 支持价格、成交量、订单簿等数据
3. 数据预处理 - 数据清洗、标准化、异常检测
4. 数据缓存 - 高效的内存缓存机制
5. 异常处理 - 完善的错误处理和恢复机制

性能目标：
- 数据采集延迟 < 100ms
- 数据处理吞吐量 > 1000条/秒
- 缓存命中率 > 95%
- 系统可用性 > 99.9%

创建时间：2026-05-01 05:06
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
import json
import statistics
import time
from pathlib import Path

logger = logging.getLogger(__name__)


class DataType(Enum):
    """数据类型"""
    PRICE = "price"  # 价格数据
    VOLUME = "volume"  # 成交量数据
    ORDERBOOK = "orderbook"  # 订单簿数据
    TRADE = "trade"  # 交易数据
    FUNDING = "funding"  # 资金费率数据
    POSITION = "position"  # 持仓数据


class Exchange(Enum):
    """交易所"""
    BINANCE = "binance"
    OKEX = "okex"
    HUOBI = "huobi"
    BYBIT = "bybit"
    COINBASE = "coinbase"


@dataclass
class MarketData:
    """市场数据"""
    exchange: Exchange
    symbol: str
    data_type: DataType
    timestamp: float
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "exchange": self.exchange.value,
            "symbol": self.symbol,
            "data_type": self.data_type.value,
            "timestamp": self.timestamp,
            "data": self.data,
            "metadata": self.metadata
        }


@dataclass
class DataQualityMetrics:
    """数据质量指标"""
    total_collected: int = 0
    successful: int = 0
    failed: int = 0
    avg_latency_ms: float = 0.0
    cache_hit_rate: float = 0.0
    anomaly_count: int = 0

    def success_rate(self) -> float:
        """成功率"""
        if self.total_collected == 0:
            return 0.0
        return self.successful / self.total_collected


class DataCollectorInterface(ABC):
    """数据采集器接口"""

    @abstractmethod
    async def collect_data(self, exchange: Exchange, symbol: str, data_type: DataType) -> Optional[MarketData]:
        """采集数据

        Args:
            exchange: 交易所
            symbol: 交易对
            data_type: 数据类型

        Returns:
            市场数据
        """
        pass

    @abstractmethod
    async def start_stream(self, exchange: Exchange, symbols: List[str]) -> None:
        """启动实时数据流

        Args:
            exchange: 交易所
            symbols: 交易对列表
        """
        pass

    @abstractmethod
    async def stop_stream(self, exchange: Exchange) -> None:
        """停止实时数据流

        Args:
            exchange: 交易所
        """
        pass


class SimulatedDataCollector(DataCollectorInterface):
    """模拟数据采集器

    用于测试和开发，生成模拟的市场数据。
    """

    def __init__(self, config: Optional[Dict] = None):
        """初始化模拟数据采集器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.running = False
        self.tasks: Dict[Exchange, asyncio.Task] = {}
        self.data_queue: asyncio.Queue = asyncio.Queue(maxsize=10000)

        # 基础价格（用于模拟）
        self.base_prices = {
            "BTC/USDT": 50000.0,
            "ETH/USDT": 3000.0,
            "BNB/USDT": 500.0,
            "SOL/USDT": 150.0,
            "XRP/USDT": 0.6
        }

        logger.info("模拟数据采集器初始化完成")

    async def collect_data(self, exchange: Exchange, symbol: str, data_type: DataType) -> Optional[MarketData]:
        """采集模拟数据

        Args:
            exchange: 交易所
            symbol: 交易对
            data_type: 数据类型

        Returns:
            模拟市场数据
        """
        try:
            # 模拟网络延迟（10-50ms）
            await asyncio.sleep(0.01 + (time.time() % 0.04))

            # 生成模拟数据
            timestamp = time.time()
            base_price = self.base_prices.get(symbol, 1000.0)

            if data_type == DataType.PRICE:
                data = self._generate_price_data(base_price, timestamp)
            elif data_type == DataType.VOLUME:
                data = self._generate_volume_data(base_price)
            elif data_type == DataType.ORDERBOOK:
                data = self._generate_orderbook_data(base_price)
            elif data_type == DataType.TRADE:
                data = self._generate_trade_data(base_price, timestamp)
            elif data_type == DataType.FUNDING:
                data = self._generate_funding_data()
            elif data_type == DataType.POSITION:
                data = self._generate_position_data(symbol)
            else:
                logger.warning(f"不支持的数据类型: {data_type}")
                return None

            market_data = MarketData(
                exchange=exchange,
                symbol=symbol,
                data_type=data_type,
                timestamp=timestamp,
                data=data,
                metadata={"source": "simulated"}
            )

            return market_data

        except Exception as e:
            logger.error(f"采集数据失败: {e}")
            return None

    def _generate_price_data(self, base_price: float, timestamp: float) -> Dict[str, Any]:
        """生成价格数据"""
        # 模拟价格波动
        price_change = (time.time() % 10 - 5) / 100.0  # -5% 到 +5% 波动
        current_price = base_price * (1 + price_change)

        return {
            "price": current_price,
            "open": current_price * 0.999,
            "high": current_price * 1.001,
            "low": current_price * 0.998,
            "close": current_price,
            "volume": 1000 + (timestamp % 500)
        }

    def _generate_volume_data(self, base_price: float) -> Dict[str, Any]:
        """生成成交量数据"""
        return {
            "volume": 1000 + (time.time() % 5000),
            "quote_volume": base_price * (1000 + (time.time() % 5000)),
            "trades": 100 + int(time.time() % 1000)
        }

    def _generate_orderbook_data(self, base_price: float) -> Dict[str, Any]:
        """生成订单簿数据"""
        bids = []
        asks = []

        for i in range(10):
            bid_price = base_price * (1 - (i + 1) * 0.0001)
            ask_price = base_price * (1 + (i + 1) * 0.0001)
            bids.append([bid_price, 1000 + i * 100])
            asks.append([ask_price, 1000 + i * 100])

        return {
            "bids": bids,
            "asks": asks,
            "timestamp": time.time()
        }

    def _generate_trade_data(self, base_price: float, timestamp: float) -> Dict[str, Any]:
        """生成交易数据"""
        return {
            "price": base_price * (1 + (time.time() % 0.002 - 0.001)),
            "quantity": 1 + (timestamp % 10),
            "side": "buy" if timestamp % 2 == 0 else "sell",
            "timestamp": timestamp
        }

    def _generate_funding_data(self) -> Dict[str, Any]:
        """生成资金费率数据"""
        return {
            "funding_rate": 0.0001 * (time.time() % 10 - 5),  # -0.05% 到 +0.05%
            "funding_time": time.time() + 3600,  # 1小时后
            "mark_price": 50000.0
        }

    def _generate_position_data(self, symbol: str) -> Dict[str, Any]:
        """生成持仓数据"""
        return {
            "position_amt": 10 + int(time.time() % 100),
            "entry_price": 50000.0,
            "unrealized_pnl": 100 + (time.time() % 1000),
            "leverage": 10,
            "symbol": symbol
        }

    async def start_stream(self, exchange: Exchange, symbols: List[str]) -> None:
        """启动实时数据流

        Args:
            exchange: 交易所
            symbols: 交易对列表
        """
        logger.info(f"启动 {exchange.value} 实时数据流: {symbols}")
        self.running = True
        self.tasks[exchange] = asyncio.create_task(self._stream_data(exchange, symbols))

    async def stop_stream(self, exchange: Exchange) -> None:
        """停止实时数据流

        Args:
            exchange: 交易所
        """
        logger.info(f"停止 {exchange.value} 实时数据流")
        self.running = False
        if exchange in self.tasks:
            self.tasks[exchange].cancel()
            try:
                await self.tasks[exchange]
            except asyncio.CancelledError:
                pass
            del self.tasks[exchange]

    async def _stream_data(self, exchange: Exchange, symbols: List[str]) -> None:
        """实时数据流处理

        Args:
            exchange: 交易所
            symbols: 交易对列表
        """
        try:
            while self.running:
                # 为每个交易对生成数据
                for symbol in symbols:
                    # 随机选择数据类型
                    data_type = DataType.PRICE  # 主要生成价格数据

                    # 采集数据
                    data = await self.collect_data(exchange, symbol, data_type)

                    if data:
                        # 放入队列
                        try:
                            await asyncio.wait_for(self.data_queue.put(data), timeout=0.1)
                        except asyncio.TimeoutError:
                            logger.warning("数据队列已满，丢弃数据")

                # 模拟数据采集间隔（100ms）
                await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            logger.info(f"{exchange.value} 数据流已取消")
        except Exception as e:
            logger.error(f"数据流异常: {e}")


class RealTimeDataCollector:
    """实时数据采集器

    管理多个交易所的数据采集，提供统一的数据接口。
    """

    def __init__(self, config: Optional[Dict] = None):
        """初始化实时数据采集器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.collectors: Dict[Exchange, DataCollectorInterface] = {}
        self.data_queue: asyncio.Queue = asyncio.Queue(maxsize=10000)

        # 数据缓存
        self.cache: Dict[str, deque] = {}
        self.max_cache_size = self.config.get("max_cache_size", 1000)

        # 性能指标
        self.metrics = DataQualityMetrics()
        self.latencies: deque = deque(maxlen=100)

        # 数据订阅
        self.subscriptions: Dict[Exchange, Set[str]] = {}

        logger.info("实时数据采集器初始化完成")

    def add_collector(self, exchange: Exchange, collector: DataCollectorInterface) -> None:
        """添加数据采集器

        Args:
            exchange: 交易所
            collector: 采集器实例
        """
        self.collectors[exchange] = collector
        logger.info(f"添加采集器: {exchange.value}")

    async def collect_single_data(
        self,
        exchange: Exchange,
        symbol: str,
        data_type: DataType
    ) -> Optional[MarketData]:
        """采集单条数据

        Args:
            exchange: 交易所
            symbol: 交易对
            data_type: 数据类型

        Returns:
            市场数据
        """
        self.metrics.total_collected += 1
        start_time = time.time()

        try:
            collector = self.collectors.get(exchange)
            if not collector:
                logger.error(f"未找到 {exchange.value} 采集器")
                self.metrics.failed += 1
                return None

            data = await collector.collect_data(exchange, symbol, data_type)

            if data:
                self.metrics.successful += 1

                # 计算延迟
                latency = (time.time() - start_time) * 1000
                self.latencies.append(latency)

                # 缓存数据
                cache_key = f"{exchange.value}_{symbol}_{data_type.value}"
                if cache_key not in self.cache:
                    self.cache[cache_key] = deque(maxlen=self.max_cache_size)
                self.cache[cache_key].append(data)

                return data
            else:
                self.metrics.failed += 1
                return None

        except Exception as e:
            logger.error(f"采集数据异常: {e}")
            self.metrics.failed += 1
            return None

    async def subscribe_data(self, exchange: Exchange, symbols: List[str]) -> None:
        """订阅实时数据

        Args:
            exchange: 交易所
            symbols: 交易对列表
        """
        collector = self.collectors.get(exchange)
        if not collector:
            logger.error(f"未找到 {exchange.value} 采集器")
            return

        await collector.start_stream(exchange, symbols)
        self.subscriptions[exchange] = set(symbols)

        logger.info(f"订阅 {exchange.value} 数据: {symbols}")

    async def unsubscribe_data(self, exchange: Exchange) -> None:
        """取消订阅实时数据

        Args:
            exchange: 交易所
        """
        collector = self.collectors.get(exchange)
        if collector:
            await collector.stop_stream(exchange)

        if exchange in self.subscriptions:
            del self.subscriptions[exchange]

        logger.info(f"取消订阅 {exchange.value} 数据")

    async def get_latest_data(
        self,
        exchange: Exchange,
        symbol: str,
        data_type: DataType
    ) -> Optional[MarketData]:
        """获取最新数据

        Args:
            exchange: 交易所
            symbol: 交易对
            data_type: 数据类型

        Returns:
            最新市场数据
        """
        cache_key = f"{exchange.value}_{symbol}_{data_type.value}"

        if cache_key in self.cache and self.cache[cache_key]:
            self.metrics.cache_hit_rate += 1
            return self.cache[cache_key][-1]

        return None

    def get_metrics(self) -> DataQualityMetrics:
        """获取性能指标

        Returns:
            数据质量指标
        """
        # 计算平均延迟
        if self.latencies:
            self.metrics.avg_latency_ms = statistics.mean(self.latencies)

        # 计算缓存命中率
        total_requests = self.metrics.successful + self.metrics.failed
        if total_requests > 0:
            self.metrics.cache_hit_rate = self.metrics.cache_hit_rate / total_requests

        return self.metrics

    def reset_metrics(self) -> None:
        """重置性能指标"""
        self.metrics = DataQualityMetrics()
        self.latencies.clear()


async def main():
    """主函数 - 测试实时数据采集器"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # 创建数据采集器
    collector = RealTimeDataCollector()

    # 添加模拟采集器
    sim_collector = SimulatedDataCollector()
    collector.add_collector(Exchange.BINANCE, sim_collector)

    # 测试单次数据采集
    print("\n=== 测试单次数据采集 ===")
    data = await collector.collect_single_data(
        exchange=Exchange.BINANCE,
        symbol="BTC/USDT",
        data_type=DataType.PRICE
    )
    if data:
        print(f"采集成功: {data.symbol} 价格: {data.data['price']:.2f}")

    # 测试批量采集
    print("\n=== 测试批量采集 ===")
    symbols = ["BTC/USDT", "ETH/USDT", "BNB/USDT"]
    for symbol in symbols:
        for data_type in [DataType.PRICE, DataType.VOLUME, DataType.ORDERBOOK]:
            data = await collector.collect_single_data(
                exchange=Exchange.BINANCE,
                symbol=symbol,
                data_type=data_type
            )
            if data:
                print(f"采集成功: {symbol} {data_type.value}")

    # 显示性能指标
    metrics = collector.get_metrics()
    print(f"\n=== 性能指标 ===")
    print(f"总采集数: {metrics.total_collected}")
    print(f"成功数: {metrics.successful}")
    print(f"失败数: {metrics.failed}")
    print(f"成功率: {metrics.success_rate()*100:.2f}%")
    print(f"平均延迟: {metrics.avg_latency_ms:.2f}ms")
    print(f"缓存命中率: {metrics.cache_hit_rate*100:.2f}%")


if __name__ == "__main__":
    asyncio.run(main())
