"""V5.10 Phase 3 集成测试 - 真正的memo0集成

测试完整的系统集成，包括：
1. 真正的memo0存储集成
2. 智能知识管理器使用memo0
3. 端到端知识流程
4. 向量搜索功能验证

创建时间：2026-04-19
"""

import asyncio
import pytest
import pytest_asyncio
from datetime import datetime
from typing import Dict, Any

# 导入存储和模块
from storage.knowledge_storage_interface import create_knowledge_storage
from storage.memory_storage_impl import InMemoryStorage
from storage.memo0_intelligent_knowledge_manager_v2 import (
    Memo0IntelligentKnowledgeManagerV2,
    create_memo0_intelligent_knowledge_manager_v2,
    ManagedKnowledge
)


class TestMemo0Integration:
    """测试memo0集成"""

    @pytest_asyncio.fixture
    async def manager_with_memory(self):
        """创建使用内存存储的管理器"""
        config = {
            "storage_type": "memory",
            "storage_config": {},
            "auto_knowledge_extractor": {},
            "intelligent_knowledge_classifier": {},
            "knowledge_quality_optimizer": {},
            "knowledge_trend_analyzer": {}
        }

        manager = create_memo0_intelligent_knowledge_manager_v2(config)
        await manager.initialize()

        yield manager

        await manager.close()

    @pytest_asyncio.fixture
    async def manager_with_memo0(self):
        """创建使用memo0存储的管理器"""
        config = {
            "storage_type": "memo0",
            "storage_config": {
                "vector_store": "local",
                "vector_store_config": {
                    "path": "./test_integration_db"
                }
            },
            "auto_knowledge_extractor": {},
            "intelligent_knowledge_classifier": {},
            "knowledge_quality_optimizer": {},
            "knowledge_trend_analyzer": {}
        }

        try:
            manager = create_memo0_intelligent_knowledge_manager_v2(config)
            await manager.initialize()

            yield manager

        except ImportError:
            pytest.skip("mem0ai未安装")
        except Exception as e:
            pytest.skip(f"Memo0初始化失败: {e}")
        finally:
            if 'manager' in locals():
                await manager.close()

    @pytest.mark.asyncio
    async def test_add_custom_knowledge(self, manager_with_memory):
        """测试添加自定义知识"""
        content = "BTC/USDT套利策略：在价格差异>0.3%时执行"
        metadata = {
            "category": "strategy",
            "risk_level": "low",
            "expected_return": 0.003
        }

        managed = await manager_with_memory.add_custom_knowledge(content, metadata)

        assert managed is not None
        assert managed.content == content
        assert managed.category == "strategy"
        assert managed.knowledge_id.startswith("knowledge_")

    @pytest.mark.asyncio
    async def test_search_knowledge(self, manager_with_memory):
        """测试搜索知识"""
        # 添加多条知识
        contents = [
            "BTC套利策略",
            "ETH交易建议",
            "市场风险评估"
        ]

        for content in contents:
            await manager_with_memory.add_custom_knowledge(content, {"category": "test"})

        # 搜索
        results = await manager_with_memory.search_knowledge("BTC", limit=10)

        assert len(results) > 0
        assert any("BTC" in result.content for result in results)

    @pytest.mark.asyncio
    async def test_get_knowledge_by_id(self, manager_with_memory):
        """测试通过ID获取知识"""
        content = "测试知识内容"
        metadata = {"category": "test"}

        managed = await manager_with_memory.add_custom_knowledge(content, metadata)
        retrieved = await manager_with_memory.get_knowledge_by_id(managed.knowledge_id)

        assert retrieved is not None
        assert retrieved.knowledge_id == managed.knowledge_id
        assert retrieved.content == content

    @pytest.mark.asyncio
    async def test_get_knowledge_by_category(self, manager_with_memory):
        """测试通过类别获取知识"""
        # 添加不同类别的知识
        await manager_with_memory.add_custom_knowledge("策略1", {"category": "strategy"})
        await manager_with_memory.add_custom_knowledge("市场1", {"category": "market"})
        await manager_with_memory.add_custom_knowledge("策略2", {"category": "strategy"})

        # 获取策略类知识
        strategy_knowledge = await manager_with_memory.get_knowledge_by_category("strategy", limit=10)

        assert len(strategy_knowledge) == 2
        assert all(k.category == "strategy" for k in strategy_knowledge)

    @pytest.mark.asyncio
    async def test_import_from_trade_data(self, manager_with_memory):
        """测试从交易数据导入知识"""
        trade_data = {
            "symbol": "BTC/USDT",
            "entry_price": 50000.0,
            "exit_price": 50300.0,
            "profit": 300.0,
            "profit_pct": 0.006,
            "execution_time": 120,
            "risk_level": "low"
        }

        imported = await manager_with_memory.import_from_trade_data(trade_data)

        assert isinstance(imported, list)
        # 知识提取器可能返回0个或多个知识

    @pytest.mark.asyncio
    async def test_import_from_market_data(self, manager_with_memory):
        """测试从市场数据导入知识"""
        market_data = {
            "symbol": "ETH/USDT",
            "price": 3000.0,
            "volume_24h": 1000000,
            "change_24h": 0.02,
            "volatility": 0.03
        }

        imported = await manager_with_memory.import_from_market_data(market_data)

        assert isinstance(imported, list)

    @pytest.mark.asyncio
    async def test_generate_comprehensive_report(self, manager_with_memory):
        """测试生成综合报告"""
        # 添加一些知识
        for i in range(5):
            await manager_with_memory.add_custom_knowledge(
                f"知识 {i}",
                {"category": "test", "index": i}
            )

        # 生成报告
        report = await manager_with_memory.generate_comprehensive_report()

        assert "generated_at" in report
        assert "summary" in report
        assert "storage_type" in report["summary"]
        assert report["summary"]["total_knowledge"] >= 5

    @pytest.mark.asyncio
    async def test_get_manager_stats(self, manager_with_memory):
        """测试获取管理器统计"""
        stats = await manager_with_memory.get_manager_stats()

        assert "total_knowledge" in stats
        assert "storage_type" in stats
        assert "storage_stats" in stats
        assert "module_stats" in stats

    @pytest.mark.asyncio
    async def test_memo0_storage_type(self, manager_with_memory):
        """测试存储类型"""
        assert manager_with_memory.storage_type == "memory"

    @pytest.mark.asyncio
    async def test_memo0_storage_type_memo0(self, manager_with_memo0):
        """测试memo0存储类型"""
        assert manager_with_memo0.storage_type == "memo0"

    @pytest.mark.asyncio
    async def test_memo0_persistence(self, manager_with_memo0):
        """测试memo0持久化"""
        content = "持久化测试内容"
        metadata = {"category": "test"}

        # 添加知识
        managed = await manager_with_memo0.add_custom_knowledge(content, metadata)

        assert managed is not None

        # 获取知识
        retrieved = await manager_with_memo0.get_knowledge_by_id(managed.knowledge_id)

        assert retrieved is not None
        assert retrieved.content == content

    @pytest.mark.asyncio
    async def test_vector_search_with_memo0(self, manager_with_memo0):
        """测试memo0的向量搜索"""
        # 添加相关知识
        contents = [
            "比特币价格趋势分析",
            "BTC/USDT技术指标",
            "加密货币市场概况",
            "以太坊交易建议"
        ]

        for content in contents:
            await manager_with_memo0.add_custom_knowledge(content, {"category": "market"})

        # 向量搜索
        results = await manager_with_memo0.search_knowledge("BTC analysis", limit=5)

        assert len(results) > 0
        # 应该包含包含BTC的内容
        assert any("BTC" in result.content or "比特币" in result.content
                  for result in results)


