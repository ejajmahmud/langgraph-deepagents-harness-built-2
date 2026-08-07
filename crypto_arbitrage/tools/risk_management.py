"""风险管理和风控系统"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RiskManager:
    """风险管理器 - 实时风险监控和控制"""

    def __init__(self, config: Dict[str, Any]):
        """初始化风险管理器

        Args:
            config: 风险配置字典，包含:
                - max_daily_loss: 最大日亏损 ($)
                - max_position_size: 最大单笔仓位 ($)
                - max_total_exposure: 最大总敞口 ($)
                - max_drawdown: 最大回撤 (%)
                - min_liquidity_ratio: 最小流动性比率
        """
        self.config = config
        self.max_daily_loss = config.get('max_daily_loss', 500)  # 默认$500
        self.max_position_size = config.get('max_position_size', 1000)  # 默认$1000
        self.max_total_exposure = config.get('max_total_exposure', 5000)  # 默认$5000
        self.max_drawdown = config.get('max_drawdown', 10.0)  # 默认10%

        # 实时风险状态
        self.current_exposure = 0.0  # 当前总敞口
        self.daily_pnl = 0.0  # 今日盈亏
        self.daily_trades = 0  # 今日交易次数
        self.risk_alerts: List[Dict] = []  # 风险告警记录

        # 历史数据
        self.pnl_history: List[Dict] = []
        self.peak_balance = 0.0  # 历史最高余额
        self._current_balance = 10000.0  # V1.9.0: 使用增量追踪，O(1)

        logger.info("风险管理器初始化完成")

    def check_position_risk(self, position: Dict[str, Any]) -> bool:
        """检查仓位风险

        Args:
            position: 仓位信息字典，包含:
                - amount: 仓位大小 ($)
                - symbol: 交易对
                - strategy: 策略类型

        Returns:
            是否通过风险检查
        """
        # 检查仓位大小
        position_size = position.get('amount', 0)
        if position_size > self.max_position_size:
            logger.warning(f"仓位过大被拒绝: {position_size} > {self.max_position_size}")
            return False

        # 检查总敞口
        if self.current_exposure + position_size > self.max_total_exposure:
            logger.warning(f"总敞口超限被拒绝: {self.current_exposure + position_size} > {self.max_total_exposure}")
            return False

        # 检查日亏损
        if self.daily_pnl < -self.max_daily_loss:
            logger.error(f"达到日亏损上限，停止交易: {self.daily_pnl} < -{self.max_daily_loss}")
            self._create_risk_alert("DAILY_LOSS_LIMIT", f"日亏损达到上限: {self.daily_pnl}")
            return False

        return True

    def update_exposure(self, amount: float, is_increase: bool = True) -> None:
        """更新当前敞口

        Args:
            amount: 变化金额
            is_increase: 是否增加敞口
        """
        if is_increase:
            self.current_exposure += amount
        else:
            self.current_exposure = max(0, self.current_exposure - amount)

        logger.debug(f"敞口更新: {self.current_exposure:.2f}")

    def record_trade_result(self, trade_result: Dict[str, Any]) -> None:
        """记录交易结果

        Args:
            trade_result: 交易结果字典，包含:
                - profit: 实际利润
                - expected_profit: 预期利润
                - strategy: 策略类型
        """
        profit = trade_result.get('profit', 0)
        self.daily_pnl += profit
        self.daily_trades += 1

        # BUG FIX #4: 使用增量计算代替 O(n) 累加
        prev_cumulative = (
            self.pnl_history[-1]['cumulative_pnl']
            if self.pnl_history else 0
        )
        self.pnl_history.append({
            'timestamp': datetime.now(),
            'profit': profit,
            'strategy': trade_result.get('strategy'),
            'cumulative_pnl': prev_cumulative + profit
        })

        # 更新增量余额 (V1.9.0)
        self._current_balance += profit

        # 更新最高余额
        current_balance = self._get_current_balance()
        if current_balance > self.peak_balance:
            self.peak_balance = current_balance

        logger.info(f"交易记录: 盈亏 {profit:.2f}, 日累计 {self.daily_pnl:.2f}, 交易次数 {self.daily_trades}")

    def check_drawdown(self) -> bool:
        """检查回撤风险

        Returns:
            回撤是否在可接受范围内
        """
        current_balance = self._get_current_balance()
        if self.peak_balance == 0:
            return True

        drawdown = ((self.peak_balance - current_balance) / self.peak_balance) * 100

        if drawdown > self.max_drawdown:
            logger.error(f"回撤超限: {drawdown:.2f}% > {self.max_drawdown}%")
            self._create_risk_alert("DRAWDOWN_LIMIT", f"回撤达到上限: {drawdown:.2f}%")
            return False

        return True

    def _get_current_balance(self) -> float:
        """获取当前余额 - V1.9.0 O(1)增量版本

        Returns:
            当前余额
        """
        return self._current_balance

    def _create_risk_alert(self, alert_type: str, message: str) -> None:
        """创建风险告警

        Args:
            alert_type: 告警类型
            message: 告警信息
        """
        alert = {
            'type': alert_type,
            'message': message,
            'timestamp': datetime.now(),
            'severity': 'HIGH'
        }
        self.risk_alerts.append(alert)
        logger.error(f"风险告警: {alert_type} - {message}")

    def get_risk_summary(self) -> Dict[str, Any]:
        """获取风险摘要

        Returns:
            风险摘要字典
        """
        current_balance = self._get_current_balance()
        drawdown = 0
        if self.peak_balance > 0:
            drawdown = ((self.peak_balance - current_balance) / self.peak_balance) * 100

        return {
            'current_exposure': self.current_exposure,
            'max_total_exposure': self.max_total_exposure,
            'exposure_utilization': (self.current_exposure / self.max_total_exposure * 100)
            if self.max_total_exposure > 0 else 0,
            'daily_pnl': self.daily_pnl,
            'daily_trades': self.daily_trades,
            'current_balance': current_balance,
            'peak_balance': self.peak_balance,
            'drawdown': drawdown,
            'max_drawdown': self.max_drawdown,
            'risk_alerts_count': len(self.risk_alerts),
            'is_risk_limit_reached': (
                self.daily_pnl < -self.max_daily_loss or
                drawdown > self.max_drawdown or
                self.current_exposure > self.max_total_exposure
            )
        }

    def reset_daily_stats(self) -> None:
        """重置日统计"""
        logger.info(f"重置日统计: 前一日盈亏 {self.daily_pnl}, 交易次数 {self.daily_trades}")
        self.daily_pnl = 0.0
        self.daily_trades = 0


class IntelligentStopLoss:
    """智能止损系统 - 动态止损和止盈"""

    def __init__(self, config: Dict[str, Any]):
        """初始化智能止损系统

        Args:
            config: 配置字典，包含:
                - base_stop_loss: 基础止损比例 (%)
                - base_take_profit: 基础止盈比例 (%)
                - trailing_stop: 追踪止损比例 (%)
                - volatility_adjustment: 波动率调整因子
        """
        self.config = config
        self.base_stop_loss = config.get('base_stop_loss', 2.0)  # 默认2%
        self.base_take_profit = config.get('base_take_profit', 1.0)  # 默认1%
        self.trailing_stop = config.get('trailing_stop', 0.5)  # 默认0.5%
        self.volatility_adjustment = config.get('volatility_adjustment', 1.5)  # 默认1.5

    def calculate_stop_loss(
        self,
        entry_price: float,
        position_size: float,
        volatility: Optional[float] = None
    ) -> Dict[str, float]:
        """计算止损价格

        Args:
            entry_price: 开仓价格
            position_size: 仓位大小
            volatility: 市场波动率

        Returns:
            止损配置字典，包含:
                - stop_loss_price: 止损价格
                - stop_loss_amount: 止损金额
                - stop_loss_rate: 止损比例
        """
        # 基础止损比例
        stop_loss_rate = self.base_stop_loss

        # 根据波动率调整
        if volatility and volatility > 0:
            adjusted_stop_loss = stop_loss_rate * (1 + volatility * self.volatility_adjustment)
            stop_loss_rate = min(adjusted_stop_loss, self.base_stop_loss * 3)  # 上限3倍

        # 计算止损价格
        stop_loss_price = entry_price * (1 - stop_loss_rate / 100)
        stop_loss_amount = (entry_price - stop_loss_price) * position_size

        return {
            'stop_loss_price': stop_loss_price,
            'stop_loss_amount': stop_loss_amount,
            'stop_loss_rate': stop_loss_rate
        }

    def calculate_take_profit(
        self,
        entry_price: float,
        stop_loss_rate: float,
        risk_reward_ratio: float = 2.0
    ) -> Dict[str, float]:
        """计算止盈价格

        Args:
            entry_price: 开仓价格
            stop_loss_rate: 止损比例
            risk_reward_ratio: 风险回报比

        Returns:
            止盈配置字典
        """
        # 根据风险回报比计算止盈比例
        take_profit_rate = stop_loss_rate * risk_reward_ratio

        # 计算止盈价格
        take_profit_price = entry_price * (1 + take_profit_rate / 100)

        return {
            'take_profit_price': take_profit_price,
            'take_profit_rate': take_profit_rate,
            'risk_reward_ratio': risk_reward_ratio
        }

    def update_trailing_stop(
        self,
        current_price: float,
        entry_price: float,
        highest_price: float,
        trailing_stop_rate: Optional[float] = None
    ) -> float:
        """更新追踪止损价格

        Args:
            current_price: 当前价格
            entry_price: 开仓价格
            highest_price: 最高价格
            trailing_stop_rate: 追踪止损比例

        Returns:
            新的追踪止损价格
        """
        if trailing_stop_rate is None:
            trailing_stop_rate = self.trailing_stop

        # 如果当前价格创新高，更新最高价
        new_highest = max(highest_price, current_price)

        # 计算追踪止损价格
        trailing_stop_price = new_highest * (1 - trailing_stop_rate / 100)

        # 确保追踪止损不低于基础止损
        base_stop_price = entry_price * (1 - self.base_stop_loss / 100)
        final_stop_price = max(trailing_stop_price, base_stop_price)

        return final_stop_price


class MarketConditionAnalyzer:
    """市场条件分析器 - 评估市场环境对交易的影响"""

    def __init__(self):
        """初始化市场条件分析器"""
        self.market_conditions: Dict[str, Any] = {
            'volatility': 'normal',
            'trend': 'neutral',
            'liquidity': 'normal',
            'sentiment': 'neutral'
        }

    def analyze_market_conditions(
        self,
        price_data: List[float],
        volume_data: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """分析市场条件

        Args:
            price_data: 价格历史数据
            volume_data: 成交量数据 (可选)

        Returns:
            市场条件分析结果
        """
        if len(price_data) < 10:
            return self.market_conditions

        # 计算波动率
        returns = [
            (price_data[i] - price_data[i-1]) / price_data[i-1]
            for i in range(1, len(price_data))
        ]
        volatility = (sum(r**2 for r in returns) / len(returns)) ** 0.5

        # 判断波动率水平
        if volatility < 0.01:
            self.market_conditions['volatility'] = 'low'
        elif volatility < 0.03:
            self.market_conditions['volatility'] = 'normal'
        else:
            self.market_conditions['volatility'] = 'high'

        # 判断趋势
        recent_trend = price_data[-1] - price_data[-5]
        if recent_trend > 0:
            self.market_conditions['trend'] = 'bullish'
        elif recent_trend < 0:
            self.market_conditions['trend'] = 'bearish'
        else:
            self.market_conditions['trend'] = 'neutral'

        # 判断流动性 (基于成交量)
        if volume_data and len(volume_data) > 0:
            avg_volume = sum(volume_data[-5:]) / 5
            recent_volume = volume_data[-1]

            if recent_volume > avg_volume * 1.5:
                self.market_conditions['liquidity'] = 'high'
            elif recent_volume < avg_volume * 0.5:
                self.market_conditions['liquidity'] = 'low'
            else:
                self.market_conditions['liquidity'] = 'normal'

        return self.market_conditions

    def get_trading_recommendation(self) -> Dict[str, Any]:
        """根据市场条件给出交易建议

        Returns:
            交易建议字典
        """
        conditions = self.market_conditions

        # 综合评估
        risk_level = 0

        # 高波动率增加风险
        if conditions['volatility'] == 'high':
            risk_level += 2
        elif conditions['volatility'] == 'low':
            risk_level -= 1

        # 趋势明确时套利风险更高
        if conditions['trend'] != 'neutral':
            risk_level += 1

        # 低流动性增加风险
        if conditions['liquidity'] == 'low':
            risk_level += 2
        elif conditions['liquidity'] == 'high':
            risk_level -= 1

        # 给出建议
        if risk_level <= -1:
            recommendation = 'highly_favorable'
            max_position_multiplier = 1.5
        elif risk_level == 0:
            recommendation = 'favorable'
            max_position_multiplier = 1.2
        elif risk_level == 1:
            recommendation = 'normal'
            max_position_multiplier = 1.0
        elif risk_level == 2:
            recommendation = 'cautious'
            max_position_multiplier = 0.7
        else:
            recommendation = 'avoid'
            max_position_multiplier = 0.3

        return {
            'recommendation': recommendation,
            'risk_level': risk_level,
            'max_position_multiplier': max_position_multiplier,
            'market_conditions': conditions
        }


# 创建全局风险管理器实例
risk_manager: Optional[RiskManager] = None


def initialize_risk_manager(config: Dict[str, Any]) -> RiskManager:
    """初始化全局风险管理器

    Args:
        config: 风险管理配置

    Returns:
        风险管理器实例
    """
    global risk_manager
    risk_manager = RiskManager(config)
    return risk_manager


def get_risk_manager() -> Optional[RiskManager]:
    """获取全局风险管理器实例

    Returns:
        风险管理器实例，如果未初始化则返回 None
    """
    return risk_manager
