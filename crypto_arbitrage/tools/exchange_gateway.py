"""交易所数据网关 V1.0 - 统一交易所API接口

提供统一的交易所数据访问层:
- 价格获取
- 订单簿数据
- 交易对信息
- 账户余额
- 模拟/真实模式切换
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ExchangeMode(str, Enum):
    """交易所模式"""
    SIMULATED = "simulated"
    TESTNET = "testnet"
    LIVE = "live"


@dataclass
class TickerPrice:
    """价格数据结构"""
    symbol: str
    bid: float  # 买一价
    ask: float  # 卖一价
    last: float  # 最新价
    volume_24h: float = 0.0
    timestamp: float = 0.0


@dataclass
class OrderBookEntry:
    """订单簿条目"""
    price: float
    quantity: float


@dataclass
class OrderBook:
    """订单簿数据"""
    symbol: str
    bids: List[OrderBookEntry]
    asks: List[OrderBookEntry]
    timestamp: float = 0.0


@dataclass
class Balance:
    """账户余额"""
    asset: str
    free: float
    locked: float

    @property
    def total(self) -> float:
        return self.free + self.locked


class BaseExchangeGateway(ABC):
    """交易所网关基类

    子类必须实现:
    - _fetch_ticker: 获取价格数据
    - _fetch_order_book: 获取订单簿
    - _fetch_balance: 获取余额
    - _place_order: 下单
    - _cancel_order: 取消订单
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """初始化交易所网关

        Args:
            config: 交易所配置
                - mode: SIMULATED | TESTNET | LIVE
                - api_key: API密钥 (LIVE模式需要)
                - api_secret: API密钥 (LIVE模式需要)
                - testnet: 测试网端点 (可选)
        """
        self.config = config
        self.mode = ExchangeMode(config.get('mode', 'simulated'))
        self.api_key = config.get('api_key', '')
        self.api_secret = config.get('api_secret', '')
        self._is_initialized = False

        logger.info(f"交易所网关初始化: {self.name} ({self.mode.value})")

    @property
    @abstractmethod
    def name(self) -> str:
        """交易所名称"""
        ...

    async def initialize(self) -> bool:
        """初始化连接"""
        if self._is_initialized:
            return True

        try:
            if self.mode == ExchangeMode.SIMULATED:
                await self._init_simulated()
            elif self.mode in [ExchangeMode.TESTNET, ExchangeMode.LIVE]:
                await self._init_api()

            self._is_initialized = True
            logger.info(f"{self.name} 连接初始化完成")
            return True
        except Exception as e:
            logger.error(f"{self.name} 初始化失败: {e}")
            return False

    async def _init_simulated(self) -> None:
        """初始化模拟模式"""
        self._simulated_prices: Dict[str, float] = {}
        self._simulated_balances: Dict[str, float] = {
            'USDT': 10000.0,
            'BTC': 0.1,
            'ETH': 1.0,
            'SOL': 10.0,
            'DOGE': 1000.0,
        }

    async def _init_api(self) -> None:
        """初始化真实API (子类覆盖实现)"""
        pass

    # -------------------- 价格数据 --------------------

    async def get_ticker(self, symbol: str) -> Optional[TickerPrice]:
        """获取价格数据

        Args:
            symbol: 交易对 (如 BTC/USDT)

        Returns:
            价格数据, 失败返回None
        """
        if not self._is_initialized:
            await self.initialize()

        try:
            return await self._fetch_ticker(symbol)
        except Exception as e:
            logger.error(f"{self.name} 获取价格失败 {symbol}: {e}")
            return None

    async def get_ticker_batch(self, symbols: List[str]) -> Dict[str, TickerPrice]:
        """批量获取价格

        Args:
            symbols: 交易对列表

        Returns:
            symbol -> 价格数据映射
        """
        results: Dict[str, TickerPrice] = {}

        # 并发请求
        tasks = [self.get_ticker(s) for s in symbols]
        ticker_list = await asyncio.gather(*tasks, return_exceptions=True)

        for symbol, ticker in zip(symbols, ticker_list):
            if isinstance(ticker, TickerPrice):
                results[symbol] = ticker
            elif isinstance(ticker, Exception):
                logger.debug(f"{symbol}: {ticker}")

        return results

    @abstractmethod
    async def _fetch_ticker(self, symbol: str) -> Optional[TickerPrice]:
        """获取价格数据 (子类实现)"""
        ...

    # -------------------- 订单簿 --------------------

    async def get_order_book(self, symbol: str, limit: int = 20) -> Optional[OrderBook]:
        """获取订单簿

        Args:
            symbol: 交易对
            limit: 深度

        Returns:
            订单簿数据, 失败返回None
        """
        if not self._is_initialized:
            await self.initialize()

        try:
            return await self._fetch_order_book(symbol, limit)
        except Exception as e:
            logger.error(f"{self.name} 获取订单簿失败 {symbol}: {e}")
            return None

    @abstractmethod
    async def _fetch_order_book(self, symbol: str, limit: int) -> Optional[OrderBook]:
        """获取订单簿 (子类实现)"""
        ...

    # -------------------- 余额 --------------------

    async def get_balance(self, asset: str) -> Optional[Balance]:
        """获取资产余额

        Args:
            asset: 资产符号 (如 BTC)

        Returns:
            余额数据, 失败返回None
        """
        if not self._is_initialized:
            await self.initialize()

        try:
            return await self._fetch_balance(asset)
        except Exception as e:
            logger.error(f"{self.name} 获取余额失败 {asset}: {e}")
            return None

    async def get_all_balances(self) -> Dict[str, Balance]:
        """获取所有余额"""
        if not self._is_initialized:
            await self.initialize()

        try:
            return await self._fetch_all_balances()
        except Exception as e:
            logger.error(f"{self.name} 获取余额失败: {e}")
            return {}

    @abstractmethod
    async def _fetch_balance(self, asset: str) -> Optional[Balance]:
        """获取余额 (子类实现)"""
        ...

    async def _fetch_all_balances(self) -> Dict[str, Balance]:
        """获取所有余额 (子类实现)"""
        return {}

    # -------------------- 交易 --------------------

    async def place_order(
        self,
        symbol: str,
        side: str,  # BUY | SELL
        order_type: str,  # LIMIT | MARKET
        quantity: float,
        price: Optional[float] = None,
    ) -> Optional[str]:
        """下单

        Args:
            symbol: 交易��
            side: 方向
            order_type: 订单类型
            quantity: 数量
            price: 价格 (LIMIT单需要)

        Returns:
            订单ID, 失败返回None
        """
        if not self._is_initialized:
            await self.initialize()

        try:
            return await self._place_order(symbol, side, order_type, quantity, price)
        except Exception as e:
            logger.error(f"{self.name} 下单失败 {symbol}: {e}")
            return None

    @abstractmethod
    async def _place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float],
    ) -> Optional[str]:
        """下单 (子类实现)"""
        ...

    async def cancel_order(self, order_id: str) -> bool:
        """取消订单"""
        try:
            return await self._cancel_order(order_id)
        except Exception as e:
            logger.error(f"{self.name} 取消订单失败 {order_id}: {e}")
            return False

    @abstractmethod
    async def _cancel_order(self, order_id: str) -> bool:
        """取消订单 (子类实现)"""
        ...

    # -------------------- 工具方法 --------------------

    @property
    def is_live_mode(self) -> bool:
        """是否为真实交易模式"""
        return self.mode == ExchangeMode.LIVE

    @property
    def is_simulated(self) -> bool:
        """是否为模拟模式"""
        return self.mode == ExchangeMode.SIMULATED


