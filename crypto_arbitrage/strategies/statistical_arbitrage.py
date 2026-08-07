"""统计套利策略实现

利用历史价格数据中的统计关系（如均值回归、协整关系）进行套利。
当两个相关资产的价格偏离历史均值时，做空被高估的资产，做多被低估的资产，
等待价格回归均值获利。
"""

import asyncio
import logging
import math
import time
from collections import deque
from typing import Any, Dict, List, Optional, Tuple

from strategies.base import BaseStrategy
from tools.exchange_api import get_exchange_manager

logger = logging.getLogger(__name__)


class StatisticalArbitrageStrategy(BaseStrategy):
    """统计套利策略"""

    STRATEGY_NAME = "statistical_arbitrage"
    STRATEGY_DESCRIPTION = "统计套利策略 - 利用历史价格关系的均值回归"

    def __init__(self, config: Dict[str, Any]):
        """初始化统计套利策略

        Args:
            config: 策略配置字典，包含:
                - min_profit_rate: 最小收益率阈值 (%)
                - max_position_size: 最大仓位大小 ($)
                - pairs: 交易对配对列表
                - lookback_period: 回溯期（数据点数量）
                - z_score_threshold: Z分数开仓阈值
                - z_score_close: Z分数平仓阈值
                - max_holding_period: 最大持仓时间（秒）
                - preferred_exchange: 首选交易所
        """
        # V1.7.0 Fix: 先设置子类属性，再调 super().__init__()
        self.lookback_period = config.get('lookback_period', 100)
        self.z_score_threshold = config.get('z_score_threshold', 2.0)
        self.z_score_close = config.get('z_score_close', 0.5)
        self.max_holding_period = config.get('max_holding_period', 86400)
        self.preferred_exchange = config.get('preferred_exchange', None)

        # 交易对配对
        self.pairs = config.get('pairs', [
            {'asset1': 'BTC/USDT', 'asset2': 'ETH/USDT', 'name': 'BTC-ETH'},
            {'asset1': 'BTC/USDT', 'asset2': 'SOL/USDT', 'name': 'BTC-SOL'},
        ])

        # 价格历史数据
        self._price_history: Dict[str, deque] = {}
        max_history = self.lookback_period * 2
        for pair in self.pairs:
            self._price_history[pair['asset1']] = deque(maxlen=max_history)
            self._price_history[pair['asset2']] = deque(maxlen=max_history)

        super().__init__(config)

    def _get_exchange_name(self, exchange_manager) -> Optional[str]:
        """获取首选交易所，避免硬编码交易所"""
        if self.preferred_exchange and self.preferred_exchange in exchange_manager.exchanges:
            return self.preferred_exchange
        for name in exchange_manager.exchanges:
            return name
        return None

    async def scan_opportunities(self) -> List[Dict[str, Any]]:
        """扫描统计套利机会"""
        exchange_manager = get_exchange_manager()
        if not exchange_manager:
            logger.error("交易所管理器未初始化")
            return []

        opportunities = []

        # 更新价格数据
        await self._update_price_data(exchange_manager)

        for pair_config in self.pairs:
            try:
                opportunity = self._analyze_pair(pair_config)
                if opportunity:
                    opportunities.append(opportunity)
            except Exception as e:
                logger.error(f"分析配对 {pair_config['name']} 失败: {e}")

        # 使用基类方法统一过滤和排序
        logger.info(f"发现 {len(opportunities)} 个统计套利机会（过滤前）")
        return self._post_process_opportunities(opportunities, sort_key='z_score')

    async def _update_price_data(self, exchange_manager) -> None:
        """更新价格历史数据"""
        ex_name = self._get_exchange_name(exchange_manager)
        if not ex_name:
            return

        all_symbols = set()
        for pair in self.pairs:
            all_symbols.add(pair['asset1'])
            all_symbols.add(pair['asset2'])

        for symbol in all_symbols:
            try:
                ticker = await exchange_manager.get_ticker(ex_name, symbol)
                if ticker and ticker.get('last'):
                    self._price_history[symbol].append({
                        'price': ticker['last'],
                        'timestamp': time.time()
                    })
            except Exception as e:
                logger.debug(f"更新 {symbol} 价格失败: {e}")

    def _analyze_pair(self, pair_config: Dict) -> Optional[Dict[str, Any]]:
        """分析配对的统计套利机会"""
        asset1 = pair_config['asset1']
        asset2 = pair_config['asset2']
        pair_name = pair_config['name']

        history1 = self._price_history.get(asset1, deque())
        history2 = self._price_history.get(asset2, deque())

        if len(history1) < self.lookback_period or len(history2) < self.lookback_period:
            logger.debug(f"{pair_name} 数据不足: {len(history1)}/{len(history2)} < {self.lookback_period}")
            return None

        prices1 = [p['price'] for p in list(history1)[-self.lookback_period:]]
        prices2 = [p['price'] for p in list(history2)[-self.lookback_period:]]

        spread = self._calculate_spread(prices1, prices2)
        if not spread:
            return None

        mean_spread, std_spread, current_spread, z_score = spread

        if abs(z_score) < self.z_score_threshold:
            logger.debug(f"{pair_name} Z-score {z_score:.2f} 未达阈值 {self.z_score_threshold}")
            return None

        if z_score > 0:
            direction = "short_asset1_long_asset2"
            short_asset = asset1
            long_asset = asset2
        else:
            direction = "long_asset1_short_asset2"
            short_asset = asset2
            long_asset = asset1

        current_prices = {
            asset1: history1[-1]['price'],
            asset2: history2[-1]['price']
        }

        # 计算预期收益
        expected_ratio_reversion = abs(z_score - self.z_score_close) * std_spread
        current_ratio = current_spread
        if current_ratio > 0:
            expected_profit_rate = (expected_ratio_reversion / current_ratio) * 100
        else:
            expected_profit_rate = 0

        if expected_profit_rate < self.min_profit_rate:
            logger.debug(f"{pair_name} 预期收益率过低: {expected_profit_rate:.3f}%")
            return None

        half_position = self.max_position_size / 2
        long_amount = half_position / current_prices[long_asset]
        short_amount = half_position / current_prices[short_asset]

        half_life = self._calculate_half_life(prices1, prices2)

        # 检查是否已有该配对的持仓
        existing = [p for p in self.active_positions
                    if p.get('pair_name') == pair_name and p.get('status') == 'open']
        if existing:
            logger.debug(f"{pair_name} 已有持仓，跳过")
            return None

        opportunity = {
            'symbol': pair_name,
            'asset1': asset1,
            'asset2': asset2,
            'direction': direction,
            'long_asset': long_asset,
            'short_asset': short_asset,
            'z_score': z_score,
            'mean_spread': mean_spread,
            'std_spread': std_spread,
            'current_spread': current_spread,
            'expected_profit_rate': expected_profit_rate,
            'half_life': half_life,
            'long_price': current_prices[long_asset],
            'short_price': current_prices[short_asset],
            'long_amount': long_amount,
            'short_amount': short_amount,
            'position_value': self.max_position_size,
            'profit_rate': expected_profit_rate,
            'expected_profit': half_position * (expected_profit_rate / 100),
            'timestamp': time.time()
        }

        logger.info(
            f"统计套利机会: {pair_name} z_score={z_score:.2f} "
            f"方向={direction} 预期收益={expected_profit_rate:.3f}% "
            f"半衰期={half_life:.1f}h"
        )

        return opportunity

    def _calculate_spread(
        self,
        prices1: List[float],
        prices2: List[float]
    ) -> Optional[Tuple[float, float, float, float]]:
        """计算价格比率及其统计特征"""
        if len(prices1) != len(prices2) or len(prices1) < 2:
            return None

        ratios = []
        for p1, p2 in zip(prices1, prices2):
            if p2 > 0:
                ratios.append(p1 / p2)

        if len(ratios) < 2:
            return None

        recent_ratios = ratios[-self.lookback_period:]

        n = len(recent_ratios)
        mean_ratio = sum(recent_ratios) / n
        variance = sum((r - mean_ratio) ** 2 for r in recent_ratios) / (n - 1)
        std_ratio = math.sqrt(variance) if variance > 0 else 0

        if std_ratio == 0:
            return None

        current_ratio = recent_ratios[-1]
        z_score = (current_ratio - mean_ratio) / std_ratio

        return (mean_ratio, std_ratio, current_ratio, z_score)

    def _calculate_half_life(self, prices1: List[float], prices2: List[float]) -> float:
        """计算均值回归的半衰期（小时）"""
        try:
            spreads = []
            for p1, p2 in zip(prices1, prices2):
                if p2 > 0:
                    spreads.append(math.log(p1 / p2))

            if len(spreads) < 10:
                return 24.0

            y = spreads[1:]
            x = spreads[:-1]

            n = len(y)
            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(xi * yi for xi, yi in zip(x, y))
            sum_x2 = sum(xi ** 2 for xi in x)

            denom = n * sum_x2 - sum_x ** 2
            if denom == 0:
                return 24.0

            slope = (n * sum_xy - sum_x * sum_y) / denom

            if slope >= 1 or slope <= -1:
                return 24.0

            theta = -math.log(slope)
            if theta <= 0:
                return 24.0

            half_life = math.log(2) / theta
            return max(1.0, min(half_life, 168.0))

        except Exception:
            return 24.0

    async def execute_arbitrage(self, opportunity: Dict[str, Any]) -> bool:
        """执行统计套利交易"""
        exchange_manager = get_exchange_manager()
        if not exchange_manager:
            logger.error("交易所管理器未初始化")
            return False

        long_asset = opportunity['long_asset']
        short_asset = opportunity['short_asset']
        long_amount = opportunity['long_amount']
        short_amount = opportunity['short_amount']

        # Fix: 使用 preferred_exchange 代替硬编码
        ex_name = self._get_exchange_name(exchange_manager)
        if not ex_name:
            logger.error("无可用交易所")
            return False

        logger.info(
            f"开始执行统计套利: {opportunity['symbol']} "
            f"做多{long_asset} 做空{short_asset}"
        )

        try:
            # 并发开仓
            long_order, short_order = await asyncio.gather(
                exchange_manager.place_order(ex_name, long_asset, 'market', 'buy', long_amount),
                exchange_manager.place_order(ex_name, short_asset, 'market', 'sell', short_amount)
            )

            if not long_order or not short_order:
                logger.error("统计套利开仓失败")
                if long_order and not short_order:
                    await exchange_manager.place_order(
                        ex_name, long_asset, 'market', 'sell', long_amount
                    )
                elif short_order and not long_order:
                    await exchange_manager.place_order(
                        ex_name, short_asset, 'market', 'buy', short_amount
                    )
                return False

            position = {
                'pair_name': opportunity['symbol'],
                'asset1': opportunity['asset1'],
                'asset2': opportunity['asset2'],
                'direction': opportunity['direction'],
                'long_asset': long_asset,
                'short_asset': short_asset,
                'long_order_id': long_order.get('id'),
                'short_order_id': short_order.get('id'),
                'long_amount': long_amount,
                'short_amount': short_amount,
                'entry_z_score': opportunity['z_score'],
                'expected_profit_rate': opportunity['expected_profit_rate'],
                'half_life': opportunity['half_life'],
                'status': 'open',
                'open_time': time.time(),
                'timestamp': time.time()
            }

            self.active_positions.append(position)
            logger.info(f"统计套利开仓成功: {opportunity['symbol']}")
            return True

        except Exception as e:
            logger.error(f"统计套利执行失败: {e}")
            return False

    async def monitor_positions(self) -> List[Dict[str, Any]]:
        """监控持仓，检查是否应该平仓"""
        close_list = []

        for position in self.active_positions:
            if position.get('status') != 'open':
                continue

            asset1 = position['asset1']
            asset2 = position['asset2']

            history1 = self._price_history.get(asset1, deque())
            history2 = self._price_history.get(asset2, deque())

            if len(history1) < 20 or len(history2) < 20:
                continue

            prices1 = [p['price'] for p in list(history1)[-self.lookback_period:]]
            prices2 = [p['price'] for p in list(history2)[-self.lookback_period:]]

            spread_info = self._calculate_spread(prices1, prices2)
            if not spread_info:
                continue

            _, _, _, current_z_score = spread_info
            entry_z = position['entry_z_score']

            should_close = False
            close_reason = ""

            if abs(current_z_score) < self.z_score_close:
                should_close = True
                close_reason = f"Z-score回归: {current_z_score:.2f} < {self.z_score_close}"

            if abs(current_z_score) > abs(entry_z) * 1.5:
                should_close = True
                close_reason = f"Z-score扩大: {current_z_score:.2f} > {abs(entry_z) * 1.5:.2f}"

            holding_time = time.time() - position['open_time']
            if holding_time > self.max_holding_period:
                should_close = True
                close_reason = f"超过最大持仓时间: {holding_time / 3600:.1f}h"

            if should_close:
                close_list.append({
                    'position': position,
                    'reason': close_reason,
                    'current_z_score': current_z_score
                })

        return close_list

    async def close_position(self, position: Dict[str, Any]) -> bool:
        """关闭持仓"""
        exchange_manager = get_exchange_manager()
        if not exchange_manager:
            return False

        try:
            # Fix: 使用 preferred_exchange 代替硬编码
            ex_name = self._get_exchange_name(exchange_manager)
            if not ex_name:
                logger.error("无可用交易所")
                return False

            # 反向平仓
            await asyncio.gather(
                exchange_manager.place_order(
                    ex_name, position['long_asset'], 'market', 'sell', position['long_amount']
                ),
                exchange_manager.place_order(
                    ex_name, position['short_asset'], 'market', 'buy', position['short_amount']
                )
            )

            position['status'] = 'closed'
            position['close_time'] = time.time()
            position['holding_hours'] = (position['close_time'] - position['open_time']) / 3600

            logger.info(f"统计套利持仓已关闭: {position['pair_name']}")
            return True

        except Exception as e:
            logger.error(f"关闭统计套利持仓失败: {e}")
            return False
