"""内存知识图谱存储实现 - Phase 7.1

使用内存存储实现知识图谱存储，用于测试和开发环境。

核心功能：
1. 基于内存的知识图谱存储
2. 图谱保存和加载
3. 快照管理
4. 语义搜索（基础实现）

创建时间：2026-04-19
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class KnowledgeGraphMemoryStorage:
    """内存知识图谱存储实现

    使用内存字典存储知识图谱，适用于测试和开发环境。
    """

    def __init__(
        self,
        graph_id: str = "default_graph",
        auto_save_enabled: bool = True
    ):
        """初始化内存图谱存储

        Args:
            graph_id: 图谱ID
            auto_save_enabled: 是否启用自动保存
        """
        self.graph_id = graph_id
        self.auto_save_enabled = auto_save_enabled

        # 内存存储
        self._nodes: Dict[str, Dict] = {}
        self._edges: Dict[str, Dict] = {}
        self._snapshots: List[Dict] = []

        # 脏变更追踪
        self._dirty_nodes: set = set()
        self._dirty_edges: set = set()

        logger.info(f"初始化内存图谱存储: {graph_id}")

    async def save_graph(
        self,
        graph,
        save_reason: str = "manual_save"
    ) -> str:
        """保存知识图谱

        Args:
            graph: 知识图谱实例
            save_reason: 保存原因

        Returns:
            版本ID
        """
        # 序列化图谱数据
        timestamp = datetime.now()
        snapshot_id = f"snapshot_{self.graph_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}"

        # 收集所有节点和边
        nodes_data = {}
        edges_data = {}

        # 收集节点数据
        for node_id in graph.nodes:
            node = graph.get_node(node_id)
            if node:
                nodes_data[node_id] = {
                    'id': node.node_id,
                    'label': node.label,
                    'category': node.category.value if hasattr(node.category, 'value') else str(node.category),
                    'content': node.content,
                    'attributes': node.attributes,
                    'embedding': node.embedding
                }

        # 收集边数据
        for edge_id in graph.edges:
            edge = graph.get_edge(edge_id)
            if edge:
                edges_data[edge_id] = {
                    'id': edge.edge_id,
                    'source_id': edge.source_id,
                    'target_id': edge.target_id,
                    'relation_type': edge.relation_type.value if hasattr(edge.relation_type, 'value') else str(edge.relation_type),
                    'weight': edge.weight,
                    'confidence': edge.confidence,
                    'metadata': edge.metadata,
                    'evidence': edge.evidence,
                    'embedding': edge.embedding if hasattr(edge, 'embedding') else None
                }

        # 创建快照
        snapshot = {
            'snapshot_id': snapshot_id,
            'graph_id': self.graph_id,
            'timestamp': timestamp.isoformat(),
            'save_reason': save_reason,
            'node_count': len(nodes_data),
            'edge_count': len(edges_data),
            'nodes': nodes_data,
            'edges': edges_data
        }

        # 保存到内存
        self._nodes.update(nodes_data)
        self._edges.update(edges_data)
        self._snapshots.append(snapshot)

        # 清理脏变更
        self._dirty_nodes.clear()
        self._dirty_edges.clear()

        logger.info(f"图谱保存成功: {snapshot_id}, 节点数: {len(nodes_data)}, 边数: {len(edges_data)}")
        return snapshot_id

    async def load_graph(self):
        """加载知识图谱

        Returns:
            知识图谱实例
        """
        from knowledge.knowledge_graph_builder import EnhancedKnowledgeGraph, RelationType, NodeCategory

        # 创建新图谱
        graph = EnhancedKnowledgeGraph()

        # 恢复节点
        for node_id, node_data in self._nodes.items():
            try:
                # 转换类别
                category = NodeCategory.ENTITY
                if node_data.get('category'):
                    try:
                        category = NodeCategory(node_data['category'])
                    except (ValueError, KeyError):
                        category = NodeCategory.ENTITY

                graph.add_node(
                    node_id=node_id,
                    label=node_data.get('label', node_id),
                    category=category,
                    content=node_data.get('content', ''),
                    attributes=node_data.get('attributes', {}),
                    embedding=node_data.get('embedding')
                )
            except Exception as e:
                logger.warning(f"加载节点失败 {node_id}: {e}")

        # 恢复边
        for edge_id, edge_data in self._edges.items():
            try:
                # 转换关系类型
                relation_type = RelationType.ASSOCIATION
                if edge_data.get('relation_type'):
                    try:
                        relation_type = RelationType(edge_data['relation_type'])
                    except (ValueError, KeyError):
                        relation_type = RelationType.ASSOCIATION

                graph.add_edge(
                    edge_id=edge_id,
                    source_id=edge_data.get('source_id'),
                    target_id=edge_data.get('target_id'),
                    relation_type=relation_type,
                    weight=edge_data.get('weight', 1.0),
                    confidence=edge_data.get('confidence', 1.0),
                    metadata=edge_data.get('metadata', {}),
                    evidence=edge_data.get('evidence', [])
                )
            except Exception as e:
                logger.warning(f"加载边失败 {edge_id}: {e}")

        logger.info(f"图谱加载成功: {len(self._nodes)} 个节点, {len(self._edges)} 条边")
        return graph

    async def get_snapshots(self, limit: int = 10) -> List[Dict]:
        """获取快照列表

        Args:
            limit: 返回的快照数量限制

        Returns:
            快照列表
        """
        snapshots = sorted(
            self._snapshots,
            key=lambda x: x['timestamp'],
            reverse=True
        )
        return snapshots[:limit]

    async def search_nodes(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """搜索节点

        Args:
            query: 搜索查询
            top_k: 返回结果数量
            filters: 过滤条件

        Returns:
            搜索结果列表
        """
        query_lower = query.lower()
        results = []

        for node_id, node_data in self._nodes.items():
            # 在多个字段中搜索
            content = node_data.get('content', '').lower()
            label = node_data.get('label', '').lower()
            attributes_str = str(node_data.get('attributes', {})).lower()
            metadata_str = str(node_data.get('metadata', {})).lower()
            category_str = node_data.get('category', '').lower()

            # 检查是否匹配任何字段
            found = (
                query_lower in content or
                query_lower in label or
                query_lower in attributes_str or
                query_lower in metadata_str or
                query_lower in category_str
            )

            if found:
                # 计算简单相似度
                similarity = 0.8

                result = {
                    'node_id': node_id,
                    'label': node_data.get('label'),
                    'content': node_data.get('content'),
                    'similarity_score': similarity,
                    'attributes': node_data.get('attributes', {}),
                    'metadata': node_data.get('metadata', {})
                }

                results.append(result)

        # 按相似度排序
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        return results[:top_k]

    async def search_edges(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """搜索边

        Args:
            query: 搜索查询
            top_k: 返回结果数量
            filters: 过滤条件

        Returns:
            搜索结果列表
        """
        query_lower = query.lower()
        results = []

        for edge_id, edge_data in self._edges.items():
            # 在边的元数据中搜索
            metadata_str = str(edge_data.get('metadata', {})).lower()
            relation_type = edge_data.get('relation_type', '').lower()

            if query_lower in metadata_str or query_lower in relation_type:
                similarity = 0.7

                result = {
                    'edge_id': edge_id,
                    'source_id': edge_data.get('source_id'),
                    'target_id': edge_data.get('target_id'),
                    'relation_type': edge_data.get('relation_type'),
                    'similarity_score': similarity,
                    'metadata': edge_data.get('metadata', {})
                }

                results.append(result)

        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        return results[:top_k]

    async def get_storage_stats(self) -> Dict[str, Any]:
        """获取存储统计信息

        Returns:
            统计信息字典
        """
        return {
            'node_count': len(self._nodes),
            'edge_count': len(self._edges),
            'snapshot_count': len(self._snapshots),
            'dirty_nodes': len(self._dirty_nodes),
            'dirty_edges': len(self._dirty_edges),
            'graph_id': self.graph_id
        }

    async def close(self):
        """关闭存储"""
        logger.info("内存图谱存储关闭")


def create_knowledge_graph_memory_storage(
    graph_id: str = "default_graph",
    auto_save_enabled: bool = True
) -> KnowledgeGraphMemoryStorage:
    """创建知识图谱内存存储

    Args:
        graph_id: 图谱ID
        auto_save_enabled: 是否启用自动保存

    Returns:
        知识图谱内存存储实例
    """
    return KnowledgeGraphMemoryStorage(
        graph_id=graph_id,
        auto_save_enabled=auto_save_enabled
    )