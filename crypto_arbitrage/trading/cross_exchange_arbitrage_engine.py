"""V34.0 跨交易所套利引擎

V34.0 新增功能:
1. Cross-Exchange Arbitrage Engine - 跨交易所套利引擎
2. 价差检测与机会识别
3. 执行协调与风险控制
4. 利润计算与优化

创建时间：2026-05-07 20:55
"""

import logging
import time
import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
from collections import deque
import heapq

logger = logging.getLogger(__name__)


class ArbitrageStatus(Enum):
    """套利状态"""
    DETECTED = "detected"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ArbitrageType(Enum):
    """套利类型"""
    SIMPLE = "simple"  # 简单价差
    TRIANGULAR = "triangular"  # 三角套利
    CROSS_EXCHANGE = "cross_exchange"  # 跨交易所
    FUNDING = "funding"  # 资金费率


@dataclass
class ArbitrageTrade:
    """套利交易"""
    opportunity_id: str
    arbitrage_type: ArbitrageType
    symbol: str
    buy_exchange: str
    sell_exchange: str
    buy_price: float
    sell_price: float
    quantity: float
    expected_profit: float
    net_profit: float
    status: ArbitrageStatus = ArbitrageStatus.DETECTED
    timestamp: float = field(default_factory=time.time)
    execution_time: float = 0.0
    notes: str = ""


@dataclass
class ArbitrageOpportunity:
    """套利机会"""
    id: str
    type: ArbitrageType
    symbols: List[str]
    buy_exchange: str
    sell_exchange: str
    buy_price: float
    sell_price: float
    spread: float
    spread_pct: float
    volume: float
    expected_profit: float
    risk_score: float
    confidence: float
    timestamp: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + 30)


