"""生产环境集成模块 V70.0 - Phase 14

核心功能：
- ConfigurationValidator: 配置验证器
- ErrorHandler: 错误处理器
- ProductionConfig: 生产配置
- CacheManager: 缓存管理器
- BatchProcessor: 批处理器
- HealthChecker: 健康检查器
- SystemMetrics: 系统指标收集

创建时间：2026-05-08 22:25
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import time
import json


# ============ 枚举定义 ============

class ValidationLevel(Enum):
    """验证级别"""
    STRICT = "strict"      # 严格模式
    NORMAL = "normal"     # 正常模式
    LENIENT = "lenient"  # 宽松模式


class HealthStatus(Enum):
    """健康状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ErrorSeverity(Enum):
    """错误严重程度"""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class MetricType(Enum):
    """指标类型"""
    COUNTER = "counter"           # 计数器
    GAUGE = "gauge"             # 仪表
    HISTOGRAM = "histogram"      # 直方图
    TIMER = "timer"             # 计时器


# ============ 数据结构 ============

@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    validated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ErrorRecord:
    """错误记录"""
    error_id: str
    severity: ErrorSeverity
    message: str
    module: str
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False


@dataclass
class ProductionConfig:
    """生产配置"""
    mode: str = "paper"                    # 交易模式: paper/live
    max_positions: int = 5                # 最大持仓数
    max_position_size: float = 0.1        # 单笔最大仓位比例
    stop_loss_pct: float = 0.02           # 止损比例
    take_profit_pct: float = 0.05          # 止盈比例
    enable_circuit_breaker: bool = True      # 启用熔断器
    circuit_breaker_threshold: float = 0.05  # 熔断阈值
    circuit_breaker_timeout: int = 300     # 熔断超时(秒)
    enable_cache: bool = True              # 启用缓存
    cache_ttl: int = 60                  # 缓存TTL(秒)
    enable_batch_processing: bool = True  # 启用批处理
    batch_size: int = 100                # 批处理大小
    batch_timeout: int = 5                # 批处理超时(秒)
    health_check_interval: int = 60      # 健康检查间隔(秒)
    metrics_retention_days: int = 30     # 指标保留天数


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    expires_at: float
    hits: int = 0


@dataclass
class MetricValue:
    """指标值"""
    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class HealthReport:
    """健康报告"""
    status: HealthStatus
    checks: Dict[str, bool] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


# ============ ConfigurationValidator ============

