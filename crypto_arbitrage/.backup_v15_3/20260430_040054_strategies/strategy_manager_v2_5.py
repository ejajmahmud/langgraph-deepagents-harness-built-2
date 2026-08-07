"""StrategyManager V2.5 深度集成增强

基于V2.3，深度集成Memo0自动知识积累器：
1. 自动记录交易决策
2. 自动学习交易结果
3. 基于历史经验的策略推荐
4. 自动市场模式记忆
5. 策略表现自动跟踪

集成点：
- execute_best_opportunity: 自动记录决策和学习结果
- scan_all_strategies: 基于历史经验的策略评分
- _update_performance: 自动记录策略表现
- market_analysis: 自动记录市场模式
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class StrategyManagerV25Mixin:
    """StrategyManager V2.5 深度集成Mixin

    这个Mixin为StrategyManager添加自动知识积累能力。
    """

    def __init__(self, *args, **kwargs):
        """初始化V2.5增强"""
        super().__init__(*args, **kwargs)

        # V2.5: 自动知识积累器
        self._auto_accumulator = None
        self.enable_auto_learning = kwargs.get('enable_auto_learning', True)  # 默认启用

        if self.enable_auto_learning:
            try:
                from storage.auto_knowledge_accumulator import initialize_auto_accumulator
                from storage.mem0_storage import get_unified_storage

                storage = get_unified_storage()
                self._auto_accumulator = initialize_auto_accumulator(storage)
                logger.info("自动知识积累器已启用 (V2.5)")
            except Exception as e:
                logger.warning(f"自动知识积累器初始化失败: {e}")

    # ---------------------- 决策记录 ----------------------

    def _record_decision(
        self,
        decision_type: str,
        strategy: str,
        opportunity: Dict,
        reasoning: str,
        outcome: Optional[str] = None
    ) -> bool:
        """记录交易决策到Memo0（V2.5新增）

        Args:
            decision_type: 决策类型 (trade_execution, trade_rejection, strategy_selection)
            strategy: 策略名称
            opportunity: 交易机会
            reasoning: 决策理由
            outcome: 决策结果

        Returns:
            是否记录成功
        """
        if not self._auto_accumulator or not self._auto_accumulator.is_enabled():
            return False

        # 提取市场条件
        market_conditions = {
            "volatility": opportunity.get("volatility", 0),
            "trend": self._detect_trend(opportunity),
            "liquidity": "normal",  # 简化实现，实际应该检测
            "funding_rate": opportunity.get("funding_rate", 0),
            "spread": opportunity.get("spread", 0)
        }

        # 提取决策参数
        parameters = {
            "profit_rate": opportunity.get("profit_rate", 0),
            "position_size": opportunity.get("position_size", 0),
            "score": opportunity.get("_score", 0),
            "stop_loss": opportunity.get("_stop_loss"),
            "take_profit": opportunity.get("_take_profit")
        }

        return self._auto_accumulator.record_decision(
            decision_type=decision_type,
            market_conditions=market_conditions,
            strategy=strategy,
            reasoning=reasoning,
            parameters=parameters,
            outcome=outcome
        )

    def _record_trade_result(
        self,
        trade_id: str,
        strategy: str,
        opportunity: Dict,
        result: Dict
    ) -> bool:
        """记录交易结果到Memo0（V2.5新增）

        Args:
            trade_id: 交易ID
            strategy: 策略名称
            opportunity: 交易机会
            result: 交易结果

        Returns:
            是否记录成功
        """
        if not self._auto_accumulator or not self._auto_accumulator.is_enabled():
            return False

        expected_profit = opportunity.get("expected_profit", opportunity.get("profit_rate", 0))
        actual_profit = result.get("actual_profit", 0)
        execution_time = result.get("execution_time", 0)
        error = result.get("error")
        success = result.get("status") == "completed"

        # 生成经验教训
        lessons = None
        if error:
            lessons = f"交易失败原因: {error}"
        elif actual_profit < expected_profit * 0.5:
            lessons = f"实际利润(${actual_profit:.2f})远低于预期(${expected_profit:.2f})"

        return self._auto_accumulator.record_trade_result(
            trade_id=trade_id,
            strategy=strategy,
            expected_profit=expected_profit,
            actual_profit=actual_profit,
            execution_time=execution_time,
            error=error,
            lessons=lessons
        )

    def _record_market_pattern(
        self,
        pattern_type: str,
        conditions: Dict,
        successful_strategies: List[str],
        failed_strategies: List[str],
        confidence: float
    ) -> bool:
        """记录市场模式到Memo0（V2.5新增）

        Args:
            pattern_type: 模式类型
            conditions: 市场条件
            successful_strategies: 成功的策略列表
            failed_strategies: 失败的策略列表
            confidence: 置信度

        Returns:
            是否记录成功
        """
        if not self._auto_accumulator or not self._auto_accumulator.is_enabled():
            return False

        return self._auto_accumulator.record_market_pattern(
            pattern_type=pattern_type,
            conditions=conditions,
            successful_strategies=successful_strategies,
            failed_strategies=failed_strategies,
            confidence=confidence
        )

    def _record_strategy_performance(
        self,
        strategy: str,
        period: str,
        metrics: Dict,
        market_conditions: Dict
    ) -> bool:
        """记录策略表现到Memo0（V2.5新增）

        Args:
            strategy: 策略名称
            period: 统计周期
            metrics: 性能指标
            market_conditions: 市场条件

        Returns:
            是否记录成功
        """
        if not self._auto_accumulator or not self._auto_accumulator.is_enabled():
            return False

        return self._auto_accumulator.record_strategy_performance(
            strategy=strategy,
            period=period,
            metrics=metrics,
            market_conditions=market_conditions
        )

    # ---------------------- 决策增强 ----------------------

    def _enhance_opportunity_scoring(
        self,
        opportunities: List[Dict],
        current_market_conditions: Optional[Dict] = None
    ) -> List[Dict]:
        """基于历史经验增强机会评分（V2.5新增）

        Args:
            opportunities: 机会列表
            current_market_conditions: 当前市场条件

        Returns:
            增强后的机会列表
        """
        if not self._auto_accumulator or not opportunities:
            return opportunities

        # 构建当前市场条件
        if current_market_conditions is None and opportunities:
            # 从第一个机会推断市场条件
            first_opp = opportunities[0]
            current_market_conditions = {
                "volatility": first_opp.get("volatility", 0),
                "trend": self._detect_trend(first_opp),
                "liquidity": "normal",
                "funding_rate": first_opp.get("funding_rate", 0),
                "spread": first_opp.get("spread", 0)
            }

        # 查询相似历史决策
        similar_decisions = self._auto_accumulator.query_similar_decisions(
            market_conditions=current_market_conditions,
            top_k=20
        )

        # 分析策略在相似条件下的表现
        strategy_performance_in_context = {}
        for decision in similar_decisions:
            metadata = decision.get("metadata", {})
            strategy = metadata.get("strategy")
            outcome = metadata.get("outcome", "")

            if strategy not in strategy_performance_in_context:
                strategy_performance_in_context[strategy] = {
                    "total": 0,
                    "success": 0
                }

            strategy_performance_in_context[strategy]["total"] += 1
            if "成功" in outcome or "profit" in outcome.lower():
                strategy_performance_in_context[strategy]["success"] += 1

        # 调整机会评分
        enhanced_opportunities = []
        for opp in opportunities:
            strategy_name = opp.get("_strategy_name")

            # 原始评分
            original_score = opp.get("_score", 50)

            # 调整评分
            adjusted_score = original_score

            if strategy_name in strategy_performance_in_context:
                perf = strategy_performance_in_context[strategy]
                success_rate = perf["success"] / perf["total"] if perf["total"] > 0 else 0.5

                # 基于历史胜率调整评分
                if success_rate > 0.7:
                    adjusted_score *= 1.2  # 提升20%
                elif success_rate > 0.5:
                    adjusted_score *= 1.1  # 提升10%
                elif success_rate < 0.3:
                    adjusted_score *= 0.8  # 降低20%

            opp["_adjusted_score"] = adjusted_score
            opp["_score"] = adjusted_score  # 更新评分为调整后评分
            enhanced_opportunities.append(opp)

        logger.info(f"基于历史经验增强了{len(enhanced_opportunities)}个机会的评分")

        return enhanced_opportunities

    # ---------------------- 辅助方法 ----------------------

    def _detect_trend(self, opportunity: Dict) -> str:
        """检测价格趋势（简化实现）

        Args:
            opportunity: 交易机会

        Returns:
            趋势类型 (rising, falling, stable)
        """
        # 简化实现：基于价差推断趋势
        spread = opportunity.get("spread", 0)

        if spread > 0.5:
            return "rising"
        elif spread < -0.5:
            return "falling"
        else:
            return "stable"

    # ---------------------- 重写方法 ----------------------

    async def execute_best_opportunity(self, opportunities: List[Dict]) -> Optional[Dict]:
        """执行最佳交易机会（V2.5增强）

        重写父类方法，添加自动决策记录和结果学习。
        """
        if not opportunities:
            return None

        best = opportunities[0]
        strategy_name = best.get("_strategy_name")
        strategy = self._strategies.get(strategy_name)

        if not strategy:
            logger.error(f"策略 {strategy_name} 未找到")
            return None

        # V2.5: 记录决策（在执行前）
        trade_id = f"trade_{datetime.now().timestamp()}"

        decision_reasoning = (
            f"最佳机会评分: {best.get('_score', 0):.1f}, "
            f"收益率: {best.get('profit_rate', 0):.2f}%, "
            f"策略: {strategy_name}"
        )

        self._record_decision(
            decision_type="trade_execution",
            strategy=strategy_name,
            opportunity=best,
            reasoning=decision_reasoning,
            outcome="pending"
        )

        # 调用父类方法执行交易
        logger.info(f"V2.5: 执行交易 {trade_id}")

        try:
            # 使用父类的执行逻辑（但捕获结果）
            result = await super().execute_best_opportunity(opportunities)

            if result:
                # V2.5: 记录交易结果
                self._record_trade_result(
                    trade_id=trade_id,
                    strategy=strategy_name,
                    opportunity=best,
                    result=result
                )

                # 更新决策的outcome
                self._record_decision(
                    decision_type="trade_execution",
                    strategy=strategy_name,
                    opportunity=best,
                    reasoning=decision_reasoning,
                    outcome="completed" if result.get("status") == "completed" else "failed"
                )

                logger.info(f"V2.5: 交易 {trade_id} 结果已记录到知识库")

            return result

        except Exception as e:
            logger.error(f"V2.5: 交易执行失败: {e}")

            # 记录失败
            self._record_trade_result(
                trade_id=trade_id,
                strategy=strategy_name,
                opportunity=best,
                result={
                    "status": "failed",
                    "error": str(e),
                    "execution_time": 0
                }
            )

            return None

    async def scan_all_strategies(self, price_data: Optional[List[float]] = None) -> List[Dict[str, Any]]:
        """扫描所有策略的交易机会（V2.5增强）

        重写父类方法，添加基于历史经验的评分增强。
        """
        # 调用父类方法获取基础机会
        opportunities = await super().scan_all_strategies(price_data)

        if not opportunities:
            return opportunities

        # V2.5: 基于历史经验增强评分
        enhanced_opportunities = self._enhance_opportunity_scoring(opportunities)

        # 重新排序
        enhanced_opportunities.sort(key=lambda x: x.get("_score", 0), reverse=True)

        return enhanced_opportunities

    def _update_performance(self, strategy_name: str, result: Dict) -> None:
        """更新策略性能（V2.5增强）

        重写父类方法，添加自动策略表现记录。
        """
        # 调用父类方法
        super()._update_performance(strategy_name, result)

        # V2.5: 定期记录策略表现到知识库
        if not self._auto_accumulator or not self._auto_accumulator.is_enabled():
            return

        perf = self._strategy_performance.get(strategy_name, {})
        total_trades = perf.get("total_trades", 0)

        # 每10次交易记录一次表现
        if total_trades > 0 and total_trades % 10 == 0:
            metrics = {
                "total_trades": total_trades,
                "win_rate": perf.get("win_rate", 0),
                "total_profit": perf.get("total_profit", 0),
                "avg_profit_per_trade": perf.get("total_profit", 0) / total_trades if total_trades > 0 else 0,
                "max_drawdown": 0,  # 简化
                "sharpe_ratio": 0  # 简化
            }

            market_conditions = {
                "volatility": 0,  # 简化
                "trend": "stable",  # 简化
                "liquidity": "normal"
            }

            self._record_strategy_performance(
                strategy=strategy_name,
                period="accumulated",
                metrics=metrics,
                market_conditions=market_conditions
            )

            logger.info(f"V2.5: 策略 {strategy_name} 表现已记录 (总计{total_trades}笔交易)")

    # ---------------------- 知识查询接口 ----------------------

    def get_knowledge_stats(self) -> Dict[str, Any]:
        """获取知识库统计（V2.5新增）

        Returns:
            知识库统计信息
        """
        if not self._auto_accumulator:
            return {"total": 0, "by_category": {}}

        return self._auto_accumulator.get_knowledge_stats()

    def query_similar_decisions(
        self,
        market_conditions: Dict,
        strategy: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict]:
        """查询相似历史决策（V2.5新增）

        Args:
            market_conditions: 市场条件
            strategy: 策略名称（可选）
            top_k: 返回数量

        Returns:
            相似决策列表
        """
        if not self._auto_accumulator:
            return []

        return self._auto_accumulator.query_similar_decisions(
            market_conditions=market_conditions,
            strategy=strategy,
            top_k=top_k
        )

    def get_strategy_performance_history(
        self,
        strategy: str,
        period: Optional[str] = None,
        top_k: int = 10
    ) -> List[Dict]:
        """查询策略历史表现（V2.5新增）

        Args:
            strategy: 策略名称
            period: 统计周期（可选）
            top_k: 返回数量

        Returns:
            表现记录列表
        """
        if not self._auto_accumulator:
            return []

        return self._auto_accumulator.query_strategy_performance(
            strategy=strategy,
            period=period,
            top_k=top_k
        )
