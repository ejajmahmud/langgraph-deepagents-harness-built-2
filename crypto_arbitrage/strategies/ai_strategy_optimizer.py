"""V66.0 AI策略优化器

V66.0 新增功能:
1. StrategyPerformanceAnalyzer - 策略性能分析器
2. AdaptiveParameterOptimizer - 自适应参数优化器
3. StrategyRecommendationEngine - 策略推荐引擎
4. MarketRegimeDetector - 市场状态检测器
5. StrategySelector - 策略选择器

创建时间：2026-05-08
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


# 市场状态
class MarketRegime(Enum):
    """市场状态枚举"""
    BULL = "bull"              # 牛市
    BEAR = "bear"              # 熊市
    SIDEWAYS = "sideways"      # 震荡市场
    VOLATILE = "volatile"    # 高波动
    CALM = "calm"            # 低波动


# 策略类型
class StrategyType(Enum):
    """策略类型"""
    TRIANGULAR = "triangular"
    CROSS_EXCHANGE = "cross_exchange"
    FUNDING_RATE = "funding_rate"
    STATISTICAL = "statistical"
    GRID = "grid"
    PERPETUAL = "perpetual"
    CROSS_CHAIN = "cross_chain"


# 优化目标
class OptimizationGoal(Enum):
    """优化目标"""
    MAX_RETURNS = "max_returns"
    MIN_RISK = "min_risk"
    SHARPE_RATIO = "sharpe_ratio"
    RISK_ADJUSTED = "risk_adjusted"


@dataclass
class StrategyMetrics:
    """策略指标"""
    total_return: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    trade_count: int = 0
    avg_trade_duration: float = 0.0
    volatility: float = 0.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class StrategyPerformance:
    """策略性能数据"""
    strategy_id: str
    strategy_type: StrategyType
    period_start: float
    period_end: float
    metrics: StrategyMetrics
    daily_returns: List[float] = field(default_factory=list)
    trades: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "strategy_type": self.strategy_type.value,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "metrics": {
                "total_return": self.metrics.total_return,
                "sharpe_ratio": self.metrics.sharpe_ratio,
                "max_drawdown": self.metrics.max_drawdown,
                "win_rate": self.metrics.win_rate,
                "profit_factor": self.metrics.profit_factor,
                "trade_count": self.metrics.trade_count,
                "volatility": self.metrics.volatility
            }
        }


@dataclass
class ParameterSet:
    """参数集"""
    name: str
    values: Dict[str, float]
    score: float = 0.0
    confidence: float = 0.0
    samples: int = 0


@dataclass
class OptimizationResult:
    """优化结果"""
    best_parameters: Dict[str, float]
    best_score: float
    improvement_pct: float
    iterations: int
    convergence: bool
    timestamp: float = field(default_factory=time.time)


@dataclass
class StrategyRecommendation:
    """策略推荐"""
    strategy_type: StrategyType
    confidence: float
    expected_return: float
    risk_score: float
    market_regime: MarketRegime
    parameters: Dict[str, float]
    reasoning: str


class StrategyPerformanceAnalyzer:
    """策略性能分析器

    功能：
    - 计算策略指标
    - 分析性能
    - 检测异常
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化分析器

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 默认参数
        self.risk_free_rate = self.config.get("risk_free_rate", 0.02)  # 2%无风险利率
        self.trading_days = self.config.get("trading_days", 365)

        # 性能缓存
        self.performance_cache: Dict[str, StrategyPerformance] = {}

        logger.info("策略性能分析器 V66.0 初始化完成")

    def analyze_performance(
        self,
        strategy_id: str,
        strategy_type: StrategyType,
        trades: List[Dict[str, Any]],
        period_days: int = 30
    ) -> StrategyPerformance:
        """分析策略性能

        Args:
            strategy_id: 策略ID
            strategy_type: 策略类型
            trades: 交易列表
            period_days: 分析天数

        Returns:
            策略性能数据
        """
        import math

        now = time.time()
        period_start = now - (period_days * 24 * 3600)
        period_end = now

        if not trades:
            return StrategyPerformance(
                strategy_id=strategy_id,
                strategy_type=strategy_type,
                period_start=period_start,
                period_end=period_end,
                metrics=StrategyMetrics()
            )

        # 计算每日收益
        daily_pnl = {}
        for trade in trades:
            timestamp = trade.get("timestamp", now)
            pnl = trade.get("pnl", 0.0)

            day = int(timestamp / 86400)
            if day not in daily_pnl:
                daily_pnl[day] = 0.0
            daily_pnl[day] += pnl

        daily_returns = list(daily_pnl.values())

        # 计算指标
        total_return = sum(daily_returns)

        # 夏普比率
        if len(daily_returns) > 1:
            returns_arr = np.array(daily_returns)
            mean_return = np.mean(returns_arr)
            std_return = np.std(returns_arr)
            if std_return > 0:
                sharpe_ratio = (mean_return - self.risk_free_rate / self.trading_days) / std_return * math.sqrt(self.trading_days)
            else:
                sharpe_ratio = 0.0
        else:
            sharpe_ratio = 0.0
            mean_return = total_return

        # 最大回撤
        cumulative = np.cumsum([0] + daily_returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdowns = cumulative - running_max
        max_drawdown = abs(min(drawdowns))

        # 胜率
        winning_trades = sum(1 for pnl in daily_returns if pnl > 0)
        win_rate = winning_trades / len(daily_returns) if daily_returns else 0.0

        # 盈利因子
        gross_profit = sum(pnl for pnl in daily_returns if pnl > 0)
        gross_loss = abs(sum(pnl for pnl in daily_returns if pnl < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0

        # 波动率
        volatility = np.std(daily_returns) if daily_returns else 0.0

        # 平均交易时长
        avg_duration = 0.0

        metrics = StrategyMetrics(
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            profit_factor=profit_factor,
            trade_count=len(trades),
            avg_trade_duration=avg_duration,
            volatility=volatility
        )

        performance = StrategyPerformance(
            strategy_id=strategy_id,
            strategy_type=strategy_type,
            period_start=period_start,
            period_end=period_end,
            metrics=metrics,
            daily_returns=daily_returns,
            trades=trades
        )

        self.performance_cache[strategy_id] = performance

        return performance

    def compare_strategies(
        self,
        performances: List[StrategyPerformance]
    ) -> List[StrategyPerformance]:
        """比较策略性能

        Args:
            performances: 策略性能列表

        Returns:
            排序后的列表(按夏普比率)
        """
        return sorted(
            performances,
            key=lambda p: p.metrics.sharpe_ratio,
            reverse=True
        )

    def detect_anomalies(
        self,
        performance: StrategyPerformance,
        threshold: float = 2.0
    ) -> List[str]:
        """检测异常

        Args:
            performance: 策略性能
            threshold: 异常阈值

        Returns:
            异常列表
        """
        anomalies = []

        # 检查回撤
        if performance.metrics.max_drawdown > 0.2:
            anomalies.append(f"高回撤: {performance.metrics.max_drawdown:.1%}")

        # 检查胜率
        if performance.metrics.win_rate < 0.4:
            anomalies.append(f"低胜率: {performance.metrics.win_rate:.1%}")

        # 检查波动率
        if performance.metrics.volatility > threshold:
            anomalies.append(f"高波动: {performance.metrics.volatility:.2f}")

        return anomalies


class AdaptiveParameterOptimizer:
    """自适应参数优化器

    功能：
    - 参数优化
    - 自适应调整
    - 超参数调优
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化优化器

        Args:
            config: 配置字典
                - optimization_goal: 优化目标
                - max_iterations: 最大迭代次数
                - convergence_threshold: 收敛阈值
        """
        self.config = config or {}

        self.optimization_goal = self.config.get(
            "optimization_goal",
            OptimizationGoal.SHARPE_RATIO
        )
        self.max_iterations = self.config.get("max_iterations", 100)
        self.convergence_threshold = self.config.get("convergence_threshold", 0.01)

        # 参数历史
        self.parameter_history: List[ParameterSet] = []

        logger.info("自适应参数优化器 V66.0 初始化完成")

    def optimize(
        self,
        strategy_type: StrategyType,
        base_parameters: Dict[str, float],
        historical_returns: List[float]
    ) -> OptimizationResult:
        """优化参数

        Args:
            strategy_type: 策略类型
            base_parameters: 基础参数
            historical_returns: 历史收益

        Returns:
            优化结果
        """
        import random

        current_params = base_parameters.copy()
        current_score = self._evaluate_parameters(current_params, historical_returns)

        best_params = current_params.copy()
        best_score = current_score

        iterations = 0
        improved = True

        while improved and iterations < self.max_iterations:
            improved = False
            iterations += 1

            # 尝试小幅度调整每个参数
            for param_name in current_params:
                if param_name in ["min_spread_pct", "max_position_pct", "stop_loss_pct"]:
                    # 小幅度调整
                    delta = (random.random() - 0.5) * 0.1
                    test_params = current_params.copy()
                    test_params[param_name] = max(0.001, test_params[param_name] + delta)

                    # 评估
                    test_score = self._evaluate_parameters(test_params, historical_returns)

                    if test_score > best_score:
                        best_params = test_params.copy()
                        best_score = test_score
                        improved = True

            current_params = best_params.copy()

        # 计算改进百分比
        base_score = self._evaluate_parameters(base_parameters, historical_returns)
        improvement_pct = (best_score - base_score) / abs(base_score) * 100 if base_score != 0 else 0

        # 检查收敛
        convergence = abs(best_score - current_score) < self.convergence_threshold

        result = OptimizationResult(
            best_parameters=best_params,
            best_score=best_score,
            improvement_pct=improvement_pct,
            iterations=iterations,
            convergence=convergence
        )

        return result

    def _evaluate_parameters(
        self,
        parameters: Dict[str, float],
        returns: List[float]
    ) -> float:
        """评估参数

        Args:
            parameters: 参数字典
            returns: 收益列表

        Returns:
            评分
        """
        if not returns:
            return 0.0

        returns_arr = np.array(returns)

        if self.optimization_goal == OptimizationGoal.SHARPE_RATIO:
            # 夏普比率
            mean_return = np.mean(returns_arr)
            std_return = np.std(returns_arr)
            if std_return > 0:
                return mean_return / std_return * math.sqrt(252)
            return 0.0

        elif self.optimization_goal == OptimizationGoal.MAX_RETURNS:
            # 最大化收益
            return np.sum(returns_arr)

        elif self.optimization_goal == OptimizationGoal.MIN_RISK:
            # 最小化风险
            return -np.std(returns_arr)

        else:
            # 风险调整收益
            mean_return = np.mean(returns_arr)
            std_return = np.std(returns_arr)
            if std_return > 0:
                return mean_return / std_return
            return 0.0

    def auto_adjust(
        self,
        current_params: Dict[str, float],
        performance: StrategyPerformance
    ) -> Dict[str, float]:
        """自动调整参数

        Args:
            current_params: 当前参数
            performance: 性能数据

        Returns:
            调整后的参数
        """
        new_params = current_params.copy()

        metrics = performance.metrics

        # 根据性能调整参数
        if metrics.max_drawdown > 0.15:
            # 减小仓位
            if "max_position_pct" in new_params:
                new_params["max_position_pct"] *= 0.8

            # 增加止损
            if "stop_loss_pct" in new_params:
                new_params["stop_loss_pct"] *= 0.9

        elif metrics.win_rate > 0.6 and metrics.sharpe_ratio > 1.5:
            # 性能良好，扩大仓位
            if "max_position_pct" in new_params:
                new_params["max_position_pct"] = min(
                    0.5,
                    new_params["max_position_pct"] * 1.2
                )

        if metrics.volatility > 0.05:
            # 高波动，增加止损距离
            if "stop_loss_pct" in new_params:
                new_params["stop_loss_pct"] *= 1.1

        return new_params


class MarketRegimeDetector:
    """市场状态检测器

    功能：
    - 检测市场状态
    - 识别牛熊市
    - 波动率分析
    """

    # 默认参数
    VOLATILITY_CALM = 0.02
    VOLATILITY_HIGH = 0.05

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化检测器

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 价格历史
        self.price_history: List[float] = []
        self.volume_history: List[float] = []

        # 当前状态
        self.current_regime: MarketRegime = MarketRegime.SIDEWAYS

        logger.info("市场状态检测器 V66.0 初始化完成")

    def add_price(self, price: float, volume: float = 0.0) -> None:
        """添加价格数据

        Args:
            price: 价格
            volume: 成交量
        """
        self.price_history.append(price)
        self.volume_history.append(volume)

        # 保留最近365个
        self.price_history = self.price_history[-365:]
        self.volume_history = self.volume_history[-365:]

    def detect_regime(self) -> MarketRegime:
        """检测市场状态

        Returns:
            市场状态
        """
        if len(self.price_history) < 30:
            return MarketRegime.SIDEWAYS

        recent = self.price_history[-30:]
        prices = np.array(recent)

        # 计算趋势
        first_half = np.mean(prices[:15])
        second_half = np.mean(prices[15:])
        trend = (second_half - first_half) / first_half

        # 计算波动率
        returns = np.diff(prices) / prices[:-1]
        volatility = np.std(returns)

        # 判断状态
        if volatility > self.VOLATILITY_HIGH:
            regime = MarketRegime.VOLATILE
        elif volatility < self.VOLATILITY_CALM:
            regime = MarketRegime.CALM
        elif trend > 0.05:
            regime = MarketRegime.BULL
        elif trend < -0.05:
            regime = MarketRegime.BEAR
        else:
            regime = MarketRegime.SIDEWAYS

        self.current_regime = regime

        return regime

    def get_regime_parameters(self, regime: MarketRegime) -> Dict[str, float]:
        """获取状态相关参数

        Args:
            regime: 市场状态

        Returns:
            推荐的参数
        """
        if regime == MarketRegime.BULL:
            return {
                "max_position_pct": 0.3,
                "stop_loss_pct": 0.05,
                "take_profit_pct": 0.15,
                "min_spread_pct": 0.3
            }
        elif regime == MarketRegime.BEAR:
            return {
                "max_position_pct": 0.1,
                "stop_loss_pct": 0.03,
                "take_profit_pct": 0.08,
                "min_spread_pct": 0.5
            }
        elif regime == MarketRegime.VOLATILE:
            return {
                "max_position_pct": 0.1,
                "stop_loss_pct": 0.02,
                "take_profit_pct": 0.10,
                "min_spread_pct": 0.8
            }
        else:  # CALM or SIDEWAYS
            return {
                "max_position_pct": 0.2,
                "stop_loss_pct": 0.04,
                "take_profit_pct": 0.10,
                "min_spread_pct": 0.4
            }


class StrategyRecommendationEngine:
    """策略推荐引擎

    功能：
    - 基于市场状态推荐策略
    - 策略选择
    - 动态调整
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化推荐引擎

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 子组件
        self.regime_detector = MarketRegimeDetector(config)
        self.performance_analyzer = StrategyPerformanceAnalyzer(config)

        # 策略历史性能
        self.strategy_performances: Dict[StrategyType, StrategyPerformance] = {}

        logger.info("策略推荐引擎 V66.0 初始化完成")

    def add_price_data(
        self,
        strategy_type: StrategyType,
        price: float,
        volume: float = 0.0
    ) -> None:
        """添加价格数据

        Args:
            strategy_type: 策略类型
            price: 价格
            volume: 成交量
        """
        self.regime_detector.add_price(price, volume)

    def recommend(
        self,
        available_strategies: List[StrategyType],
        market_data: Dict[str, Any]
    ) -> List[StrategyRecommendation]:
        """推荐策略

        Args:
            available_strategies: 可用策略
            market_data: 市场数据

        Returns:
            推荐列表
        """
        recommendations = []

        # 检测市场状态
        regime = self.regime_detector.detect_regime()
        regime_params = self.regime_detector.get_regime_parameters(regime)

        # 为每个策略评分
        for strategy_type in available_strategies:
            rec = self._score_strategy(strategy_type, regime, regime_params)
            if rec:
                recommendations.append(rec)

        # 按置信度排序
        recommendations.sort(key=lambda r: r.confidence, reverse=True)

        return recommendations[:3]

    def _score_strategy(
        self,
        strategy_type: StrategyType,
        regime: MarketRegime,
        regime_params: Dict[str, float]
    ) -> Optional[StrategyRecommendation]:
        """评分策略

        Args:
            strategy_type: 策略类型
            regime: 市场状态
            regime_params: 状态参数

        Returns:
            推荐或None
        """
        # 策略-状态匹配矩阵
        strategy_regime_scores = {
            (StrategyType.TRIANGULAR, MarketRegime.BULL): 0.8,
            (StrategyType.TRIANGULAR, MarketRegime.BEAR): 0.6,
            (StrategyType.TRIANGULAR, MarketRegime.SIDEWAYS): 0.9,
            (StrategyType.TRIANGULAR, MarketRegime.VOLATILE): 0.5,
            (StrategyType.CROSS_EXCHANGE, MarketRegime.BULL): 0.9,
            (StrategyType.CROSS_EXCHANGE, MarketRegime.BEAR): 0.7,
            (StrategyType.CROSS_EXCHANGE, MarketRegime.VOLATILE): 0.8,
            (StrategyType.FUNDING_RATE, MarketRegime.BULL): 0.9,
            (StrategyType.FUNDING_RATE, MarketRegime.SIDEWAYS): 0.7,
            (StrategyType.PERPETUAL, MarketRegime.SIDEWAYS): 0.8,
            (StrategyType.GRID, MarketRegime.SIDEWAYS): 0.9,
            (StrategyType.GRID, MarketRegime.CALM): 0.95,
            (StrategyType.CROSS_CHAIN, MarketRegime.VOLATILE): 0.6
        }

        base_confidence = strategy_regime_scores.get(
            (strategy_type, regime),
            0.5
        )

        # 估算预期收益
        expected_return = 0.01 * base_confidence
        risk_score = 1.0 - base_confidence

        return StrategyRecommendation(
            strategy_type=strategy_type,
            confidence=base_confidence,
            expected_return=expected_return,
            risk_score=risk_score,
            market_regime=regime,
            parameters=regime_params,
            reasoning=f"基于{regime.value}市场状态"
        )


# 全局单例
_performance_analyzer: Optional[StrategyPerformanceAnalyzer] = None
_parameter_optimizer: Optional[AdaptiveParameterOptimizer] = None
_recommendation_engine: Optional[StrategyRecommendationEngine] = None


def get_performance_analyzer() -> Optional[StrategyPerformanceAnalyzer]:
    """获取性能分析器

    Returns:
        性能分析器实例
    """
    return _performance_analyzer


def initialize_performance_analyzer(
    config: Optional[Dict[str, Any]] = None
) -> StrategyPerformanceAnalyzer:
    """初始化性能分析器

    Args:
        config: 配置字典

    Returns:
        性能分析器实例
    """
    global _performance_analyzer

    _performance_analyzer = StrategyPerformanceAnalyzer(config)
    return _performance_analyzer


def get_parameter_optimizer() -> Optional[AdaptiveParameterOptimizer]:
    """获取参数优化器

    Returns:
        参数优化器实例
    """
    return _parameter_optimizer


def initialize_parameter_optimizer(
    config: Optional[Dict[str, Any]] = None
) -> AdaptiveParameterOptimizer:
    """初始化参数优化器

    Args:
        config: 配置字典

    Returns:
        参数优化器实例
    """
    global _parameter_optimizer

    _parameter_optimizer = AdaptiveParameterOptimizer(config)
    return _parameter_optimizer


def get_recommendation_engine() -> Optional[StrategyRecommendationEngine]:
    """获取推荐引擎

    Returns:
        推荐引擎实例
    """
    return _recommendation_engine


def initialize_recommendation_engine(
    config: Optional[Dict[str, Any]] = None
) -> StrategyRecommendationEngine:
    """初始化推荐引擎

    Args:
        config: 配置字典

    Returns:
        推荐引擎实例
    """
    global _recommendation_engine

    _recommendation_engine = StrategyRecommendationEngine(config)
    return _recommendation_engine


__all__ = [
    # 枚举
    'MarketRegime',
    'StrategyType',
    'OptimizationGoal',
    # 数据类
    'StrategyMetrics',
    'StrategyPerformance',
    'ParameterSet',
    'OptimizationResult',
    'StrategyRecommendation',
    # 主类
    'StrategyPerformanceAnalyzer',
    'AdaptiveParameterOptimizer',
    'MarketRegimeDetector',
    'StrategyRecommendationEngine',
    # 工厂函数
    'get_performance_analyzer',
    'initialize_performance_analyzer',
    'get_parameter_optimizer',
    'initialize_parameter_optimizer',
    'get_recommendation_engine',
    'initialize_recommendation_engine',
]