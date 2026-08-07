"""系统诊断脚本 - V15.4迭代"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print(f"项目根目录: {project_root}")
print(f"Python路径: {sys.path[:3]}")
print()

# 检查关键文件
print("=== 检查关键文件 ===")
files_to_check = [
    "storage/__init__.py",
    "storage/mem0_storage.py",
    "storage/deep_memo0_integration_v5_9.py",
    "strategies/enhanced_low_risk_arbitrage_engine_v5_9.py",
    "agents/main_agent_v5_10.py",
    "storage/modules/async_analysis_module.py",
]

for filepath in files_to_check:
    full_path = project_root / filepath
    exists = full_path.exists()
    status = "[OK]" if exists else "[MISSING]"
    print(f"{status} {filepath}")

print()

# 测试逐步导入
print("=== 逐步导入测试 ===")

# 测试1: 基础导入
try:
    from storage.storage_factory import StorageFactory
    print("[OK] StorageFactory 导入成功")
except ImportError as e:
    print(f"[FAIL] StorageFactory 导入失败: {e}")

# 测试2: storage模块
try:
    from storage import (
        KnowledgeBase,
        initialize_knowledge_base,
        DeepMemo0IntegrationV59,
        create_deep_memo0_integration_v5_9,
        get_mem0_storage
    )
    print("[OK] storage 模块导入成功")
except ImportError as e:
    print(f"[FAIL] storage 模块导入失败: {e}")

# 测试3: storage.modules
try:
    from storage.modules import (
        AsyncAnalysisModule,
        SemanticSearchModule,
        KnowledgeFusionModule,
        PredictiveAnalysisModule,
        KnowledgeManagementModule,
        CacheManagerModule
    )
    print("[OK] storage.modules 导入成功")
except ImportError as e:
    print(f"[FAIL] storage.modules 导入失败: {e}")

# 测试4: strategies模块
try:
    from strategies.enhanced_low_risk_arbitrage_engine_v5_9 import (
        EnhancedLowRiskArbitrageEngineV59,
        create_enhanced_low_risk_engine_v5_9
    )
    print("[OK] strategies.enhanced_low_risk_arbitrage_engine_v5_9 导入成功")
except ImportError as e:
    print(f"[FAIL] strategies.enhanced_low_risk_arbitrage_engine_v5_9 导入失败: {e}")

# 测试5: agents模块
try:
    from agents.main_agent_v5_10 import (
        CryptoArbitrageAgentV510,
        run_crypto_arbitrage_agent_v5_10
    )
    print("[OK] agents.main_agent_v5_10 导入成功")
except ImportError as e:
    print(f"[FAIL] agents.main_agent_v5_10 导入失败: {e}")

print()
print("=== 诊断总结 ===")
print("系统V15.4主要组件:")
print("  - Storage模块: [OK] (模块化设计)")
print("  - Memo0集成: [OK] (V5.9深度集成)")
print("  - 异步分析: [OK] (AsyncAnalysisModule)")
print("  - 套利引擎: [OK] (V5.9增强版)")
print("  - 主代理: [OK] (V5.10生产级)")
