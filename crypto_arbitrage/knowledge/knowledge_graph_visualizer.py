"""增强知识图谱可视化 V1.0 - Phase 6.1核心模块

交互式知识图谱可视化，支持关系类型着色、路径追踪和推理链展示。

核心功能：
1. 交互式图谱浏览器
2. 关系类型着色和分类
3. 路径追踪和高亮
4. 推理链可视化
5. 多种可视化格式（Plotly、Cytoscape.js）

基于：V5.10架构设计
创建时间：2026-04-19 15:10
"""

import json
import logging
import math
import random
from typing import Any, Dict, List, Optional, Set, Tuple

from knowledge.knowledge_graph_builder import (
    EnhancedKnowledgeGraph,
    RelationType,
    NodeCategory,
    KnowledgeNode,
    KnowledgeEdge,
    GraphPath
)

logger = logging.getLogger(__name__)


class EnhancedKnowledgeGraphVisualizer:
    """增强知识图谱可视化

    支持交互式图谱浏览器和推理链可视化。
    """

    # 可视化配置
    NODE_SIZE_BASE = 20
    NODE_SIZE_SCALE = 0.5
    EDGE_WIDTH_BASE = 1.0
    EDGE_WIDTH_SCALE = 0.5

    # 颜色配置
    CATEGORY_COLORS = {
        NodeCategory.ENTITY: "#00D4FF",  # 蓝色
        NodeCategory.EVENT: "#FF6B6B",    # 红色
        NodeCategory.PATTERN: "#4ECDC4",   # 青色
        NodeCategory.STRATEGY: "#FFE66D",   # 黄色
        NodeCategory.RISK: "#F38181",      # 粉色
        NodeCategory.METRIC: "#95E1D3",   # 绿色
        NodeCategory.KNOWLEDGE: "#AA96DA",  # 紫色
    }

    RELATION_COLORS = {
        RelationType.CAUSAL: "#FF6B6B",      # 红色
        RelationType.DEPENDENCY: "#4ECDC4",  # 青色
        RelationType.ASSOCIATION: "#FFE66D", # 黄色
        RelationType.TEMPORAL: "#95E1D3",    # 绿色
        RelationType.HIERARCHICAL: "#AA96DA", # 紫色
        RelationType.SIMILARITY: "#FF9F43",  # 橙色
        RelationType.SEQUENTIAL: "#54A0FF",    # 浅蓝
        RelationType.CONDITIONAL: "#5F27CD",  # 深紫
    }

    def __init__(self, knowledge_graph: EnhancedKnowledgeGraph):
        """初始化可视化生成器

        Args:
            knowledge_graph: 知识图谱实例
        """
        self.knowledge_graph = knowledge_graph

        logger.info("✅ 增强知识图谱可视化初始化完成")

    # ========== 图谱生成 ==========

    def generate_interactive_graph(
        self,
        max_nodes: int = 50,
        similarity_threshold: float = 0.3,
        highlight_path: Optional[GraphPath] = None
    ) -> Dict[str, Any]:
        """生成交互式图谱

        Args:
            max_nodes: 最大节点数
            similarity_threshold: 相似度阈值
            highlight_path: 高亮的路径

        Returns:
            图谱数据字典
        """
        # 获取节点和边
        nodes_data = list(self.knowledge_graph.nodes.values())
        edges_data = list(self.knowledge_graph.edges.values())

        # 限制节点数量
        if len(nodes_data) > max_nodes:
            nodes_data = self._select_high_priority_nodes(nodes_data, max_nodes)

        # 生成节点
        nodes = self._generate_visual_nodes(nodes_data, highlight_path)

        # 生成边（仅保留存在的边）
        edges = self._generate_visual_edges(nodes_data, edges_data, highlight_path)

        # 计算布局位置
        nodes_with_pos = self._calculate_force_directed_layout(nodes, edges)

        return {
            "nodes": nodes_with_pos,
            "edges": edges,
            "stats": {
                "node_count": len(nodes),
                "edge_count": len(edges),
                "highlighted_path": highlight_path.path_id if highlight_path else None
            },
            "layout": "force_directed"
        }

    def _select_high_priority_nodes(
        self,
        nodes: List[KnowledgeNode],
        limit: int
    ) -> List[KnowledgeNode]:
        """选择高优先级节点"""
        # 按节点重要性排序（简化版本：按度数）
        node_scores = []
        for node in nodes:
            neighbors = self.knowledge_graph.get_neighbors(node.node_id)
            score = len(neighbors)
            node_scores.append((score, node))

        node_scores.sort(key=lambda x: x[0], reverse=True)

        return [node for score, node in node_scores[:limit]]

    def _generate_visual_nodes(
        self,
        nodes: List[KnowledgeNode],
        highlight_path: Optional[GraphPath]
    ) -> List[Dict]:
        """生成可视化节点"""
        visual_nodes = []

        # 高亮节点集合
        highlighted_nodes = set(highlight_path.node_ids) if highlight_path else set()

        for node in nodes:
            category_color = self.CATEGORY_COLORS.get(
                node.category,
                "#808080"
            )

            # 节点大小（基于连接数）
            neighbors = self.knowledge_graph.get_neighbors(node.node_id)
            node_size = self.NODE_SIZE_BASE + len(neighbors) * self.NODE_SIZE_SCALE

            visual_nodes.append({
                "id": node.node_id,
                "label": node.label,
                "category": node.category.value,
                "color": category_color,
                "size": node_size,
                "x": random.uniform(-10, 10),
                "y": random.uniform(-10, 10),
                "metadata": node.metadata,
                "highlighted": node.node_id in highlighted_nodes,
                "content": node.content[:100] + "..." if len(node.content) > 100 else node.content
            })

        return visual_nodes

    def _generate_visual_edges(
        self,
        nodes: List[KnowledgeNode],
        edges: List[KnowledgeEdge],
        highlight_path: Optional[GraphPath]
    ) -> List[Dict]:
        """生成可视化边"""
        node_ids = {node.node_id for node in nodes}
        visual_edges = []

        # 高亮边集合
        highlighted_edges = set()
        if highlight_path:
            for edge in highlight_path.edges:
                highlighted_edges.add(edge.edge_id)

        for edge in edges:
            # 过滤边（只保留存在的节点）
            if edge.source_id not in node_ids or edge.target_id not in node_ids:
                continue

            relation_color = self.RELATION_COLORS.get(
                edge.relation_type,
                "#888888"
            )

            # 边宽度（基于权重）
            edge_width = self.EDGE_WIDTH_BASE + edge.weight * self.EDGE_WIDTH_SCALE

            visual_edges.append({
                "id": edge.edge_id,
                "source": edge.source_id,
                "target": edge.target_id,
                "relation_type": edge.relation_type.value,
                "color": relation_color,
                "width": edge_width,
                "weight": edge.weight,
                "confidence": edge.confidence,
                "highlighted": edge.edge_id in highlighted_edges,
                "label": f"{edge.relation_type.value} ({edge.confidence:.2f})"
            })

        return visual_edges

    def _calculate_force_directed_layout(
        self,
        nodes: List[Dict],
        edges: List[Dict],
        iterations: int = 50
    ) -> List[Dict]:
        """计算力导向布局"""
        # 创建节点ID到索引的映射
        node_ids = {node["id"]: i for i, node in enumerate(nodes)}

        # 迭代计算
        for iteration in range(iterations):
            # 斥力（节点之间）
            for i, node1 in enumerate(nodes):
                for j, node2 in enumerate(nodes):
                    if i >= j:
                        continue

                    dx = node1["x"] - node2["x"]
                    dy = node1["y"] - node2["y"]
                    dist = math.sqrt(dx * dx + dy * dy)

                    if dist < 0.1:
                        dist = 0.1

                    # 斥力
                    force = 200.0 / (dist * dist)
                    fx = (dx / dist) * force
                    fy = (dy / dist) * force

                    node1["x"] += fx
                    node1["y"] += fy
                    node2["x"] -= fx
                    node2["y"] -= fy

            # 引力（边）
            for edge in edges:
                source_id = edge["source"]
                target_id = edge["target"]

                if source_id not in node_ids or target_id not in node_ids:
                    continue

                node1 = nodes[node_ids[source_id]]
                node2 = nodes[node_ids[target_id]]

                dx = node1["x"] - node2["x"]
                dy = node1["y"] - node2["y"]
                dist = math.sqrt(dx * dx + dy * dy)

                if dist < 0.1:
                    dist = 0.1

                # 引力（弹簧）
                weight = edge.get("weight", 1.0)
                force = 0.1 * weight * (dist - 2.0)
                fx = (dx / dist) * force
                fy = (dy / dist) * force

                node1["x"] -= fx
                node1["y"] -= fy
                node2["x"] += fx
                node2["y"] += fy

            # 中心引力（保持图居中）
            for node in nodes:
                node["x"] *= 0.95
                node["y"] *= 0.95

            # 防止节点跑出边界
            for node in nodes:
                node["x"] = max(-20, min(20, node["x"]))
                node["y"] = max(-20, min(20, node["y"]))

        return nodes

    # ========== 路径和推理链可视化 ==========

    def visualize_path(
        self,
        path: GraphPath
    ) -> Dict[str, Any]:
        """可视化路径

        Args:
            path: 图谱路径

        Returns:
            路径可视化数据
        """
        # 获取路径节点
        path_nodes = []
        for node_id in path.node_ids:
            node = self.knowledge_graph.get_node(node_id)
            if node:
                path_nodes.append(node)

        # 生成可视化节点
        nodes = self._generate_path_nodes(path_nodes)

        # 生成可视化边
        edges = self._generate_path_edges(path.edges)

        # 线性布局
        nodes_with_pos = self._calculate_linear_layout(nodes)

        return {
            "type": "path_visualization",
            "path_id": path.path_id,
            "nodes": nodes_with_pos,
            "edges": edges,
            "stats": {
                "node_count": len(nodes),
                "edge_count": len(edges),
                "total_weight": path.total_weight,
                "confidence": path.confidence
            }
        }

    def _generate_path_nodes(
        self,
        nodes: List[KnowledgeNode]
    ) -> List[Dict]:
        """生成路径节点"""
        path_nodes = []

        for i, node in enumerate(nodes):
            category_color = self.CATEGORY_COLORS.get(
                node.category,
                "#808080"
            )

            path_nodes.append({
                "id": node.node_id,
                "label": node.label,
                "category": node.category.value,
                "color": category_color,
                "size": 30,
                "position": i,
                "content": node.content
            })

        return path_nodes

    def _generate_path_edges(
        self,
        edges: List[KnowledgeEdge]
    ) -> List[Dict]:
        """生成路径边"""
        path_edges = []

        for edge in edges:
            relation_color = self.RELATION_COLORS.get(
                edge.relation_type,
                "#888888"
            )

            path_edges.append({
                "id": edge.edge_id,
                "source": edge.source_id,
                "target": edge.target_id,
                "relation_type": edge.relation_type.value,
                "color": relation_color,
                "width": 3.0,
                "weight": edge.weight,
                "confidence": edge.confidence,
                "label": f"{edge.relation_type.value}"
            })

        return path_edges

    def _calculate_linear_layout(
        self,
        nodes: List[Dict]
    ) -> List[Dict]:
        """计算线性布局"""
        for node in nodes:
            position = node["position"]
            node["x"] = position * 2.0
            node["y"] = 0.0

        return nodes

    # ========== 推理链可视化 ==========

    def visualize_reasoning_chain(
        self,
        reasoning_chain: 'ReasoningChain'
    ) -> Dict[str, Any]:
        """可视化推理链

        Args:
            reasoning_chain: 推理链对象

        Returns:
            推理链可视化数据
        """
        # 获取推理链节点
        chain_nodes = []
        node_ids = [reasoning_chain.start_node] + [step.target_node for step in reasoning_chain.steps]

        for node_id in node_ids:
            node = self.knowledge_graph.get_node(node_id)
            if node:
                chain_nodes.append(node)

        # 生成可视化节点
        nodes = self._generate_reasoning_nodes(
            chain_nodes,
            reasoning_chain.steps
        )

        # 生成可视化边（推理步骤）
        edges = self._generate_reasoning_edges(reasoning_chain.steps)

        # 层次布局
        nodes_with_pos = self._calculate_hierarchical_layout(nodes, edges)

        return {
            "type": "reasoning_chain_visualization",
            "chain_id": reasoning_chain.chain_id,
            "nodes": nodes_with_pos,
            "edges": edges,
            "conclusion": reasoning_chain.conclusion,
            "overall_confidence": reasoning_chain.overall_confidence,
            "stats": {
                "node_count": len(nodes),
                "edge_count": len(edges),
                "step_count": len(reasoning_chain.steps)
            }
        }

    def _generate_reasoning_nodes(
        self,
        nodes: List[KnowledgeNode],
        steps: List['ReasoningStep']
    ) -> List[Dict]:
        """生成推理节点"""
        reasoning_nodes = []

        for i, node in enumerate(nodes):
            category_color = self.CATEGORY_COLORS.get(
                node.category,
                "#808080"
            )

            # 获取对应的推理步骤
            step_info = None
            if i > 0 and i - 1 < len(steps):
                step = steps[i - 1]
                step_info = {
                    "reasoning": step.reasoning,
                    "confidence": step.confidence,
                    "evidence": step.evidence
                }

            reasoning_nodes.append({
                "id": node.node_id,
                "label": node.label,
                "category": node.category.value,
                "color": category_color,
                "size": 35,
                "level": i,
                "content": node.content,
                "step_info": step_info
            })

        return reasoning_nodes

    def _generate_reasoning_edges(
        self,
        steps: List['ReasoningStep']
    ) -> List[Dict]:
        """生成推理边"""
        reasoning_edges = []

        for i, step in enumerate(steps):
            reasoning_edges.append({
                "id": f"reasoning_edge_{i}",
                "source": step.source_node,
                "target": step.target_node,
                "relation_type": step.reasoning_mode.value,
                "color": self.RELATION_COLORS.get(
                    RelationType.CAUSAL,  # 默认使用因果关系的颜色
                    "#FF6B6B"
                ),
                "width": 2.5,
                "label": step.reasoning[:50] + "..." if len(step.reasoning) > 50 else step.reasoning,
                "confidence": step.confidence,
                "step_id": step.step_id
            })

        return reasoning_edges

    def _calculate_hierarchical_layout(
        self,
        nodes: List[Dict],
        edges: List[Dict]
    ) -> List[Dict]:
        """计算层次布局"""
        # 按层级分组
        nodes_by_level = {}
        for node in nodes:
            level = node["level"]
            if level not in nodes_by_level:
                nodes_by_level[level] = []
            nodes_by_level[level].append(node)

        # 计算每个节点的位置
        for level, level_nodes in nodes_by_level.items():
            count = len(level_nodes)
            if count == 1:
                level_nodes[0]["x"] = level * 2.0
                level_nodes[0]["y"] = 0.0
            else:
                for i, node in enumerate(level_nodes):
                    node["x"] = level * 2.0
                    node["y"] = (i - (count - 1) / 2) * 2.0

        return nodes

    # ========== 导出功能 ==========

    def export_plotly_graph(
        self,
        graph_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """导出Plotly格式的图谱

        Args:
            graph_data: 图谱数据

        Returns:
            Plotly图表数据
        """
        nodes = graph_data["nodes"]
        edges = graph_data["edges"]

        # 边的轨迹
        edge_x = []
        edge_y = []
        for edge in edges:
            source_node = next((n for n in nodes if n["id"] == edge["source"]), None)
            target_node = next((n for n in nodes if n["id"] == edge["target"]), None)
            if source_node and target_node:
                edge_x.extend([source_node["x"], target_node["x"], None])
                edge_y.extend([source_node["y"], target_node["y"], None])

        # 节点的轨迹
        node_x = [node["x"] for node in nodes]
        node_y = [node["y"] for node in nodes]
        node_text = [node["label"] for node in nodes]
        node_colors = [node["color"] for node in nodes]
        node_sizes = [node["size"] for node in nodes]

        traces = []

        # 边
        if edge_x and edge_y:
            traces.append({
                "x": edge_x,
                "y": edge_y,
                "mode": "lines",
                "line": {"width": 0.5, "color": "#888"},
                "hoverinfo": "none",
                "type": "scatter",
                "name": "Edges"
            })

        # 节点
        traces.append({
            "x": node_x,
            "y": node_y,
            "mode": "markers",
            "marker": {
                "size": node_sizes,
                "color": node_colors,
                "line": {"width": 1, "color": "white"}
            },
            "text": node_text,
            "hoverinfo": "text",
            "type": "scatter",
            "name": "Nodes"
        })

        layout = {
            "title": "Knowledge Graph",
            "showlegend": False,
            "hovermode": "closest",
            "margin": {"b": 20, "l": 5, "r": 5, "t": 40},
            "xaxis": {"showgrid": False, "zeroline": False, "showticklabels": False},
            "yaxis": {"showgrid": False, "zeroline": False, "showticklabels": False},
            "template": "plotly_dark"
        }

        return {
            "data": traces,
            "layout": layout
        }

    def export_cytoscape_json(
        self,
        graph_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """导出Cytoscape.js格式的JSON

        Args:
            graph_data: 图谱数据

        Returns:
            Cytoscape.js格式数据
        """
        nodes = graph_data["nodes"]
        edges = graph_data["edges"]

        elements = []

        # 节点
        for node in nodes:
            elements.append({
                "data": {
                    "id": node["id"],
                    "label": node["label"],
                    "category": node["category"],
                    "color": node["color"],
                    "size": node["size"]
                },
                "position": {
                    "x": node["x"],
                    "y": node["y"]
                }
            })

        # 边
        for edge in edges:
            elements.append({
                "data": {
                    "id": edge["id"],
                    "source": edge["source"],
                    "target": edge["target"],
                    "relation_type": edge["relation_type"],
                    "color": edge["color"],
                    "width": edge["width"],
                    "weight": edge["weight"],
                    "confidence": edge["confidence"]
                }
            })

        return {
            "elements": elements,
            "layout": {
                "name": "preset"
            },
            "style": self._generate_cytoscape_styles()
        }

    def _generate_cytoscape_styles(self) -> List[Dict]:
        """生成Cytoscape.js样式"""
        return [
            {
                "selector": "node",
                "style": {
                    "width": "data(size)",
                    "height": "data(size)",
                    "background-color": "data(color)",
                    "label": "data(label)",
                    "font-size": "12px",
                    "text-valign": "center",
                    "text-halign": "center",
                    "border-width": "2px",
                    "border-color": "#ffffff"
                }
            },
            {
                "selector": "edge",
                "style": {
                    "width": "data(width)",
                    "line-color": "data(color)",
                    "target-arrow-color": "data(color)",
                    "target-arrow-shape": "triangle",
                    "curve-style": "bezier"
                }
            },
            {
                "selector": ".highlighted",
                "style": {
                    "border-width": "4px",
                    "border-color": "#FFD700"
                }
            }
        ]


def create_knowledge_graph_visualizer(
    knowledge_graph: EnhancedKnowledgeGraph
) -> EnhancedKnowledgeGraphVisualizer:
    """创建知识图谱可视化实例

    Args:
        knowledge_graph: 知识图谱实例

    Returns:
        知识图谱可视化实例
    """
    return EnhancedKnowledgeGraphVisualizer(knowledge_graph)
