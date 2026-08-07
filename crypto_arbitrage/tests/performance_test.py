"""Phase 7.1 性能基准测试

测试知识图谱存储和推理历史的性能指标。

创建时间：2026-04-19
"""

import asyncio
import time
import random
from datetime import datetime, timedelta
from typing import List

import sys
import os

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

from knowledge.knowledge_graph_memory_storage import (
    KnowledgeGraphMemoryStorage,
    create_knowledge_graph_memory_storage
)

from tests.test_phase7 import SimpleMemoryReasoningHistoryStorage


class PerformanceBenchmark:
    """性能基准测试"""

    def __init__(self):
        self.results = {}

    def record_performance(self, test_name: str, duration_ms: float, operations: int):
        """记录性能结果

        Args:
            test_name: 测试名称
            duration_ms: 执行时间（毫秒）
            operations: 操作次数
        """
        ops_per_second = operations / (duration_ms / 1000) if duration_ms > 0 else 0

        self.results[test_name] = {
            'duration_ms': duration_ms,
            'operations': operations,
            'ops_per_second': ops_per_second,
            'avg_time_per_op_ms': duration_ms / operations if operations > 0 else 0
        }

    def print_results(self):
        """打印性能结果"""
        print("\n" + "=" * 60)
        print("PERFORMANCE BENCHMARK RESULTS")
        print("=" * 60)

        for test_name, metrics in self.results.items():
            print(f"\n{test_name}:")
            print(f"  Total Time: {metrics['duration_ms']:.2f} ms")
            print(f"  Operations: {metrics['operations']}")
            print(f"  Ops/Second: {metrics['ops_per_second']:.2f}")
            print(f"  Avg Time/Op: {metrics['avg_time_per_op_ms']:.4f} ms")

        print("\n" + "=" * 60)


async def benchmark_graph_operations(benchmark: PerformanceBenchmark):
    """基准测试图谱操作性能"""
    print("\n[1] Graph Operations Performance Test")

    # 创建存储
    storage = create_knowledge_graph_memory_storage(
        graph_id="benchmark_graph",
        auto_save_enabled=False
    )

    # 测试节点添加性能
    print("Testing node addition performance...")
    graph = create_knowledge_graph()

    start_time = time.time()
    for i in range(100):
        node_id = f"BENCHMARK_NODE_{i}"
        graph.add_node(
            node_id=node_id,
            label=f"Node {i}",
            category=NodeCategory.ENTITY,
            content=f"Test content for node {i}",
            attributes={"index": i, "type": "benchmark"}
        )

    duration_ms = (time.time() - start_time) * 1000
    benchmark.record_performance("Graph Node Addition", duration_ms, 100)
    print(f"  100 nodes added in {duration_ms:.2f} ms")

    # 测试边添加性能
    print("Testing edge addition performance...")
    start_time = time.time()
    for i in range(50):
        edge_id = f"BENCHMARK_EDGE_{i}"
        source_id = f"BENCHMARK_NODE_{i}"
        target_id = f"BENCHMARK_NODE_{(i + 1) % 100}"
        graph.add_edge(
            edge_id=edge_id,
            source_id=source_id,
            target_id=target_id,
            relation_type=RelationType.ASSOCIATION,
            weight=random.random(),
            confidence=random.random()
        )

    duration_ms = (time.time() - start_time) * 1000
    benchmark.record_performance("Graph Edge Addition", duration_ms, 50)
    print(f"  50 edges added in {duration_ms:.2f} ms")

    # 测试图谱保存性能
    print("Testing graph save performance...")
    start_time = time.time()
    version_id = await storage.save_graph(graph, save_reason="benchmark")
    duration_ms = (time.time() - start_time) * 1000
    benchmark.record_performance("Graph Save", duration_ms, 1)
    print(f"  Graph saved in {duration_ms:.2f} ms")

    # 测试图谱加载性能
    print("Testing graph load performance...")
    start_time = time.time()
    loaded_graph = await storage.load_graph()
    duration_ms = (time.time() - start_time) * 1000
    benchmark.record_performance("Graph Load", duration_ms, 1)
    print(f"  Graph loaded in {duration_ms:.2f} ms")

    # 测试节点搜索性能
    print("Testing node search performance...")
    start_time = time.time()
    for i in range(10):
        results = await storage.search_nodes(
            query=f"benchmark {i}",
            top_k=10
        )
    duration_ms = (time.time() - start_time) * 1000
    benchmark.record_performance("Node Search (10 queries)", duration_ms, 10)
    print(f"  10 searches completed in {duration_ms:.2f} ms")


