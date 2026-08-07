"""真实市场数据生成器 - Phase 9核心模块

基于真实市场统计特征生成模拟交易数据，用于系统性能验证。

核心功能：
1. K线数据生成 - 基于真实价格统计特征
2. 订单簿模拟 - 深度订单簿生成
3. 交易量模拟 - 真实交易量分布
4. 多市场场景 - 牛市/熊市/震荡/高波动

创建时间：2026-04-19 18:57:00
"""

import json
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class MarketDataGenerator:
    """市场数据生成器

    基于真实市场统计特征生成模拟数据。
    """

    def __init__(self, config: Dict[str, Any] = None):
        """初始化市场数据生成器

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 价格范围（基于真实市场）
        self.price_ranges = {
            'BTC/USDT': (60000, 70000),
            'ETH/USDT': (3000, 4000),
            'BNB/USDT': (500, 700),
            'SOL/USDT': (140, 200),
            'DOGE/USDT': (0.12, 0.18),
        }

        # 波动率（标准差，相对于价格）
        self.volatility_map = {
            'BTC/USDT': 0.02,
            'ETH/USDT': 0.03,
            'BNB/USDT': 0.04,
            'SOL/USDT': 0.05,
            'DOGE/USDT': 0.08,
        }

        # 交易量分布（相对BTC）
        self.volume_multiplier_map = {
            'BTC/USDT': 1.0,
            'ETH/USDT': 1.5,
            'BNB/USDT': 0.8,
            'SOL/USDT': 0.6,
            'DOGE/USDT': 2.0,
        }

        logger.info("市场数据生成器初始化完成")

    def generate_klines(
        self,
        symbol: str,
        count: int,
        interval: str = '1m',
        market_trend: str = 'normal'
    ) -> List[Dict[str, Any]]:
        """生成K线数据

        Args:
            symbol: 交易对符号
            count: 生成数量
            interval: 时间间隔 (1m/5m/15m/1h/4h/1d)
            market_trend: 市场趋势 (bull/bear/normal/volatile)

        Returns:
            K线数据列表
        """
        if symbol not in self.price_ranges:
            logger.warning(f"未知交易对: {symbol}")
            symbol = 'BTC/USDT'

        price_range = self.price_ranges[symbol]
        volatility = self.volatility_map[symbol]

        # 趋势调整
        trend_drift = self._get_trend_drift(market_trend)

        # 初始价格
        base_price = random.uniform(*price_range)

        # 时间间隔转换
        interval_minutes = self._interval_to_minutes(interval)

        klines = []
        current_time = datetime.now() - timedelta(minutes=count * interval_minutes)

        for i in range(count):
            # 随机游走（带趋势）
            price_change = np.random.normal(
                trend_drift * volatility,
                volatility * base_price * 0.01
            )

            base_price = max(base_price + price_change, price_range[0])
            base_price = min(base_price, price_range[1])

            # 生成OHLCV
            high = base_price + abs(np.random.normal(0, volatility * base_price * 0.005))
            low = base_price - abs(np.random.normal(0, volatility * base_price * 0.005))
            open_price = low + random.random() * (high - low)
            close_price = low + random.random() * (high - low)

            # 确保OHLC关系
            high = max(high, open_price, close_price)
            low = min(low, open_price, close_price)

            # 交易量
            volume = self._generate_volume(symbol, base_price)

            kline = {
                'symbol': symbol,
                'timestamp': int(current_time.timestamp() * 1000),
                'open': round(open_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'close': round(close_price, 2),
                'volume': round(volume, 4),
                'interval': interval,
            }

            klines.append(kline)
            current_time += timedelta(minutes=interval_minutes)

        logger.debug(f"生成 {count} 条 {symbol} K线数据 ({market_trend})")
        return klines

    def generate_orderbook(
        self,
        symbol: str,
        depth: int = 20,
        spread_pct: float = 0.05
    ) -> Dict[str, List[Dict[str, Any]]]:
        """生成订单簿数据

        Args:
            symbol: 交易对符号
            depth: 深度（每边订单数量）
            spread_pct: 价差百分比

        Returns:
            订单簿字典
        """
        if symbol not in self.price_ranges:
            symbol = 'BTC/USDT'

        price_range = self.price_ranges[symbol]
        mid_price = random.uniform(*price_range)
        spread = mid_price * (spread_pct / 100)

        # 买单（从mid价格向下）
        bids = []
        bid_price = mid_price - spread / 2
        for i in range(depth):
            price_step = mid_price * 0.0001 * (i + 1)
            price = bid_price - price_step
            amount = self._generate_order_amount(symbol)

            bids.append({
                'price': round(price, 2),
                'amount': round(amount, 4),
                'orders': random.randint(1, 10)
            })

        # 卖单（从mid价格向上）
        asks = []
        ask_price = mid_price + spread / 2
        for i in range(depth):
            price_step = mid_price * 0.0001 * (i + 1)
            price = ask_price + price_step
            amount = self._generate_order_amount(symbol)

            asks.append({
                'price': round(price, 2),
                'amount': round(amount, 4),
                'orders': random.randint(1, 10)
            })

        orderbook = {
            'symbol': symbol,
            'timestamp': int(time.time() * 1000),
            'bids': bids,
            'asks': asks,
            'spread': round(spread, 2),
            'spread_pct': round(spread_pct, 4)
        }

        return orderbook

    def generate_ticker(
        self,
        symbol: str
    ) -> Dict[str, Any]:
        """生成24小时行情数据

        Args:
            symbol: 交易对符号

        Returns:
            行情数据字典
        """
        if symbol not in self.price_ranges:
            symbol = 'BTC/USDT'

        price_range = self.price_ranges[symbol]
        current_price = random.uniform(*price_range)

        # 24小时变化
        price_change_pct = np.random.normal(0, 0.02)
        price_change = current_price * price_change_pct

        high_price = current_price * (1 + abs(price_change_pct) * 0.5)
        low_price = current_price * (1 - abs(price_change_pct) * 0.5)

        ticker = {
            'symbol': symbol,
            'timestamp': int(time.time() * 1000),
            'last': round(current_price, 2),
            'open': round(low_price + random.random() * (current_price - low_price), 2),
            'high': round(high_price, 2),
            'low': round(low_price, 2),
            'volume': round(self._generate_volume(symbol, current_price) * 24, 4),
            'change': round(price_change, 2),
            'change_pct': round(price_change_pct * 100, 2),
        }

        return ticker

    # ========== 辅助方法 ==========

    def _get_trend_drift(self, market_trend: str) -> float:
        """获取趋势漂移

        Args:
            market_trend: 市场趋势

        Returns:
            趋势漂移值
        """
        trend_map = {
            'bull': 0.0005,      # 牛市：价格上涨
            'bear': -0.0005,     # 熊市：价格下跌
            'normal': 0.0,       # 正常：无趋势
            'volatile': 0.0,     # 高波动：随机
        }
        return trend_map.get(market_trend, 0.0)

    def _interval_to_minutes(self, interval: str) -> int:
        """时间间隔转换为分钟

        Args:
            interval: 时间间隔字符串

        Returns:
            分钟数
        """
        interval_map = {
            '1m': 1,
            '5m': 5,
            '15m': 15,
            '30m': 30,
            '1h': 60,
            '4h': 240,
            '1d': 1440,
        }
        return interval_map.get(interval, 1)

    def _generate_volume(self, symbol: str, price: float) -> float:
        """生成交易量

        Args:
            symbol: 交易对符号
            price: 当前价格

        Returns:
            交易量
        """
        multiplier = self.volume_multiplier_map.get(symbol, 1.0)

        # 对数正态分布
        volume_base = np.random.lognormal(mean=np.log(100 * multiplier), sigma=0.5)

        # 根据价格调整
        volume_adjusted = volume_base * (100000 / price)

        return round(volume_adjusted, 4)

    def _generate_order_amount(self, symbol: str) -> float:
        """生成订单数量

        Args:
            symbol: 交易对符号

        Returns:
            订单数量
        """
        multiplier = self.volume_multiplier_map.get(symbol, 1.0)

        # 指数分布
        amount = np.random.exponential(scale=10 * multiplier)

        return round(amount, 4)


class PriceSpreadSimulator:
    """价差模拟器

    模拟各种套利场景的价差数据。
    """

    def __init__(self, config: Dict[str, Any] = None):
        """初始化价差模拟器

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 交易所列表
        self.exchanges = ['binance', 'okx', 'huobi', 'bybit', 'gate']

        # 价差范围（百分比）
        self.cross_exchange_spread_range = (0.01, 0.5)  # 0.01% - 0.5%

        # 三角套利利润范围
        self.triangular_profit_range = (0.05, 0.8)  # 0.05% - 0.8%

        logger.info("价差模拟器初始化完成")

    def simulate_cross_exchange_arbitrage(
        self,
        symbol: str,
        count: int,
        spread_range: Tuple[float, float] = None
    ) -> List[Dict[str, Any]]:
        """模拟跨交易所套利

        Args:
            symbol: 交易对符号
            count: 生成数量
            spread_range: 价差范围（百分比）

        Returns:
            套利机会列表
        """
        if spread_range is None:
            spread_range = self.cross_exchange_spread_range

        opportunities = []
        generator = MarketDataGenerator()

        for _ in range(count):
            # 选择两个交易所
            exchange_pair = random.sample(self.exchanges, 2)

            # 获取基础价格
            base_price = generator.generate_ticker(symbol)['last']

            # 计算价差
            spread_pct = random.uniform(*spread_range)
            spread_amount = base_price * (spread_pct / 100)

            # 确定买卖方向
            if random.random() > 0.5:
                buy_exchange = exchange_pair[0]
                sell_exchange = exchange_pair[1]
                buy_price = base_price
                sell_price = base_price + spread_amount
            else:
                buy_exchange = exchange_pair[1]
                sell_exchange = exchange_pair[0]
                buy_price = base_price
                sell_price = base_price + spread_amount

            profit_rate = ((sell_price - buy_price) / buy_price) * 100

            opportunity = {
                'type': 'cross_exchange',
                'symbol': symbol,
                'buy_exchange': buy_exchange,
                'sell_exchange': sell_exchange,
                'buy_price': round(buy_price, 2),
                'sell_price': round(sell_price, 2),
                'spread': round(spread_amount, 2),
                'spread_pct': round(spread_pct, 4),
                'profit_rate': round(profit_rate, 4),
                'timestamp': int(time.time() * 1000),
            }

            opportunities.append(opportunity)

        logger.debug(f"生成 {count} 条跨交易所套利机会")
        return opportunities

    def simulate_triangular_arbitrage(
        self,
        triangle: List[str],
        count: int,
        profit_range: Tuple[float, float] = None
    ) -> List[Dict[str, Any]]:
        """模拟三角套利

        Args:
            triangle: 三角路径 [A, B, C]
            count: 生成数量
            profit_range: 利润范围（百分比）

        Returns:
            套利机会列表
        """
        if len(triangle) != 3:
            raise ValueError("三角路径必须包含3个币种")

        if profit_range is None:
            profit_range = self.triangular_profit_range

        opportunities = []
        generator = MarketDataGenerator()

        for _ in range(count):
            # 获取基础价格
            prices = {}
            for i in range(3):
                pair = f"{triangle[i]}/{triangle[(i+1)%3]}"
                ticker = generator.generate_ticker(pair)
                prices[pair] = ticker['last']

            # 计算三角套利利润
            # 假设起始100 USDT
            start_amount = 100.0

            # 路径1: USDT -> A -> B -> USDT
            amount1 = start_amount / prices[f"{triangle[0]}/{triangle[1]}"]
            amount2 = amount1 * prices[f"{triangle[1]}/{triangle[2]}"]
            final_amount = amount2 * prices[f"{triangle[2]}/{triangle[0]}"]

            profit_rate = ((final_amount - start_amount) / start_amount) * 100

            # 确保在指定范围内
            if profit_rate < profit_range[0] or profit_rate > profit_range[1]:
                # 调整价格
                adjustment = random.uniform(-0.001, 0.001)
                prices[f"{triangle[1]}/{triangle[2]}"] *= (1 + adjustment)
                final_amount = amount2 * prices[f"{triangle[2]}/{triangle[0]}"]
                profit_rate = ((final_amount - start_amount) / start_amount) * 100

            opportunity = {
                'type': 'triangular',
                'triangle': triangle,
                'path': f"{triangle[0]} -> {triangle[1]} -> {triangle[2]} -> {triangle[0]}",
                'prices': prices,
                'start_amount': start_amount,
                'final_amount': round(final_amount, 4),
                'profit': round(final_amount - start_amount, 4),
                'profit_rate': round(profit_rate, 4),
                'timestamp': int(time.time() * 1000),
            }

            opportunities.append(opportunity)

        logger.debug(f"生成 {count} 条三角套利机会")
        return opportunities

    def simulate_funding_rate_arbitrage(
        self,
        symbol: str,
        count: int,
        rate_range: Tuple[float, float] = (0.01, 0.5)
    ) -> List[Dict[str, Any]]:
        """模拟资金费率套利

        Args:
            symbol: 交易对符号
            count: 生成数量
            rate_range: 费率范围（百分比）

        Returns:
            套利机会列表
        """
        opportunities = []

        for _ in range(count):
            # 资金费率
            funding_rate = random.uniform(*rate_range) / 100

            # 市场价格
            generator = MarketDataGenerator()
            spot_price = generator.generate_ticker(symbol)['last']
            futures_price = spot_price * (1 + funding_rate * 0.5)

            opportunity = {
                'type': 'funding_rate',
                'symbol': symbol,
                'spot_price': round(spot_price, 2),
                'futures_price': round(futures_price, 2),
                'funding_rate': round(funding_rate * 100, 4),
                'expected_daily_profit': round(spot_price * funding_rate, 4),
                'timestamp': int(time.time() * 1000),
            }

            opportunities.append(opportunity)

        logger.debug(f"生成 {count} 条资金费率套利机会")
        return opportunities


