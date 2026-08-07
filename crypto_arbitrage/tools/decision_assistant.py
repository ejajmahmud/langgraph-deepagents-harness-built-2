"""智能决策辅助器 (DecisionAssistant) - V4.0

基于历史知识提供智能决策建议。

核心功能：
1. 相似交易查询
2. 风险模式识别
3. 策略效果评估
4. 最优参数推荐
5. 决策建议生成

集成范围：
- 套利引擎
- 风险管理器
- 策略选择器
- 参数优化器
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class DecisionType(Enum):
    """决策类型"""
    TRADE = "trade"  # 交易决策
    RISK = "risk"  # 风险决策
    STRATEGY = "strategy"  # 策略决策
    PARAMETER = "parameter"  # 参数决策
    STOP = "stop"  # 停止决策


class ConfidenceLevel(Enum):
    """置信度等级"""
    LOW = "low"  # 低 (< 0.5)
    MEDIUM = "medium"  # 中 (0.5-0.7)
    HIGH = "high"  # 高 (0.7-0.9)
    VERY_HIGH = "very_high"  # 极高 (> 0.9)


@dataclass
class DecisionAdvice:
    """决策建议

    Attributes:
        decision_type: 决策类型
        recommendation: 推荐行动
        confidence: 置信度 (0-1)
        evidence: 证据列表
        risk_assessment: 风险评估
        alternatives: 替代方案
        reasoning: 推理过程
        timestamp: 时间戳
    """
    decision_type: DecisionType
    recommendation: str
    confidence: float
    evidence: List[str] = field(default_factory=list)
    risk_assessment: Dict[str, Any] = field(default_factory=dict)
    alternatives: List[str] = field(default_factory=list)
    reasoning: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class SimilarTrade:
    """相似交易

    Attributes:
        symbol: 交易对
        strategy: 策略
        profit: 利润
        risk_score: 风险分数
        similarity: 相似度 (0-1)
        timestamp: 时间戳
    """
    symbol: str
    strategy: str
    profit: float
    risk_score: float
    similarity: float
    timestamp: float


@dataclass
class StrategyPerformance:
    """策略性能

    Attributes:
        strategy_name: 策略名称
        total_trades: 总交易数
        win_rate: 胜率
        avg_profit: 平均利润
        profit_loss_ratio: 盈亏比
        max_drawdown: 最大回撤
        confidence: 置信度
    """
    strategy_name: str
    total_trades: int
    win_rate: float
    avg_profit: float
    profit_loss_ratio: float
    max_drawdown: float
    confidence: float


class DecisionAssistant:
    """智能决策辅助器

    基于历史知识提供智能决策建议。
    """

    def __init__(self, mem0_storage=None, config: Optional[Dict[str, Any]] = None):
        """初始化决策辅助器

        Args:
            mem0_storage: Memo0 存储实例
            config: 配置字典
        """
        self.mem0 = mem0_storage
        self.config = config or {}

        # 配置参数
        self.max_similar_trades = self.config.get('max_similar_trades', 5)
        self.min_similarity = self.config.get('min_similarity', 0.7)
        self.min_sample_size = self.config.get('min_sample_size', 10)
        self.cache_ttl = self.config.get('cache_ttl', 300)  # 5分钟

        # 缓存
        self._cache: Dict[str, Tuple[Any, float]] = {}

        logger.info("✅ 智能决策辅助器初始化完成")

    async def advise_on_trade(
        self,
        trade_context: Dict[str, Any]
    ) -> DecisionAdvice:
        """提供交易决策建议

        Args:
            trade_context: 交易上下文，包含：
                - symbol: 交易对
                - expected_profit: 预期利润
                - risk_score: 风险分数
                - strategy: 策略名称
                - market_conditions: 市场条件

        Returns:
            决策建议
        """
        try:
            # 1. 查找相似交易
            similar_trades = await self.find_similar_trades(trade_context)

            # 2. 分析历史表现
            analysis = self._analyze_similar_trades(similar_trades)

            # 3. 生成建议
            if analysis["avg_win_rate"] >= 0.7 and analysis["avg_profit"] > 0:
                recommendation = "建议执行交易"
                confidence = 0.8 + (analysis["avg_win_rate"] - 0.7) * 1.0
                risk_assessment = "低风险"
            elif analysis["avg_win_rate"] >= 0.5:
                recommendation = "建议谨慎执行，降低仓位"
                confidence = 0.6 + (analysis["avg_win_rate"] - 0.5) * 1.0
                risk_assessment = "中等风险"
            else:
                recommendation = "建议跳过此次交易"
                confidence = 0.7
                risk_assessment = "高风险"

            return DecisionAdvice(
                decision_type=DecisionType.TRADE,
                recommendation=recommendation,
                confidence=confidence,
                evidence=[
                    f"找到 {len(similar_trades)} 笔相似交易",
                    f"历史胜率: {analysis['avg_win_rate']:.2%}",
                    f"平均利润: {analysis['avg_profit']:.2f}",
                ],
                risk_assessment={
                    "level": risk_assessment,
                    "similar_trades": len(similar_trades),
                    "historical_win_rate": analysis["avg_win_rate"],
                },
                alternatives=self._generate_trade_alternatives(trade_context),
                reasoning=f"基于 {len(similar_trades)} 笔相似交易的历史表现"
            )

        except Exception as e:
            logger.error(f"提供交易决策建议失败: {e}")
            return DecisionAdvice(
                decision_type=DecisionType.TRADE,
                recommendation="无法提供建议，请人工决策",
                confidence=0.0,
                evidence=[],
                reasoning="系统错误"
            )

    async def advise_on_risk(
        self,
        risk_context: Dict[str, Any]
    ) -> DecisionAdvice:
        """提供风险决策建议

        Args:
            risk_context: 风险上下文，包含：
                - current_risk_score: 当前风险分数
                - risk_level: 风险级别
                - market_volatility: 市场波动率
                - position_size: 仓位大小

        Returns:
            决策建议
        """
        try:
            # 1. 查找相似风险场景
            similar_risks = await self.find_similar_risks(risk_context)

            # 2. 分析风险模式
            risk_pattern = self._analyze_risk_pattern(similar_risks)

            # 3. 生成建议
            current_risk = risk_context["current_risk_score"]
            if current_risk < 0.3:
                recommendation = "当前风险较低，可以适当增加仓位"
                confidence = 0.85
            elif current_risk < 0.6:
                recommendation = "当前风险适中，建议保持现有策略"
                confidence = 0.8
            elif current_risk < 0.8:
                recommendation = "当前风险较高，建议降低仓位或设置止损"
                confidence = 0.85
            else:
                recommendation = "当前风险极高，建议暂停交易"
                confidence = 0.9

            return DecisionAdvice(
                decision_type=DecisionType.RISK,
                recommendation=recommendation,
                confidence=confidence,
                evidence=[
                    f"当前风险分数: {current_risk:.2f}",
                    f"风险级别: {risk_context['risk_level']}",
                    f"历史相似风险次数: {len(similar_risks)}",
                ],
                risk_assessment={
                    "current_risk": current_risk,
                    "risk_level": risk_context["risk_level"],
                    "market_volatility": risk_context.get("market_volatility", 0),
                },
                alternatives=self._generate_risk_alternatives(risk_context),
                reasoning=f"基于风险分数 {current_risk:.2f} 和历史风险模式"
            )

        except Exception as e:
            logger.error(f"提供风险决策建议失败: {e}")
            return DecisionAdvice(
                decision_type=DecisionType.RISK,
                recommendation="无法提供建议，请人工决策",
                confidence=0.0,
                evidence=[],
                reasoning="系统错误"
            )

    async def advise_on_strategy(
        self,
        strategy_context: Dict[str, Any]
    ) -> DecisionAdvice:
        """提供策略选择建议

        Args:
            strategy_context: 策略上下文，包含：
                - available_strategies: 可用策略列表
                - market_conditions: 市场条件
                - risk_tolerance: 风险容忍度
                - time_horizon: 时间范围

        Returns:
            决策建议
        """
        try:
            # 1. 评估每个策略的性能
            strategy_performances = []
            for strategy_name in strategy_context["available_strategies"]:
                performance = await self.get_strategy_performance(strategy_name)
                if performance:
                    strategy_performances.append(performance)

            # 2. 选择最佳策略
            if not strategy_performances:
                # 如果没有历史数据，提供通用建议
                return DecisionAdvice(
                    decision_type=DecisionType.STRATEGY,
                    recommendation="建议使用低风险套利策略",
                    confidence=0.6,
                    evidence=["无历史数据"],
                    alternatives=[
                        "跨交易所套利",
                        "三角套利",
                        "基差交易"
                    ],
                    reasoning="基于市场条件选择低风险策略"
                )

            # 根据风险容忍度选择
            if strategy_context["risk_tolerance"] == "low":
                # 选择低风险、稳定策略
                best_strategy = max(
                    strategy_performances,
                    key=lambda x: x.win_rate if x.max_drawdown < 0.1 else 0
                )
            else:
                # 选择高收益策略
                best_strategy = max(
                    strategy_performances,
                    key=lambda x: x.avg_profit * x.win_rate
                )

            return DecisionAdvice(
                decision_type=DecisionType.STRATEGY,
                recommendation=f"推荐使用策略: {best_strategy.strategy_name}",
                confidence=best_strategy.confidence,
                evidence=[
                    f"策略胜率: {best_strategy.win_rate:.2%}",
                    f"平均利润: {best_strategy.avg_profit:.2f}",
                    f"盈亏比: {best_strategy.profit_loss_ratio:.2f}",
                ],
                risk_assessment={
                    "strategy": best_strategy.strategy_name,
                    "win_rate": best_strategy.win_rate,
                    "max_drawdown": best_strategy.max_drawdown,
                },
                alternatives=[
                    f"{s.strategy_name} (胜率: {s.win_rate:.2%})"
                    for s in strategy_performances
                    if s.strategy_name != best_strategy.strategy_name
                ][:3],
                reasoning=f"基于 {len(strategy_performances)} 个策略的历史表现"
            )

        except Exception as e:
            logger.error(f"提供策略选择建议失败: {e}")
            return DecisionAdvice(
                decision_type=DecisionType.STRATEGY,
                recommendation="无法提供建议，请人工决策",
                confidence=0.0,
                evidence=[],
                reasoning="系统错误"
            )

    async def find_similar_trades(
        self,
        trade_context: Dict[str, Any]
    ) -> List[SimilarTrade]:
        """查找相似交易

        Args:
            trade_context: 交易上下文

        Returns:
            相似交易列表
        """
        try:
            if not self.mem0:
                return []

            # 构建查询
            query = f"""
            查找相似的交易记录：
            - 交易对: {trade_context['symbol']}
            - 策略: {trade_context['strategy']}
            - 预期利润范围: {trade_context['expected_profit'] * 0.9:.2f} - {trade_context['expected_profit'] * 1.1:.2f}
            - 风险分数范围: {trade_context['risk_score'] * 0.9:.2f} - {trade_context['risk_score'] * 1.1:.2f}
            """

            # 查询 Memo0
            results = await self.mem0.search(query, limit=self.max_similar_trades * 2)

            # 转换为相似交易对象
            similar_trades = []
            for result in results:
                metadata = result.get("metadata", {})
                similar_trade = SimilarTrade(
                    symbol=metadata.get("symbol", ""),
                    strategy=metadata.get("strategy", ""),
                    profit=metadata.get("profit", 0),
                    risk_score=metadata.get("risk_score", 0),
                    similarity=metadata.get("similarity", 0.8),
                    timestamp=metadata.get("timestamp", time.time())
                )

                # 过滤低相似度交易
                if similar_trade.similarity >= self.min_similarity:
                    similar_trades.append(similar_trade)

            # 按相似度排序，返回前N个
            similar_trades.sort(key=lambda x: x.similarity, reverse=True)
            return similar_trades[:self.max_similar_trades]

        except Exception as e:
            logger.error(f"查找相似交易失败: {e}")
            return []

    async def find_similar_risks(
        self,
        risk_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """查找相似风险场景

        Args:
            risk_context: 风险上下文

        Returns:
            相似风险列表
        """
        try:
            if not self.mem0:
                return []

            # 构建查询
            query = f"""
            查找相似的风险预测记录：
            - 风险分数范围: {risk_context['current_risk_score'] * 0.9:.2f} - {risk_context['current_risk_score'] * 1.1:.2f}
            - 风险级别: {risk_context['risk_level']}
            - 市场波动率: {risk_context.get('market_volatility', 0)}
            """

            # 查询 Memo0
            results = await self.mem0.search(query, limit=self.max_similar_trades)

            # 提取元数据
            similar_risks = []
            for result in results:
                metadata = result.get("metadata", {})
                similar_risks.append(metadata)

            return similar_risks

        except Exception as e:
            logger.error(f"查找相似风险失败: {e}")
            return []

    async def get_strategy_performance(
        self,
        strategy_name: str
    ) -> Optional[StrategyPerformance]:
        """获取策略性能

        Args:
            strategy_name: 策略名称

        Returns:
            策略性能，如果不存在则返回 None
        """
        try:
            if not self.mem0:
                return None

            # 构建查询
            query = f"查找策略 {strategy_name} 的性能记录和统计数据"

            # 查询 Memo0
            results = await self.mem0.search(query, limit=20)

            if not results or len(results) < self.min_sample_size:
                return None

            # 聚合性能数据
            profits = []
            outcomes = []

            for result in results:
                metadata = result.get("metadata", {})
                if "performance" in metadata:
                    perf = metadata["performance"]
                    profits.append(perf.get("profit", 0))
                    outcomes.append(perf.get("outcome", "unknown"))

            if not profits:
                return None

            # 计算性能指标
            total_trades = len(profits)
            win_trades = sum(1 for p, o in zip(profits, outcomes) if p > 0 and o == "completed")
            win_rate = win_trades / total_trades if total_trades > 0 else 0
            avg_profit = sum(profits) / total_trades if total_trades > 0 else 0

            # 计算盈亏比
            profits_list = [p for p in profits if p > 0]
            losses_list = [abs(p) for p in profits if p < 0]
            profit_loss_ratio = (
                sum(profits_list) / len(profits_list) / (sum(losses_list) / len(losses_list))
                if profits_list and losses_list else 1.0
            )

            # 计算最大回撤（简化版）
            max_drawdown = max(losses_list) if losses_list else 0

            # 计算置信度
            confidence = min(total_trades / self.min_sample_size, 1.0)

            return StrategyPerformance(
                strategy_name=strategy_name,
                total_trades=total_trades,
                win_rate=win_rate,
                avg_profit=avg_profit,
                profit_loss_ratio=profit_loss_ratio,
                max_drawdown=max_drawdown,
                confidence=confidence
            )

        except Exception as e:
            logger.error(f"获取策略性能失败: {e}")
            return None

    def _analyze_similar_trades(
        self,
        similar_trades: List[SimilarTrade]
    ) -> Dict[str, Any]:
        """分析相似交易

        Args:
            similar_trades: 相似交易列表

        Returns:
            分析结果
        """
        if not similar_trades:
            return {
                "avg_win_rate": 0,
                "avg_profit": 0,
                "avg_risk_score": 0,
            }

        # 计算平均指标
        win_trades = sum(1 for t in similar_trades if t.profit > 0)
        avg_win_rate = win_trades / len(similar_trades) if similar_trades else 0
        avg_profit = sum(t.profit for t in similar_trades) / len(similar_trades) if similar_trades else 0
        avg_risk_score = sum(t.risk_score for t in similar_trades) / len(similar_trades) if similar_trades else 0

        return {
            "avg_win_rate": avg_win_rate,
            "avg_profit": avg_profit,
            "avg_risk_score": avg_risk_score,
        }

    def _analyze_risk_pattern(
        self,
        similar_risks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析风险模式

        Args:
            similar_risks: 相似风险列表

        Returns:
            风险模式分析
        """
        if not similar_risks:
            return {
                "pattern": "unknown",
                "frequency": 0,
                "avg_impact": 0,
            }

        # 分析风险级别分布
        risk_levels = [r.get("risk_level", "low") for r in similar_risks]
        pattern = max(set(risk_levels), key=risk_levels.count)
        frequency = risk_levels.count(pattern) / len(risk_levels) if risk_levels else 0

        return {
            "pattern": pattern,
            "frequency": frequency,
            "avg_impact": sum(r.get("risk_score", 0) for r in similar_risks) / len(similar_risks),
        }

    def _generate_trade_alternatives(
        self,
        trade_context: Dict[str, Any]
    ) -> List[str]:
        """生成交易替代方案

        Args:
            trade_context: 交易上下文

        Returns:
            替代方案列表
        """
        return [
            "降低仓位至 50%",
            "设置更严格的止损",
            "分批执行交易",
            "等待更好的市场时机"
        ]

    def _generate_risk_alternatives(
        self,
        risk_context: Dict[str, Any]
    ) -> List[str]:
        """生成风险管理替代方案

        Args:
            risk_context: 风险上下文

        Returns:
            替代方案列表
        """
        return [
            "降低仓位大小",
            "设置动态止损",
            "分散投资到多个策略",
            "暂停交易直到风险降低"
        ]

    def get_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """获取置信度等级

        Args:
            confidence: 置信度 (0-1)

        Returns:
            置信度等级
        """
        if confidence < 0.5:
            return ConfidenceLevel.LOW
        elif confidence < 0.7:
            return ConfidenceLevel.MEDIUM
        elif confidence < 0.9:
            return ConfidenceLevel.HIGH
        else:
            return ConfidenceLevel.VERY_HIGH


# 全局单例
_decision_assistant: Optional[DecisionAssistant] = None


def get_decision_assistant(mem0_storage=None, config: Optional[Dict[str, Any]] = None) -> DecisionAssistant:
    """获取决策辅助器实例

    Args:
        mem0_storage: Memo0 存储实例
        config: 配置字典

    Returns:
        DecisionAssistant 实例
    """
    global _decision_assistant

    if _decision_assistant is None:
        _decision_assistant = DecisionAssistant(mem0_storage, config)

    return _decision_assistant
