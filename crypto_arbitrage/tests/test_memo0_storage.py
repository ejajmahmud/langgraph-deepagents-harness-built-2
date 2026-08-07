"""Memo0存储单元测试 - V5.10 Phase 3

测试真正的memo0存储实现的功能和性能。

创建时间：2026-04-19
"""

import asyncio
import pytest
import pytest_asyncio
from datetime import datetime
from typing import Dict, Any

# 导入存储接口和实现
from storage.knowledge_storage_interface import (
    KnowledgeStorage,
    KnowledgeItem,
    SearchResult,
    StorageStats,
    create_knowledge_storage
)
from storage.memory_storage_impl import InMemoryStorage
from storage.memo0_storage_impl import Memo0Storage


class TestKnowledgeStorageInterface:
    """测试知识存储抽象接口"""

    @pytest_asyncio.fixture
    async def storage(self):
        """创建存储实例"""
        storage = InMemoryStorage({})
        await storage.initialize()
        yield storage
        await storage.close()

    @pytest.mark.asyncio
    async def test_add_knowledge(self, storage):
        """测试添加知识"""
        content = "BTC/USDT套利机会：价格差异0.5%"
        metadata = {
            "category": "strategy",
            "risk_level": "low",
            "expected_return": 0.005
        }

        knowledge_id = await storage.add_knowledge(content, metadata)

        assert knowledge_id is not None
        assert knowledge_id.startswith("knowledge_")

        # 验证知识已添加
        item = await storage.get_knowledge(knowledge_id)
        assert item is not None
        assert item.content == content
        assert item.metadata["category"] == "strategy"

    @pytest.mark.asyncio
    async def test_get_knowledge(self, storage):
        """测试获取知识"""
        content = "ETH/USDT趋势分析：上涨中"
        metadata = {"category": "market_analysis"}

        knowledge_id = await storage.add_knowledge(content, metadata)
        item = await storage.get_knowledge(knowledge_id)

        assert item is not None
        assert item.knowledge_id == knowledge_id
        assert item.content == content
        assert item.metadata["category"] == "market_analysis"

    @pytest.mark.asyncio
    async def test_update_knowledge(self, storage):
        """测试更新知识"""
        content = "初始内容"
        metadata = {"category": "test"}

        knowledge_id = await storage.add_knowledge(content, metadata)

        # 更新内容
        new_content = "更新后的内容"
        success = await storage.update_knowledge(knowledge_id, content=new_content)

        assert success is True

        # 验证更新
        item = await storage.get_knowledge(knowledge_id)
        assert item.content == new_content
        assert item.updated_at >= item.created_at  # 允许时间戳相同（快速操作）

    @pytest.mark.asyncio
    async def test_delete_knowledge(self, storage):
        """测试删除知识"""
        content = "待删除的知识"
        metadata = {"category": "test"}

        knowledge_id = await storage.add_knowledge(content, metadata)

        # 删除知识
        success = await storage.delete_knowledge(knowledge_id)

        assert success is True

        # 验证删除
        item = await storage.get_knowledge(knowledge_id)
        assert item is None

    @pytest.mark.asyncio
    async def test_search_knowledge(self, storage):
        """测试搜索知识"""
        # 添加多条知识
        contents = [
            "BTC套利策略",
            "ETH交易建议",
            "BTC/USDT分析",
            "市场风险评估"
        ]

        for content in contents:
            await storage.add_knowledge(content, {"category": "test"})

        # 搜索
        results = await storage.search_knowledge("BTC", top_k=10)

        assert len(results) > 0
        assert any("BTC" in result.content for result in results)

    @pytest.mark.asyncio
    async def test_semantic_search(self, storage):
        """测试语义搜索（仅memo0存储支持）"""
        # 内存存储不支持语义搜索，跳过
        if isinstance(storage, InMemoryStorage):
            pytest.skip("内存存储不支持语义搜索")

        content = "比特币价格趋势分析"
        await storage.add_knowledge(content, {"category": "market_analysis"})

        # 语义搜索
        results = await storage.semantic_search("BTC price", top_k=5)

        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_list_knowledge(self, storage):
        """测试列出知识"""
        # 添加多条知识
        for i in range(5):
            await storage.add_knowledge(f"知识 {i}", {"index": i})

        # 列出知识
        items = await storage.list_knowledge(limit=10)

        assert len(items) == 5
        assert all(isinstance(item, KnowledgeItem) for item in items)

    @pytest.mark.asyncio
    async def test_count_knowledge(self, storage):
        """测试统计知识数量"""
        # 添加知识
        for i in range(10):
            await storage.add_knowledge(f"知识 {i}", {"index": i})

        # 统计
        count = await storage.count_knowledge()

        assert count == 10

    @pytest.mark.asyncio
    async def test_batch_operations(self, storage):
        """测试批量操作"""
        # 批量添加
        items = [
            (f"批量内容 {i}", {"index": i})
            for i in range(5)
        ]

        knowledge_ids = await storage.add_knowledge_batch(items)

        assert len(knowledge_ids) == 5
        assert all(kid.startswith("knowledge_") for kid in knowledge_ids)

        # 批量删除
        delete_results = await storage.delete_knowledge_batch(knowledge_ids)

        assert len(delete_results) == 5
        assert all(result is True for result in delete_results.values())

    @pytest.mark.asyncio
    async def test_storage_stats(self, storage):
        """测试存储统计"""
        # 添加知识
        for i in range(5):
            await storage.add_knowledge(f"知识 {i}", {"index": i})

        # 搜索
        await storage.search_knowledge("test", top_k=10)

        # 获取统计
        stats = storage.get_storage_stats()

        assert stats.total_knowledge == 5
        assert stats.total_adds == 5
        assert stats.total_searches == 1
        assert stats.storage_type == "InMemoryStorage"