class BinanceGateway(BaseExchangeGateway):
    """Binance 交易所网关"""

    @property
    def name(self) -> str:
        return "Binance"

    async def _fetch_ticker(self, symbol: str) -> Optional[TickerPrice]:
        """获取价格数据"""
        if self.mode == ExchangeMode.SIMULATED:
            # 模拟数据
            base_price = self._simulated_prices.get(symbol, 50000.0)
            spread = base_price * 0.0001  # 0.01% 价差
            return TickerPrice(
                symbol=symbol,
                bid=base_price - spread,
                ask=base_price + spread,
                last=base_price,
            )

        # 真实API (需要实现)
        # import requests
        # url = f"{self.config.get('base_url')}/api/v3/ticker"
        # resp = requests.get(url, params={"symbol": symbol.replace('/', '')})
        # data = resp.json()
        # return TickerPrice(...)

        return None

    async def _fetch_order_book(self, symbol: str, limit: int) -> Optional[OrderBook]:
        """获取订单簿"""
        if self.mode == ExchangeMode.SIMULATED:
            # 模拟订单簿
            base_price = self._simulated_prices.get(symbol, 50000.0)
            bids = [
                OrderBookEntry(price=base_price - i * 0.5, quantity=1.0 + i * 0.1)
                for i in range(limit)
            ]
            asks = [
                OrderBookEntry(price=base_price + i * 0.5 + 0.01, quantity=1.0 + i * 0.1)
                for i in range(limit)
            ]
            return OrderBook(symbol=symbol, bids=bids, asks=asks)

        return None

    async def _fetch_balance(self, asset: str) -> Optional[Balance]:
        """获取余额"""
        if self.mode == ExchangeMode.SIMULATED:
            free = self._simulated_balances.get(asset, 0.0)
            return Balance(asset=asset, free=free, locked=0.0)

        return None

    async def _fetch_all_balances(self) -> Dict[str, Balance]:
        """获取所有余额"""
        if self.mode == ExchangeMode.SIMULATED:
            return {
                asset: Balance(asset=asset, free=free, locked=0.0)
                for asset, free in self._simulated_balances.items()
            }

        return {}

    async def _place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float],
    ) -> Optional[str]:
        """下单"""
        import time
        order_id = f"ORDER_{int(time.time() * 1000)}"
        logger.info(f"模拟下单: {symbol} {side} {order_type} {quantity} @ {price}")
        return order_id

    async def _cancel_order(self, order_id: str) -> bool:
        """取消订单"""
        logger.info(f"模拟取消订单: {order_id}")
        return True