async def benchmark_reasoning_operations(benchmark: PerformanceBenchmark):
    """基准测试推理操作性能"""
    print("\n[2] Reasoning Operations Performance Test")

    # 创建存储
    storage = SimpleMemoryReasoningHistoryStorage()

    # 测试推理保存性能
    print("Testing inference save performance...")

    from knowledge.decision_reasoning_engine import (
        DecisionInference,
        ReasoningChain,
        ReasoningStep
    )

    start_time = time.time()
    for i in range(20):
        reasoning_chain = ReasoningChain(
            chain_id=f"benchmark_chain_{i}",
            start_node=f"node_{i}",
            end_node=f"node_{i+1}",
            steps=[
                ReasoningStep(
                    step_id=f"step_{i}",
                    reasoning_mode="deductive",
                    source_node=f"node_{i}",
                    target_node=f"node_{i+1}",
                    reasoning=f"Benchmark reasoning step {i}",
                    evidence=[f"evidence_{i}"],
                    confidence=random.random()
                )
            ],
            conclusion=f"Benchmark conclusion {i}",
            overall_confidence=random.random(),
            reasoning_mode="deductive",
            metadata={"benchmark": True}
        )

        inference = DecisionInference(
            inference_id=f"benchmark_inference_{i}",
            decision_node=f"node_{i+1}",
            reasoning_chain=reasoning_chain,
            supporting_graph_paths=[],
            confidence=random.random(),
            reasoning=f"Benchmark reasoning {i}",
            recommended_actions=[f"action_{i}"],
            risk_factors=[f"risk_{i}"],
            metadata={"benchmark": True, "timestamp": datetime.now().isoformat()}
        )

        await storage.save_inference(inference)

    duration_ms = (time.time() - start_time) * 1000
    benchmark.record_performance("Inference Save (20 operations)", duration_ms, 20)
    print(f"  20 inferences saved in {duration_ms:.2f} ms")

    # 测试推理历史检索性能
    print("Testing inference history retrieval performance...")
    start_time = time.time()
    for i in range(5):
        history = await storage.get_inference_history(limit=20)
    duration_ms = (time.time() - start_time) * 1000
    benchmark.record_performance("History Retrieval (5 queries)", duration_ms, 5)
    print(f"  5 history retrievals completed in {duration_ms:.2f} ms")

    # 测试推理搜索性能
    print("Testing inference search performance...")
    start_time = time.time()
    for i in range(10):
        results = await storage.search_inferences(
            query="benchmark",
            top_k=10
        )
    duration_ms = (time.time() - start_time) * 1000
    benchmark.record_performance("Inference Search (10 queries)", duration_ms, 10)
    print(f"  10 searches completed in {duration_ms:.2f} ms")

    # 测试统计分析性能
    print("Testing statistics calculation performance...")
    start_time = time.time()
    for i in range(5):
        stats = await storage.get_reasoning_stats(days=7)
        performance = await storage.get_mode_performance()
    duration_ms = (time.time() - start_time) * 1000
    benchmark.record_performance("Statistics Calculation (5 iterations)", duration_ms, 5)
    print(f"  5 statistics calculations completed in {duration_ms:.2f} ms")


