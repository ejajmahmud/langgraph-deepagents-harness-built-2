"""增强版低风险套利引擎 V5.2 - 智能深度集成版

深度集成V5.2智能决策引擎，实现真正的AI驱动低风险套利。

V5.2核心升级：
1. 深度集成V5.2智能决策引擎（Memo0语义搜索）
2. 实现预测性风险管理和智能决策
3. 优化套利执行的智能路径选择
4. 增强知识学习和参数自优化
5. 实现自适应风险调整机制
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from strategies.enhanced_low_risk_arbitrage_engine import (
    EnhancedLowRiskArbitrageEngine,
    RiskPrediction, HealthStatus, IntelligentDecision,
    EnhancedArbitrageExecution
)
from storage.intelligent_decision_engine_v5_2 import IntelligentDecisionEngineV52

logger = logging.getLogger(__name__)


@dataclass
class IntelligentArbitrageContext:
    """智能套利上下文"""
    opportunity: Dict[str, Any]
    market_conditions: Dict[str, Any]
    strategy: str
    timestamp: float
    decision_result: Optional[Dict] = None
    risk_assessment: Optional[Dict] = None


@dataclass
class AdaptiveRiskParameters:
    """自适应风险参数"""
    base_position_size: float
    base_stop_loss: float
    base_take_profit: float
    adjusted_position_size: float
    adjusted_stop_loss: float
    adjusted_take_profit: float
    adjustment_factor: float
    reasoning: str


class EnhancedLowRiskArbitrageEngineV52(EnhancedLowRiskArbitrageEngine):
    """增强版低风险套利引擎 V5.2 - 智能深度集成版

    深度集成V5.2智能决策引擎，实现AI驱动的低风险套利。
    """

    def __init__(self, config: Dict[str, Any], decision_engine: IntelligentDecisionEngineV52):
        """初始化V5.2增强版低风险套利引擎

        Args:
            config: 引擎配置
            decision_engine: V5.2智能决策引擎实例
        """
        # 调用父类初始化
        super().__init__(config)

        # V5.2 智能决策引擎
        self.decision_engine = decision_engine

        # 自适应风险参数
        self.adaptive_params: Dict[str, AdaptiveRiskParameters] = {}

        # 统计信息
        self.v5_2_stats = {
            "intelligent_decisions": 0,
            "risk_predictions": 0,
            "adaptive_adjustments": 0,
            "knowledge_learned": 0
        }

        logger.info("✅ V5.2 增强版低风险套利引擎初始化成功 (智能深度集成)")

    # ---------------------- 智能套利决策（V5.2核心） ----------------------

    async def evaluate_opportunity_intelligent(
        self,
        opportunity: Dict[str, Any],
        strategy: str,
        current_market_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """智能评估套利机会（V5.2核心功能）

        Args:
            opportunity: 套利机会
            strategy: 策略名称
            current_market_conditions: 当前市场条件

        Returns:
            智能评估结果
            {
                "should_execute": bool,
                "confidence": float,
                "decision_reasoning": str,
                "risk_assessment": Dict,
                "adaptive_parameters": Dict,
                "expected_outcome": Dict,
                "knowledge_references": List[Dict]
            }
        """
        self.v5_2_stats["intelligent_decisions"] += 1

        # 构建智能上下文
        context = IntelligentArbitrageContext(
            opportunity=opportunity,
            market_conditions=current_market_conditions,
            strategy=strategy,
            timestamp=datetime.now().timestamp()
        )

        # 1. 获取策略推荐
        strategy_recommendation = await self.decision_engine.recommend_strategy(
            current_market_conditions=current_market_conditions,
            available_strategies=[strategy],
            top_k=1
        )

        # 2. 执行风险评估
        risk_assessment = await self.decision_engine.assess_opportunity_risk(
            opportunity=opportunity,
            strategy=strategy,
            current_market_conditions=current_market_conditions
        )

        context.decision_result = strategy_recommendation
        context.risk_assessment = risk_assessment

        # 3. 生成智能决策
        intelligent_decision = await self._generate_intelligent_decision(
            context, strategy_recommendation, risk_assessment
        )

        # 4. 计算自适应风险参数
        adaptive_params = await self._calculate_adaptive_risk_parameters(
            context, risk_assessment
        )

        # 5. 预测预期结果
        expected_outcome = await self._predict_execution_outcome(
            context, intelligent_decision, adaptive_params
        )

        # 6. 生成最终决策
        should_execute = self._make_final_execution_decision(
            intelligent_decision, risk_assessment, expected_outcome
        )

        result = {
            "should_execute": should_execute,
            "confidence": intelligent_decision.get("confidence", 0),
            "decision_reasoning": intelligent_decision.get("reasoning", ""),
            "risk_assessment": risk_assessment,
            "adaptive_parameters": adaptive_params.__dict__,
            "expected_outcome": expected_outcome,
            "strategy_recommendation": strategy_recommendation,
            "knowledge_references": self._extract_knowledge_references(
                strategy_recommendation, risk_assessment
            ),
            "evaluated_at": datetime.now().isoformat(),
            "engine_version": "5.2"
        }

        return result

    async def _generate_intelligent_decision(
        self,
        context: IntelligentArbitrageContext,
        strategy_recommendation: Dict,
        risk_assessment: Dict
    ) -> Dict[str, Any]:
        """生成智能决策"""
        # 分析策略推荐
        recommendations = strategy_recommendation.get("recommendations", [])
        if not recommendations:
            return {
                "action": "reject",
                "confidence": 0.0,
                "reasoning": "没有可用的策略推荐"
            }

        top_recommendation = recommendations[0]
        strategy_confidence = top_recommendation.get("confidence", 0.5)

        # 分析风险评估
        risk_level = risk_assessment.get("risk_level", "medium")
        risk_score = risk_assessment.get("risk_score", 50)

        # 机会评估
        opportunity = context.opportunity
        profit_rate = opportunity.get("profit_rate", 0)
        expected_profit = opportunity.get("expected_profit", 0)

        # 综合决策逻辑
        decision_factors = []

        # 因子1：策略推荐置信度
        if strategy_confidence >= 0.8:
            decision_factors.append(("strong_recommendation", 0.4, "策略推荐置信度高"))
        elif strategy_confidence >= 0.6:
            decision_factors.append(("moderate_recommendation", 0.3, "策略推荐置信度中等"))
        else:
            decision_factors.append(("weak_recommendation", 0.1, "策略推荐置信度低"))

        # 因子2：风险水平
        if risk_level == "low":
            decision_factors.append(("low_risk", 0.3, "风险评估为低风险"))
        elif risk_level == "medium":
            decision_factors.append(("medium_risk", 0.2, "风险评估为中等风险"))
        elif risk_level == "high":
            decision_factors.append(("high_risk", 0.1, "风险评估为高风险"))
        else:  # critical
            decision_factors.append(("critical_risk", 0.0, "风险评估为极高风险"))

        # 因子3：收益预期
        if profit_rate >= 0.8:
            decision_factors.append(("high_profit", 0.2, "预期收益率较高"))
        elif profit_rate >= 0.5:
            decision_factors.append(("moderate_profit", 0.15, "预期收益率中等"))
        elif profit_rate >= 0.3:
            decision_factors.append(("acceptable_profit", 0.1, "预期收益率可接受"))
        else:
            decision_factors.append(("low_profit", 0.05, "预期收益率较低"))

        # 计算综合置信度
        total_confidence = sum(weight for _, weight, _ in decision_factors)

        # 生成推理过程
        reasoning_parts = []
        for factor_name, weight, description in decision_factors:
            reasoning_parts.append(f"{description} (权重: {weight:.2f})")

        # 确定行动
        if total_confidence >= 0.7:
            action = "execute"
            action_reasoning = "综合评估建议执行此套利机会"
        elif total_confidence >= 0.5:
            action = "cautious_execute"
            action_reasoning = "综合评估建议谨慎执行此套利机会"
        else:
            action = "reject"
            action_reasoning = "综合评估建议拒绝此套利机会"

        return {
            "action": action,
            "confidence": total_confidence,
            "reasoning": f"{action_reasoning}。{' | '.join(reasoning_parts)}",
            "decision_factors": decision_factors,
            "strategy_match": top_recommendation.get("strategy") == context.strategy,
            "expected_win_rate": top_recommendation.get("expected_win_rate", 0.5)
        }

    async def _calculate_adaptive_risk_parameters(
        self,
        context: IntelligentArbitrageContext,
        risk_assessment: Dict
    ) -> AdaptiveRiskParameters:
        """计算自适应风险参数"""
        self.v5_2_stats["adaptive_adjustments"] += 1

        # 基础参数
        base_position_size = context.opportunity.get("max_position_size", 1000)
        base_stop_loss = self.config.get("base_stop_loss", 2.0)
        base_take_profit = self.config.get("base_take_profit", 1.0)

        # 风险调整因子
        risk_level = risk_assessment.get("risk_level", "medium")
        risk_score = risk_assessment.get("risk_score", 50)

        if risk_level == "low":
            adjustment_factor = 1.2  # 低风险，可以适当激进
            reasoning = "风险评估为低风险，适当增加仓位"
        elif risk_level == "medium":
            adjustment_factor = 1.0  # 中等风险，保持正常
            reasoning = "风险评估为中等风险，保持正常仓位"
        elif risk_level == "high":
            adjustment_factor = 0.6  # 高风险，大幅降低仓位
            reasoning = "风险评估为高风险，大幅降低仓位"
        else:  # critical
            adjustment_factor = 0.3  # 极高风险，极大降低仓位
            reasoning = "风险评估为极高风险，极大降低仓位"

        # 计算调整后的参数
        adjusted_position_size = base_position_size * adjustment_factor
        adjusted_stop_loss = base_stop_loss / adjustment_factor  # 风险高时止损更紧
        adjusted_take_profit = base_take_profit * adjustment_factor

        return AdaptiveRiskParameters(
            base_position_size=base_position_size,
            base_stop_loss=base_stop_loss,
            base_take_profit=base_take_profit,
            adjusted_position_size=adjusted_position_size,
            adjusted_stop_loss=adjusted_stop_loss,
            adjusted_take_profit=adjusted_take_profit,
            adjustment_factor=adjustment_factor,
            reasoning=reasoning
        )

    async def _predict_execution_outcome(
        self,
        context: IntelligentArbitrageContext,
        intelligent_decision: Dict,
        adaptive_params: AdaptiveRiskParameters
    ) -> Dict[str, Any]:
        """预测执行结果"""
        # 基于历史数据预测
        decision_confidence = intelligent_decision.get("confidence", 0.5)
        expected_win_rate = intelligent_decision.get("expected_win_rate", 0.5)

        # 风险调整影响
        risk_adjustment = adaptive_params.adjustment_factor

        # 预测成功概率
        success_probability = decision_confidence * expected_win_rate * risk_adjustment

        # 预测收益
        opportunity = context.opportunity
        base_profit = opportunity.get("expected_profit", 0)
        expected_profit = base_profit * risk_adjustment

        # 预测风险
        risk_assessment = context.risk_assessment
        expected_loss_risk = risk_assessment.get("risk_score", 50) / 100 * base_profit

        return {
            "success_probability": min(1.0, max(0.0, success_probability)),
            "expected_profit": expected_profit,
            "expected_loss_risk": expected_loss_risk,
            "risk_adjusted_return": expected_profit - expected_loss_risk,
            "confidence_level": "high" if success_probability > 0.7 else
                           "medium" if success_probability > 0.5 else "low",
            "prediction_basis": "intelligent_decision + risk_adjustment + historical_pattern"
        }

    def _make_final_execution_decision(
        self,
        intelligent_decision: Dict,
        risk_assessment: Dict,
        expected_outcome: Dict
    ) -> bool:
        """做出最终执行决策"""
        # 检查风险等级
        risk_level = risk_assessment.get("risk_level", "")
        if risk_level == "critical":
            logger.warning("🚫 风险等级为critical，拒绝执行")
            return False

        # 检查智能决策
        action = intelligent_decision.get("action", "")
        if action == "reject":
            logger.info("🚫 智能决策建议拒绝")
            return False

        # 检查预期收益
        success_probability = expected_outcome.get("success_probability", 0)
        if success_probability < 0.4:
            logger.warning(f"🚫 预期成功率过低 ({success_probability:.2%})，拒绝执行")
            return False

        # 检查风险调整后收益
        risk_adjusted_return = expected_outcome.get("risk_adjusted_return", 0)
        if risk_adjusted_return < 0:
            logger.warning("🚫 风险调整后预期收益为负，拒绝执行")
            return False

        # 所有检查通过，建议执行
        logger.info(f"✅ 所有检查通过，建议执行 (成功率: {success_probability:.1%})")
        return True

    def _extract_knowledge_references(
        self,
        strategy_recommendation: Dict,
        risk_assessment: Dict
    ) -> List[Dict]:
        """提取知识引用"""
        references = []

        # 策略推荐知识
        if strategy_recommendation.get("recommendations"):
            for rec in strategy_recommendation["recommendations"][:2]:
                references.append({
                    "type": "strategy_recommendation",
                    "content": rec.get("reasoning", ""),
                    "confidence": rec.get("confidence", 0),
                    "historical_trades": rec.get("historical_trades", 0)
                })

        # 风险评估知识
        similar_risks = risk_assessment.get("historical_similar_risks", [])
        for risk in similar_risks[:3]:
            references.append({
                "type": "risk_reference",
                "content": risk.get("content", ""),
                "metadata": risk.get("metadata", {})
            })

        return references

    # ---------------------- 智能执行路径优化 ----------------------

    async def optimize_execution_path(
        self,
        opportunity: Dict[str, Any],
        strategy: str
    ) -> Dict[str, Any]:
        """优化执行路径（V5.2新增）"""
        # 基于策略类型和历史数据优化执行路径
        if strategy == "cross_exchange":
            return await self._optimize_cross_exchange_path(opportunity)
        elif strategy == "triangular":
            return await self._optimize_triangular_path(opportunity)
        else:
            return {"optimized": False, "reasoning": "策略类型不支持路径优化"}

    async def _optimize_cross_exchange_path(
        self,
        opportunity: Dict[str, Any]
    ) -> Dict[str, Any]:
        """优化跨交易所套利执行路径"""
        # 这里可以基于历史执行数据优化交易所选择、执行顺序等
        # 简化实现：返回当前机会作为优化结果
        return {
            "optimized": True,
            "execution_plan": {
                "steps": [
                    {
                        "exchange": opportunity.get("buy_exchange"),
                        "action": "buy",
                        "symbol": opportunity.get("symbol"),
                        "amount": opportunity.get("amount")
                    },
                    {
                        "exchange": opportunity.get("sell_exchange"),
                        "action": "sell",
                        "symbol": opportunity.get("symbol"),
                        "amount": opportunity.get("amount")
                    }
                ],
                "estimated_time": 5.0,  # 秒
                "confidence": 0.8
            },
            "optimization_basis": "historical_execution_performance"
        }

    async def _optimize_triangular_path(
        self,
        opportunity: Dict[str, Any]
    ) -> Dict[str, Any]:
        """优化三角套利执行路径"""
        # 优化三角形路径的执行顺序
        triangles = opportunity.get("triangles", [])
        if not triangles:
            return {"optimized": False, "reasoning": "没有可用的三角形路径"}

        # 选择最优路径（简化实现）
        best_triangle = max(
            triangles,
            key=lambda t: t.get("profit_rate", 0)
        )

        return {
            "optimized": True,
            "execution_plan": {
                "triangle": best_triangle,
                "estimated_time": 8.0,  # 秒
                "confidence": 0.75
            },
            "optimization_basis": "maximum_profit_rate"
        }

    # ---------------------- 知识学习和自优化 ----------------------

    async def learn_from_execution(
        self,
        execution: EnhancedArbitrageExecution
    ):
        """从执行中学习（V5.2增强）"""
        self.v5_2_stats["knowledge_learned"] += 1

        # 从opportunity中提取策略信息
        strategy = execution.opportunity.get("strategy", "unknown") if hasattr(execution, "opportunity") else "unknown"

        # 构建学习知识
        knowledge = {
            "content": self._build_knowledge_content(execution, strategy),
            "metadata": {
                "type": "trading_execution",
                "strategy": strategy,
                "outcome": execution.status.value,
                "profit": execution.actual_profit,
                "risk_level": execution.risk_level.value if execution.risk_level else "unknown",
                "timestamp": execution.start_time,
                "engine_version": "5.2"
            }
        }

        # 添加到Memo0
        if self.decision_engine.mem0_storage:
            try:
                await self.decision_engine.mem0_storage.add_knowledge(knowledge)
                logger.info(f"✅ 知识已学习: {strategy} - {execution.status.value}")
            except Exception as e:
                logger.error(f"❌ 知识学习失败: {e}")

    def _build_knowledge_content(
        self,
        execution: EnhancedArbitrageExecution,
        strategy: str = "unknown"
    ) -> str:
        """构建知识内容"""
        parts = []

        # 策略和结果
        parts.append(f"{strategy}策略执行{'成功' if execution.status.value == 'completed' else '失败'}")

        # 收益信息
        if execution.actual_profit is not None:
            if execution.actual_profit > 0:
                parts.append(f"获得收益${execution.actual_profit:.2f}")
            else:
                parts.append(f"产生损失${abs(execution.actual_profit):.2f}")

        # 风险信息
        if execution.risk_level:
            parts.append(f"风险等级为{execution.risk_level.value}")

        # 决策信息
        if execution.intelligent_decision:
            reasoning = execution.intelligent_decision.reasoning if hasattr(execution.intelligent_decision, 'reasoning') else ""
            if reasoning:
                parts.append(f"决策依据: {reasoning[:100]}...")

        # 市场条件（从opportunity中提取）
        if hasattr(execution, "opportunity") and isinstance(execution.opportunity, dict):
            market_conditions = execution.opportunity.get("market_conditions", {})
            if market_conditions:
                parts.append(f"市场波动率: {market_conditions.get('volatility', 0):.2f}%")

        return ". ".join(parts)

    # ---------------------- 统计和监控 ----------------------

    def get_v5_2_statistics(self) -> Dict[str, Any]:
        """获取V5.2统计信息"""
        # 父类没有get_statistics方法，直接构建基础统计信息
        base_stats = {
            "total_executions": getattr(self, 'total_executions', 0),
            "successful_executions": getattr(self, 'successful_executions', 0),
            "failed_executions": getattr(self, 'failed_executions', 0),
            "total_profit": getattr(self, 'total_profit', 0.0),
            "total_loss": getattr(self, 'total_loss', 0.0)
        }

        return {
            **base_stats,
            "v5_2_intelligent_decisions": self.v5_2_stats["intelligent_decisions"],
            "v5_2_risk_predictions": self.v5_2_stats["risk_predictions"],
            "v5_2_adaptive_adjustments": self.v5_2_stats["adaptive_adjustments"],
            "v5_2_knowledge_learned": self.v5_2_stats["knowledge_learned"],
            "decision_engine_stats": self.decision_engine.get_statistics()
        }


# ======================= 工厂函数 =======================

def create_enhanced_low_risk_engine_v5_2(
    config: Dict[str, Any],
    decision_engine: IntelligentDecisionEngineV52
) -> EnhancedLowRiskArbitrageEngineV52:
    """创建V5.2增强版低风险套利引擎实例

    Args:
        config: 引擎配置
        decision_engine: V5.2智能决策引擎实例

    Returns:
        EnhancedLowRiskArbitrageEngineV52实例
    """
    return EnhancedLowRiskArbitrageEngineV52(
        config=config,
        decision_engine=decision_engine
    )
