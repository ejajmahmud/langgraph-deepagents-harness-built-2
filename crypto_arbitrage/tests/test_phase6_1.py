"""Phase 6.1 测试套件

测试增强知识图谱和决策推理引擎的核心功能。

测试覆盖：
1. 知识图谱构建和管理
2. 决策推理引擎功能
3. 图谱可视化生成
4. 集成测试

创建时间：2026-04-19
"""

import asyncio
import json
import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from knowledge.knowledge_graph_builder import (
    EnhancedKnowledgeGraph,
    RelationType,
    NodeCategory,
    create_knowledge_graph
)

from knowledge.decision_reasoning_engine import (
    DecisionReasoningEngine,
    ReasoningMode,
    create_decision_reasoning_engine
)

from knowledge.knowledge_graph_visualizer import (
    EnhancedKnowledgeGraphVisualizer,
    create_knowledge_graph_visualizer
)


class TestKnowledgeGraphBuilder:
    """测试知识图谱构建器"""

    def __init__(self):
        self.graph = None

    async def test_init(self):
        """测试图谱初始化"""
        print("\n[测试1] 知识图谱初始化")
        self.graph = create_knowledge_graph()
        assert self.graph is not None, "图谱初始化失败"
        assert self.graph.stats["node_count"] == 0, "初始节点数应为0"
        assert self.graph.stats["edge_count"] == 0, "初始边数应为0"
        print("[SUCCESS] 图谱初始化成功")

    async def test_add_nodes(self):
        """测试添加节点"""
        print("\n[测试2] 添加节点")

        # 添加多个节点
        nodes_to_add = [
            {
                "node_id": "BTC_USDT",
                "label": "BTC/USDT",
                "category": NodeCategory.ENTITY,
                "content": "比特币兑USDT交易对",
                "attributes": {"exchange": "binance", "type": "spot"}
            },
            {
                "node_id": "ETH_USDT",
                "label": "ETH/USDT",
                "category": NodeCategory.ENTITY,
                "content": "以太坊兑USDT交易对",
                "attributes": {"exchange": "binance", "type": "spot"}
            },
            {
                "node_id": "triangular_arbitrage",
                "label": "三角套利",
                "category": NodeCategory.STRATEGY,
                "content": "利用三种货币间价格差异进行套利",
                "attributes": {"risk_level": "low", "profit_potential": "medium"}
            },
            {
                "node_id": "high_volatility_risk",
                "label": "高波动风险",
                "category": NodeCategory.RISK,
                "content": "市场波动率过高导致的风险",
                "attributes": {"severity": "high"}
            }
        ]

        for node_data in nodes_to_add:
            success = self.graph.add_node(**node_data)
            assert success, f"添加节点{node_data['node_id']}失败"

        assert self.graph.stats["node_count"] == 4, "节点数应为4"
        print(f"[SUCCESS] 成功添加{len(nodes_to_add)}个节点")

    async def test_add_edges(self):
        """测试添加边"""
        print("\n[测试3] 添加边")

        # 添加多条边
        edges_to_add = [
            {
                "edge_id": "BTC_to_ETH",
                "source_id": "BTC_USDT",
                "target_id": "ETH_USDT",
                "relation_type": RelationType.ASSOCIATION,
                "weight": 0.8,
                "confidence": 0.9
            },
            {
                "edge_id": "BTC_to_triangular",
                "source_id": "BTC_USDT",
                "target_id": "triangular_arbitrage",
                "relation_type": RelationType.CAUSAL,
                "weight": 0.7,
                "confidence": 0.85
            },
            {
                "edge_id": "risk_to_triangular",
                "source_id": "high_volatility_risk",
                "target_id": "triangular_arbitrage",
                "relation_type": RelationType.DEPENDENCY,
                "weight": 0.9,
                "confidence": 0.8
            }
        ]

        for edge_data in edges_to_add:
            success = self.graph.add_edge(**edge_data)
            assert success, f"添加边{edge_data['edge_id']}失败"

        assert self.graph.stats["edge_count"] == 3, "边数应为3"
        print(f"[SUCCESS] 成功添加{len(edges_to_add)}条边")

    async def test_query_operations(self):
        """测试查询操作"""
        print("\n[测试4] 查询操作")

        # 测试获取邻居节点
        neighbors = self.graph.get_neighbors("BTC_USDT")
        assert len(neighbors) == 2, "BTC_USDT应有2个邻居"
        print(f"[SUCCESS] BTC_USDT的邻居: {neighbors}")

        # 测试按类别查询
        strategy_nodes = self.graph.query_by_category(NodeCategory.STRATEGY)
        assert len(strategy_nodes) >= 1, "应有至少1个策略节点"
        print(f"[SUCCESS] 策略节点数: {len(strategy_nodes)}")

        # 测试按属性查询
        risk_nodes = self.graph.query_by_attributes({"severity": "high"})
        assert len(risk_nodes) >= 1, "应有至少1个高风险节点"
        print(f"[SUCCESS] 高风险节点数: {len(risk_nodes)}")

    async def test_path_finding(self):
        """测试路径查找"""
        print("\n[测试5] 路径查找")

        # 测试最短路径查找
        path = self.graph.find_shortest_path("BTC_USDT", "triangular_arbitrage")
        assert path is not None, "应找到路径"
        assert path.path_id is not None, "路径ID不应为空"
        print(f"[SUCCESS] 找到路径: {path.path_id}")
        print(f"   路径节点: {path.node_ids}")
        print(f"   路径置信度: {path.confidence:.2%}")


