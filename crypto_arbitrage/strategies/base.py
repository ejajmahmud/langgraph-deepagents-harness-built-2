"""策略基类 V2.4 - 统一策略接口、生命周期管理和通用功能

消除 5 个策略间的代码重复，提供统一的:
- scan_opportunities / execute_arbitrage / get_performance_stats 接口
- 策略生命周期管理 (start/stop/pause/resume)
- 交易记录和性能统计
- 仓位追踪
- 风险检查集成
- 策略健康状态
"""

import logging
import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class StrategyState(str, Enum):
    """策略运行状态"""
    INITIALIZED = "initialized"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class BaseStrategy(ABC):
    """策略基类 - 所有套利策略的抽象基类

    子类必须:
    1. 覆盖 STRATEGY_NAME 和 STRATEGY_DESCRIPTION
    2. 实现 scan_opportunities() 和 execute_arbitrage()
    3. 调用 super().__init__(config)

    可选覆盖:
    - on_start() / on_stop(): 生命周期钩子
    - validate_config(): 配置验证
    - custom_scan_filter(): 自定义过滤逻辑
    - monitor_positions() / close_position(): 持仓管理 (有状态策略)
    """

    # 策略元数据 - 子类必须覆盖
    STRATEGY_NAME: str = "base"
    STRATEGY_DESCRIPTION: str = "基础策略"

    def __init__(self, config: Dict[str, Any]) -> None:
        """初始化策略

        Args:
            config: 策略配置字典
        """
        self.config = config
        self.min_profit_rate = config.get('min_profit_rate', 0.5)
        self.max_position_size = config.get('max_position_size', 1000)

        # 通用交易记录
        self.active_positions: List[Dict] = []
        self._trade_history: List[Dict] = []

        # 生命周期状态
        self._state = StrategyState.INITIALIZED
        self._start_time: Optional[float] = None
        self._last_scan_time: float = 0.0
        self._total_scans: int = 0
        self._error_count: int = 0
        self._max_consecutive_errors: int = 5

        # 策略健康指标
        self._consecutive_losses: int = 0

        # 验证配置
        validation_errors = self.validate_config()
        if validation_errors:
            for err in validation_errors:
                logger.warning(f"{self.STRATEGY_NAME} 配置警告: {err}")

        logger.info(f"{self.STRATEGY_NAME} 策略初始化完成")

    # -------------------- 生命周期管理 --------------------

    def start(self) -> None:
        """启动策略"""
        if self._state == StrategyState.RUNNING:
            logger.warning(f"{self.STRATEGY_NAME} 已在运行中")
            return
        self._state = StrategyState.RUNNING
        self._start_time = time.time()
        self.on_start()
        logger.info(f"{self.STRATEGY_NAME} 策略已启动")

    def stop(self) -> None:
        """停止策略"""
        if self._state == StrategyState.STOPPED:
            return
        self.on_stop()
        self._state = StrategyState.STOPPED
        logger.info(f"{self.STRATEGY_NAME} 策略已停止")

    def pause(self) -> None:
        """暂停策略"""
        if self._state != StrategyState.RUNNING:
            return
        self._state = StrategyState.PAUSED
        logger.info(f"{self.STRATEGY_NAME} 策略已暂停")

    def resume(self) -> None:
        """恢复策略"""
        if self._state != StrategyState.PAUSED:
            return
        self._state = StrategyState.RUNNING
        logger.info(f"{self.STRATEGY_NAME} 策略已恢复")

    def on_start(self) -> None:
        """策略启动钩子（子类可覆盖）"""

    def on_stop(self) -> None:
        """策略停止钩子（子类可覆盖）"""

    @property
    def state(self) -> StrategyState:
        """当前策略状态"""
        return self._state

    @property
    def is_running(self) -> bool:
        """策略是否在运行"""
        return self._state == StrategyState.RUNNING

    @property
    def uptime_seconds(self) -> float:
        """策略运行时间"""
        if not self._start_time:
            return 0.0
        if self._state == StrategyState.RUNNING:
            return time.time() - self._start_time
        return self._start_time  # type: ignore[return-value]

    # -------------------- 抽象方法 --------------------

    @abstractmethod
    async def scan_opportunities(self) -> List[Dict[str, Any]]:
        """扫描套利机会（子类必须实现）

        Returns:
            套利机会列表，每个机会必须包含:
                - symbol: 交易对
                - profit_rate: 预期收益率 (%)
                - strategy: 策略标识
                - timestamp: 时间戳
        """
        ...

    @abstractmethod
    async def execute_arbitrage(self, opportunity: Dict[str, Any]) -> bool:
        """执行套利交易（子类必须实现）

        Args:
            opportunity: 套利机会字典

        Returns:
            是否执行成功
        """
        ...

    # -------------------- 配置验证 --------------------

    def validate_config(self) -> List[str]:
        """验证策略配置（子类可覆盖以添加自定义验证）

        Returns:
            配置错误列表，空列表表示通过
        """
        errors: List[str] = []
        if self.min_profit_rate < 0:
            errors.append(f"min_profit_rate 不应为负数: {self.min_profit_rate}")
        if self.max_position_size <= 0:
            errors.append(f"max_position_size 必须为正数: {self.max_position_size}")
        return errors

    # -------------------- 交易执行（带状态检查） --------------------

    async def safe_scan(self) -> List[Dict[str, Any]]:
        """安全的扫描方法 - 带状态检查和错误处理

        Returns:
            套利机会列表，错误时返回空列表
        """
        if not self.is_running:
            logger.debug(f"{self.STRATEGY_NAME} 策略未运行，跳过扫描")
            return []

        try:
            opportunities = await self.scan_opportunities()
            self._total_scans += 1
            self._last_scan_time = time.time()
            self._error_count = 0  # 成功扫描重置错误计数
            return opportunities
        except Exception as e:
            self._error_count += 1
            logger.error(f"{self.STRATEGY_NAME} 扫描失败 (连续{self._error_count}次): {e}")
            if self._error_count >= self._max_consecutive_errors:
                logger.error(f"{self.STRATEGY_NAME} 连续错误过多，自动暂停")
                self.pause()
            return []

    async def safe_execute(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """安全的执行方法 - 带状态检查、记录和错误处理

        Args:
            opportunity: 套利机会字典

        Returns:
            执行结果字典:
                - status: 'completed' | 'failed' | 'rejected'
                - profit: 实际利润
                - error: 错误信息 (如有)
                - execution_time: 执行耗时
        """
        if not self.is_running:
            return {'status': 'rejected', 'error': '策略未运行', 'execution_time': 0}

        start_time = time.time()
        try:
            success = await self.execute_arbitrage(opportunity)
            elapsed = time.time() - start_time

            if success:
                profit = opportunity.get('actual_profit', opportunity.get('expected_profit', 0))
                record = self._record_trade(opportunity, 'completed', profit=profit)
                self._consecutive_losses = 0
                return {
                    'status': 'completed',
                    'profit': profit,
                    'record': record,
                    'execution_time': elapsed,
                }
            else:
                record = self._record_trade(
                    opportunity, 'failed',
                    error=opportunity.get('error', '执行返回 False')
                )
                self._consecutive_losses += 1
                return {
                    'status': 'failed',
                    'error': '执行返回 False',
                    'record': record,
                    'execution_time': elapsed,
                }
        except Exception as e:
            elapsed = time.time() - start_time
            record = self._record_trade(opportunity, 'failed', error=str(e))
            self._consecutive_losses += 1
            return {
                'status': 'failed',
                'error': str(e),
                'record': record,
                'execution_time': elapsed,
            }

    # -------------------- 性能统计 --------------------

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取策略性能统计（通用实现）"""
        total_trades = len(self._trade_history)
        if total_trades == 0:
            return self._empty_stats()

        successful = [
            t for t in self._trade_history
            if t.get('status') == 'completed'
        ]

        total_profit = sum(
            t.get('actual_profit', t.get('expected_profit', 0))
            for t in successful
        )

        avg_profit_rate = 0.0
        if successful:
            avg_profit_rate = sum(
                t.get('actual_profit_rate', t.get('expected_profit_rate', 0))
                for t in successful
            ) / len(successful)

        return {
            'total_trades': total_trades,
            'successful_trades': len(successful),
            'total_profit': total_profit,
            'average_profit_rate': avg_profit_rate,
            'success_rate': len(successful) / total_trades if total_trades > 0 else 0,
            'consecutive_losses': self._consecutive_losses,
            'total_scans': self._total_scans,
            'uptime_seconds': self.uptime_seconds,
            'state': self._state.value,
        }

    def _empty_stats(self) -> Dict[str, Any]:
        """返回空统计数据"""
        return {
            'total_trades': 0,
            'successful_trades': 0,
            'total_profit': 0,
            'average_profit_rate': 0,
            'success_rate': 0,
            'consecutive_losses': 0,
            'total_scans': 0,
            'uptime_seconds': 0,
            'state': self._state.value,
        }

    # -------------------- 交易记录 --------------------

    def _record_trade(
        self,
        opportunity: Dict[str, Any],
        status: str,
        profit: float = 0,
        order_ids: Optional[Dict[str, str]] = None,
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        """记录交易到历史

        Args:
            opportunity: 套利机会
            status: 交易状态 (completed, failed, rejected)
            profit: 实际利润
            order_ids: 订单ID映射
            error: 错误信息

        Returns:
            交易记录字典
        """
        record = {
            'strategy': self.STRATEGY_NAME,
            'symbol': opportunity.get('symbol', 'N/A'),
            'status': status,
            'expected_profit': opportunity.get('expected_profit', 0),
            'expected_profit_rate': opportunity.get('profit_rate', 0),
            'actual_profit': profit,
            'actual_profit_rate': (
                (profit / opportunity.get('buy_cost', 1)) * 100
                if opportunity.get('buy_cost', 0) > 0 else 0
            ),
            'order_ids': order_ids or {},
            'error': error,
            'timestamp': time.time(),
        }
        self._trade_history.append(record)

        # V1.7.0: 自动记录交易知识到 Memo0
        self._record_trade_to_memory(record)

        return record

    # -------------------- 通用工具方法 --------------------

    def _sort_opportunities(
        self,
        opportunities: List[Dict[str, Any]],
        key: str = 'profit_rate',
        reverse: bool = True,
    ) -> List[Dict[str, Any]]:
        """按指定键排序机会列表"""
        return sorted(opportunities, key=lambda x: x.get(key, 0), reverse=reverse)

    def _filter_by_threshold(
        self,
        opportunities: List[Dict[str, Any]],
        min_profit_rate: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """按收益率阈值过滤"""
        threshold = min_profit_rate if min_profit_rate is not None else self.min_profit_rate
        return [o for o in opportunities if o.get('profit_rate', 0) >= threshold]

    def _post_process_opportunities(
        self,
        opportunities: List[Dict[str, Any]],
        sort_key: str = 'profit_rate',
    ) -> List[Dict[str, Any]]:
        """对扫描结果进行后处理: 过滤 + 排序 + 策略标识

        Args:
            opportunities: 原始机会列表
            sort_key: 排序键

        Returns:
            处理后的机会列表
        """
        filtered = self._filter_by_threshold(opportunities)
        sorted_ops = self._sort_opportunities(filtered, key=sort_key)
        # 注入策略标识
        for opp in sorted_ops:
            opp.setdefault('strategy', self.STRATEGY_NAME)
            opp.setdefault('timestamp', time.time())
        return sorted_ops

    # -------------------- 健康状态 --------------------

    @property
    def is_healthy(self) -> bool:
        """策略是否健康（连续亏损未超过阈值且未处于错误状态）"""
        return (
            self._consecutive_losses < 3
            and self._state != StrategyState.ERROR
            and self._error_count < self._max_consecutive_errors
        )

    @property
    def active_position_count(self) -> int:
        """当前活跃持仓数"""
        return len([
            p for p in self.active_positions
            if p.get('status') == 'open'
        ])

    @property
    def trade_history(self) -> List[Dict]:
        """交易历史（只读）"""
        return list(self._trade_history)

    def get_health_report(self) -> Dict[str, Any]:
        """获取策略健康报告"""
        return {
            'strategy': self.STRATEGY_NAME,
            'state': self._state.value,
            'is_healthy': self.is_healthy,
            'consecutive_losses': self._consecutive_losses,
            'error_count': self._error_count,
            'total_scans': self._total_scans,
            'active_positions': self.active_position_count,
            'uptime_seconds': self.uptime_seconds,
        }

    # -------------------- Memo0 集成 --------------------

    def _record_trade_to_memory(self, record: Dict[str, Any]) -> None:
        """将交易记录自动同步到 Memo0 知识库

        Args:
            record: 交易记录字典
        """
        try:
            from storage.mem0_storage import add_trading_knowledge
            status = record.get('status', 'unknown')
            symbol = record.get('symbol', 'N/A')
            profit = record.get('actual_profit', 0)

            if status == 'completed':
                content = (
                    f"策略 {self.STRATEGY_NAME} 交易成功: {symbol}, "
                    f"利润 ${profit:.2f}, "
                    f"收益率 {record.get('actual_profit_rate', 0):.3f}%"
                )
                add_trading_knowledge('trade_success', content)
            elif status == 'failed':
                error = record.get('error', '未知错误')
                content = (
                    f"策略 {self.STRATEGY_NAME} 交易失败: {symbol}, "
                    f"错误: {error}"
                )
                add_trading_knowledge('trade_failure', content)
        except Exception as e:
            logger.debug(f"交易知识记录失败: {e}")
