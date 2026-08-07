"""风险管理器V2 - Phase 13核心模块

增强的风险管理系统，提供实时风险监控、多层次风险控制和熔断机制。

核心功能：
1. 实时风险监控 - 实时监控交易风险
2. 多层次风险控制 - 账户、仓位、交易多层风险控制
3. 熔断器机制 - 熔断器防止重大损失
4. 风险预警 - 提前预警风险事件
5. 风险报告 - 生成详细的风险报告

创建时间：2026-04-19 23:15:00
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from collections import deque, defaultdict

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskType(Enum):
    """风险类型"""
    POSITION_RISK = "position_risk"          # 仓位风险
    PORTFOLIO_RISK = "portfolio_risk"        # 投资组合风险
    MARKET_RISK = "market_risk"              # 市场风险
    LIQUIDITY_RISK = "liquidity_risk"        # 流动性风险
    CONCENTRATION_RISK = "concentration_risk" # 集中度风险
    VOLATILITY_RISK = "volatility_risk"      # 波动性风险


class RiskAction(Enum):
    """风险行动"""
    APPROVE = "approve"
    REJECT = "reject"
    REDUCE_SIZE = "reduce_size"
    INCREASE_STOP_LOSS = "increase_stop_loss"
    MONITOR = "monitor"


class RiskManagerV2:
    """风险管理器V2

    增强的风险管理系统。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化风险管理器V2

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 风险阈值
        self.risk_limits = {
            'max_position_size': self.config.get('max_position_size', 10000.0),     # 最大仓位大小
            'max_daily_loss': self.config.get('max_daily_loss', 500.0),             # 最大日损失
            'max_total_exposure': self.config.get('max_total_exposure', 50000.0),   # 最大总敞口
            'max_drawdown_percent': self.config.get('max_drawdown_percent', 10.0),   # 最大回撤百分比
            'max_single_loss_percent': self.config.get('max_single_loss_percent', 2.0), # 单次最大损失百分比
            'max_correlation_exposure': self.config.get('max_correlation_exposure', 0.8), # 最大相关性敞口
        }

        # 熔断器配置
        self.enable_circuit_breaker = self.config.get('enable_circuit_breaker', True)
        self.circuit_breaker_loss_threshold = self.config.get('circuit_breaker_loss_threshold', 1000.0)
        self.circuit_breaker_window = self.config.get('circuit_breaker_window', 3600)  # 1小时
        self.circuit_breaker_cooldown = self.config.get('circuit_breaker_cooldown', 7200)  # 2小时

        # 熔断器状态
        self.circuit_breaker_triggered = False
        self.circuit_breaker_triggered_at: Optional[datetime] = None
        self.recent_losses: deque = deque()

        # 风险历史
        self.risk_events: List[Dict] = []
        self.max_risk_events = 1000

        # 风险统计
        self.risk_stats = {
            'total_risk_assessments': 0,
            'approvals': 0,
            'rejections': 0,
            'circuit_breaker_triggers': 0,
            'risk_warnings': 0,
            'max_risk_level': RiskLevel.LOW.value,
        }

        # 实时风险监控
        self.current_risks: Dict[str, Dict] = {}
        self.risk_monitoring_enabled = self.config.get('enable_risk_monitoring', True)

        # 风险监控任务
        self._risk_monitoring_task: Optional[asyncio.Task] = None
        self._risk_monitoring_interval = self.config.get('risk_monitoring_interval', 10)  # 秒

        # 存储引用
        self.storage: Optional[Any] = None

        logger.info("✅ 风险管理器V2初始化完成")

    async def initialize(self) -> bool:
        """初始化风险模型

        Returns:
            是否成功
        """
        logger.info("🚀 初始化风险管理器V2...")

        try:
            # 初始化风险模型
            await self._initialize_risk_models()

            # 启动风险监控任务
            if self.risk_monitoring_enabled:
                self._risk_monitoring_task = asyncio.create_task(
                    self._risk_monitoring_loop()
                )
                logger.info("✅ 风险监控任务已启动")

            logger.info("✅ 风险管理器V2初始化完成")
            return True

        except Exception as e:
            logger.error(f"❌ 风险管理器V2初始化失败: {e}")
            return False

    async def stop(self) -> bool:
        """停止风险管理器

        Returns:
            是否成功
        """
        logger.info("🛑 停止风险管理器V2...")

        try:
            # 停止风险监控任务
            if self._risk_monitoring_task:
                self._risk_monitoring_task.cancel()
                try:
                    await self._risk_monitoring_task
                except asyncio.CancelledError:
                    pass

            logger.info("✅ 风险管理器V2已停止")
            return True

        except Exception as e:
            logger.error(f"❌ 停止风险管理器V2失败: {e}")
            return False

    async def check_pre_trade_risk(
        self,
        signals: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """交易前风险检查

        Args:
            signals: 交易信号列表

        Returns:
            风险评估字典
        """
        self.risk_stats['total_risk_assessments'] += 1

        try:
            # 检查熔断器
            if self._is_circuit_breaker_active():
                logger.warning("⚠️ 熔断器激活，拒绝所有交易")
                self._record_risk_event({
                    'type': 'circuit_breaker',
                    'level': RiskLevel.CRITICAL.value,
                    'action': RiskAction.REJECT.value,
                    'reason': 'Circuit breaker is active',
                })
                return {
                    'approved': False,
                    'reason': 'Circuit breaker is active',
                    'risk_level': RiskLevel.CRITICAL.value,
                    'action': RiskAction.REJECT.value,
                }

            # 评估每个信号
            assessed_signals = []
            for signal in signals:
                assessment = await self._assess_signal_risk(signal)
                assessed_signals.append(assessment)

            # 综合评估
            overall_assessment = self._combine_signal_assessments(assessed_signals)

            # 如果有信号被批准
            approved_signals = [
                signal for signal, assessment in zip(signals, assessed_signals)
                if assessment.get('action') == RiskAction.APPROVE.value
            ]

            if approved_signals:
                self.risk_stats['approvals'] += 1
                return {
                    'approved': True,
                    'reason': overall_assessment.get('reason'),
                    'risk_level': overall_assessment.get('risk_level'),
                    'action': overall_assessment.get('action'),
                    'approved_signals': approved_signals,
                    'assessed_signals': assessed_signals,
                }
            else:
                self.risk_stats['rejections'] += 1
                return {
                    'approved': False,
                    'reason': overall_assessment.get('reason'),
                    'risk_level': overall_assessment.get('risk_level'),
                    'action': overall_assessment.get('action'),
                    'assessed_signals': assessed_signals,
                }

        except Exception as e:
            logger.error(f"交易前风险检查失败: {e}")
            return {
                'approved': False,
                'reason': f'Risk assessment error: {e}',
                'risk_level': RiskLevel.HIGH.value,
                'action': RiskAction.REJECT.value,
            }

    async def check_post_trade_risk(
        self,
        execution_result: Dict[str, Any],
        current_positions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """交易后风险检查

        Args:
            execution_result: 执行结果
            current_positions: 当前仓位列表

        Returns:
            风险评估字典
        """
        try:
            # 检查执行结果
            if not execution_result.get('success'):
                # 记录损失
                loss = abs(execution_result.get('loss', 0))
                if loss > 0:
                    self._add_to_recent_losses(loss)
                    self._check_circuit_breaker()

            # 评估投资组合风险
            portfolio_risk = await self._calculate_portfolio_risk(current_positions)

            # 检查风险限制
            risk_violations = self._check_risk_limits(portfolio_risk, current_positions)

            if risk_violations:
                # 发送风险警告
                for violation in risk_violations:
                    self.risk_stats['risk_warnings'] += 1
                    self._record_risk_event({
                        'type': 'risk_limit_violation',
                        'level': RiskLevel.HIGH.value,
                        'action': RiskAction.MONITOR.value,
                        'reason': violation['reason'],
                        'details': violation,
                    })

                return {
                    'risk_level': RiskLevel.HIGH.value,
                    'action': RiskAction.MONITOR.value,
                    'violations': risk_violations,
                    'portfolio_risk': portfolio_risk,
                }
            else:
                # 更新最大风险等级
                risk_level = self._determine_risk_level(portfolio_risk)
                if self._compare_risk_levels(risk_level, self.risk_stats['max_risk_level']) > 0:
                    self.risk_stats['max_risk_level'] = risk_level.value

                return {
                    'risk_level': risk_level.value,
                    'action': RiskAction.APPROVE.value,
                    'portfolio_risk': portfolio_risk,
                }

        except Exception as e:
            logger.error(f"交易后风险检查失败: {e}")
            return {
                'risk_level': RiskLevel.HIGH.value,
                'action': RiskAction.MONITOR.value,
                'error': str(e),
            }

    async def monitor_risk(self) -> Dict[str, Any]:
        """监控风险

        Returns:
            风险状态字典
        """
        try:
            # 获取所有当前风险
            risk_assessments = []

            # 仓位风险
            position_risks = await self._get_position_risks()
            risk_assessments.extend(position_risks)

            # 投资组合风险
            portfolio_risk = await self._get_portfolio_risk()
            risk_assessments.append(portfolio_risk)

            # 市场风险
            market_risk = await self._get_market_risk()
            risk_assessments.append(market_risk)

            # 流动性风险
            liquidity_risk = await self._get_liquidity_risk()
            risk_assessments.append(liquidity_risk)

            # 综合风险评估
            overall_risk_level = self._assess_overall_risk(risk_assessments)

            # 更新当前风险
            self.current_risks = {
                'timestamp': datetime.now().isoformat(),
                'overall_risk_level': overall_risk_level.value,
                'assessments': risk_assessments,
            }

            return self.current_risks

        except Exception as e:
            logger.error(f"监控风险失败: {e}")
            return {}

    def get_risk_status(self) -> Dict[str, Any]:
        """获取风险状态

        Returns:
            风险状态字典
        """
        return {
            'circuit_breaker_active': self._is_circuit_breaker_active(),
            'circuit_breaker_triggered': self.circuit_breaker_triggered,
            'current_risks': self.current_risks,
            'stats': self.risk_stats,
            'risk_limits': self.risk_limits,
        }

    async def generate_risk_report(self) -> Dict[str, Any]:
        """生成风险报告

        Returns:
            风险报告字典
        """
        try:
            # 获取当前风险状态
            current_risks = await self.monitor_risk()

            # 分析风险历史
            risk_history_analysis = self._analyze_risk_history()

            # 计算风险趋势
            risk_trends = self._calculate_risk_trends()

            # 生成风险摘要
            risk_summary = self._generate_risk_summary(current_risks, risk_history_analysis)

            return {
                'report_time': datetime.now().isoformat(),
                'current_risks': current_risks,
                'risk_history_analysis': risk_history_analysis,
                'risk_trends': risk_trends,
                'risk_summary': risk_summary,
                'stats': self.risk_stats,
            }

        except Exception as e:
            logger.error(f"生成风险报告失败: {e}")
            return {'error': str(e)}

    # ========== 私有方法 ==========

    async def _initialize_risk_models(self) -> None:
        """初始化风险模型"""
        # 这里可以初始化各种风险模型
        # 例如VaR模型、压力测试模型等
        pass

    async def _assess_signal_risk(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """评估信号风险

        Args:
            signal: 信号字典

        Returns:
            风险评估字典
        """
        try:
            # 基础风险检查
            if signal.get('action') == 'hold':
                return {
                    'action': RiskAction.APPROVE.value,
                    'risk_level': RiskLevel.LOW.value,
                    'reason': 'Hold signal has no risk',
                }

            # 检查信号置信度
            confidence = signal.get('confidence', 0)
            if confidence < 0.6:
                return {
                    'action': RiskAction.REJECT.value,
                    'risk_level': RiskLevel.HIGH.value,
                    'reason': f'Signal confidence too low: {confidence:.2f}',
                }

            # 检查仓位大小
            position_size = signal.get('position_size', 0)
            if position_size > self.risk_limits['max_position_size']:
                return {
                    'action': RiskAction.REDUCE_SIZE.value,
                    'risk_level': RiskLevel.HIGH.value,
                    'reason': f'Position size exceeds limit: {position_size:.2f} > {self.risk_limits["max_position_size"]:.2f}',
                }

            # 检查单次损失风险
            if signal.get('action') in ['buy', 'sell']:
                # 估算潜在损失（假设2%的波动）
                potential_loss = position_size * 0.02
                if potential_loss > self.risk_limits['max_single_loss_percent'] * position_size:
                    return {
                        'action': RiskAction.INCREASE_STOP_LOSS.value,
                        'risk_level': RiskLevel.MEDIUM.value,
                        'reason': f'Potential loss too high: {potential_loss:.2f}',
                    }

            # 通过所有检查
            return {
                'action': RiskAction.APPROVE.value,
                'risk_level': RiskLevel.LOW.value,
                'reason': 'Signal passes all risk checks',
            }

        except Exception as e:
            logger.error(f"评估信号风险失败: {e}")
            return {
                'action': RiskAction.REJECT.value,
                'risk_level': RiskLevel.HIGH.value,
                'reason': f'Risk assessment error: {e}',
            }

    def _combine_signal_assessments(self, assessments: List[Dict]) -> Dict[str, Any]:
        """综合评估信号

        Args:
            assessments: 评估列表

        Returns:
            综合评估字典
        """
        if not assessments:
            return {
                'action': RiskAction.REJECT.value,
                'risk_level': RiskLevel.HIGH.value,
                'reason': 'No signals to assess',
            }

        # 找出最高的风险等级
        max_risk_level = max(
            assessments,
            key=lambda x: self._compare_risk_levels(
                RiskLevel(x['risk_level']),
                RiskLevel.LOW
            )
        )

        # 综合行动
        actions = [a['action'] for a in assessments]
        if RiskAction.REJECT.value in actions:
            action = RiskAction.REJECT.value
            reason = 'Some signals were rejected'
        elif RiskAction.REDUCE_SIZE.value in actions:
            action = RiskAction.REDUCE_SIZE.value
            reason = 'Some signals require size reduction'
        elif RiskAction.INCREASE_STOP_LOSS.value in actions:
            action = RiskAction.INCREASE_STOP_LOSS.value
            reason = 'Some signals require increased stop loss'
        else:
            action = RiskAction.APPROVE.value
            reason = 'All signals approved'

        return {
            'action': action,
            'risk_level': max_risk_level['risk_level'],
            'reason': reason,
        }

    async def _calculate_portfolio_risk(
        self,
        positions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """计算投资组合风险

        Args:
            positions: 仓位列表

        Returns:
            投资组合风险字典
        """
        try:
            if not positions:
                return {
                    'total_exposure': 0.0,
                    'total_unrealized_pnl': 0.0,
                    'risk_level': RiskLevel.LOW.value,
                }

            # 计算总敞口
            total_exposure = sum(
                abs(p.get('size', 0) * p.get('current_price', 0))
                for p in positions
            )

            # 计算总未实现盈亏
            total_unrealized_pnl = sum(
                p.get('unrealized_pnl', 0)
                for p in positions
            )

            # 检查敞口限制
            risk_level = RiskLevel.LOW
            if total_exposure > self.risk_limits['max_total_exposure']:
                risk_level = RiskLevel.HIGH

            # 计算回撤
            peak_value = 100000.0  # 假设初始资金
            current_value = peak_value + total_unrealized_pnl
            drawdown_percent = (peak_value - current_value) / peak_value * 100

            if drawdown_percent > self.risk_limits['max_drawdown_percent']:
                risk_level = RiskLevel.CRITICAL
            elif drawdown_percent > self.risk_limits['max_drawdown_percent'] * 0.5:
                risk_level = RiskLevel.HIGH

            return {
                'total_exposure': total_exposure,
                'total_unrealized_pnl': total_unrealized_pnl,
                'drawdown_percent': drawdown_percent,
                'number_of_positions': len(positions),
                'risk_level': risk_level.value,
            }

        except Exception as e:
            logger.error(f"计算投资组合风险失败: {e}")
            return {
                'risk_level': RiskLevel.HIGH.value,
                'error': str(e),
            }

    def _check_risk_limits(
        self,
        portfolio_risk: Dict[str, Any],
        positions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """检查风险限制

        Args:
            portfolio_risk: 投资组合风险
            positions: 仓位列表

        Returns:
            违规列表
        """
        violations = []

        # 检查总敞口
        if portfolio_risk.get('total_exposure', 0) > self.risk_limits['max_total_exposure']:
            violations.append({
                'type': 'total_exposure',
                'reason': f'Total exposure exceeds limit: {portfolio_risk["total_exposure"]:.2f} > {self.risk_limits["max_total_exposure"]:.2f}',
                'current': portfolio_risk.get('total_exposure', 0),
                'limit': self.risk_limits['max_total_exposure'],
            })

        # 检查回撤
        if portfolio_risk.get('drawdown_percent', 0) > self.risk_limits['max_drawdown_percent']:
            violations.append({
                'type': 'drawdown',
                'reason': f'Drawdown exceeds limit: {portfolio_risk["drawdown_percent"]:.2f}% > {self.risk_limits["max_drawdown_percent"]:.2f}%',
                'current': portfolio_risk.get('drawdown_percent', 0),
                'limit': self.risk_limits['max_drawdown_percent'],
            })

        # 检查单个仓位
        for position in positions:
            position_size = abs(position.get('size', 0) * position.get('current_price', 0))
            if position_size > self.risk_limits['max_position_size']:
                violations.append({
                    'type': 'position_size',
                    'symbol': position.get('symbol', 'N/A'),
                    'reason': f'Position size exceeds limit: {position_size:.2f} > {self.risk_limits["max_position_size"]:.2f}',
                    'current': position_size,
                    'limit': self.risk_limits['max_position_size'],
                })

        return violations

    async def _get_position_risks(self) -> List[Dict[str, Any]]:
        """获取仓位风险

        Returns:
            仓位风险列表
        """
        # 这里应该从仓位管理器获取实际仓位
        # 暂时返回空列表
        return []

    async def _get_portfolio_risk(self) -> Dict[str, Any]:
        """获取投资组合风险

        Returns:
            投资组合风险字典
        """
        # 这里应该从仓位管理器获取实际投资组合
        # 暂时返回默认值
        return {
            'type': RiskType.PORTFOLIO_RISK.value,
            'level': RiskLevel.LOW.value,
            'exposure': 0.0,
            'unrealized_pnl': 0.0,
        }

    async def _get_market_risk(self) -> Dict[str, Any]:
        """获取市场风险

        Returns:
            市场风险字典
        """
        # 这里应该从市场数据管理器获取实际市场数据
        # 暂时返回默认值
        return {
            'type': RiskType.MARKET_RISK.value,
            'level': RiskLevel.LOW.value,
            'volatility': 0.0,
            'trend': 'stable',
        }

    async def _get_liquidity_risk(self) -> Dict[str, Any]:
        """获取流动性风险

        Returns:
            流动性风险字典
        """
        # 这里应该从市场数据管理器获取实际流动性数据
        # 暂时返回默认值
        return {
            'type': RiskType.LIQUIDITY_RISK.value,
            'level': RiskLevel.LOW.value,
            'liquidity_score': 100.0,
        }

    def _assess_overall_risk(self, risk_assessments: List[Dict]) -> RiskLevel:
        """评估整体风险

        Args:
            risk_assessments: 风险评估列表

        Returns:
            整体风险等级
        """
        if not risk_assessments:
            return RiskLevel.LOW

        # 找出最高的风险等级
        max_risk_level = max(
            assessments,
            key=lambda x: self._compare_risk_levels(
                RiskLevel(x.get('level', RiskLevel.LOW.value)),
                RiskLevel.LOW
            )
        )

        return RiskLevel(max_risk_level.get('level', RiskLevel.LOW.value))

    def _compare_risk_levels(self, level1: RiskLevel, level2: RiskLevel) -> int:
        """比较风险等级

        Args:
            level1: 风险等级1
            level2: 风险等级2

        Returns:
            1 if level1 > level2, 0 if equal, -1 if level1 < level2
        """
        risk_order = [
            RiskLevel.LOW,
            RiskLevel.MEDIUM,
            RiskLevel.HIGH,
            RiskLevel.CRITICAL,
        ]

        try:
            idx1 = risk_order.index(level1)
            idx2 = risk_order.index(level2)

            if idx1 > idx2:
                return 1
            elif idx1 < idx2:
                return -1
            else:
                return 0
        except ValueError:
            return 0

    def _determine_risk_level(self, portfolio_risk: Dict[str, Any]) -> RiskLevel:
        """确定风险等级

        Args:
            portfolio_risk: 投资组合风险

        Returns:
            风险等级
        """
        drawdown = portfolio_risk.get('drawdown_percent', 0)
        exposure = portfolio_risk.get('total_exposure', 0)

        # 基于回撤和敞口确定风险等级
        if drawdown > self.risk_limits['max_drawdown_percent']:
            return RiskLevel.CRITICAL
        elif drawdown > self.risk_limits['max_drawdown_percent'] * 0.7:
            return RiskLevel.HIGH
        elif drawdown > self.risk_limits['max_drawdown_percent'] * 0.3:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _is_circuit_breaker_active(self) -> bool:
        """检查熔断器是否激活

        Returns:
            是否激活
        """
        if not self.circuit_breaker_triggered:
            return False

        # 检查冷却时间
        if self.circuit_breaker_triggered_at:
            cooldown_end = self.circuit_breaker_triggered_at + timedelta(
                seconds=self.circuit_breaker_cooldown
            )
            if datetime.now() > cooldown_end:
                # 冷却结束，重置熔断器
                logger.info("✅ 熔断器冷却结束，重置熔断器")
                self.circuit_breaker_triggered = False
                self.circuit_breaker_triggered_at = None
                return False

        return True

    def _check_circuit_breaker(self) -> None:
        """检查熔断器"""
        if not self.enable_circuit_breaker:
            return

        # 清理过期的损失记录
        self._clean_recent_losses()

        # 计算窗口内的总损失 - 从字典中提取amount字段
        total_loss = sum(l['amount'] for l in self.recent_losses)

        if total_loss >= self.circuit_breaker_loss_threshold:
            # 触发熔断器
            self.circuit_breaker_triggered = True
            self.circuit_breaker_triggered_at = datetime.now()
            self.risk_stats['circuit_breaker_triggers'] += 1

            logger.warning(
                f"🚨 熔断器触发！窗口内总损失: ${total_loss:.2f}, "
                f"阈值: ${self.circuit_breaker_loss_threshold:.2f}"
            )

            # 记录熔断事件
            self._record_risk_event({
                'type': 'circuit_breaker',
                'level': RiskLevel.CRITICAL.value,
                'action': RiskAction.REJECT.value,
                'reason': f'Circuit breaker triggered: ${total_loss:.2f} loss in {self.circuit_breaker_window}s window',
            })

    def _add_to_recent_losses(self, loss: float) -> None:
        """添加到最近损失

        Args:
            loss: 损失金额
        """
        self.recent_losses.append({
            'amount': loss,
            'timestamp': datetime.now(),
        })

    def _clean_recent_losses(self) -> None:
        """清理过期的损失记录"""
        window_start = datetime.now() - timedelta(seconds=self.circuit_breaker_window)

        # 保留窗口内的损失记录
        self.recent_losses = deque([
            loss for loss in self.recent_losses
            if loss['timestamp'] >= window_start
        ])

    def _record_risk_event(self, event: Dict[str, Any]) -> None:
        """记录风险事件

        Args:
            event: 风险事件字典
        """
        event['recorded_at'] = datetime.now().isoformat()
        self.risk_events.append(event)

        # 限制历史大小
        if len(self.risk_events) > self.max_risk_events:
            self.risk_events = self.risk_events[-self.max_risk_events:]

    async def _risk_monitoring_loop(self) -> None:
        """风险监控循环"""
        while True:
            try:
                # 监控风险
                await self.monitor_risk()

                # 等待下一个周期
                await asyncio.sleep(self._risk_monitoring_interval)

            except asyncio.CancelledError:
                logger.info("风险监控任务已取消")
                break
            except Exception as e:
                logger.error(f"风险监控失败: {e}")
                await asyncio.sleep(10)  # 错误后等待10秒

    def _analyze_risk_history(self) -> Dict[str, Any]:
        """分析风险历史

        Returns:
            风险历史分析字典
        """
        if not self.risk_events:
            return {
                'total_events': 0,
                'events_by_level': {},
                'events_by_type': {},
            }

        # 按级别统计
        events_by_level = defaultdict(int)
        for event in self.risk_events:
            level = event.get('level', RiskLevel.LOW.value)
            events_by_level[level] += 1

        # 按类型统计
        events_by_type = defaultdict(int)
        for event in self.risk_events:
            event_type = event.get('type', 'unknown')
            events_by_type[event_type] += 1

        return {
            'total_events': len(self.risk_events),
            'events_by_level': dict(events_by_level),
            'events_by_type': dict(events_by_type),
            'recent_events': self.risk_events[-10:],  # 最近10个事件
        }

    def _calculate_risk_trends(self) -> Dict[str, Any]:
        """计算风险趋势

        Returns:
            风险趋势字典
        """
        # 这里可以实现更复杂的趋势分析
        # 暂时返回基本统计
        if not self.risk_events:
            return {
                'trend': 'stable',
                'avg_risk_level': RiskLevel.LOW.value,
            }

        # 计算最近的平均风险等级
        recent_events = self.risk_events[-50:]  # 最近50个事件
        risk_levels = [
            event.get('level', RiskLevel.LOW.value)
            for event in recent_events
        ]

        # 简单趋势分析
        high_risk_count = sum(1 for level in risk_levels if level in [RiskLevel.HIGH.value, RiskLevel.CRITICAL.value])
        if high_risk_count > len(recent_events) * 0.3:
            trend = 'increasing'
        elif high_risk_count < len(recent_events) * 0.1:
            trend = 'decreasing'
        else:
            trend = 'stable'

        return {
            'trend': trend,
            'recent_high_risk_count': high_risk_count,
            'recent_total_events': len(recent_events),
        }

    def _generate_risk_summary(
        self,
        current_risks: Dict[str, Any],
        risk_history_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成风险摘要

        Args:
            current_risks: 当前风险
            risk_history_analysis: 风险历史分析

        Returns:
            风险摘要字典
        """
        overall_risk_level = current_risks.get('overall_risk_level', RiskLevel.LOW.value)

        # 生成摘要
        summary = {
            'overall_risk_level': overall_risk_level,
            'status': self._get_risk_status_summary(overall_risk_level),
            'recommendations': self._generate_risk_recommendations(overall_risk_level),
        }

        return summary

    def _get_risk_status_summary(self, risk_level: str) -> str:
        """获取风险状态摘要

        Args:
            risk_level: 风险等级

        Returns:
            状态摘要
        """
        if risk_level == RiskLevel.LOW.value:
            return "所有风险指标正常，系统运行良好。"
        elif risk_level == RiskLevel.MEDIUM.value:
            return "存在中等风险，建议关注风险指标变化。"
        elif risk_level == RiskLevel.HIGH.value:
            return "风险水平较高，建议采取风险控制措施。"
        elif risk_level == RiskLevel.CRITICAL.value:
            return "风险水平严重，建议立即采取行动！"
        else:
            return "未知风险等级。"

    def _generate_risk_recommendations(self, risk_level: str) -> List[str]:
        """生成风险建议

        Args:
            risk_level: 风险等级

        Returns:
            建议列表
        """
        if risk_level == RiskLevel.LOW.value:
            return [
                "继续正常运行，定期检查风险指标。",
                "考虑适当增加仓位以优化收益。",
            ]
        elif risk_level == RiskLevel.MEDIUM.value:
            return [
                "密切监控风险指标变化。",
                "考虑降低仓位大小。",
                "检查止损设置是否合适。",
            ]
        elif risk_level == RiskLevel.HIGH.value:
            return [
                "立即降低仓位大小。",
                "收紧止损设置。",
                "暂停新开仓。",
                "考虑部分平仓。",
            ]
        elif risk_level == RiskLevel.CRITICAL.value:
            return [
                "立即停止所有交易！",
                "平仓所有仓位。",
                "审查交易策略。",
                "等待风险水平下降后再恢复交易。",
            ]
        else:
            return ["未知风险等级，建议审查系统状态。"]


# ========== 全局风险管理器V2实例 ==========

_risk_manager_v2_instance: Optional[RiskManagerV2] = None


def get_risk_manager_v2() -> RiskManagerV2:
    """获取风险管理器V2单例

    Returns:
        风险管理器V2实例
    """
    global _risk_manager_v2_instance
    if _risk_manager_v2_instance is None:
        _risk_manager_v2_instance = RiskManagerV2()
    return _risk_manager_v2_instance
