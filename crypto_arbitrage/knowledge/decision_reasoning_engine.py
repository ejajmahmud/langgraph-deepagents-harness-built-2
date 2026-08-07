"""决策推理引擎 V1.0 - Phase 6.1核心模块

基于知识图谱实现智能决策推理，支持多跳推理和路径分析。

核心功能：
1. 基于图谱的路径推理
2. 知识关联挖掘
3. 决策支持图构建
4. 多种推理模式（演绎、归纳、类比）

基于：V5.10架构设计
创建时间：2026-04-19 15:05
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict

from knowledge.knowledge_graph_builder import (
    EnhancedKnowledgeGraph,
    GraphPath,
    RelationType,
    NodeCategory
)

logger = logging.getLogger(__name__)


class ReasoningMode(Enum):
    """推理模式"""
    DEDUCTIVE = "deductive"  # 演绎推理
    INDUCTIVE = "inductive"  # 归纳推理
    ABDUCTIVE = "abductive"  # 溯因推理
    ANALOGICAL = "analogical"  # 类比推理
    PATH_BASED = "path_based"  # 基于路径的推理


@dataclass
class ReasoningStep:
    """推理步骤"""
    step_id: str
    reasoning_mode: ReasoningMode
    source_node: str
    target_node: str
    reasoning: str
    evidence: List[str]
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "step_id": self.step_id,
            "reasoning_mode": self.reasoning_mode.value,
            "source_node": self.source_node,
            "target_node": self.target_node,
            "reasoning": self.reasoning,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "metadata": self.metadata
        }


@dataclass
class ReasoningChain:
    """推理链"""
    chain_id: str
    start_node: str
    end_node: str
    steps: List[ReasoningStep]
    conclusion: str
    overall_confidence: float
    reasoning_mode: ReasoningMode
    alternative_paths: List[GraphPath] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "chain_id": self.chain_id,
            "start_node": self.start_node,
            "end_node": self.end_node,
            "steps": [step.to_dict() for step in self.steps],
            "conclusion": self.conclusion,
            "overall_confidence": self.overall_confidence,
            "reasoning_mode": self.reasoning_mode.value,
            "alternative_paths": [p.to_dict() for p in self.alternative_paths],
            "metadata": self.metadata
        }


@dataclass
class DecisionInference:
    """决策推断"""
    inference_id: str
    decision_node: str
    reasoning_chain: ReasoningChain
    supporting_graph_paths: List[GraphPath]
    confidence: float
    reasoning: str
    recommended_actions: List[str]
    risk_factors: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "inference_id": self.inference_id,
            "decision_node": self.decision_node,
            "reasoning_chain": self.reasoning_chain.to_dict(),
            "supporting_graph_paths": [p.to_dict() for p in self.supporting_graph_paths],
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "recommended_actions": self.recommended_actions,
            "risk_factors": self.risk_factors,
            "metadata": self.metadata
        }


class DecisionReasoningEngine:
    """决策推理引擎

    基于知识图谱实现智能决策推理。
    """

    # 推理参数
    MAX_PATH_LENGTH = 5
    MIN_CONFIDENCE_THRESHOLD = 0.6
    MAX_ALTERNATIVE_PATHS = 5

    def __init__(
        self,
        knowledge_graph: EnhancedKnowledgeGraph,
        config: Optional[Dict[str, Any]] = None
    ):
        """初始化推理引擎

        Args:
            knowledge_graph: 知识图谱实例
            config: 配置字典
        """
        self.knowledge_graph = knowledge_graph
        self.config = config or {} if config is not None else {}

        # 推理参数
        self.max_path_length = self.config.get('max_path_length', self.MAX_PATH_LENGTH)
        self.min_confidence = self.config.get('min_confidence', self.MIN_CONFIDENCE_THRESHOLD)
        self.max_alternatives = self.config.get('max_alternatives', self.MAX_ALTERNATIVE_PATHS)

        # 推理历史
        self.inference_history: List[DecisionInference] = []

        # 统计
        self.stats = {
            "total_inferences": 0,
            "inferences_by_mode": defaultdict(int),
            "average_confidence": 0.0,
            "successful_inferences": 0
        }

        logger.info("✅ 决策推理引擎初始化完成")

    # ========== 基于路径的推理 ==========

    async def reason_by_path(
        self,
        start_node_id: str,
        end_node_id: Optional[str] = None,
        reasoning_mode: ReasoningMode = ReasoningMode.PATH_BASED
    ) -> DecisionInference:
        """基于路径的推理

        Args:
            start_node_id: 起始节点ID
            end_node_id: 目标节点ID（可选）
            reasoning_mode: 推理模式

        Returns:
            决策推断对象
        """
        # 查找路径
        if end_node_id:
            path = self.knowledge_graph.find_shortest_path(
                start_node_id,
                end_node_id,
                max_hops=self.max_path_length
            )
        else:
            # 推理所有可能的路径
            paths = self.knowledge_graph.infer_relations(
                start_node_id,
                max_depth=self.max_path_length
            )
            path = paths[0] if paths else None

        if not path:
            logger.warning(f"未找到路径: {start_node_id} -> {end_node_id}")
            return self._create_empty_inference(start_node_id, reasoning_mode)

        # 构建推理链
        reasoning_chain = await self._build_reasoning_chain(
            path, reasoning_mode
        )

        # 查找替代路径
        alternative_paths = self._find_alternative_paths(
            start_node_id, path
        )[:self.max_alternatives]

        # 生成推断
        inference = self._create_inference(
            start_node_id,
            reasoning_chain,
            [path] + alternative_paths,
            reasoning_mode
        )

        # 记录统计
        await self._record_inference(inference)

        return inference

    async def _build_reasoning_chain(
        self,
        path: GraphPath,
        reasoning_mode: ReasoningMode
    ) -> ReasoningChain:
        """构建推理链

        Args:
            path: 图谱路径
            reasoning_mode: 推理模式

        Returns:
            推理链对象
        """
        steps = []
        node_ids = path.node_ids
        edges = path.edges

        # 为每个边创建推理步骤
        for i, edge in enumerate(edges):
            source_node = node_ids[i]
            target_node = node_ids[i + 1]

            step = ReasoningStep(
                step_id=f"step_{i}",
                reasoning_mode=reasoning_mode,
                source_node=source_node,
                target_node=target_node,
                reasoning=self._generate_step_reasoning(edge, i),
                evidence=edge.evidence,
                confidence=edge.confidence,
                metadata={
                    "relation_type": edge.relation_type.value,
                    "weight": edge.weight
                }
            )
            steps.append(step)

        # 生成结论
        conclusion = self._generate_conclusion(path)

        # 计算整体置信度
        overall_confidence = min(step.confidence for step in steps) if steps else 0.0

        return ReasoningChain(
            chain_id=f"chain_{path.path_id}",
            start_node=node_ids[0],
            end_node=node_ids[-1],
            steps=steps,
            conclusion=conclusion,
            overall_confidence=overall_confidence,
            reasoning_mode=reasoning_mode,
            metadata={"path_id": path.path_id}
        )

    def _generate_step_reasoning(
        self,
        edge: 'KnowledgeEdge',
        step_index: int
    ) -> str:
        """生成步骤推理"""
        relation_desc = self._get_relation_description(edge.relation_type)
        return f"步骤{step_index + 1}: 通过{relation_desc}关系，从{edge.source_id}推导至{edge.target_id}，置信度{edge.confidence:.2%}"

    def _generate_conclusion(self, path: GraphPath) -> str:
        """生成结论"""
        node_count = len(path.node_ids)
        relation_types = [edge.relation_type.value for edge in path.edges]

        return f"经过{node_count}个节点的推理路径，通过{', '.join(set(relation_types))}关系，最终得出结论"

    def _get_relation_description(self, relation_type: RelationType) -> str:
        """获取关系描述"""
        descriptions = {
            RelationType.CAUSAL: "因果",
            RelationType.DEPENDENCY: "依赖",
            RelationType.ASSOCIATION: "关联",
            RelationType.TEMPORAL: "时间",
            RelationType.HIERARCHICAL: "层次",
            RelationType.SIMILARITY: "相似",
            RelationType.SEQUENTIAL: "顺序",
            RelationType.CONDITIONAL: "条件"
        }
        return descriptions.get(relation_type, "未知")

    def _find_alternative_paths(
        self,
        start_node_id: str,
        primary_path: GraphPath
    ) -> List[GraphPath]:
        """查找替代路径"""
        # 查找从起始节点的所有推理路径
        all_paths = self.knowledge_graph.infer_relations(
            start_node_id,
            max_depth=self.max_path_length
        )

        # 过滤掉主路径
        alternative_paths = [
            path for path in all_paths
            if path.path_id != primary_path.path_id
        ]

        return alternative_paths

    def _create_inference(
        self,
        start_node_id: str,
        reasoning_chain: ReasoningChain,
        paths: List[GraphPath],
        reasoning_mode: ReasoningMode
    ) -> DecisionInference:
        """创建决策推断"""
        # 生成推理说明
        reasoning = self._generate_inference_reasoning(
            reasoning_chain, paths
        )

        # 生成推荐行动
        recommended_actions = self._generate_recommended_actions(
            reasoning_chain, paths
        )

        # 识别风险因素
        risk_factors = self._identify_risk_factors(paths)

        # 计算置信度
        confidence = reasoning_chain.overall_confidence

        return DecisionInference(
            inference_id=f"inference_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            decision_node=reasoning_chain.end_node,
            reasoning_chain=reasoning_chain,
            supporting_graph_paths=paths,
            confidence=confidence,
            reasoning=reasoning,
            recommended_actions=recommended_actions,
            risk_factors=risk_factors,
            metadata={
                "reasoning_mode": reasoning_mode.value,
                "path_count": len(paths),
                "created_at": datetime.now().isoformat()
            }
        )

    def _generate_inference_reasoning(
        self,
        reasoning_chain: ReasoningChain,
        paths: List[GraphPath]
    ) -> str:
        """生成推断推理"""
        primary_path = paths[0]
        path_length = len(primary_path.node_ids)
        confidence = reasoning_chain.overall_confidence

        reasoning_parts = [
            f"基于知识图谱推理",
            f"发现从{reasoning_chain.start_node}到{reasoning_chain.end_node}的路径",
            f"路径长度: {path_length}个节点",
            f"推理置信度: {confidence:.2%}"
        ]

        if len(paths) > 1:
            reasoning_parts.append(f"发现{len(paths)-1}条替代路径")

        return ". ".join(reasoning_parts) + "."

    def _generate_recommended_actions(
        self,
        reasoning_chain: ReasoningChain,
        paths: List[GraphPath]
    ) -> List[str]:
        """生成推荐行动"""
        actions = []

        # 基于置信度
        confidence = reasoning_chain.overall_confidence
        if confidence >= 0.8:
            actions.append("建议执行此决策")
        elif confidence >= 0.6:
            actions.append("建议谨慎评估后执行")
        else:
            actions.append("建议等待更多信息")

        # 基于路径数量
        if len(paths) > 3:
            actions.append("存在多条推理路径，建议综合评估")

        # 基于关系类型
        for edge in paths[0].edges:
            if edge.relation_type == RelationType.CAUSAL:
                actions.append("因果链条清晰，风险相对较低")
            elif edge.relation_type == RelationType.ASSOCIATION:
                actions.append("基于关联关系，存在不确定性")

        return list(set(actions))

    def _identify_risk_factors(self, paths: List[GraphPath]) -> List[str]:
        """识别风险因素"""
        risks = []

        if not paths:
            return ["未找到推理路径"]

        primary_path = paths[0]

        # 检查路径长度
        if len(primary_path.node_ids) > self.max_path_length:
            risks.append(f"推理路径过长（{len(primary_path.node_ids)}跳），可能降低置信度")

        # 检查边置信度
        low_confidence_edges = [
            edge for edge in primary_path.edges
            if edge.confidence < self.min_confidence
        ]
        if low_confidence_edges:
            risks.append(f"存在{len(low_confidence_edges)}个低置信度边")

        # 检查关系类型
        risky_relations = [
            edge.relation_type for edge in primary_path.edges
            if edge.relation_type == RelationType.ASSOCIATION
        ]
        if risky_relations:
            risks.append("包含关联性关系，推理可靠性较低")

        # 检查替代路径一致性
        if len(paths) > 1:
            endpoints = [p.node_ids[-1] for p in paths]
            if len(set(endpoints)) > 1:
                risks.append("替代路径指向不同结论，需要谨慎评估")

        return risks

    def _create_empty_inference(
        self,
        start_node_id: str,
        reasoning_mode: ReasoningMode
    ) -> DecisionInference:
        """创建空推断"""
        empty_chain = ReasoningChain(
            chain_id="empty_chain",
            start_node=start_node_id,
            end_node="unknown",
            steps=[],
            conclusion="未找到推理路径",
            overall_confidence=0.0,
            reasoning_mode=reasoning_mode
        )

        return DecisionInference(
            inference_id=f"empty_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            decision_node="unknown",
            reasoning_chain=empty_chain,
            supporting_graph_paths=[],
            confidence=0.0,
            reasoning="未找到有效的推理路径",
            recommended_actions=["建议收集更多信息后重试"],
            risk_factors=["缺乏推理依据"],
            metadata={"status": "no_path_found"}
        )

    # ========== 多种推理模式 ==========

    async def reason_deductive(
        self,
        premise_node_id: str,
        rule_relation: RelationType,
        conclusion_category: NodeCategory
    ) -> DecisionInference:
        """演绎推理

        Args:
            premise_node_id: 前提节点ID
            rule_relation: 规则关系类型
            conclusion_category: 结论节点类别

        Returns:
            决策推断对象
        """
        # 查找符合条件的邻居节点
        neighbors = self.knowledge_graph.get_neighbors(
            premise_node_id,
            relation_type=rule_relation
        )

        # 过滤到目标类别
        target_nodes = []
        for neighbor_id in neighbors:
            node = self.knowledge_graph.get_node(neighbor_id)
            if node and node.category == conclusion_category:
                target_nodes.append(neighbor_id)

        if not target_nodes:
            logger.warning(f"演绎推理失败: 未找到{conclusion_category.value}类别的节点")
            return self._create_empty_inference(premise_node_id, ReasoningMode.DEDUCTIVE)

        # 选择置信度最高的节点
        best_node_id = target_nodes[0]  # 简化版本

        # 构建推理链
        steps = [
            ReasoningStep(
                step_id="deductive_step_1",
                reasoning_mode=ReasoningMode.DEDUCTIVE,
                source_node=premise_node_id,
                target_node=best_node_id,
                reasoning=f"从前提{premise_node_id}，通过{rule_relation.value}规则，推导至{best_node_id}",
                evidence=[],
                confidence=0.8
            )
        ]

        reasoning_chain = ReasoningChain(
            chain_id=f"deductive_{premise_node_id}",
            start_node=premise_node_id,
            end_node=best_node_id,
            steps=steps,
            conclusion=f"通过演绎推理，得出结论{best_node_id}",
            overall_confidence=0.8,
            reasoning_mode=ReasoningMode.DEDUCTIVE
        )

        # 创建一个模拟路径用于构建推断
        mock_path_edges = steps[0] if steps else None
        if mock_path_edges:
            from knowledge.knowledge_graph_builder import GraphPath
            mock_path = GraphPath(
                path_id=f"deductive_{premise_node_id}",
                node_ids=[premise_node_id, best_node_id],
                edges=[],
                total_weight=1.0,
                confidence=0.8,
                reasoning="演绎推理路径",
                metadata={}
            )
            return self._create_inference(
                premise_node_id,
                reasoning_chain,
                [mock_path],
                ReasoningMode.DEDUCTIVE
            )
        else:
            return self._create_inference(
                premise_node_id,
                reasoning_chain,
                [],
                ReasoningMode.DEDUCTIVE
            )

    async def reason_inductive(
        self,
        sample_nodes: List[str],
        target_category: NodeCategory
    ) -> DecisionInference:
        """归纳推理

        Args:
            sample_nodes: 样本节点列表
            target_category: 目标类别

        Returns:
            决策推断对象
        """
        # 分析样本节点的共同特征
        common_patterns = self._analyze_common_patterns(sample_nodes)

        # 推导出一般性结论
        conclusion = f"基于{len(sample_nodes)}个样本的共同特征：{common_patterns}"

        steps = []
        for i, node_id in enumerate(sample_nodes):
            steps.append(
                ReasoningStep(
                    step_id=f"inductive_step_{i}",
                    reasoning_mode=ReasoningMode.INDUCTIVE,
                    source_node=node_id,
                    target_node=target_category.value,
                    reasoning=f"观察样本{i+1}: {node_id}",
                    evidence=[],
                    confidence=0.7
                )
            )

        reasoning_chain = ReasoningChain(
            chain_id=f"inductive_{len(sample_nodes)}_samples",
            start_node=sample_nodes[0],
            end_node=target_category.value,
            steps=steps,
            conclusion=conclusion,
            overall_confidence=0.7,
            reasoning_mode=ReasoningMode.INDUCTIVE
        )

        return self._create_inference(
            sample_nodes[0],
            reasoning_chain,
            [],
            ReasoningMode.INDUCTIVE
        )

    def _analyze_common_patterns(self, node_ids: List[str]) -> str:
        """分析共同模式"""
        # 简化版本：返回共同类别
        categories = set()
        for node_id in node_ids:
            node = self.knowledge_graph.get_node(node_id)
            if node:
                categories.add(node.category.value)

        return f"共同类别: {', '.join(categories)}"

    # ========== 推理历史管理 ==========

    async def _record_inference(self, inference: DecisionInference):
        """记录推断"""
        self.inference_history.append(inference)

        # 更新统计
        self.stats["total_inferences"] += 1
        self.stats["inferences_by_mode"][inference.reasoning_chain.reasoning_mode.value] += 1

        # 更新平均置信度
        if self.stats["total_inferences"] > 0:
            total_confidence = sum(
                inf.confidence for inf in self.inference_history
            )
            self.stats["average_confidence"] = total_confidence / self.stats["total_inferences"]

        # 成功推断计数
        if inference.confidence >= self.min_confidence:
            self.stats["successful_inferences"] += 1

    async def get_inference_history(
        self,
        limit: int = 100
    ) -> List[DecisionInference]:
        """获取推断历史

        Args:
            limit: 返回数量限制

        Returns:
            推断历史列表
        """
        return self.inference_history[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "inferences_by_mode": dict(self.stats["inferences_by_mode"]),
            "success_rate": (
                self.stats["successful_inferences"] / max(self.stats["total_inferences"], 1)
            )
        }


def create_decision_reasoning_engine(
    knowledge_graph: EnhancedKnowledgeGraph,
    config: Optional[Dict[str, Any]] = None
) -> DecisionReasoningEngine:
    """创建决策推理引擎实例

    Args:
        knowledge_graph: 知识图谱实例
        config: 配置字典

    Returns:
        决策推理引擎实例
    """
    return DecisionReasoningEngine(knowledge_graph, config)
