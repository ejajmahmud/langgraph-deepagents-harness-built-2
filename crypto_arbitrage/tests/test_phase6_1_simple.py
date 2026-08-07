"""Phase 6.1 简化测试套件

测试增强知识图谱和决策推理引擎的核心功能。
"""

import asyncio
import os
import sys

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from knowledge.knowledge_graph_builder import (
    EnhancedKnowledgeGraph,
    RelationType,
    NodeCategory,
    create_knowledge_graph
)

# Import corrected module names
try:
    from knowledge.decision_reasoning_engine import (
        DecisionReasoningEngine,
        ReasoningMode,
        create_decision_reasoning_engine
    )
except ImportError:
    # Fallback to actual file name
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "decision_reasoning_engine",
        "../knowledge/decision_reasoning_engine.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    DecisionReasoningEngine = module.DecisionReasoningEngine
    ReasoningMode = module.ReasoningMode
    create_decision_reasoning_engine = module.create_decision_reasoning_engine

try:
    from knowledge.knowledge_graph_visualizer import (
        EnhancedKnowledgeGraphVisualizer,
        create_knowledge_graph_visualizer
    )
except ImportError:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "knowledge_graph_visualizer",
        "../knowledge/knowledge_graph_visualizer.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    EnhancedKnowledgeGraphVisualizer = module.EnhancedKnowledgeGraphVisualizer
    create_knowledge_graph_visualizer = module.create_knowledge_graph_visualizer


async def test_knowledge_graph():
    """Test 1-3: Knowledge Graph Builder"""
    print("\n=== Testing Knowledge Graph Builder ===")

    # Initialize graph
    graph = create_knowledge_graph()
    assert graph is not None
    assert graph.stats["node_count"] == 0
    print("[PASS] Graph initialization")

    # Add nodes
    nodes_added = [
        ("BTC_USDT", "BTC/USDT", NodeCategory.ENTITY, "Bitcoin trading pair"),
        ("ETH_USDT", "ETH/USDT", NodeCategory.ENTITY, "Ethereum trading pair"),
        ("triangular_arbitrage", "Triangular Arbitrage", NodeCategory.STRATEGY, "Arbitrage strategy"),
        ("high_volatility_risk", "High Volatility Risk", NodeCategory.RISK, "Market risk factor")
    ]

    for node_id, label, category, content in nodes_added:
        success = graph.add_node(
            node_id=node_id,
            label=label,
            category=category,
            content=content
        )
        assert success
    print(f"[PASS] Added {len(nodes_added)} nodes")

    # Add edges
    edges_added = [
        ("BTC_to_ETH", "BTC_USDT", "ETH_USDT", RelationType.ASSOCIATION, 0.8),
        ("BTC_to_triangular", "BTC_USDT", "triangular_arbitrage", RelationType.CAUSAL, 0.7),
        ("risk_to_triangular", "high_volatility_risk", "triangular_arbitrage", RelationType.DEPENDENCY, 0.9)
    ]

    for edge_id, source, target, relation, weight in edges_added:
        success = graph.add_edge(
            edge_id=edge_id,
            source_id=source,
            target_id=target,
            relation_type=relation,
            weight=weight
        )
        assert success
    print(f"[PASS] Added {len(edges_added)} edges")

    return graph


async def test_graph_operations(graph):
    """Test 4-5: Graph Query Operations"""
    print("\n=== Testing Graph Operations ===")

    # Test neighbor queries
    neighbors = graph.get_neighbors("BTC_USDT")
    assert len(neighbors) == 2
    print(f"[PASS] Found {len(neighbors)} neighbors for BTC_USDT")

    # Test category queries
    strategy_nodes = graph.query_by_category(NodeCategory.STRATEGY)
    assert len(strategy_nodes) >= 1
    print(f"[PASS] Found {len(strategy_nodes)} strategy nodes")

    # Test path finding
    path = graph.find_shortest_path("BTC_USDT", "triangular_arbitrage")
    assert path is not None
    assert path.path_id is not None
    print(f"[PASS] Found path: {path.path_id} with {len(path.node_ids)} nodes")
    print(f"       Path confidence: {path.confidence:.2%}")


