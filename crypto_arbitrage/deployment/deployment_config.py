"""部署配置 - Phase 10核心模块

管理不同环境的配置（开发/测试/生产）。

核心功能：
1. 环境配置 - 多环境配置管理
2. 配置验证 - 配置完整性检查
3. 配置加载 - 从文件或环境变量加载
4. 配置导出 - 配置导出功能

创建时间：2026-04-19 19:52:00
"""

import json
import logging
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, Union

logger = logging.getLogger(__name__)


class DeploymentConfig:
    """部署配置

    管理不同环境的配置。
    """

    # 支持的环境
    SUPPORTED_ENVS = ['development', 'staging', 'production']

    def __init__(self, env: str = 'production', config_path: Optional[str] = None):
        """初始化部署配置

        Args:
            env: 环境名称（development/staging/production）
            config_path: 配置文件路径（可选）

        Raises:
            ValueError: 如果环境不支持
        """
        if env not in self.SUPPORTED_ENVS:
            raise ValueError(f"不支持的环境: {env}. 支持的环境: {self.SUPPORTED_ENVS}")

        self.env = env
        self.config_path = config_path
        self.config = self._load_config()

        logger.info(f"部署配置初始化完成: {env}")

    def _load_config(self) -> Dict[str, Any]:
        """加载配置

        Returns:
            配置字典
        """
        config = {
            'env': self.env,
            'storage': self._get_storage_config(),
            'database': self._get_database_config(),
            'monitoring': self._get_monitoring_config(),
            'security': self._get_security_config(),
            'automation': self._get_automation_config(),
        }

        # 如果有配置文件，加载并合并
        if self.config_path and Path(self.config_path).exists():
            file_config = self._load_config_file(self.config_path)
            config = self._merge_configs(config, file_config)

        return config

    def _load_config_file(self, path: str) -> Dict[str, Any]:
        """从文件加载配置

        Args:
            path: 配置文件路径

        Returns:
            配置字典
        """
        file_path = Path(path)

        if file_path.suffix in ['.yml', '.yaml']:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        elif file_path.suffix == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            logger.warning(f"不支持的配置文件格式: {file_path.suffix}")
            return {}

    def _merge_configs(
        self,
        base: Dict[str, Any],
        override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """合并配置

        Args:
            base: 基础配置
            override: 覆盖配置

        Returns:
            合并后的配置
        """
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value

        return result

    def _get_storage_config(self) -> Dict[str, Any]:
        """获取存储配置

        Returns:
            存储配置
        """
        base_config = {
            'storage_type': 'local_vector',
            'database_path': './local_vector_db.sqlite3',
            'cache_enabled': True,
            'cache_size': 1000,
            'monitoring_enabled': True,
        }

        if self.env == 'development':
            base_config.update({
                'cache_enabled': True,
                'cache_size': 100,
            })
        elif self.env == 'production':
            base_config.update({
                'cache_enabled': True,
                'cache_size': 10000,
                'monitoring_enabled': True,
            })

        return base_config

    def _get_database_config(self) -> Dict[str, Any]:
        """获取数据库配置

        Returns:
            数据库配置
        """
        base_config = {
            'type': 'sqlite',
            'path': './crypto_arbitrage.db',
            'backup_enabled': False,
            'auto_backup_interval_hours': 24,
        }

        if self.env == 'production':
            base_config.update({
                'backup_enabled': True,
                'auto_backup_interval_hours': 6,
            })

        return base_config

    def _get_monitoring_config(self) -> Dict[str, Any]:
        """获取监控配置

        Returns:
            监控配置
        """
        base_config = {
            'enabled': True,
            'metrics_interval_seconds': 60,
            'alert_enabled': False,
            'dashboard_enabled': False,
        }

        if self.env == 'production':
            base_config.update({
                'metrics_interval_seconds': 30,
                'alert_enabled': True,
                'dashboard_enabled': True,
            })

        return base_config

    def _get_security_config(self) -> Dict[str, Any]:
        """获取安全配置

        Returns:
            安全配置
        """
        base_config = {
            'auth_enabled': False,
            'encryption_enabled': False,
            'audit_logging': False,
            'session_timeout_minutes': 30,
        }

        if self.env == 'production':
            base_config.update({
                'auth_enabled': True,
                'encryption_enabled': True,
                'audit_logging': True,
            })

        return base_config

    def _get_automation_config(self) -> Dict[str, Any]:
        """获取自动化配置

        Returns:
            自动化配置
        """
        base_config = {
            'auto_scaling_enabled': False,
            'auto_recovery_enabled': False,
            'auto_backup_enabled': False,
            'maintenance_enabled': False,
        }

        if self.env == 'production':
            base_config.update({
                'auto_scaling_enabled': True,
                'auto_recovery_enabled': True,
                'auto_backup_enabled': True,
                'maintenance_enabled': True,
            })

        return base_config

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """设置配置值

        Args:
            key: 配置键
            value: 配置值
        """
        keys = key.split('.')
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value
        logger.info(f"配置更新: {key} = {value}")

    def get_storage_config(self) -> Dict[str, Any]:
        """获取存储配置

        Returns:
            存储配置字典
        """
        return self.config.get('storage', {})

    def get_database_config(self) -> Dict[str, Any]:
        """获取数据库配置

        Returns:
            数据库配置字典
        """
        return self.config.get('database', {})

    def get_monitoring_config(self) -> Dict[str, Any]:
        """获取监控配置

        Returns:
            监控配置字典
        """
        return self.config.get('monitoring', {})

    def get_security_config(self) -> Dict[str, Any]:
        """获取安全配置

        Returns:
            安全配置字典
        """
        return self.config.get('security', {})

    def get_automation_config(self) -> Dict[str, Any]:
        """获取自动化配置

        Returns:
            自动化配置字典
        """
        return self.config.get('automation', {})

    def validate_config(self) -> Dict[str, Any]:
        """验证配置

        Returns:
            验证结果字典
        """
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
        }

        # 验证存储配置
        storage_config = self.get_storage_config()
        if 'storage_type' not in storage_config:
            results['errors'].append('缺少存储类型配置')
        else:
            storage_type = storage_config['storage_type']
            if storage_type == 'local_vector':
                if 'database_path' not in storage_config:
                    results['errors'].append('本地向量存储需要配置数据库路径')

        # 验证数据库配置
        database_config = self.get_database_config()
        if 'type' not in database_config:
            results['errors'].append('缺少数据库类型配置')

        # 验证监控配置
        monitoring_config = self.get_monitoring_config()
        if self.env == 'production':
            if not monitoring_config.get('alert_enabled', False):
                results['warnings'].append('生产环境建议启用告警')
            if not monitoring_config.get('dashboard_enabled', False):
                results['warnings'].append('生产环境建议启用监控仪表板')

        # 验证安全配置
        security_config = self.get_security_config()
        if self.env == 'production':
            if not security_config.get('auth_enabled', False):
                results['warnings'].append('生产环境建议启用认证')
            if not security_config.get('encryption_enabled', False):
                results['warnings'].append('生产环境建议启用加密')

        # 设置验证结果
        results['valid'] = len(results['errors']) == 0

        return results

    def export_config(self, format: str = 'json') -> str:
        """导出配置

        Args:
            format: 导出格式（json/yaml）

        Returns:
            配置字符串

        Raises:
            ValueError: 如果格式不支持
        """
        if format == 'json':
            return json.dumps(self.config, indent=2, ensure_ascii=False)
        elif format in ['yaml', 'yml']:
            return yaml.dump(self.config, default_flow_style=False, allow_unicode=True)
        else:
            raise ValueError(f"不支持的导出格式: {format}")

    def save_config(self, path: str, format: str = 'json'):
        """保存配置到文件

        Args:
            path: 保存路径
            format: 文件格式（json/yaml）
        """
        config_str = self.export_config(format)

        with open(path, 'w', encoding='utf-8') as f:
            f.write(config_str)

        logger.info(f"配置已保存到: {path}")

    def __repr__(self) -> str:
        """字符串表示

        Returns:
            字符串表示
        """
        return f"DeploymentConfig(env={self.env}, keys={list(self.config.keys())})"