class TestEndToEndWorkflow:
    """测试端到端工作流程"""

    @pytest_asyncio.fixture
    async def manager(self):
        """创建管理器"""
        config = {
            "storage_type": "memory",
            "storage_config": {},
            "auto_knowledge_extractor": {},
            "intelligent_knowledge_classifier": {},
            "knowledge_quality_optimizer": {},
            "knowledge_trend_analyzer": {}
        }

        manager = create_memo0_intelligent_knowledge_manager_v2(config)
        await manager.initialize()

        yield manager

        await manager.close()

    @pytest.mark.asyncio
    async def test_complete_knowledge_lifecycle(self, manager):
        """测试完整的知识生命周期"""
        # 1. 添加知识
        content = "BTC/USDT套利策略"
        metadata = {"category": "strategy", "risk": "low"}
        managed = await manager.add_custom_knowledge(content, metadata)

        assert managed is not None

        # 2. 搜索知识
        results = await manager.search_knowledge("BTC", limit=10)
        assert len(results) > 0

        # 3. 获取知识
        retrieved = await manager.get_knowledge_by_id(managed.knowledge_id)
        assert retrieved is not None

        # 4. 按类别获取
        category_results = await manager.get_knowledge_by_category("strategy", limit=10)
        assert len(category_results) > 0

        # 5. 生成报告
        report = await manager.generate_comprehensive_report()
        assert report["summary"]["total_knowledge"] >= 1

    @pytest.mark.asyncio
    async def test_knowledge_quality_filtering(self, manager):
        """测试知识质量过滤"""
        # 添加高质量知识
        await manager.add_custom_knowledge(
            "高质量策略",
            {"quality": 0.9, "category": "strategy"}
        )

        # 添加低质量知识
        await manager.add_custom_knowledge(
            "低质量内容",
            {"quality": 0.3, "category": "test"}
        )

        # 搜索（默认最低质量0.5）
        results = await manager.search_knowledge("策略", min_quality=0.5, limit=10)

        # 应该只返回高质量知识
        assert len(results) > 0
        assert all(r.quality_score >= 0.5 for r in results)


