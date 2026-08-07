"""价格历史管理器 V16.4

维护多交易所多币种的滚动价格窗口，为统计套利提供数据基础。

核心能力：
1. 滚动价格窗口 — 每个币种/交易所维护可配置长度的价格序列
2. 收益率计算 — 对数收益率序列（用于协整分析）
3. 价差跟踪 — 跨交易所价差历史
4. 统计摘要 — 均值/标准差/偏度/峰度等统计量
5. 数据注入 — 从CcxtPriceFeed批量初始化历史

架构位置:
    CcxtPriceFeed ─→ PriceHistoryManager ─→ StatisticalArbEngine
                                              ↕
                                    ArbitragePipeline (V16.4)

创建时间：2026-05-05
"""

import logging
import math
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class PricePoint:
    """价格数据点"""
    timestamp: float
    price: float
    bid: float = 0.0
    ask: float = 0.0
    volume: float = 0.0
    exchange: str = ""


@dataclass
class RollingStats:
    """滚动统计量"""
    symbol: str
    exchange: str
    count: int = 0
    mean: float = 0.0
    std: float = 0.0
    min_val: float = 0.0
    max_val: float = 0.0
    last_price: float = 0.0
    returns_mean: float = 0.0
    returns_std: float = 0.0
    skewness: float = 0.0
    kurtosis: float = 0.0
    timestamp: float = 0.0


