"""运维模块 V3.7 - Production Operations

提供生产级的运维能力，包括系统健康监控、自动恢复和备份管理。

核心组件：
- SystemHealthMonitor: 24/7系统健康监控
- AutoRecoveryEngine: 自动故障检测和恢复
- BackupManager: 数据备份和灾难恢复
"""

from .system_health_monitor import (
    SystemHealthMonitor,
    HealthCheck,
    ComponentHealthCheck,
    DatabaseHealthCheck,
    ResourceHealthCheck,
    PerformanceHealthCheck,
    HealthStatus,
    HealthCheckType,
    HealthReport,
    HealthCheckResult,
    create_system_health_monitor
)

from .auto_recovery_engine import (
    AutoRecoveryEngine,
    RecoveryActionExecutor,
    RecoveryAction,
    RecoveryPlan,
    RecoveryReport,
    RecoveryActionType,
    RecoveryPriority,
    RecoveryStatus,
    create_auto_recovery_engine
)

from .backup_manager import (
    BackupManager,
    BackupValidator,
    BackupMetadata,
    RestoreResult,
    BackupType,
    BackupStatus,
    create_backup_manager
)

__all__ = [
    # System Health Monitor
    'SystemHealthMonitor',
    'HealthCheck',
    'ComponentHealthCheck',
    'DatabaseHealthCheck',
    'ResourceHealthCheck',
    'PerformanceHealthCheck',
    'HealthStatus',
    'HealthCheckType',
    'HealthReport',
    'HealthCheckResult',
    'create_system_health_monitor',

    # Auto Recovery Engine
    'AutoRecoveryEngine',
    'RecoveryActionExecutor',
    'RecoveryAction',
    'RecoveryPlan',
    'RecoveryReport',
    'RecoveryActionType',
    'RecoveryPriority',
    'RecoveryStatus',
    'create_auto_recovery_engine',

    # Backup Manager
    'BackupManager',
    'BackupValidator',
    'BackupMetadata',
    'RestoreResult',
    'BackupType',
    'BackupStatus',
    'create_backup_manager',
]

__version__ = '3.7.0'