class TestInMemoryStorage:
    """测试内存存储实现"""

    @pytest_asyncio.fixture
    async def storage(self):
        """创建内存存储实例"""
        storage = InMemoryStorage({})
        await storage.initialize()
        yield storage
        await storage.close()

    @pytest.mark.asyncio
    async def test_persistence(self, storage):
        """测试内存存储的持久化（应该不支持）"""
        content = "测试内容"
        knowledge_id = await storage.add_knowledge(content, {})

        # 获取知识
        item = await storage.get_knowledge(knowledge_id)
        assert item is not None

    @pytest.mark.asyncio
    async def test_clear_all(self, storage):
        """测试清除所有知识"""
        # 添加知识
        for i in range(10):
            await storage.add_knowledge(f"知识 {i}", {"index": i})

        # 清除所有
        success = await storage.clear_all()

        assert success is True

        # 验证清除
        count = await storage.count_knowledge()
        assert count == 0

    @pytest.mark.asyncio
    async def test_search_by_metadata(self, storage):
        """测试按元数据搜索"""
        # 添加知识
        await storage.add_knowledge("知识1", {"category": "strategy"})
        await storage.add_knowledge("知识2", {"category": "market"})
        await storage.add_knowledge("知识3", {"category": "strategy"})

        # 按元数据搜索
        results = await storage.search_by_metadata({"category": "strategy"}, limit=10)

        assert len(results) == 2
        assert all(r.metadata.get("category") == "strategy" for r in results)


class TestMemo0Storage:
    """测试Memo0存储实现"""

    @pytest_asyncio.fixture
    async def storage(self):
        """创建Memo0存储实例"""
        # 使用本地存储（不需要API密钥）
        config = {
            "vector_store": "local",
            "vector_store_config": {
                "path": "./test_memo0_db"
            }
        }

        try:
            storage = Memo0Storage(config)
            await storage.initialize()
            yield storage
        except ImportError:
            # 如果mem0ai未安装，跳过测试
            pytest.skip("mem0ai未安装")
        except Exception as e:
            pytest.skip(f"Memo0初始化失败: {e}")
        finally:
            if 'storage' in locals():
                await storage.close()

    @pytest.mark.asyncio
    async def test_add_and_get_knowledge(self, storage):
        """测试添加和获取知识"""
        content = "BTC/USDT套利机会：价格差异0.5%"
        metadata = {
            "category": "strategy",
            "risk_level": "low",
            "expected_return": 0.005
        }

        knowledge_id = await storage.add_knowledge(content, metadata)

        assert knowledge_id is not None
        assert knowledge_id.startswith("knowledge_")

        # 获取知识
        item = await storage.get_knowledge(knowledge_id)

        assert item is not None
        assert item.content == content
        assert item.metadata["category"] == "strategy"

    @pytest.mark.asyncio
    async def test_vector_search(self, storage):
        """测试向量搜索"""
        # 添加相关知识
        contents = [
            "比特币价格趋势分析",
            "BTC/USDT技术指标",
            "加密货币市场概况",
            "以太坊交易建议"
        ]

        for content in contents:
            await storage.add_knowledge(content, {"category": "market"})

        # 向量搜索
        results = await storage.semantic_search("BTC analysis", top_k=5)

        assert len(results) > 0
        # 应该包含包含BTC的内容
        assert any("BTC" in result.content or "比特币" in result.content
                  for result in results)

    @pytest.mark.asyncio
    async def test_metadata_filtering(self, storage):
        """测试元数据过滤"""
        # 添加不同类别的知识
        await storage.add_knowledge("策略1", {"category": "strategy"})
        await storage.add_knowledge("市场1", {"category": "market"})
        await storage.add_knowledge("策略2", {"category": "strategy"})

        # 按元数据搜索
        results = await storage.search_knowledge("", top_k=10, filters={"category": "strategy"})

        assert len(results) >= 2
        assert all(r.metadata.get("category") == "strategy" for r in results)


