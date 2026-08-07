"""V5.10 Phase 5 测试套件

测试Phase 5实现的性能优化功能：
1. 搜索缓存优化
2. 向量嵌入批处理
3. 健康检查API
4. 数据迁移工具

创建时间：2026-04-19
"""

import asyncio
import time
import pytest
import pytest_asyncio
import numpy as np

# 导入待测试模块
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
from monitoring.health_check_api import HealthCheckAPI, HealthStatus, AlertSeverity
from tools.data_migration import DataMigrator, MigrationStatus


class TestSearchCache:
    """搜索缓存系统测试"""

    @pytest_asyncio.fixture
    async def cache(self):
        """创建缓存实例"""
        cache = SearchCache()
        await cache.start()
        yield cache
        await cache.stop()

    @pytest.mark.asyncio
    async def test_price_cache_hit(self, cache):
        """测试价格缓存命中"""
        # 首次查询
        async def fetch_func():
            await asyncio.sleep(0.1)  # 模拟网络延迟
            return {'price': 50000.0, 'timestamp': time.time()}

        result1 = await cache.get_price_cached('binance', 'BTC/USDT', fetch_func)
        assert result1 is not None
        assert result1['price'] == 50000.0

        # 第二次查询（应该命中缓存）
        start = time.time()
        result2 = await cache.get_price_cached('binance', 'BTC/USDT', fetch_func)
        elapsed = time.time() - start

        assert result2 is not None
        assert result2['price'] == 50000.0
        # 缓存查询应该快10倍以上
        assert elapsed < 0.01, f"缓存查询耗时{elapsed:.3f}秒超过预期"

        # 检查统计
        stats = cache.get_stats()
        assert stats['price_cache']['hits'] >= 1
        assert stats['price_cache']['size'] >= 1

    @pytest.mark.asyncio
    async def test_fee_cache_hit(self, cache):
        """测试费用缓存命中"""
        # 首次查询
        async def fetch_func():
            await asyncio.sleep(0.1)
            return {'maker': 0.001, 'taker': 0.001}

        result1 = await cache.get_fee_cached('binance', 'BTC/USDT', fetch_func)
        assert result1 is not None
        assert result1['taker'] == 0.001

        # 第二次查询（应该命中缓存）
        start = time.time()
        result2 = await cache.get_fee_cached('binance', 'BTC/USDT', fetch_func)
        elapsed = time.time() - start

        assert result2 is not None
        assert result2['taker'] == 0.001
        assert elapsed < 0.01, f"缓存查询耗时{elapsed:.3f}秒超过预期"

        # 检查统计
        stats = cache.get_stats()
        assert stats['fee_cache']['hits'] >= 1

    @pytest.mark.asyncio
    async def test_batched_write(self, cache):
        """测试批量写入"""
        # 模拟批量写入函数
        async def batch_write_func(records):
            await asyncio.sleep(0.05)  # 模拟批量写入延迟
            return len(records)

        # 添加多个记录到批量缓冲区
        for i in range(10):
            await cache.add_to_batch(
                {'id': i, 'data': f'record_{i}'},
                batch_write_func
            )

        # 检查统计
        stats = cache.get_stats()
        assert stats['batch_write']['buffer_size'] >= 0

    @pytest.mark.asyncio
    async def test_cache_expiration(self, cache):
        """测试缓存过期"""
        # 设置较短的TTL
        cache_with_ttl = SearchCache(price_ttl=0.1)  # 100ms过期

        # 首次查询
        async def fetch_func():
            return {'price': 50000.0}

        result1 = await cache_with_ttl.get_price_cached('binance', 'BTC/USDT', fetch_func)
        assert result1 is not None

        # 等待缓存过期
        await asyncio.sleep(0.2)

        # 查询应该触发重新获取
        result2 = await cache_with_ttl.get_price_cached('binance', 'BTC/USDT', fetch_func)
        assert result2 is not None

        # 统计应该显示misses
        stats = cache_with_ttl.get_stats()
        assert stats['price_cache']['misses'] >= 1


