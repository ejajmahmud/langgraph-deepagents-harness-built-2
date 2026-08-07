"""配置热更新 V3.3

支持运行时配置更新，无需重启系统。

核心功能：
1. 配置热加载
2. 配置验证
3. 配置回滚
4. 配置变更通知
"""

import copy
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class ConfigChange:
    """配置变更记录"""

    def __init__(
        self,
        section: str,
        old_value: Any,
        new_value: Any,
        changed_at: str,
        changed_by: str = 'system'
    ):
        """初始化配置变更记录

        Args:
            section: 配置节
            old_value: 旧值
            new_value: 新值
            changed_at: 变更时间
            changed_by: 变更者
        """
        self.section = section
        self.old_value = old_value
        self.new_value = new_value
        self.changed_at = changed_at
        self.changed_by = changed_by


class ConfigValidator:
    """配置验证器"""

    def __init__(self):
        """初始化配置验证器"""
        self.validators: Dict[str, List[Callable]] = {}

    def register_validator(
        self,
        section: str,
        validator: Callable[[Any], bool]
    ) -> None:
        """注册验证器

        Args:
            section: 配置节
            validator: 验证函数
        """
        if section not in self.validators:
            self.validators[section] = []
        self.validators[section].append(validator)
        logger.debug(f"Registered validator for section: {section}")

    def validate(self, section: str, value: Any) -> bool:
        """验证配置值

        Args:
            section: 配置节
            value: 配置值

        Returns:
            是否有效
        """
        if section not in self.validators:
            return True

        for validator in self.validators[section]:
            try:
                if not validator(value):
                    logger.warning(f"Validation failed for {section}: {value}")
                    return False
            except Exception as e:
                logger.error(f"Error validating {section}: {e}")
                return False

        return True