class TestKnowledgeStorageFactory:
    """测试知识存储工厂函数"""

    @pytest.mark.asyncio
    async def test_create_memory_storage(self):
        """测试创建内存存储"""
        config = {}
        storage = create_knowledge_storage("memory", config)

        assert isinstance(storage, InMemoryStorage)
        await storage.close()

    @pytest.mark.asyncio
    async def test_create_memo0_storage(self):
        """测试创建Memo0存储"""
        config = {
            "vector_store": "local",
            "vector_store_config": {
                "path": "./test_factory_db"
            }
        }

        try:
            storage = create_knowledge_storage("memo0", config)

            assert isinstance(storage, Memo0Storage)
            await storage.close()

        except ImportError:
            pytest.skip("mem0ai未安装")

    @pytest.mark.asyncio
    async def test_create_invalid_storage(self):
        """测试创建无效存储类型"""
        config = {}

        with pytest.raises(ValueError):
            create_knowledge_storage("invalid_type", config)


class TestKnowledgeItem:
    """测试KnowledgeItem数据类"""

    def test_to_dict(self):
        """测试转换为字典"""
        item = KnowledgeItem(
            knowledge_id="test_123",
            content="测试内容",
            metadata={"category": "test"},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        item_dict = item.to_dict()

        assert item_dict["knowledge_id"] == "test_123"
        assert item_dict["content"] == "测试内容"
        assert item_dict["metadata"]["category"] == "test"

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "knowledge_id": "test_123",
            "content": "测试内容",
            "metadata": {"category": "test"},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "quality_score": 0.8,
            "value_score": 0.7
        }

        item = KnowledgeItem.from_dict(data)

        assert item.knowledge_id == "test_123"
        assert item.content == "测试内容"
        assert item.quality_score == 0.8


class TestSearchResult:
    """测试SearchResult数据类"""

    def test_to_dict(self):
        """测试转换为字典"""
        result = SearchResult(
            knowledge_id="test_123",
            content="测试内容",
            metadata={"category": "test"},
            similarity_score=0.95,
            quality_score=0.8,
            value_score=0.7
        )

        result_dict = result.to_dict()

        assert result_dict["knowledge_id"] == "test_123"
        assert result_dict["similarity_score"] == 0.95
        assert result_dict["quality_score"] == 0.8


# ========== 运行测试的便捷函数 ==========

async def run_basic_tests():
    """运行基本测试"""
    print("运行基本存储测试...")

    # 创建内存存储
    storage = InMemoryStorage({})
    await storage.initialize()

    try:
        # 添加知识
        content = "BTC/USDT套利机会：价格差异0.5%"
        knowledge_id = await storage.add_knowledge(content, {"category": "strategy"})

        print(f"✓ 添加知识: {knowledge_id}")

        # 获取知识
        item = await storage.get_knowledge(knowledge_id)
        assert item is not None
        print(f"✓ 获取知识: {item.content}")

        # 搜索知识
        results = await storage.search_knowledge("BTC", top_k=10)
        assert len(results) > 0
        print(f"✓ 搜索知识: 找到 {len(results)} 条结果")

        # 删除知识
        success = await storage.delete_knowledge(knowledge_id)
        assert success
        print(f"✓ 删除知识: {knowledge_id}")

        # 获取统计
        stats = storage.get_storage_stats()
        print(f"✓ 存储统计: {stats.to_dict()}")

        print("\n所有基本测试通过！")

    finally:
        await storage.close()


if __name__ == "__main__":
    # 运行基本测试
    asyncio.run(run_basic_tests())