class TestDecisionReasoningEngine:
    """测试决策推理引擎"""

    def __init__(self, graph):
        self.graph = graph
        self.reasoning_engine = None

    async def test_init(self):
        """测试推理引擎初始化"""
        print("\n[测试6] 推理引擎初始化")
        self.reasoning_engine = create_decision_reasoning_engine(self.graph)
        assert self.reasoning_engine is not None, "推理引擎初始化失败"
        print("[SUCCESS] 推理引擎初始化成功")

    async def test_path_based_reasoning(self):
        """测试基于路径的推理"""
        print("\n[测试7] 基于路径的推理")

        inference = await self.reasoning_engine.reason_by_path(
            start_node_id="BTC_USDT",
            end_node_id="triangular_arbitrage",
            reasoning_mode=ReasoningMode.PATH_BASED
        )

        assert inference.inference_id is not None, "推断ID不应为空"
        assert inference.decision_node == "triangular_arbitrage", "决策节点应为triangular_arbitrage"
        assert inference.confidence > 0, "置信度应大于0"

        print(f"[SUCCESS] 推理成功")
        print(f"   推断ID: {inference.inference_id}")
        print(f"   决策节点: {inference.decision_node}")
        print(f"   置信度: {inference.confidence:.2%}")
        print(f"   推理: {inference.reasoning}")

    async def test_deductive_reasoning(self):
        """测试演绎推理"""
        print("\n[测试8] 演绎推理")

        inference = await self.reasoning_engine.reason_deductive(
            premise_node_id="BTC_USDT",
            rule_relation=RelationType.CAUSAL,
            conclusion_category=NodeCategory.STRATEGY
        )

        assert inference.inference_id is not None, "推断ID不应为空"
        print(f"[SUCCESS] 演绎推理成功")
        print(f"   推断ID: {inference.inference_id}")
        print(f"   推荐行动: {inference.recommended_actions}")

    async def test_inference_history(self):
        """测试推断历史"""
        print("\n[测试9] 推断历史")

        history = await self.reasoning_engine.get_inference_history(limit=10)
        assert len(history) >= 1, "应有至少1条推断记录"

        stats = self.reasoning_engine.get_stats()
        assert stats["total_inferences"] >= 1, "总推断数应>=1"

        print(f"[SUCCESS] 推断历史记录: {len(history)}条")
        print(f"   统计信息: {stats}")


class TestKnowledgeGraphVisualizer:
    """测试知识图谱可视化"""

    def __init__(self, graph):
        self.graph = graph
        self.visualizer = None

    async def test_init(self):
        """测试可视化初始化"""
        print("\n[测试10] 可视化初始化")
        self.visualizer = create_knowledge_graph_visualizer(self.graph)
        assert self.visualizer is not None, "可视化初始化失败"
        print("[SUCCESS] 可视化初始化成功")

    async def test_interactive_graph(self):
        """测试生成交互式图谱"""
        print("\n[测试11] 生成交互式图谱")

        graph_data = self.visualizer.generate_interactive_graph(
            max_nodes=50,
            similarity_threshold=0.3
        )

        assert "nodes" in graph_data, "应包含nodes"
        assert "edges" in graph_data, "应包含edges"
        assert len(graph_data["nodes"]) > 0, "节点数应大于0"

        print(f"[SUCCESS] 生成交互式图谱成功")
        print(f"   节点数: {len(graph_data['nodes'])}")
        print(f"   边数: {len(graph_data['edges'])}")

    async def test_path_visualization(self):
        """测试路径可视化"""
        print("\n[测试12] 路径可视化")

        # 首先找到一条路径
        path = self.graph.find_shortest_path("BTC_USDT", "triangular_arbitrage")
        assert path is not None, "应找到路径"

        # 可视化路径
        path_viz = self.visualizer.visualize_path(path)

        assert "nodes" in path_viz, "应包含nodes"
        assert "edges" in path_viz, "应包含edges"
        assert path_viz["path_id"] == path.path_id, "路径ID应匹配"

        print(f"[SUCCESS] 路径可视化成功")
        print(f"   路径ID: {path_viz['path_id']}")

    async def test_plotly_export(self):
        """测试Plotly导出"""
        print("\n[测试13] Plotly导出")

        graph_data = self.visualizer.generate_interactive_graph()
        plotly_data = self.visualizer.export_plotly_graph(graph_data)

        assert "data" in plotly_data, "应包含data"
        assert "layout" in plotly_data, "应包含layout"

        print(f"[SUCCESS] Plotly导出成功")
        print(f"   traces数: {len(plotly_data['data'])}")


