"""LLM集成模块

V2.7: 异步LLM分析 + 信号融合缓存 + 性能优化
V3.7: 智能决策支持 + 自适应优化 + 异常检测
"""

from llm.trading_agents_wrapper import TradingAgentsWrapper
from llm.signal_fusion import SignalFusionEngine
from llm.async_trading_agents import (
    AsyncLLMAnalyzer,
    get_async_analyzer,
    analyze_crypto_async,
    analyze_batch_async
)
from llm.signal_cache import (
    SignalCache,
    SignalFusionWithCache,
    get_signal_fusion_with_cache
)
from llm.memo0_decision_support import (
    Memo0DecisionSupport,
    MarketContext,
    KnowledgeQueryResult,
    DecisionInsight,
    MarketContextBuilder,
    create_decision_support
)
from llm.adaptive_strategy_optimizer import (
    AdaptiveStrategyOptimizer,
    PerformanceAnalyzer,
    MarketRegimeDetector,
    StrategyPerformance,
    ParameterRecommendation,
    StrategyCombination,
    create_strategy_optimizer
)
from llm.intelligent_anomaly_detector import (
    IntelligentAnomalyDetector,
    StatisticalAnomalyDetector,
    PatternAnomalyDetector,
    AnomalyType,
    AnomalySeverity,
    AnomalyCategory,
    AnomalyDetectionResult,
    AnomalyDiagnosis,
    AnomalyPrediction,
    initialize_intelligent_anomaly_detector,
    get_intelligent_anomaly_detector
)

__all__ = [
    # V2.7 模块
    "TradingAgentsWrapper",
    "SignalFusionEngine",
    "AsyncLLMAnalyzer",
    "get_async_analyzer",
    "analyze_crypto_async",
    "analyze_batch_async",
    "SignalCache",
    "SignalFusionWithCache",
    "get_signal_fusion_with_cache",

    # V3.7 新增模块
    # Memo0 决策支持
    "Memo0DecisionSupport",
    "MarketContext",
    "KnowledgeQueryResult",
    "DecisionInsight",
    "MarketContextBuilder",
    "create_decision_support",

    # 自适应策略优化
    "AdaptiveStrategyOptimizer",
    "PerformanceAnalyzer",
    "MarketRegimeDetector",
    "StrategyPerformance",
    "ParameterRecommendation",
    "StrategyCombination",
    "create_strategy_optimizer",

    # 智能异常检测
    "IntelligentAnomalyDetector",
    "StatisticalAnomalyDetector",
    "PatternAnomalyDetector",
    "AnomalyType",
    "AnomalySeverity",
    "AnomalyCategory",
    "AnomalyDetectionResult",
    "AnomalyDiagnosis",
    "AnomalyPrediction",
    "initialize_intelligent_anomaly_detector",
    "get_intelligent_anomaly_detector",
]
