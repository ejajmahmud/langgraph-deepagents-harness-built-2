"""V30.0 增强版低风险套利引擎

集成交易所网关的增强版套利引擎:
- 多交易所支持
- 智能价差计算
- 动态风险评估
- 实时资金监控
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from strategies.base import BaseStrategy, StrategyState
from tools.exchange_gateway import (
    BaseExchangeGateway,
    ExchangeMode,
    TickerPrice,
    create_exchange_gateway,
)

logger = logging.getLogger(__name__)


@dataclass
class ArbitrageOpportunity:
    """套利机会数据结构"""
    symbol: str
    buy_exchange: str
    sell_exchange: str
    buy_price: float
    sell_price: float
    spread_pct: float
    expected_profit: float
    fee_estimate: float
    net_profit: float
    risk_score: float
    timestamp: float = field(default_factory=time.time)


class EnhancedLowRiskArbitrageV30(BaseStrategy):
    """V30.0 增强版低风险套利引擎

    新增功能:
    - 多交易所网关支持
    - 智能价差计算
    - 动态风险评分
    - 实时利润监控
    """

    STRATEGY_NAME: str = "enhanced_low_risk_v30"
    STRATEGY_DESCRIPTION: str = "V30.0 增强版低风险套利"

    def __init__(self, config: Dict[str, Any]) -> None:
        """初始化V30套利引擎

        Args:
            config: 策略配置
                - exchanges: 交易所列表 ["binance", "okx"]
                - symbols: 交易对列表
                - min_spread: 最小价差 (%)
                - max_risk_score: 最大风险评分
                - position_size: 仓位大小
        """
        super().__init__(config)

        # 交易所配置
        exchange_configs = config.get('exchanges', ['binance'])
        self._gateways: Dict[str, BaseExchangeGateway] = {}
        self._init_exchanges(exchange_configs, config)

        # 交易对配置
        self.symbols = config.get('symbols', ['BTC/USDT', 'ETH/USDT'])
        self.min_spread = config.get('min_spread', 0.3)  # 默认0.3%
        self.max_risk_score = config.get('max_risk_score', 0.7)
        self.position_size = config.get('position_size', 1000)

        # 交易对缓存
        self._price_cache: Dict[str, Dict[str, TickerPrice]] = {}
        self._opportunity_history: List[ArbitrageOpportunity] = []

        # 统计
        self._total_scans = 0
        self._total_opportunities = 0

        logger.info(
            f"V30套利引擎初始化: {len(self._gateways)} 交易所, "
            f"{len(self.symbols)} 交易对"
        )

    def _init_exchanges(
        self, exchanges: List[str], config: Dict[str, Any]
    ) -> None:
        """初始化交易所网关"""
        for exchange in exchanges:
            gateway = create_exchange_gateway(
                exchange,
                {
                    'mode': config.get('mode', 'simulated'),
                    'api_key': config.get('api_key', ''),
                    'api_secret': config.get('api_secret', ''),
                },
            )
            if gateway:
                self._gateways[exchange] = gateway
                logger.info(f"已添加交易所: {exchange}")

    async def initialize(self) -> bool:
        """初始化所有交易所连接"""
        init_tasks = [
            gateway.initialize() for gateway in self._gateways.values()
        ]
        results = await asyncio.gather(*init_tasks, return_exceptions=True)

        success_count = sum(
            1 for r in results if r is True
        )
        logger.info(f"交易所初始化完成: {success_count}/{len(self._gateways)}")
        return success_count > 0

    # -------------------- 核心扫描 --------------------

    async def scan_opportunities(self) -> List[Dict[str, Any]]:
        """扫描套利机会

        Returns:
            套利机会列表
        """
        if not self._gateways:
            logger.warning("未初始化交易所网关")
            return []

        opportunities = []

        for symbol in self.symbols:
            opp = await self._scan_symbol(symbol)
            if opp:
                opportunities.append(opp)

        self._total_scans += 1

        # 过滤低质量机会
        filtered = [
            o for o in opportunities
            if o.get('risk_score', 1.0) <= self.max_risk_score
            and o.get('spread_pct', 0) >= self.min_spread
        ]

        # 按利润排序
        filtered.sort(key=lambda x: x.get('net_profit', 0), reverse=True)

        self._total_opportunities += len(filtered)

        return filtered

    async def _scan_symbol(
        self, symbol: str
    ) -> Optional[Dict[str, Any]]:
        """扫描单个交易对

        Args:
            symbol: 交易对

        Returns:
            套利机会字典, 无机会返回None
        """
        # 并发获取所有交易所的价格
        tasks = {
            name: gateway.get_ticker(symbol)
            for name, gateway in self._gateways.items()
        }

        prices = {}
        for name, task in tasks.items():
            ticker = await task
            if ticker:
                prices[name] = ticker

        if len(prices) < 2:
            return None

        # 计算最佳买卖组合
        opportunities = self._find_arbitrage(prices)

        if not opportunities:
            return None

        # 返回最佳机会
        best = opportunities[0]

        return {
            'symbol': symbol,
            'buy_exchange': best.buy_exchange,
            'sell_exchange': best.sell_exchange,
            'buy_price': best.buy_price,
            'sell_price': best.sell_price,
            'spread_pct': best.spread_pct,
            'expected_profit': best.expected_profit,
            'fee_estimate': best.fee_estimate,
            'net_profit': best.net_profit,
            'risk_score': best.risk_score,
            'strategy': self.STRATEGY_NAME,
            'timestamp': time.time(),
        }

    def _find_arbitrage(
        self, prices: Dict[str, TickerPrice]
    ) -> List[ArbitrageOpportunity]:
        """寻找最佳套利机会

        Args:
            prices: 交易所 -> 价格映射

        Returns:
            机会列表 (按利润排序)
        """
        opportunities = []
        exchange_names = list(prices.keys())

        # 遍历所有交易对组合
        for i, buy_ex in enumerate(exchange_names):
            for sell_ex in exchange_names[i + 1:]:
                buy_data = prices[buy_ex]
                sell_data = prices[sell_ex]

                # 方案1: 在buy_ex买入, sell_ex卖出
                opp1 = self._calculate_arbitrage(
                    buy_ex, sell_ex,
                    buy_data.ask, sell_data.bid,
                )
                if opp1 and opp1.net_profit > 0:
                    opportunities.append(opp1)

                # 方案2: 在sell_ex买入, buy_ex卖出
                opp2 = self._calculate_arbitrage(
                    sell_ex, buy_ex,
                    sell_data.ask, buy_data.bid,
                )
                if opp2 and opp2.net_profit > 0:
                    opportunities.append(opp2)

        # 按净利润排序
        opportunities.sort(key=lambda x: x.net_profit, reverse=True)
        return opportunities

    def _calculate_arbitrage(
        self,
        buy_exchange: str,
        sell_exchange: str,
        buy_price: float,
        sell_price: float,
    ) -> Optional[ArbitrageOpportunity]:
        """计算套利机会

        Args:
            buy_exchange: 买入交易所
            sell_exchange: 卖出交易所
            buy_price: 买入价格
            sell_price: 卖出价格

        Returns:
            套利机会
        """
        # 计算价差
        spread_pct = ((sell_price - buy_price) / buy_price) * 100

        # 费用估算 (买卖各0.1%)
        fee_rate = 0.001
        fee_estimate = (buy_price + sell_price) * fee_rate

        # 预期利润
        position_value = self.position_size
        expected_profit = position_value * (spread_pct / 100)

        # 净利润 (扣除费用)
        net_profit = expected_profit - fee_estimate

        # 风险评分
        risk_score = self._calculate_risk_score(
            buy_exchange, sell_exchange, spread_pct
        )

        return ArbitrageOpportunity(
            symbol="",
            buy_exchange=buy_exchange,
            sell_exchange=sell_exchange,
            buy_price=buy_price,
            sell_price=sell_price,
            spread_pct=spread_pct,
            expected_profit=expected_profit,
            fee_estimate=fee_estimate,
            net_profit=net_profit,
            risk_score=risk_score,
        )

    def _calculate_risk_score(
        self,
        buy_ex: str,
        sell_ex: str,
        spread_pct: float,
    ) -> float:
        """计算风险评分

        Args:
            buy_ex: 买入交易所
            sell_ex: 卖出交易所
            spread_pct: 价差百分比

        Returns:
            风险评分 (0-1, 越高风险越大)
        """
        risk = 0.5  # 基础风险

        # 不同交易所风险加成
        if buy_ex != sell_ex:
            risk += 0.1  # 跨交易所额外风险

        # 低价差风险 (可能昙花一现)
        if spread_pct < 0.5:
            risk += 0.2

        # 高价差风险 (可能无法执行)
        if spread_pct > 2.0:
            risk += 0.1

        return min(risk, 1.0)

    # -------------------- 执行 --------------------

    async def execute_arbitrage(
        self, opportunity: Dict[str, Any]
    ) -> bool:
        """执行套利交易

        Args:
            opportunity: 套利机会

        Returns:
            是否执行成功
        """
        symbol = opportunity.get('symbol')
        buy_ex = opportunity.get('buy_exchange')
        sell_ex = opportunity.get('sell_exchange')

        buy_gateway = self._gateways.get(buy_ex)
        sell_gateway = self._gateways.get(sell_ex)

        if not buy_gateway or not sell_gateway:
            logger.error(f"交易所网关不存在: {buy_ex} or {sell_ex}")
            return False

        try:
            # 在买入交易所下单
            quantity = self.position_size / opportunity.get('buy_price', 1)
            order_id_buy = await buy_gateway.place_order(
                symbol=symbol,
                side="BUY",
                order_type="MARKET",
                quantity=quantity,
            )

            if not order_id_buy:
                logger.error(f"买入失败: {symbol}")
                return False

            # 在卖出交易所下单
            order_id_sell = await sell_gateway.place_order(
                symbol=symbol,
                side="SELL",
                order_type="MARKET",
                quantity=quantity,
            )

            if not order_id_sell:
                logger.error(f"卖出失败: {symbol}")
                # 尝试取消买入订单
                await buy_gateway.cancel_order(order_id_buy)
                return False

            logger.info(
                f"套利执行成功: {symbol} {buy_ex}->{sell_ex}, "
                f"预期利润 ${opportunity.get('net_profit', 0):.2f}"
            )
            return True

        except Exception as e:
            logger.error(f"套利执行失败: {e}")
            return False

    # -------------------- 性能统计 --------------------

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        stats = super().get_performance_stats()

        # 添加V30特有统计
        stats.update({
            'total_scans': self._total_scans,
            'total_opportunities': self._total_opportunities,
            'gateways': list(self._gateways.keys()),
            'symbols': self.symbols,
            'version': 'V30.0',
        })

        return stats

    # -------------------- 生命周期 --------------------

    def on_start(self) -> None:
        """启动回调"""
        logger.info(f"{self.STRATEGY_NAME} 启动")

    def on_stop(self) -> None:
        """停止回调"""
        logger.info(f"{self.STRATEGY_NAME} 停止")

    async def close_all_positions(self) -> Dict[str, bool]:
        """关闭所有持仓"""
        results = {}

        for name, gateway in self._gateways.items():
            try:
                balances = await gateway.get_all_balances()
                for asset, balance in balances.items():
                    if balance.free > 0:
                        # 卖出所有资产
                        results[asset] = await gateway.place_order(
                            symbol=f"{asset}/USDT",
                            side="SELL",
                            order_type="MARKET",
                            quantity=balance.free,
                        ) is not None
            except Exception as e:
                logger.error(f"关闭持仓失败 {name}: {e}")
                results[name] = False

        return results