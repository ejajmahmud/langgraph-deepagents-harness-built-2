"""V64.0 多交易所统一网关模块

V64.0 新增功能:
1. MultiExchangeGateway - 多交易所统一网关
2. ExchangeConnection - 连接状态管理
3. ExchangeHealth - 交易所健康状态
4. ConnectionPool - 连接池管理
5. UnifiedPriceAPI - 统一价格API
6. Automatic Failover - 自动故障转移

创建时间: 2026-05-08
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable

from deepagents_crypto_trading.types import Exchange, Price

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """连接状态"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"


class ExchangeHealth(Enum):
    """交易所健康状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ExchangeConnection:
    """交易所连接状态"""
    exchange: Exchange
    state: ConnectionState = ConnectionState.DISCONNECTED
    health: ExchangeHealth = ExchangeHealth.UNKNOWN
    latency_ms: float = 0.0  # 延迟(毫秒)
    error_count: int = 0
    last_error: Optional[str] = None
    last_success: Optional[datetime] = None
    connect_time: Optional[datetime] = None
    request_count: int = 0
    success_rate: float = 1.0  # 成功率

    def is_healthy(self) -> bool:
        """是否健康"""
        return (
            self.health == ExchangeHealth.HEALTHY
            and self.state == ConnectionState.CONNECTED
            and self.success_rate > 0.95
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "exchange": self.exchange.value,
            "state": self.state.value,
            "health": self.health.value,
            "latency_ms": self.latency_ms,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "last_success": self.last_success.isoformat() if self.last_success else None,
            "success_rate": self.success_rate,
        }


@dataclass
class GatewayConfig:
    """网关配置"""
    timeout_seconds: float = 10.0  # 请求超时
    max_retries: int = 3  # 最大重试次数
    health_check_interval_seconds: int = 60  # 健康检查间隔
    rate_limit_requests_per_minute: int = 1200  # 速率限制
    enable_auto_failover: bool = True  # 自动故障转移
    min_health_threshold: float = 0.8  # 最小健康阈值
    circuit_breaker_threshold: int = 5  # 熔断阈值(连续错误)


class ConnectionPool:
    """连接池管理"""

    def __init__(self, config: GatewayConfig) -> None:
        """初始化连接池"""
        self.config = config
        self._connections: Dict[Exchange, ExchangeConnection] = {}
        self._last_health_check: Dict[Exchange, datetime] = {}
        self._lock = asyncio.Lock()

    def register(self, exchange: Exchange) -> ExchangeConnection:
        """注册交易所连接"""
        conn = ExchangeConnection(
            exchange=exchange,
            state=ConnectionState.DISCONNECTED,
            health=ExchangeHealth.UNKNOWN,
        )
        self._connections[exchange] = conn
        logger.info(f"Registered exchange: {exchange.value}")
        return conn

    def get_connection(self, exchange: Exchange) -> Optional[ExchangeConnection]:
        """获取连接"""
        return self._connections.get(exchange)

    def get_all_connections(self) -> Dict[Exchange, ExchangeConnection]:
        """获取所有连接"""
        return self._connections.copy()

    def update_health(
        self,
        exchange: Exchange,
        success: bool,
        latency_ms: float,
        error: Optional[str] = None,
    ) -> None:
        """更新健康状态"""
        conn = self._connections.get(exchange)
        if not conn:
            return

        conn.latency_ms = latency_ms
        conn.request_count += 1

        if success:
            conn.state = ConnectionState.CONNECTED
            conn.last_success = datetime.now()
            conn.error_count = 0
            conn.last_error = None
            # 计算成功率
            conn.success_rate = (
                conn.request_count - conn.error_count
            ) / conn.request_count
            # 健康状态
            if conn.success_rate > 0.98 and latency_ms < 100:
                conn.health = ExchangeHealth.HEALTHY
            elif conn.success_rate > 0.9 and latency_ms < 500:
                conn.health = ExchangeHealth.DEGRADED
            else:
                conn.health = ExchangeHealth.UNHEALTHY
        else:
            conn.error_count += 1
            conn.last_error = error
            # 熔断
            if conn.error_count >= self.config.circuit_breaker_threshold:
                conn.state = ConnectionState.ERROR
                conn.health = ExchangeHealth.UNHEALTHY
                logger.warning(f"Circuit breaker triggered for {exchange.value}")

    def get_healthy_exchanges(self) -> List[Exchange]:
        """获取健康交易所列表"""
        return [
            ex
            for ex, conn in self._connections.items()
            if conn.is_healthy()
        ]

    def get_best_exchange(self) -> Optional[Exchange]:
        """获取最佳交易所(最低延迟)"""
        healthy = self.get_healthy_exchanges()
        if not healthy:
            return None

        # 选择延迟最低的
        best = min(
            healthy,
            key=lambda ex: self._connections[ex].latency_ms,
        )
        return best


@dataclass
class UnifiedPriceResponse:
    """统一价格响应"""
    symbol: str
    price: float
    volume_24h: float
    timestamp: datetime
    exchange: Exchange
    latency_ms: float


class MultiExchangeGateway:
    """多交易所统一网关

    功能:
    1. 统一API - 跨交易所价格获取
    2. 自动故障转移 - 主交易所失败自动切换
    3. 连接池管理 - 多连接状态跟踪
    4. 速率限制 - 自动限流
    5. 健康检查 - 自动健康监测
    """

    def __init__(self, config: Optional[GatewayConfig] = None) -> None:
        """初始化网关"""
        self.config = config or GatewayConfig()
        self.pool = ConnectionPool(self.config)
        self._price_fetchers: Dict[Exchange, Callable] = {}
        self._lock = asyncio.Lock()
        self._running = False

    def register_fetcher(
        self,
        exchange: Exchange,
        fetcher: Callable[[List[str]], Dict[str, Price]],
    ) -> None:
        """注册价格获取器

        Args:
            exchange: 交易所
            fetcher: 异步价格获取函数
        """
        self._price_fetchers[exchange] = fetcher
        self.pool.register(exchange)
        logger.info(f"Registered fetcher for {exchange.value}")

    async def fetch_price(
        self,
        symbol: str,
        preferred_exchange: Optional[Exchange] = None,
    ) -> Optional[UnifiedPriceResponse]:
        """获取统一价格

        Args:
            symbol: 交易对
            preferred_exchange: 首选交易所

        Returns:
            价格响应
        """
        # 确定要尝试的交易所顺序
        exchanges = []
        if preferred_exchange and preferred_exchange in self._price_fetchers:
            exchanges.append(preferred_exchange)

        # 添加其他健康交易所
        for ex in self.pool.get_healthy_exchanges():
            if ex not in exchanges:
                exchanges.append(ex)

        if not exchanges:
            logger.error("No available exchanges")
            return None

        # 尝试获取价格
        last_error = None
        for exchange in exchanges:
            try:
                result = await self._fetch_from_exchange(exchange, symbol)
                if result:
                    return result
            except Exception as e:
                last_error = e
                logger.warning(f"Failed to fetch from {exchange.value}: {e}")
                # 更新健康状态
                self.pool.update_health(
                    exchange, False, 0.0, str(e)
                )

                # 自动故障转移
                if self.config.enable_auto_failover:
                    continue

        logger.error(f"All exchanges failed for {symbol}")
        return None

    async def _fetch_from_exchange(
        self,
        exchange: Exchange,
        symbol: str,
    ) -> Optional[UnifiedPriceResponse]:
        """从指定交易所获取价格"""
        fetcher = self._price_fetchers.get(exchange)
        if not fetcher:
            return None

        start_time = time.perf_counter()

        try:
            prices = await fetcher([symbol])
            price_data = prices.get(symbol)

            if not price_data:
                return None

            latency_ms = (time.perf_counter() - start_time) * 1000

            # 更新健康状态
            self.pool.update_health(exchange, True, latency_ms)

            return UnifiedPriceResponse(
                symbol=symbol,
                price=price_data.price,
                volume_24h=price_data.volume_24h,
                timestamp=price_data.timestamp,
                exchange=exchange,
                latency_ms=latency_ms,
            )

        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            self.pool.update_health(exchange, False, latency_ms, str(e))
            raise

    async def fetch_prices(
        self,
        symbols: List[str],
        exchange: Optional[Exchange] = None,
    ) -> Dict[str, UnifiedPriceResponse]:
        """批量获取价格

        Args:
            symbols: 交易对列表
            exchange: 指定交易所(None则用最佳的)

        Returns:
            价格字典
        """
        results = {}

        # 获取最佳交易所
        if exchange is None:
            exchange = self.pool.get_best_exchange()

        if exchange is None:
            logger.error("No healthy exchange available")
            return results

        for symbol in symbols:
            result = await self.fetch_price(symbol, exchange)
            if result:
                results[symbol] = result

        return results

    def get_gateway_status(self) -> Dict[str, Any]:
        """获取网关状态"""
        connections = {
            ex.value: conn.to_dict()
            for ex, conn in self.pool.get_all_connections().items()
        }

        return {
            "running": self._running,
            "healthy_exchanges": [ex.value for ex in self.pool.get_healthy_exchanges()],
            "best_exchange": self.pool.get_best_exchange().value
            if self.pool.get_best_exchange()
            else None,
            "connections": connections,
        }


# 全局网关实例
_gateway: Optional[MultiExchangeGateway] = None


def get_gateway(config: Optional[GatewayConfig] = None) -> MultiExchangeGateway:
    """获取多交易所网关实例"""
    global _gateway
    if _gateway is None:
        config = config or GatewayConfig()
        _gateway = MultiExchangeGateway(config)
    return _gateway


def create_gateway_config(
    timeout: float = 10.0,
    enable_failover: bool = True,
    rate_limit: int = 1200,
) -> GatewayConfig:
    """创建网关配置"""
    return GatewayConfig(
        timeout_seconds=timeout,
        enable_auto_failover=enable_failover,
        rate_limit_requests_per_minute=rate_limit,
    )