class TradingScenarioBuilder:
    """交易场景构建器

    构建完整的交易场景，用于端到端测试。
    """

    def __init__(self, config: Dict[str, Any] = None):
        """初始化场景构建器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.market_generator = MarketDataGenerator()
        self.spread_simulator = PriceSpreadSimulator()

        logger.info("交易场景构建器初始化完成")

    def build_bull_market_scenario(
        self,
        duration_hours: int = 24,
        symbols: List[str] = None
    ) -> Dict[str, Any]:
        """构建牛市场景

        Args:
            duration_hours: 持续时间（小时）
            symbols: 交易对列表

        Returns:
            场景数据字典
        """
        if symbols is None:
            symbols = ['BTC/USDT', 'ETH/USDT']

        scenario = {
            'type': 'bull_market',
            'duration_hours': duration_hours,
            'timestamp': datetime.now().isoformat(),
            'data': {}
        }

        # 生成K线数据
        for symbol in symbols:
            klines_count = duration_hours * 60  # 1分钟K线
            klines = self.market_generator.generate_klines(
                symbol=symbol,
                count=klines_count,
                interval='1m',
                market_trend='bull'
            )
            scenario['data'][symbol] = {
                'klines': klines,
                'ticker': self.market_generator.generate_ticker(symbol),
                'orderbook': self.market_generator.generate_orderbook(symbol),
            }

        # 生成套利机会
        arbitrage_opportunities = []
        for symbol in symbols:
            arbitrage_opportunities.extend(
                self.spread_simulator.simulate_cross_exchange_arbitrage(
                    symbol=symbol,
                    count=10
                )
            )
        scenario['arbitrage'] = arbitrage_opportunities

        logger.info(f"构建牛市场景: {duration_hours}小时, {len(symbols)}个交易对")
        return scenario

    def build_bear_market_scenario(
        self,
        duration_hours: int = 24,
        symbols: List[str] = None
    ) -> Dict[str, Any]:
        """构建熊市场景

        Args:
            duration_hours: 持续时间（小时）
            symbols: 交易对列表

        Returns:
            场景数据字典
        """
        if symbols is None:
            symbols = ['BTC/USDT', 'ETH/USDT']

        scenario = {
            'type': 'bear_market',
            'duration_hours': duration_hours,
            'timestamp': datetime.now().isoformat(),
            'data': {}
        }

        # 生成K线数据
        for symbol in symbols:
            klines_count = duration_hours * 60  # 1分钟K线
            klines = self.market_generator.generate_klines(
                symbol=symbol,
                count=klines_count,
                interval='1m',
                market_trend='bear'
            )
            scenario['data'][symbol] = {
                'klines': klines,
                'ticker': self.market_generator.generate_ticker(symbol),
                'orderbook': self.market_generator.generate_orderbook(symbol),
            }

        # 生成套利机会
        arbitrage_opportunities = []
        for symbol in symbols:
            arbitrage_opportunities.extend(
                self.spread_simulator.simulate_cross_exchange_arbitrage(
                    symbol=symbol,
                    count=10
                )
            )
        scenario['arbitrage'] = arbitrage_opportunities

        logger.info(f"构建熊市场景: {duration_hours}小时, {len(symbols)}个交易对")
        return scenario

    def build_sideways_scenario(
        self,
        duration_hours: int = 24,
        symbols: List[str] = None
    ) -> Dict[str, Any]:
        """构建震荡市场场景

        Args:
            duration_hours: 持续时间（小时）
            symbols: 交易对列表

        Returns:
            场景数据字典
        """
        if symbols is None:
            symbols = ['BTC/USDT', 'ETH/USDT']

        scenario = {
            'type': 'sideways_market',
            'duration_hours': duration_hours,
            'timestamp': datetime.now().isoformat(),
            'data': {}
        }

        # 生成K线数据
        for symbol in symbols:
            klines_count = duration_hours * 60  # 1分钟K线
            klines = self.market_generator.generate_klines(
                symbol=symbol,
                count=klines_count,
                interval='1m',
                market_trend='normal'
            )
            scenario['data'][symbol] = {
                'klines': klines,
                'ticker': self.market_generator.generate_ticker(symbol),
                'orderbook': self.market_generator.generate_orderbook(symbol),
            }

        # 生成套利机会
        arbitrage_opportunities = []
        for symbol in symbols:
            arbitrage_opportunities.extend(
                self.spread_simulator.simulate_cross_exchange_arbitrage(
                    symbol=symbol,
                    count=10
                )
            )
        scenario['arbitrage'] = arbitrage_opportunities

        logger.info(f"构建震荡市场场景: {duration_hours}小时, {len(symbols)}个交易对")
        return scenario

    def build_volatile_scenario(
        self,
        duration_hours: int = 24,
        symbols: List[str] = None
    ) -> Dict[str, Any]:
        """构建高波动场景

        Args:
            duration_hours: 持续时间（小时）
            symbols: 交易对列表

        Returns:
            场景数据字典
        """
        if symbols is None:
            symbols = ['BTC/USDT', 'ETH/USDT', 'DOGE/USDT']

        scenario = {
            'type': 'volatile_market',
            'duration_hours': duration_hours,
            'timestamp': datetime.now().isoformat(),
            'data': {}
        }

        # 生成K线数据
        for symbol in symbols:
            klines_count = duration_hours * 60  # 1分钟K线
            klines = self.market_generator.generate_klines(
                symbol=symbol,
                count=klines_count,
                interval='1m',
                market_trend='volatile'
            )
            scenario['data'][symbol] = {
                'klines': klines,
                'ticker': self.market_generator.generate_ticker(symbol),
                'orderbook': self.market_generator.generate_orderbook(symbol, depth=30),
            }

        # 生成套利机会（更多）
        arbitrage_opportunities = []
        for symbol in symbols:
            arbitrage_opportunities.extend(
                self.spread_simulator.simulate_cross_exchange_arbitrage(
                    symbol=symbol,
                    count=20,
                    spread_range=(0.1, 1.0)  # 更大的价差
                )
            )
        scenario['arbitrage'] = arbitrage_opportunities

        # 生成三角套利
        triangles = [
            ['USDT', 'BTC', 'ETH'],
            ['USDT', 'BTC', 'BNB'],
        ]
        for triangle in triangles:
            triangle_opportunities = self.spread_simulator.simulate_triangular_arbitrage(
                triangle=triangle,
                count=10
            )
            scenario['arbitrage'].extend(triangle_opportunities)

        logger.info(f"构建高波动场景: {duration_hours}小时, {len(symbols)}个交易对")
        return scenario

    def export_scenario(self, scenario: Dict[str, Any], filepath: str) -> None:
        """导出场景数据

        Args:
            scenario: 场景数据字典
            filepath: 导出文件路径
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(scenario, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"场景数据已导出到: {filepath}")


# ========== 便捷函数 ==========

def create_market_generator(config: Dict[str, Any] = None) -> MarketDataGenerator:
    """创建市场数据生成器

    Args:
        config: 配置字典

    Returns:
        市场数据生成器实例
    """
    return MarketDataGenerator(config)


def create_spread_simulator(config: Dict[str, Any] = None) -> PriceSpreadSimulator:
    """创建价差模拟器

    Args:
        config: 配置字典

    Returns:
        价差模拟器实例
    """
    return PriceSpreadSimulator(config)


def create_scenario_builder(config: Dict[str, Any] = None) -> TradingScenarioBuilder:
    """创建场景构建器

    Args:
        config: 配置字典

    Returns:
        场景构建器实例
    """
    return TradingScenarioBuilder(config)