async def benchmark_integration_operations(benchmark: PerformanceBenchmark):
    """基准测试集成操作性能"""
    print("\n[3] Integration Operations Performance Test")

    # 创建存储
    graph_storage = create_knowledge_graph_memory_storage(
        graph_id="integration_benchmark",
        auto_save_enabled=False
    )
    history_storage = SimpleMemoryReasoningHistoryStorage()

    # 创建测试图谱
    print("Creating test graph...")
    graph = create_knowledge_graph()
    for i in range(10):
        graph.add_node(
            node_id=f"INT_NODE_{i}",
            label=f"Integration Node {i}",
            category=NodeCategory.ENTITY,
            content=f"Integration test content {i}",
            attributes={"type": "test"}
        )

    # 测试集成保存性能
    print("Testing integrated save performance...")
    start_time = time.time()

    # 保存图谱
    version_id = await graph_storage.save_graph(graph)

    # 创建和保存推理
    from knowledge.decision_reasoning_engine import (
        DecisionInference,
        ReasoningChain,
        ReasoningStep
    )

    reasoning_chain = ReasoningChain(
        chain_id="integration_chain",
        start_node="INT_NODE_0",
        end_node="INT_NODE_9",
        steps=[
            ReasoningStep(
                step_id="integration_step",
                reasoning_mode="deductive",
                source_node="INT_NODE_0",
                target_node="INT_NODE_9",
                reasoning="Integration test reasoning",
                evidence=["integration evidence"],
                confidence=0.85
            )
        ],
        conclusion="Integration test conclusion",
        overall_confidence=0.85,
        reasoning_mode="deductive",
        metadata={"integration_test": True}
    )

    inference = DecisionInference(
        inference_id="integration_inference",
        decision_node="INT_NODE_9",
        reasoning_chain=reasoning_chain,
        supporting_graph_paths=[],
        confidence=0.85,
        reasoning="Integration test reasoning",
        recommended_actions=["integration action"],
        risk_factors=["integration risk"],
        metadata={"integration_test": True}
    )

    history_id = await history_storage.save_inference(inference)

    duration_ms = (time.time() - start_time) * 1000
    benchmark.record_performance("Integrated Save", duration_ms, 1)
    print(f"  Integrated save completed in {duration_ms:.2f} ms")

    # 测试集成搜索性能
    print("Testing integrated search performance...")
    start_time = time.time()

    # 同时搜索图谱和推理历史
    graph_results = await graph_storage.search_nodes("integration", top_k=5)
    inference_results = await history_storage.search_inferences("integration", top_k=5)

    duration_ms = (time.time() - start_time) * 1000
    benchmark.record_performance("Integrated Search", duration_ms, 1)
    print(f"  Integrated search completed in {duration_ms:.2f} ms")


async def main():
    """主函数"""
    print("=" * 60)
    print("Phase 7.1 Performance Benchmark")
    print("=" * 60)

    benchmark = PerformanceBenchmark()

    try:
        # 执行基准测试
        await benchmark_graph_operations(benchmark)
        await benchmark_reasoning_operations(benchmark)
        await benchmark_integration_operations(benchmark)

        # 打印结果
        benchmark.print_results()

        # 性能评级
        print("\nPERFORMANCE RATING:")
        print("=" * 60)

        # 分析性能指标
        save_performance = benchmark.results.get('Graph Save', {})
        if save_performance.get('duration_ms', 9999) < 500:
            graph_rating = "EXCELLENT"
        elif save_performance.get('duration_ms', 9999) < 1000:
            graph_rating = "GOOD"
        else:
            graph_rating = "NEEDS OPTIMIZATION"

        inference_performance = benchmark.results.get('Inference Save (20 operations)', {})
        ops_per_sec = inference_performance.get('ops_per_second', 0)
        if ops_per_sec > 50:
            inference_rating = "EXCELLENT"
        elif ops_per_sec > 20:
            inference_rating = "GOOD"
        else:
            inference_rating = "NEEDS OPTIMIZATION"

        search_performance = benchmark.results.get('Node Search (10 queries)', {})
        avg_search_time = search_performance.get('avg_time_per_op_ms', 9999)
        if avg_search_time < 10:
            search_rating = "EXCELLENT"
        elif avg_search_time < 50:
            search_rating = "GOOD"
        else:
            search_rating = "NEEDS OPTIMIZATION"

        print(f"Graph Operations: {graph_rating}")
        print(f"Reasoning Operations: {inference_rating}")
        print(f"Search Performance: {search_rating}")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] Benchmark failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())