class PriceHistoryManager:
    """价格历史管理器 V16.4

    维护多交易所多币种的滚动价格窗口，
    为统计套利策略提供历史数据和分析工具。
    """

    # 默认监控的币种和交易所
    DEFAULT_SYMBOLS = [
        "BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT",
        "XRP/USDT", "ADA/USDT", "DOGE/USDT", "AVAX/USDT"
    ]

    DEFAULT_EXCHANGES = ["binance", "okex", "bybit", "huobi", "coinbase"]

    # 统计套利配对（高度相关的资产对）
    STATISTICAL_PAIRS = [
        ("BTC/USDT", "ETH/USDT"),
        ("BTC/USDT", "SOL/USDT"),
        ("ETH/USDT", "SOL/USDT"),
        ("BTC/USDT", "BNB/USDT"),
        ("ETH/USDT", "BNB/USDT"),
        ("XRP/USDT", "ADA/USDT"),
        ("DOGE/USDT", "SOL/USDT"),
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化价格历史管理器

        Args:
            config: 配置字典，支持:
                - window_size: 滚动窗口大小 (默认500)
                - symbols: 监控币种列表
                - exchanges: 监控交易所列表
        """
        self.config = config or {}

        self._window_size = self.config.get("window_size", 500)
        self._symbols = self.config.get("symbols", self.DEFAULT_SYMBOLS)
        self._exchanges = self.config.get("exchanges", self.DEFAULT_EXCHANGES)

        # 价格历史: {symbol: {exchange: deque[PricePoint]}}
        self._price_history: Dict[str, Dict[str, deque]] = {}

        # 收益率序列: {symbol: {exchange: deque[float]}}
        self._returns: Dict[str, Dict[str, deque]] = {}

        # 最新价格缓存
        self._latest_prices: Dict[str, Dict[str, PricePoint]] = {}

        # 统计信息
        self.total_updates = 0
        self.total_ticks = 0

        # 初始化数据结构
        self._init_data_structures()

        logger.info(
            f"价格历史管理器 V16.4 初始化: "
            f"window={self._window_size}, "
            f"symbols={len(self._symbols)}, "
            f"exchanges={len(self._exchanges)}"
        )

    def _init_data_structures(self) -> None:
        """初始化所有数据结构"""
        for symbol in self._symbols:
            self._price_history[symbol] = {}
            self._returns[symbol] = {}
            self._latest_prices[symbol] = {}

            for exchange in self._exchanges:
                self._price_history[symbol][exchange] = deque(maxlen=self._window_size)
                self._returns[symbol][exchange] = deque(maxlen=self._window_size - 1)

    def update_price(
        self,
        symbol: str,
        exchange: str,
        price: float,
        bid: float = 0.0,
        ask: float = 0.0,
        volume: float = 0.0,
        timestamp: Optional[float] = None
    ) -> None:
        """更新单个价格数据点

        Args:
            symbol: 交易对
            exchange: 交易所
            price: 最新价格
            bid: 买一价
            ask: 卖一价
            volume: 成交量
            timestamp: 时间戳
        """
        ts = timestamp or time.time()

        point = PricePoint(
            timestamp=ts,
            price=price,
            bid=bid or price,
            ask=ask or price,
            volume=volume,
            exchange=exchange
        )

        # 确保数据结构存在
        if symbol not in self._price_history:
            self._price_history[symbol] = {}
            self._returns[symbol] = {}
            self._latest_prices[symbol] = {}

        if exchange not in self._price_history[symbol]:
            self._price_history[symbol][exchange] = deque(maxlen=self._window_size)
            self._returns[symbol][exchange] = deque(maxlen=self._window_size - 1)

        # 计算对数收益率
        history = self._price_history[symbol][exchange]
        if len(history) > 0:
            last_price = history[-1].price
            if last_price > 0 and price > 0:
                log_return = math.log(price / last_price)
                self._returns[symbol][exchange].append(log_return)

        # 追加价格
        history.append(point)
        self._latest_prices[symbol][exchange] = point
        self.total_updates += 1

    def update_from_snapshot(self, snapshot) -> int:
        """从CcxtPriceFeed的PriceSnapshot批量更新

        Args:
            snapshot: PriceSnapshot 实例

        Returns:
            更新的数据点数量
        """
        count = 0
        for symbol, exchange_prices in snapshot.prices.items():
            for exchange, ticker in exchange_prices.items():
                self.update_price(
                    symbol=symbol,
                    exchange=exchange,
                    price=ticker.last,
                    bid=ticker.bid,
                    ask=ticker.ask,
                    volume=ticker.volume_24h,
                    timestamp=ticker.timestamp
                )
                count += 1

        self.total_ticks += 1
        return count

    def get_price_history(
        self,
        symbol: str,
        exchange: str,
        length: Optional[int] = None
    ) -> List[PricePoint]:
        """获取价格历史

        Args:
            symbol: 交易对
            exchange: 交易所
            length: 返回的数据点数量（None=全部）

        Returns:
            价格数据点列表
        """
        history = self._price_history.get(symbol, {}).get(exchange, deque())
        if length is None:
            return list(history)
        return list(history)[-length:]

    def get_price_series(
        self,
        symbol: str,
        exchange: str,
        length: Optional[int] = None
    ) -> List[float]:
        """获取价格序列（仅价格值）

        Args:
            symbol: 交易对
            exchange: 交易所
            length: 返回的数据点数量

        Returns:
            价格值列表
        """
        history = self.get_price_history(symbol, exchange, length)
        return [p.price for p in history]

    def get_returns_series(
        self,
        symbol: str,
        exchange: str,
        length: Optional[int] = None
    ) -> List[float]:
        """获取对数收益率序列

        Args:
            symbol: 交易对
            exchange: 交易所
            length: 返回的数据点数量

        Returns:
            对数收益率列表
        """
        returns = list(self._returns.get(symbol, {}).get(exchange, deque()))
        if length is None:
            return returns
        return returns[-length:]

    def calculate_rolling_stats(
        self,
        symbol: str,
        exchange: str,
        window: Optional[int] = None
    ) -> Optional[RollingStats]:
        """计算滚动统计量

        Args:
            symbol: 交易对
            exchange: 交易所
            window: 统计窗口大小

        Returns:
            滚动统计量，数据不足返回None
        """
        prices = self.get_price_series(symbol, exchange, window)
        returns = self.get_returns_series(symbol, exchange, window)

        if len(prices) < 2:
            return None

        n = len(prices)
        mean_price = sum(prices) / n
        variance = sum((p - mean_price) ** 2 for p in prices) / max(n - 1, 1)
        std_price = math.sqrt(variance) if variance > 0 else 0

        # 收益率统计
        returns_mean = 0.0
        returns_std = 0.0
        skewness = 0.0
        kurtosis = 0.0

        if len(returns) >= 2:
            returns_mean = sum(returns) / len(returns)
            ret_var = sum((r - returns_mean) ** 2 for r in returns) / max(len(returns) - 1, 1)
            returns_std = math.sqrt(ret_var) if ret_var > 0 else 0

            # 偏度
            if returns_std > 0:
                n_ret = len(returns)
                skewness = sum((r - returns_mean) ** 3 for r in returns) / (n_ret * returns_std ** 3)

                # 峰度（超额）
                kurtosis = sum((r - returns_mean) ** 4 for r in returns) / (n_ret * returns_std ** 4) - 3.0

        return RollingStats(
            symbol=symbol,
            exchange=exchange,
            count=n,
            mean=mean_price,
            std=std_price,
            min_val=min(prices),
            max_val=max(prices),
            last_price=prices[-1],
            returns_mean=returns_mean,
            returns_std=returns_std,
            skewness=skewness,
            kurtosis=kurtosis,
            timestamp=time.time()
        )

    def calculate_correlation(
        self,
        symbol1: str,
        symbol2: str,
        exchange: str,
        window: Optional[int] = None
    ) -> Optional[float]:
        """计算两个币种的相关系数

        Args:
            symbol1: 币种1
            symbol2: 币种2
            exchange: 交易所
            window: 计算窗口

        Returns:
            相关系数 (-1到1)，数据不足返回None
        """
        returns1 = self.get_returns_series(symbol1, exchange, window)
        returns2 = self.get_returns_series(symbol2, exchange, window)

        # 对齐长度
        min_len = min(len(returns1), len(returns2))
        if min_len < 10:
            return None

        returns1 = returns1[-min_len:]
        returns2 = returns2[-min_len:]

        mean1 = sum(returns1) / min_len
        mean2 = sum(returns2) / min_len

        cov = sum((r1 - mean1) * (r2 - mean2) for r1, r2 in zip(returns1, returns2)) / min_len
        var1 = sum((r - mean1) ** 2 for r in returns1) / min_len
        var2 = sum((r - mean2) ** 2 for r in returns2) / min_len

        if var1 <= 0 or var2 <= 0:
            return None

        return cov / (math.sqrt(var1) * math.sqrt(var2))

    def calculate_spread_series(
        self,
        symbol1: str,
        symbol2: str,
        exchange: str,
        window: Optional[int] = None
    ) -> List[float]:
        """计算价差序列（对数价格比）

        spread = ln(price1) - ln(price2)

        Args:
            symbol1: 币种1
            symbol2: 币种2
            exchange: 交易所
            window: 计算窗口

        Returns:
            价差序列
        """
        prices1 = self.get_price_series(symbol1, exchange, window)
        prices2 = self.get_price_series(symbol2, exchange, window)

        min_len = min(len(prices1), len(prices2))
        if min_len < 2:
            return []

        prices1 = prices1[-min_len:]
        prices2 = prices2[-min_len:]

        spread = []
        for p1, p2 in zip(prices1, prices2):
            if p1 > 0 and p2 > 0:
                spread.append(math.log(p1 / p2))

        return spread

    def calculate_z_score(
        self,
        symbol1: str,
        symbol2: str,
        exchange: str,
        window: Optional[int] = None
    ) -> Optional[Tuple[float, float, float]]:
        """计算价差的Z-score

        Args:
            symbol1: 币种1
            symbol2: 币种2
            exchange: 交易所
            window: 计算窗口

        Returns:
            (z_score, mean, std) 或 None
        """
        spread = self.calculate_spread_series(symbol1, symbol2, exchange, window)
        if len(spread) < 10:
            return None

        n = len(spread)
        mean_s = sum(spread) / n
        var_s = sum((s - mean_s) ** 2 for s in spread) / max(n - 1, 1)
        std_s = math.sqrt(var_s) if var_s > 0 else 0

        if std_s == 0:
            return None

        current_spread = spread[-1]
        z_score = (current_spread - mean_s) / std_s

        return z_score, mean_s, std_s

    def calculate_half_life(
        self,
        symbol1: str,
        symbol2: str,
        exchange: str,
        window: Optional[int] = None
    ) -> Optional[float]:
        """计算均值回归的半衰期（小时）

        基于OU过程参数估计: spread_t = α + β * spread_{t-1} + ε
        half_life = -ln(2) / ln(β)

        Args:
            symbol1: 币种1
            symbol2: 币种2
            exchange: 交易所
            window: 计算窗口

        Returns:
            半衰期（小时），数据不足返回None
        """
        spread = self.calculate_spread_series(symbol1, symbol2, exchange, window)
        if len(spread) < 20:
            return None

        # OLS回归: spread_t = α + β * spread_{t-1}
        y = spread[1:]
        x = spread[:-1]

        n = len(y)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi ** 2 for xi in x)

        denom = n * sum_x2 - sum_x ** 2
        if denom == 0:
            return None

        beta = (n * sum_xy - sum_x * sum_y) / denom

        if beta <= 0 or beta >= 1:
            return None

        half_life_ticks = -math.log(2) / math.log(beta)

        # 假设每个tick约1秒（基于典型更新频率）
        # 对于模拟数据，我们假设每tick=1分钟
        half_life_hours = half_life_ticks / 60.0

        return max(0.1, min(half_life_hours, 168.0))

    def seed_from_price_feed(self, feed, ticks: int = 100) -> int:
        """用CcxtPriceFeed初始化历史数据

        Args:
            feed: CcxtPriceFeed实例
            ticks: 生成的历史tick数量

        Returns:
            总数据点数量
        """
        total_points = 0
        for _ in range(ticks):
            snapshot = feed.get_all_prices()
            count = self.update_from_snapshot(snapshot)
            total_points += count

        logger.info(
            f"价格历史初始化完成: {ticks} ticks, "
            f"{total_points} 数据点, "
            f"每个币种/交易所约 {ticks} 个价格点"
        )
        return total_points

    def get_latest_price(self, symbol: str, exchange: str) -> Optional[float]:
        """获取最新价格

        Args:
            symbol: 交易对
            exchange: 交易所

        Returns:
            最新价格，无数据返回None
        """
        point = self._latest_prices.get(symbol, {}).get(exchange)
        return point.price if point else None

    def get_statistics(self) -> Dict[str, Any]:
        """获取管理器统计信息

        Returns:
            统计数据字典
        """
        total_data_points = sum(
            len(history)
            for symbol_hist in self._price_history.values()
            for history in symbol_hist.values()
        )

        return {
            "version": "V16.4",
            "window_size": self._window_size,
            "symbols_tracked": len(self._price_history),
            "exchanges_tracked": len(self._exchanges),
            "total_data_points": total_data_points,
            "total_updates": self.total_updates,
            "total_ticks": self.total_ticks,
            "statistical_pairs": len(self.STATISTICAL_PAIRS),
        }


# 全局实例
_history_manager: Optional[PriceHistoryManager] = None


def get_price_history_manager(
    config: Optional[Dict[str, Any]] = None
) -> PriceHistoryManager:
    """获取全局价格历史管理器实例

    Args:
        config: 配置字典

    Returns:
        价格历史管理器实例
    """
    global _history_manager
    if _history_manager is None:
        _history_manager = PriceHistoryManager(config)
    return _history_manager
