#!/usr/bin/env python3
"""测试和修复Memo0存储集成"""

import sys
import os
from pathlib import Path

def test_imports():
    """测试模块导入"""
    print("="*60)
    print("测试模块导入...")
    print("="*60)

    # 测试storage模块导入
    try:
        import storage
        print("✅ storage 模块导入成功")
        print(f"   导出的类: {[n for n in dir(storage) if not n.startswith('_')]}")
    except ImportError as e:
        print(f"❌ storage 模块导入失败: {e}")
        return False

    # 测试strategies模块导入
    try:
        import strategies
        print("✅ strategies 模块导入成功")
        print(f"   导出的类: {[n for n in dir(strategies) if not n.startswith('_')]}")
    except ImportError as e:
        print(f"❌ strategies 模块导入失败: {e}")
        return False

    # 测试trading模块导入
    try:
        import trading
        print("✅ trading 模块导入成功")
        print(f"   导出的类: {[n for n in dir(trading) if not n.startswith('_')]}")
    except ImportError as e:
        print(f"❌ trading 模块导入失败: {e}")
        return False

    # 测试agents模块导入
    try:
        import agents
        print("✅ agents 模块导入成功")
        print(f"   导出的类: {[n for n in dir(agents) if not n.startswith('_')]}")
    except ImportError as e:
        print(f"❌ agents 模块导入失败: {e}")
        return False

    return True

def test_memo0_storage():
    """测试Memo0存储"""
    print()
    print("="*60)
    print("测试Memo0存储...")
    print("="*60)

    # 检查环境变量
    print("\n环境变量检查:")
    print(f"  MEM0_API_KEY: {'已设置' if os.environ.get('MEM0_API_KEY') else '未设置'}")
    print(f"  MEM0_USER_ID: {os.environ.get('MEM0_USER_ID', 'crypto-arbitrage-user')}")
    print(f"  MEM0_AGENT_ID: {os.environ.get('MEM0_AGENT_ID', 'crypto-arbitrage')}")

    # 尝试初始化Memo0存储
    try:
        from storage import initialize_mem0, get_mem0_storage, is_mem0_available

        # 测试本地存储（无API密钥）
        print("\n测试本地存储（无API密钥）:")
        storage = initialize_mem0(None)

        if storage is None:
            print("❌ Memo0存储初始化失败（返回None）")
            return False

        print(f"✅ Memo0存储类型: {type(storage).__name__}")

        # 测试基本功能
        print("\n测试基本功能:")

        # 测试添加知识
        try:
            storage.add("test_knowledge", {
                "content": "这是一条测试知识",
                "type": "test",
                "timestamp": "2026-04-28T21:10:00"
            })
            print("✅ 添加知识成功")
        except Exception as e:
            print(f"❌ 添加知识失败: {e}")
            return False

        # 测试搜索知识
        try:
            results = storage.search("测试")
            print(f"✅ 搜索知识成功，找到 {len(results)} 条结果")
        except Exception as e:
            print(f"❌ 搜索知识失败: {e}")
            return False

        return True

    except Exception as e:
        print(f"❌ Memo0存储测试失败: {e}")
        return False

def test_unified_storage():
    """测试统一存储接口"""
    print()
    print("="*60)
    print("测试统一存储接口...")
    print("="*60)

    try:
        from storage import get_unified_storage

        unified = get_unified_storage()
        if unified is None:
            print("❌ 统一存储接口不可用")
            return False

        print(f"✅ 统一存储类型: {type(unified).__name__}")

        # 测试添加交易知识
        try:
            unified.add_trading_knowledge({
                "strategy": "test_strategy",
                "market_condition": "bull_market",
                "decision": "buy",
                "confidence": 0.85,
                "timestamp": "2026-04-28T21:10:00"
            })
            print("✅ 添加交易知识成功")
        except Exception as e:
            print(f"❌ 添加交易知识失败: {e}")
            return False

        # 测试搜索交易知识
        try:
            results = unified.search_trading_knowledge({"strategy": "test_strategy"})
            print(f"✅ 搜索交易知识成功，找到 {len(results)} 条结果")
        except Exception as e:
            print(f"❌ 搜索交易知识失败: {e}")
            return False

        return True

    except Exception as e:
        print(f"❌ 统一存储接口测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("数字货币套利系统 - Memo0集成测试")
    print("测试时间:", "2026-04-28 21:10:00")
    print()

    # 测试1: 模块导入
    imports_ok = test_imports()
    if not imports_ok:
        print("\n❌ 模块导入测试失败，无法继续")
        sys.exit(1)

    # 测试2: Memo0存储
    memo0_ok = test_memo0_storage()
    if not memo0_ok:
        print("\n⚠️ Memo0存储测试失败")

    # 测试3: 统一存储接口
    unified_ok = test_unified_storage()
    if not unified_ok:
        print("\n⚠️ 统一存储接口测试失败")

    # 总结
    print()
    print("="*60)
    print("测试总结")
    print("="*60)

    if imports_ok and memo0_ok and unified_ok:
        print("✅ 所有测试通过！Memo0集成正常")
    else:
        print("⚠️ 部分测试失败，需要修复")

    print()
    print("修复建议:")
    print("1. 如果Memo0不可用，系统会自动使用本地SQLite存储")
    print("2. 可以通过设置MEM0_API_KEY环境变量启用Memo0云存储")
    print("3. 本地SQLite存储位于: crypto_arbitrage_knowledge.db")

if __name__ == '__main__':
    main()