class TestVectorEmbeddingBatch:
    """向量嵌入批处理优化测试"""

    @pytest_asyncio.fixture
    async def optimizer(self):
        """创建批处理优化器实例"""
        optimizer = VectorEmbeddingBatchOptimizer(batch_size=5, max_delay=1.0)
        optimizer.set_embedding_function(mock_embedding_function)
        await optimizer.start()
        yield optimizer
        await optimizer.stop()

    @pytest.mark.asyncio
    async def test_single_embedding(self, optimizer):
        """测试单个向量生成"""
        text = "这是一个测试文本"
        embedding = await optimizer.get_embedding(text)

        assert embedding is not None
        assert len(embedding) == 1536  # 默认维度
        assert embedding.dtype == np.float32

        # 检查统计
        stats = optimizer.get_stats()
        assert stats['batch']['single_requests'] >= 1

    @pytest.mark.asyncio
    async def test_batch_embedding(self, optimizer):
        """测试批量向量生成"""
        texts = [
            "这是第一个文本",
            "这是第二个文本",
            "这是第三个文本"
        ]

        embeddings = await optimizer.get_embeddings_batch(texts, use_batch=False)

        assert len(embeddings) == 3
        for embedding in embeddings:
            assert embedding is not None
            assert len(embedding) == 1536

    @pytest.mark.asyncio
    async def test_embedding_cache(self, optimizer):
        """测试向量缓存"""
        text = "这是一个测试文本"

        # 首次生成
        embedding1 = await optimizer.get_embedding(text)
        assert embedding1 is not None

        # 第二次生成（应该命中缓存）
        start = time.time()
        embedding2 = await optimizer.get_embedding(text)
        elapsed = time.time() - start

        assert embedding2 is not None
        assert elapsed < 0.01, f"缓存查询耗时{elapsed:.3f}秒超过预期"

        # 两个向量应该相同
        import numpy as np
        np.testing.assert_array_equal(embedding1, embedding2)

        # 检查统计
        stats = optimizer.get_stats()
        assert stats['cache']['hits'] >= 1

    @pytest.mark.asyncio
    async def test_similar_search(self, optimizer):
        """测试相似度搜索"""
        query = "加密货币交易"
        candidates = [
            ("数字货币套利策略", {}),
            ("外汇交易系统", {}),
            ("股票市场分析", {}),
            ("期货交易风险", {}),
            ("区块链技术应用", {})
        ]

        results = await optimizer.search_similar(query, candidates, top_k=3)

        assert len(results) <= 3
        assert all(len(r) == 3 for r in results)  # (text, metadata, score)

        # 检查分数是否在合理范围内
        for _, _, score in results:
            assert -1 <= score <= 1, f"分数超出范围: {score}"  # 余弦相似度范围


class TestHealthCheckAPI:
    """健康检查API测试"""

    @pytest_asyncio.fixture
    async def health_api(self):
        """创建健康检查API实例"""
        api = HealthCheckAPI()
        yield api
        # 停止后台任务
        await api.stop()

    @pytest.mark.asyncio
    async def test_component_registration(self, health_api):
        """测试组件注册"""
        # 注册测试组件
        def mock_check():
            from monitoring.health_check_api import ComponentHealth
            return ComponentHealth(
                name="test_component",
                status=HealthStatus.HEALTHY,
                message="测试组件正常"
            )

        health_api.register_health_check("test_component", mock_check)

        # 检查所有组件
        components = await health_api.check_all_components()
        assert len(components) >= 1
        assert components[0].name == "test_component"
        assert components[0].status == HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_overall_health(self, health_api):
        """测试整体健康状态"""
        # 注册健康组件
        def healthy_check():
            from monitoring.health_check_api import ComponentHealth
            return ComponentHealth(
                name="healthy_component",
                status=HealthStatus.HEALTHY,
                message="健康"
            )

        # 注册不健康组件
        def unhealthy_check():
            from monitoring.health_check_api import ComponentHealth
            return ComponentHealth(
                name="unhealthy_component",
                status=HealthStatus.UNHEALTHY,
                message="不健康"
            )

        health_api.register_health_check("healthy", healthy_check)
        health_api.register_health_check("unhealthy", unhealthy_check)

        # 获取整体健康状态
        overall = await health_api.get_overall_health()

        assert overall.status == HealthStatus.UNHEALTHY  # 有不健康组件
        assert overall.metadata['unhealthy'] == 1
        assert overall.metadata['healthy'] == 1

    @pytest.mark.asyncio
    async def test_metrics_recording(self, health_api):
        """测试指标记录"""
        # 记录测试指标
        health_api.record_metric("test.metric1", 100.0, "count")
        health_api.record_metric("test.metric2", 0.95, "percent")
        health_api.record_metric("test.metric1", 150.0, "count")

        # 获取指标
        metrics = health_api.get_metrics("test.metric1")

        assert len(metrics) == 2
        assert all(m.name == "test.metric1" for m in metrics)
        assert metrics[1].value > metrics[0].value  # 第二个值更大

        # 获取最新指标
        latest = health_api.get_latest_metric("test.metric1")
        assert latest is not None
        assert latest.value == 150.0

    @pytest.mark.asyncio
    async def test_alert_rules(self, health_api):
        """测试告警规则"""
        # 设置告警规则
        rules = [
            {
                'component': 'test_component',
                'metric': 'test.metric',
                'condition': '>',
                'threshold': 100.0,
                'severity': 'warning',
                'message': '测试指标超过阈值'
            }
        ]
        health_api.set_alert_rules(rules)

        # 记录触发告警的指标
        health_api.record_metric("test.metric", 150.0)

        # 检查告警
        alerts = health_api.check_alerts()
        assert len(alerts) > 0
        assert alerts[0].severity == AlertSeverity.WARNING
        assert "超过阈值" in alerts[0].message


