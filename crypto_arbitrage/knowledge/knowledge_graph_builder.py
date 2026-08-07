"""增强知识图谱构建器 V1.0 - Phase 6.1核心模块

构建交易决策知识图谱，支持多层次知识关系和智能推理。

核心功能：
1. 超越TF-IDF的丰富关系类型
2. 显式关系建模（因果、依赖、关联）
3. 多层次知识组织（实体→类别→主题）
4. 图谱查询和推理接口

基于：V5.10架构设计
创建时间：2026-04-19 14:58
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


class RelationType(Enum):
    """关系类型"""
    CAUSAL = "causal"  # 因果关系
    DEPENDENCY = "dependency"  # 依赖关系
    ASSOCIATION = "association"  # 关联关系
    TEMPORAL = "temporal"  # 时间关系
    HIERARCHICAL = "hierarchical"  # 层次关系
    SIMILARITY = "similarity"  # 相似关系
    SEQUENTIAL = "sequential"  # 顺序关系
    CONDITIONAL = "conditional"  # 条件关系


class NodeCategory(Enum):
    """节点类别"""
    ENTITY = "entity"  # 实体（货币对、交易所）
    EVENT = "event"  # 事件（交易、异常）
    PATTERN = "pattern"  # 模式（趋势、周期）
    STRATEGY = "strategy"  # 策略
    RISK = "risk"  # 风险
    METRIC = "metric"  # 指标
    KNOWLEDGE = "knowledge"  # 知识条目


@dataclass
class KnowledgeNode:
    """知识图谱节点"""
    node_id: str
    label: str
    category: NodeCategory
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    attributes: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "node_id": self.node_id,
            "label": self.label,
            "category": self.category.value,
            "content": self.content,
            "metadata": self.metadata,
            "attributes": self.attributes,
            "embedding": self.embedding,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class KnowledgeEdge:
    """知识图谱边"""
    edge_id: str
    source_id: str
    target_id: str
    relation_type: RelationType
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    evidence: List[str] = field(default_factory=list)
    confidence: float = 0.8
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "edge_id": self.edge_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation_type": self.relation_type.value,
            "weight": self.weight,
            "metadata": self.metadata,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class GraphPath:
    """图谱路径"""
    path_id: str
    node_ids: List[str]
    edges: List[KnowledgeEdge]
    total_weight: float
    confidence: float
    reasoning: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "path_id": self.path_id,
            "node_ids": self.node_ids,
            "edges": [e.to_dict() for e in self.edges],
            "total_weight": self.total_weight,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "metadata": self.metadata
        }


class EnhancedKnowledgeGraph:
    """增强知识图谱

    支持多层次知识关系和智能推理。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化知识图谱

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 图谱数据
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.edges: Dict[str, KnowledgeEdge] = {}

        # 索引
        self._category_index: Dict[NodeCategory, Set[str]] = defaultdict(set)
        self._relation_index: Dict[RelationType, Set[str]] = defaultdict(set)
        self._attribute_index: Dict[Tuple[str, Any], Set[str]] = defaultdict(set)

        # 统计
        self.stats = {
            "node_count": 0,
            "edge_count": 0,
            "relation_distribution": defaultdict(int),
            "category_distribution": defaultdict(int)
        }

        logger.info("✅ 增强知识图谱初始化完成")

    # ========== 节点管理 ==========

    def add_node(
        self,
        node_id: str,
        label: str,
        category: NodeCategory,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        attributes: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None
    ) -> bool:
        """添加节点

        Args:
            node_id: 节点ID
            label: 节点标签
            category: 节点类别
            content: 节点内容
            metadata: 元数据
            attributes: 属性字典
            embedding: 向量嵌入

        Returns:
            是否成功添加
        """
        if node_id in self.nodes:
            logger.warning(f"节点已存在: {node_id}")
            return False

        node = KnowledgeNode(
            node_id=node_id,
            label=label,
            category=category,
            content=content,
            metadata=metadata or {},
            attributes=attributes or {},
            embedding=embedding
        )

        self.nodes[node_id] = node
        self._category_index[category].add(node_id)

        # 属性索引
        for key, value in (attributes or {}).items():
            self._attribute_index[(key, value)].add(node_id)

        # 更新统计
        self.stats["node_count"] += 1
        self.stats["category_distribution"][category.value] += 1

        logger.debug(f"添加节点: {node_id} ({category.value})")
        return True

    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        """获取节点

        Args:
            node_id: 节点ID

        Returns:
            节点对象，不存在则返回None
        """
        return self.nodes.get(node_id)

    def update_node(
        self,
        node_id: str,
        **kwargs
    ) -> bool:
        """更新节点

        Args:
            node_id: 节点ID
            **kwargs: 更新的字段

        Returns:
            是否成功更新
        """
        node = self.nodes.get(node_id)
        if not node:
            logger.warning(f"节点不存在: {node_id}")
            return False

        for key, value in kwargs.items():
            if hasattr(node, key):
                setattr(node, key, value)

        node.updated_at = datetime.now()
        logger.debug(f"更新节点: {node_id}")
        return True

    def remove_node(self, node_id: str) -> bool:
        """移除节点

        Args:
            node_id: 节点ID

        Returns:
            是否成功移除
        """
        if node_id not in self.nodes:
            logger.warning(f"节点不存在: {node_id}")
            return False

        node = self.nodes[node_id]

        # 移除相关边
        edges_to_remove = [
            edge_id for edge_id, edge in self.edges.items()
            if edge.source_id == node_id or edge.target_id == node_id
        ]
        for edge_id in edges_to_remove:
            self.remove_edge(edge_id)

        # 移除索引
        self._category_index[node.category].discard(node_id)

        # 移除属性索引
        for key, value in node.attributes.items():
            self._attribute_index[(key, value)].discard(node_id)

        # 移除节点
        del self.nodes[node_id]

        # 更新统计
        self.stats["node_count"] -= 1
        self.stats["category_distribution"][node.category.value] -= 1

        logger.debug(f"移除节点: {node_id}")
        return True

    # ========== 边管理 ==========

    def add_edge(
        self,
        edge_id: str,
        source_id: str,
        target_id: str,
        relation_type: RelationType,
        weight: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
        evidence: Optional[List[str]] = None,
        confidence: float = 0.8
    ) -> bool:
        """添加边

        Args:
            edge_id: 边ID
            source_id: 源节点ID
            target_id: 目标节点ID
            relation_type: 关系类型
            weight: 权重
            metadata: 元数据
            evidence: 证据列表
            confidence: 置信度

        Returns:
            是否成功添加
        """
        if edge_id in self.edges:
            logger.warning(f"边已存在: {edge_id}")
            return False

        if source_id not in self.nodes or target_id not in self.nodes:
            logger.warning(f"节点不存在: source={source_id}, target={target_id}")
            return False

        edge = KnowledgeEdge(
            edge_id=edge_id,
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            weight=weight,
            metadata=metadata or {},
            evidence=evidence or [],
            confidence=confidence
        )

        self.edges[edge_id] = edge
        self._relation_index[relation_type].add(edge_id)

        # 更新统计
        self.stats["edge_count"] += 1
        self.stats["relation_distribution"][relation_type.value] += 1

        logger.debug(f"添加边: {edge_id} ({relation_type.value})")
        return True

    def get_edge(self, edge_id: str) -> Optional[KnowledgeEdge]:
        """获取边

        Args:
            edge_id: 边ID

        Returns:
            边对象，不存在则返回None
        """
        return self.edges.get(edge_id)

    def remove_edge(self, edge_id: str) -> bool:
        """移除边

        Args:
            edge_id: 边ID

        Returns:
            是否成功移除
        """
        if edge_id not in self.edges:
            logger.warning(f"边不存在: {edge_id}")
            return False

        edge = self.edges[edge_id]

        # 移除索引
        self._relation_index[edge.relation_type].discard(edge_id)

        # 移除边
        del self.edges[edge_id]

        # 更新统计
        self.stats["edge_count"] -= 1
        self.stats["relation_distribution"][edge.relation_type.value] -= 1

        logger.debug(f"移除边: {edge_id}")
        return True

    # ========== 图谱查询 ==========

    def get_neighbors(
        self,
        node_id: str,
        relation_type: Optional[RelationType] = None,
        direction: str = "both"  # "out", "in", "both"
    ) -> List[str]:
        """获取邻居节点

        Args:
            node_id: 节点ID
            relation_type: 关系类型过滤
            direction: 方向

        Returns:
            邻居节点ID列表
        """
        neighbors = []

        for edge in self.edges.values():
            if relation_type and edge.relation_type != relation_type:
                continue

            if direction in ["out", "both"] and edge.source_id == node_id:
                neighbors.append(edge.target_id)
            if direction in ["in", "both"] and edge.target_id == node_id:
                neighbors.append(edge.source_id)

        return neighbors

    def find_shortest_path(
        self,
        source_id: str,
        target_id: str,
        max_hops: int = 5
    ) -> Optional[GraphPath]:
        """查找最短路径

        Args:
            source_id: 源节点ID
            target_id: 目标节点ID
            max_hops: 最大跳数

        Returns:
            路径对象，不存在则返回None
        """
        if source_id not in self.nodes or target_id not in self.nodes:
            return None

        # BFS搜索
        queue = [(source_id, [], 0)]
        visited = {source_id}

        while queue:
            current_id, path, hops = queue.pop(0)

            if hops > max_hops:
                continue

            if current_id == target_id:
                # 构建路径
                full_path = [source_id] + path
                edges = self._get_edges_for_path(full_path)
                total_weight = sum(e.weight for e in edges)
                confidence = min(e.confidence for e in edges) if edges else 0.0

                return GraphPath(
                    path_id=f"path_{source_id}_to_{target_id}",
                    node_ids=full_path,
                    edges=edges,
                    total_weight=total_weight,
                    confidence=confidence,
                    reasoning=f"从{source_id}到{target_id}的最短路径，共{hops}跳",
                    metadata={"hops": hops}
                )

            # 探索邻居
            neighbors = self.get_neighbors(current_id)
            for neighbor_id in neighbors:
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, path + [neighbor_id], hops + 1))

        return None

    def _get_edges_for_path(self, node_ids: List[str]) -> List[KnowledgeEdge]:
        """获取路径对应的边"""
        edges = []
        for i in range(len(node_ids) - 1):
            source_id = node_ids[i]
            target_id = node_ids[i + 1]

            # 查找边
            for edge in self.edges.values():
                if edge.source_id == source_id and edge.target_id == target_id:
                    edges.append(edge)
                    break

        return edges

    def query_by_category(
        self,
        category: NodeCategory,
        limit: Optional[int] = None
    ) -> List[KnowledgeNode]:
        """按类别查询节点

        Args:
            category: 节点类别
            limit: 返回数量限制

        Returns:
            节点列表
        """
        node_ids = list(self._category_index[category])
        if limit:
            node_ids = node_ids[:limit]

        return [self.nodes[nid] for nid in node_ids if nid in self.nodes]

    def query_by_relation(
        self,
        relation_type: RelationType,
        limit: Optional[int] = None
    ) -> List[KnowledgeEdge]:
        """按关系类型查询边

        Args:
            relation_type: 关系类型
            limit: 返回数量限制

        Returns:
            边列表
        """
        edge_ids = list(self._relation_index[relation_type])
        if limit:
            edge_ids = edge_ids[:limit]

        return [self.edges[eid] for eid in edge_ids if eid in self.edges]

    def query_by_attributes(
        self,
        attributes: Dict[str, Any]
    ) -> List[KnowledgeNode]:
        """按属性查询节点

        Args:
            attributes: 属性字典

        Returns:
            节点列表
        """
        result_ids = None

        for key, value in attributes.items():
            matching_ids = self._attribute_index.get((key, value), set())
            if result_ids is None:
                result_ids = matching_ids.copy()
            else:
                result_ids &= matching_ids

        if result_ids is None:
            return []

        return [self.nodes[nid] for nid in result_ids if nid in self.nodes]

    # ========== 图谱推理 ==========

    def infer_relations(
        self,
        node_id: str,
        max_depth: int = 3
    ) -> List[GraphPath]:
        """推理关系

        Args:
            node_id: 起始节点ID
            max_depth: 最大推理深度

        Returns:
            推理路径列表
        """
        paths = []

        # 深度优先搜索
        def dfs(current_id: str, path: List[str], edges: List[KnowledgeEdge], depth: int):
            if depth >= max_depth:
                return

            neighbors = self.get_neighbors(current_id)
            for neighbor_id in neighbors:
                # 获取边
                edge = next(
                    (e for e in self.edges.values()
                     if e.source_id == current_id and e.target_id == neighbor_id),
                    None
                )

                if edge:
                    new_path = path + [neighbor_id]
                    new_edges = edges + [edge]

                    # 创建路径对象
                    if len(new_path) > 1:
                        total_weight = sum(e.weight for e in new_edges)
                        confidence = min(e.confidence for e in new_edges)

                        graph_path = GraphPath(
                            path_id=f"infer_{node_id}_to_{neighbor_id}",
                            node_ids=new_path,
                            edges=new_edges,
                            total_weight=total_weight,
                            confidence=confidence,
                            reasoning=f"通过{edge.relation_type.value}关系推理",
                            metadata={"depth": depth + 1}
                        )
                        paths.append(graph_path)

                    # 继续深度搜索
                    dfs(neighbor_id, new_path, new_edges, depth + 1)

        dfs(node_id, [node_id], [], 0)

        # 按置信度排序
        paths.sort(key=lambda p: p.confidence, reverse=True)

        return paths[:10]  # 返回Top 10

    def find_connected_components(
        self,
        min_size: int = 2
    ) -> List[List[str]]:
        """查找连通分量

        Args:
            min_size: 最小组件大小

        Returns:
            连通分量列表
        """
        visited = set()
        components = []

        def bfs(start_id: str) -> List[str]:
            """BFS遍历"""
            component = []
            queue = [start_id]
            visited.add(start_id)

            while queue:
                current_id = queue.pop(0)
                component.append(current_id)

                neighbors = self.get_neighbors(current_id)
                for neighbor_id in neighbors:
                    if neighbor_id not in visited:
                        visited.add(neighbor_id)
                        queue.append(neighbor_id)

            return component

        for node_id in self.nodes:
            if node_id not in visited:
                component = bfs(node_id)
                if len(component) >= min_size:
                    components.append(component)

        # 按大小排序
        components.sort(key=lambda c: len(c), reverse=True)

        return components

    # ========== 图谱导出 ==========

    def export_to_dict(self) -> Dict[str, Any]:
        """导出为字典

        Returns:
            图谱数据字典
        """
        return {
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": [edge.to_dict() for edge in self.edges.values()],
            "stats": dict(self.stats),
            "exported_at": datetime.now().isoformat()
        }

    def export_to_json(self, filepath: str) -> bool:
        """导出为JSON文件

        Args:
            filepath: 文件路径

        Returns:
            是否成功导出
        """
        try:
            data = self.export_to_dict()
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"图谱已导出到: {filepath}")
            return True
        except Exception as e:
            logger.error(f"导出图谱失败: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息

        Returns:
            统计信息字典
        """
        return {
            **self.stats,
            "avg_degree": self._calculate_average_degree(),
            "density": self._calculate_density(),
            "component_count": len(self.find_connected_components())
        }

    def _calculate_average_degree(self) -> float:
        """计算平均度数"""
        if not self.nodes:
            return 0.0

        total_degree = sum(len(self.get_neighbors(nid)) for nid in self.nodes)
        return total_degree / len(self.nodes)

    def _calculate_density(self) -> float:
        """计算图密度"""
        n = len(self.nodes)
        m = len(self.edges)

        if n < 2:
            return 0.0

        # 无向图最大边数：n*(n-1)/2
        max_edges = n * (n - 1) / 2

        return m / max_edges


def create_knowledge_graph(config: Optional[Dict[str, Any]] = None) -> EnhancedKnowledgeGraph:
    """创建知识图谱实例

    Args:
        config: 配置字典

    Returns:
        知识图谱实例
    """
    return EnhancedKnowledgeGraph(config)
