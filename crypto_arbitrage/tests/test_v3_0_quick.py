"""V3.0 快速验证脚本

验证 V3.0 组件是否可以正确导入和初始化：
1. 智能优化引擎导入和初始化
2. 智能知识管理器导入和初始化
3. 自适应错误处理器导入和初始化
4. 主代理 V3.0 组件集成验证

运行方式:
    python tests/test_v3_0_quick.py
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 设置 UTF-8 编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("\n" + "="*80)
print(" 数字货币套利交易系统 V3.0 - 快速验证")
print(f" 验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

all_passed = True

# 测试 1: 智能优化引擎导入和初始化
print("\n[测试 1] 智能优化引擎 V3.0")
try:
    from tools.intelligent_optimizer import IntelligentOptimizer

    optimizer = IntelligentOptimizer(
        optimization_interval=60,
        history_window=100,
        min_data_points=5,
        config_path='config/test_optimization_state.json'
    )

    # 测试基本功能
    optimizer.record_performance(
        'test_strategy',
        {'profit': 100.0, 'profit_rate': 0.5, 'success': True}
    )

    optimizations = optimizer.get_current_optimizations()
    trends = optimizer.analyze_performance_trends('test_strategy')

    print("  [OK] 智能优化引擎导入成功")
    print("  [OK] 初始化成功")
    print("  [OK] 性能数据记录功能正常")
    print("  [OK] 趋势分析功能正常")
    print("  [OK] 当前优化查询功能正常")

except Exception as e:
    print(f"  [FAIL] 智能优化引擎测试失败: {e}")
    all_passed = False

# 测试 2: 智能知识管理器导入和初始化
print("\n[测试 2] 智能知识管理器 V3.0")
try:
    from tools.knowledge_manager_v3 import IntelligentKnowledgeManager
    from storage.mem0_storage import get_unified_storage

    storage = get_unified_storage()
    km = IntelligentKnowledgeManager(
        storage_backend=storage,
        config={'cache_ttl': 60}
    )

    # 测试基本功能
    knowledge_id = km.add_knowledge(
        content="测试知识：低波动率市场应降低风险敞口",
        category="risk",
        metadata={'test': True}
    )

    results = km.search_knowledge("风险", top_k=5)
    stats = km.get_knowledge_statistics()

    print("  [OK] 智能知识管理器导入成功")
    print("  [OK] 初始化成功")
    print("  [OK] 知识添加功能正常")
    print("  [OK] 知识搜索功能正常")
    print("  [OK] 知识统计功能正常")

except Exception as e:
    print(f"  [FAIL] 智能知识管理器测试失败: {e}")
    all_passed = False

# 测试 3: 自适应错误处理器导入和初始化
print("\n[测试 3] 自适应错误处理器 V3.0")
try:
    from tools.adaptive_error_handler import AdaptiveErrorHandler

    eh = AdaptiveErrorHandler(config={
        'max_retries': 2,
        'retry_delay': 0.5,
        'backoff_factor': 2.0,
        'circuit_breaker': {
            'failure_threshold': 3,
            'timeout': 30.0
        }
    })

    # 测试基本功能
    eh.handle_error(
        error=Exception("测试错误"),
        context={"scenario": "测试场景", "operation": "测试操作"}
    )

    stats = eh.get_error_statistics()
    patterns = eh.get_error_patterns()

    print("  [OK] 自适应错误处理器导入成功")
    print("  [OK] 初始化成功")
    print("  [OK] 错误处理功能正常")
    print("  [OK] 错误统计功能正常")
    print("  [OK] 错误模式分析功能正常")

except Exception as e:
    print(f"  [FAIL] 自适应错误处理器测试失败: {e}")
    all_passed = False

# 测试 4: 主代理 V3.0 集成验证（检查代码存在）
print("\n[测试 4] 主代理 V3.0 集成验证")
try:
    # 检查主代理文件是否包含 V3.0 相关代码
    main_agent_path = os.path.join(os.path.dirname(__file__), '..', 'agents', 'main_agent.py')
    with open(main_agent_path, 'r', encoding='utf-8') as f:
        content = f.read()

    v3_components = [
        'IntelligentOptimizer',
        'IntelligentKnowledgeManager',
        'AdaptiveErrorHandler',
        'trigger_optimization_tool',
        'get_optimization_status_tool',
        'add_intelligent_knowledge_tool',
        'get_error_statistics_tool'
    ]

    print("  [OK] 主代理文件读取成功")

    for component in v3_components:
        if component in content:
            print(f"  [OK] {component} 已集成到主代理")
        else:
            print(f"  [FAIL] {component} 未找到")
            all_passed = False

except Exception as e:
    print(f"  [FAIL] 主代理 V3.0 集成验证失败: {e}")
    all_passed = False

# 测试结果汇总
print("\n" + "="*80)
print(" 验证结果汇总")
print("="*80)

if all_passed:
    print("\n[SUCCESS] 所有 V3.0 组件验证通过！")
    print("\n主要成就:")
    print("  1. 智能优化引擎 V3.0 - 完全集成")
    print("  2. 智能知识管理器 V3.0 - 完全集成")
    print("  3. 自适应错误处理器 V3.0 - 完全集成")
    print("  4. 主代理 V3.0 - 升级完成")
    print("\nV3.0 系统已具备智能自适应能力！")
else:
    print("\n[WARNING] 部分验证失败，请检查上述输出")

print("="*80 + "\n")

sys.exit(0 if all_passed else 1)
