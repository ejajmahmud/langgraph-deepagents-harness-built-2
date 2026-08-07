"""简化的 V5.10 Phase 5 测试运行器

只运行最核心的测试来验证功能。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tools.search_cache import SearchCache
from tools.vector_embedding_batch import (
    VectorEmbeddingBatchOptimizer,
    mock_embedding_function
)
from monitoring.health_check_api import HealthCheckAPI, HealthStatus
from tools.data_migration import DataMigrator


async def run_core_tests():
    """运行核心测试"""
    print("=" * 60)
    print("V5.10 Phase 5 核心功能测试")
    print("=" * 60)

    # 测试1: 搜索缓存
    print("\n[1/4] 测试搜索缓存...")
    cache = SearchCache()
    await cache.start()
    try:
        # 测试价格缓存
        async def fetch_price():
            await asyncio.sleep(0.05)
            return {'price': 50000.0, 'timestamp': time.time()}

        import time
        t1 = time.time()
        result1 = await cache.get_price_cached('binance', 'BTC/USDT', fetch_price)
        t2 = time.time()
        result2 = await cache.get_price_cached('binance', 'BTC/USDT', fetch_price)
        t3 = time.time()

        assert result1 is not None
        assert result2 is not None
        assert result1['price'] == result2['price']

        # 缓存查询应该快很多
        cache_time = t3 - t2
        print(f"  首次查询: {(t2-t1)*1000:.1f}ms")
        print(f"  缓存查询: {cache_time*1000:.1f}ms")
        assert cache_time < 0.01, f"缓存查询太慢: {cache_time:.3f}s"

        stats = cache.get_stats()
        price_stats = stats['price_cache']
        print(f"  缓存统计: 命中{price_stats['hits']}次, "
              f"未命中{price_stats['misses']}次")
        print("  [PASS] 搜索缓存测试通过")
    except Exception as e:
        print(f"  [FAIL] 搜索缓存测试失败: {e}")
    finally:
        await cache.stop()

    # 测试2: 向量嵌入批处理
    print("\n[2/4] 测试向量嵌入批处理...")
    optimizer = VectorEmbeddingBatchOptimizer()
    optimizer.set_embedding_function(mock_embedding_function)
    await optimizer.start()
    try:
        # 测试单个向量生成
        text = "这是一个测试文本"
        import time
        start = time.time()
        embedding = await optimizer.get_embedding(text, use_batch=False)
        elapsed = time.time() - start

        assert embedding is not None
        assert len(embedding) == 1536
        print(f"  向量生成耗时: {elapsed*1000:.1f}ms")

        # 测试缓存
        start2 = time.time()
        embedding2 = await optimizer.get_embedding(text, use_batch=False)
        elapsed2 = time.time() - start2

        import numpy as np
        np.testing.assert_array_equal(embedding, embedding2)
        print(f"  缓存查询耗时: {elapsed2*1000:.1f}ms")
        assert elapsed2 < 0.01, f"缓存查询太慢: {elapsed2:.3f}s"

        stats = optimizer.get_stats()
        batch_stats = stats['batch']
        print(f"  统计: 单次请求{batch_stats['single_requests']}次")
        print("  [PASS] 向量嵌入批处理测试通过")
    except Exception as e:
        print(f"  [FAIL] 向量嵌入批处理测试失败: {e}")
    finally:
        await optimizer.stop()

    # 测试3: 健康检查API
    print("\n[3/4] 测试健康检查API...")
    health_api = HealthCheckAPI()
    try:
        # 注册测试组件
        def test_check():
            from monitoring.health_check_api import ComponentHealth
            return ComponentHealth(
                name="test_component",
                status=HealthStatus.HEALTHY,
                message="测试组件正常"
            )

        health_api.register_health_check("test_component", test_check)

        # 记录测试指标
        health_api.record_metric("test.metric", 100.0, "count")
        health_api.record_metric("test.metric2", 0.95, "percent")

        # 获取指标
        metrics = health_api.get_metrics()
        print(f"  记录指标数: {len(metrics)}")

        latest = health_api.get_latest_metric("test.metric")
        assert latest is not None
        assert latest.value == 100.0
        print(f"  最新指标值: {latest.value}")

        # 检查组件
        components = await health_api.check_all_components()
        print(f"  组件数: {len(components)}")
        assert len(components) >= 1

        print("  [PASS] 健康检查API测试通过")
    except Exception as e:
        print(f"  [FAIL] 健康检查API测试失败: {e}")
    finally:
        await health_api.stop()

    # 测试4: 数据迁移工具
    print("\n[4/4] 测试数据迁移工具...")
    migrator = DataMigrator()
    try:
        # 测试内存数据导出
        import time
        memory_store = {
            'key1': {'data': 'value1'},
            'key2': {'data': 'value2'},
            'key3': 'data_value_3'
        }

        records = migrator.export_memory_data(memory_store)

        assert len(records) == 3
        assert all(r.source_type == 'memory' for r in records)
        print(f"  导出记录数: {len(records)}")

        # 测试交易历史导出
        trade_history = [
            {'strategy': 'triangular', 'symbol': 'BTC/USDT', 'status': 'completed'},
            {'strategy': 'basis_trading', 'symbol': 'ETH/USDT', 'status': 'completed'}
        ]

        records2 = migrator.export_trade_history(trade_history)
        assert len(records2) == 2
        print(f"  导出交易数: {len(records2)}")

        stats = migrator.get_stats()
        migration_stats = stats['migrations']
        print(f"  总记录数: {migration_stats['records']}")

        print("  [PASS] 数据迁移工具测试通过")
    except Exception as e:
        print(f"  [FAIL] 数据迁移工具测试失败: {e}")

    print("\n" + "=" * 60)
    print("核心功能测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_core_tests())
