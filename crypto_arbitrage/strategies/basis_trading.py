"""基差套利策略实现

利用现货价格和期货价格的差异进行套利，当期货价格高于现货价格时，
在现货市场买入，同时在期货市场卖出，等待价格收敛获利。
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from strategies.base import BaseStrategy
from tools.exchange_api import get_exchange_manager

logger = logging.getLogger(__name__)


class BasisTradingStrategy(BaseStrategy):
    """基差套利策略"""

    STRATEGY_NAME = "basis_trading"
    STRATEGY_DESCRIPTION = "基差套利策略 - 利用现货与期货价格差异"

    def __init__(self, config: Dict[str, Any]):
        """初始化基差套利策略

        Args:
            config: 策略配置字典，包含:
                - min_profit_rate: 最小收益率阈值 (%)
                - max_position_size: 最大仓位大小
                - risk_tolerance: 风险容忍度
                - symbols: 监控的交易对列表
                - futures_exchange: 期货交易所
                - min_basis_spread: 最小基差 (%)
                - holding_period: 持有期限制（天）
                - execution_timeout: 执行超时（秒）
                - preferred_exchange: 首选现货交易所
        """
        # V1.7.0 Fix: 先设置子类属性，再调 super().__init__()（内部会调用 validate_config）
        self.risk_tolerance = config.get('risk_tolerance', 0.15)
        self.symbols = config.get('symbols', ['BTC/USDT', 'ETH/USDT'])
        self.futures_exchange = config.get('futures_exchange', None)
        self.preferred_exchange = config.get('preferred_exchange', None)
        self.min_basis_spread = config.get('min_basis_spread', 0.2)
        self.holding_period = config.get('holding_period', 7)
        self.execution_timeout = config.get('execution_timeout', 120)
        super().__init__(config)

    def validate_config(self) -> List[str]:
        """验证基差套利配置"""
        errors = super().validate_config()
        if self.futures_exchange is None:
            errors.append("futures_exchange 未配置，基差套利无法运行")
        return errors

    async def scan_opportunities(self) -> List[Dict[str, Any]]:
        """扫描基差套利机会

        Returns:
            基差套利机会列表
        """
        if not self.futures_exchange:
            logger.warning("期货交易所未配置")
            return []

        exchange_manager = get_exchange_manager()
        if not exchange_manager:
            logger.error("交易所管理器未初始化")
            return []

        opportunities = []

        try:
            for symbol in self.symbols:
                # 获取现货价格
                spot_prices: Dict[str, Dict] = {}
                for exchange_name in exchange_manager.exchanges:
                    if exchange_name == self.futures_exchange:
                        continue

                    try:
                        ticker = await exchange_manager.get_ticker(exchange_name, symbol)
                        if ticker:
                            spot_prices[exchange_name] = {
                                'bid': ticker.get('bid'),
                                'ask': ticker.get('ask'),
                                'last': ticker.get('last')
                            }
                    except Exception as e:
                        logger.warning(f"获取 {exchange_name} 现货价格失败: {e}")

                # 获取期货价格
                futures_price_data: Optional[Dict] = None
                try:
                    ticker = await exchange_manager.get_ticker(self.futures_exchange, symbol)
                    if ticker:
                        futures_price_data = {
                            'bid': ticker.get('bid'),
                            'ask': ticker.get('ask'),
                            'last': ticker.get('last')
                        }
                except Exception as e:
                    logger.warning(f"获取期货交易所 {self.futures_exchange} 价格失败: {e}")
                    continue

                if not futures_price_data:
                    continue

                # 遍历每个现货交易所计算基差
                for spot_ex_name, spot_data in spot_prices.items():
                    spot_price = spot_data.get('ask')
                    futures_price = futures_price_data.get('bid')

                    if not spot_price or not futures_price:
                        continue

                    # 计算基差
                    basis_spread = ((futures_price - spot_price) / spot_price) * 100

                    if basis_spread < self.min_basis_spread:
                        logger.debug(f"基差过小: {basis_spread:.2f}% < {self.min_basis_spread:.2f}%")
                        continue

                    # 考虑手续费
                    buy_fee_rate = 0.001
                    sell_fee_rate = 0.001
                    buy_cost = spot_price * (1 + buy_fee_rate)
                    sell_revenue = futures_price * (1 - sell_fee_rate)

                    expected_profit = sell_revenue - buy_cost
                    profit_rate = (expected_profit / buy_cost) * 100

                    if profit_rate >= self.min_profit_rate:
                        max_amount = self.max_position_size / spot_price

                        opportunity = {
                            'symbol': symbol,
                            'buy_exchange': spot_ex_name,
                            'sell_exchange': self.futures_exchange,
                            'spot_price': spot_price,
                            'futures_price': futures_price,
                            'basis_spread': basis_spread,
                            'holding_period': self.holding_period,
                            'profit': expected_profit,
                            'profit_rate': profit_rate,
                            'expected_profit': expected_profit,
                            'buy_cost': buy_cost,
                            'max_amount': max_amount,
                            'timestamp': time.time()
                        }

                        opportunities.append(opportunity)

        except Exception as e:
            logger.error(f"扫描基差套利机会失败: {e}")

        # 使用基类方法统一过滤和排序
        logger.info(f"发现 {len(opportunities)} 个基差套利机会（过滤前）")
        return self._post_process_opportunities(opportunities)

    async def execute_arbitrage(self, opportunity: Dict[str, Any]) -> bool:
        """执行基差套利交易

        Args:
            opportunity: 基差套利机会字典

        Returns:
            是否执行成功
        """
        exchange_manager = get_exchange_manager()
        if not exchange_manager:
            logger.error("交易所管理器未初始化")
            return False

        symbol = opportunity['symbol']
        spot_exchange = opportunity.get('spot_exchange', opportunity.get('buy_exchange'))
        futures_exchange = opportunity.get('futures_exchange', opportunity.get('sell_exchange'))
        amount = opportunity['max_amount']

        logger.info(f"开始执行基差套利: {symbol} {spot_exchange} -> {futures_exchange}")

        try:
            # 买入现货
            spot_order = await exchange_manager.place_order(
                spot_exchange,
                symbol,
                'market',
                'buy',
                amount
            )

            if not spot_order:
                logger.error("现货买入失败")
                return False

            spot_order_id = spot_order.get('id')

            # 等待现货成交
            await asyncio.sleep(5)

            # 转账到期货交易所（如果是跨交易所）
            transfer_order = {'success': True, 'transfer_id': 'internal'}
            if spot_exchange != futures_exchange:
                transfer_id = f"transfer_{int(time.time() * 1000)}"
                transfer_order = {
                    'success': True,
                    'transfer_id': transfer_id,
                    'from_exchange': spot_exchange,
                    'to_exchange': futures_exchange
                }
                await asyncio.sleep(min(self.execution_timeout, 60))

            # 卖出期货
            futures_order = await exchange_manager.place_order(
                futures_exchange,
                symbol,
                'market',
                'sell',
                amount
            )

            if not futures_order:
                logger.error("期货卖出失败")
                return False

            futures_order_id = futures_order.get('id')

            # 记录交易（通过 safe_execute 的 _record_trade 统一处理，此处仅追加到 active_positions）
            arbitrage_record = {
                'symbol': symbol,
                'spot_exchange': spot_exchange,
                'futures_exchange': futures_exchange,
                'spot_order_id': spot_order_id,
                'futures_order_id': futures_order_id,
                'transfer_id': transfer_order.get('transfer_id'),
                'expected_profit': opportunity['expected_profit'],
                'status': 'completed',
                'timestamp': time.time()
            }

            self.active_positions.append(arbitrage_record)

            logger.info(f"基差套利交易完成: 预期收益率 {opportunity['profit_rate']:.2f}%")
            return True

        except Exception as e:
            logger.error(f"基差套利交易失败: {e}")
            return False