class ConfigHotReload:
    """配置热加载

    支持运行时配置更新和热重载。
    """

    def __init__(self, config_manager):
        """初始化配置热加载

        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
        self.validator = ConfigValidator()

        # 当前配置
        self.current_config: Dict[str, Any] = {}

        # 配置历史（用于回滚）
        self.config_history: List[ConfigChange] = []
        self.max_history_size = 50

        # 变更监听器
        self.change_listeners: List[Callable] = []

        # 重载锁
        self.reload_lock = threading.Lock()

        # 初始化验证器
        self._initialize_validators()

        # 加载当前配置
        self._load_current_config()

        logger.info("ConfigHotReload initialized")

    def _initialize_validators(self) -> None:
        """初始化默认验证器"""
        # 策略配置验证
        self.validator.register_validator('strategies', self._validate_strategies)

        # 风险管理配置验证
        self.validator.register_validator('risk_management', self._validate_risk_management)

        # 监控配置验证
        self.validator.register_validator('monitoring', self._validate_monitoring)

        # 深度风险管理配置验证
        self.validator.register_validator('deep_risk_manager', self._validate_deep_risk_manager)

        # 低风险套利引擎配置验证
        self.validator.register_validator('low_risk_arbitrage_engine', self._validate_low_risk_engine)

        logger.info("Default validators initialized")

    def _load_current_config(self) -> None:
        """加载当前配置"""
        try:
            self.current_config = self.config_manager.load_config()
            logger.info("Current config loaded")
        except Exception as e:
            logger.error(f"Error loading current config: {e}")
            self.current_config = {}

    # ==================== 验证方法 ====================

    def _validate_strategies(self, value: Any) -> bool:
        """验证策略配置"""
        if not isinstance(value, dict):
            return False

        for strategy_name, strategy_config in value.items():
            if not isinstance(strategy_config, dict):
                return False

            # 检查必需的字段
            if 'enabled' not in strategy_config:
                return False

            # 验证 allocation
            if 'allocation' in strategy_config:
                allocation = strategy_config['allocation']
                if not isinstance(allocation, (int, float)) or allocation < 0 or allocation > 1:
                    return False

        return True

    def _validate_risk_management(self, value: Any) -> bool:
        """验证风险管理配置"""
        if not isinstance(value, dict):
            return False

        # 验证 max_exposure
        if 'max_exposure' in value:
            max_exposure = value['max_exposure']
            if not isinstance(max_exposure, (int, float)) or max_exposure <= 0:
                return False

        # 验证 max_drawdown
        if 'max_drawdown' in value:
            max_drawdown = value['max_drawdown']
            if not isinstance(max_drawdown, (int, float)) or max_drawdown <= 0 or max_drawdown > 1:
                return False

        return True

    def _validate_monitoring(self, value: Any) -> bool:
        """验证监控配置"""
        if not isinstance(value, dict):
            return False

        # 验证 update_interval
        if 'update_interval' in value:
            update_interval = value['update_interval']
            if not isinstance(update_interval, (int, float)) or update_interval <= 0:
                return False

        return True

    def _validate_deep_risk_manager(self, value: Any) -> bool:
        """验证深度风险管理配置"""
        if not isinstance(value, dict):
            return False

        # 验证 max_exposure
        if 'max_exposure' in value:
            max_exposure = value['max_exposure']
            if not isinstance(max_exposure, (int, float)) or max_exposure <= 0:
                return False

        # 验证 volatility_threshold
        if 'volatility_threshold' in value:
            volatility_threshold = value['volatility_threshold']
            if not isinstance(volatility_threshold, (int, float)) or volatility_threshold <= 0:
                return False

        return True

    def _validate_low_risk_engine(self, value: Any) -> bool:
        """验证低风险套利引擎配置"""
        if not isinstance(value, dict):
            return False

        # 验证 execution_timeout
        if 'execution_timeout' in value:
            execution_timeout = value['execution_timeout']
            if not isinstance(execution_timeout, (int, float)) or execution_timeout <= 0:
                return False

        return True

    # ==================== 热重载方法 ====================

    async def reload_config(self, section: Optional[str] = None) -> Dict[str, Any]:
        """重新加载配置

        Args:
            section: 配置节（None表示全部）

        Returns:
            重载结果
        """
        result = {
            'success': False,
            'message': '',
            'changes': []
        }

        with self.reload_lock:
            try:
                # 保存旧配置
                old_config = copy.deepcopy(self.current_config)

                # 重新加载配置
                new_config = self.config_manager.load_config()

                # 确定要更新的节
                sections_to_update = [section] if section else list(new_config.keys())

                changes = []

                for sec in sections_to_update:
                    if sec not in new_config:
                        continue

                    # 获取旧值和新值
                    old_value = old_config.get(sec)
                    new_value = new_config[sec]

                    # 验证新值
                    if not self.validator.validate(sec, new_value):
                        result['message'] = f'Validation failed for section: {sec}'
                        logger.warning(f"Config validation failed for {sec}")
                        return result

                    # 检查是否有变化
                    if old_value != new_value:
                        # 创建变更记录
                        change = ConfigChange(
                            section=sec,
                            old_value=copy.deepcopy(old_value),
                            new_value=copy.deepcopy(new_value),
                            changed_at=datetime.now().isoformat()
                        )
                        changes.append(change)

                        # 更新当前配置
                        self.current_config[sec] = new_value

                        # 添加到历史
                        self.config_history.append(change)
                        if len(self.config_history) > self.max_history_size:
                            self.config_history.pop(0)

                if changes:
                    # 通知变更
                    await self._notify_changes(changes)

                    result['success'] = True
                    result['message'] = f'Updated {len(changes)} section(s)'
                    result['changes'] = [
                        {
                            'section': change.section,
                            'changed_at': change.changed_at
                        }
                        for change in changes
                    ]

                    logger.info(f"Config hot reload completed: {len(changes)} sections updated")
                else:
                    result['success'] = True
                    result['message'] = 'No changes detected'

                return result

            except Exception as e:
                logger.error(f"Error during config reload: {e}")
                result['message'] = str(e)
                return result

    async def update_config(
        self,
        section: str,
        config_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新配置

        Args:
            section: 配置节
            config_data: 配置数据

        Returns:
            更新结果
        """
        result = {
            'success': False,
            'message': ''
        }

        with self.reload_lock:
            try:
                # 获取旧值
                old_value = copy.deepcopy(self.current_config.get(section))

                # 验证新值
                if not self.validator.validate(section, config_data):
                    result['message'] = f'Validation failed for section: {section}'
                    logger.warning(f"Config validation failed for {section}")
                    return result

                # 创建变更记录
                change = ConfigChange(
                    section=section,
                    old_value=old_value,
                    new_value=copy.deepcopy(config_data),
                    changed_at=datetime.now().isoformat(),
                    changed_by='api'
                )

                # 更新配置
                self.current_config[section] = config_data

                # 添加到历史
                self.config_history.append(change)
                if len(self.config_history) > self.max_history_size:
                    self.config_history.pop(0)

                # 通知变更
                await self._notify_changes([change])

                result['success'] = True
                result['message'] = f'Config section {section} updated'
                logger.info(f"Config section {section} updated via API")

                return result

            except Exception as e:
                logger.error(f"Error updating config: {e}")
                result['message'] = str(e)
                return result

    async def rollback_config(self, change_index: int) -> Dict[str, Any]:
        """回滚配置

        Args:
            change_index: 变更索引

        Returns:
            回滚结果
        """
        result = {
            'success': False,
            'message': ''
        }

        with self.reload_lock:
            try:
                if change_index < 0 or change_index >= len(self.config_history):
                    result['message'] = 'Invalid change index'
                    return result

                change = self.config_history[change_index]

                # 验证旧值
                if not self.validator.validate(change.section, change.old_value):
                    result['message'] = f'Validation failed for rollback of {change.section}'
                    return result

                # 执行回滚
                new_change = ConfigChange(
                    section=change.section,
                    old_value=copy.deepcopy(self.current_config.get(change.section)),
                    new_value=copy.deepcopy(change.old_value),
                    changed_at=datetime.now().isoformat(),
                    changed_by='rollback'
                )

                self.current_config[change.section] = change.old_value
                self.config_history.append(new_change)

                # 通知变更
                await self._notify_changes([new_change])

                result['success'] = True
                result['message'] = f'Config rolled back to change {change_index}'
                logger.info(f"Config rolled back to change {change_index}")

                return result

            except Exception as e:
                logger.error(f"Error rolling back config: {e}")
                result['message'] = str(e)
                return result

    def get_config_history(self) -> List[Dict[str, Any]]:
        """获取配置历史

        Returns:
            配置历史列表
        """
        return [
            {
                'index': idx,
                'section': change.section,
                'changed_at': change.changed_at,
                'changed_by': change.changed_by
            }
            for idx, change in enumerate(self.config_history)
        ]

    def get_current_config(self) -> Dict[str, Any]:
        """获取当前配置

        Returns:
            当前配置字典
        """
        return copy.deepcopy(self.current_config)

    def register_change_listener(self, listener: Callable) -> None:
        """注册变更监听器

        Args:
            listener: 监听器函数
        """
        if listener not in self.change_listeners:
            self.change_listeners.append(listener)
            logger.info("Config change listener registered")

    def unregister_change_listener(self, listener: Callable) -> None:
        """注销变更监听器

        Args:
            listener: 监听器函数
        """
        if listener in self.change_listeners:
            self.change_listeners.remove(listener)
            logger.info("Config change listener unregistered")

    async def _notify_changes(self, changes: List[ConfigChange]) -> None:
        """通知配置变更

        Args:
            changes: 变更列表
        """
        for listener in self.change_listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(changes)
                else:
                    listener(changes)
            except Exception as e:
                logger.error(f"Error notifying config change listener: {e}")


# 全局实例
_hot_reload: Optional[ConfigHotReload] = None


def get_hot_reload() -> Optional[ConfigHotReload]:
    """获取全局配置热加载实例

    Returns:
        配置热加载实例
    """
    return _hot_reload


def initialize_hot_reload(config_manager) -> ConfigHotReload:
    """初始化全局配置热加载

    Args:
        config_manager: 配置管理器实例

    Returns:
        配置热加载实例
    """
    global _hot_reload

    if _hot_reload is None:
        _hot_reload = ConfigHotReload(config_manager)
        logger.info("Global hot reload initialized")

    return _hot_reload
