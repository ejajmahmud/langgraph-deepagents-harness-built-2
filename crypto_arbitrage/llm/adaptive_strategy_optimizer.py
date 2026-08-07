"""自适应策略优化器 V3.7
基于 Memo0 知识的自适应策略优化系统
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import statistics

from llm.memo0_decision_support import Memo0DecisionSupport, MarketContext
from storage.mem0_storage import Memo0Storage


logger = logging.getLogger(__name__)


@dataclass
class StrategyPerformance:
    """策略性能数据"""
    strategy_name: str
    total_trades: int
    profitable_trades: int
    total_profit: float
    win_rate: float
    avg_profit_per_trade: float
    max_drawdown: float
    sharpe_ratio: float
    last_update: datetime


@dataclass
class ParameterRecommendation:
    """参数推荐"""
    parameter_name: str
    current_value: float
    recommended_value: float
    reason: str
    confidence: float
    expected_improvement: float


@dataclass
class StrategyCombination:
    """策略组合推荐"""
    strategies: List[str]
    weights: List[float]
    expected_return: float
    expected_risk: float
    reasoning: str


class PerformanceAnalyzer:
    """性能分析器"""

    def __init__(self):
        self.performance_cache = {}
        self.cache_duration = timedelta(hours=1)

    async def analyze_strategy_performance(
        self,
        strategy_name: str,
        trade_history: List[Dict[str, Any]]
    ) -> StrategyPerformance:
        """分析策略性能

        Args:
            strategy_name: 策略名称
            trade_history: 交易历史

        Returns:
            策略性能数据
        """
        # 检查缓存
        cache_key = f"{strategy_name}_{len(trade_history)}"
        if cache_key in self.performance_cache:
            cached_data, cached_time = self.performance_cache[cache_key]
            if datetime.now() - cached_time < self.cache_duration:
                return cached_data

        # 计算基本指标
        total_trades = len(trade_history)
        if total_trades == 0:
            return StrategyPerformance(
                strategy_name=strategy_name,
                total_trades=0,
                profitable_trades=0,
                total_profit=0.0,
                win_rate=0.0,
                avg_profit_per_trade=0.0,
                max_drawdown=0.0,
                sharpe_ratio=0.0,
                last_update=datetime.now()
            )

        profitable_trades = sum(1 for t in trade_history if t.get('profit', 0) > 0)
        total_profit = sum(t.get('profit', 0) for t in trade_history)
        win_rate = profitable_trades / total_trades
        avg_profit = total_profit / total_trades

        # 计算最大回撤
        max_drawdown = self._calculate_max_drawdown(trade_history)

        # 计算夏普比率
        sharpe_ratio = self._calculate_sharpe_ratio(trade_history)

        performance = StrategyPerformance(
            strategy_name=strategy_name,
            total_trades=total_trades,
            profitable_trades=profitable_trades,
            total_profit=total_profit,
            win_rate=win_rate,
            avg_profit_per_trade=avg_profit,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            last_update=datetime.now()
        )

        # 缓存结果
        self.performance_cache[cache_key] = (performance, datetime.now())

        logger.info(f"策略 {strategy_name} 性能分析完成: 胜率 {win_rate:.2%}, 夏普比率 {sharpe_ratio:.2f}")
        return performance

    def _calculate_max_drawdown(self, trades: List[Dict[str, Any]]) -> float:
        """计算最大回撤"""
        if not trades:
            return 0.0

        cumulative_profit = 0.0
        peak = 0.0
        max_drawdown = 0.0

        for trade in trades:
            profit = trade.get('profit', 0)
            cumulative_profit += profit
            peak = max(peak, cumulative_profit)
            drawdown = peak - cumulative_profit
            max_drawdown = max(max_drawdown, drawdown)

        return max_drawdown

    def _calculate_sharpe_ratio(self, trades: List[Dict[str, Any]], risk_free_rate: float = 0.02) -> float:
        """计算夏普比率"""
        if len(trades) < 2:
            return 0.0

        profits = [t.get('profit', 0) for t in trades]
        avg_profit = statistics.mean(profits)

        if len(profits) > 1:
            std_dev = statistics.stdev(profits)
        else:
            std_dev = 0.0

        if std_dev == 0:
            return 0.0

        # 年化夏普比率 (假设每日交易)
        sharpe = (avg_profit - risk_free_rate / 252) / std_dev * (252 ** 0.5)
        return sharpe


class MarketRegimeDetector:
    """市场制式检测器"""

    def __init__(self):
        self.historical_context = []

    async def detect_market_regime(
        self,
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """检测市场制式

        Args:
            market_data: 市场数据

        Returns:
            市场制式信息
        """
        volatility = market_data.get('volatility', 0)
        trend = self._detect_trend(market_data)
        volume_profile = market_data.get('volume_profile', 'normal')

        # 确定制式
        if volatility > 0.08:
            regime = "high_volatility"
            description = "高波动制式 - 需要谨慎风险管理"
        elif volatility < 0.02:
            regime = "low_volatility"
            description = "低波动制式 - 可能需要更大杠杆"
        elif trend == "uptrend":
            regime = "bull_market"
            description = "牛市制式 - 偏多策略表现较好"
        elif trend == "downtrend":
            regime = "bear_market"
            description = "熊市制式 - 偏空或对冲策略表现较好"
        else:
            regime = "sideways"
            description = "震荡市制式 - 适合区间交易策略"

        # 更新历史上下文
        self.historical_context.append({
            'timestamp': datetime.now(),
            'regime': regime,
            'data': market_data
        })

        # 保持最近30天的上下文
        if len(self.historical_context) > 30:
            self.historical_context = self.historical_context[-30:]

        return {
            'regime': regime,
            'description': description,
            'trend': trend,
            'volatility': volatility,
            'volume_profile': volume_profile,
            'timestamp': datetime.now().isoformat()
        }

    def _detect_trend(self, market_data: Dict[str, Any]) -> str:
        """检测趋势"""
        ma_short = market_data.get('ma_short', 0)
        ma_long = market_data.get('ma_long', 0)
        rsi = market_data.get('rsi', 50)

        if ma_short > ma_long:
            if rsi > 70:
                return "strong_uptrend"
            else:
                return "uptrend"
        elif ma_short < ma_long:
            if rsi < 30:
                return "strong_downtrend"
            else:
                return "downtrend"
        else:
            return "sideways"


class AdaptiveStrategyOptimizer:
    """基于 Memo0 知识的自适应策略优化器"""

    def __init__(
        self,
        memo0_storage: Memo0Storage,
        decision_support: Memo0DecisionSupport
    ):
        """初始化自适应策略优化器

        Args:
            memo0_storage: Memo0 存储实例
            decision_support: 决策支持系统
        """
        self.memo0 = memo0_storage
        self.decision_support = decision_support
        self.performance_analyzer = PerformanceAnalyzer()
        self.regime_detector = MarketRegimeDetector()

        # 策略参数空间
        self.parameter_spaces = self._initialize_parameter_spaces()

        # 优化历史
        self.optimization_history = []

        logger.info("自适应策略优化器初始化完成")

    def _initialize_parameter_spaces(self) -> Dict[str, Dict[str, Tuple[float, float]]]:
        """初始化策略参数空间"""
        return {
            'cross_exchange_arbitrage': {
                'min_profit_threshold': (0.001, 0.02),  # 0.1% - 2%
                'max_position_size': (0.01, 0.1),  # 1% - 10%
                'execution_timeout': (5, 60),  # 5 - 60 seconds
                'slippage_tolerance': (0.0005, 0.005)  # 0.05% - 0.5%
            },
            'triangular_arbitrage': {
                'min_profit_threshold': (0.002, 0.03),  # 0.2% - 3%
                'max_position_size': (0.005, 0.05),  # 0.5% - 5%
                'execution_timeout': (3, 30),  # 3 - 30 seconds
                'max_gas_price': (10, 100)  # gwei
            },
            'funding_rate_arbitrage': {
                'min_funding_rate_diff': (0.001, 0.01),  # 0.1% - 1%
                'position_size_factor': (0.5, 2.0),  # 0.5x - 2x
                'rebalance_threshold': (0.0005, 0.005),  # 0.05% - 0.5%
                'max_position_duration': (1, 7)  # 1 - 7 days
            }
        }

    async def optimize_strategy_parameters(
        self,
        strategy_name: str,
        market_context: MarketContext,
        trade_history: List[Dict[str, Any]]
    ) -> List[ParameterRecommendation]:
        """优化策略参数

        Args:
            strategy_name: 策略名称
            market_context: 市场上下文
            trade_history: 交易历史

        Returns:
            参数推荐列表
        """
        try:
            # 分析当前性能
            performance = await self.performance_analyzer.analyze_strategy_performance(
                strategy_name, trade_history
            )

            # 获取相关知识
            knowledge = await self.decision_support.get_relevant_knowledge(
                market_context,
                query_type="optimization",
                limit=5
            )

            # 检测市场制式
            regime_info = await self.regime_detector.detect_market_regime({
                'volatility': market_context.volatility,
                'ma_short': market_context.technical_indicators.get('ma_short', 0),
                'ma_long': market_context.technical_indicators.get('ma_long', 0),
                'rsi': market_context.technical_indicators.get('rsi', 50),
                'volume_profile': 'normal'
            })

            # 生成参数推荐
            recommendations = await self._generate_parameter_recommendations(
                strategy_name,
                performance,
                market_context,
                regime_info,
                knowledge
            )

            # 记录优化历史
            self._record_optimization(strategy_name, recommendations, regime_info)

            logger.info(f"为策略 {strategy_name} 生成 {len(recommendations)} 条参数推荐")
            return recommendations

        except Exception as e:
            logger.error(f"优化策略参数失败: {e}")
            return []

    async def _generate_parameter_recommendations(
        self,
        strategy_name: str,
        performance: StrategyPerformance,
        market_context: MarketContext,
        regime_info: Dict[str, Any],
        knowledge: List[Any]
    ) -> List[ParameterRecommendation]:
        """生成参数推荐"""
        recommendations = []

        # 获取参数空间
        param_space = self.parameter_spaces.get(strategy_name, {})
        if not param_space:
            logger.warning(f"未知策略: {strategy_name}")
            return recommendations

        # 基于性能分析生成推荐
        if performance.total_trades > 10:  # 有足够的历史数据
            if performance.win_rate < 0.5:
                # 胜率低 - 提高阈值，减少交易频率
                if 'min_profit_threshold' in param_space:
                    current = param_space['min_profit_threshold'][0]
                    recommended = current * 1.5
                    recommendations.append(ParameterRecommendation(
                        parameter_name='min_profit_threshold',
                        current_value=current,
                        recommended_value=min(recommended, param_space['min_profit_threshold'][1]),
                        reason=f"胜率偏低 ({performance.win_rate:.1%})，建议提高利润阈值以提高交易质量",
                        confidence=0.7,
                        expected_improvement=0.15  # 预期胜率提升15%
                    ))

            if performance.max_drawdown > 0.02:  # 回撤过大
                if 'max_position_size' in param_space:
                    current = param_space['max_position_size'][1]
                    recommended = current * 0.7
                    recommendations.append(ParameterRecommendation(
                        parameter_name='max_position_size',
                        current_value=current,
                        recommended_value=max(recommended, param_space['max_position_size'][0]),
                        reason=f"最大回撤较大 ({performance.max_drawdown:.2%})，建议降低仓位以控制风险",
                        confidence=0.8,
                        expected_improvement=-0.3  # 预期回撤减少30%
                    ))

        # 基于市场制式生成推荐
        regime = regime_info['regime']
        if regime == "high_volatility":
            if 'max_position_size' in param_space:
                current = param_space['max_position_size'][1]
                recommended = current * 0.5
                recommendations.append(ParameterRecommendation(
                    parameter_name='max_position_size',
                    current_value=current,
                    recommended_value=max(recommended, param_space['max_position_size'][0]),
                    reason="高波动市场，建议降低仓位以控制风险",
                    confidence=0.85,
                    expected_improvement=-0.4  # 预期回撤减少40%
                ))

        elif regime == "low_volatility":
            if 'min_profit_threshold' in param_space:
                current = param_space['min_profit_threshold'][0]
                recommended = current * 0.8
                recommendations.append(ParameterRecommendation(
                    parameter_name='min_profit_threshold',
                    current_value=current,
                    recommended_value=max(recommended, param_space['min_profit_threshold'][0]),
                    reason="低波动市场，可以降低利润阈值以增加交易机会",
                    confidence=0.75,
                    expected_improvement=0.1  # 预期收益增加10%
                ))

        # 基于知识生成推荐
        if knowledge:
            for item in knowledge[:2]:
                # 这里可以根据知识内容生成更智能的推荐
                # 简化版本：假设知识包含参数优化建议
                pass

        return recommendations

    def _record_optimization(
        self,
        strategy_name: str,
        recommendations: List[ParameterRecommendation],
        regime_info: Dict[str, Any]
    ):
        """记录优化历史"""
        record = {
            'timestamp': datetime.now(),
            'strategy': strategy_name,
            'regime': regime_info['regime'],
            'recommendations': [
                {
                    'parameter': r.parameter_name,
                    'current': r.current_value,
                    'recommended': r.recommended_value,
                    'confidence': r.confidence
                }
                for r in recommendations
            ]
        }

        self.optimization_history.append(record)

        # 保持最近100条记录
        if len(self.optimization_history) > 100:
            self.optimization_history = self.optimization_history[-100:]

    async def recommend_strategy_combination(
        self,
        market_state: Dict[str, Any],
        available_strategies: List[str]
    ) -> StrategyCombination:
        """推荐策略组合

        Args:
            market_state: 市场状态
            available_strategies: 可用策略列表

        Returns:
            策略组合推荐
        """
        try:
            # 构建市场上下文
            context = await self.decision_support.context_builder.build_context(market_state)

            # 检测市场制式
            regime_info = await self.regime_detector.detect_market_regime(market_state)

            # 基于制式选择策略组合
            combination = self._select_strategy_combination(regime_info, available_strategies)

            logger.info(f"推荐策略组合: {combination.strategies}")
            return combination

        except Exception as e:
            logger.error(f"推荐策略组合失败: {e}")
            # 返回默认组合
            return StrategyCombination(
                strategies=['cross_exchange_arbitrage'],
                weights=[1.0],
                expected_return=0.01,
                expected_risk=0.02,
                reasoning="默认组合，由于错误无法优化"
            )

    def _select_strategy_combination(
        self,
        regime_info: Dict[str, Any],
        available_strategies: List[str]
    ) -> StrategyCombination:
        """选择策略组合"""
        regime = regime_info['regime']

        # 基于制式的策略映射
        strategy_mapping = {
            'bull_market': {
                'strategies': ['cross_exchange_arbitrage', 'triangular_arbitrage'],
                'weights': [0.6, 0.4],
                'reasoning': '牛市中，跨交易所套利和三角套利表现较好'
            },
            'bear_market': {
                'strategies': ['funding_rate_arbitrage'],
                'weights': [1.0],
                'reasoning': '熊市中，资金费率套利相对稳定'
            },
            'high_volatility': {
                'strategies': ['triangular_arbitrage'],
                'weights': [1.0],
                'reasoning': '高波动环境下，快速执行的三角套利更具优势'
            },
            'low_volatility': {
                'strategies': ['cross_exchange_arbitrage', 'funding_rate_arbitrage'],
                'weights': [0.7, 0.3],
                'reasoning': '低波动环境下，可以采用多种策略提高收益'
            },
            'sideways': {
                'strategies': ['cross_exchange_arbitrage'],
                'weights': [1.0],
                'reasoning': '震荡市中，跨交易所套利是最稳定的选择'
            }
        }

        # 获取制式对应的组合
        combination_config = strategy_mapping.get(regime, strategy_mapping['sideways'])

        # 过滤可用策略
        available_combination = [
            (s, w) for s, w in zip(combination_config['strategies'], combination_config['weights'])
            if s in available_strategies
        ]

        # 如果没有可用策略，使用第一个可用策略
        if not available_combination:
            strategies = [available_strategies[0]]
            weights = [1.0]
            reasoning = f"制式 {regime} 下没有推荐策略，使用默认策略"
        else:
            strategies = [s for s, w in available_combination]
            weights = [w for s, w in available_combination]
            reasoning = combination_config['reasoning']

        # 归一化权重
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]

        return StrategyCombination(
            strategies=strategies,
            weights=weights,
            expected_return=self._estimate_expected_return(regime),
            expected_risk=self._estimate_expected_risk(regime),
            reasoning=reasoning
        )

    def _estimate_expected_return(self, regime: str) -> float:
        """估算预期收益"""
        return_estimates = {
            'bull_market': 0.015,  # 1.5%
            'bear_market': 0.008,  # 0.8%
            'high_volatility': 0.012,  # 1.2%
            'low_volatility': 0.005,  # 0.5%
            'sideways': 0.008  # 0.8%
        }
        return return_estimates.get(regime, 0.01)

    def _estimate_expected_risk(self, regime: str) -> float:
        """估算预期风险"""
        risk_estimates = {
            'bull_market': 0.02,  # 2%
            'bear_market': 0.03,  # 3%
            'high_volatility': 0.04,  # 4%
            'low_volatility': 0.01,  # 1%
            'sideways': 0.015  # 1.5%
        }
        return risk_estimates.get(regime, 0.02)

    async def learn_from_performance(
        self,
        performance_data: Dict[str, Any]
    ) -> bool:
        """从表现数据中学习

        Args:
            performance_data: 表现数据

        Returns:
            是否成功学习
        """
        try:
            # 提取学习要点
            learning_content = self._extract_learning_content(performance_data)

            # 存储到 Memo0
            await self.memo0.add(
                content=learning_content,
                metadata={
                    'source': 'performance_learning',
                    'timestamp': datetime.now().isoformat(),
                    'strategy': performance_data.get('strategy'),
                    'regime': performance_data.get('regime'),
                    'performance': performance_data.get('performance_summary')
                }
            )

            logger.info(f"从表现数据中学习: {performance_data.get('strategy')}")
            return True

        except Exception as e:
            logger.error(f"学习失败: {e}")
            return False

    def _extract_learning_content(self, performance_data: Dict[str, Any]) -> str:
        """提取学习内容"""
        strategy = performance_data.get('strategy', 'unknown')
        regime = performance_data.get('regime', 'unknown')
        win_rate = performance_data.get('win_rate', 0)
        profit = performance_data.get('total_profit', 0)

        if win_rate > 0.6 and profit > 0:
            return f"{strategy} 策略在 {regime} 制式下表现优秀，胜率 {win_rate:.1%}，盈利 {profit:.2f}。建议在类似市场条件下积极使用此策略。"
        elif win_rate < 0.4 or profit < 0:
            return f"{strategy} 策略在 {regime} 制式下表现不佳，胜率 {win_rate:.1%}，{'盈利' if profit > 0 else '亏损'} {abs(profit):.2f}。建议在类似市场条件下谨慎使用或调整参数。"
        else:
            return f"{strategy} 策略在 {regime} 制式下表现一般，胜率 {win_rate:.1%}，{'盈利' if profit > 0 else '亏损'} {abs(profit):.2f}。可以继续观察并适度优化。"


# 便捷函数
async def create_strategy_optimizer(
    memo0_storage: Memo0Storage,
    decision_support: Memo0DecisionSupport
) -> AdaptiveStrategyOptimizer:
    """创建自适应策略优化器实例

    Args:
        memo0_storage: Memo0 存储实例
        decision_support: 决策支持系统

    Returns:
        自适应策略优化器实例
    """
    return AdaptiveStrategyOptimizer(memo0_storage, decision_support)