async def test_reasoning_engine(graph):
    """Test 6-9: Decision Reasoning Engine"""
    print("\n=== Testing Decision Reasoning Engine ===")

    # Initialize reasoning engine
    engine = create_decision_reasoning_engine(graph)
    assert engine is not None
    print("[PASS] Reasoning engine initialization")

    # Test path-based reasoning
    inference = await engine.reason_by_path(
        start_node_id="BTC_USDT",
        end_node_id="triangular_arbitrage",
        reasoning_mode=ReasoningMode.PATH_BASED
    )
    assert inference.inference_id is not None
    assert inference.confidence > 0
    print(f"[PASS] Path-based reasoning - confidence: {inference.confidence:.2%}")
    print(f"       Recommended actions: {len(inference.recommended_actions)}")
    print(f"       Risk factors: {len(inference.risk_factors)}")

    # Test deductive reasoning
    deductive_inference = await engine.reason_deductive(
        premise_node_id="BTC_USDT",
        rule_relation=RelationType.CAUSAL,
        conclusion_category=NodeCategory.STRATEGY
    )
    assert deductive_inference.inference_id is not None
    print(f"[PASS] Deductive reasoning completed")

    # Test statistics
    stats = engine.get_stats()
    assert stats["total_inferences"] >= 2
    print(f"[PASS] Statistics - total inferences: {stats['total_inferences']}")


async def test_visualization(graph):
    """Test 10-13: Graph Visualization"""
    print("\n=== Testing Graph Visualization ===")

    # Initialize visualizer
    visualizer = create_knowledge_graph_visualizer(graph)
    assert visualizer is not None
    print("[PASS] Visualizer initialization")

    # Test interactive graph generation
    graph_data = visualizer.generate_interactive_graph(max_nodes=50)
    assert "nodes" in graph_data
    assert "edges" in graph_data
    assert len(graph_data["nodes"]) > 0
    print(f"[PASS] Generated interactive graph - nodes: {len(graph_data['nodes'])}, edges: {len(graph_data['edges'])}")

    # Test path visualization
    path = graph.find_shortest_path("BTC_USDT", "triangular_arbitrage")
    path_viz = visualizer.visualize_path(path)
    assert "nodes" in path_viz
    assert "edges" in path_viz
    print(f"[PASS] Path visualization - path_id: {path_viz['path_id']}")

    # Test Plotly export
    plotly_data = visualizer.export_plotly_graph(graph_data)
    assert "data" in plotly_data
    assert "layout" in plotly_data
    print(f"[PASS] Plotly export - traces: {len(plotly_data['data'])}")


async def test_integration(graph):
    """Test 14-16: Integration Tests"""
    print("\n=== Testing Integration ===")

    # Test end-to-end workflow
    engine = create_decision_reasoning_engine(graph)
    visualizer = create_knowledge_graph_visualizer(graph)

    inference = await engine.reason_by_path("BTC_USDT")
    chain_viz = visualizer.visualize_reasoning_chain(inference.reasoning_chain)

    assert inference.inference_id is not None
    assert chain_viz["chain_id"] is not None
    print(f"[PASS] End-to-end workflow - inference confidence: {inference.confidence:.2%}")

    # Test graph export
    graph_dict = graph.export_to_dict()
    assert "nodes" in graph_dict
    assert "edges" in graph_dict
    print(f"[PASS] Graph export - nodes: {len(graph_dict['nodes'])}, edges: {len(graph_dict['edges'])}")

    # Test statistics
    stats = graph.get_stats()
    assert "node_count" in stats
    assert stats["node_count"] > 0
    print(f"[PASS] Statistics - nodes: {stats['node_count']}, edges: {stats['edge_count']}")
    print(f"       Average degree: {stats['avg_degree']:.2f}")
    print(f"       Density: {stats['density']:.4f}")


async def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Phase 6.1 Test Suite - Starting")
    print("=" * 60)

    try:
        # Test knowledge graph builder
        graph = await test_knowledge_graph()
        await test_graph_operations(graph)

        # Test reasoning engine
        await test_reasoning_engine(graph)

        # Test visualization
        await test_visualization(graph)

        # Test integration
        await test_integration(graph)

        print("\n" + "=" * 60)
        print("SUCCESS: All tests passed!")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\nFAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
