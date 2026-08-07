"""知识图谱可视化

生成知识库的交互式网络图，展示知识之间的关系。

功能：
- 节点：知识条目
- 边：知识关联（相似度、类别关联等）
- 交互：缩放、拖拽、悬停

输出格式：Plotly JSON / Cytoscape.js JSON
"""

import json
from typing import Any, Dict, List, Optional, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class KnowledgeGraphVisualizer:
    """知识图谱可视化生成器

    生成知识库的网络图，展示知识条目之间的关系。
    """

    def __init__(self):
        """初始化可视化生成器"""
        pass

    def generate_graph(
        self,
        knowledge_items: List[Dict[str, Any]],
        similarity_threshold: float = 0.3,
        max_nodes: int = 50
    ) -> Dict[str, Any]:
        """生成知识图谱

        Args:
            knowledge_items: 知识条目列表
                - id: 知识ID
                - content: 知识内容
                - category: 知识类别
                - metadata: 元数据（可选）
            similarity_threshold: 相似度阈值（超过此值创建边）
            max_nodes: 最大节点数

        Returns:
            图谱数据字典
        """
        if not knowledge_items:
            return {"nodes": [], "edges": []}

        # 限制节点数量
        if len(knowledge_items) > max_nodes:
            knowledge_items = knowledge_items[:max_nodes]

        # 生成节点
        nodes = self._generate_nodes(knowledge_items)

        # 生成边（基于相似度）
        edges = self._generate_edges(
            knowledge_items,
            similarity_threshold
        )

        # 计算节点布局位置
        nodes_with_pos = self._calculate_layout(nodes, edges)

        return {
            "nodes": nodes_with_pos,
            "edges": edges,
            "stats": {
                "node_count": len(nodes),
                "edge_count": len(edges)
            }
        }

    def _generate_nodes(self, knowledge_items: List[Dict]) -> List[Dict]:
        """生成节点列表

        Args:
            knowledge_items: 知识条目列表

        Returns:
            节点列表
        """
        nodes = []

        # 类别颜色映射
        category_colors = {
            "decision": "#00D4FF",
            "market": "#FF6B6B",
            "strategy": "#4ECDC4",
            "risk": "#FFE66D",
            "performance": "#95E1D3",
            "alert": "#F38181",
            "default": "#808080"
        }

        for item in knowledge_items:
            node_id = item.get("id", "")
            content = item.get("content", "")
            category = item.get("category", "default")

            # 提取标题（前50个字符）
            title = content[:50] + "..." if len(content) > 50 else content

            nodes.append({
                "id": node_id,
                "label": title,
                "category": category,
                "color": category_colors.get(category, category_colors["default"]),
                "size": 20,
                "metadata": item.get("metadata", {})
            })

        return nodes

    def _generate_edges(
        self,
        knowledge_items: List[Dict],
        similarity_threshold: float
    ) -> List[Dict]:
        """生成边列表（基于TF-IDF相似度）

        Args:
            knowledge_items: 知识条目列表
            similarity_threshold: 相似度阈值

        Returns:
            边列表
        """
        edges = []

        # 提取文本内容
        texts = [item.get("content", "") for item in knowledge_items]

        if not texts or len(texts) < 2:
            return edges

        # 计算TF-IDF和相似度
        try:
            vectorizer = TfidfVectorizer(max_features=100)
            tfidf_matrix = vectorizer.fit_transform(texts)
            similarity_matrix = cosine_similarity(tfidf_matrix)

            # 创建边
            for i in range(len(knowledge_items)):
                for j in range(i + 1, len(knowledge_items)):
                    similarity = similarity_matrix[i][j]

                    if similarity >= similarity_threshold:
                        edges.append({
                            "source": knowledge_items[i].get("id", ""),
                            "target": knowledge_items[j].get("id", ""),
                            "weight": similarity,
                            "label": f"{similarity:.2f}"
                        })
        except Exception as e:
            print(f"Error calculating similarities: {e}")
            return []

        return edges

    def _calculate_layout(
        self,
        nodes: List[Dict],
        edges: List[Dict]
    ) -> List[Dict]:
        """计算节点布局位置（简单力导向算法）

        Args:
            nodes: 节点列表
            edges: 边列表

        Returns:
            带位置的节点列表
        """
        import math
        import random

        # 创建节点ID到索引的映射
        node_ids = {node["id"]: i for i, node in enumerate(nodes)}

        # 初始随机位置
        for node in nodes:
            node["x"] = random.uniform(-10, 10)
            node["y"] = random.uniform(-10, 10)

        # 简单迭代（10次）
        for iteration in range(10):
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
                    force = 1.0 / (dist * dist)
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
                force = 0.5 * (dist - 1.0)
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

        return nodes

    def generate_plotly_graph(
        self,
        knowledge_items: List[Dict],
        similarity_threshold: float = 0.3
    ) -> Dict[str, Any]:
        """生成Plotly格式的知识图谱

        Args:
            knowledge_items: 知识条目列表
            similarity_threshold: 相似度阈值

        Returns:
            Plotly图表数据
        """
        graph_data = self.generate_graph(knowledge_items, similarity_threshold)

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

        traces = []

        # 边
        if edge_x and edge_y:
            traces.append({
                "x": edge_x,
                "y": edge_y,
                "mode": "lines",
                "line": {"width": 0.5, "color": "#888"},
                "hoverinfo": "none",
                "type": "scatter"
            })

        # 节点
        traces.append({
            "x": node_x,
            "y": node_y,
            "mode": "markers",
            "marker": {
                "size": 10,
                "color": node_colors
            },
            "text": node_text,
            "hoverinfo": "text",
            "type": "scatter"
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

    def filter_by_category(
        self,
        knowledge_items: List[Dict],
        category: str
    ) -> List[Dict]:
        """按类别过滤知识条目

        Args:
            knowledge_items: 知识条目列表
            category: 类别名称

        Returns:
            过滤后的知识条目列表
        """
        return [item for item in knowledge_items if item.get("category") == category]

    def filter_by_keywords(
        self,
        knowledge_items: List[Dict],
        keywords: List[str]
    ) -> List[Dict]:
        """按关键词过滤知识条目

        Args:
            knowledge_items: 知识条目列表
            keywords: 关键词列表

        Returns:
            过滤后的知识条目列表
        """
        filtered = []
        for item in knowledge_items:
            content = item.get("content", "").lower()
            if any(keyword.lower() in content for keyword in keywords):
                filtered.append(item)
        return filtered


def create_knowledge_graph_visualizer() -> KnowledgeGraphVisualizer:
    """工厂函数：创建知识图谱可视化生成器

    Returns:
        KnowledgeGraphVisualizer实例
    """
    return KnowledgeGraphVisualizer()
