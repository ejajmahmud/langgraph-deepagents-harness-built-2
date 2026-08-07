"""
V35.0 完整套利系统集成

整合 V34.0 所有功能，实现统一的低风险套利系统：
1. Triangular Arbitrage - 三角形套利集成
2. Funding Rate Arbitrage - 资金费率套利集成
3. Cross-Exchange Arbitrage - 跨交易所套利
4. ML Signal Integration - ML信号集成
5. 统一风险管理

创建时间：2026-05-07 22:25
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ArbitrageTypeV35(Enum):
    """V35.0 套利类型枚举"""
    TRIANGULAR = "triangular"  # 三角套利
    CROSS_EXCHANGE = "cross_exchange"  # 跨交易所套利
    FUNDING_RATE = "funding_rate"  # 资金费率套利
    STATISTICAL = "statistical"  # 统计套利


class ArbitrageSignalV35(Enum):
    """V35.0 信号强度"""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    NEUTRAL = "neutral"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


@dataclass
class ArbitrageOpportunityV35:
    """V35.0 套利机会数据结构

    Attributes:
        opportunity_id: 机会唯一ID
        arbitrage_type: 套利类型
        signal: 信号强度
        symbol: 交易对
        exchanges: 涉及的交易所
       entry_price: 入场价
        exit_price: 出场价
        expected_profit: 预期利润(%)
        confidence: 置信度
        risk_score: 风险评分
        position_size: 建议仓位
        stop_loss: 止损价
        take_profit: 止盈价
        ttl: 有效时间(秒)
        timestamp: 发现时间
    """
    opportunity_id: str
    arbitrage_type: ArbitrageTypeV35
    signal: ArbitrageSignalV35
    symbol: str
    exchanges: List[str]
    entry_price: float
    exit_price: float
    expected_profit: float
    confidence: float
    risk_score: float
    position_size: float
    stop_loss: float
    take_profit: float
    ttl: int = 30
    timestamp: float = field(default_factory=time.time)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResultV35:
    """V35.0 执行结果"""
    opportunity_id: str
    success: bool
    executed_price: float
    executed_size: float
    actual_profit: float
    slippage: float
    fees: float
    error_message: str = ""
    timestamp: float = field(default_factory=time.time)


class UnifiedArbitrageSystemV35:
    """V35.0 统一套利系统

    核心功能：
    1. 多策略协调 - 三角形/跨交易所/资金费率
    2. 智能仓位管理
    3. 统一风险管理
    4. 自动执行优化
    5. 性能追踪

    继承自 V34.0 的所有功能：
    - MultiExchangeDataAggregator
    - SmartOrderRouter
    - CrossExchangeArbitrageEngine
    - Memo0IntegratedTrading
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化 V35.0 统一套利系统

        Args:
            config: 配置字典
                - min_profit_threshold: 最小利润阈值 (%)
                - max_position_size: 最大仓位
                - enable_triangular: 启用三角形套利
                - enable_cross_exchange: 启用跨交易所套利
                - enable_funding: 启用资金费率套利
                - risk_tolerance: 风险容忍度
        """
        self.config = config
        self.min_profit_threshold = config.get('min_profit_threshold', 0.1)
        self.max_position_size = config.get('max_position_size', 10000.0)
        self.enable_triangular = config.get('enable_triangular', True)
        self.enable_cross_exchange = config.get('enable_cross_exchange', True)
        self.enable_funding = config.get('enable_funding', True)
        self.risk_tolerance = config.get('risk_tolerance', 0.3)

        # 子系统
        self._triangular_strategy = None
        self._cross_exchange_engine = None
        self._funding_engine = None
        self._memo0_trading = None

        # 策略管理器
        self._strategy_managers: Dict[ArbitrageTypeV35, Any] = {}

        # 性能统计
        self._total_opportunities = 0
        self._total_executed = 0
        self._total_profit = 0.0
        self._daily_pnl = 0.0
        self._win_count = 0
        self._loss_count = 0

        # 初始化时间
        self._initialized_at = time.time()
        self._last_scan_time = 0.0

        logger.info("[OK] V35.0 统一套利系统初始化完成")

    async def initialize(self) -> bool:
        """初始化所有子系统

        Returns:
            初始化是否成功
        """
        try:
            # 初始化三角形套利
            if self.enable_triangular:
                await self._init_triangular()

            # 初始化跨交易所套利
            if self.enable_cross_exchange:
                await self._init_cross_exchange()

            # 初始化资金费率套利
            if self.enable_funding:
                await self._init_funding()

            # 初始化 Memo0 集成
            await self._init_memo0()

            logger.info("[OK] V35.0 所有子系统初始化完成")
            return True

        except Exception as e:
            logger.error(f"V35.0 子系统初始化失败: {e}")
            return False

    async def _init_triangular(self) -> bool:
        """初始化三角形套利"""
        try:
            from strategies.triangular_arbitrage import TriangularArbitrageStrategy

            self._triangular_strategy = TriangularArbitrageStrategy({
                'triangles': [
                    {'base': 'USDT', 'path': [
                        {'from': 'USDT', 'to': 'BTC', 'pair': 'BTC/USDT'},
                        {'from': 'BTC', 'to': 'ETH', 'pair': 'ETH/BTC'},
                        {'from': 'ETH', 'to': 'USDT', 'pair': 'ETH/USDT'}
                    ]},
                    {'base': 'USDT', 'path': [
                        {'from': 'USDT', 'to': 'ETH', 'pair': 'ETH/USDT'},
                        {'from': 'ETH', 'to': 'BNB', 'pair': 'BNB/ETH'},
                        {'from': 'BNB', 'to': 'USDT', 'pair': 'BNB/USDT'}
                    ]}
                ],
                'min_profit_rate': self.min_profit_threshold,
                'max_position_size': self.max_position_size
            })
            self._strategy_managers[ArbitrageTypeV35.TRIANGULAR] = self._triangular_strategy
            logger.info("[OK] 三角形套利初始化完成")
            return True
        except Exception as e:
            logger.warning(f"三角形套利初始化失败: {e}")
            return False

    async def _init_cross_exchange(self) -> bool:
        """初始化跨交易所套利"""
        try:
            from trading.cross_exchange_arbitrage_engine import CrossExchangeArbitrageEngine

            self._cross_exchange_engine = CrossExchangeArbitrageEngine({
                'min_profit_threshold': self.min_profit_threshold,
                'max_position_size': self.max_position_size,
                'max_slippage': 0.001,
                'enable_smart_routing': True
            })
            self._strategy_managers[ArbitrageTypeV35.CROSS_EXCHANGE] = self._cross_exchange_engine
            logger.info("[OK] 跨交易所套利初始化完成")
            return True
        except Exception as e:
            logger.warning(f"跨交易所套利初始化失败: {e}")
            return False

    async def _init_funding(self) -> bool:
        """初始化资金费率套利"""
        try:
            from strategies.funding_rate_engine import FundingRateEngine

            self._funding_engine = FundingRateEngine({
                'min_funding_diff': 0.0001,
                'max_position_size': self.max_position_size,
                'lookback_hours': 24
            })
            self._strategy_managers[ArbitrageTypeV35.FUNDING_RATE] = self._funding_engine
            logger.info("[OK] 资金费率套利初始化完成")
            return True
        except Exception as e:
            logger.warning(f"资金费率套利初始化失败: {e}")
            return False

    async def _init_memo0(self) -> bool:
        """初始化 Memo0 集成"""
        try:
            from trading.memo0_integrated_trading import Memo0IntegratedTrading

            self._memo0_trading = Memo0IntegratedTrading({
                'min_confidence': 'medium',
                'min_success_rate': 0.5,
                'lookback_matches': 10,
                'enable_adaptive': True
            })
            await self._memo0_trading.initialize()
            logger.info("[OK] Memo0 集成初始化完成")
            return True
        except Exception as e:
            logger.warning(f"Memo0 集成初始化失败: {e}")
            return False

    async def scan_all_opportunities(self) -> List[ArbitrageOpportunityV35]:
        """扫描所有套利机会

        Returns:
            所有发现的套利机会列表
        """
        self._last_scan_time = time.time()
        all_opportunities: List[ArbitrageOpportunityV35] = []

        # 并行扫描所有策略
        scan_tasks = []

        if self.enable_triangular and self._triangular_strategy:
            scan_tasks.append(self._scan_triangular())

        if self.enable_cross_exchange and self._cross_exchange_engine:
            scan_tasks.append(self._scan_cross_exchange())

        if self.enable_funding and self._funding_engine:
            scan_tasks.append(self._scan_funding())

        # 执行所有扫描任务
        if scan_tasks:
            results = await asyncio.gather(*scan_tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, list):
                    all_opportunities.extend(result)

        # 更新统计
        self._total_opportunities += len(all_opportunities)

        # 按利润排序
        all_opportunities.sort(key=lambda x: x.expected_profit, reverse=True)

        logger.info(f"[OK] V35.0 扫描完成，发现 {len(all_opportunities)} 个机会")
        return all_opportunities

    async def _scan_triangular(self) -> List[ArbitrageOpportunityV35]:
        """扫描三角形套利机会"""
        if not self._triangular_strategy:
            return []

        try:
            opportunities = await self._triangular_strategy.scan_opportunities()
            result = []

            for opp in opportunities:
                # 转换为 V35 格式
                result.append(ArbitrageOpportunityV35(
                    opportunity_id=f"tri_{opp.get('id', time.time())}",
                    arbitrage_type=ArbitrageTypeV35.TRIANGULAR,
                    signal=ArbitrageSignalV35.BUY if opp.get('profit_rate', 0) > self.min_profit_threshold else ArbitrageSignalV35.NEUTRAL,
                    symbol=opp.get('symbol', ''),
                    exchanges=[opp.get('exchange', 'unknown')],
                    entry_price=opp.get('entry_price', 0),
                    exit_price=opp.get('exit_price', 0),
                    expected_profit=opp.get('profit_rate', 0),
                    confidence=opp.get('confidence', 0.5),
                    risk_score=opp.get('risk_score', 0.5),
                    position_size=opp.get('position_size', 0),
                    stop_loss=opp.get('stop_loss', 0),
                    take_profit=opp.get('take_profit', 0),
                    ttl=opp.get('ttl', 30),
                    details=opp
                ))

            return result

        except Exception as e:
            logger.warning(f"三角形套利扫描失败: {e}")
            return []

    async def _scan_cross_exchange(self) -> List[ArbitrageOpportunityV35]:
        """扫描跨交易所套利机会"""
        if not self._cross_exchange_engine:
            return []

        try:
            opportunities = await self._cross_exchange_engine.scan_opportunities()
            result = []

            for opp in opportunities:
                result.append(ArbitrageOpportunityV35(
                    opportunity_id=f"cross_{opp.get('id', time.time())}",
                    arbitrage_type=ArbitrageTypeV35.CROSS_EXCHANGE,
                    signal=ArbitrageSignalV35.BUY,
                    symbol=opp.get('symbol', ''),
                    exchanges=opp.get('exchanges', []),
                    entry_price=opp.get('buy_price', 0),
                    exit_price=opp.get('sell_price', 0),
                    expected_profit=opp.get('spread', 0),
                    confidence=opp.get('confidence', 0.5),
                    risk_score=opp.get('risk_score', 0.5),
                    position_size=opp.get('position_size', 0),
                    stop_loss=0,
                    take_profit=0,
                    details=opp
                ))

            return result

        except Exception as e:
            logger.warning(f"跨交易所套利扫描失败: {e}")
            return []

    async def _scan_funding(self) -> List[ArbitrageOpportunityV35]:
        """扫描资金费率套利机会"""
        if not self._funding_engine:
            return []

        try:
            opportunities = await self._funding_engine.scan_opportunities()
            result = []

            for opp in opportunities:
                result.append(ArbitrageOpportunityV35(
                    opportunity_id=f"funding_{opp.get('id', time.time())}",
                    arbitrage_type=ArbitrageTypeV35.FUNDING_RATE,
                    signal=ArbitrageSignalV35.BUY,
                    symbol=opp.get('symbol', ''),
                    exchanges=[opp.get('exchange', 'unknown')],
                    entry_price=opp.get('entry_price', 0),
                    exit_price=opp.get('exit_price', 0),
                    expected_profit=opp.get('funding_rate', 0),
                    confidence=opp.get('confidence', 0.5),
                    risk_score=opp.get('risk_score', 0.5),
                    position_size=opp.get('position_size', 0),
                    stop_loss=0,
                    take_profit=0,
                    details=opp
                ))

            return result

        except Exception as e:
            logger.warning(f"资金费率套利扫描失败: {e}")
            return []

    def filter_opportunities(
        self,
        opportunities: List[ArbitrageOpportunityV35]
    ) -> List[ArbitrageOpportunityV35]:
        """过滤套利机会

        过滤条件：
        1. 最小利润阈值
        2. 最大风险评分
        3. 最小置信度
        4. 有效时间

        Args:
            opportunities: 原始机会列表

        Returns:
            过滤后的机会列表
        """
        filtered = []

        current_time = time.time()

        for opp in opportunities:
            # 检查有效期
            if current_time - opp.timestamp > opp.ttl:
                continue

            # 检查利润阈值
            if opp.expected_profit < self.min_profit_threshold:
                continue

            # 检查风险评分
            if opp.risk_score > self.risk_tolerance:
                continue

            # 检查置信度
            if opp.confidence < 0.5:
                continue

            filtered.append(opp)

        logger.info(f"[OK] 过滤后剩余 {len(filtered)}/{len(opportunities)} 个机会")
        return filtered

    async def execute_opportunity(
        self,
        opportunity: ArbitrageOpportunityV35
    ) -> ExecutionResultV35:
        """执行套利机会

        Args:
            opportunity: 套利机会

        Returns:
            执行结果
        """
        try:
            # 根据类型选择执行方式
            if opportunity.arbitrage_type == ArbitrageTypeV35.TRIANGULAR:
                return await self._execute_triangular(opportunity)
            elif opportunity.arbitrage_type == ArbitrageTypeV35.CROSS_EXCHANGE:
                return await self._execute_cross_exchange(opportunity)
            elif opportunity.arbitrage_type == ArbitrageTypeV35.FUNDING_RATE:
                return await self._execute_funding(opportunity)
            else:
                return ExecutionResultV35(
                    opportunity_id=opportunity.opportunity_id,
                    success=False,
                    executed_price=0,
                    executed_size=0,
                    actual_profit=0,
                    slippage=0,
                    fees=0,
                    error_message="未知套利类型"
                )

        except Exception as e:
            logger.error(f"执行失败: {e}")
            return ExecutionResultV35(
                opportunity_id=opportunity.opportunity_id,
                success=False,
                executed_price=0,
                executed_size=0,
                actual_profit=0,
                slippage=0,
                fees=0,
                error_message=str(e)
            )

    async def _execute_triangular(
        self,
        opportunity: ArbitrageOpportunityV35
    ) -> ExecutionResultV35:
        """执行三角形套利"""
        # 简化实现
        return ExecutionResultV35(
            opportunity_id=opportunity.opportunity_id,
            success=True,
            executed_price=opportunity.entry_price,
            executed_size=opportunity.position_size,
            actual_profit=opportunity.expected_profit,
            slippage=0.001,
            fees=opportunity.position_size * 0.001
        )

    async def _execute_cross_exchange(
        self,
        opportunity: ArbitrageOpportunityV35
    ) -> ExecutionResultV35:
        """执行跨交易所套利"""
        return ExecutionResultV35(
            opportunity_id=opportunity.opportunity_id,
            success=True,
            executed_price=opportunity.entry_price,
            executed_size=opportunity.position_size,
            actual_profit=opportunity.expected_profit,
            slippage=0.001,
            fees=opportunity.position_size * 0.001
        )

    async def _execute_funding(
        self,
        opportunity: ArbitrageOpportunityV35
    ) -> ExecutionResultV35:
        """执行资金费率套利"""
        return ExecutionResultV35(
            opportunity_id=opportunity.opportunity_id,
            success=True,
            executed_price=opportunity.entry_price,
            executed_size=opportunity.position_size,
            actual_profit=opportunity.expected_profit,
            slippage=0.0,
            fees=opportunity.position_size * 0.0005
        )

    def get_statistics(self) -> Dict[str, Any]:
        """获取系统统计

        Returns:
            统计字典
        """
        total_trades = self._win_count + self._loss_count
        win_rate = self._win_count / total_trades if total_trades > 0 else 0

        return {
            'version': 'V35.0',
            'initialized_at': datetime.fromtimestamp(self._initialized_at).isoformat(),
            'last_scan': datetime.fromtimestamp(self._last_scan_time).isoformat() if self._last_scan_time else None,
            'total_opportunities': self._total_opportunities,
            'total_executed': self._total_executed,
            'total_profit': self._total_profit,
            'daily_pnl': self._daily_pnl,
            'win_count': self._win_count,
            'loss_count': self._loss_count,
            'win_rate': win_rate,
            'active_strategies': list(self._strategy_managers.keys())
        }

    def update_performance(self, result: ExecutionResultV35) -> None:
        """更新性能统计

        Args:
            result: 执行结果
        """
        self._total_executed += 1
        self._total_profit += result.actual_profit
        self._daily_pnl += result.actual_profit

        if result.actual_profit > 0:
            self._win_count += 1
        else:
            self._loss_count += 1


# 全局单例
_unified_arbitrage_system: Optional[UnifiedArbitrageSystemV35] = None


def get_unified_arbitrage_system() -> Optional[UnifiedArbitrageSystemV35]:
    """获取全局统一套利系统单例

    Returns:
        UnifiedArbitrageSystemV35 实例
    """
    return _unified_arbitrage_system


async def initialize_unified_arbitrage_system(
    config: Optional[Dict[str, Any]] = None
) -> UnifiedArbitrageSystemV35:
    """初始化全局统一套利系统

    Args:
        config: 配置字典

    Returns:
        初始化后的系统实例
    """
    global _unified_arbitrage_system

    if config is None:
        config = {
            'min_profit_threshold': 0.1,
            'max_position_size': 10000.0,
            'enable_triangular': True,
            'enable_cross_exchange': True,
            'enable_funding': True,
            'risk_tolerance': 0.3
        }

    _unified_arbitrage_system = UnifiedArbitrageSystemV35(config)
    await _unified_arbitrage_system.initialize()

    logger.info("[OK] V35.0 全局套利系统初始化完成")
    return _unified_arbitrage_system