class TestIntegration:
    """集成测试"""

    def __init__(self, graph):
        self.graph = graph

    async def test_end_to_end_workflow(self):
        """测试端到端工作流"""
        print("\n[集成测试1] 端到端工作流")

        # 1. 创建推理引擎和可视化
        reasoning_engine = create_decision_reasoning_engine(self.graph)
        visualizer = create_knowledge_graph_visualizer(self.graph)

        # 2. 执行推理
        inference = await reasoning_engine.reason_by_path("BTC_USDT")

        # 3. 可视化推理链
        reasoning_chain = inference.reasoning_chain
        chain_viz = visualizer.visualize_reasoning_chain(reasoning_chain)

        assert inference.inference_id is not None, "推断应成功"
        assert chain_viz["chain_id"] is not None, "推理链可视化应成功"

        print(f"[SUCCESS] 端到端工作流成功")
        print(f"   推断置信度: {inference.confidence:.2%}")
        print(f"   推理链步骤数: {chain_viz['stats']['step_count']}")

    async def test_graph_export(self):
        """测试图谱导出"""
        print("\n[集成测试2] 图谱导出")

        # 导出为JSON
        graph_dict = self.graph.export_to_dict()

        assert "nodes" in graph_dict, "应包含nodes"
        assert "edges" in graph_dict, "应包含edges"
        assert graph_dict["stats"]["node_count"] > 0, "节点数应大于0"

        print(f"[SUCCESS] 图谱导出成功")
        print(f"   导出节点数: {len(graph_dict['nodes'])}")
        print(f"   导出边数: {len(graph_dict['edges'])}")

    async def test_statistics(self):
        """测试统计信息"""
        print("\n[集成测试3] 统计信息")

        stats = self.graph.get_stats()

        assert "node_count" in stats, "应包含node_count"
        assert "edge_count" in stats, "应包含edge_count"
        assert stats["node_count"] > 0, "节点数应大于0"

        print(f"[SUCCESS] 统计信息获取成功")
        print(f"   节点数: {stats['node_count']}")
        print(f"   边数: {stats['edge_count']}")
        print(f"   平均度数: {stats['avg_degree']:.2f}")
        print(f"   图密度: {stats['density']:.4f}")


async def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("Phase 6.1 测试套件 - 开始执行")
    print("=" * 60)

    # 测试知识图谱构建器
    graph_test = TestKnowledgeGraphBuilder()
    await graph_test.test_init()
    await graph_test.test_add_nodes()
    await graph_test.test_add_edges()
    await graph_test.test_query_operations()
    await graph_test.test_path_finding()

    # 测试决策推理引擎
    reasoning_test = TestDecisionReasoningEngine(graph_test.graph)
    await reasoning_test.test_init()
    await reasoning_test.test_path_based_reasoning()
    await reasoning_test.test_deductive_reasoning()
    await reasoning_test.test_inference_history()

    # 测试知识图谱可视化
    viz_test = TestKnowledgeGraphVisualizer(graph_test.graph)
    await viz_test.test_init()
    await viz_test.test_interactive_graph()
    await viz_test.test_path_visualization()
    await viz_test.test_plotly_export()

    # 集成测试
    integration_test = TestIntegration(graph_test.graph)
    await integration_test.test_end_to_end_workflow()
    await integration_test.test_graph_export()
    await integration_test.test_statistics()

    print("\n" + "=" * 60)
    print("🎉 所有测试通过！Phase 6.1 测试套件执行完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
