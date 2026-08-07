"""资金管理系统 V3.7 - 科学仓位控制和资金配置

实现科学的资金管理，确保交易系统的长期稳定性和盈利能力。
核心功能：
1. 凯利公式仓位管理 - 基于胜率和风险回报比的科学仓位
2. 风险平价配置 - 多策略风险平价资金分配
3. 动态资金调整 - 基于市场状况的资金配置
4. 资金使用效率优化 - 最大化资金利用率
5. 与 Memo0 智能集成 - 基于历史数据的智能决策
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from collections import defaultdict
import statistics

from llm.memo0_decision_support import MarketContext
from storage.mem0_storage import Memo0Storage


logger = logging.getLogger(__name__)


@dataclass
class StrategyPerformance:
    """策略性能数据（用于资金管理）"""
    strategy_name: str
    total_trades: int
    profitable_trades: int
    win_rate: float
    avg_profit_per_trade: float
    avg_loss_per_trade: float
    risk_reward_ratio: float
    max_drawdown: float
    sharpe_ratio: float
    last_update: datetime


@dataclass
class PositionAllocation:
    """仓位分配方案"""
    strategy_name: str
    position_size: float  # USD
    position_weight: float  # % of capital
    risk_amount: float  # USD at risk
    reasoning: str


@dataclass
class CapitalAllocation:
    """资金配置方案"""
    allocations: List[PositionAllocation]
    total_capital: float
    allocated_capital: float
    unallocated_capital: float
    allocation_efficiency: float
    max_risk_amount: float
    reasoning: str


class KellyCriterion:
    """凯利公式计算器"""

    @staticmethod
    def calculate_kelly_fraction(
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        kelly_fraction: float = 0.5  # 半凯利，更保守
    ) -> float:
        """计算凯利公式仓位比例

        Args:
            win_rate: 胜率 (0-1)
            avg_win: 平均盈利
            avg_loss: 平均亏损（绝对值）
            kelly_fraction: 凯利系数（通常使用半凯利）

        Returns:
            凯利仓位比例 (0-1)
        """
        if avg_loss <= 0:
            return 0.0

        # 凯利公式: f* = (bp - q) / b
        # b = avg_win / avg_loss (赔率）
        # p = win_rate (胜率）
        # q = 1 - p (败率）
        b = avg_win / avg_loss
        p = win_rate
        q = 1 - p

        if b <= 0:
            return 0.0

        kelly = (b * p - q) / b

        # 应用半凯利和限制
        kelly = max(0, kelly) * kelly_fraction

        # 限制最大仓位为20%
        kelly = min(kelly, 0.2)

        return kelly


class RiskParity:
    """风险平价计算器"""

    @staticmethod
    def calculate_risk_parity_weights(
        strategies: Dict[str, float],
        correlation_matrix: Optional[Dict[str, Dict[str, float]]] = None
    ) -> Dict[str, float]:
        """计算风险平价权重

        Args:
            strategies: 策略名称到风险（标准差）的映射
            correlation_matrix: 策略相关性矩阵（可选）

        Returns:
            策略权重字典
        """
        # 简化版本：基于风险倒数分配权重
        total_risk = sum(1.0 / risk for risk in strategies.values())

        weights = {
            strategy: (1.0 / risk) / total_risk
            for strategy, risk in strategies.items()
        }

        return weights

    @staticmethod
    def optimize_for_target_risk(
        returns: Dict[str, List[float]],
        target_risk: float = 0.02
    ) -> Dict[str, float]:
        """优化权重以匹配目标风险

        Args:
            returns: 各策略收益率历史
            target_risk: 目标风险（标准差）

        Returns:
            优化后的权重
        """
        # 简化版本：等权重分配
        num_strategies = len(returns)
        equal_weight = 1.0 / num_strategies if num_strategies > 0 else 0.0

        return {strategy: equal_weight for strategy in returns.keys()}


class CapitalManager:
    """资金管理系统 V3.7

    实现科学的资金管理和仓位控制。
    """

    def __init__(
        self,
        config: Dict[str, Any],
        memo0_storage: Optional[Memo0Storage] = None
    ):
        """初始化资金管理器

        Args:
            config: 配置字典，包含:
                - total_capital: 总资金
                - risk_per_trade: 单笔交易风险 (%)
                - max_total_risk: 最大总风险 (%)
                - min_cash_reserve: 最小现金储备 (%)
                - default_allocation_method: 默认分配方法
            memo0_storage: Memo0 存储（用于智能决策）
        """
        self.config = config
        self.memo0 = memo0_storage

        # 资金配置
        self.total_capital = config.get('total_capital', 10000.0)
        self.risk_per_trade = config.get('risk_per_trade', 0.01)  # 1%
        self.max_total_risk = config.get('max_total_risk', 0.03)  # 3%
        self.min_cash_reserve = config.get('min_cash_reserve', 0.1)  # 10%

        # 计算器
        self.kelly_calculator = KellyCriterion()
        self.risk_parity_calculator = RiskParity()

        # 策略性能历史
        self.strategy_performances: Dict[str, StrategyPerformance] = {}
        self.performance_history: List[Dict] = []

        # 当前仓位
        self.current_positions: Dict[str, float] = {}
        self.total_exposure: float = 0.0

        # 配置历史
        self.allocation_history: List[CapitalAllocation] = []

        logger.info(f"资金管理系统初始化完成 - 总资金: ${self.total_capital:.2f}")

    def calculate_optimal_position(
        self,
        strategy_name: str,
        performance: StrategyPerformance,
        opportunity: Dict[str, Any]
    ) -> PositionAllocation:
        """计算最优仓位

        Args:
            strategy_name: 策略名称
            performance: 策略性能
            opportunity: 交易机会

        Returns:
            仓位分配方案
        """
        # 1. 计算凯利仓位
        kelly_fraction = self.kelly_calculator.calculate_kelly_fraction(
            win_rate=performance.win_rate,
            avg_win=performance.avg_profit_per_trade,
            avg_loss=abs(performance.avg_loss_per_trade) if performance.avg_loss_per_trade < 0 else 1.0,
            kelly_fraction=0.5  # 半凯利
        )

        # 2. 基于风险限制调整
        base_position = self.total_capital * kelly_fraction
        max_risk_amount = self.total_capital * self.risk_per_trade

        # 3. 考虑机会质量
        opportunity_quality = opportunity.get('confidence', 0.5)
        quality_multiplier = 0.5 + opportunity_quality * 0.5  # 0.5 - 1.0

        # 4. 考虑市场条件
        market_condition = opportunity.get('market_regime', 'normal')
        if market_condition == 'volatile':
            risk_multiplier = 0.7
        elif market_condition == 'low_volatility':
            risk_multiplier = 1.2
        else:
            risk_multiplier = 1.0

        # 5. 计算最终仓位
        adjusted_position = (
            base_position *
            quality_multiplier *
            risk_multiplier
        )

        # 确保不超过风险限制
        position_risk = adjusted_position * 0.02  # 假设2%的止损
        if position_risk > max_risk_amount:
            adjusted_position = max_risk_amount / 0.02

        # 确保不超过可用资金
        available_capital = self.total_capital - self.total_exposure
        adjusted_position = min(adjusted_position, available_capital)

        position_weight = adjusted_position / self.total_capital if self.total_capital > 0 else 0.0

        return PositionAllocation(
            strategy_name=strategy_name,
            position_size=adjusted_position,
            position_weight=position_weight,
            risk_amount=position_risk,
            reasoning=f"凯利仓位: {kelly_fraction:.2%}, 质量调整: {quality_multiplier:.2f}, 市场调整: {risk_multiplier:.2f}"
        )

    def allocate_capital(
        self,
        strategies: List[str],
        market_context: MarketContext,
        allocation_method: Optional[str] = None
    ) -> CapitalAllocation:
        """分配资金给多个策略

        Args:
            strategies: 策略列表
            market_context: 市场上下文
            allocation_method: 分配方法 (kelly/risk_parity/equal)

        Returns:
            资金配置方案
        """
        method = allocation_method or self.config.get('default_allocation_method', 'equal')

        logger.info(f"分配资金给 {len(strategies)} 个策略 - 方法: {method}")

        # 获取策略性能
        performances = {
            s: self.strategy_performances.get(s)
            for s in strategies
            if s in self.strategy_performances
        }

        # 过滤掉没有性能数据的策略
        valid_strategies = [s for s in strategies if performances.get(s)]
        if not valid_strategies:
            logger.warning("没有可用的策略性能数据，使用等权重分配")
            valid_strategies = strategies
            method = 'equal'

        # 根据方法分配资金
        allocations = []

        if method == 'kelly':
            allocations = self._allocate_by_kelly(valid_strategies, market_context)
        elif method == 'risk_parity':
            allocations = self._allocate_by_risk_parity(valid_strategies, market_context)
        else:  # equal
            allocations = self._allocate_equal(valid_strategies, market_context)

        # 计算分配汇总
        total_allocated = sum(a.position_size for a in allocations)
        unallocated = self.total_capital - total_allocated
        efficiency = total_allocated / self.total_capital if self.total_capital > 0 else 0.0

        # 计算最大风险
        max_risk = sum(a.risk_amount for a in allocations)

        allocation = CapitalAllocation(
            allocations=allocations,
            total_capital=self.total_capital,
            allocated_capital=total_allocated,
            unallocated_capital=unallocated,
            allocation_efficiency=efficiency,
            max_risk_amount=max_risk,
            reasoning=f"使用 {method} 方法分配资金"
        )

        # 记录历史
        self.allocation_history.append(allocation)

        # 保持最近100条记录
        if len(self.allocation_history) > 100:
            self.allocation_history = self.allocation_history[-100:]

        logger.info(f"资金分配完成 - 分配: {efficiency:.1%}, 总风险: ${max_risk:.2f}")

        return allocation

    def _allocate_by_kelly(
        self,
        strategies: List[str],
        market_context: MarketContext
    ) -> List[PositionAllocation]:
        """基于凯利公式分配资金"""
        allocations = []

        # 计算每个策略的凯利权重
        kelly_weights = {}
        total_kelly = 0.0

        for strategy in strategies:
            perf = self.strategy_performances.get(strategy)
            if not perf:
                continue

            kelly_fraction = self.kelly_calculator.calculate_kelly_fraction(
                win_rate=perf.win_rate,
                avg_win=perf.avg_profit_per_trade,
                avg_loss=abs(perf.avg_loss_per_trade) if perf.avg_loss_per_trade < 0 else 1.0
            )

            # 根据市场制式调整
            market_adjustment = self._get_market_adjustment(market_context, strategy)
            kelly_fraction *= market_adjustment

            kelly_weights[strategy] = kelly_fraction
            total_kelly += kelly_fraction

        # 归一化并分配资金
        if total_kelly > 0:
            for strategy, kelly in kelly_weights.items():
                weight = kelly / total_kelly
                position_size = self.total_capital * weight
                risk_amount = position_size * self.risk_per_trade

                allocations.append(PositionAllocation(
                    strategy_name=strategy,
                    position_size=position_size,
                    position_weight=weight,
                    risk_amount=risk_amount,
                    reasoning=f"凯利权重: {kelly:.2%}"
                ))

        return allocations

    def _allocate_by_risk_parity(
        self,
        strategies: List[str],
        market_context: MarketContext
    ) -> List[PositionAllocation]:
        """基于风险平价分配资金"""
        # 使用最大回撤作为风险指标
        risk_values = {}
        for strategy in strategies:
            perf = self.strategy_performances.get(strategy)
            if not perf:
                continue
            risk_values[strategy] = perf.max_drawdown

        # 计算风险平价权重
        if not risk_values:
            return self._allocate_equal(strategies, market_context)

        weights = self.risk_parity_calculator.calculate_risk_parity_weights(risk_values)

        # 分配资金
        allocations = []
        for strategy, weight in weights.items():
            position_size = self.total_capital * weight
            risk_amount = position_size * (risk_values[strategy] / 100.0)

            allocations.append(PositionAllocation(
                strategy_name=strategy,
                position_size=position_size,
                position_weight=weight,
                risk_amount=risk_amount,
                reasoning=f"风险平价权重: {weight:.2%}"
            ))

        return allocations

    def _allocate_equal(
        self,
        strategies: List[str],
        market_context: MarketContext
    ) -> List[PositionAllocation]:
        """等权重分配资金"""
        if not strategies:
            return []

        weight = 1.0 / len(strategies)
        allocations = []

        for strategy in strategies:
            position_size = self.total_capital * weight
            risk_amount = position_size * self.risk_per_trade

            allocations.append(PositionAllocation(
                strategy_name=strategy,
                position_size=position_size,
                position_weight=weight,
                risk_amount=risk_amount,
                reasoning="等权重分配"
            ))

        return allocations

    def _get_market_adjustment(
        self,
        market_context: MarketContext,
        strategy: str
    ) -> float:
        """获取市场制式调整因子"""
        regime = market_context.market_regime
        trend = market_context.trend

        # 基于策略类型和市场制式的调整
        adjustments = {
            'cross_exchange_arbitrage': {
                'bullish': 1.2,
                'bearish': 0.8,
                'volatile': 0.6,
                'stable': 1.1
            },
            'triangular_arbitrage': {
                'bullish': 1.0,
                'bearish': 1.0,
                'volatile': 1.2,
                'stable': 0.8
            },
            'funding_rate_arbitrage': {
                'bullish': 0.9,
                'bearish': 1.3,
                'volatile': 0.8,
                'stable': 1.0
            }
        }

        strategy_adjustments = adjustments.get(strategy, {})
        adjustment = strategy_adjustments.get(regime, 1.0)

        logger.debug(f"策略 {strategy} 在 {regime} 制式下的调整因子: {adjustment:.2f}")
        return adjustment

    def update_strategy_performance(
        self,
        strategy_name: str,
        trade_history: List[Dict[str, Any]]
    ) -> None:
        """更新策略性能数据

        Args:
            strategy_name: 策略名称
            trade_history: 交易历史
        """
        if not trade_history:
            return

        # 计算性能指标
        total_trades = len(trade_history)
        profitable_trades = sum(1 for t in trade_history if t.get('profit', 0) > 0)
        win_rate = profitable_trades / total_trades

        profits = [t.get('profit', 0) for t in trade_history if t.get('profit', 0) > 0]
        losses = [t.get('profit', 0) for t in trade_history if t.get('profit', 0) < 0]

        avg_profit = statistics.mean(profits) if profits else 0.0
        avg_loss = statistics.mean(losses) if losses else 0.0

        # 计算风险回报比
        if avg_loss != 0:
            risk_reward_ratio = avg_profit / abs(avg_loss)
        else:
            risk_reward_ratio = 0.0

        # 计算最大回撤
        cumulative = 0.0
        peak = 0.0
        max_drawdown = 0.0
        for trade in trade_history:
            cumulative += trade.get('profit', 0)
            peak = max(peak, cumulative)
            drawdown = peak - cumulative
            max_drawdown = max(max_drawdown, drawdown)

        # 计算夏普比率（简化）
        all_returns = [t.get('profit', 0) for t in trade_history]
        if len(all_returns) > 1:
            avg_return = statistics.mean(all_returns)
            std_return = statistics.stdev(all_returns)
            sharpe = avg_return / std_return if std_return > 0 else 0.0
        else:
            sharpe = 0.0

        # 更新性能数据
        performance = StrategyPerformance(
            strategy_name=strategy_name,
            total_trades=total_trades,
            profitable_trades=profitable_trades,
            win_rate=win_rate,
            avg_profit_per_trade=avg_profit,
            avg_loss_per_trade=avg_loss,
            risk_reward_ratio=risk_reward_ratio,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe,
            last_update=datetime.now()
        )

        self.strategy_performances[strategy_name] = performance

        # 记录历史
        self.performance_history.append({
            'strategy': strategy_name,
            'win_rate': win_rate,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'timestamp': datetime.now()
        })

        logger.info(f"策略 {strategy_name} 性能更新 - 胜率: {win_rate:.1%}, 夏普: {sharpe:.2f}")

        # 学习到 Memo0
        if self.memo0:
            self._learn_from_performance(performance)

    def _learn_from_performance(self, performance: StrategyPerformance) -> None:
        """从性能中学习到 Memo0"""
        try:
            learning_content = (
                f"{performance.strategy_name} 策略性能更新："
                f"胜率 {performance.win_rate:.1%}, "
                f"夏普比率 {performance.sharpe_ratio:.2f}, "
                f"最大回撤 {performance.max_drawdown:.2%}, "
                f"风险回报比 {performance.risk_reward_ratio:.2f}. "
            )

            if performance.win_rate > 0.6 and performance.sharpe_ratio > 1.0:
                learning_content += "表现优秀，建议积极使用。"
            elif performance.win_rate < 0.4 or performance.max_drawdown > 0.05:
                learning_content += "表现不佳，建议谨慎使用或优化参数。"
            else:
                learning_content += "表现一般，继续观察。"

            asyncio.create_task(self.memo0.add(
                content=learning_content,
                metadata={
                    'source': 'capital_manager',
                    'strategy': performance.strategy_name,
                    'type': 'performance_learning',
                    'timestamp': datetime.now().isoformat()
                }
            ))

        except Exception as e:
            logger.error(f"学习性能数据到 Memo0 失败: {e}")

    def get_capital_summary(self) -> Dict[str, Any]:
        """获取资金摘要

        Returns:
            资金摘要字典
        """
        available_capital = self.total_capital - self.total_exposure
        cash_reserve = self.total_capital * self.min_cash_reserve

        return {
            'total_capital': self.total_capital,
            'available_capital': available_capital,
            'total_exposure': self.total_exposure,
            'exposure_ratio': self.total_exposure / self.total_capital if self.total_capital > 0 else 0.0,
            'cash_reserve': cash_reserve,
            'usable_capital': max(0, available_capital - cash_reserve),
            'active_strategies': len(self.strategy_performances),
            'recent_allocation': self.allocation_history[-1] if self.allocation_history else None
        }

    def get_strategy_performance_summary(self) -> Dict[str, Any]:
        """获取策略性能摘要

        Returns:
            策略性能摘要
        """
        return {
            strategy: {
                'win_rate': perf.win_rate,
                'sharpe_ratio': perf.sharpe_ratio,
                'max_drawdown': perf.max_drawdown,
                'risk_reward_ratio': perf.risk_reward_ratio,
                'total_trades': perf.total_trades,
                'last_update': perf.last_update
            }
            for strategy, perf in self.strategy_performances.items()
        }


# 便捷函数
def create_capital_manager(
    config: Dict[str, Any],
    memo0_storage: Optional[Memo0Storage] = None
) -> CapitalManager:
    """创建资金管理器实例

    Args:
        config: 配置字典
        memo0_storage: Memo0 存储（可选）

    Returns:
        资金管理器实例
    """
    return CapitalManager(config, memo0_storage)