class OKXGateway(BaseExchangeGateway):
    """OKX 交易所网关"""

    @property
    def name(self) -> str:
        return "OKX"

    async def _fetch_ticker(self, symbol: str) -> Optional[TickerPrice]:
        """获取价格数据"""
        if self.mode == ExchangeMode.SIMULATED:
            base_price = self._simulated_prices.get(symbol, 50000.0)
            spread = base_price * 0.0001
            return TickerPrice(
                symbol=symbol,
                bid=base_price - spread,
                ask=base_price + spread,
                last=base_price,
            )
        return None

    async def _fetch_order_book(self, symbol: str, limit: int) -> Optional[OrderBook]:
        """获取订单簿"""
        if self.mode == ExchangeMode.SIMULATED:
            base_price = self._simulated_prices.get(symbol, 50000.0)
            bids = [
                OrderBookEntry(price=base_price - i * 0.5, quantity=1.0 + i * 0.1)
                for i in range(limit)
            ]
            asks = [
                OrderBookEntry(price=base_price + i * 0.5 + 0.01, quantity=1.0 + i * 0.1)
                for i in range(limit)
            ]
            return OrderBook(symbol=symbol, bids=bids, asks=asks)
        return None

    async def _fetch_balance(self, asset: str) -> Optional[Balance]:
        """获取余额"""
        if self.mode == ExchangeMode.SIMULATED:
            free = self._simulated_balances.get(asset, 0.0)
            return Balance(asset=asset, free=free, locked=0.0)
        return None

    async def _fetch_all_balances(self) -> Dict[str, Balance]:
        """获取所有余额"""
        if self.mode == ExchangeMode.SIMULATED:
            return {
                asset: Balance(asset=asset, free=free, locked=0.0)
                for asset, free in self._simulated_prices.items()
            }
        return {}

    async def _place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float],
    ) -> Optional[str]:
        """下单"""
        import time
        order_id = f"OKX_{int(time.time() * 1000)}"
        logger.info(f"模拟下单: {symbol} {side} {order_type} {quantity} @ {price}")
        return order_id

    async def _cancel_order(self, order_id: str) -> bool:
        """取消订单"""
        logger.info(f"模拟取消订单: {order_id}")
        return True


# -------------------- 工厂函数 --------------------

def create_exchange_gateway(
    exchange: str,
    config: Dict[str, Any],
) -> Optional[BaseExchangeGateway]:
    """创建交易所网关

    Args:
        exchange: 交易所名 (binance, okx)
        config: 配置字典

    Returns:
        交易所网关实例
    """
    gateways = {
        'binance': BinanceGateway,
        'okx': OKXGateway,
    }

    gateway_class = gateways.get(exchange.lower())
    if not gateway_class:
        logger.error(f"不支持的交易所: {exchange}")
        return None

    return gateway_class(config)