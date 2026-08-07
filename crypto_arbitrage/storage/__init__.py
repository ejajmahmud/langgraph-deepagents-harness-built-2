"""存储模块初始化 V15.3 - 统一的存储接口

V15.3重大更新：存储模块统一化，消除版本碎片化，提供清晰的导入接口。

核心存储:
- KnowledgeBase: 基础知识库
- ProjectTracker: 项目进度追踪器
- DeepMemo0IntegrationV59: 深度Memo0集成V5.9（最新，异步分析）
- UnifiedStorage: 统一存储接口
"""

from storage.knowledge_base import (
    KnowledgeBase,
    initialize_knowledge_base,
    get_knowledge_base
)

from storage.project_tracker import (
    ProjectTracker,
    initialize_project_tracker,
    get_project_tracker,
    record_current_iteration
)

# V2.2: 智能决策组件
from storage.intelligent_decision_engine import IntelligentDecisionEngine
from storage.market_pattern_recognizer import MarketPatternRecognizer
from storage.strategy_optimizer import StrategyOptimizer

# V3.0: Memo0 智能存储集成
from storage.mem0_storage import (
    Memo0Storage,
    UnifiedStorage,
    initialize_mem0,
    get_mem0_storage,
    is_mem0_available,
    get_unified_storage,
    add_trading_knowledge,
    search_trading_knowledge,
    load_mem0_config
)

# V15.3: 深度Memo0集成V5.9（最新版本，包含异步分析能力）
from storage.deep_memo0_integration_v5_9 import (
    DeepMemo0IntegrationV59,
    create_deep_memo0_integration_v5_9
)

# V15.3: 统一的存储接口（保持向后兼容性）
DeepMemo0Integration = DeepMemo0IntegrationV59
Memo0StorageAdvanced = DeepMemo0IntegrationV59

__all__ = [
    # 基础存储
    'KnowledgeBase',
    'initialize_knowledge_base',
    'get_knowledge_base',
    'ProjectTracker',
    'initialize_project_tracker',
    'get_project_tracker',
    'record_current_iteration',
    # V2.2: 智能决策组件
    'IntelligentDecisionEngine',
    'MarketPatternRecognizer',
    'StrategyOptimizer',
    # V3.0: Memo0 智能存储集成
    'Memo0Storage',
    'UnifiedStorage',
    'initialize_mem0',
    'get_mem0_storage',
    'is_mem0_available',
    'get_unified_storage',
    'add_trading_knowledge',
    'search_trading_knowledge',
    'load_mem0_config',
    # V15.3: 深度Memo0集成V5.9（最新）
    'DeepMemo0IntegrationV59',
    'create_deep_memo0_integration_v5_9',
    # V15.3: 向后兼容别名
    'DeepMemo0Integration',
    'Memo0StorageAdvanced',
]
