"""存储模块包 - V5.10架构增强

V5.8新增：将DeepMemo0Integration拆分为5个高内聚性模块：
1. SemanticSearchModule - 语义搜索专用
2. KnowledgeFusionModule - 知识融合专用
3. PredictiveAnalysisModule - 预测分析专用
4. KnowledgeManagementModule - 知识管理专用
5. CacheManagerModule - 缓存管理专用

V5.9新增：第6个高内聚性模块
6. AsyncAnalysisModule - 异步分析专用

V5.10新增：4个智能知识管理模块
7. AutoKnowledgeExtractor - 自动知识提取
8. IntelligentKnowledgeClassifier - 智能分类
9. KnowledgeQualityOptimizer - 质量优化
10. KnowledgeTrendAnalyzer - 趋势分析

V5.10新增：3个性能优化模块
11. SmartCacheOptimizer - 智能缓存优化
12. ConcurrentController - 并发控制
13. MemoryOptimizer - 内存优化
"""

from .semantic_search_module import SemanticSearchModule
from .knowledge_fusion_module import KnowledgeFusionModule
from .predictive_analysis_module import PredictiveAnalysisModule
from .knowledge_management_module import KnowledgeManagementModule
from .cache_manager_module import CacheManagerModule
from .async_analysis_module import AsyncAnalysisModule

# V5.10新增模块
from .auto_knowledge_extractor import AutoKnowledgeExtractor
from .intelligent_knowledge_classifier import IntelligentKnowledgeClassifier
from .knowledge_quality_optimizer import KnowledgeQualityOptimizer
from .knowledge_trend_analyzer import KnowledgeTrendAnalyzer

# V5.10性能优化模块
from .smart_cache_optimizer import SmartCacheOptimizer
from .concurrent_controller import ConcurrentController
from .memory_optimizer import MemoryOptimizer

# V15.5缓存优化模块
from .cache_optimization_v15_5 import (
    CacheOptimizationV15,
    CacheMetrics,
    create_cache_optimization,
    optimized_cache_get
)

# V5.10 Phase 2决策系统模块
from .knowledge_based_decision_maker import (
    KnowledgeBasedDecisionMaker,
    Decision,
    DecisionContext,
    DecisionRationale,
    DecisionRecord,
    DecisionType,
    KnowledgeMatch
)
from .real_time_knowledge_updater import (
    RealTimeKnowledgeUpdater,
    MarketDataSnapshot,
    KnowledgeUpdateTask,
    KnowledgeGap,
    UpdatePriority,
    UpdateStatus
)
from .decision_confidence_calculator import (
    DecisionConfidenceCalculator,
    ConfidenceScore,
    ConfidenceReport,
    ConfidenceLevel,
    ConfidenceCalibration
)
from .knowledge_feedback_loop import (
    KnowledgeFeedbackLoop,
    DecisionOutcome,
    KnowledgeValueAssessment,
    OptimizationTrigger,
    LearningCycle,
    OutcomeType,
    KnowledgeValueLevel,
    OptimizationAction
)

__all__ = [
    'SemanticSearchModule',
    'KnowledgeFusionModule',
    'PredictiveAnalysisModule',
    'KnowledgeManagementModule',
    'CacheManagerModule',
    'AsyncAnalysisModule',
    'AutoKnowledgeExtractor',
    'IntelligentKnowledgeClassifier',
    'KnowledgeQualityOptimizer',
    'KnowledgeTrendAnalyzer',
    'SmartCacheOptimizer',
    'ConcurrentController',
    'MemoryOptimizer',
    # V15.5缓存优化
    'CacheOptimizationV15',
    'CacheMetrics',
    'create_cache_optimization',
    'optimized_cache_get'
    # V5.10 Phase 2
    'KnowledgeBasedDecisionMaker',
    'Decision',
    'DecisionContext',
    'DecisionRationale',
    'DecisionRecord',
    'DecisionType',
    'KnowledgeMatch',
    # RealTimeKnowledgeUpdater
    'RealTimeKnowledgeUpdater',
    'MarketDataSnapshot',
    'KnowledgeUpdateTask',
    'KnowledgeGap',
    'UpdatePriority',
    'UpdateStatus',
    # DecisionConfidenceCalculator
    'DecisionConfidenceCalculator',
    'ConfidenceScore',
    'ConfidenceReport',
    'ConfidenceLevel',
    'ConfidenceCalibration',
    # KnowledgeFeedbackLoop
    'KnowledgeFeedbackLoop',
    'DecisionOutcome',
    'KnowledgeValueAssessment',
    'OptimizationTrigger',
    'LearningCycle',
    'OutcomeType',
    'KnowledgeValueLevel',
    'OptimizationAction'
]
