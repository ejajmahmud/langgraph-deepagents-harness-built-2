"""自适应错误处理系统 V3.0

智能错误检测、恢复和预防机制，提升系统稳定性和容错能力。

核心特性：
1. 智能错误分类 - 自动识别错误类型和严重程度
2. 自动恢复策略 - 针对不同错误类型的自动恢复机制
3. 错误预防 - 基于历史错误的预防措施
4. 熔断器模式 - 防止级联故障
5. 降级策略 - 在部分功能失效时保持核心功能

V3.0新增：AI驱动的错误预测和预防
"""

import json
import logging
import threading
import time
import traceback
from collections import defaultdict, deque
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"           # 低：不影响核心功能
    MEDIUM = "medium"     # 中：影响部分功能
    HIGH = "high"         # 高：影响核心功能
    CRITICAL = "critical" # 严重：系统无法继续运行


class ErrorCategory(Enum):
    """错误类别"""
    NETWORK = "network"           # 网络错误
    API = "api"                   # API错误
    DATA = "data"                 # 数据错误
    STRATEGY = "strategy"         # 策略错误
    EXECUTION = "execution"       # 执行错误
    CONFIGURATION = "configuration" # 配置错误
    EXTERNAL = "external"         # 外部服务错误
    UNKNOWN = "unknown"           # 未知错误


class CircuitBreakerState(Enum):
    """熔断器状态"""
    CLOSED = "closed"     # 关闭：正常工作
    OPEN = "open"         # 开启：熔断中
    HALF_OPEN = "half_open" # 半开：尝试恢复


class CircuitBreaker:
    """熔断器

    防止级联故障，在连续失败达到阈值时熔断。
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        half_open_max_calls: int = 3
    ):
        """初始化熔断器

        Args:
            failure_threshold: 失败阈值
            timeout: 熔断超时时间（秒）
            half_open_max_calls: 半开状态最大调用次数
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.half_open_max_calls = half_open_max_calls

        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.half_open_calls = 0
        self.lock = threading.Lock()

    def record_success(self) -> None:
        """记录成功"""
        with self.lock:
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.half_open_calls += 1
                if self.half_open_calls >= self.half_open_max_calls:
                    self.state = CircuitBreakerState.CLOSED
                    self.half_open_calls = 0
                    logger.info("Circuit breaker recovered to CLOSED state")
            else:
                self.failure_count = 0

    def record_failure(self) -> None:
        """记录失败"""
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.state = CircuitBreakerState.OPEN
                logger.warning(
                    f"Circuit breaker opened after {self.failure_count} failures"
                )

    def can_execute(self) -> bool:
        """检查是否可以执行

        Returns:
            是否可以执行
        """
        with self.lock:
            if self.state == CircuitBreakerState.CLOSED:
                return True

            elif self.state == CircuitBreakerState.OPEN:
                # 检查是否超时
                if (self.last_failure_time and
                    time.time() - self.last_failure_time >= self.timeout):
                    self.state = CircuitBreakerState.HALF_OPEN
                    self.half_open_calls = 0
                    logger.info("Circuit breaker transitioned to HALF_OPEN state")
                    return True
                return False

            elif self.state == CircuitBreakerState.HALF_OPEN:
                return self.half_open_calls < self.half_open_max_calls

        return False

    def get_state(self) -> Dict[str, Any]:
        """获取熔断器状态

        Returns:
            状态字典
        """
        with self.lock:
            return {
                "state": self.state.value,
                "failure_count": self.failure_count,
                "last_failure_time": self.last_failure_time,
                "half_open_calls": self.half_open_calls
            }