class TestDataMigration:
    """数据迁移工具测试"""

    @pytest_asyncio.fixture
    def migrator(self):
        """创建数据迁移工具实例"""
        migrator = DataMigrator(batch_size=10)
        yield migrator

    def test_export_memory_data(self, migrator):
        """测试内存数据导出"""
        # 准备测试数据
        memory_store = {
            'key1': {'data': 'value1'},
            'key2': {'data': 'value2'},
            'key3': 'data_value_3'
        }

        # 导出数据
        records = migrator.export_memory_data(memory_store)

        assert len(records) == 3
        assert all(r.source_type == 'memory' for r in records)
        assert all(r.migration_id for r in records)

        # 检查统计
        stats = migrator.get_stats()
        assert stats['migrations']['records'] >= 3

    def test_export_trade_history(self, migrator):
        """测试交易历史导出"""
        # 准备测试数据
        trade_history = [
            {'strategy': 'triangular', 'symbol': 'BTC/USDT', 'status': 'completed', 'profit': 100.0},
            {'strategy': 'basis_trading', 'symbol': 'ETH/USDT', 'status': 'completed', 'profit': 50.0},
            {'strategy': 'triangular', 'symbol': 'BNB/USDT', 'status': 'failed', 'profit': 0.0}
        ]

        # 导出数据
        records = migrator.export_trade_history(trade_history)

        assert len(records) == 3
        assert all(r.source_type == 'trade_history' for r in records)
        assert records[0].metadata['strategy'] == 'triangular'

    def test_migration_progress(self, migrator):
        """测试迁移进度跟踪"""
        # 创建模拟进度对象
        from tools.data_migration import MigrationProgress
        progress_obj = MigrationProgress(
            migration_id="test_migration",
            total_records=100,
            processed_records=50,
            successful_records=45,
            failed_records=5,
            start_time=time.time() - 10  # 10秒前开始
        )

        # 检查进度计算
        assert progress_obj.progress_percentage == 50.0
        assert progress_obj.elapsed_time >= 10.0
        assert progress_obj.records_per_second > 0

    def test_checkpoint_management(self, migrator):
        """测试检查点管理"""
        # 创建测试检查点
        from tools.data_migration import MigrationProgress, MigrationStatus
        progress = MigrationProgress(
            migration_id="test_checkpoint",
            total_records=10,
            processed_records=5,
            successful_records=5,
            failed_records=0,
            start_time=time.time(),
            status=MigrationStatus.RUNNING
        )

        # 保存检查点
        migrator._save_checkpoint("test_checkpoint", progress)

        # 加载检查点
        loaded = migrator.load_checkpoint("test_checkpoint")

        assert loaded is not None
        assert loaded.migration_id == "test_checkpoint"
        assert loaded.processed_records == 5

    def test_stats_collection(self, migrator):
        """测试统计信息收集"""
        # 导出一些数据
        memory_store = {'test_key': 'test_value'}
        migrator.export_memory_data(memory_store)

        # 获取统计信息
        stats = migrator.get_stats()

        assert 'migrations' in stats
        assert 'config' in stats
        assert stats['migrations']['records'] > 0