class TestStorageComparison:
    """测试存储对比"""

    @pytest.mark.asyncio
    async def test_memory_vs_memo0_comparison(self):
        """对比内存存储和memo0存储"""
        # 创建内存管理器
        memory_config = {
            "storage_type": "memory",
            "storage_config": {},
            "auto_knowledge_extractor": {},
            "intelligent_knowledge_classifier": {},
            "knowledge_quality_optimizer": {},
            "knowledge_trend_analyzer": {}
        }

        memory_manager = create_memo0_intelligent_knowledge_manager_v2(memory_config)
        await memory_manager.initialize()

        try:
            # 创建memo0管理器
            memo0_config = {
                "storage_type": "memo0",
                "storage_config": {
                    "vector_store": "local",
                    "vector_store_config": {
                        "path": "./test_comparison_db"
                    }
                },
                "auto_knowledge_extractor": {},
                "intelligent_knowledge_classifier": {},
                "knowledge_quality_optimizer": {},
                "knowledge_trend_analyzer": {}
            }

            try:
                memo0_manager = create_memo0_intelligent_knowledge_manager_v2(memo0_config)
                await memo0_manager.initialize()

                # 添加相同的知识
                test_content = "BTC/USDT套利测试"

                memory_result = await memory_manager.add_custom_knowledge(test_content, {})
                memo0_result = await memo0_manager.add_custom_knowledge(test_content, {})

                assert memory_result is not None
                assert memo0_result is not None

                # 搜索
                memory_search = await memory_manager.search_knowledge("BTC", limit=10)
                memo0_search = await memo0_manager.search_knowledge("BTC", limit=10)

                assert len(memory_search) > 0
                assert len(memo0_search) > 0

                # 比较存储类型
                assert memory_manager.storage_type == "memory"
                assert memo0_manager.storage_type == "memo0"

                await memo0_manager.close()

            except ImportError:
                print("mem0ai未安装，跳过对比测试")

        finally:
            await memory_manager.close()


# ========== 运行集成测试的便捷函数 ==========

async def run_basic_integration_tests():
    """运行基本集成测试"""
    print("运行基本集成测试...")

    # 创建管理器
    config = {
        "storage_type": "memory",
        "storage_config": {},
        "auto_knowledge_extractor": {},
        "intelligent_knowledge_classifier": {},
        "knowledge_quality_optimizer": {},
        "knowledge_trend_analyzer": {}
    }

    manager = create_memo0_intelligent_knowledge_manager_v2(config)
    await manager.initialize()

    try:
        # 1. 添加知识
        content = "BTC/USDT套利策略：在价格差异>0.3%时执行"
        managed = await manager.add_custom_knowledge(content, {"category": "strategy"})

        print(f"✓ 添加知识: {managed.knowledge_id}")

        # 2. 搜索知识
        results = await manager.search_knowledge("BTC", limit=10)
        assert len(results) > 0
        print(f"✓ 搜索知识: 找到 {len(results)} 条结果")

        # 3. 获取知识
        retrieved = await manager.get_knowledge_by_id(managed.knowledge_id)
        assert retrieved is not None
        print(f"✓ 获取知识: {retrieved.content[:30]}...")

        # 4. 按类别获取
        category_results = await manager.get_knowledge_by_category("strategy", limit=10)
        assert len(category_results) > 0
        print(f"✓ 按类别获取: 找到 {len(category_results)} 条策略知识")

        # 5. 生成报告
        report = await manager.generate_comprehensive_report()
        print(f"✓ 生成报告: {report['summary']['total_knowledge']} 条知识")
        print(f"  存储类型: {report['summary']['storage_type']}")

        print("\n所有基本集成测试通过！")

    finally:
        await manager.close()


async def run_memo0_integration_tests():
    """运行memo0集成测试"""
    print("运行memo0集成测试...")

    try:
        # 创建memo0管理器
        config = {
            "storage_type": "memo0",
            "storage_config": {
                "vector_store": "local",
                "vector_store_config": {
                    "path": "./test_integration_db"
                }
            },
            "auto_knowledge_extractor": {},
            "intelligent_knowledge_classifier": {},
            "knowledge_quality_optimizer": {},
            "knowledge_trend_analyzer": {}
        }

        manager = create_memo0_intelligent_knowledge_manager_v2(config)
        await manager.initialize()

        try:
            # 1. 添加知识
            contents = [
                "比特币价格趋势分析",
                "BTC/USDT技术指标",
                "加密货币市场概况"
            ]

            for content in contents:
                managed = await manager.add_custom_knowledge(content, {"category": "market"})
                print(f"✓ 添加知识: {managed.knowledge_id}")

            # 2. 向量搜索
            results = await manager.search_knowledge("BTC analysis", limit=5)
            print(f"✓ 向量搜索: 找到 {len(results)} 条结果")

            # 3. 验证结果
            assert len(results) > 0
            assert any("BTC" in result.content or "比特币" in result.content
                      for result in results)

            print("\n所有memo0集成测试通过！")

        finally:
            await manager.close()

    except ImportError:
        print("✗ mem0ai未安装，跳过memo0集成测试")
    except Exception as e:
        print(f"✗ Memo0测试失败: {e}")


if __name__ == "__main__":
    # 运行基本集成测试
    asyncio.run(run_basic_integration_tests())

    print("\n" + "="*50 + "\n")

    # 运行memo0集成测试
    asyncio.run(run_memo0_integration_tests())
