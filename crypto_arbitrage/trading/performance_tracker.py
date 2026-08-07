"""实盘数据收集和绩效分析系统 V3.7

实现高质量的实盘交易数据管理和全面的绩效分析。
核心功能：
1. 高质量数据收集 - 实盘交易数据的全面记录
2. 详细绩效报告 - 多维度的绩效分析
3. 风险暴露分析 - 实盘风险的详细分析
4. 归因分析 - 交易结果的多维度归因
5. 实时监控 - 绩效指标的实时计算
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict, deque
import statistics
import json

from storage.mem0_storage import Memo0Storage


logger = logging.getLogger(__name__)


@dataclass
class TradeRecord:
    """交易记录"""
    trade_id: str
    strategy: str
    entry_time: datetime
    exit_time: Optional[datetime]
    symbol: str
    entry_price: float
    exit_price: Optional[float]
    position_size: float
    trading_mode: str  # SIMULATION/PAPER_TRADING/LIVE_TRADING
    expected_profit: float
    actual_profit: Optional[float]
    execution_time: float
    slippage: float
    market_regime: str
    decision_confidence: float
    risk_amount: float
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class PerformanceMetrics:
    """绩效指标"""
    # 收益指标
    total_return: float
    annualized_return: float
    avg_return_per_trade: float
    median_return: float

    # 风险指标
    volatility: float
    max_drawdown: float
    avg_drawdown: float
    value_at_risk: float  # 95% VaR

    # 风险调整收益指标
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float

    # 交易质量指标
    win_rate: float
    profit_factor: float  # 总盈利/总亏损
    avg_win_loss_ratio: float

    # 执行质量指标
    avg_slippage: float
    avg_execution_time: float
    fill_rate: float

    # 时间维度
    avg_holding_time: float
    trades_per_day: float

    timestamp: datetime


@dataclass
class RiskAnalysis:
    """风险分析"""
    exposure_analysis: Dict[str, Any]
    concentration_risk: Dict[str, Any]
    correlation_risk: Dict[str, Any]
    tail_risk: Dict[str, Any]
    liquidity_risk: Dict[str, Any]
    recommendations: List[str]


@dataclass
class AttributionAnalysis:
    """归因分析"""
    strategy_attribution: Dict[str, Any]
    regime_attribution: Dict[str, Any]
    time_attribution: Dict[str, Any]
    execution_attribution: Dict[str, Any]
    risk_attribution: Dict[str, Any]
    insights: List[str]


class PerformanceTracker:
    """绩效跟踪器 V3.7

    实现高质量的实盘交易数据收集和绩效分析。
    """

    def __init__(
        self,
        config: Dict[str, Any],
        memo0_storage: Optional[Memo0Storage] = None
    ):
        """初始化绩效跟踪器

        Args:
            config: 配置字典
            memo0_storage: Memo0 存储（可选）
        """
        self.config = config
        self.memo0 = memo0_storage

        # 数据存储
        self.trades: List[TradeRecord] = []
        self.trades_by_strategy: Dict[str, List[TradeRecord]] = defaultdict(list)
        self.trades_by_mode: Dict[str, List[TradeRecord]] = defaultdict(list)
        self.trades_by_regime: Dict[str, List[TradeRecord]] = defaultdict(list)

        # 性能缓存
        self.performance_cache: Optional[PerformanceMetrics] = None
        self.cache_expiry: Optional[datetime] = None

        # 历史数据（用于趋势分析）
        self.daily_returns: deque = deque(maxlen=365)
        self.daily_pnl: deque = deque(maxlen=365)
        self.weekly_returns: deque = deque(maxlen=52)
        self.monthly_returns: deque = deque(maxlen=12)

        # 统计信息
        self.total_trades = 0
        self.total_profit = 0.0
        self.total_loss = 0.0
        self.start_time = datetime.now()

        logger.info("绩效跟踪器初始化完成")

    async def record_trade(
        self,
        trade_data: Dict[str, Any]
    ) -> None:
        """记录交易数据

        Args:
            trade_data: 交易数据字典
        """
        try:
            # 创建交易记录
            trade_record = TradeRecord(
                trade_id=trade_data.get('trade_id', ''),
                strategy=trade_data.get('strategy', 'unknown'),
                entry_time=trade_data.get('entry_time', datetime.now()),
                exit_time=trade_data.get('exit_time'),
                symbol=trade_data.get('symbol', ''),
                entry_price=trade_data.get('entry_price', 0.0),
                exit_price=trade_data.get('exit_price'),
                position_size=trade_data.get('position_size', 0.0),
                trading_mode=trade_data.get('trading_mode', 'SIMULATION'),
                expected_profit=trade_data.get('expected_profit', 0.0),
                actual_profit=trade_data.get('actual_profit'),
                execution_time=trade_data.get('execution_time', 0.0),
                slippage=trade_data.get('slippage', 0.0),
                market_regime=trade_data.get('market_regime', 'unknown'),
                decision_confidence=trade_data.get('decision_confidence', 0.5),
                risk_amount=trade_data.get('risk_amount', 0.0),
                notes=trade_data.get('notes'),
                metadata=trade_data.get('metadata', {})
            )

            # 添加到存储
            self.trades.append(trade_record)
            self.trades_by_strategy[trade_record.strategy].append(trade_record)
            self.trades_by_mode[trade_record.trading_mode].append(trade_record)
            self.trades_by_regime[trade_record.market_regime].append(trade_record)

            # 更新统计
            if trade_record.actual_profit is not None:
                self.total_trades += 1
                if trade_record.actual_profit > 0:
                    self.total_profit += trade_record.actual_profit
                else:
                    self.total_loss += abs(trade_record.actual_profit)

            # 清除性能缓存
            self.performance_cache = None

            logger.info(f"记录交易: {trade_record.trade_id} - 利润: {trade_record.actual_profit}")

            # 学习到 Memo0
            if self.memo0:
                await self._learn_from_trade(trade_record)

        except Exception as e:
            logger.error(f"记录交易失败: {e}")

    async def generate_performance_report(
        self,
        period: Optional[str] = None
    ) -> PerformanceMetrics:
        """生成绩效报告

        Args:
            period: 时间周期 (daily/weekly/monthly/all)

        Returns:
            绩效指标
        """
        # 检查缓存
        if (self.performance_cache and
            self.cache_expiry and
            datetime.now() < self.cache_expiry):
            return self.performance_cache

        try:
            # 过滤交易
            trades = self._filter_trades_by_period(period)

            if not trades:
                logger.warning(f"没有{period or ''}交易数据")
                return PerformanceMetrics(*[0.0]*20, timestamp=datetime.now())

            # 计算收益指标
            total_return, annualized_return, avg_return, median_return = (
                self._calculate_return_metrics(trades)
            )

            # 计算风险指标
            volatility, max_drawdown, avg_drawdown, var = self._calculate_risk_metrics(trades)

            # 计算风险调整收益指标
            sharpe, sortino, calmar = self._calculate_risk_adjusted_metrics(
                trades, avg_return, volatility, max_drawdown
            )

            # 计算交易质量指标
            win_rate, profit_factor, avg_win_loss = self._calculate_quality_metrics(trades)

            # 计算执行质量指标
            avg_slippage, avg_execution_time, fill_rate = self._calculate_execution_metrics(trades)

            # 计算时间维度
            avg_holding_time, trades_per_day = self._calculate_time_metrics(trades)

            # 创建绩效指标
            performance = PerformanceMetrics(
                total_return=total_return,
                annualized_return=annualized_return,
                avg_return_per_trade=avg_return,
                median_return=median_return,
                volatility=volatility,
                max_drawdown=max_drawdown,
                avg_drawdown=avg_drawdown,
                value_at_risk=var,
                sharpe_ratio=sharpe,
                sortino_ratio=sortino,
                calmar_ratio=calmar,
                win_rate=win_rate,
                profit_factor=profit_factor,
                avg_win_loss_ratio=avg_win_loss,
                avg_slippage=avg_slippage,
                avg_execution_time=avg_execution_time,
                fill_rate=fill_rate,
                avg_holding_time=avg_holding_time,
                trades_per_day=trades_per_day,
                timestamp=datetime.now()
            )

            # 更新缓存
            self.performance_cache = performance
            self.cache_expiry = datetime.now() + timedelta(minutes=5)

            return performance

        except Exception as e:
            logger.error(f"生成绩效报告失败: {e}")
            raise

    async def analyze_risk_exposure(self) -> RiskAnalysis:
        """分析风险暴露

        Returns:
            风险分析结果
        """
        # 敞口分析
        exposure_analysis = {
            'total_exposure': sum(t.position_size for t in self.trades if t.exit_time is None),
            'exposure_by_strategy': {
                strategy: sum(t.position_size for t in trades if t.exit_time is None)
                for strategy, trades in self.trades_by_strategy.items()
            },
            'exposure_by_regime': {
                regime: len(trades)
                for regime, trades in self.trades_by_regime.items()
            }
        }

        # 集中度风险
        concentration_risk = self._analyze_concentration_risk()

        # 相关性风险（简化版）
        correlation_risk = self._analyze_correlation_risk()

        # 尾部风险
        tail_risk = self._analyze_tail_risk()

        # 流动性风险
        liquidity_risk = self._analyze_liquidity_risk()

        # 生成建议
        recommendations = self._generate_risk_recommendations(
            exposure_analysis, concentration_risk, tail_risk
        )

        return RiskAnalysis(
            exposure_analysis=exposure_analysis,
            concentration_risk=concentration_risk,
            correlation_risk=correlation_risk,
            tail_risk=tail_risk,
            liquidity_risk=liquidity_risk,
            recommendations=recommendations
        )

    async def perform_attribution_analysis(
        self,
        trade_id: Optional[str] = None
    ) -> AttributionAnalysis:
        """进行归因分析

        Args:
            trade_id: 特定交易ID（可选）

        Returns:
            归因分析结果
        """
        # 策略归因
        strategy_attribution = self._analyze_strategy_attribution()

        # 制式归因
        regime_attribution = self._analyze_regime_attribution()

        # 时间归因
        time_attribution = self._analyze_time_attribution()

        # 执行归因
        execution_attribution = self._analyze_execution_attribution()

        # 风险归因
        risk_attribution = self._analyze_risk_attribution()

        # 生成洞察
        insights = self._generate_attribution_insights(
            strategy_attribution, regime_attribution, execution_attribution
        )

        return AttributionAnalysis(
            strategy_attribution=strategy_attribution,
            regime_attribution=regime_attribution,
            time_attribution=time_attribution,
            execution_attribution=execution_attribution,
            risk_attribution=risk_attribution,
            insights=insights
        )

    def _filter_trades_by_period(
        self,
        period: Optional[str]
    ) -> List[TradeRecord]:
        """按时间周期过滤交易"""
        if not period or period == 'all':
            return self.trades.copy()

        now = datetime.now()
        if period == 'daily':
            cutoff = now - timedelta(days=1)
        elif period == 'weekly':
            cutoff = now - timedelta(weeks=1)
        elif period == 'monthly':
            cutoff = now - timedelta(days=30)
        else:
            return self.trades.copy()

        return [t for t in self.trades if t.entry_time >= cutoff]

    def _calculate_return_metrics(
        self,
        trades: List[TradeRecord]
    ) -> Tuple[float, float, float, float]:
        """计算收益指标"""
        if not trades:
            return 0.0, 0.0, 0.0, 0.0

        # 完成的交易
        completed_trades = [t for t in trades if t.actual_profit is not None]
        if not completed_trades:
            return 0.0, 0.0, 0.0, 0.0

        returns = [t.actual_profit for t in completed_trades]
        total_return = sum(returns)

        # 年化收益（假设每日交易）
        days_elapsed = (datetime.now() - self.start_time).days
        if days_elapsed > 0:
            annualized_return = total_return / days_elapsed * 365
        else:
            annualized_return = 0.0

        avg_return = statistics.mean(returns) if returns else 0.0
        median_return = statistics.median(returns) if returns else 0.0

        return total_return, annualized_return, avg_return, median_return

    def _calculate_risk_metrics(
        self,
        trades: List[TradeRecord]
    ) -> Tuple[float, float, float, float]:
        """计算风险指标"""
        completed_trades = [t for t in trades if t.actual_profit is not None]
        if not completed_trades:
            return 0.0, 0.0, 0.0, 0.0

        returns = [t.actual_profit for t in completed_trades]

        # 波动率
        if len(returns) > 1:
            volatility = statistics.stdev(returns)
        else:
            volatility = 0.0

        # 最大回撤
        cumulative = 0.0
        peak = 0.0
        max_drawdown = 0.0
        avg_drawdown = 0.0
        drawdowns = []

        for trade in completed_trades:
            cumulative += trade.actual_profit
            peak = max(peak, cumulative)
            drawdown = peak - cumulative
            max_drawdown = max(max_drawdown, drawdown)
            if drawdown > 0:
                drawdowns.append(drawdown)

        avg_drawdown = statistics.mean(drawdowns) if drawdowns else 0.0

        # 95% VaR
        if len(returns) > 1:
            sorted_returns = sorted(returns)
            var_index = int(len(sorted_returns) * 0.05)
            var = sorted_returns[var_index] if var_index < len(sorted_returns) else sorted_returns[0]
        else:
            var = 0.0

        return volatility, max_drawdown, avg_drawdown, var

    def _calculate_risk_adjusted_metrics(
        self,
        trades: List[TradeRecord],
        avg_return: float,
        volatility: float,
        max_drawdown: float
    ) -> Tuple[float, float, float]:
        """计算风险调整收益指标"""
        if volatility == 0 or max_drawdown == 0:
            return 0.0, 0.0, 0.0

        # 夏普比率（简化版）
        sharpe = avg_return / volatility if volatility > 0 else 0.0

        # 索提诺比率（只考虑下行风险）
        completed_trades = [t for t in trades if t.actual_profit is not None]
        negative_returns = [t.actual_profit for t in completed_trades if t.actual_profit < 0]

        if negative_returns:
            downside_deviation = statistics.stdev(negative_returns)
            sortino = avg_return / downside_deviation if downside_deviation > 0 else 0.0
        else:
            sortino = 0.0

        # 卡玛比率
        calmar = avg_return / max_drawdown if max_drawdown > 0 else 0.0

        return sharpe, sortino, calmar

    def _calculate_quality_metrics(
        self,
        trades: List[TradeRecord]
    ) -> Tuple[float, float, float]:
        """计算交易质量指标"""
        completed_trades = [t for t in trades if t.actual_profit is not None]
        if not completed_trades:
            return 0.0, 0.0, 0.0

        # 胜率
        winning_trades = [t for t in completed_trades if t.actual_profit > 0]
        win_rate = len(winning_trades) / len(completed_trades)

        # 盈利因子
        total_profit = sum(t.actual_profit for t in winning_trades) if winning_trades else 0.0
        losing_trades = [t for t in completed_trades if t.actual_profit < 0]
        total_loss = sum(abs(t.actual_profit) for t in losing_trades) if losing_trades else 0.0

        profit_factor = total_profit / total_loss if total_loss > 0 else 0.0

        # 平均盈亏比
        avg_win = statistics.mean([t.actual_profit for t in winning_trades]) if winning_trades else 0.0
        avg_loss = statistics.mean([abs(t.actual_profit) for t in losing_trades]) if losing_trades else 0.0
        avg_win_loss = avg_win / avg_loss if avg_loss > 0 else 0.0

        return win_rate, profit_factor, avg_win_loss

    def _calculate_execution_metrics(
        self,
        trades: List[TradeRecord]
    ) -> Tuple[float, float, float]:
        """计算执行质量指标"""
        if not trades:
            return 0.0, 0.0, 0.0

        # 平均滑点
        slippages = [t.slippage for t in trades]
        avg_slippage = statistics.mean(slippages) if slippages else 0.0

        # 平均执行时间
        execution_times = [t.execution_time for t in trades]
        avg_execution_time = statistics.mean(execution_times) if execution_times else 0.0

        # 成交率（假设所有记录的交易都成交）
        fill_rate = 1.0

        return avg_slippage, avg_execution_time, fill_rate

    def _calculate_time_metrics(
        self,
        trades: List[TradeRecord]
    ) -> Tuple[float, float]:
        """计算时间维度指标"""
        completed_trades = [t for t in trades if t.exit_time is not None]
        if not completed_trades:
            return 0.0, 0.0

        # 平均持仓时间
        holding_times = [
            (t.exit_time - t.entry_time).total_seconds()
            for t in completed_trades
        ]
        avg_holding_time = statistics.mean(holding_times) if holding_times else 0.0

        # 每日交易数
        days_elapsed = (datetime.now() - self.start_time).days
        trades_per_day = len(trades) / days_elapsed if days_elapsed > 0 else 0.0

        return avg_holding_time, trades_per_day

    def _analyze_concentration_risk(self) -> Dict[str, Any]:
        """分析集中度风险"""
        if not self.trades:
            return {}

        # 策略集中度
        strategy_counts = defaultdict(int)
        for trade in self.trades:
            strategy_counts[trade.strategy] += 1

        total_trades = len(self.trades)
        strategy_concentration = {
            strategy: count / total_trades
            for strategy, count in strategy_counts.items()
        }

        # 最大集中度
        max_concentration = max(strategy_concentration.values()) if strategy_concentration else 0.0

        return {
            'strategy_concentration': strategy_concentration,
            'max_concentration': max_concentration,
            'risk_level': 'HIGH' if max_concentration > 0.7 else 'MEDIUM' if max_concentration > 0.4 else 'LOW'
        }

    def _analyze_correlation_risk(self) -> Dict[str, Any]:
        """分析相关性风险（简化版）"""
        # 在实际实现中，这里会计算策略之间的相关性
        # 暂时返回简化版本
        return {
            'note': '相关性分析需要更多历史数据',
            'risk_level': 'UNKNOWN'
        }

    def _analyze_tail_risk(self) -> Dict[str, Any]:
        """分析尾部风险"""
        completed_trades = [t for t in self.trades if t.actual_profit is not None]
        if not completed_trades:
            return {}

        returns = [t.actual_profit for t in completed_trades]
        sorted_returns = sorted(returns)

        # 尾部风险指标
        worst_5_pct = sorted_returns[:max(1, int(len(sorted_returns) * 0.05))]
        tail_risk = sum(worst_5_pct) if worst_5_pct else 0.0

        return {
            'worst_5_percent': worst_5_pct,
            'tail_risk': tail_risk,
            'risk_level': 'HIGH' if tail_risk < -100 else 'MEDIUM' if tail_risk < -50 else 'LOW'
        }

    def _analyze_liquidity_risk(self) -> Dict[str, Any]:
        """分析流动性风险"""
        # 基于交易符号和时间分析
        recent_trades = [
            t for t in self.trades
            if (datetime.now() - t.entry_time).total_seconds() < 3600
        ]

        symbol_counts = defaultdict(int)
        for trade in recent_trades:
            symbol_counts[trade.symbol] += 1

        return {
            'recent_symbols': list(symbol_counts.keys()),
            'diversification_score': len(symbol_counts),
            'risk_level': 'LOW'
        }

    def _generate_risk_recommendations(
        self,
        exposure: Dict,
        concentration: Dict,
        tail: Dict
    ) -> List[str]:
        """生成风险建议"""
        recommendations = []

        if concentration.get('max_concentration', 0) > 0.7:
            recommendations.append("策略集中度较高，建议分散到多个策略")

        if tail.get('risk_level') == 'HIGH':
            recommendations.append("尾部风险较高，建议降低仓位或增加止损保护")

        if exposure.get('total_exposure', 0) > 8000:
            recommendations.append("总敞口较高，建议减少开仓")

        if not recommendations:
            recommendations.append("风险水平正常")

        return recommendations

    def _analyze_strategy_attribution(self) -> Dict[str, Any]:
        """分析策略归因"""
        attribution = {}
        for strategy, trades in self.trades_by_strategy.items():
            completed_trades = [t for t in trades if t.actual_profit is not None]
            if not completed_trades:
                continue

            total_profit = sum(t.actual_profit for t in completed_trades)
            attribution[strategy] = {
                'total_profit': total_profit,
                'trade_count': len(completed_trades),
                'avg_profit': total_profit / len(completed_trades)
            }

        return attribution

    def _analyze_regime_attribution(self) -> Dict[str, Any]:
        """分析制式归因"""
        attribution = {}
        for regime, trades in self.trades_by_regime.items():
            completed_trades = [t for t in trades if t.actual_profit is not None]
            if not completed_trades:
                continue

            total_profit = sum(t.actual_profit for t in completed_trades)
            win_rate = len([t for t in completed_trades if t.actual_profit > 0]) / len(completed_trades)

            attribution[regime] = {
                'total_profit': total_profit,
                'trade_count': len(completed_trades),
                'win_rate': win_rate
            }

        return attribution

    def _analyze_time_attribution(self) -> Dict[str, Any]:
        """分析时间归因"""
        # 按小时分析
        hourly_performance = defaultdict(lambda: {'profit': 0.0, 'trades': 0})

        for trade in self.trades:
            if trade.actual_profit is None:
                continue

            hour = trade.entry_time.hour
            hourly_performance[hour]['profit'] += trade.actual_profit
            hourly_performance[hour]['trades'] += 1

        return {
            'hourly_performance': dict(hourly_performance),
            'best_hour': max(hourly_performance.keys(), key=lambda h: hourly_performance[h]['profit']) if hourly_performance else None
        }

    def _analyze_execution_attribution(self) -> Dict[str, Any]:
        """分析执行归因"""
        # 按交易模式分析
        mode_analysis = {}
        for mode, trades in self.trades_by_mode.items():
            completed_trades = [t for t in trades if t.actual_profit is not None]
            if not completed_trades:
                continue

            total_profit = sum(t.actual_profit for t in completed_trades)
            avg_slippage = statistics.mean([t.slippage for t in completed_trades])
            win_rate = len([t for t in completed_trades if t.actual_profit > 0]) / len(completed_trades)

            mode_analysis[mode] = {
                'total_profit': total_profit,
                'avg_slippage': avg_slippage,
                'win_rate': win_rate,
                'trade_count': len(completed_trades)
            }

        return mode_analysis

    def _analyze_risk_attribution(self) -> Dict[str, Any]:
        """分析风险归因"""
        # 按风险金额分析
        completed_trades = [t for t in self.trades if t.actual_profit is not None]
        if not completed_trades:
            return {}

        # 风险分组
        low_risk_trades = [t for t in completed_trades if t.risk_amount < 50]
        medium_risk_trades = [t for t in completed_trades if 50 <= t.risk_amount < 100]
        high_risk_trades = [t for t in completed_trades if t.risk_amount >= 100]

        return {
            'low_risk': {
                'count': len(low_risk_trades),
                'avg_profit': statistics.mean([t.actual_profit for t in low_risk_trades]) if low_risk_trades else 0.0
            },
            'medium_risk': {
                'count': len(medium_risk_trades),
                'avg_profit': statistics.mean([t.actual_profit for t in medium_risk_trades]) if medium_risk_trades else 0.0
            },
            'high_risk': {
                'count': len(high_risk_trades),
                'avg_profit': statistics.mean([t.actual_profit for t in high_risk_trades]) if high_risk_trades else 0.0
            }
        }

    def _generate_attribution_insights(
        self,
        strategy_attribution: Dict,
        regime_attribution: Dict,
        execution_attribution: Dict
    ) -> List[str]:
        """生成归因洞察"""
        insights = []

        # 策略洞察
        if strategy_attribution:
            best_strategy = max(strategy_attribution.items(), key=lambda x: x[1]['total_profit'])
            insights.append(f"表现最佳策略: {best_strategy[0]} (利润: ${best_strategy[1]['total_profit']:.2f})")

        # 制式洞察
        if regime_attribution:
            best_regime = max(regime_attribution.items(), key=lambda x: x[1]['win_rate'])
            insights.append(f"最佳市场制式: {best_regime[0]} (胜率: {best_regime[1]['win_rate']:.1%})")

        # 执行洞察
        if execution_attribution:
            live_trading = execution_attribution.get('LIVE_TRADING', {})
            if live_trading:
                insights.append(f"实盘交易: {live_trading.get('trade_count', 0)} 笔, 平均滑点: {live_trading.get('avg_slippage', 0):.4f}")

        return insights

    async def _learn_from_trade(self, trade: TradeRecord) -> None:
        """从交易中学习到 Memo0"""
        try:
            if trade.actual_profit is None:
                return

            performance_desc = "盈利" if trade.actual_profit > 0 else "亏损"
            learning_content = (
                f"{trade.strategy} 策略在 {trade.market_regime} 制式下 "
                f"{performance_desc} ${abs(trade.actual_profit):.2f}。"
                f"决策置信度: {trade.decision_confidence:.2%}, "
                f"风险金额: ${trade.risk_amount:.2f}, "
                f"滑点: {trade.slippage:.4f}。"
            )

            # 添加到 Memo0
            await self.memo0.add(
                content=learning_content,
                metadata={
                    'source': 'performance_tracker',
                    'strategy': trade.strategy,
                    'trade_id': trade.trade_id,
                    'market_regime': trade.market_regime,
                    'profit': trade.actual_profit,
                    'type': 'trade_learning',
                    'timestamp': datetime.now().isoformat()
                }
            )

        except Exception as e:
            logger.error(f"学习交易数据到 Memo0 失败: {e}")

    def get_summary(self) -> Dict[str, Any]:
        """获取摘要信息"""
        return {
            'total_trades': self.total_trades,
            'total_profit': self.total_profit,
            'total_loss': self.total_loss,
            'net_profit': self.total_profit - self.total_loss,
            'trades_by_strategy': {s: len(t) for s, t in self.trades_by_strategy.items()},
            'trades_by_mode': {m: len(t) for m, t in self.trades_by_mode.items()},
            'running_time': (datetime.now() - self.start_time).total_seconds()
        }


# 便捷函数
def create_performance_tracker(
    config: Dict[str, Any],
    memo0_storage: Optional[Memo0Storage] = None
) -> PerformanceTracker:
    """创建绩效跟踪器实例

    Args:
        config: 配置字典
        memo0_storage: Memo0 存储（可选）

    Returns:
        绩效跟踪器实例
    """
    return PerformanceTracker(config, memo0_storage)