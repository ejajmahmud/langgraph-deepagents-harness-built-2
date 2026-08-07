"""交易监控器 - Phase 13核心模块

监控交易活动和性能，检测交易异常，生成交易报告。

核心功能：
1. 实时交易监控 - 实时监控所有交易
2. 交易性能跟踪 - 跟踪交易性能指标
3. 交易异常检测 - 检测交易异常
4. 交易报告 - 生成详细的交易报告
5. 交易历史管理 - 管理交易历史

创建时间：2026-04-19 23:24:00
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class TradeSeverity(Enum):
    """交易严重程度"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class TradeAnomalyType(Enum):
    """交易异常类型"""
    FAILED_TRADE = "failed_trade"
    EXCESSIVE_SLIPPAGE = "excessive_slippage"
    ABNORMAL_DELAY = "abnormal_delay"
    EXECUTION_ERROR = "execution_error"
    UNUSUAL_PATTERN = "unusual_pattern"
    RISK_VIOLATION = "risk_violation"


class TradeMonitor:
    """交易监控器

    监控交易活动和性能。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化交易监控器

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 交易监控配置
        self.enable_monitoring = self.config.get('enable_monitoring', True)
        self.monitoring_interval = self.config.get('monitoring_interval', 5)  # 秒
        self.max_execution_time = self.config.get('max_execution_time', 30.0)  # 最大执行时间
        self.max_slippage_percent = self.config.get('max_slippage_percent', 0.5)  # 最大滑点百分比

        # 交易数据
        self.trades: Dict[str, Dict] = {}
        self.trade_history: List[Dict] = []
        self.max_trade_history = 1000

        # 性能指标
        self.performance_metrics = {
            'total_trades': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'avg_execution_time': 0.0,
            'avg_slippage': 0.0,
            'success_rate': 0.0,
            'total_profit': 0.0,
            'total_loss': 0.0,
            'profit_factor': 0.0,
        }

        # 异常检测
        self.anomalies: List[Dict] = []
        self.max_anomalies = 100
        self.anomaly_thresholds = {
            'failed_trades_count': 5,           # 5个失败交易
            'failed_trades_window': 300,         # 5分钟窗口
            'excessive_slippage_percent': 1.0,  # 1%滑点
            'abnormal_delay_seconds': 10.0,      # 10秒延迟
        }

        # 实时监控数据
        self.recent_trades: deque = deque(maxlen=100)
        self.recent_performance: deque = deque(maxlen=100)

        # 监控任务
        self._monitoring_task: Optional[asyncio.Task] = None

        # 事件处理器
        self.event_handlers: Dict[str, List] = {}

        # 存储引用
        self.storage: Optional[Any] = None

        logger.info("✅ 交易监控器初始化完成")

    async def initialize(self) -> bool:
        """初始化监控

        Returns:
            是否成功
        """
        logger.info("🚀 初始化交易监控器...")

        try:
            # 启动监控任务
            if self.enable_monitoring:
                self._monitoring_task = asyncio.create_task(
                    self._monitoring_loop()
                )
                logger.info("✅ 交易监控任务已启动")

            logger.info("✅ 交易监控器初始化完成")
            return True

        except Exception as e:
            logger.error(f"❌ 交易监控器初始化失败: {e}")
            return False

    async def stop(self) -> bool:
        """停止监控

        Returns:
            是否成功
        """
        logger.info("🛑 停止交易监控器...")

        try:
            # 停止监控任务
            if self._monitoring_task:
                self._monitoring_task.cancel()
                try:
                    await self._monitoring_task
                except asyncio.CancelledError:
                    pass

            logger.info("✅ 交易监控器已停止")
            return True

        except Exception as e:
            logger.error(f"❌ 停止交易监控器失败: {e}")
            return False

    async def start_monitoring(self) -> bool:
        """开始监控

        Returns:
            是否成功
        """
        logger.info("🚀 开始交易监控...")

        try:
            # 生成监控报告
            report = await self.generate_monitoring_report()

            logger.info(f"✅ 交易监控已启动: {report['total_trades']} 个交易, "
                       f"成功率: {report['success_rate']:.1%}")

            return True

        except Exception as e:
            logger.error(f"❌ 开始交易监控失败: {e}")
            return False

    async def stop_monitoring(self) -> bool:
        """停止监控

        Returns:
            是否成功
        """
        logger.info("🛑 停止交易监控...")

        try:
            # 生成最终报告
            final_report = await self.generate_final_report()

            logger.info(f"✅ 交易监控已停止: {final_report['summary']}")

            return True

        except Exception as e:
            logger.error(f"❌ 停止交易监控失败: {e}")
            return False

    async def monitor_trade(self, trade: Dict[str, Any]) -> Dict[str, Any]:
        """监控交易

        Args:
            trade: 交易字典

        Returns:
            监控结果字典
        """
        try:
            # 生成交易ID
            trade_id = trade.get('trade_id') or self._generate_trade_id()
            trade['trade_id'] = trade_id

            # 添加到交易列表
            self.trades[trade_id] = trade
            self.performance_metrics['total_trades'] += 1

            # 添加到最近交易
            self.recent_trades.append({
                'trade_id': trade_id,
                'timestamp': datetime.now(),
                'status': trade.get('status'),
            })

            # 检测异常
            anomalies = await self._detect_trade_anomalies(trade)

            if anomalies:
                # 记录异常
                for anomaly in anomalies:
                    self._record_anomaly(anomaly)

                return {
                    'trade_id': trade_id,
                    'status': trade.get('status'),
                    'anomalies': anomalies,
                    'has_anomalies': True,
                }
            else:
                return {
                    'trade_id': trade_id,
                    'status': trade.get('status'),
                    'has_anomalies': False,
                }

        except Exception as e:
            logger.error(f"❌ 监控交易失败: {e}")
            return {
                'error': str(e),
            }

    async def get_trade_performance(self) -> Dict[str, Any]:
        """获取交易性能

        Returns:
            性能字典
        """
        return self.performance_metrics.copy()

    async def generate_trade_report(
        self,
        report_type: str = 'daily'
    ) -> Dict[str, Any]:
        """生成交易报告

        Args:
            report_type: 报告类型（daily/weekly/monthly）

        Returns:
            交易报告字典
        """
        try:
            # 确定时间范围
            if report_type == 'daily':
                start_time = datetime.now() - timedelta(days=1)
            elif report_type == 'weekly':
                start_time = datetime.now() - timedelta(weeks=1)
            elif report_type == 'monthly':
                start_time = datetime.now() - timedelta(days=30)
            else:
                start_time = datetime.now() - timedelta(days=1)

            # 过滤交易
            filtered_trades = [
                trade for trade in self.trades.values()
                if datetime.fromisoformat(trade.get('created_at', '')) >= start_time
            ]

            # 生成报告
            report = {
                'report_type': report_type,
                'start_time': start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'total_trades': len(filtered_trades),
                'successful_trades': sum(1 for t in filtered_trades if t.get('status') == 'completed'),
                'failed_trades': sum(1 for t in filtered_trades if t.get('status') == 'failed'),
                'anomalies': [
                    anomaly for anomaly in self.anomalies
                    if datetime.fromisoformat(anomaly.get('detected_at', '')) >= start_time
                ],
                'performance_metrics': self._calculate_period_performance(filtered_trades),
            }

            # 计算成功率
            if report['total_trades'] > 0:
                report['success_rate'] = report['successful_trades'] / report['total_trades']
            else:
                report['success_rate'] = 0.0

            return report

        except Exception as e:
            logger.error(f"❌ 生成交易报告失败: {e}")
            return {
                'error': str(e),
            }

    async def generate_monitoring_report(self) -> Dict[str, Any]:
        """生成监控报告

        Returns:
            监控报告字典
        """
        try:
            return {
                'report_time': datetime.now().isoformat(),
                'total_trades': len(self.trades),
                'active_trades': len([
                    t for t in self.trades.values()
                    if t.get('status') in ['executing', 'queued']
                ]),
                'performance_metrics': self.performance_metrics,
                'recent_anomalies': self.anomalies[-10:],
                'monitoring_enabled': self.enable_monitoring,
                'anomaly_count': len(self.anomalies),
            }

        except Exception as e:
            logger.error(f"❌ 生成监控报告失败: {e}")
            return {
                'error': str(e),
            }

    async def generate_final_report(self) -> Dict[str, Any]:
        """生成最终报告

        Returns:
            最终报告字典
        """
        try:
            # 计算整体统计
            total_trades = len(self.trade_history)
            successful_trades = sum(1 for t in self.trade_history if t.get('status') == 'completed')
            failed_trades = sum(1 for t in self.trade_history if t.get('status') == 'failed')

            total_profit = sum(
                t.get('profit', 0)
                for t in self.trade_history
                if t.get('profit', 0) > 0
            )
            total_loss = sum(
                abs(t.get('profit', 0))
                for t in self.trade_history
                if t.get('profit', 0) < 0
            )

            profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')

            # 生成摘要
            summary = (
                f"总交易数: {total_trades}, "
                f"成功: {successful_trades}, "
                f"失败: {failed_trades}, "
                f"成功率: {(successful_trades / total_trades * 100):.1f}%"
            )

            return {
                'report_time': datetime.now().isoformat(),
                'summary': summary,
                'total_trades': total_trades,
                'successful_trades': successful_trades,
                'failed_trades': failed_trades,
                'success_rate': successful_trades / total_trades if total_trades > 0 else 0,
                'total_profit': total_profit,
                'total_loss': total_loss,
                'net_profit': total_profit - total_loss,
                'profit_factor': profit_factor,
                'total_anomalies': len(self.anomalies),
                'performance_metrics': self.performance_metrics,
            }

        except Exception as e:
            logger.error(f"❌ 生成最终报告失败: {e}")
            return {
                'error': str(e),
            }

    # ========== 私有方法 ==========

    async def _monitoring_loop(self) -> None:
        """监控循环"""
        while True:
            try:
                # 检测异常
                await self._detect_system_anomalies()

                # 更新性能指标
                self._update_performance_metrics()

                # 等待下一个周期
                await asyncio.sleep(self.monitoring_interval)

            except asyncio.CancelledError:
                logger.info("监控任务已取消")
                break
            except Exception as e:
                logger.error(f"监控任务失败: {e}")
                await asyncio.sleep(10)  # 错误后等待10秒

    async def _detect_trade_anomalies(self, trade: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检测交易异常

        Args:
            trade: 交易字典

        Returns:
            异常列表
        """
        anomalies = []

        try:
            # 检查失败交易
            if trade.get('status') == 'failed':
                anomalies.append({
                    'type': TradeAnomalyType.FAILED_TRADE.value,
                    'severity': TradeSeverity.ERROR.value,
                    'trade_id': trade.get('trade_id'),
                    'reason': trade.get('error', 'Unknown error'),
                    'detected_at': datetime.now().isoformat(),
                })

            # 检查执行时间
            execution_time = trade.get('execution_time')
            if execution_time and execution_time > self.max_execution_time:
                anomalies.append({
                    'type': TradeAnomalyType.ABNORMAL_DELAY.value,
                    'severity': TradeSeverity.WARNING.value,
                    'trade_id': trade.get('trade_id'),
                    'reason': f'Execution time {execution_time:.2f}s exceeds limit {self.max_execution_time:.2f}s',
                    'detected_at': datetime.now().isoformat(),
                })

            # 检查滑点
            execution_result = trade.get('execution_result', {})
            slippage = execution_result.get('slippage')
            if slippage and slippage > self.max_slippage_percent:
                anomalies.append({
                    'type': TradeAnomalyType.EXCESSIVE_SLIPPAGE.value,
                    'severity': TradeSeverity.WARNING.value,
                    'trade_id': trade.get('trade_id'),
                    'reason': f'Slippage {slippage:.2f}% exceeds limit {self.max_slippage_percent:.2f}%',
                    'detected_at': datetime.now().isoformat(),
                })

            # 检查执行错误
            if 'error' in trade:
                anomalies.append({
                    'type': TradeAnomalyType.EXECUTION_ERROR.value,
                    'severity': TradeSeverity.ERROR.value,
                    'trade_id': trade.get('trade_id'),
                    'reason': trade['error'],
                    'detected_at': datetime.now().isoformat(),
                })

        except Exception as e:
            logger.error(f"检测交易异常失败: {e}")

        return anomalies

    async def _detect_system_anomalies(self) -> None:
        """检测系统异常"""
        try:
            # 检查最近失败的交易数量
            failed_trades_count = sum(
                1 for trade in self.recent_trades
                if trade.get('status') == 'failed'
            )

            if failed_trades_count >= self.anomaly_thresholds['failed_trades_count']:
                self._record_anomaly({
                    'type': TradeAnomalyType.FAILED_TRADE.value,
                    'severity': TradeSeverity.CRITICAL.value,
                    'reason': f'{failed_trades_count} trades failed in recent window',
                    'detected_at': datetime.now().isoformat(),
                })

        except Exception as e:
            logger.error(f"检测系统异常失败: {e}")

    def _update_performance_metrics(self) -> None:
        """更新性能指标"""
        try:
            total_trades = self.performance_metrics['total_trades']

            if total_trades == 0:
                return

            # 计算成功率
            if total_trades > 0:
                self.performance_metrics['success_rate'] = (
                    self.performance_metrics['successful_trades'] / total_trades
                )

            # 计算利润因子
            total_loss = self.performance_metrics['total_loss']
            if total_loss > 0:
                self.performance_metrics['profit_factor'] = (
                    self.performance_metrics['total_profit'] / total_loss
                )

        except Exception as e:
            logger.error(f"更新性能指标失败: {e}")

    def _calculate_period_performance(self, trades: List[Dict]) -> Dict[str, Any]:
        """计算期间性能

        Args:
            trades: 交易列表

        Returns:
            性能字典
        """
        if not trades:
            return {
                'total_trades': 0,
                'successful_trades': 0,
                'failed_trades': 0,
                'avg_execution_time': 0.0,
                'avg_slippage': 0.0,
                'total_profit': 0.0,
                'total_loss': 0.0,
            }

        # 计算统计
        successful_trades = [t for t in trades if t.get('status') == 'completed']
        failed_trades = [t for t in trades if t.get('status') == 'failed']

        execution_times = [
            t.get('execution_time', 0)
            for t in trades
            if t.get('execution_time') is not None
        ]
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0

        slippages = [
            t.get('execution_result', {}).get('slippage', 0)
            for t in trades
        ]
        avg_slippage = sum(slippages) / len(slippages) if slippages else 0

        profits = [
            t.get('profit', 0)
            for t in trades
            if t.get('profit', 0) > 0
        ]
        losses = [
            abs(t.get('profit', 0))
            for t in trades
            if t.get('profit', 0) < 0
        ]

        return {
            'total_trades': len(trades),
            'successful_trades': len(successful_trades),
            'failed_trades': len(failed_trades),
            'avg_execution_time': avg_execution_time,
            'avg_slippage': avg_slippage,
            'total_profit': sum(profits),
            'total_loss': sum(losses),
        }

    def _record_anomaly(self, anomaly: Dict[str, Any]) -> None:
        """记录异常

        Args:
            anomaly: 异常字典
        """
        self.anomalies.append(anomaly)

        # 限制异常数量
        if len(self.anomalies) > self.max_anomalies:
            self.anomalies = self.anomalies[-self.max_anomalies:]

        # 记录到交易历史
        self.trade_history.append({
            'type': 'anomaly',
            'data': anomaly,
            'recorded_at': datetime.now().isoformat(),
        })

    def _generate_trade_id(self) -> str:
        """生成交易ID

        Returns:
            交易ID
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        import random
        random_str = ''.join(random.choices('0123456789ABCDEF', k=8))
        return f"MONITOR_{timestamp}_{random_str}"


# ========== 全局交易监控器实例 ==========

_trade_monitor_instance: Optional[TradeMonitor] = None


def get_trade_monitor() -> TradeMonitor:
    """获取交易监控器单例

    Returns:
        交易监控器实例
    """
    global _trade_monitor_instance
    if _trade_monitor_instance is None:
        _trade_monitor_instance = TradeMonitor()
    return _trade_monitor_instance
