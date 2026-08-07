"""自动化模块初始化文件

Phase 11 核心模块 - 实时监控与运维自动化
"""

from .auto_scaler import AutoScaler
from .auto_recovery import AutoRecovery
from .backup_manager import BackupManager

__all__ = [
    'AutoScaler',
    'AutoRecovery',
    'BackupManager',
]
