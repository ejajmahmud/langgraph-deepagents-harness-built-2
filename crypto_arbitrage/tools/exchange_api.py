"""交易所 API 集成模块 - 统一的交易所接口"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

import ccxt.async_support as ccxt

logger = logging.getLogger(__name__)


class ExchangeManager:
    """交易所管理器 - 统一管理多个交易所连接"""

    def __init__(self, config: Dict[str, Any]):
        """初始化交易所管理器

        Args:
            config: 交易所配置字典
        """
        self.exchanges: Dict[str, ccxt.Exchange] = {}
        self.config = config
        self._initialize_exchanges()

    def _initialize_exchanges(self) -> None:
        """初始化所有配置的交易所"""
        for exchange_name, exchange_config in self.config.items():
            try:
                exchange_class = getattr(ccxt, exchange_name)
                self.exchanges[exchange_name] = exchange_class({
                    'apiKey': exchange_config.get('api_key'),
                    'secret': exchange_config.get('secret'),
                    'enableRateLimit': True,
                    'options': exchange_config.get('options', {})
                })
                logger.info(f"成功初始化交易所: {exchange_name}")
            except Exception as e:
                logger.error(f"初始化交易所 {exchange_name} 失败: {e}")

    async def get_ticker(self, exchange_name: str, symbol: str) -> Optional[Dict]:
        """获取交易对行情

        Args:
            exchange_name: 交易所名称
            symbol: 交易对符号，如 'BTC/USDT'

        Returns:
            行情数据字典，包含价格等信息
        """
        exchange = self.exchanges.get(exchange_name)
        if not exchange:
            logger.error(f"交易所 {exchange_name} 未初始化")
            return None

        try:
            ticker = await exchange.fetch_ticker(symbol)
            return ticker
        except Exception as e:
            logger.error(f"获取 {exchange_name} {symbol} 行情失败: {e}")
            return None

    async def get_tickers_batch(
        self,
        exchange_name: str,
        symbols: List[str],
        timeout: float = 10.0
    ) -> Dict[str, Optional[Dict]]:
        """V1.8.0: 并发获取多个交易对行情

        Args:
            exchange_name: 交易所名称
            symbols: 交易对符号列表
            timeout: 超时时间（秒）

        Returns:
            字典，key 为交易对，value 为行情数据或 None
        """
        async def fetch_one(symbol: str) -> tuple:
            try:
                ticker = await asyncio.wait_for(
                    self.get_ticker(exchange_name, symbol),
                    timeout=timeout
                )
                return symbol, ticker
            except asyncio.TimeoutError:
                logger.warning(f"获取 {symbol} 超时")
                return symbol, None
            except Exception as e:
                logger.debug(f"获取 {symbol} 失败: {e}")
                return symbol, None

        results = await asyncio.gather(*[fetch_one(s) for s in symbols])
        return {symbol: ticker for symbol, ticker in results}

    async def get_order_book(self, exchange_name: str, symbol: str, limit: int = 20) -> Optional[Dict]:
        """获取订单簿

        Args:
            exchange_name: 交易所名称
            symbol: 交易对符号
            limit: 订单簿深度

        Returns:
            订单簿数据，包含买单和卖单
        """
        exchange = self.exchanges.get(exchange_name)
        if not exchange:
            logger.error(f"交易所 {exchange_name} 未初始化")
            return None

        try:
            order_book = await exchange.fetch_order_book(symbol, limit)
            return order_book
        except Exception as e:
            logger.error(f"获取 {exchange_name} {symbol} 订单簿失败: {e}")
            return None

    async def get_balance(self, exchange_name: str) -> Optional[Dict]:
        """获取账户余额

        Args:
            exchange_name: 交易所名称

        Returns:
            余额信息字典
        """
        exchange = self.exchanges.get(exchange_name)
        if not exchange:
            logger.error(f"交易所 {exchange_name} 未初始化")
            return None

        try:
            balance = await exchange.fetch_balance()
            return balance
        except Exception as e:
            logger.error(f"获取 {exchange_name} 余额失败: {e}")
            return None

    async def place_order(self, exchange_name: str, symbol: str,
                         order_type: str, side: str, amount: float,
                         price: Optional[float] = None) -> Optional[Dict]:
        """下单

        Args:
            exchange_name: 交易所名称
            symbol: 交易对符号
            order_type: 订单类型 ('market' 或 'limit')
            side: 买卖方向 ('buy' 或 'sell')
            amount: 数量
            price: 价格 (限价单必需)

        Returns:
            订单信息字典
        """
        exchange = self.exchanges.get(exchange_name)
        if not exchange:
            logger.error(f"交易所 {exchange_name} 未初始化")
            return None

        try:
            if order_type == 'market':
                order = await exchange.create_market_order(symbol, side, amount)
            else:
                if price is None:
                    logger.error("限价单必须指定价格")
                    return None
                order = await exchange.create_limit_order(symbol, side, amount, price)

            logger.info(f"在 {exchange_name} 下单成功: {symbol} {side} {amount} @ {price}")
            return order
        except Exception as e:
            logger.error(f"在 {exchange_name} 下单失败: {e}")
            return None

    async def cancel_order(self, exchange_name: str, order_id: str, symbol: str) -> bool:
        """取消订单

        Args:
            exchange_name: 交易所名称
            order_id: 订单ID
            symbol: 交易对符号

        Returns:
            是否成功取消
        """
        exchange = self.exchanges.get(exchange_name)
        if not exchange:
            logger.error(f"交易所 {exchange_name} 未初始化")
            return False

        try:
            await exchange.cancel_order(order_id, symbol)
            logger.info(f"成功取消订单: {order_id}")
            return True
        except Exception as e:
            logger.error(f"取消订单失败: {e}")
            return False

    async def get_trading_fees(self, exchange_name: str, symbol: str) -> Optional[Dict]:
        """获取交易手续费

        Args:
            exchange_name: 交易所名称
            symbol: 交易对符号

        Returns:
            手续费信息字典
        """
        exchange = self.exchanges.get(exchange_name)
        if not exchange:
            logger.error(f"交易所 {exchange_name} 未初始化")
            return None

        try:
            # BUG FIX #5: ccxt 4.x 使用 fetch_trading_fees_for_symbol 替代废弃的 fetch_trading_fees
            if hasattr(exchange, 'fetch_trading_fees_for_symbol'):
                fees = await exchange.fetch_trading_fees_for_symbol(symbol)
                return fees
            # 降级兼容旧版 ccxt
            fees = await exchange.fetch_trading_fees()
            return fees
        except Exception as e:
            logger.error(f"获取 {exchange_name} 手续费失败: {e}")
            return None

    async def close_all(self) -> None:
        """关闭所有交易所连接"""
        for exchange_name, exchange in self.exchanges.items():
            try:
                await exchange.close()
                logger.info(f"已关闭交易所连接: {exchange_name}")
            except Exception as e:
                logger.error(f"关闭 {exchange_name} 连接失败: {e}")


class ArbitrageCalculator:
    """套利计算器 - 计算套利机会和收益率"""

    @staticmethod
    def calculate_cross_exchange_arbitrage(
        buy_exchange: str, sell_exchange: str,
        buy_price: float, sell_price: float,
        buy_fee: float, sell_fee: float,
        amount: float
    ) -> Dict[str, Any]:
        """计算跨交易所套利收益率

        Args:
            buy_exchange: 买入交易所
            sell_exchange: 卖出交易所
            buy_price: 买入价格
            sell_price: 卖出价格
            buy_fee: 买入手续费率
            sell_fee: 卖出手续费率
            amount: 交易数量

        Returns:
            套利分析结果字典
        """
        # 计算实际成本
        buy_cost = buy_price * amount * (1 + buy_fee)
        sell_revenue = sell_price * amount * (1 - sell_fee)

        # 计算利润和收益率
        profit = sell_revenue - buy_cost
        profit_rate = (profit / buy_cost) * 100

        return {
            'buy_exchange': buy_exchange,
            'sell_exchange': sell_exchange,
            'buy_price': buy_price,
            'sell_price': sell_price,
            'amount': amount,
            'buy_cost': buy_cost,
            'sell_revenue': sell_revenue,
            'profit': profit,
            'profit_rate': profit_rate,
            'is_profitable': profit > 0
        }

    @staticmethod
    def calculate_triangular_arbitrage(
        rates: Dict[str, float],
        fees: Dict[str, float],
        amount: float
    ) -> Dict[str, Any]:
        """计算三角套利机会

        Args:
            rates: 汇率字典，如 {'BTC/USDT': 50000, 'ETH/BTC': 0.05, 'ETH/USDT': 2500}
            fees: 手续费率字典
            amount: 初始数量

        Returns:
            三角套利分析结果
        """
        # 示例：BTC/USDT -> ETH/BTC -> ETH/USDT
        # 路径: USDT -> BTC -> ETH -> USDT

        # 第一步：USDT -> BTC
        btc_amount = amount / rates['BTC/USDT'] * (1 - fees['BTC/USDT'])

        # 第二步：BTC -> ETH
        eth_amount = btc_amount * rates['ETH/BTC'] * (1 - fees['ETH/BTC'])

        # 第三步：ETH -> USDT
        final_amount = eth_amount * rates['ETH/USDT'] * (1 - fees['ETH/USDT'])

        profit = final_amount - amount
        profit_rate = (profit / amount) * 100

        return {
            'initial_amount': amount,
            'final_amount': final_amount,
            'profit': profit,
            'profit_rate': profit_rate,
            'is_profitable': profit > 0,
            'path': ['USDT->BTC', 'BTC->ETH', 'ETH->USDT']
        }


# 创建全局交易所管理器实例
exchange_manager: Optional[ExchangeManager] = None


def initialize_exchange_manager(config: Dict[str, Any]) -> ExchangeManager:
    """初始化全局交易所管理器

    Args:
        config: 交易所配置

    Returns:
        交易所管理器实例
    """
    global exchange_manager
    exchange_manager = ExchangeManager(config)
    return exchange_manager


def get_exchange_manager() -> Optional[ExchangeManager]:
    """获取全局交易所管理器实例

    Returns:
        交易所管理器实例，如果未初始化则返回 None
    """
    return exchange_manager
