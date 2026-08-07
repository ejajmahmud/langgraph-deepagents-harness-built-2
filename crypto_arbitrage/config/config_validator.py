"""配置验证器 - V5.1

验证系统配置的完整性和正确性。

核心功能：
1. 配置 Schema 验证
2. 版本兼容性检查
3. 数据类型验证
4. 必需字段检查
5. 配置建议生成
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationErrorLevel(Enum):
    """验证错误级别"""
    CRITICAL = "critical"  # 阻塞系统启动
    ERROR = "error"  # 影响系统功能
    WARNING = "warning"  # 可能导致问题
    INFO = "info"  # 建议性提示


@dataclass
class ValidationError:
    """验证错误

    Attributes:
        level: 错误级别
        field: 字段路径 (例如: "system.version")
        message: 错误消息
        suggestion: 修复建议
    """
    level: ValidationErrorLevel
    field: str
    message: str
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """验证结果

    Attributes:
        is_valid: 是否通过验证
        errors: 错误列表
        warnings: 警告列表
        suggestions: 建议列表
    """
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    def add_error(self, level: ValidationErrorLevel, field: str, message: str, suggestion: str = None):
        """添加错误"""
        error = ValidationError(level, field, message, suggestion)

        if level == ValidationErrorLevel.CRITICAL or level == ValidationErrorLevel.ERROR:
            self.errors.append(error)
        elif level == ValidationErrorLevel.WARNING:
            self.warnings.append(error)
        else:
            self.suggestions.append(message)

        # 更新验证状态
        if level in [ValidationErrorLevel.CRITICAL, ValidationErrorLevel.ERROR]:
            self.is_valid = False


class ConfigSchema:
    """配置 Schema 定义"""

    # 系统版本要求
    MIN_VERSION = "5.0"
    MAX_VERSION = "5.9"

    # 必需字段
    REQUIRED_FIELDS: Set[str] = {
        "system",
        "system.name",
        "system.version",
        "system.mode",
        "model",
        "model.provider",
        "model.model",
        "exchanges",
        "risk_management",
        "strategies",
    }

    # V5.0 新增必需字段
    V5_REQUIRED_FIELDS: Set[str] = {
        "enhanced_low_risk_engine",
        "enhanced_low_risk_engine.enabled",
        "performance_v5",
        "performance_v5.lazy_loading",
    }

    # 字段类型定义
    FIELD_TYPES: Dict[str, type] = {
        "system.version": str,
        "system.mode": str,
        "model.temperature": float,
        "model.max_tokens": int,
        "risk_management.max_daily_loss": (int, float),
        "enhanced_low_risk_engine.enabled": bool,
        "performance_v5.lazy_loading.enabled": bool,
    }

    # 枚举值验证
    ENUM_VALUES: Dict[str, List[str]] = {
        "system.mode": ["simulation", "paper_trading", "live_trading"],
        "model.provider": ["anthropic", "openai", "google", "xai", "openrouter", "ollama"],
    }

    # 数值范围验证
    VALUE_RANGES: Dict[str, tuple] = {
        "model.temperature": (0.0, 2.0),
        "model.max_tokens": (1, 128000),
        "risk_management.max_daily_loss": (0, 100000),
        "enhanced_low_risk_engine.decision_confidence_threshold": (0.0, 1.0),
    }


class ConfigValidator:
    """配置验证器"""

    def __init__(self, schema: Optional[ConfigSchema] = None):
        """初始化配置验证器

        Args:
            schema: 配置 Schema，默认使用 ConfigSchema
        """
        self.schema = schema or ConfigSchema()
        self.current_version = "5.1"

    def validate_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证配置完整性

        Args:
            config: 配置字典

        Returns:
            验证结果
        """
        result = ValidationResult(is_valid=True)

        logger.info("开始配置验证...")

        # 1. 检查必需字段
        self._check_required_fields(config, result)

        # 2. 检查版本兼容性
        self._check_version_compatibility(config, result)

        # 3. 检查数据类型
        self._check_field_types(config, result)

        # 4. 检查枚举值
        self._check_enum_values(config, result)

        # 5. 检查数值范围
        self._check_value_ranges(config, result)

        # 6. 检查业务逻辑
        self._check_business_logic(config, result)

        # 7. 生成优化建议
        self._generate_suggestions(config, result)

        # 记录验证结果
        if result.is_valid:
            logger.info("✅ 配置验证通过")
            if result.warnings:
                logger.warning(f"⚠️ 发现 {len(result.warnings)} 个警告")
        else:
            logger.error(f"❌ 配置验证失败: {len(result.errors)} 个错误")

        return result

    def _check_required_fields(self, config: Dict[str, Any], result: ValidationResult):
        """检查必需字段"""
        # 基础必需字段
        for field_path in self.schema.REQUIRED_FIELDS:
            if not self._get_nested_value(config, field_path):
                result.add_error(
                    ValidationErrorLevel.CRITICAL,
                    field_path,
                    f"缺少必需字段: {field_path}",
                    f"在配置文件中添加 {field_path}"
                )

        # V5.0 必需字段
        for field_path in self.schema.V5_REQUIRED_FIELDS:
            if not self._get_nested_value(config, field_path):
                result.add_error(
                    ValidationErrorLevel.ERROR,
                    field_path,
                    f"V5.0 缺少必需字段: {field_path}",
                    f"添加 V5.0 配置项: {field_path}"
                )

    def _check_version_compatibility(self, config: Dict[str, Any], result: ValidationResult):
        """检查版本兼容性"""
        system_config = config.get("system", {})
        version = system_config.get("version", "")

        if not version:
            result.add_error(
                ValidationErrorLevel.CRITICAL,
                "system.version",
                "缺少系统版本号",
                "设置 system.version 为当前版本 (例如: 5.1)"
            )
            return

        # 检查版本格式
        try:
            major, minor = map(int, version.split('.'))
        except (ValueError, AttributeError):
            result.add_error(
                ValidationErrorLevel.ERROR,
                "system.version",
                f"版本号格式错误: {version}",
                "使用标准版本号格式: 主版本.次版本 (例如: 5.1)"
            )
            return

        # 检查版本范围
        try:
            min_major, min_minor = map(int, self.schema.MIN_VERSION.split('.'))
            max_major, max_minor = map(int, self.schema.MAX_VERSION.split('.'))

            current = major * 100 + minor
            min_ver = min_major * 100 + min_minor
            max_ver = max_major * 100 + max_minor

            if current < min_ver:
                result.add_error(
                    ValidationErrorLevel.ERROR,
                    "system.version",
                    f"版本过低: {version} (最低要求: {self.schema.MIN_VERSION})",
                    f"更新 system.version 到至少 {self.schema.MIN_VERSION}"
                )
            elif current > max_ver:
                result.add_error(
                    ValidationErrorLevel.WARNING,
                    "system.version",
                    f"版本过高: {version} (最高支持: {self.schema.MAX_VERSION})",
                    f"考虑降级到 {self.schema.MAX_VERSION} 或更新系统"
                )

        except (ValueError, AttributeError) as e:
            logger.warning(f"版本比较失败: {e}")

    def _check_field_types(self, config: Dict[str, Any], result: ValidationResult):
        """检查数据类型"""
        for field_path, expected_type in self.schema.FIELD_TYPES.items():
            value = self._get_nested_value(config, field_path)

            if value is None:
                continue  # 缺失字段在其他地方检查

            # 处理多种允许的类型
            if isinstance(expected_type, tuple):
                if not isinstance(value, expected_type):
                    result.add_error(
                        ValidationErrorLevel.ERROR,
                        field_path,
                        f"字段类型错误: {type(value).__name__} (期望: {'或'.join(t.__name__ for t in expected_type)})",
                        f"将 {field_path} 的值转换为正确的类型"
                    )
            else:
                if not isinstance(value, expected_type):
                    result.add_error(
                        ValidationErrorLevel.ERROR,
                        field_path,
                        f"字段类型错误: {type(value).__name__} (期望: {expected_type.__name__})",
                        f"将 {field_path} 的值转换为 {expected_type.__name__}"
                    )

    def _check_enum_values(self, config: Dict[str, Any], result: ValidationResult):
        """检查枚举值"""
        for field_path, valid_values in self.schema.ENUM_VALUES.items():
            value = self._get_nested_value(config, field_path)

            if value is None:
                continue

            if value not in valid_values:
                result.add_error(
                    ValidationErrorLevel.ERROR,
                    field_path,
                    f"字段值无效: {value} (有效值: {', '.join(valid_values)})",
                    f"将 {field_path} 设置为以下值之一: {', '.join(valid_values)}"
                )

    def _check_value_ranges(self, config: Dict[str, Any], result: ValidationResult):
        """检查数值范围"""
        for field_path, (min_val, max_val) in self.schema.VALUE_RANGES.items():
            value = self._get_nested_value(config, field_path)

            if value is None:
                continue

            if not isinstance(value, (int, float)):
                continue  # 类型错误在其他地方检查

            if value < min_val or value > max_val:
                result.add_error(
                    ValidationErrorLevel.ERROR,
                    field_path,
                    f"数值超出范围: {value} (有效范围: {min_val}-{max_val})",
                    f"将 {field_path} 的值调整到 {min_val}-{max_val} 范围内"
                )

    def _check_business_logic(self, config: Dict[str, Any], result: ValidationResult):
        """检查业务逻辑"""
        # 检查 Memo0 配置
        mem0_config = config.get("mem0", {})
        if not mem0_config.get("api_key"):
            result.add_error(
                ValidationErrorLevel.WARNING,
                "mem0.api_key",
                "Memo0 API Key 未配置，系统将使用 SQLite 降级模式",
                "设置 MEM0_API_KEY 环境变量或在配置文件中设置 mem0.api_key"
            )

        # 检查交易所配置
        exchanges = config.get("exchanges", {})
        enabled_exchanges = [name for name, cfg in exchanges.items() if cfg.get("enabled", False)]

        if not enabled_exchanges:
            result.add_error(
                ValidationErrorLevel.ERROR,
                "exchanges",
                "没有启用的交易所",
                "至少启用一个交易所 (binance/okx/huobi)"
            )

        # 检查策略配置
        strategies = config.get("strategies", {})
        enabled_strategies = [name for name, cfg in strategies.items() if cfg.get("enabled", False)]

        if not enabled_strategies:
            result.add_error(
                ValidationErrorLevel.ERROR,
                "strategies",
                "没有启用的交易策略",
                "至少启用一个交易策略"
            )

    def _generate_suggestions(self, config: Dict[str, Any], result: ValidationResult):
        """生成优化建议"""
        # 建议启用增强版引擎
        enhanced_config = config.get("enhanced_low_risk_engine", {})
        if not enhanced_config.get("enabled"):
            result.suggestions.append(
                "建议启用 enhanced_low_risk_engine 以获得更好的风险预测和智能决策功能"
            )

        # 建议配置 Memo0
        if not config.get("mem0", {}).get("api_key"):
            result.suggestions.append(
                "建议配置 Memo0 API Key 以启用 AI 搜索和知识关联功能"
            )

        # 建议启用性能优化
        perf_v5 = config.get("performance_v5", {})
        if not perf_v5.get("lazy_loading", {}).get("enabled"):
            result.suggestions.append(
                "建议启用 performance_v5.lazy_loading 以提升系统启动速度"
            )

    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """获取嵌套字典中的值

        Args:
            data: 字典数据
            path: 字段路径 (例如: "system.version")

        Returns:
            字段值，如果不存在则返回 None
        """
        keys = path.split('.')
        value = data

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None

        return value


# 全局单例
_validator: Optional[ConfigValidator] = None


def get_config_validator() -> ConfigValidator:
    """获取配置验证器实例

    Returns:
        ConfigValidator 实例
    """
    global _validator

    if _validator is None:
        _validator = ConfigValidator()

    return _validator


def validate_config(config: Dict[str, Any]) -> ValidationResult:
    """验证配置

    Args:
        config: 配置字典

    Returns:
        验证结果
    """
    validator = get_config_validator()
    return validator.validate_config(config)