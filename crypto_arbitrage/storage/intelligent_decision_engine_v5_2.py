"""
智能决策引擎 V5.2 - Memo0深度集成版

基于Memo0语义搜索和知识关联，提供AI驱动的交易决策支持。

V5.2核心升级：
1. 深度集成Memo0语义搜索（替代基础SQL查询）
2. 实现知识关联和推理能力
3. 增强风险预测的AI学习能力
4. 优化决策解释和可追溯性
5. 实现智能缓存和性能优化
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DecisionContext:
    """决策上下文"""
    query: str
    market_conditions: Dict[str, Any]
    timestamp: float
    cache_key: str


class IntelligentDecisionEngineV52:
    """智能决策引擎 V5.2 - Memo0深度集成版

    基于Memo0语义搜索的历史经验，提供智能决策支持。
    """

    def __init__(self, mem0_storage, fallback_storage=None):
        """初始化智能决策引擎 V5.2

        Args:
            mem0_storage: Memo0存储实例（必须）
            fallback_storage: 降级存储实例（可选）
        """
        self.mem0_storage = mem0_storage
        self.fallback_storage = fallback_storage

        # 缓存系统
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._cache_ttl = 300  # 缓存5分钟

        # 统计信息
        self._stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "mem0_queries": 0,
            "fallback_queries": 0
        }

        # 检查Memo0可用性
        self._mem0_available = self._check_mem0_available()

        if self._mem0_available:
            logger.info("[OK] V5.2 智能决策引擎初始化成功 (Memo0模式)")
        else:
            logger.warning("[WARNING] V5.2 智能决策引擎运行在降级模式 (SQLite)")
            if fallback_storage:
                logger.info("[OK] 降级存储已配置")

    def _check_mem0_available(self) -> bool:
        """检查Memo0是否可用"""
        if self.mem0_storage is None:
            return False

        try:
            # 尝试简单的搜索操作
            if hasattr(self.mem0_storage, 'search_knowledge'):
                return True
            return False
        except Exception as e:
            logger.warning(f"Memo0可用性检查失败: {e}")
            return False

    def _get_cache_key(self, context: DecisionContext) -> str:
        """生成缓存键"""
        data = f"{context.query}:{json.dumps(context.market_conditions, sort_keys=True)}"
        return hashlib.md5(data.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """从缓存获取数据"""
        if cache_key in self._cache:
            data, timestamp = self._cache[cache_key]
            if datetime.now().timestamp() - timestamp < self._cache_ttl:
                self._stats["cache_hits"] += 1
                return data
            else:
                # 缓存过期，删除
                del self._cache[cache_key]
        return None

    def _set_cache(self, cache_key: str, data: Any):
        """设置缓存"""
        self._cache[cache_key] = (data, datetime.now().timestamp())

        # 限制缓存大小
        if len(self._cache) > 1000:
            # 删除最旧的100个条目
            sorted_keys = sorted(
                self._cache.keys(),
                key=lambda k: self._cache[k][1]
            )
            for key in sorted_keys[:100]:
                del self._cache[key]

    # ---------------------- 策略选择建议 (Memo0语义搜索) ----------------------

    async def recommend_strategy(
        self,
        current_market_conditions: Dict[str, Any],
        available_strategies: List[str],
        top_k: int = 3
    ) -> Dict[str, Any]:
        """基于Memo0语义搜索推荐策略

        Args:
            current_market_conditions: 当前市场条件
            available_strategies: 可用策略列表
            top_k: 返回Top-K推荐

        Returns:
            推荐结果
        """
        self._stats["total_queries"] += 1

        # 构建决策上下文
        context = DecisionContext(
            query=self._build_strategy_query(current_market_conditions),
            market_conditions=current_market_conditions,
            timestamp=datetime.now().timestamp(),
            cache_key=self._get_cache_key(DecisionContext(
                query="strategy_recommendation",
                market_conditions=current_market_conditions,
                timestamp=0,
                cache_key=""
            ))
        )

        # 检查缓存
        cached_result = self._get_from_cache(context.cache_key)
        if cached_result:
            logger.debug("策略推荐缓存命中")
            return cached_result

        # 使用Memo0语义搜索
        similar_decisions = await self._search_similar_decisions(context)

        # 分析策略表现
        strategy_performance = self._analyze_strategy_performance(
            similar_decisions,
            available_strategies
        )

        # 生成推荐
        recommendations = self._generate_strategy_recommendations(
            strategy_performance,
            current_market_conditions,
            top_k
        )

        # 市场分析
        market_analysis = self._analyze_market_conditions(current_market_conditions)

        result = {
            "recommendations": recommendations,
            "market_analysis": market_analysis,
            "alternative_strategies": list(set(available_strategies) - {r["strategy"] for r in recommendations}),
            "generated_at": datetime.now().isoformat(),
            "engine_version": "5.2",
            "data_source": "memo0_semantic_search" if self._mem0_available else "fallback_sql"
        }

        # 缓存结果
        self._set_cache(context.cache_key, result)

        return result

    def _build_strategy_query(self, market_conditions: Dict[str, Any]) -> str:
        """构建策略推荐的自然语言查询"""
        conditions = []

        volatility = market_conditions.get("volatility", 0)
        if volatility > 3.0:
            conditions.append("高波动率市场环境")
        elif volatility > 1.5:
            conditions.append("中等波动率市场")
        else:
            conditions.append("低波动率稳定市场")

        trend = market_conditions.get("trend", "stable")
        trend_map = {
            "rising": "价格上升趋势",
            "falling": "价格下降趋势",
            "stable": "价格横盘震荡"
        }
        conditions.append(trend_map.get(trend, "市场趋势不明"))

        liquidity = market_conditions.get("liquidity", "normal")
        liquidity_map = {
            "high": "高流动性",
            "normal": "正常流动性",
            "low": "低流动性"
        }
        conditions.append(liquidity_map.get(liquidity, "流动性一般"))

        funding_rate = market_conditions.get("funding_rate", 0)
        if funding_rate > 0.1:
            conditions.append("正资金费率较高")
        elif funding_rate < -0.1:
            conditions.append("负资金费率")

        spread = market_conditions.get("spread", 0)
        if spread > 0.5:
            conditions.append("价差较大")

        # 构建完整的自然语言查询
        query = f"在{', '.join(conditions)}的情况下，哪种套利策略表现最好？"
        return query

    async def _search_similar_decisions(self, context: DecisionContext) -> List[Dict]:
        """使用Memo0语义搜索相似决策"""
        if self._mem0_available:
            try:
                self._stats["mem0_queries"] += 1

                # 使用Memo0语义搜索
                results = await self.mem0_storage.search_knowledge(
                    context.query,
                    top_k=20,
                    metadata_filter={"type": "trading_decision"}
                )

                logger.info(f"Memo0语义搜索返回 {len(results)} 条结果")
                return results

            except Exception as e:
                logger.error(f"Memo0语义搜索失败: {e}，使用降级存储")
                return await self._fallback_search(context)
        else:
            return await self._fallback_search(context)

    async def _fallback_search(self, context: DecisionContext) -> List[Dict]:
        """降级搜索（使用SQLite）"""
        if self.fallback_storage is None:
            logger.warning("降级存储不可用，返回空结果")
            return []

        try:
            self._stats["fallback_queries"] += 1

            # 使用降级存储的基本查询
            # 这里假设fallback_storage有query_trades方法
            if hasattr(self.fallback_storage, 'query_trades'):
                return self.fallback_storage.query_trades(context.market_conditions)
            elif hasattr(self.fallback_storage, 'query_similar_decisions'):
                return self.fallback_storage.query_similar_decisions(
                    market_conditions=context.market_conditions,
                    top_k=20
                )
            else:
                logger.warning("降级存储不支持查询功能")
                return []

        except Exception as e:
            logger.error(f"降级搜索失败: {e}")
            return []

    def _analyze_strategy_performance(
        self,
        similar_decisions: List[Dict],
        available_strategies: List[str]
    ) -> Dict[str, Dict]:
        """分析策略表现"""
        performance = {s: {
            "trades": [],
            "wins": 0,
            "total_profit": 0,
            "total_loss": 0
        } for s in available_strategies}

        for decision in similar_decisions:
            metadata = decision.get("metadata", {})
            content = decision.get("content", "")
            strategy = metadata.get("strategy")

            # 尝试从内容中提取策略信息
            if not strategy and isinstance(content, str):
                for s in available_strategies:
                    if s in content.lower():
                        strategy = s
                        break

            if strategy in performance:
                performance[strategy]["trades"].append(decision)

                # 记录胜率
                outcome = metadata.get("outcome", "")
                if "成功" in outcome or "profit" in outcome.lower() or "盈利" in outcome:
                    performance[strategy]["wins"] += 1

                # 记录利润和损失
                profit = metadata.get("actual_profit")
                if profit:
                    if profit > 0:
                        performance[strategy]["total_profit"] += profit
                    else:
                        performance[strategy]["total_loss"] += abs(profit)

        # 计算统计指标
        for strategy, data in performance.items():
            trades = data["trades"]
            if trades:
                data["trade_count"] = len(trades)
                data["win_rate"] = data["wins"] / len(trades)
                data["avg_profit"] = data["total_profit"] / len(trades) if len(trades) > 0 else 0
                data["avg_loss"] = data["total_loss"] / len(trades) if len(trades) > 0 else 0
                data["profit_factor"] = (
                    data["total_profit"] / data["total_loss"]
                    if data["total_loss"] > 0 else float('inf')
                )
            else:
                data["trade_count"] = 0
                data["win_rate"] = 0.0
                data["avg_profit"] = 0.0
                data["avg_loss"] = 0.0
                data["profit_factor"] = 0.0

        return performance

    def _generate_strategy_recommendations(
        self,
        performance: Dict[str, Dict],
        market_conditions: Dict[str, Any],
        top_k: int
    ) -> List[Dict]:
        """生成策略推荐（V5.2增强版）"""
        # V5.2 综合评分算法
        scored_strategies = []

        for strategy, data in performance.items():
            if data["trade_count"] > 0:
                # 多维度评分
                scores = {
                    "win_rate": self._normalize_score(data["win_rate"], 0, 1),
                    "profit_factor": self._normalize_score(min(data["profit_factor"], 5), 0, 5),
                    "avg_profit": self._normalize_score(max(data["avg_profit"], 0), 0, 100),
                    "trade_count": self._normalize_score(min(data["trade_count"], 50), 0, 50)
                }

                # 加权综合评分
                weights = {
                    "win_rate": 0.35,      # 胜率权重35%
                    "profit_factor": 0.25,  # 盈亏比权重25%
                    "avg_profit": 0.25,     # 平均利润权重25%
                    "trade_count": 0.15     # 样本数量权重15%
                }

                total_score = sum(scores[k] * weights[k] for k in scores.keys())

                # 生成推荐理由
                reasoning = self._generate_strategy_reasoning_v52(
                    strategy, data, scores, market_conditions
                )

                scored_strategies.append({
                    "strategy": strategy,
                    "confidence": total_score,
                    "expected_win_rate": data["win_rate"],
                    "expected_profit": data["avg_profit"],
                    "profit_factor": data["profit_factor"],
                    "historical_trades": data["trade_count"],
                    "reasoning": reasoning,
                    "detailed_scores": scores
                })

        # 排序并返回Top-K
        scored_strategies.sort(key=lambda x: x["confidence"], reverse=True)
        return scored_strategies[:top_k]

    def _normalize_score(self, value: float, min_val: float, max_val: float) -> float:
        """归一化评分到0-1范围"""
        if max_val == min_val:
            return 0.0
        normalized = (value - min_val) / (max_val - min_val)
        return max(0.0, min(1.0, normalized))

    def _generate_strategy_reasoning_v52(
        self,
        strategy: str,
        data: Dict,
        scores: Dict[str, float],
        market_conditions: Dict
    ) -> str:
        """生成策略推荐理由（V5.2增强版）"""
        reasons = []

        # 基于历史表现（使用多维度评分）
        if scores["win_rate"] >= 0.7:
            reasons.append(f"[OK] {strategy}历史胜率优秀({data['win_rate']:.1%})")
        elif scores["win_rate"] >= 0.5:
            reasons.append(f"✓ {strategy}历史胜率稳定({data['win_rate']:.1%})")
        else:
            reasons.append(f"[WARNING] {strategy}历史胜率较低({data['win_rate']:.1%})，需谨慎")

        if data["profit_factor"] >= 2.0:
            reasons.append(f"[OK] 盈亏比优秀({data['profit_factor']:.1f})")
        elif data["profit_factor"] >= 1.0:
            reasons.append(f"✓ 盈亏比良好({data['profit_factor']:.1f})")

        if scores["avg_profit"] >= 0.7:
            reasons.append(f"[OK] 平均收益较高")

        if scores["trade_count"] >= 0.5:
            reasons.append(f"[OK] 历史样本充足({data['trade_count']}笔)")

        # 基于市场条件
        volatility = market_conditions.get("volatility", 0)
        if volatility > 3.0:
            reasons.append("[STATS] 当前高波动环境，建议降低仓位")
        elif volatility < 1.0:
            reasons.append("[STATS] 当前低波动环境，套利机会可能减少")

        trend = market_conditions.get("trend", "stable")
        if trend == "rising":
            reasons.append("📈 上升趋势，适合趋势跟随策略")
        elif trend == "falling":
            reasons.append("📉 下降趋势，注意止损设置")

        liquidity = market_conditions.get("liquidity", "normal")
        if liquidity == "low":
            reasons.append("💧 流动性不足，建议避免大额交易")

        return " | ".join(reasons)

    def _analyze_market_conditions(self, conditions: Dict) -> Dict:
        """分析市场条件"""
        volatility = conditions.get("volatility", 0)

        # 波动率等级
        if volatility > 3.0:
            volatility_level = "高"
            volatility_advice = "适合高波动策略，需严格风控"
        elif volatility > 1.5:
            volatility_level = "中"
            volatility_advice = "适合均衡策略组合"
        else:
            volatility_level = "低"
            volatility_advice = "适合稳健策略，关注小利润机会"

        # 趋势强度
        trend = conditions.get("trend", "stable")
        spread = conditions.get("spread", 0)
        if spread > 0.5:
            trend_strength = "强"
            trend_advice = "趋势明显，可适当加大仓位"
        elif spread > 0.2:
            trend_strength = "中"
            trend_advice = "趋势温和，保持正常仓位"
        else:
            trend_strength = "弱"
            trend_advice = "趋势不明显，宜谨慎操作"

        # 流动性状态
        liquidity = conditions.get("liquidity", "normal")
        liquidity_map = {
            "high": ("充足", "可正常执行所有策略"),
            "normal": ("正常", "建议关注主要交易对"),
            "low": ("不足", "优先选择高流动性交易对")
        }
        liquidity_status, liquidity_advice = liquidity_map.get(liquidity, ("一般", "保持谨慎"))

        return {
            "volatility_level": volatility_level,
            "volatility_advice": volatility_advice,
            "trend_strength": trend_strength,
            "trend_advice": trend_advice,
            "liquidity_status": liquidity_status,
            "liquidity_advice": liquidity_advice
        }

    # ---------------------- 风险评估 (Memo0增强) ----------------------

    async def assess_opportunity_risk(
        self,
        opportunity: Dict[str, Any],
        strategy: str,
        current_market_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """评估交易机会风险（V5.2 Memo0增强版）"""
        # 构建风险评估查询
        risk_query = self._build_risk_query(opportunity, strategy, current_market_conditions)

        # 使用Memo0搜索历史风险事件
        historical_risks = await self._search_historical_risks(risk_query)

        # 执行多维度风险评估
        risk_assessment = await self._comprehensive_risk_assessment(
            opportunity, strategy, current_market_conditions, historical_risks
        )

        return risk_assessment

    def _build_risk_query(
        self,
        opportunity: Dict[str, Any],
        strategy: str,
        market_conditions: Dict[str, Any]
    ) -> str:
        """构建风险评估的自然语言查询"""
        parts = []

        # 策略信息
        parts.append(f"{strategy}策略")

        # 交易对信息
        symbol = opportunity.get("symbol", "")
        if symbol:
            parts.append(f"{symbol}交易对")

        # 预期收益
        profit_rate = opportunity.get("profit_rate", 0)
        if profit_rate > 1.0:
            parts.append("高收益机会")
        elif profit_rate > 0.5:
            parts.append("中等收益机会")

        # 市场条件
        volatility = market_conditions.get("volatility", 0)
        if volatility > 3.0:
            parts.append("高波动环境")

        # 构建查询
        query = f"{' '.join(parts)}的历史风险事件和失败案例"
        return query

    async def _search_historical_risks(self, query: str) -> List[Dict]:
        """搜索历史风险事件"""
        if self._mem0_available:
            try:
                results = await self.mem0_storage.search_knowledge(
                    query,
                    top_k=15,
                    metadata_filter={"type": "risk_event"}
                )
                logger.info(f"找到 {len(results)} 条历史风险事件")
                return results
            except Exception as e:
                logger.error(f"历史风险搜索失败: {e}")
                return []
        return []

    async def _comprehensive_risk_assessment(
        self,
        opportunity: Dict[str, Any],
        strategy: str,
        market_conditions: Dict[str, Any],
        historical_risks: List[Dict]
    ) -> Dict[str, Any]:
        """综合风险评估"""
        risk_factors = []
        risk_score = 0

        # 1. 波动率风险评估
        volatility = opportunity.get("volatility", market_conditions.get("volatility", 0))
        if volatility > 4.0:
            risk_factors.append({
                "factor": "极端波动",
                "severity": "critical",
                "description": f"波动率{volatility:.2f}%超过安全阈值",
                "score": 35,
                "mitigation": "建议避免交易或大幅降低仓位"
            })
            risk_score += 35
        elif volatility > 2.5:
            risk_factors.append({
                "factor": "高波动",
                "severity": "high",
                "description": f"波动率{volatility:.2f}%较高",
                "score": 20,
                "mitigation": "建议降低仓位，设置严格止损"
            })
            risk_score += 20

        # 2. 历史风险模式分析
        if historical_risks:
            similar_risk_count = len(historical_risks)
            if similar_risk_count >= 5:
                risk_factors.append({
                    "factor": "历史高风险",
                    "severity": "high",
                    "description": f"在相似条件下发现{similar_risk_count}个历史风险事件",
                    "score": 25,
                    "mitigation": "建议避免此机会或采取额外风控措施"
                })
                risk_score += 25
            elif similar_risk_count >= 2:
                risk_factors.append({
                    "factor": "历史中风险",
                    "severity": "medium",
                    "description": f"在相似条件下发现{similar_risk_count}个历史风险事件",
                    "score": 15,
                    "mitigation": "建议加强风险监控"
                })
                risk_score += 15

        # 3. 收益风险评估
        profit_rate = opportunity.get("profit_rate", 0)
        if profit_rate > 2.0:
            risk_factors.append({
                "factor": "过高收益预期",
                "severity": "medium",
                "description": f"预期收益率{profit_rate:.2f}%异常高，可能存在风险",
                "score": 15,
                "mitigation": "建议谨慎验证，检查滑点和流动性"
            })
            risk_score += 15

        # 4. 流动性风险评估
        liquidity = market_conditions.get("liquidity", "normal")
        if liquidity == "low":
            risk_factors.append({
                "factor": "流动性不足",
                "severity": "high",
                "description": "市场流动性较低，可能影响交易执行",
                "score": 20,
                "mitigation": "建议减少交易量，分批执行"
            })
            risk_score += 20

        # 确定风险等级
        if risk_score >= 60:
            risk_level = "critical"
            risk_advice = "🚫 高风险！建议避免此机会"
        elif risk_score >= 40:
            risk_level = "high"
            risk_advice = "[WARNING] 高风险，建议谨慎或大幅降低仓位"
        elif risk_score >= 20:
            risk_level = "medium"
            risk_advice = "[FAST] 中等风险，建议正常风控"
        else:
            risk_level = "low"
            risk_advice = "[OK] 低风险，可以正常执行"

        # 生成建议
        recommendations = [risk_advice]
        for factor in risk_factors:
            if factor.get("mitigation"):
                recommendations.append(factor["mitigation"])

        return {
            "risk_level": risk_level,
            "risk_score": min(100, risk_score),
            "risk_factors": risk_factors,
            "recommendations": list(set(recommendations)),
            "historical_similar_risks": historical_risks,
            "assessed_at": datetime.now().isoformat(),
            "engine_version": "5.2"
        }

    # ---------------------- 统计信息 ----------------------

    def get_statistics(self) -> Dict[str, Any]:
        """获取引擎统计信息"""
        cache_hit_rate = (
            self._stats["cache_hits"] / self._stats["total_queries"] * 100
            if self._stats["total_queries"] > 0 else 0
        )

        return {
            "total_queries": self._stats["total_queries"],
            "cache_hits": self._stats["cache_hits"],
            "cache_hit_rate": f"{cache_hit_rate:.1f}%",
            "mem0_queries": self._stats["mem0_queries"],
            "fallback_queries": self._stats["fallback_queries"],
            "mem0_available": self._mem0_available,
            "cache_size": len(self._cache)
        }

    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
        logger.info("决策引擎缓存已清空")


# ======================= 工厂函数 =======================

def create_intelligent_decision_engine_v5_2(
    mem0_storage,
    fallback_storage=None
) -> IntelligentDecisionEngineV52:
    """创建V5.2智能决策引擎实例

    Args:
        mem0_storage: Memo0存储实例
        fallback_storage: 降级存储实例（可选）

    Returns:
        IntelligentDecisionEngineV52实例
    """
    return IntelligentDecisionEngineV52(
        mem0_storage=mem0_storage,
        fallback_storage=fallback_storage
    )
