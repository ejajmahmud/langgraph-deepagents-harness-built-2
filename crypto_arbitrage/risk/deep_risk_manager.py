"""深度风险管理器 V3.2

实现多层次、智能化的风险管理系统，确保套利交易的低风险特性。

核心功能:
1. 实时风险监控 - 敞口、波动率、流动性、相关性
2. 多级风险预警 - INFO/WARNING/CRITICAL三级预警
3. 动态风险限额 - 基于市场条件自动调整
4. 风险事件管理 - 记录、分析和预防
5. 预检机制 - 交易前风险评估
6. 实时监控 - 交易中风险跟踪
7. 后评估 - 交易后风险分析
"""

import asyncio
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """风险等级"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertLevel(Enum):
    """预警等级"""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass
class RiskMetrics:
    """风险指标"""
    exposure: float = 0.0              # 总敞口
    exposure_utilization: float = 0.0   # 敞口使用率
    daily_pnl: float = 0.0             # 日盈亏
    drawdown: float = 0.0              # 回撤率
    volatility: float = 0.0             # 波动率
    liquidity_score: float = 1.0         # 流动性评分
    correlation_risk: float = 0.0        # 相关性风险
    concentration_risk: float = 0.0      # 集中度风险
    overall_risk: RiskLevel = RiskLevel.LOW  # 综合风险等级
    timestamp: float = field(default_factory=time.time)


@dataclass
class RiskAlert:
    """风险预警"""
    level: AlertLevel
    type: str
    message: str
    metrics: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    resolved: bool = False


@dataclass
class RiskEvent:
    """风险事件"""
    event_type: str
    severity: RiskLevel
    description: str
    impact: str
    lessons_learned: str
    timestamp: float = field(default_factory=time.time)
    prevention_measures: List[str] = field(default_factory=list)


class DeepRiskManager:
    """深度风险管理器 V3.2

    实现多层次、智能化的风险管理系统。
    """

    def __init__(
        self,
        config: Dict[str, Any]
    ):
        """初始化深度风险管理器

        Args:
            config: 配置字典，包含:
                - max_exposure: 最大敞口
                - max_drawdown: 最大回撤率
                - daily_loss_limit: 日亏损限制
                - volatility_threshold: 波动率阈值
                - min_liquidity_score: 最小流动性评分
                - alert_callbacks: 预警回调函数列表
        """
        # 风险限制配置
        self.max_exposure = config.get('max_exposure', 10000.0)
        self.max_drawdown = config.get('max_drawdown', 5.0)
        self.daily_loss_limit = config.get('daily_loss_limit', -500.0)
        self.volatility_threshold = config.get('volatility_threshold', 3.0)
        self.min_liquidity_score = config.get('min_liquidity_score', 0.7)

        # 预警回调
        self.alert_callbacks: List[Callable[[RiskAlert], None]] = (
            config.get('alert_callbacks', [])
        )

        # 历史数据（用于计算趋势和波动率）
        self.exposure_history = deque(maxlen=1000)
        self.pnl_history = deque(maxlen=1000)
        self.volatility_history = deque(maxlen=100)

        # 风险预警和事件
        self.active_alerts: List[RiskAlert] = []
        self.risk_events: List[RiskEvent] = []

        # 当前持仓和交易
        self.active_positions: Dict[str, Any] = {}
        self.pending_trades: List[Dict[str, Any]] = []

        # 实时风险指标
        self.current_metrics = RiskMetrics()

        # 运行状态
        self.is_monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None

        logger.info("深度风险管理器 V3.2 初始化完成")

    async def start_monitoring(
        self,
        interval: float = 5.0
    ) -> None:
        """启动实时风险监控

        Args:
            interval: 监控间隔（秒）
        """
        if self.is_monitoring:
            logger.warning("风险监控已在运行")
            return

        self.is_monitoring = True
        self._monitor_task = asyncio.create_task(
            self._monitor_loop(interval)
        )
        logger.info(f"深度风险监控已启动 (间隔: {interval}s)")

    async def stop_monitoring(self) -> None:
        """停止实时风险监控"""
        if not self.is_monitoring:
            return

        self.is_monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None

        logger.info("深度风险监控已停止")

    async def _monitor_loop(self, interval: float) -> None:
        """风险监控循环"""
        while self.is_monitoring:
            try:
                await self._update_risk_metrics()
                await self._check_risk_thresholds()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"风险监控出错: {e}")
                await asyncio.sleep(interval)

    def pre_trade_risk_check(
        self,
        trade: Dict[str, Any]
    ) -> Dict[str, Any]:
        """交易前风险预检

        Args:
            trade: 交易信息字典

        Returns:
            风险检查结果字典，包含:
                - approved: 是否通过
                - reason: 原因描述
                - level: 风险等级
                - details: 详细信息
        """
        # 计算交易后的敞口
        new_exposure = self.current_metrics.exposure + trade.get('amount', 0)
        new_utilization = (new_exposure / self.max_exposure) * 100

        # 检查敞口限制
        if new_exposure > self.max_exposure:
            reason = f"超过最大敞口限制 ({new_exposure:.2f} > {self.max_exposure:.2f})"
            return {
                'approved': False,
                'reason': reason,
                'level': RiskLevel.CRITICAL.value,
                'details': {
                    'current_exposure': self.current_metrics.exposure,
                    'new_exposure': new_exposure,
                    'max_exposure': self.max_exposure,
                    'utilization': new_utilization
                }
            }

        # 检查日亏损限制
        if self.current_metrics.daily_pnl < self.daily_loss_limit:
            reason = f"超过日亏损限制 ({self.current_metrics.daily_pnl:.2f} < {self.daily_loss_limit:.2f})"
            return {
                'approved': False,
                'reason': reason,
                'level': RiskLevel.CRITICAL.value,
                'details': {
                    'daily_pnl': self.current_metrics.daily_pnl,
                    'daily_loss_limit': self.daily_loss_limit
                }
            }

        # 检查波动率
        if self.current_metrics.volatility > self.volatility_threshold:
            reason = f"市场波动率过高 ({self.current_metrics.volatility:.2f} > {self.volatility_threshold:.2f})"
            return {
                'approved': False,
                'reason': reason,
                'level': RiskLevel.HIGH.value,
                'details': {
                    'volatility': self.current_metrics.volatility,
                    'volatility_threshold': self.volatility_threshold
                }
            }

        # 检查流动性
        if self.current_metrics.liquidity_score < self.min_liquidity_score:
            reason = f"流动性不足 ({self.current_metrics.liquidity_score:.2f} < {self.min_liquidity_score:.2f})"
            return {
                'approved': False,
                'reason': reason,
                'level': RiskLevel.HIGH.value,
                'details': {
                    'liquidity_score': self.current_metrics.liquidity_score,
                    'min_liquidity_score': self.min_liquidity_score
                }
            }

        # 检查回撤
        if self.current_metrics.drawdown > self.max_drawdown:
            reason = f"超过最大回撤限制 ({self.current_metrics.drawdown:.2f}% > {self.max_drawdown:.2f}%)"
            return {
                'approved': False,
                'reason': reason,
                'level': RiskLevel.CRITICAL.value,
                'details': {
                    'drawdown': self.current_metrics.drawdown,
                    'max_drawdown': self.max_drawdown
                }
            }

        # 评估综合风险
        risk_level = self._assess_trade_risk(trade)
        if risk_level == RiskLevel.CRITICAL:
            return {
                'approved': False,
                'reason': "综合风险等级过高",
                'level': risk_level.value,
                'details': {
                    'overall_risk': risk_level.value
                }
            }

        return {
            'approved': True,
            'reason': "风险预检通过",
            'level': risk_level.value,
            'details': {
                'new_exposure': new_exposure,
                'utilization': new_utilization,
                'overall_risk': risk_level.value
            }
        }

    async def monitor_trade_execution(
        self,
        trade_id: str,
        trade: Dict[str, Any]
    ) -> None:
        """监控交易执行过程中的风险

        Args:
            trade_id: 交易ID
            trade: 交易信息
        """
        self.pending_trades.append({
            'trade_id': trade_id,
            'trade': trade,
            'start_time': time.time(),
            'status': 'executing'
        })

        logger.info(f"开始监控交易执行: {trade_id}")

    async def complete_trade_execution(
        self,
        trade_id: str,
        result: Dict[str, Any]
    ) -> None:
        """完成交易执行，进行后评估

        Args:
            trade_id: 交易ID
            result: 交易结果
        """
        # 从待监控列表中移除
        self.pending_trades = [
            t for t in self.pending_trades
            if t['trade_id'] != trade_id
        ]

        # 记录到历史
        self.pnl_history.append(result.get('profit', 0.0))

        # 分析交易风险
        await self._analyze_trade_risk(trade_id, result)

        logger.info(f"交易执行完成: {trade_id}, 利润: {result.get('profit', 0):.2f}")

    async def _update_risk_metrics(self) -> None:
        """更新风险指标"""
        # 更新敞口历史
        self.exposure_history.append(self.current_metrics.exposure)

        # 计算波动率（基于PnL历史）
        if len(self.pnl_history) >= 20:
            recent_pnl = list(self.pnl_history)[-20:]
            mean_pnl = sum(recent_pnl) / len(recent_pnl)
            variance = sum((p - mean_pnl) ** 2 for p in recent_pnl) / len(recent_pnl)
            self.current_metrics.volatility = (variance ** 0.5)

        # 计算敞口使用率
        self.current_metrics.exposure_utilization = (
            (self.current_metrics.exposure / self.max_exposure) * 100
            if self.max_exposure > 0 else 0
        )

        # 计算回撤
        if len(self.pnl_history) >= 2:
            peak = max(self.pnl_history)
            current = self.pnl_history[-1]
            self.current_metrics.drawdown = (
                ((peak - current) / peak) * 100 if peak > 0 else 0
            )

        # 更新综合风险等级
        self.current_metrics.overall_risk = self._assess_overall_risk()

        self.current_metrics.timestamp = time.time()

    async def _check_risk_thresholds(self) -> None:
        """检查风险阈值，触发预警"""
        alerts = []

        # 检查敞口使用率
        if self.current_metrics.exposure_utilization > 90:
            alerts.append(RiskAlert(
                level=AlertLevel.CRITICAL,
                type="exposure",
                message=f"敞口使用率过高: {self.current_metrics.exposure_utilization:.1f}%",
                metrics={"exposure_utilization": self.current_metrics.exposure_utilization}
            ))
        elif self.current_metrics.exposure_utilization > 75:
            alerts.append(RiskAlert(
                level=AlertLevel.WARNING,
                type="exposure",
                message=f"敞口使用率较高: {self.current_metrics.exposure_utilization:.1f}%",
                metrics={"exposure_utilization": self.current_metrics.exposure_utilization}
            ))

        # 检查日亏损
        if self.current_metrics.daily_pnl < self.daily_loss_limit:
            alerts.append(RiskAlert(
                level=AlertLevel.CRITICAL,
                type="daily_loss",
                message=f"超过日亏损限制: {self.current_metrics.daily_pnl:.2f}",
                metrics={"daily_pnl": self.current_metrics.daily_pnl}
            ))

        # 检查回撤
        if self.current_metrics.drawdown > self.max_drawdown:
            alerts.append(RiskAlert(
                level=AlertLevel.CRITICAL,
                type="drawdown",
                message=f"超过最大回撤: {self.current_metrics.drawdown:.2f}%",
                metrics={"drawdown": self.current_metrics.drawdown}
            ))

        # 检查波动率
        if self.current_metrics.volatility > self.volatility_threshold:
            alerts.append(RiskAlert(
                level=AlertLevel.WARNING,
                type="volatility",
                message=f"市场波动率较高: {self.current_metrics.volatility:.2f}",
                metrics={"volatility": self.current_metrics.volatility}
            ))

        # 检查流动性
        if self.current_metrics.liquidity_score < self.min_liquidity_score:
            alerts.append(RiskAlert(
                level=AlertLevel.WARNING,
                type="liquidity",
                message=f"流动性不足: {self.current_metrics.liquidity_score:.2f}",
                metrics={"liquidity_score": self.current_metrics.liquidity_score}
            ))

        # 触发预警
        for alert in alerts:
            await self._trigger_alert(alert)

    async def _trigger_alert(self, alert: RiskAlert) -> None:
        """触发风险预警"""
        self.active_alerts.append(alert)
        logger.warning(f"风险预警 [{alert.level.value}]: {alert.message}")

        # 调用回调函数
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"预警回调失败: {e}")

    def _assess_trade_risk(self, trade: Dict[str, Any]) -> RiskLevel:
        """评估交易风险等级

        Args:
            trade: 交易信息

        Returns:
            风险等级
        """
        risk_score = 0

        # 金额风险
        amount = trade.get('amount', 0)
        risk_score += min(amount / 1000 * 10, 30)

        # 预期收益率风险（收益率过高可能是高风险）
        profit_rate = trade.get('profit_rate', 0)
        if profit_rate > 10:
            risk_score += 30
        elif profit_rate > 5:
            risk_score += 15

        # 当前市场状况风险
        if self.current_metrics.volatility > 2.0:
            risk_score += 20
        if self.current_metrics.liquidity_score < 0.8:
            risk_score += 15

        # 敞口使用率风险
        utilization = self.current_metrics.exposure_utilization
        if utilization > 80:
            risk_score += 25
        elif utilization > 60:
            risk_score += 10

        # 映射到风险等级
        if risk_score >= 70:
            return RiskLevel.CRITICAL
        elif risk_score >= 50:
            return RiskLevel.HIGH
        elif risk_score >= 30:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _assess_overall_risk(self) -> RiskLevel:
        """评估综合风险等级

        Returns:
            风险等级
        """
        risk_score = 0

        # 敞口风险
        risk_score += min(self.current_metrics.exposure_utilization / 2, 30)

        # 回撤风险
        risk_score += min(self.current_metrics.drawdown * 2, 25)

        # 波动率风险
        risk_score += min(self.current_metrics.volatility * 5, 20)

        # 流动性风险
        risk_score += min((1 - self.current_metrics.liquidity_score) * 30, 25)

        # 映射到风险等级
        if risk_score >= 70:
            return RiskLevel.CRITICAL
        elif risk_score >= 50:
            return RiskLevel.HIGH
        elif risk_score >= 30:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    async def _analyze_trade_risk(
        self,
        trade_id: str,
        result: Dict[str, Any]
    ) -> None:
        """分析交易风险，提取经验教训

        Args:
            trade_id: 交易ID
            result: 交易结果
        """
        profit = result.get('profit', 0)
        status = result.get('status', 'unknown')

        # 如果交易失败或亏损严重，记录风险事件
        if status == 'failed' or profit < -50:
            event = RiskEvent(
                event_type="trade_failure" if status == 'failed' else "significant_loss",
                severity=RiskLevel.HIGH if profit < -100 else RiskLevel.MEDIUM,
                description=f"交易 {trade_id} {'失败' if status == 'failed' else f'亏损${profit:.2f}'}",
                impact=f"影响: 日盈亏 {self.current_metrics.daily_pnl:.2f}",
                lessons_learned="需要分析失败原因，优化策略",
                prevention_measures=["提高风险预检标准", "降低仓位大小"]
            )
            self.risk_events.append(event)
            logger.warning(f"记录风险事件: {event.event_type}")

    def get_risk_summary(self) -> Dict[str, Any]:
        """获取风险摘要

        Returns:
            风险摘要字典
        """
        return {
            'current_metrics': {
                'exposure': self.current_metrics.exposure,
                'exposure_utilization': self.current_metrics.exposure_utilization,
                'daily_pnl': self.current_metrics.daily_pnl,
                'drawdown': self.current_metrics.drawdown,
                'volatility': self.current_metrics.volatility,
                'liquidity_score': self.current_metrics.liquidity_score,
                'overall_risk': self.current_metrics.overall_risk.value,
            },
            'risk_limits': {
                'max_exposure': self.max_exposure,
                'max_drawdown': self.max_drawdown,
                'daily_loss_limit': self.daily_loss_limit,
                'volatility_threshold': self.volatility_threshold,
                'min_liquidity_score': self.min_liquidity_score,
            },
            'active_alerts': len([a for a in self.active_alerts if not a.resolved]),
            'risk_events_count': len(self.risk_events),
            'monitoring_status': 'running' if self.is_monitoring else 'stopped',
            'is_risk_limit_reached': (
                self.current_metrics.overall_risk == RiskLevel.CRITICAL or
                self.current_metrics.daily_pnl < self.daily_loss_limit or
                self.current_metrics.drawdown > self.max_drawdown
            )
        }

    def get_risk_history(
        self,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """获取风险历史数据

        Args:
            hours: 查询小时数

        Returns:
            风险历史列表
        """
        cutoff_time = time.time() - hours * 3600

        history = []

        # 风险预警历史
        for alert in self.active_alerts:
            if alert.timestamp >= cutoff_time:
                history.append({
                    'type': 'alert',
                    'level': alert.level.value,
                    'message': alert.message,
                    'timestamp': alert.timestamp,
                    'resolved': alert.resolved
                })

        # 风险事件历史
        for event in self.risk_events:
            if event.timestamp >= cutoff_time:
                history.append({
                    'type': 'event',
                    'event_type': event.event_type,
                    'severity': event.severity.value,
                    'description': event.description,
                    'timestamp': event.timestamp
                })

        # 按时间排序
        history.sort(key=lambda x: x['timestamp'], reverse=True)

        return history


# 全局风险管理器实例
_risk_manager: Optional[DeepRiskManager] = None


def initialize_deep_risk_manager(config: Dict[str, Any]) -> DeepRiskManager:
    """初始化全局深度风险管理器

    Args:
        config: 配置字典

    Returns:
        深度风险管理器实例
    """
    global _risk_manager
    _risk_manager = DeepRiskManager(config)
    return _risk_manager


def get_deep_risk_manager() -> Optional[DeepRiskManager]:
    """获取全局深度风险管理器

    Returns:
        深度风险管理器实例，如果未初始化则返回 None
    """
    return _risk_manager
