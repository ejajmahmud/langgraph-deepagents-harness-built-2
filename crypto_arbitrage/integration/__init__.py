"""系统集成模块 - Phase 13

提供系统级集成功能，包括：
- 系统协调器：统一协调系统各模块的运行
- 存储集成器：Memo0存储深度对接
- 策略优化器：基于监控反馈的智能优化
- 交易模块集成：完整的生产级交易系统

创建时间：2026-04-19 21:35:00
更新时间：2026-04-28 交易模块集成
"""

from integration.system_coordinator import (
    SystemCoordinator,
    SystemStatus,
    ModuleStatus,
    EventType,
    get_system_coordinator
)

from integration.storage_integration import (
    StorageIntegrator,
    get_storage_integrator
)

from integration.strategy_optimizer import (
    StrategyOptimizer,
    get_strategy_optimizer
)

__all__ = [
    # 系统协调器
    'SystemCoordinator',
    'SystemStatus',
    'ModuleStatus',
    'EventType',
    'get_system_coordinator',
    # 存储集成器
    'StorageIntegrator',
    'get_storage_integrator',
    # 策略优化器
    'StrategyOptimizer',
    'get_strategy_optimizer',
]

__version__ = '3.2.0'
__phase__ = "Phase 20: 多链支持与治理投票"
