"""V34.0 多交易所数据聚合器

V34.0 新增功能 - 多交易所交易机器人:
1. Multi-Exchange Data Aggregator - 多交易所数据聚合
2. Smart Order Router - 智能订单路由
3. Cross-Exchange Arbitrage Engine - 跨交易所套利引擎
4. Deep memo0 Integration - memo0深度集成

创建时间：2026-05-07 20:45
"""

import logging
import time
import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
from collections import defaultdict
import heapq

logger = logging.getLogger(__name__)


class Exchange(Enum):
    """支持的交易所"""
    BINANCE = "binance"
    OKX = "okx"
    BYBIT = "bybit"
    GATE = "gate"
    HUOBI = "huobi"


class MarketRegime(Enum):
    """市场状态"""
    TRENDING = "trending"
    RANGING = "ranging"
    VOLATILE = "volatile"
    CALM = "calm"


@dataclass
class TickerData:
    """交易对数据"""
    symbol: str
    exchange: Exchange
    bid_price: float
    ask_price: float
    bid_volume: float
    ask_volume: float
    last_price: float
    volume_24h: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class AggregatedTicker:
    """聚合后的交易数据"""
    symbol: str
    best_bid: float
    best_ask: float
    best_bid_exchange: Exchange
    best_ask_exchange: Exchange
    spread: float
    spread_pct: float
    total_bid_volume: float
    total_ask_volume: float
    price_change_24h: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class ArbitrageOpportunity:
    """套利机会"""
    symbol: str
    buy_exchange: Exchange
    sell_exchange: Exchange
    buy_price: float
    sell_price: float
    spread: float
    spread_pct: float
    volume: float
    estimated_profit: float
    risk_score: float
    timestamp: float = field(default_factory=time.time)
    ttl: int = 30  # 秒