class ConfigurationValidator:
    """配置验证器"""

    def __init__(self, level: ValidationLevel = ValidationLevel.NORMAL):
        self.level = level
        self._validators: Dict[str, Callable] = {}
        self._register_default_validators()

    def _register_default_validators(self):
        """注册默认验证器"""
        self._validators = {
            "trading_mode": self._validate_trading_mode,
            "position_size": self._validate_position_size,
            "risk_limits": self._validate_risk_limits,
            "api_keys": self._validate_api_keys,
            "exchanges": self._validate_exchanges,
        }

    def _validate_trading_mode(self, config: ProductionConfig) -> ValidationResult:
        """验证交易模式"""
        valid_modes = ["paper", "live", "backtest"]
        if config.mode not in valid_modes:
            return ValidationResult(
                is_valid=False,
                errors=[f"Invalid trading mode: {config.mode}"]
            )
        return ValidationResult(is_valid=True)

    def _validate_position_size(self, config: ProductionConfig) -> ValidationResult:
        """验证仓位大小"""
        errors = []
        warnings = []

        if config.max_position_size > 0.5:
            errors.append("Max position size exceeds 50%")
        elif config.max_position_size > 0.3:
            warnings.append("Max position size is high (>30%)")

        if config.max_positions > 20:
            errors.append("Too many max positions (>20)")
        elif config.max_positions > 10:
            warnings.append("High max positions (>10)")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def _validate_risk_limits(self, config: ProductionConfig) -> ValidationResult:
        """验证风险限制"""
        errors = []
        warnings = []

        if config.stop_loss_pct <= 0:
            errors.append("Stop loss must be positive")
        elif config.stop_loss_pct > 0.2:
            warnings.append("Stop loss >20% is aggressive")

        if config.take_profit_pct <= config.stop_loss_pct:
            errors.append("Take profit must exceed stop loss")

        if config.circuit_breaker_threshold > 0.2:
            warnings.append("Circuit breaker threshold >20%")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def _validate_api_keys(self, config: Dict[str, Any]) -> ValidationResult:
        """验证API密钥"""
        # 实际实现会检查环境变量中的API密钥
        return ValidationResult(is_valid=True)

    def _validate_exchanges(self, config: List[str]) -> ValidationResult:
        """验证交易所"""
        valid_exchanges = ["binance", "okx", "bybit", "coinbase", "kraken"]
        errors = []

        for exchange in config:
            if exchange not in valid_exchanges:
                errors.append(f"Unknown exchange: {exchange}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )

    def validate(self, config: ProductionConfig) -> ValidationResult:
        """验证配置"""
        all_errors = []
        all_warnings = []

        # 验证交易模式
        if config.mode not in ["paper", "live", "backtest"]:
            all_errors.append(f"Invalid mode: {config.mode}")

        # 验证仓位大小
        if config.max_position_size > 0.5:
            all_errors.append("Max position size > 50%")
        elif config.max_position_size > 0.3:
            all_warnings.append("Max position size > 30%")

        if config.max_positions > 20:
            all_errors.append("Too many positions")
        elif config.max_positions > 10:
            all_warnings.append("High position count")

        # 验证风控参数
        if config.stop_loss_pct <= 0:
            all_errors.append("Stop loss must be positive")
        elif config.stop_loss_pct > 0.2:
            all_warnings.append("Stop loss >20%")

        if config.take_profit_pct <= config.stop_loss_pct:
            all_errors.append("Take profit must exceed stop loss")

        # 验证熔断器
        if config.circuit_breaker_threshold > 0.2:
            all_warnings.append("Circuit breaker >20%")

        return ValidationResult(
            is_valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings
        )


# ============ ErrorHandler ============

class ErrorHandler:
    """错误处理器"""

    def __init__(self):
        self._errors: List[ErrorRecord] = []
        self._handlers: Dict[ErrorSeverity, List[Callable]] = {
            ErrorSeverity.CRITICAL: [],
            ErrorSeverity.ERROR: [],
            ErrorSeverity.WARNING: [],
            ErrorSeverity.INFO: [],
        }
        self._error_count = 0

    def register_handler(self, severity: ErrorSeverity, handler: Callable):
        """注册处理器"""
        self._handlers[severity].append(handler)

    def handle_error(
        self,
        message: str,
        module: str,
        severity: ErrorSeverity,
        details: Optional[Dict[str, Any]] = None
    ) -> ErrorRecord:
        """处理错误"""
        self._error_count += 1
        record = ErrorRecord(
            error_id=f"ERR_{self._error_count:06d}",
            severity=severity,
            message=message,
            module=module,
            details=details or {}
        )

        self._errors.append(record)

        # 调用注册的处理器
        for handler in self._handlers[severity]:
            try:
                handler(record)
            except Exception:
                pass

        return record

    def get_errors(
        self,
        severity: Optional[ErrorSeverity] = None,
        unresolved_only: bool = False
    ) -> List[ErrorRecord]:
        """获取错误列表"""
        errors = self._errors

        if severity:
            errors = [e for e in errors if e.severity == severity]

        if unresolved_only:
            errors = [e for e in errors if not e.resolved]

        return errors

    def resolve_error(self, error_id: str) -> bool:
        """解决错误"""
        for error in self._errors:
            if error.error_id == error_id:
                error.resolved = True
                return True
        return False

    def get_error_summary(self) -> Dict[str, int]:
        """获取错误摘要"""
        return {
            "total": len(self._errors),
            "critical": len([e for e in self._errors if e.severity == ErrorSeverity.CRITICAL]),
            "error": len([e for e in self._errors if e.severity == ErrorSeverity.ERROR]),
            "warning": len([e for e in self._errors if e.severity == ErrorSeverity.WARNING]),
            "info": len([e for e in self._errors if e.severity == ErrorSeverity.INFO]),
            "unresolved": len([e for e in self._errors if not e.resolved]),
        }


# ============ CacheManager ============

class CacheManager:
    """缓存管理器"""

    def __init__(self, default_ttl: int = 60):
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        entry = self._cache.get(key)

        if entry is None:
            self._misses += 1
            return None

        if time.time() > entry.expires_at:
            del self._cache[key]
            self._misses += 1
            return None

        entry.hits += 1
        self._hits += 1
        return entry.value

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置缓存"""
        ttl = ttl or self.default_ttl
        self._cache[key] = CacheEntry(
            key=key,
            value=value,
            expires_at=time.time() + ttl
        )

    def delete(self, key: str) -> bool:
        """删除缓存"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self):
        """清空缓存"""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    def cleanup(self):
        """清理过期缓存"""
        now = time.time()
        expired = [k for k, v in self._cache.items() if now > v.expires_at]
        for key in expired:
            del self._cache[key]

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0

        return {
            "size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
        }


# ============ BatchProcessor ============

class BatchProcessor:
    """批处理器"""

    def __init__(self, batch_size: int = 100, timeout: int = 5):
        self.batch_size = batch_size
        self.timeout = timeout
        self._queue: List[Any] = []
        self._last_processed = time.time()
        self._processed_count = 0

    def add(self, item: Any) -> int:
        """添加项目到队列"""
        self._queue.append(item)
        return len(self._queue)

    def add_batch(self, items: List[Any]) -> int:
        """批量添加"""
        self._queue.extend(items)
        return len(self._queue)

    def process(self, handler) -> Optional[Any]:
        """处理队列"""
        if not self._queue:
            return None

        # 获取需要处理的项目
        batch = self._queue[:self.batch_size]
        self._queue = self._queue[self.batch_size:]

        # 调用处理器
        result = handler(batch)
        self._processed_count += len(batch)
        self._last_processed = time.time()

        return result

    def should_process(self) -> bool:
        """检查是否应该处理"""
        if len(self._queue) >= self.batch_size:
            return True

        if self._queue and time.time() - self._last_processed > self.timeout:
            return True

        return False

    def get_size(self) -> int:
        """获取队列大小"""
        return len(self._queue)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计"""
        return {
            "queue_size": len(self._queue),
            "total_processed": self._processed_count,
            "last_processed": self._last_processed,
        }


# ============ HealthChecker ============

class HealthChecker:
    """健康检查器"""

    def __init__(self, check_interval: int = 60):
        self.check_interval = check_interval
        self._checkers: Dict = {}
        self._last_check = time.time()
        self._last_report = None

    def register_checker(self, name: str, checker):
        """注册检查器"""
        self._checkers[name] = checker

    def check(self) -> HealthReport:
        """执行健康检查"""
        results = {}
        metrics = {}
        errors = []

        for name, checker in self._checkers.items():
            try:
                results[name] = checker()
            except Exception as e:
                results[name] = False
                errors.append(f"{name}: {str(e)}")

        # 确定整体状态
        if all(results.values()):
            status = HealthStatus.HEALTHY
        elif any(results.values()):
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.UNHEALTHY

        # 基本指标
        metrics["check_count"] = len(results)
        metrics["pass_count"] = sum(1 for v in results.values() if v)

        report = HealthReport(
            status=status,
            checks=results,
            metrics=metrics,
            errors=errors
        )

        self._last_check = time.time()
        self._last_report = report

        return report

    def get_last_report(self) -> Optional[HealthReport]:
        """获取上次报告"""
        return self._last_report

    def is_healthy(self) -> bool:
        """检查是否健康"""
        if self._last_report:
            return self._last_report.status == HealthStatus.HEALTHY
        return False


# ============ SystemMetrics ============

class SystemMetrics:
    """系统指标收集器"""

    def __init__(self):
        self._metrics: Dict[str, List[MetricValue]] = {}
        self._counters: Dict[str, float] = {}
        self._gauges: Dict[str, float] = {}
        self._timers: Dict[str, List[float]] = {}

    def increment_counter(self, name: str, value: float = 1.0):
        """增加计数器"""
        self._counters[name] = self._counters.get(name, 0) + value

        self._metrics.setdefault(name, []).append(MetricValue(
            name=name,
            value=self._counters[name],
            metric_type=MetricType.COUNTER
        ))

    def set_gauge(self, name: str, value: float):
        """设置仪表值"""
        self._gauges[name] = value

        self._metrics.setdefault(name, []).append(MetricValue(
            name=name,
            value=value,
            metric_type=MetricType.GAUGE
        ))

    def record_timer(self, name: str, duration: float):
        """记录计时器"""
        self._timers.setdefault(name, []).append(duration)

        self._metrics.setdefault(name, []).append(MetricValue(
            name=name,
            value=duration,
            metric_type=MetricType.TIMER
        ))

    def get_counter(self, name: str) -> float:
        """获取计数器值"""
        return self._counters.get(name, 0)

    def get_gauge(self, name: str) -> Optional[float]:
        """获取仪表值"""
        return self._gauges.get(name)

    def get_timer_stats(self, name: str) -> Optional[Dict[str, float]]:
        """获取计时器统计"""
        values = self._timers.get(name)
        if not values:
            return None

        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
        }

    def get_all_metrics(self) -> Dict[str, Any]:
        """获取所有指标"""
        return {
            "counters": self._counters.copy(),
            "gauges": self._gauges.copy(),
            "timers": {k: self.get_timer_stats(k) for k in self._timers},
        }

    def reset(self):
        """重置指标"""
        self._metrics.clear()
        self._counters.clear()
        self._gauges.clear()
        self._timers.clear()


# ============ 全局函数 ============

# 全局实例
_validator: Optional[ConfigurationValidator] = None
_error_handler: Optional[ErrorHandler] = None
_cache_manager: Optional[CacheManager] = None
_batch_processor: Optional[BatchProcessor] = None
_health_checker: Optional[HealthChecker] = None
_system_metrics: Optional[SystemMetrics] = None


def get_configuration_validator() -> ConfigurationValidator:
    """获取配置验证器"""
    global _validator
    if _validator is None:
        _validator = ConfigurationValidator()
    return _validator


def initialize_configuration_validator(level: ValidationLevel = ValidationLevel.NORMAL):
    """初始化配置验证器"""
    global _validator
    _validator = ConfigurationValidator(level)
    return _validator


def get_error_handler() -> ErrorHandler:
    """获取错误处理器"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


def initialize_error_handler():
    """初始化错误处理器"""
    global _error_handler
    _error_handler = ErrorHandler()
    return _error_handler


def get_cache_manager() -> CacheManager:
    """获取缓存管��器"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def initialize_cache_manager(default_ttl: int = 60):
    """初始化缓存管理器"""
    global _cache_manager
    _cache_manager = CacheManager(default_ttl)
    return _cache_manager


def get_batch_processor() -> BatchProcessor:
    """获取批处理器"""
    global _batch_processor
    if _batch_processor is None:
        _batch_processor = BatchProcessor()
    return _batch_processor


def initialize_batch_processor(batch_size: int = 100, timeout: int = 5):
    """初始化批处理器"""
    global _batch_processor
    _batch_processor = BatchProcessor(batch_size, timeout)
    return _batch_processor


def get_health_checker() -> HealthChecker:
    """获取健康检查器"""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker


def initialize_health_checker(check_interval: int = 60):
    """初始化健康检查器"""
    global _health_checker
    _health_checker = HealthChecker(check_interval)
    return _health_checker


def get_system_metrics() -> SystemMetrics:
    """获取系统指标"""
    global _system_metrics
    if _system_metrics is None:
        _system_metrics = SystemMetrics()
    return _system_metrics


def initialize_system_metrics():
    """初始化系统指标"""
    global _system_metrics
    _system_metrics = SystemMetrics()
    return _system_metrics


def create_production_config(**kwargs) -> ProductionConfig:
    """创建生产配置"""
    return ProductionConfig(**kwargs)


# ============ 版本信息 ============

__version__ = "1.6.0"
__phase__ = "Phase 14: 生产环境集成"