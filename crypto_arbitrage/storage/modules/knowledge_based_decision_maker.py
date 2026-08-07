"""基于知识的决策制定器 - V5.10 Phase 2.1

基于memo0知识库实现智能交易决策，支持知识检索、匹配、融合和决策生成。

核心功能：
1. 知识检索和匹配
2. 决策生成和推理
3. 多源知识融合
4. 决策历史管理

基于：V5.10架构设计
创建时间：2026-04-19
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)


class DecisionType(Enum):
    """决策类型"""
    TRADE = "trade"  # 交易决策
    HOLD = "hold"  # 持有决策
    WAIT = "wait"  # 等待决策
    EXIT = "exit"  # 退出决策
    ADJUST = "adjust"  # 调整决策


class KnowledgeRelevance(Enum):
    """知识相关性等级"""
    HIGHLY_RELEVANT = "highly_relevant"  # 高度相关
    MODERATELY_RELEVANT = "moderately_relevant"  # 中等相关
    SLIGHTLY_RELEVANT = "slightly_relevant"  # 轻微相关
    NOT_RELEVANT = "not_relevant"  # 不相关


@dataclass
class DecisionContext:
    """决策上下文"""
    market_data: Dict[str, Any]
    trading_parameters: Dict[str, Any]
    risk_profile: Dict[str, Any]
    time_constraints: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "market_data": self.market_data,
            "trading_parameters": self.trading_parameters,
            "risk_profile": self.risk_profile,
            "time_constraints": self.time_constraints,
            "metadata": self.metadata
        }


@dataclass
class KnowledgeMatch:
    """知识匹配结果"""
    knowledge_id: str
    content: str
    relevance_score: float  # 0-1
    relevance_level: KnowledgeRelevance
    quality_score: float
    value_score: float
    confidence: float
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "knowledge_id": self.knowledge_id,
            "content": self.content,
            "relevance_score": self.relevance_score,
            "relevance_level": self.relevance_level.value,
            "quality_score": self.quality_score,
            "value_score": self.value_score,
            "confidence": self.confidence,
            "metadata": self.metadata
        }


@dataclass
class DecisionRationale:
    """决策理由"""
    primary_reason: str
    supporting_reasons: List[str]
    knowledge_sources: List[str]
    confidence_factors: Dict[str, float]
    reasoning_chain: List[str]
    limitations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "primary_reason": self.primary_reason,
            "supporting_reasons": self.supporting_reasons,
            "knowledge_sources": self.knowledge_sources,
            "confidence_factors": self.confidence_factors,
            "reasoning_chain": self.reasoning_chain,
            "limitations": self.limitations
        }


@dataclass
class Decision:
    """决策结果"""
    decision_id: str
    decision_type: DecisionType
    action: str
    parameters: Dict[str, Any]
    rationale: DecisionRationale
    confidence: float
    knowledge_matches: List[KnowledgeMatch]
    context: DecisionContext
    created_at: datetime
    estimated_outcome: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "decision_id": self.decision_id,
            "decision_type": self.decision_type.value,
            "action": self.action,
            "parameters": self.parameters,
            "rationale": self.rationale.to_dict(),
            "confidence": self.confidence,
            "knowledge_matches": [km.to_dict() for km in self.knowledge_matches],
            "context": self.context.to_dict(),
            "created_at": self.created_at.isoformat(),
            "estimated_outcome": self.estimated_outcome
        }


@dataclass
class DecisionRecord:
    """决策记录"""
    decision: Decision
    execution_result: Optional[Dict[str, Any]] = None
    outcome: Optional[str] = None
    effectiveness_score: Optional[float] = None
    lessons_learned: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "decision": self.decision.to_dict(),
            "execution_result": self.execution_result,
            "outcome": self.outcome,
            "effectiveness_score": self.effectiveness_score,
            "lessons_learned": self.lessons_learned,
            "created_at": self.created_at.isoformat()
        }


class KnowledgeBasedDecisionMaker:
    """基于知识的决策制定器

    基于memo0知识库实现智能交易决策。
    """

    # 决策参数
    MIN_RELEVANCE_THRESHOLD = 0.5
    MAX_KNOWLEDGE_MATCHES = 10
    CONFIDENCE_THRESHOLD = 0.6

    # 知识权重
    KNOWLEDGE_WEIGHTS = {
        "quality": 0.4,
        "value": 0.3,
        "relevance": 0.2,
        "freshness": 0.1
    }

    def __init__(self, config: Dict[str, Any]):
        """初始化决策制定器

        Args:
            config: 配置字典
        """
        self.config = config

        # 决策参数
        self.min_relevance = config.get('min_relevance', self.MIN_RELEVANCE_THRESHOLD)
        self.max_matches = config.get('max_matches', self.MAX_KNOWLEDGE_MATCHES)
        self.confidence_threshold = config.get('confidence_threshold', self.CONFIDENCE_THRESHOLD)

        # 知识库引用（外部注入）
        self.knowledge_base: Dict[str, Dict[str, Any]] = {}

        # 决策历史
        self.decision_history: List[DecisionRecord] = []
        self._decision_id_counter = 0

        # 统计信息
        self.decision_stats = {
            "total_decisions": 0,
            "decisions_by_type": defaultdict(int),
            "average_confidence": 0.0,
            "high_confidence_count": 0,
            "low_confidence_count": 0
        }

        logger.info("[OK] 基于知识的决策制定器初始化完成")

    # ========== 知识检索和匹配 ==========

    async def retrieve_relevant_knowledge(
        self,
        context: DecisionContext,
        limit: Optional[int] = None
    ) -> List[KnowledgeMatch]:
        """检索相关知识

        Args:
            context: 决策上下文
            limit: 返回数量限制

        Returns:
            相关知识匹配列表
        """
        limit = limit or self.max_matches
        matches = []

        # 提取上下文关键词
        keywords = self._extract_context_keywords(context)

        # 检索知识
        for knowledge_id, knowledge in self.knowledge_base.items():
            # 计算相关性
            relevance_score = await self._calculate_relevance(
                knowledge, context, keywords
            )

            if relevance_score >= self.min_relevance:
                # 创建知识匹配
                match = KnowledgeMatch(
                    knowledge_id=knowledge_id,
                    content=knowledge.get('content', ''),
                    relevance_score=relevance_score,
                    relevance_level=self._determine_relevance_level(relevance_score),
                    quality_score=knowledge.get('quality_score', 0.5),
                    value_score=knowledge.get('value_score', 0.5),
                    confidence=knowledge.get('confidence', 0.5),
                    metadata=knowledge.get('metadata', {})
                )
                matches.append(match)

        # 按相关性排序
        matches.sort(key=lambda x: x.relevance_score, reverse=True)

        return matches[:limit]

    async def match_knowledge_to_context(
        self,
        knowledge: Dict[str, Any],
        context: DecisionContext
    ) -> float:
        """匹配知识与上下文

        Args:
            knowledge: 知识条目
            context: 决策上下文

        Returns:
            匹配分数 (0-1)
        """
        # 提取上下文关键词
        keywords = self._extract_context_keywords(context)

        # 计算匹配分数
        match_score = await self._calculate_relevance(knowledge, context, keywords)

        return match_score

    async def rank_knowledge_by_relevance(
        self,
        knowledge_matches: List[KnowledgeMatch]
    ) -> List[KnowledgeMatch]:
        """按相关性排序知识

        Args:
            knowledge_matches: 知识匹配列表

        Returns:
            排序后的知识列表
        """
        # 计算综合分数
        for match in knowledge_matches:
            match.composite_score = self._calculate_composite_score(match)

        # 按综合分数排序
        knowledge_matches.sort(key=lambda x: x.composite_score, reverse=True)

        return knowledge_matches

    # ========== 决策生成 ==========

    async def make_decision(
        self,
        context: DecisionContext
    ) -> Decision:
        """制定决策

        Args:
            context: 决策上下文

        Returns:
            决策结果
        """
        # 1. 检索相关知识
        knowledge_matches = await self.retrieve_relevant_knowledge(context)

        # 2. 生成决策
        decision_type, action, parameters = await self._generate_decision_logic(
            context, knowledge_matches
        )

        # 3. 生成决策理由
        rationale = await self.generate_decision_rationale(
            context, knowledge_matches, decision_type
        )

        # 4. 计算置信度
        confidence = await self._calculate_decision_confidence(
            knowledge_matches, rationale
        )

        # 5. 创建决策
        decision = Decision(
            decision_id=self._generate_decision_id(),
            decision_type=decision_type,
            action=action,
            parameters=parameters,
            rationale=rationale,
            confidence=confidence,
            knowledge_matches=knowledge_matches,
            context=context,
            created_at=datetime.now()
        )

        # 6. 记录决策
        await self.record_decision(decision)

        return decision

    async def generate_decision_rationale(
        self,
        context: DecisionContext,
        knowledge_matches: List[KnowledgeMatch],
        decision_type: DecisionType
    ) -> DecisionRationale:
        """生成决策理由

        Args:
            context: 决策上下文
            knowledge_matches: 知识匹配列表
            decision_type: 决策类型

        Returns:
            决策理由
        """
        # 主要理由
        primary_reason = await self._generate_primary_reason(
            context, knowledge_matches, decision_type
        )

        # 支持理由
        supporting_reasons = await self._generate_supporting_reasons(
            knowledge_matches
        )

        # 知识来源
        knowledge_sources = [km.knowledge_id for km in knowledge_matches[:5]]

        # 置信度因子
        confidence_factors = {
            "knowledge_quality": statistics.mean([km.quality_score for km in knowledge_matches]) if knowledge_matches else 0.0,
            "knowledge_relevance": statistics.mean([km.relevance_score for km in knowledge_matches]) if knowledge_matches else 0.0,
            "knowledge_coverage": len(knowledge_matches) / self.max_matches,
            "context_clarity": self._assess_context_clarity(context)
        }

        # 推理链
        reasoning_chain = await self._generate_reasoning_chain(
            context, knowledge_matches, decision_type
        )

        # 局限性
        limitations = await self._identify_limitations(
            context, knowledge_matches
        )

        return DecisionRationale(
            primary_reason=primary_reason,
            supporting_reasons=supporting_reasons,
            knowledge_sources=knowledge_sources,
            confidence_factors=confidence_factors,
            reasoning_chain=reasoning_chain,
            limitations=limitations
        )

    async def validate_decision(
        self,
        decision: Decision
    ) -> Tuple[bool, List[str]]:
        """验证决策

        Args:
            decision: 决策结果

        Returns:
            (是否有效, 问题列表)
        """
        issues = []

        # 置信度检查
        if decision.confidence < self.confidence_threshold:
            issues.append(f"决策置信度过低: {decision.confidence:.2f} < {self.confidence_threshold}")

        # 知识覆盖检查
        if len(decision.knowledge_matches) == 0:
            issues.append("没有相关知识支持决策")

        # 上下文完整性检查
        if not decision.context.market_data:
            issues.append("缺少市场数据")

        # 参数有效性检查
        if not decision.parameters:
            issues.append("决策参数为空")

        # 风险检查
        if decision.decision_type == DecisionType.TRADE:
            risk_level = decision.context.risk_profile.get('level', 'medium')
            if risk_level == 'high' and decision.confidence < 0.8:
                issues.append("高风险交易需要更高置信度")

        return len(issues) == 0, issues

    # ========== 多源知识融合 ==========

    async def fuse_knowledge_sources(
        self,
        knowledge_matches: List[KnowledgeMatch]
    ) -> Dict[str, Any]:
        """融合多源知识

        Args:
            knowledge_matches: 知识匹配列表

        Returns:
            融合后的知识
        """
        if not knowledge_matches:
            return {}

        # 按类别分组
        knowledge_by_category = defaultdict(list)
        for match in knowledge_matches:
            category = match.metadata.get('category', 'general')
            knowledge_by_category[category].append(match)

        # 融合每个类别的知识
        fused_knowledge = {}
        for category, matches in knowledge_by_category.items():
            # 加权融合
            category_fusion = await self._fuse_category_knowledge(matches)
            fused_knowledge[category] = category_fusion

        return fused_knowledge

    async def resolve_knowledge_conflicts(
        self,
        knowledge_matches: List[KnowledgeMatch]
    ) -> List[KnowledgeMatch]:
        """解决知识冲突

        Args:
            knowledge_matches: 知识匹配列表

        Returns:
            解决冲突后的知识列表
        """
        if len(knowledge_matches) <= 1:
            return knowledge_matches

        # 检测冲突
        conflicts = await self._detect_knowledge_conflicts(knowledge_matches)

        # 解决冲突
        resolved_matches = []
        for match in knowledge_matches:
            if match.knowledge_id not in conflicts:
                resolved_matches.append(match)
            else:
                # 应用冲突解决策略
                resolved_match = await self._resolve_conflict(match, conflicts[match.knowledge_id])
                if resolved_match:
                    resolved_matches.append(resolved_match)

        return resolved_matches

    async def weight_knowledge_by_quality(
        self,
        knowledge_matches: List[KnowledgeMatch]
    ) -> List[KnowledgeMatch]:
        """按质量加权知识

        Args:
            knowledge_matches: 知识匹配列表

        Returns:
            加权后的知识列表
        """
        # 计算加权分数
        for match in knowledge_matches:
            match.weighted_score = self._calculate_composite_score(match)

        # 按加权分数排序
        knowledge_matches.sort(key=lambda x: x.weighted_score, reverse=True)

        return knowledge_matches

    # ========== 决策历史管理 ==========

    async def record_decision(self, decision: Decision):
        """记录决策

        Args:
            decision: 决策结果
        """
        record = DecisionRecord(decision=decision)
        self.decision_history.append(record)

        # 更新统计
        self.decision_stats["total_decisions"] += 1
        self.decision_stats["decisions_by_type"][decision.decision_type.value] += 1

        # 更新平均置信度
        if self.decision_stats["total_decisions"] > 0:
            total_confidence = sum(
                record.decision.confidence for record in self.decision_history
            )
            self.decision_stats["average_confidence"] = total_confidence / self.decision_stats["total_decisions"]

        # 更新置信度计数
        if decision.confidence >= 0.8:
            self.decision_stats["high_confidence_count"] += 1
        elif decision.confidence < 0.5:
            self.decision_stats["low_confidence_count"] += 1

        logger.info(f"记录决策: {decision.decision_id}, 置信度: {decision.confidence:.2f}")

    async def get_decision_history(
        self,
        limit: int = 100,
        decision_type: Optional[DecisionType] = None
    ) -> List[DecisionRecord]:
        """获取决策历史

        Args:
            limit: 返回数量限制
            decision_type: 决策类型过滤

        Returns:
            决策记录列表
        """
        history = self.decision_history[-limit:] if limit else self.decision_history.copy()

        # 类型过滤
        if decision_type:
            history = [
                record for record in history
                if record.decision.decision_type == decision_type
            ]

        return history

    async def analyze_decision_patterns(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """分析决策模式

        Args:
            days: 分析天数

        Returns:
            决策模式分析结果
        """
        # 获取近期决策
        recent_records = await self.get_decision_history(limit=1000)

        # 按天分组
        decisions_by_day = defaultdict(list)
        for record in recent_records:
            day = record.decision.created_at.date()
            decisions_by_day[day].append(record)

        # 分析模式
        patterns = {
            "decision_frequency": len(recent_records) / max(days, 1),
            "type_distribution": defaultdict(int),
            "confidence_trend": [],
            "success_rate": 0.0
        }

        # 类型分布
        for record in recent_records:
            patterns["type_distribution"][record.decision.decision_type.value] += 1

        # 置信度趋势
        for day in sorted(decisions_by_day.keys())[-days:]:
            day_records = decisions_by_day[day]
            if day_records:
                avg_confidence = statistics.mean(
                    record.decision.confidence for record in day_records
                )
                patterns["confidence_trend"].append({
                    "date": day.isoformat(),
                    "average_confidence": avg_confidence
                })

        # 成功率（有结果记录的决策）
        successful_decisions = [
            record for record in recent_records
            if record.outcome == "success" and record.effectiveness_score and record.effectiveness_score > 0.7
        ]
        total_outcome_decisions = [
            record for record in recent_records
            if record.outcome is not None
        ]

        if total_outcome_decisions:
            patterns["success_rate"] = len(successful_decisions) / len(total_outcome_decisions)

        return patterns

    # ========== 辅助方法 ==========

    def _extract_context_keywords(self, context: DecisionContext) -> List[str]:
        """提取上下文关键词"""
        keywords = []

        # 市场数据关键词
        market_data = context.market_data
        if 'symbol' in market_data:
            keywords.append(market_data['symbol'])
        if 'trend' in market_data:
            keywords.append(market_data['trend'])
        if 'volatility' in market_data:
            keywords.append(f"volatility_{market_data['volatility']}")

        # 交易参数关键词
        trading_params = context.trading_parameters
        if 'strategy' in trading_params:
            keywords.append(trading_params['strategy'])
        if 'timeframe' in trading_params:
            keywords.append(trading_params['timeframe'])

        return keywords

    async def _calculate_relevance(
        self,
        knowledge: Dict[str, Any],
        context: DecisionContext,
        keywords: List[str]
    ) -> float:
        """计算知识相关性"""
        content = knowledge.get('content', '').lower()
        relevance_score = 0.0

        # 关键词匹配
        for keyword in keywords:
            if keyword.lower() in content:
                relevance_score += 0.2

        # 归一化
        relevance_score = min(relevance_score, 1.0)

        return relevance_score

    def _determine_relevance_level(self, score: float) -> KnowledgeRelevance:
        """确定相关性等级"""
        if score >= 0.8:
            return KnowledgeRelevance.HIGHLY_RELEVANT
        elif score >= 0.6:
            return KnowledgeRelevance.MODERATELY_RELEVANT
        elif score >= 0.4:
            return KnowledgeRelevance.SLIGHTLY_RELEVANT
        else:
            return KnowledgeRelevance.NOT_RELEVANT

    def _calculate_composite_score(self, match: KnowledgeMatch) -> float:
        """计算综合分数"""
        composite_score = (
            match.quality_score * self.KNOWLEDGE_WEIGHTS["quality"] +
            match.value_score * self.KNOWLEDGE_WEIGHTS["value"] +
            match.relevance_score * self.KNOWLEDGE_WEIGHTS["relevance"] +
            match.confidence * self.KNOWLEDGE_WEIGHTS["freshness"]
        )
        return composite_score

    async def _generate_decision_logic(
        self,
        context: DecisionContext,
        knowledge_matches: List[KnowledgeMatch]
    ) -> Tuple[DecisionType, str, Dict[str, Any]]:
        """生成决策逻辑"""
        # 简化版本：基于市场趋势和知识匹配
        market_trend = context.market_data.get('trend', 'neutral')

        if market_trend == 'bullish' and len(knowledge_matches) > 3:
            return DecisionType.TRADE, "execute_buy", {
                "symbol": context.market_data.get('symbol'),
                "amount": context.trading_parameters.get('amount', 1.0),
                "strategy": "trend_following"
            }
        elif market_trend == 'bearish':
            return DecisionType.HOLD, "wait_for_recovery", {
                "reason": "bearish_market"
            }
        else:
            return DecisionType.WAIT, "monitor_market", {
                "action": "continue_monitoring"
            }

    async def _generate_primary_reason(
        self,
        context: DecisionContext,
        knowledge_matches: List[KnowledgeMatch],
        decision_type: DecisionType
    ) -> str:
        """生成主要理由"""
        if not knowledge_matches:
            return f"基于市场趋势 {context.market_data.get('trend', 'unknown')} 作出{decision_type.value}决策"

        top_match = knowledge_matches[0]
        return f"基于知识 '{top_match.knowledge_id}' (相关性: {top_match.relevance_score:.2f}) 作出{decision_type.value}决策"

    async def _generate_supporting_reasons(
        self,
        knowledge_matches: List[KnowledgeMatch]
    ) -> List[str]:
        """生成支持理由"""
        reasons = []
        for match in knowledge_matches[:3]:
            reasons.append(
                f"知识 '{match.knowledge_id}' 支持此决策 (质量: {match.quality_score:.2f}, 价值: {match.value_score:.2f})"
            )
        return reasons

    async def _calculate_decision_confidence(
        self,
        knowledge_matches: List[KnowledgeMatch],
        rationale: DecisionRationale
    ) -> float:
        """计算决策置信度"""
        if not knowledge_matches:
            return 0.3

        # 基于知识质量
        knowledge_confidence = statistics.mean([km.confidence for km in knowledge_matches])

        # 基于理由完整性
        rationale_confidence = len(rationale.supporting_reasons) / 3.0

        # 综合置信度
        overall_confidence = (knowledge_confidence + rationale_confidence) / 2

        return min(overall_confidence, 1.0)

    async def _generate_reasoning_chain(
        self,
        context: DecisionContext,
        knowledge_matches: List[KnowledgeMatch],
        decision_type: DecisionType
    ) -> List[str]:
        """生成推理链"""
        chain = []

        # 步骤1: 分析市场
        chain.append(f"分析市场趋势: {context.market_data.get('trend', 'unknown')}")

        # 步骤2: 检索知识
        chain.append(f"检索到 {len(knowledge_matches)} 条相关知识")

        # 步骤3: 评估知识
        if knowledge_matches:
            avg_quality = statistics.mean([km.quality_score for km in knowledge_matches])
            chain.append(f"知识平均质量: {avg_quality:.2f}")

        # 步骤4: 生成决策
        chain.append(f"生成{decision_type.value}决策")

        return chain

    async def _identify_limitations(
        self,
        context: DecisionContext,
        knowledge_matches: List[KnowledgeMatch]
    ) -> List[str]:
        """识别局限性"""
        limitations = []

        if len(knowledge_matches) < 3:
            limitations.append("相关知识数量有限")

        if not context.market_data:
            limitations.append("市场数据不完整")

        if knowledge_matches:
            avg_quality = statistics.mean([km.quality_score for km in knowledge_matches])
            if avg_quality < 0.7:
                limitations.append("知识质量偏低")

        return limitations

    async def _detect_knowledge_conflicts(
        self,
        knowledge_matches: List[KnowledgeMatch]
    ) -> Dict[str, List[KnowledgeMatch]]:
        """检测知识冲突"""
        conflicts = {}

        # 简化版本：检测内容冲突
        for i, match1 in enumerate(knowledge_matches):
            for match2 in knowledge_matches[i+1:]:
                # 检查是否冲突（简化逻辑）
                if "buy" in match1.content.lower() and "sell" in match2.content.lower():
                    if match1.knowledge_id not in conflicts:
                        conflicts[match1.knowledge_id] = []
                    conflicts[match1.knowledge_id].append(match2)

        return conflicts

    async def _resolve_conflict(
        self,
        match: KnowledgeMatch,
        conflicting_matches: List[KnowledgeMatch]
    ) -> Optional[KnowledgeMatch]:
        """解决冲突"""
        # 简化版本：选择质量更高的知识
        all_matches = [match] + conflicting_matches
        best_match = max(all_matches, key=lambda m: m.quality_score)
        return best_match

    async def _fuse_category_knowledge(
        self,
        matches: List[KnowledgeMatch]
    ) -> Dict[str, Any]:
        """融合类别知识"""
        if not matches:
            return {}

        # 加权平均
        weighted_content = []
        total_weight = 0

        for match in matches:
            weight = match.quality_score * match.relevance_score
            weighted_content.append((match.content, weight))
            total_weight += weight

        if total_weight == 0:
            return {"content": matches[0].content if matches else ""}

        # 简化版本：返回最高质量的知识
        best_match = max(matches, key=lambda m: m.quality_score)
        return {
            "content": best_match.content,
            "quality": best_match.quality_score,
            "sources": [m.knowledge_id for m in matches]
        }

    def _assess_context_clarity(self, context: DecisionContext) -> float:
        """评估上下文清晰度"""
        clarity_score = 1.0

        # 检查必要字段
        if not context.market_data:
            clarity_score -= 0.3
        if not context.trading_parameters:
            clarity_score -= 0.3
        if not context.risk_profile:
            clarity_score -= 0.2

        return max(clarity_score, 0.0)

    def _generate_decision_id(self) -> str:
        """生成决策ID"""
        self._decision_id_counter += 1
        return f"decision_{self._decision_id_counter:06d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def get_decision_stats(self) -> Dict[str, Any]:
        """获取决策统计"""
        return {
            **self.decision_stats,
            "decisions_by_type": dict(self.decision_stats["decisions_by_type"])
        }

    def reset_stats(self):
        """重置统计"""
        self.decision_stats = {
            "total_decisions": 0,
            "decisions_by_type": defaultdict(int),
            "average_confidence": 0.0,
            "high_confidence_count": 0,
            "low_confidence_count": 0
        }
        logger.info("决策统计已重置")


def create_knowledge_based_decision_maker(
    config: Dict[str, Any]
) -> KnowledgeBasedDecisionMaker:
    """创建基于知识的决策制定器实例

    Args:
        config: 配置字典

    Returns:
        决策制定器实例
    """
    return KnowledgeBasedDecisionMaker(config)