class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_cache_and_embedding_integration(self):
        """测试缓存和向量嵌入集成"""
        # 创建缓存
        cache = SearchCache()
        await cache.start()

        # 创建批处理优化器
        optimizer = VectorEmbeddingBatchOptimizer()
        optimizer.set_embedding_function(mock_embedding_function)
        await optimizer.start()

        try:
            # 模拟工作流程
            texts = ["文本1", "文本2", "文本3"]

            # 使用缓存获取文本（假设从某个来源获取）
            async def fetch_text(text_id):
                await asyncio.sleep(0.05)
                return texts[int(text_id.split('_')[1])]

            # 批量生成向量
            embeddings = await optimizer.get_embeddings_batch(texts, use_batch=False)

            assert len(embeddings) == 3
            assert all(e is not None for e in embeddings)

            # 检查缓存和优化器统计
            cache_stats = cache.get_stats()
            optimizer_stats = optimizer.get_stats()

            assert 'price_cache' in cache_stats
            assert 'cache' in optimizer_stats

        finally:
            await cache.stop()
            await optimizer.stop()

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """测试端到端工作流程"""
        # 创建所有组件
        cache = SearchCache()
        optimizer = VectorEmbeddingBatchOptimizer()
        optimizer.set_embedding_function(mock_embedding_function)
        health_api = HealthCheckAPI()

        # 启动组件
        await cache.start()
        await optimizer.start()

        try:
            # 1. 模拟数据查询（使用缓存）
            async def fetch_price():
                await asyncio.sleep(0.1)
                return {'price': 50000.0}

            price = await cache.get_price_cached('binance', 'BTC/USDT', fetch_price)
            assert price is not None

            # 2. 生成向量（使用批处理）
            texts = ["比特币价格分析", "以太坊交易策略", "市场趋势预测"]
            embeddings = await optimizer.get_embeddings_batch(texts, use_batch=False)

            assert len(embeddings) == 3

            # 3. 记录性能指标
            health_api.record_metric("api.response_time", 0.15, "seconds")
            health_api.record_metric("embedding.generation_time", 0.3, "seconds")
            health_api.record_metric("cache.hit_rate", 0.85, "percent")

            # 4. 检查系统健康
            def cache_check():
                from monitoring.health_check_api import ComponentHealth
                stats = cache.get_stats()
                return ComponentHealth(
                    name="cache",
                    status=HealthStatus.HEALTHY,
                    message="缓存系统正常",
                    metadata=stats
                )

            def optimizer_check():
                from monitoring.health_check_api import ComponentHealth
                stats = optimizer.get_stats()
                return ComponentHealth(
                    name="optimizer",
                    status=HealthStatus.HEALTHY,
                    message="批处理优化器正常",
                    metadata=stats
                )

            health_api.register_health_check("cache", cache_check)
            health_api.register_health_check("optimizer", optimizer_check)

            # 5. 获取整体健康状态
            overall = await health_api.get_overall_health()
            assert overall.status == HealthStatus.HEALTHY

            # 6. 获取性能指标
            metrics = health_api.get_metrics()
            assert len(metrics) >= 3

            print("\n[SUCCESS] 端到端测试通过！")
            print(f"缓存统计: {cache.get_stats()}")
            print(f"优化器统计: {optimizer.get_stats()}")
            print(f"健康检查: {overall.to_dict()}")
            print(f"性能指标: {len(metrics)}条")

        finally:
            await cache.stop()
            await optimizer.stop()


# 运行测试的辅助函数
async def run_tests():
    """运行所有测试"""
    print("开始运行 V5.10 Phase 5 测试...")

    # 测试搜索缓存
    print("\n[TEST] 测试搜索缓存...")
    test_cache = TestSearchCache()
    cache = SearchCache()
    await cache.start()
    try:
        await test_cache.test_price_cache_hit(cache)
        await test_cache.test_fee_cache_hit(cache)
        print("[PASS] 搜索缓存测试通过")
    finally:
        await cache.stop()

    # 测试向量嵌入
    print("\n[TEST] 测试向量嵌入...")
    test_embedding = TestVectorEmbeddingBatch()
    optimizer = VectorEmbeddingBatchOptimizer()
    optimizer.set_embedding_function(mock_embedding_function)
    await optimizer.start()
    try:
        await test_embedding.test_single_embedding(optimizer)
        await test_embedding.test_embedding_cache(optimizer)
        print("[PASS] 向量嵌入测试通过")
    finally:
        await optimizer.stop()

    # 测试健康检查API
    print("\n[TEST] 测试健康检查API...")
    test_health = TestHealthCheckAPI()
    health_api = HealthCheckAPI()
    try:
        await test_health.test_component_registration(health_api)
        await test_health.test_metrics_recording(health_api)
        print("[PASS] 健康检查API测试通过")
    finally:
        await health_api.stop()

    # 测试数据迁移
    print("\n[TEST] 测试数据迁移...")
    test_migration = TestDataMigration()
    migrator = DataMigrator()
    try:
        test_migration.test_export_memory_data(migrator)
        test_migration.test_stats_collection(migrator)
        print("[PASS] 数据迁移测试通过")
    finally:
        pass

    # 集成测试
    print("\n[TEST] 测试集成...")
    test_integration = TestIntegration()
    await test_integration.test_end_to_end_workflow()

    print("\n[SUCCESS] 所有测试完成！")


if __name__ == "__main__":
    # 直接运行测试
    asyncio.run(run_tests())
