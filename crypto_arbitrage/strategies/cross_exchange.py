"""跨交易所套利策略实现"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from strategies.base import BaseStrategy
from tools.exchange_api import ArbitrageCalculator, get_exchange_manager

logger = logging.getLogger(__name__)


class CrossExchangeArbitrageStrategy(BaseStrategy):
    """跨交易所套利策略 - 利用不同交易所间的价格差异"""

    STRATEGY_NAME = "cross_exchange"
    STRATEGY_DESCRIPTION = "跨交易所套利策略 - 利用不同交易所间的价格差异"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.risk_tolerance = config.get('risk_tolerance', 0.1)
        self.symbols = config.get('symbols', ['BTC/USDT', 'ETH/USDT'])

    async def scan_opportunities(self) -> List[Dict[str, Any]]:
        """扫描套利机会

        Returns:
            套利机会列表，按收益率排序
        """
        exchange_manager = get_exchange_manager()
        if not exchange_manager:
            logger.error("交易所管理器未初始化")
            return []

        opportunities = []

        for symbol in self.symbols:
            try:
                symbol_opportunities = await self._scan_symbol_opportunities(
                    symbol, exchange_manager
                )
                opportunities.extend(symbol_opportunities)
            except Exception as e:
                logger.error(f"扫描 {symbol} 套利机会失败: {e}")

        # 使用基类方法统一过滤和排序
        logger.info(f"发现 {len(opportunities)} 个套利机会（过滤前）")
        return self._post_process_opportunities(opportunities)

    async def _scan_symbol_opportunities(
        self,
        symbol: str,
        exchange_manager
    ) -> List[Dict[str, Any]]:
        """扫描单个交易对的套利机会"""
        opportunities = []
        prices = {}
        fees = {}

        for exchange_name in exchange_manager.exchanges.keys():
            try:
                ticker = await exchange_manager.get_ticker(exchange_name, symbol)
                if ticker:
                    prices[exchange_name] = {
                        'bid': ticker.get('bid'),
                        'ask': ticker.get('ask'),
                        'last': ticker.get('last')
                    }

                fee_info = await exchange_manager.get_trading_fees(exchange_name, symbol)
                if fee_info:
                    trading_fee = fee_info.get('trading', {})
                    fees[exchange_name] = {
                        'maker': trading_fee.get('maker', 0.001),
                        'taker': trading_fee.get('taker', 0.001)
                    }

            except Exception as e:
                logger.warning(f"获取 {exchange_name} {symbol} 数据失败: {e}")
                continue

        for buy_exchange in prices:
            for sell_exchange in prices:
                if buy_exchange == sell_exchange:
                    continue

                try:
                    buy_price = prices[buy_exchange]['ask']
                    sell_price = prices[sell_exchange]['bid']

                    if not buy_price or not sell_price:
                        continue

                    buy_fee = fees.get(buy_exchange, {}).get('taker', 0.001)
                    sell_fee = fees.get(sell_exchange, {}).get('taker', 0.001)

                    amount = min(
                        self.max_position_size / buy_price,
                        self.max_position_size / sell_price
                    )

                    arbitrage_result = ArbitrageCalculator.calculate_cross_exchange_arbitrage(
                        buy_exchange,
                        sell_exchange,
                        buy_price,
                        sell_price,
                        buy_fee,
                        sell_fee,
                        amount
                    )

                    arbitrage_result['symbol'] = symbol
                    arbitrage_result['price_spread'] = sell_price - buy_price
                    arbitrage_result['spread_rate'] = ((sell_price - buy_price) / buy_price) * 100
                    arbitrage_result['timestamp'] = time.time()

                    opportunities.append(arbitrage_result)

                except Exception as e:
                    logger.error(f"计算 {buy_exchange}->{sell_exchange} 套利失败: {e}")
                    continue

        return opportunities

    async def execute_arbitrage(self, opportunity: Dict[str, Any]) -> bool:
        """执行套利交易"""
        exchange_manager = get_exchange_manager()
        if not exchange_manager:
            logger.error("交易所管理器未初始化")
            return False

        symbol = opportunity['symbol']
        buy_exchange = opportunity['buy_exchange']
        sell_exchange = opportunity['sell_exchange']
        amount = opportunity['amount']

        logger.info(f"开始执行套利: {symbol} {buy_exchange}->{sell_exchange}")

        try:
            # BUG FIX #1: 顺序执行而非并发 - 跨交易所时两边余额独立，
            # 并发可能导致一边余额不足。先买后卖更安全。
            buy_order = await exchange_manager.place_order(
                buy_exchange, symbol, 'market', 'buy', amount
            )

            if not buy_order:
                logger.error("买入订单执行失败")
                return False

            sell_order = await exchange_manager.place_order(
                sell_exchange, symbol, 'market', 'sell', amount
            )

            if not sell_order:
                logger.error("卖出订单执行失败，买入单已成交需手动处理")
                return False

            arbitrage_record = {
                'symbol': symbol,
                'buy_exchange': buy_exchange,
                'sell_exchange': sell_exchange,
                'amount': amount,
                'expected_profit': opportunity['profit'],
                'expected_profit_rate': opportunity['profit_rate'],
                'buy_order_id': buy_order.get('id'),
                'sell_order_id': sell_order.get('id'),
                'status': 'executed',
                'timestamp': time.time()
            }

            self.active_positions.append(arbitrage_record)
            # 交易记录由 safe_execute 的 _record_trade 统一处理，此处不重复记录

            logger.info(f"套利执行成功: 预期收益率 {opportunity['profit_rate']:.2f}%")
            return True

        except Exception as e:
            logger.error(f"执行套利失败: {e}")
            return False



class LowRiskArbitrageFilter:
    """低风险套利过滤器"""

    @staticmethod
    def filter_opportunities(
        opportunities: List[Dict],
        max_volatility: float = 5.0,
        min_liquidity: float = 10000,
        max_slippage: float = 0.1
    ) -> List[Dict]:
        """过滤高风险的套利机会"""
        filtered = []

        for opp in opportunities:
            try:
                if opp.get('spread_rate', 0) > max_volatility:
                    continue

                if opp.get('profit_rate', 0) > 10:
                    continue

                if opp.get('buy_cost', 0) > min_liquidity * 2:
                    continue

                filtered.append(opp)

            except Exception as e:
                logger.warning(f"过滤套利机会时出错: {e}")
                continue

        logger.info(f"过滤后剩余 {len(filtered)} 个低风险套利机会")
        return filtered

    @staticmethod
    def calculate_risk_score(opportunity: Dict) -> float:
        """计算套利机会的风险评分 (0-100, 越低越安全)"""
        risk_score = 0

        profit_rate = opportunity.get('profit_rate', 0)
        risk_score += min(profit_rate * 5, 30)

        spread_rate = opportunity.get('spread_rate', 0)
        risk_score += min(spread_rate * 3, 20)

        buy_cost = opportunity.get('buy_cost', 0)
        risk_score += min(buy_cost / 1000 * 2, 20)

        return min(risk_score, 100)


# ---------------------- 辅助函数 (V29添加) ----------------------

def calculate_cross_exchange_spread(price_a: dict, price_b: dict) -> float:
    """计算跨交易所价差

    Args:
        price_a: 交易所A价格 {'bid': float, 'ask': float}
        price_b: 交易所B价格 {'bid': float, 'ask': float}

    Returns:
        价差百分比
    """
    if not price_a or not price_b:
        return 0.0

    # 使用卖一价(ask)在低价交易所买，买一价(bid)在高价交易所卖
    ask_price = min(price_a.get('ask', 0), price_b.get('ask', 0))
    bid_price = max(price_a.get('bid', 0), price_b.get('bid', 0))

    if ask_price <= 0 or bid_price <= 0:
        return 0.0

    # 价差 = (卖价 - 买价) / 买价 * 100%
    spread = (bid_price - ask_price) / ask_price * 100
    return spread


def calculate_net_profit(
    gross_profit_rate: float,
    total_fee: float,
    min_profit_rate: float = 0.5
) -> float:
    """计算扣除费用后的净利润

    Args:
        gross_profit_rate: 总利润率 (%)
        total_fee: 总手续费 (%)
        min_profit_rate: 最小利润率阈值 (%)

    Returns:
        净利润率，如果低于阈值返回0
    """
    net = gross_profit_rate - total_fee
    return net if net >= min_profit_rate else 0.0