class CrossExchangeArbitrageEngine:
    """跨交易所套利引擎

    功能：
    - 价差检测
    - 机会识别
    - 执行协调
    - 风险管理
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化套利引擎

        Args:
            config: 配置字典
                - min_spread_pct: 最小价差百分比
                - min_volume: 最小成交量
                - max_position_size: 最大仓位
                - min_confidence: 最小置信度
        """
        self.config = config
        self.min_spread_pct = config.get('min_spread_pct', 0.1)
        self.min_volume = config.get('min_volume', 10.0)
        self.max_position_size = config.get('max_position_size', 10000)
        self.min_confidence = config.get('min_confidence', 0.6)

        # 手续费率
        self.fee_rates: Dict[str, float] = {
            'binance': 0.001,
            'okx': 0.001,
            'bybit': 0.001,
            'gate': 0.002,
            'huobi': 0.002
        }

        # 活跃交易
        self.active_trades: Dict[str, ArbitrageTrade] = {}

        # 历史交易
        self.trade_history: deque = deque(maxlen=1000)

        # 机会队列 (优先队列)
        self.opportunity_queue: List[tuple] = []

        # 回调函数
        self.on_opportunity_detected: Optional[Callable] = None
        self.on_trade_executed: Optional[Callable] = None
        self.on_trade_completed: Optional[Callable] = None

        # 统计
        self.stats = {
            'total_opportunities': 0,
            'total_trades': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'total_profit': 0.0,
            'win_rate': 0.0
        }

        logger.info(f"[OK] CrossExchangeArbitrageEngine 初始化完成")
        logger.info(f"    最小价差: {self.min_spread_pct}%")
        logger.info(f"    最小成交量: {self.min_volume}")

    def calculate_opportunity(
        self,
        symbol: str,
        buy_exchange: str,
        sell_exchange: str,
        buy_price: float,
        sell_price: float,
        volume: float
    ) -> Optional[ArbitrageOpportunity]:
        """计算套利机会

        Args:
            symbol: 交易对
            buy_exchange: 买入交易所
            sell_exchange: 卖出交易所
            buy_price: 买入价
            sell_price: 卖出价
            volume: 成交量

        Returns:
            ArbitrageOpportunity: 套利机会
        """
        if buy_price <= 0 or sell_price <= 0 or volume <= 0:
            return None

        spread = sell_price - buy_price
        spread_pct = (spread / buy_price) * 100

        # 检查最小价差
        if spread_pct < self.min_spread_pct:
            return None

        # 计算预期利润
        buy_fee = buy_price * volume * self.fee_rates.get(buy_exchange, 0.001)
        sell_fee = sell_price * volume * self.fee_rates.get(sell_exchange, 0.001)
        total_fee = buy_fee + sell_fee

        expected_profit = spread * volume - total_fee
        net_profit = expected_profit * 0.8  # 预留20%滑点缓冲

        # 检查最大仓位
        notional_value = buy_price * volume
        if notional_value > self.max_position_size:
            volume = self.max_position_size / buy_price
            expected_profit = spread * volume - total_fee

        # 风险评分
        risk_score = self._calculate_risk_score(spread_pct, volume)

        # 置信度
        confidence = self._calculate_confidence(spread_pct, volume)

        # 检查置信度
        if confidence < self.min_confidence:
            return None

        opp_id = f"{symbol}_{buy_exchange}_{sell_exchange}_{int(time.time())}"

        return ArbitrageOpportunity(
            id=opp_id,
            type=ArbitrageType.CROSS_EXCHANGE,
            symbols=[symbol],
            buy_exchange=buy_exchange,
            sell_exchange=sell_exchange,
            buy_price=buy_price,
            sell_price=sell_price,
            spread=spread,
            spread_pct=spread_pct,
            volume=volume,
            expected_profit=expected_profit,
            risk_score=risk_score,
            confidence=confidence
        )

    def _calculate_risk_score(
        self,
        spread_pct: float,
        volume: float
    ) -> float:
        """计算风险评分

        Args:
            spread_pct: 价差百分比
            volume: 成交量

        Returns:
            float: 风险评分 (0-1, 越低越好)
        """
        # 低价差 = 高风险
        spread_score = spread_pct / 1.0  # 1%为基准

        # 小成交量 = 高风险
        volume_score = volume / 100.0  # 100为基准

        # 综合评分
        risk_score = 1.0 - min(spread_score * 0.7 + volume_score * 0.3, 0.95)

        return max(risk_score, 0.05)  # 最低0.05

    def _calculate_confidence(
        self,
        spread_pct: float,
        volume: float
    ) -> float:
        """计算置信度

        Args:
            spread_pct: 价差百分比
            volume: 成交量

        Returns:
            float: 置信度 (0-1)
        """
        # 高价差 = 高置信度
        spread_conf = min(spread_pct / 0.5, 1.0)  # 0.5%为基准

        # 高成交量 = 高置信度
        volume_conf = min(volume / 100.0, 1.0)  # 100为基准

        return spread_conf * 0.6 + volume_conf * 0.4

    def execute_trade(
        self,
        opportunity: ArbitrageOpportunity,
        executor: Callable
    ) -> ArbitrageTrade:
        """执行交易

        Args:
            opportunity: 套利机会
            executor: 执行回调函数

        Returns:
            ArbitrageTrade: 交易结果
        """
        trade = ArbitrageTrade(
            opportunity_id=opportunity.id,
            arbitrage_type=opportunity.type,
            symbol=opportunity.symbols[0],
            buy_exchange=opportunity.buy_exchange,
            sell_exchange=opportunity.sell_exchange,
            buy_price=opportunity.buy_price,
            sell_price=opportunity.sell_price,
            quantity=opportunity.volume,
            expected_profit=opportunity.expected_profit,
            net_profit=opportunity.expected_profit * 0.8,
            status=ArbitrageStatus.EXECUTING
        )

        self.active_trades[opportunity.id] = trade
        self.stats['total_trades'] += 1

        logger.info(f"[OK] 开始执行套利: {opportunity.id}")
        logger.info(f"    买入: {opportunity.buy_exchange} @ {opportunity.buy_price}")
        logger.info(f"    卖出: {opportunity.sell_exchange} @ {opportunity.sell_price}")

        # 调用执行器
        try:
            result = executor(opportunity)

            trade.status = ArbitrageStatus.COMPLETED
            trade.execution_time = time.time() - trade.timestamp

            self.stats['successful_trades'] += 1
            self.stats['total_profit'] += trade.net_profit

            # 更新胜率
            if self.stats['total_trades'] > 0:
                self.stats['win_rate'] = (
                    self.stats['successful_trades'] / self.stats['total_trades']
                )

            logger.info(f"[OK] 套利完成: {opportunity.id}")
            logger.info(f"    净利润: ${trade.net_profit:.2f}")

        except Exception as e:
            trade.status = ArbitrageStatus.FAILED
            trade.notes = str(e)
            self.stats['failed_trades'] += 1

            logger.error(f"[X] 套利失败: {opportunity.id} - {e}")

        # 记录到历史
        self.trade_history.append(trade)

        return trade

    def scan_opportunities(
        self,
        market_data: Dict[str, Any]
    ) -> List[ArbitrageOpportunity]:
        """扫描套利机会

        Args:
            market_data: 市场数据

        Returns:
            List[ArbitrageOpportunity]: 机会列表
        """
        opportunities = []

        # 遍历所有交易对
        for symbol, exchanges in market_data.items():
            if len(exchanges) < 2:
                continue

            # 遍历所有交易所组合
            exchange_list = list(exchanges.keys())
            for i, buy_ex in enumerate(exchange_list):
                for sell_ex in exchange_list[i+1:]:
                    buy_data = exchanges[buy_ex]
                    sell_data = exchanges[sell_ex]

                    opp = self.calculate_opportunity(
                        symbol=symbol,
                        buy_exchange=buy_ex,
                        sell_exchange=sell_ex,
                        buy_price=buy_data.get('bid_price', 0),
                        sell_price=sell_data.get('ask_price', 0),
                        volume=min(
                            buy_data.get('bid_volume', 0),
                            sell_data.get('ask_volume', 0)
                        )
                    )

                    if opp:
                        opportunities.append(opp)
                        self.stats['total_opportunities'] += 1

        # 按预期利润排序
        opportunities.sort(key=lambda x: x.expected_profit, reverse=True)

        logger.info(f"[OK] 扫描完成: 发现 {len(opportunities)} 个��会")

        return opportunities

    def get_best_opportunity(
        self,
        market_data: Dict[str, Any]
    ) -> Optional[ArbitrageOpportunity]:
        """获取最佳机会

        Args:
            market_data: 市场数据

        Returns:
            ArbitrageOpportunity: 最佳机会
        """
        opportunities = self.scan_opportunities(market_data)

        if not opportunities:
            return None

        return opportunities[0]

    def cancel_trade(self, opportunity_id: str) -> bool:
        """取消交易

        Args:
            opportunity_id: 机会ID

        Returns:
            bool: 是否成功
        """
        trade = self.active_trades.get(opportunity_id)
        if not trade:
            return False

        trade.status = ArbitrageStatus.CANCELLED
        del self.active_trades[opportunity_id]

        logger.info(f"[OK] 交易已取消: {opportunity_id}")
        return True

    def get_stats(self) -> Dict[str, Any]:
        """获取统计数据

        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            'total_opportunities': self.stats['total_opportunities'],
            'active_trades': len(self.active_trades),
            'total_trades': self.stats['total_trades'],
            'successful_trades': self.stats['successful_trades'],
            'failed_trades': self.stats['failed_trades'],
            'win_rate': self.stats['win_rate'],
            'total_profit': self.stats['total_profit'],
            'avg_profit_per_trade': (
                self.stats['total_profit'] / self.stats['successful_trades']
                if self.stats['successful_trades'] > 0 else 0
            )
        }

    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要

        Returns:
            Dict[str, Any]: 性能信息
        """
        stats = self.get_stats()

        return {
            'opportunities_detected': stats['total_opportunities'],
            'trades_executed': stats['total_trades'],
            'success_rate': f"{stats['win_rate']:.1%}",
            'total_profit': f"${stats['total_profit']:.2f}",
            'avg_profit': f"${stats['avg_profit_per_trade']:.2f}",
            'active_opportunities': len(self.opportunity_queue)
        }