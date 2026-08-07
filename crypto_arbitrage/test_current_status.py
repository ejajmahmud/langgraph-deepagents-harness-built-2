"""快速测试当前系统状态"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from storage.storage_factory import StorageFactory
from storage.memo0_storage_impl import Memo0Storage
from storage.knowledge_storage_interface import KnowledgeStorage


async def test_storage_status():
    """测试存储系统状态"""
    print("=== 数字货币交易系统状态检查 ===\n")

    try:
        # 测试存储工厂
        print("1. Testing storage factory...")
        factory = StorageFactory()
        storage = await factory.create_storage()
        print(f"   [OK] Storage factory works normally")
        print(f"   [INFO] Storage type: {type(storage).__name__}")

        # 测试基本操作
        print("\n2. Testing basic storage operations...")
        test_id = await storage.add_knowledge(
            content="Test knowledge entry - crypto arbitrage system status check",
            metadata={
                "category": "system_test",
                "timestamp": "2026-04-20T10:58:00",
                "test": True
            }
        )
        print(f"   [OK] Add knowledge success: {test_id}")

        # 测试搜索
        results = await storage.search_knowledge(
            query="crypto arbitrage",
            top_k=5
        )
        print(f"   [OK] Search knowledge success: found {len(results)} results")

        # 获取统计信息
        stats = storage.get_storage_stats()
        print(f"   [STATS] Storage statistics:")
        print(f"      - Total knowledge: {stats.total_knowledge}")
        print(f"      - Search count: {stats.total_searches}")
        print(f"      - Add count: {stats.total_adds}")

        # 测试接口兼容性
        print("\n3. Checking interface compatibility...")
        storage_methods = dir(storage)
        has_add = 'add_knowledge' in storage_methods
        has_search = 'search_knowledge' in storage_methods
        has_add_simple = 'add' in storage_methods
        has_search_simple = 'search' in storage_methods

        print(f"   [OK] add_knowledge: {has_add}")
        print(f"   [OK] search_knowledge: {has_search}")
        print(f"   [WARN] add: {has_add_simple}")
        print(f"   [WARN] search: {has_search_simple}")

        if has_add_simple or has_search_simple:
            print("\n   [WARN] Interface compatibility issues found:")
            if has_add_simple:
                print("      - Storage provides both add() and add_knowledge() methods")
            if has_search_simple:
                print("      - Storage provides both search() and search_knowledge() methods")

        await storage.close()

        print("\n=== System status check completed ===")
        print("[OK] Storage system works normally")
        print("[WARN] Need to fix interface compatibility issues")

        return True

    except Exception as e:
        print(f"\n[ERROR] System status check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_storage_status())
    sys.exit(0 if success else 1)