class MultiExchangeDataAggregator:
    """多交易所数据聚合器

    功能：
    - 统一多交易所数据接口
    - 实时价格聚合
    - 流动性聚合
    - 套利机会检测
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化聚合器

        Args:
            config: 配置字典
                - exchanges: 启用的交易所列表
                - symbols: 关注的交易对
                - update_interval: 更新间隔(秒)
        """
        self.config = config

        # 支持字符串或枚举格式
        exchange_list = config.get('exchanges', ['binance', 'okx', 'bybit'])
        self.enabled_exchanges = []
        for e in exchange_list:
            if isinstance(e, str):
                self.enabled_exchanges.append(Exchange(e))
            else:
                self.enabled_exchanges.append(e)

        self.symbols = config.get('symbols', ['BTC/USDT', 'ETH/USDT'])
        self.update_interval = config.get('update_interval', 1.0)

        # 数据存储
        self.ticker_data: Dict[str, Dict[Exchange, TickerData]] = defaultdict(dict)
        self.aggregated_data: Dict[str, AggregatedTicker] = {}

        # 历史数据
        self.price_history: Dict[str, List[float]] = defaultdict(list)
        self.volume_history: Dict[str, List[float]] = defaultdict(list)

        # 市场状态
        self.market_regime: Dict[str, MarketRegime] = {}

        logger.info(f"[OK] MultiExchangeDataAggregator 初始化完成")
        logger.info(f"    交易所: {[e.value for e in self.enabled_exchanges]}")
        logger.info(f"    交易对: {self.symbols}")

    async def fetch_ticker(self, exchange: Exchange, symbol: str) -> Optional[TickerData]:
        """获取交易对数据

        Args:
            exchange: 交易所
            symbol: 交易对

        Returns:
            TickerData: 交易数据
        """
        # 模拟数据（实际应该调用API）
        base_price = 50000 if 'BTC' in symbol else 3000
        spread = base_price * 0.001  # 0.1% spread

        return TickerData(
            symbol=symbol,
            exchange=exchange,
            bid_price=base_price - spread,
            ask_price=base_price + spread,
            bid_volume=100.0,
            ask_volume=100.0,
            last_price=base_price,
            volume_24h=10000.0,
            timestamp=time.time()
        )

    def aggregate(self, symbol: str) -> Optional[AggregatedTicker]:
        """聚合单个交易对数据

        Args:
            symbol: 交易对

        Returns:
            AggregatedTicker: 聚合数据
        """
        tickers = self.ticker_data.get(symbol, {})
        if not tickers:
            return None

        # 找最佳买卖价
        best_bid = None
        best_ask = None
        best_bid_exchange = None
        best_ask_exchange = None

        for ex, ticker in tickers.items():
            if best_bid is None or ticker.bid_price > best_bid:
                best_bid = ticker.bid_price
                best_bid_exchange = ex

            if best_ask is None or ticker.ask_price < best_ask:
                best_ask = ticker.ask_price
                best_ask_exchange = ex

        if best_bid is None or best_ask is None:
            return None

        spread = best_ask - best_bid
        spread_pct = (spread / best_bid) * 100 if best_bid > 0 else 0

        # 计算总成交量
        total_bid = sum(t.bid_volume for t in tickers.values())
        total_ask = sum(t.ask_volume for t in tickers.values())

        # 价格变化（从历史数据计算）
        last_prices = self.price_history.get(symbol, [])
        price_change = 0.0
        if len(last_prices) >= 2:
            price_change = ((last_prices[-1] - last_prices[0]) / last_prices[0]) * 100

        return AggregatedTicker(
            symbol=symbol,
            best_bid=best_bid,
            best_ask=best_ask,
            best_bid_exchange=best_bid_exchange,
            best_ask_exchange=best_ask_exchange,
            spread=spread,
            spread_pct=spread_pct,
            total_bid_volume=total_bid,
            total_ask_volume=total_ask,
            price_change_24h=price_change,
            timestamp=time.time()
        )

    def detect_arbitrage_opportunity(
        self,
        symbol: str,
        min_spread_pct: float = 0.1,
        min_volume: float = 10.0
    ) -> Optional[ArbitrageOpportunity]:
        """检测套利机会

        Args:
            symbol: 交易对
            min_spread_pct: 最小价差百分比
            min_volume: 最小成交量

        Returns:
            ArbitrageOpportunity: 套利机会
        """
        tickers = self.ticker_data.get(symbol, {})
        if len(tickers) < 2:
            return None

        best_opportunity = None
        max_spread = 0.0

        # 遍历所有交易所组合
        exchanges = list(tickers.keys())
        for i, buy_ex in enumerate(exchanges):
            for sell_ex in exchanges[i+1:]:
                buy_ticker = tickers[buy_ex]
                sell_ticker = tickers[sell_ex]

                # 买入价(低) -> 卖出价(高)
                spread = sell_ticker.ask_price - buy_ticker.bid_price
                spread_pct = (spread / buy_ticker.bid_price) * 100 if buy_ticker.bid_price > 0 else 0

                if spread_pct < min_spread_pct:
                    continue

                volume = min(buy_ticker.bid_volume, sell_ticker.ask_volume)
                if volume < min_volume:
                    continue

                # 计算预期利润 (假设0.1%手续费)
                fee_rate = 0.001
                estimated_profit = spread * volume * (1 - fee_rate * 2)

                # 风险评分 (基于价差稳定性)
                risk_score = 0.3 if spread_pct > 0.5 else 0.6

                if spread_pct > max_spread:
                    max_spread = spread_pct
                    best_opportunity = ArbitrageOpportunity(
                        symbol=symbol,
                        buy_exchange=buy_ex,
                        sell_exchange=sell_ex,
                        buy_price=buy_ticker.bid_price,
                        sell_price=sell_ticker.ask_price,
                        spread=spread,
                        spread_pct=spread_pct,
                        volume=volume,
                        estimated_profit=estimated_profit,
                        risk_score=risk_score,
                        ttl=30
                    )

        return best_opportunity

    def detect_all_opportunities(
        self,
        min_spread_pct: float = 0.1,
        min_volume: float = 10.0
    ) -> List[ArbitrageOpportunity]:
        """检测所有套利机会

        Args:
            min_spread_pct: 最小价差百分比
            min_volume: 最小成交量

        Returns:
            List[ArbitrageOpportunity]: 套利机会列表
        """
        opportunities = []

        for symbol in self.symbols:
            opp = self.detect_arbitrage_opportunity(
                symbol,
                min_spread_pct=min_spread_pct,
                min_volume=min_volume
            )
            if opp:
                opportunities.append(opp)

        # 按利润排序
        opportunities.sort(key=lambda x: x.estimated_profit, reverse=True)

        return opportunities

    def get_best_exchange_for_order(
        self,
        symbol: str,
        side: str
    ) -> Optional[Tuple[Exchange, TickerData]]:
        """获取最佳交易所

        Args:
            symbol: 交易对
            side: 方向 (buy/sell)

        Returns:
            Tuple[Exchange, TickerData]: 最佳交易所和数据
        """
        tickers = self.ticker_data.get(symbol, {})
        if not tickers:
            return None

        if side == "buy":
            # 买 -> 找最低ask
            return min(
                ((ex, t) for ex, t in tickers.items()),
                key=lambda x: x[1].ask_price
            )
        else:
            # 卖 -> 找最高bid
            return max(
                ((ex, t) for ex, t in tickers.items()),
                key=lambda x: x[1].bid_price
            )

    def update_market_state(self, symbol: str, regime: MarketRegime) -> None:
        """更新市场状态

        Args:
            symbol: 交易对
            regime: 市场状态
        """
        self.market_regime[symbol] = regime
        logger.info(f"[OK] 市场状态更新: {symbol} -> {regime.value}")

    def get_liquidity_rankings(
        self,
        symbol: str,
        side: str
    ) -> List[Tuple[Exchange, float]]:
        """获取流动性排名

        Args:
            symbol: 交易对
            side: 方向 (bid/ask)

        Returns:
            List[Tuple[Exchange, float]]: 交易所和流动性
        """
        tickers = self.ticker_data.get(symbol, {})
        if not tickers:
            return []

        if side == "bid":
            return sorted(
                ((ex, t.bid_volume) for ex, t in tickers.items()),
                key=lambda x: x[1],
                reverse=True
            )
        else:
            return sorted(
                ((ex, t.ask_volume) for ex, t in tickers.items()),
                key=lambda x: x[1],
                reverse=True
            )