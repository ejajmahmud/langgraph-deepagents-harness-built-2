"""Memo0 集成快速测试脚本

测试 Memo0 存储集成的基本功能。
"""

import sys
import os
import logging

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_unified_storage():
    """测试统一存储功能"""
    print("\n" + "="*80)
    print("测试 1: 统一存储功能")
    print("="*80)

    try:
        from storage.mem0_storage import get_unified_storage

        # 获取统一存储
        storage = get_unified_storage()

        print(f"存储类型: {'Memo0' if storage.is_using_mem0 else 'SQLite (本地存储)'}")

        # 测试添加知识
        test_knowledges = [
            ("strategy", "成功套利：BTC/USDT 跨交易所套利利润 $50.25"),
            ("risk", "市场波动率较高时，建议降低最大仓位"),
            ("insight", "三角套利在 ETH/BTC/USDT 路径上表现最佳"),
        ]

        print("\n添加测试知识:")
        knowledge_ids = []
        for category, content in test_knowledges:
            success = storage.add_knowledge(category, content)
            status = "[OK]" if success else "[FAIL]"
            print(f"  {status} [{category}] {content[:50]}...")
            if success:
                knowledge_ids.append(f"{category}_{len(knowledge_ids)}")

        # 测试搜索知识
        print("\n搜索知识 'BTC':")
        results = storage.search_knowledge("BTC", top_k=3)
        for i, result in enumerate(results, 1):
            content = result.get('content', '')
            print(f"  {i}. {content[:60]}...")

        # 测试获取所有知识
        print("\n获取所有知识:")
        all_knowledge = storage.get_all_knowledge()
        print(f"  总计: {len(all_knowledge)} 条知识")

        print("\n[OK] 统一存储测试通过")
        return True

    except Exception as e:
        print(f"\n[FAIL] 统一存储测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_knowledge_manager_with_mem0():
    """测试知识管理器与 Memo0 集成"""
    print("\n" + "="*80)
    print("测试 2: 知识管理器与 Memo0 集成")
    print("="*80)

    try:
        from tools.knowledge_manager_v3 import IntelligentKnowledgeManager
        from storage.mem0_storage import get_unified_storage

        # 获取统一存储
        storage = get_unified_storage()

        # 创建知识管理器
        km = IntelligentKnowledgeManager(
            storage_backend=storage,
            config={
                "cache_ttl": 300,
                "auto_extract": True,
                "auto_classify": True
            }
        )

        print(f"知识管理器初始化成功，存储类型: {'Memo0' if storage.is_using_mem0 else 'SQLite'}")

        # 测试添加知识
        test_knowledges = [
            "成功套利：ETH/USDT 三角套利利润 $12.50，利润率 0.65%",
            "风险提示：在单边行情中，三角套利风险显著增加",
            "执行优化：网络延迟超过 500ms 时，建议减少套利频率",
        ]

        print("\n通过知识管理器添加知识:")
        for content in test_knowledges:
            kid = km.add_knowledge(content, auto_classify=True)
            status = "[OK]" if kid != "error" and kid != "duplicate" else "[SKIP]"
            print(f"  {status} {content[:50]}... (ID: {kid})")

        # 测试搜索
        print("\n搜索知识 '三角套利':")
        results = km.search_knowledge("三角套利", top_k=2)
        for i, result in enumerate(results, 1):
            content = result.get('content', '')
            print(f"  {i}. {content[:60]}...")

        # 获取统计
        stats = km.get_knowledge_statistics()
        print(f"\n知识统计: {stats}")

        print("\n[OK] 知识管理器与 Memo0 集成测试通过")
        return True

    except Exception as e:
        print(f"\n[FAIL] 知识管理器与 Memo0 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_memo0_config():
    """测试 Memo0 配置加载"""
    print("\n" + "="*80)
    print("测试 3: Memo0 配置加载")
    print("="*80)

    try:
        from storage.mem0_storage import load_mem0_config, is_mem0_available

        # 加载配置
        config = load_mem0_config()
        print("配置加载成功:")
        print(f"  API Key: {'已配置' if config.get('api_key') else '未配置'}")
        print(f"  User ID: {config.get('user_id')}")
        print(f"  Agent ID: {config.get('agent_id')}")
        print(f"  Rerank: {config.get('rerank')}")

        # 检查可用性
        available = is_mem0_available()
        print(f"\nMemo0 可用: {'是' if available else '否 (使用本地 SQLite)'}")

        print("\n[OK] Memo0 配置加载测试通过")
        return True

    except Exception as e:
        print(f"\n[FAIL] Memo0 配置加载测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "="*80)
    print("Memo0 集成快速测试")
    print("="*80)
    print("开始时间:", __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    results = {
        "统一存储功能": False,
        "知识管理器集成": False,
        "Memo0 配置加载": False
    }

    # 运行测试
    results["统一存储功能"] = test_unified_storage()
    results["知识管理器集成"] = test_knowledge_manager_with_mem0()
    results["Memo0 配置加载"] = test_memo0_config()

    # 汇总结果
    print("\n" + "="*80)
    print("测试结果汇总")
    print("="*80)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, is_passed in results.items():
        status = "[PASS] 通过" if is_passed else "[FAIL] 失败"
        print(f"{status}: {test_name}")

    print(f"\n总计: {passed}/{total} 测试通过")
    print(f"成功率: {passed/total*100:.1f}%")

    if passed == total:
        print("\n[SUCCESS] 所有测试通过！Memo0 集成成功！")
    else:
        print(f"\n[WARNING] {total - passed} 个测试失败")

    print("结束时间:", __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


if __name__ == "__main__":
    main()
