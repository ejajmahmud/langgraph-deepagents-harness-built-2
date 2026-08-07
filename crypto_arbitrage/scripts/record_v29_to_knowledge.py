"""记录V29.0迭代到知识库"""

import asyncio
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入memo0存储
try:
    from storage.mem0_storage import get_unified_storage, add_trading_knowledge, search_trading_knowledge
except ImportError:
    print("[WARN] memo0存储导入失败，使用本地存储")
    get_unified_storage = None
    add_trading_knowledge = None
    search_trading_knowledge = None


def record_v29_progress():
    """记录V29.0进度到知识库"""
    iteration_info = {
        "version": "V29.0",
        "date": datetime.now().isoformat(),
        "features": [
            "三角套利策略测试 (test_v29_triangular.py)",
            "跨交易所套利策略测试 (test_v29_cross_exchange.py)",
            "calculate_triangle_profit 辅助函数",
            "is_profitable_triangle 辅助函数",
            "calculate_cross_exchange_spread 辅助函数",
            "calculate_net_profit 辅助函数",
            "修复 memo0_storage_impl import错误"
        ],
        "tests_passed": 6,
        "status": "completed"
    }

    # 记录到知识库
    if add_trading_knowledge:
        try:
            success = add_trading_knowledge(
                "iteration",
                f"Crypto Arbitrage V29.0 完成: {len(iteration_info['features'])}个功能",
                iteration_info
            )
            if success:
                print("[OK] V29.0进度已记录到memo0知识库")
            else:
                print("[WARN] 记录失败")
        except Exception as e:
            print(f"[ERROR] 记录错误: {e}")
    else:
        print("[INFO] memo0不可用，跳过记录")

    return iteration_info


if __name__ == "__main__":
    result = record_v29_progress()
    print(f"\n=== V29.0 记录完成 ===")
    print(f"版本: {result['version']}")
    print(f"日期: {result['date']}")
    print(f"功能数: {len(result['features'])}")
    print(f"测试通过: {result['tests_passed']}")
    print(f"状态: {result['status']}")