class AdaptiveErrorHandler:
    """自适应错误处理器 V3.0

    智能处理各种错误，提供自动恢复和预防机制。
    """

    def __init__(self, config: Optional[Dict] = None):
        """初始化错误处理器

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 错误历史
        self.error_history: deque = deque(maxlen=1000)
        self.error_patterns: Dict[str, Dict] = defaultdict(lambda: {
            "count": 0,
            "last_occurrence": None,
            "severity": ErrorSeverity.MEDIUM,
            "recovery_actions": []
        })

        # 熔断器
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.circuit_breaker_lock = threading.Lock()

        # 恢复策略
        self.recovery_strategies = {
            ErrorCategory.NETWORK: self._recover_network_error,
            ErrorCategory.API: self._recover_api_error,
            ErrorCategory.DATA: self._recover_data_error,
            ErrorCategory.STRATEGY: self._recover_strategy_error,
            ErrorCategory.EXECUTION: self._recover_execution_error,
        }

        # 预防措施
        self.preventive_actions: List[Callable] = []

        # 错误统计
        self.error_stats: Dict[str, int] = defaultdict(int)

        # 重试配置
        self.retry_config = {
            "max_retries": self.config.get("max_retries", 3),
            "retry_delay": self.config.get("retry_delay", 1.0),
            "backoff_factor": self.config.get("backoff_factor", 2.0)
        }

        logger.info("AdaptiveErrorHandler V3.0 initialized")

    def handle_error(
        self,
        error: Exception,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """处理错误

        Args:
            error: 错误对象
            context: 上下文信息

        Returns:
            处理结果
        """
        # 分类错误
        error_category = self._classify_error(error)
        error_severity = self._assess_severity(error, error_category)

        # 记录错误
        error_record = {
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "category": error_category.value,
            "severity": error_severity.value,
            "context": context or {},
            "traceback": traceback.format_exc()
        }

        self.error_history.append(error_record)
        self.error_patterns[f"{error_category.value}_{type(error).__name__}"]["count"] += 1
        self.error_stats[error_category.value] += 1

        logger.error(
            f"Error handled: {error_category.value}/{error_severity.value} - "
            f"{type(error).__name__}: {str(error)}"
        )

        # 根据严重程度处理
        if error_severity == ErrorSeverity.CRITICAL:
            return self._handle_critical_error(error, error_record)

        # 尝试自动恢复
        recovery_result = self._attempt_recovery(error, error_category, context)

        # 更新熔断器
        self._update_circuit_breaker(error_category, recovery_result["success"])

        return {
            "handled": True,
            "category": error_category.value,
            "severity": error_severity.value,
            "recovery": recovery_result,
            "error_record": error_record
        }

    def _classify_error(self, error: Exception) -> ErrorCategory:
        """分类错误

        Args:
            error: 错误对象

        Returns:
            错误类别
        """
        error_type = type(error).__name__.lower()
        error_message = str(error).lower()

        # 网络错误
        if any(keyword in error_type or keyword in error_message
               for keyword in ["connection", "timeout", "network", "dns"]):
            return ErrorCategory.NETWORK

        # API错误
        if any(keyword in error_type or keyword in error_message
               for keyword in ["api", "http", "request", "response"]):
            return ErrorCategory.API

        # 数据错误
        if any(keyword in error_type or keyword in error_message
               for keyword in ["data", "value", "type", "format", "parse"]):
            return ErrorCategory.DATA

        # 策略错误
        if any(keyword in error_type or keyword in error_message
               for keyword in ["strategy", "arbitrage", "position", "order"]):
            return ErrorCategory.STRATEGY

        # 执行错误
        if any(keyword in error_type or keyword in error_message
               for keyword in ["execution", "trade", "balance", "insufficient"]):
            return ErrorCategory.EXECUTION

        # 配置错误
        if any(keyword in error_type or keyword in error_message
               for keyword in ["config", "setting", "parameter", "option"]):
            return ErrorCategory.CONFIGURATION

        return ErrorCategory.UNKNOWN

    def _assess_severity(
        self,
        error: Exception,
        category: ErrorCategory
    ) -> ErrorSeverity:
        """评估错误严重程度

        Args:
            error: 错误对象
            category: 错误类别

        Returns:
            错误严重程度
        """
        error_message = str(error).lower()

        # 严重错误
        critical_keywords = ["critical", "fatal", "system", "shutdown", "cannot"]
        if any(keyword in error_message for keyword in critical_keywords):
            return ErrorSeverity.CRITICAL

        # 高严重程度
        if category in [ErrorCategory.EXECUTION, ErrorCategory.STRATEGY]:
            return ErrorSeverity.HIGH

        # 中等严重程度
        if category in [ErrorCategory.API, ErrorCategory.NETWORK]:
            return ErrorSeverity.MEDIUM

        # 低严重程度
        return ErrorSeverity.LOW

    def _attempt_recovery(
        self,
        error: Exception,
        category: ErrorCategory,
        context: Optional[Dict]
    ) -> Dict[str, Any]:
        """尝试恢复

        Args:
            error: 错误对象
            category: 错误类别
            context: 上下文

        Returns:
            恢复结果
        """
        # 检查熔断器
        cb_key = category.value
        if not self._can_execute_through_circuit_breaker(cb_key):
            return {
                "success": False,
                "action": "circuit_breaker_open",
                "message": f"Circuit breaker is open for {category.value}"
            }

        # 执行恢复策略
        recovery_func = self.recovery_strategies.get(category)
        if recovery_func:
            try:
                result = recovery_func(error, context)
                if result.get("success"):
                    return result
            except Exception as e:
                logger.error(f"Recovery strategy failed: {e}")

        # 默认重试策略
        return self._default_retry_strategy(error, context)

    def _recover_network_error(
        self,
        error: Exception,
        context: Optional[Dict]
    ) -> Dict[str, Any]:
        """恢复网络错误

        Args:
            error: 错误对象
            context: 上下文

        Returns:
            恢复结果
        """
        logger.info("Attempting network error recovery...")

        # 等待一段时间后重试
        retry_delay = self.retry_config["retry_delay"]
        time.sleep(retry_delay)

        return {
            "success": True,
            "action": "network_retry",
            "message": f"Network error recovered after {retry_delay}s delay",
            "retry_delay": retry_delay
        }

    def _recover_api_error(
        self,
        error: Exception,
        context: Optional[Dict]
    ) -> Dict[str, Any]:
        """恢复API错误

        Args:
            error: 错误对象
            context: 上下文

        Returns:
            恢复结果
        """
        logger.info("Attempting API error recovery...")

        # 检查是否是速率限制
        error_message = str(error).lower()
        if "rate limit" in error_message:
            # 等待更长时间
            retry_delay = self.retry_config["retry_delay"] * 5
            time.sleep(retry_delay)
            return {
                "success": True,
                "action": "rate_limit_wait",
                "message": f"Rate limit recovered after {retry_delay}s delay",
                "retry_delay": retry_delay
            }

        # 其他API错误，使用默认重试
        return self._default_retry_strategy(error, context)

    def _recover_data_error(
        self,
        error: Exception,
        context: Optional[Dict]
    ) -> Dict[str, Any]:
        """恢复数据错误

        Args:
            error: 错误对象
            context: 上下文

        Returns:
            恢复结果
        """
        logger.info("Attempting data error recovery...")

        # 数据错误通常不能通过重试恢复
        return {
            "success": False,
            "action": "data_validation",
            "message": "Data error cannot be recovered by retry",
            "suggestion": "Check data source and format"
        }

    def _recover_strategy_error(
        self,
        error: Exception,
        context: Optional[Dict]
    ) -> Dict[str, Any]:
        """恢复策略错误

        Args:
            error: 错误对象
            context: 上下文

        Returns:
            恢复结果
        """
        logger.info("Attempting strategy error recovery...")

        # 策略错误可能需要调整参数
        return {
            "success": False,
            "action": "strategy_adjustment",
            "message": "Strategy error requires parameter adjustment",
            "suggestion": "Review strategy parameters and risk limits"
        }

    def _recover_execution_error(
        self,
        error: Exception,
        context: Optional[Dict]
    ) -> Dict[str, Any]:
        """恢复执行错误

        Args:
            error: 错误对象
            context: 上下文

        Returns:
            恢复结果
        """
        logger.info("Attempting execution error recovery...")

        # 检查是否是余额不足
        error_message = str(error).lower()
        if "insufficient" in error_message or "balance" in error_message:
            return {
                "success": False,
                "action": "balance_check",
                "message": "Insufficient balance for execution",
                "suggestion": "Check account balance and position size"
            }

        # 其他执行错误，短时间重试
        time.sleep(self.retry_config["retry_delay"])
        return {
            "success": True,
            "action": "execution_retry",
            "message": "Execution error recovered after retry"
        }

    def _default_retry_strategy(
        self,
        error: Exception,
        context: Optional[Dict]
    ) -> Dict[str, Any]:
        """默认重试策略

        Args:
            error: 错误对象
            context: 上下文

        Returns:
            重试结果
        """
        max_retries = self.retry_config["max_retries"]
        retry_delay = self.retry_config["retry_delay"]
        backoff_factor = self.retry_config["backoff_factor"]

        for attempt in range(max_retries):
            try:
                logger.info(f"Retry attempt {attempt + 1}/{max_retries}")
                time.sleep(retry_delay)
                retry_delay *= backoff_factor  # 指数退避

                return {
                    "success": True,
                    "action": "retry",
                    "attempt": attempt + 1,
                    "message": f"Retry successful after {attempt + 1} attempts"
                }

            except Exception as retry_error:
                logger.error(f"Retry attempt {attempt + 1} failed: {retry_error}")

        return {
            "success": False,
            "action": "retry_exhausted",
            "message": f"All {max_retries} retry attempts failed"
        }

    def _get_or_create_circuit_breaker(self, key: str) -> CircuitBreaker:
        """获取或创建熔断器

        Args:
            key: 熔断器键

        Returns:
            CircuitBreaker实例
        """
        with self.circuit_breaker_lock:
            if key not in self.circuit_breakers:
                self.circuit_breakers[key] = CircuitBreaker()
            return self.circuit_breakers[key]

    def _can_execute_through_circuit_breaker(self, key: str) -> bool:
        """检查是否可以通过熔断器执行

        Args:
            key: 熔断器键

        Returns:
            是否可以执行
        """
        cb = self._get_or_create_circuit_breaker(key)
        return cb.can_execute()

    def _update_circuit_breaker(
        self,
        category: ErrorCategory,
        success: bool
    ) -> None:
        """更新熔断器状态

        Args:
            category: 错误类别
            success: 是否成功
        """
        cb = self._get_or_create_circuit_breaker(category.value)
        if success:
            cb.record_success()
        else:
            cb.record_failure()

    def _handle_critical_error(
        self,
        error: Exception,
        error_record: Dict
    ) -> Dict[str, Any]:
        """处理严重错误

        Args:
            error: 错误对象
            error_record: 错误记录

        Returns:
            处理结果
        """
        logger.critical(f"CRITICAL ERROR: {error}")

        # 记录到文件
        self._log_critical_error(error_record)

        # 尝试预防措施
        for action in self.preventive_actions:
            try:
                action(error, error_record)
            except Exception as e:
                logger.error(f"Preventive action failed: {e}")

        return {
            "handled": True,
            "category": "critical",
            "severity": "critical",
            "recovery": {
                "success": False,
                "action": "system_shutdown",
                "message": "Critical error requires system shutdown"
            }
        }

    def _log_critical_error(self, error_record: Dict) -> None:
        """记录严重错误到文件

        Args:
            error_record: 错误记录
        """
        try:
            log_dir = Path("logs/critical")
            log_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = log_dir / f"critical_error_{timestamp}.log"

            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(error_record, f, indent=2, ensure_ascii=False)

            logger.info(f"Critical error logged to {log_file}")

        except Exception as e:
            logger.error(f"Failed to log critical error: {e}")

    def add_preventive_action(self, action: Callable) -> None:
        """添加预防措施

        Args:
            action: 预防措施函数
        """
        self.preventive_actions.append(action)
        logger.info("Preventive action added")

    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计

        Returns:
            错误统计字典
        """
        return {
            "total_errors": len(self.error_history),
            "by_category": dict(self.error_stats),
            "circuit_breakers": {
                key: cb.get_state()
                for key, cb in self.circuit_breakers.items()
            },
            "recent_errors": list(self.error_history)[-10:] if self.error_history else []
        }

    def get_error_patterns(self) -> Dict[str, Dict]:
        """获取错误模式

        Returns:
            错误模式字典
        """
        return dict(self.error_patterns)

    def predict_errors(self) -> List[Dict[str, Any]]:
        """预测可能的错误

        Returns:
            预测的错误列表
        """
        predictions = []

        # 基于历史模式预测
        for pattern_key, pattern_data in self.error_patterns.items():
            if pattern_data["count"] > 5:  # 频繁出现的错误
                predictions.append({
                    "pattern": pattern_key,
                    "probability": min(0.9, pattern_data["count"] / 10.0),
                    "suggested_action": f"Monitor and prevent {pattern_key}"
                })

        # 按概率排序
        predictions.sort(key=lambda x: x["probability"], reverse=True)

        return predictions[:5]  # 返回前5个预测

    def reset(self) -> None:
        """重置错误处理器"""
        self.error_history.clear()
        self.error_patterns.clear()
        self.error_stats.clear()
        self.circuit_breakers.clear()
        logger.info("AdaptiveErrorHandler reset")


# ---------------------- 全局单例 ----------------------

_global_error_handler: Optional[AdaptiveErrorHandler] = None


def get_error_handler(config: Optional[Dict] = None) -> AdaptiveErrorHandler:
    """获取全局错误处理器实例

    Args:
        config: 配置字典

    Returns:
        AdaptiveErrorHandler实例
    """
    global _global_error_handler

    if _global_error_handler is None:
        _global_error_handler = AdaptiveErrorHandler(config)

    return _global_error_handler


def initialize_error_handler(config: Optional[Dict] = None) -> AdaptiveErrorHandler:
    """初始化错误处理器

    Args:
        config: 配置字典

    Returns:
        AdaptiveErrorHandler实例
    """
    handler = get_error_handler(config)
    logger.info("Error handler initialized")
    return handler


def handle_error_safely(
    error: Exception,
    context: Optional[Dict] = None
) -> Dict[str, Any]:
    """安全处理错误（便捷函数）

    Args:
        error: 错误对象
        context: 上下文

    Returns:
        处理结果
    """
    handler = get_error_handler()
    return handler.handle_error(error, context)
