"""三角套利策略实现"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from strategies.base import BaseStrategy
from tools.exchange_api import get_exchange_manager

logger = logging.getLogger(__name__)


class TriangularArbitrageStrategy(BaseStrategy):
    """三角套利策略 - 利用三种货币间的价格不一致"""

    STRATEGY_NAME = "triangular"
    STRATEGY_DESCRIPTION = "三角套利策略 - 利用三种货币间的价格不一致"

    def __init__(self, config: Dict[str, Any]):
        """初始化三角套利策略

        Args:
            config: 策略配置字典，包含:
                - triangles: 三角套利路径列表
                - min_profit_rate: 最小收益率阈值 (%)
                - max_position_size: 最大仓位大小
                - exchange: 指定交易所（可选，默认扫描所有）
        """
        super().__init__(config)
        self.exchange = config.get('exchange', None)

        # 默认三角套利路径 (USDT为基准货币)
        self.triangles = config.get('triangles', [
            {
                'base': 'USDT',
                'path': [
                    {'from': 'USDT', 'to': 'BTC', 'pair': 'BTC/USDT'},
                    {'from': 'BTC', 'to': 'ETH', 'pair': 'ETH/BTC'},
                    {'from': 'ETH', 'to': 'USDT', 'pair': 'ETH/USDT'}
                ]
            },
            {
                'base': 'USDT',
                'path': [
                    {'from': 'USDT', 'to': 'BTC', 'pair': 'BTC/USDT'},
                    {'from': 'BTC', 'to': 'BNB', 'pair': 'BNB/BTC'},
                    {'from': 'BNB', 'to': 'USDT', 'pair': 'BNB/USDT'}
                ]
            },
            {
                'base': 'USDT',
                'path': [
                    {'from': 'USDT', 'to': 'ETH', 'pair': 'ETH/USDT'},
                    {'from': 'ETH', 'to': 'BNB', 'pair': 'BNB/ETH'},
                    {'from': 'BNB', 'to': 'USDT', 'pair': 'BNB/USDT'}
                ]
            }
        ])

    async def scan_opportunities(self) -> List[Dict[str, Any]]:
        """扫描三角套利机会（统一接口，无参数）

        Returns:
            三角套利机会列表
        """
        exchange_manager = get_exchange_manager()
        if not exchange_manager:
            logger.error("交易所管理器未初始化")
            return []

        # 确定扫描的交易所列表
        if self.exchange:
            exchanges_to_scan = [self.exchange]
        else:
            exchanges_to_scan = list(exchange_manager.exchanges.keys())

        all_opportunities = []

        for exchange_name in exchanges_to_scan:
            try:
                opportunities = await self._scan_exchange(exchange_name, exchange_manager)
                all_opportunities.extend(opportunities)
            except Exception as e:
                logger.error(f"扫描 {exchange_name} 三角套利失败: {e}")

        # 使用基类方法统一过滤和排序
        logger.info(f"发现 {len(all_opportunities)} 个三角套利机会（过滤前）")
        return self._post_process_opportunities(all_opportunities)

    async def _scan_exchange(
        self,
        exchange_name: str,
        exchange_manager
    ) -> List[Dict[str, Any]]:
        """扫描单个交易所的三角套利机会

        Args:
            exchange_name: 交易所名称
            exchange_manager: 交易所管理器

        Returns:
            三角套利机会列表
        """
        opportunities = []

        for triangle in self.triangles:
            try:
                opportunity = await self._scan_triangle(
                    triangle,
                    exchange_name,
                    exchange_manager
                )
                if opportunity and opportunity['profit_rate'] >= self.min_profit_rate:
                    opportunities.append(opportunity)
            except Exception as e:
                logger.error(f"扫描三角套利路径失败: {e}")
                continue

        return opportunities

    async def _scan_triangle(
        self,
        triangle: Dict,
        exchange_name: str,
        exchange_manager
    ) -> Optional[Dict[str, Any]]:
        """扫描单个三角套利路径

        Args:
            triangle: 三角套利路径配置
            exchange_name: 交易所名称
            exchange_manager: 交易所管理器

        Returns:
            三角套利机会字典
        """
        try:
            rates = {}
            fees = {}

            for step in triangle['path']:
                pair = step['pair']

                ticker = await exchange_manager.get_ticker(exchange_name, pair)
                if not ticker:
                    return None

                if step['from'] == pair.split('/')[1]:
                    rates[pair] = {
                        'rate': ticker.get('ask'),
                        'direction': 'buy'
                    }
                else:
                    rates[pair] = {
                        'rate': ticker.get('bid'),
                        'direction': 'sell'
                    }

                fee_info = await exchange_manager.get_trading_fees(exchange_name, pair)
                if fee_info:
                    trading_fee = fee_info.get('trading', {})
                    fees[pair] = {
                        'maker': trading_fee.get('maker', 0.001),
                        'taker': trading_fee.get('taker', 0.001)
                    }

            # 计算三角套利收益
            initial_amount = self.max_position_size
            current_amount = initial_amount

            for i, step in enumerate(triangle['path']):
                pair = step['pair']
                rate_info = rates[pair]
                fee_info = fees.get(pair, {'taker': 0.001})

                if rate_info['direction'] == 'buy':
                    current_amount = current_amount / rate_info['rate'] * (1 - fee_info['taker'])
                else:
                    current_amount = current_amount * rate_info['rate'] * (1 - fee_info['taker'])

            profit = current_amount - initial_amount
            profit_rate = (profit / initial_amount) * 100

            return {
                'symbol': f"{triangle['path'][0]['pair']}-triangular",
                'exchange': exchange_name,
                'triangle': triangle,
                'initial_amount': initial_amount,
                'final_amount': current_amount,
                'profit': profit,
                'profit_rate': profit_rate,
                'is_profitable': profit > 0,
                'strategy': 'triangular',
                'buy_exchange': exchange_name,
                'sell_exchange': exchange_name,
                'amount': initial_amount,
                'expected_profit': profit,
                'timestamp': time.time()
            }

        except Exception as e:
            logger.error(f"计算三角套利失败: {e}")
            return None

    async def execute_arbitrage(self, opportunity: Dict[str, Any]) -> bool:
        """执行三角套利交易

        Args:
            opportunity: 三角套利机会字典

        Returns:
            是否执行成功
        """
        exchange_manager = get_exchange_manager()
        if not exchange_manager:
            logger.error("交易所管理器未初始化")
            return False

        exchange_name = opportunity['exchange']
        triangle = opportunity['triangle']
        initial_amount = opportunity['initial_amount']

        logger.info(f"开始执行三角套利: {exchange_name}")

        try:
            current_amount = initial_amount
            orders = []

            for step in triangle['path']:
                pair = step['pair']
                from_currency = step['from']
                to_currency = step['to']

                if from_currency == pair.split('/')[1]:
                    side = 'buy'
                    amount = current_amount
                else:
                    side = 'sell'
                    # 从订单结果获取实际数量
                    amount = current_amount

                order = await exchange_manager.place_order(
                    exchange_name,
                    pair,
                    'market',
                    side,
                    amount
                )

                if not order:
                    logger.error(f"三角套利第 {len(orders)+1} 步失败")
                    return False

                orders.append(order)

            arbitrage_record = {
                'exchange': exchange_name,
                'triangle': triangle,
                'initial_amount': initial_amount,
                'expected_profit': opportunity['profit'],
                'expected_profit_rate': opportunity['profit_rate'],
                'orders': [order.get('id') for order in orders],
                'status': 'executed',
                'timestamp': time.time()
            }

            self.active_positions.append(arbitrage_record)
            # 交易记录由 safe_execute 的 _record_trade 统一处理，此处不重复记录

            logger.info(f"三角套利执行成功: 预期收益率 {opportunity['profit_rate']:.2f}%")
            return True

        except Exception as e:
            logger.error(f"执行三角套利失败: {e}")
            return False


# ---------------------- 辅助函数 (V29添加) ----------------------

def calculate_triangle_profit(prices: Dict[str, float]) -> Dict[str, float]:
    """计算三角套利利润

    Args:
        prices: 三角路径价格字典 {'pair': price}

    Returns:
        包含profit_rate等信息的字典
    """
    if not prices:
        return {'profit_rate': 0.0, 'theoretical_price': 0.0, 'actual_price': 0.0}

    theoretical_price = 1.0  # 理论价格应为1

    # 提取价格
    usdt_btc = prices.get('BTC/USDT', 0)
    btc_eth = prices.get('ETH/BTC', 0)
    eth_usdt = prices.get('ETH/USDT', 0)

    if usdt_btc <= 0 or btc_eth <= 0 or eth_usdt <= 0:
        return {'profit_rate': 0.0, 'theoretical_price': theoretical_price, 'actual_price': 0.0}

    # 计算实际价格: (1/USDT_BTC) * (1/BTC_ETH) * ETH_USDT
    # 或者直接乘法: 1/USDT_BTC * BTC_ETH * ETH_USDT = 1
    actual_price = (1.0 / usdt_btc) * btc_eth * eth_usdt

    # 利润率 = (实际价格 - 理论价格) / 理论价格 * 100%
    profit_rate = (actual_price - theoretical_price) / theoretical_price * 100

    return {
        'profit_rate': profit_rate,
        'theoretical_price': theoretical_price,
        'actual_price': actual_price,
        'has_opportunity': abs(profit_rate) > 0.01
    }


def is_profitable_triangle(profit_rate: float, min_profit_rate: float = 0.5) -> bool:
    """检查三角套利是否有利可图

    Args:
        profit_rate: 利润率 (%)
        min_profit_rate: 最小利润率阈值 (%)

    Returns:
        是否有利可图
    """
    return profit_rate >= min_profit_rate


