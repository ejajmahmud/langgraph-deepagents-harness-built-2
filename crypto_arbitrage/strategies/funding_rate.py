"""资金费率套利策略实现

利用永续合约的资金费率机制进行套利：
- 当资金费率为正且较高时，做空永续合约 + 做多现货，收取资金费率
- 当资金费率为负且绝对值较高时，做多永续合约 + 做空现货，收取资金费率
- V2.1: 新增资金费率预测功能，基于历史数据预测未来趋势
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from strategies.base import BaseStrategy
from tools.exchange_api import get_exchange_manager

logger = logging.getLogger(__name__)


class FundingRatePredictor:
    """资金费率预测器 - V2.1"""

    def __init__(self, lookback_periods: int = 50):
        """初始化预测器

        Args:
            lookback_periods: 回溯期数（用于预测）
        """
        self.lookback_periods = lookback_periods
        self.history: Dict[str, List[Dict]] = {}

    def add_observation(self, symbol: str, rate: float, timestamp: Optional[float] = None) -> None:
        """添加观察数据

        Args:
            symbol: 交易对
            rate: 资金费率
            timestamp: 时间戳
        """
        if symbol not in self.history:
            self.history[symbol] = []

        self.history[symbol].append({
            'rate': rate,
            'timestamp': timestamp or time.time()
        })

        # 限制历史长度
        if len(self.history[symbol]) > self.lookback_periods * 2:
            self.history[symbol] = self.history[symbol][-self.lookback_periods * 2:]

    def predict_next_rate(self, symbol: str, periods_ahead: int = 1) -> Dict[str, Any]:
        """预测未来资金费率

        Args:
            symbol: 交易对
            periods_ahead: 向前预测的期数

        Returns:
            预测结果字典
        """
        if symbol not in self.history or len(self.history[symbol]) < self.lookback_periods:
            return {
                'predicted_rate': None,
                'confidence': 0.0,
                'trend': 'unknown',
                'method': 'insufficient_data'
            }

        data = self.history[symbol]
        rates = [d['rate'] for d in data]

        # 方法1: 移动平均
        ma_short = sum(rates[-10:]) / 10 if len(rates) >= 10 else rates[-1]
        ma_long = sum(rates[-30:]) / 30 if len(rates) >= 30 else ma_short

        # 方法2: 线性回归（简单版本）
        import math
        n = min(20, len(rates))
        recent_rates = rates[-n:]
        x = list(range(n))
        y = recent_rates

        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(xi * xi for xi in x)

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x) if (n * sum_x2 - sum_x * sum_x) != 0 else 0
        intercept = (sum_y - slope * sum_x) / n

        predicted_rate_linear = slope * (n + periods_ahead) + intercept

        # 方法3: 加权预测（结合移动平均和趋势）
        trend_strength = ma_short - ma_long
        predicted_rate = ma_short + trend_strength * periods_ahead * 0.5

        # 综合预测
        final_prediction = (predicted_rate + predicted_rate_linear) / 2

        # 计算置信度（基于波动率和一致性）
        recent_std = math.sqrt(sum((r - ma_short) ** 2 for r in rates[-10:]) / 10)
        consistency = 1.0 - min(recent_std / abs(ma_short) if abs(ma_short) > 0.01 else 0, 1.0)
        confidence = max(0.0, min(consistency, 0.9))

        # 确定趋势
        if trend_strength > 0.01:
            trend = 'rising'
        elif trend_strength < -0.01:
            trend = 'falling'
        else:
            trend = 'stable'

        return {
            'predicted_rate': final_prediction,
            'current_rate': rates[-1],
            'ma_short': ma_short,
            'ma_long': ma_long,
            'trend_strength': trend_strength,
            'trend': trend,
            'trend_indicator': '[UP]' if trend == 'rising' else '[DOWN]' if trend == 'falling' else '[FLAT]',  # V2.1: 可视化标识
            'confidence': confidence,
            'method': 'hybrid',
            'lookback_periods': len(rates)
        }

    def get_prediction_summary(self, symbol: str) -> str:
        """获取预测摘要

        Args:
            symbol: 交易对

        Returns:
            预测摘要字符串
        """
        prediction = self.predict_next_rate(symbol)

        if prediction['predicted_rate'] is None:
            return f"{symbol}: 数据不足，无法预测"

        current = prediction['current_rate']
        predicted = prediction['predicted_rate']
        trend = prediction['trend']
        confidence = prediction['confidence']

        # 使用 ASCII 兼容的趋势标识
        trend_indicator = prediction.get('trend_indicator', '[FLAT]')

        return (
            f"{symbol} {trend_indicator} "
            f"当前: {current:.4f}% -> 预测: {predicted:.4f}% "
            f"(置信度: {confidence:.0%}) "
            f"趋势: {trend}"
        )


class FundingRateArbitrageStrategy(BaseStrategy):
    """资金费率套利策略"""

    STRATEGY_NAME = "funding_rate"
    STRATEGY_DESCRIPTION = "资金费率套利策略 - 利用永续合约资金费率差异"

    def __init__(self, config: Dict[str, Any]):
        """初始化资金费率套利策略

        Args:
            config: 策略配置字典，包含:
                - min_funding_rate: 最小资金费率阈值 (%)
                - max_position_size: 最大仓位大小 ($)
                - symbols: 监控的交易对列表
                - holding_periods: 最少持仓期数（资金费率结算次数）
                - max_funding_rate: 最大资金费率（风险控制）
                - preferred_exchange: 首选交易所
        """
        # V1.7.0 Fix: 先设置子类属性，再调 super().__init__()
        self.max_funding_rate = config.get('max_funding_rate', 0.5)
        self.holding_periods = config.get('holding_periods', 3)
        self.symbols = config.get('symbols', ['BTC/USDT:USDT', 'ETH/USDT:USDT'])
        self.spot_symbols = config.get('spot_symbols', ['BTC/USDT', 'ETH/USDT'])
        self.preferred_exchange = config.get('preferred_exchange', None)

        # 从永续合约交易对映射到现货交易对
        self._symbol_map: Dict[str, str] = {}
        for perp, spot in zip(self.symbols, self.spot_symbols):
            self._symbol_map[perp] = spot

        self._funding_rate_history: Dict[str, List[Dict]] = {}

        super().__init__(config)

        # V2.1: 资金费率预测器
        self.funding_rate_predictor = FundingRatePredictor(lookback_periods=50)

    def validate_config(self) -> List[str]:
        """验证资金费率配置"""
        errors = super().validate_config()
        if len(self.symbols) != len(self.spot_symbols):
            errors.append(f"永续合约交易对数量({len(self.symbols)})与现货交易对数量({len(self.spot_symbols)})不匹配")
        return errors

    def _get_exchange_name(self, exchange_manager) -> Optional[str]:
        """获取首选交易所，避免硬编码交易所"""
        if self.preferred_exchange and self.preferred_exchange in exchange_manager.exchanges:
            return self.preferred_exchange
        for name in exchange_manager.exchanges:
            return name
        return None

    async def scan_opportunities(self) -> List[Dict[str, Any]]:
        """扫描资金费率套利机会"""
        exchange_manager = get_exchange_manager()
        if not exchange_manager:
            logger.error("交易所管理器未初始化")
            return []

        opportunities = []

        for perp_symbol in self.symbols:
            try:
                opportunity = await self._analyze_funding_rate(
                    perp_symbol, exchange_manager
                )
                if opportunity:
                    opportunities.append(opportunity)
            except Exception as e:
                logger.error(f"分析 {perp_symbol} 资金费率失败: {e}")

        # 使用基类方法统一过滤和排序
        logger.info(f"发现 {len(opportunities)} 个资金费率套利机会（过滤前）")
        return self._post_process_opportunities(opportunities, sort_key='annualized_return')

    async def _analyze_funding_rate(
        self,
        perp_symbol: str,
        exchange_manager
    ) -> Optional[Dict[str, Any]]:
        """分析单个交易对的资金费率"""
        funding_rate = await self._get_funding_rate(perp_symbol, exchange_manager)
        if funding_rate is None:
            return None

        abs_rate = abs(funding_rate)

        # 记录历史
        if perp_symbol not in self._funding_rate_history:
            self._funding_rate_history[perp_symbol] = []
        self._funding_rate_history[perp_symbol].append({
            'rate': funding_rate,
            'timestamp': time.time()
        })

        # V2.1: 更新预测器
        self.funding_rate_predictor.add_observation(perp_symbol, funding_rate, time.time())

        if abs_rate < self.min_profit_rate:
            logger.debug(f"{perp_symbol} 资金费率过低: {funding_rate:.4f}%")
            return None

        if abs_rate > self.max_funding_rate:
            logger.warning(f"{perp_symbol} 资金费率异常高: {funding_rate:.4f}%, 跳过")
            return None

        spot_symbol = self._symbol_map.get(perp_symbol)
        if not spot_symbol:
            spot_symbol = perp_symbol.replace(':USDT', '')

        spot_price = await self._get_price(spot_symbol, exchange_manager)
        perp_price = await self._get_price(perp_symbol, exchange_manager)

        if not spot_price or not perp_price:
            return None

        is_positive = funding_rate > 0
        direction = "long_spot_short_perp" if is_positive else "short_spot_long_perp"

        daily_funding = abs_rate * 3
        annualized_return = daily_funding * 365

        position_value = self.max_position_size
        per_settlement_profit = position_value * (abs_rate / 100)
        daily_profit = per_settlement_profit * 3

        price_spread = abs(perp_price - spot_price) / spot_price * 100

        open_cost = position_value * 0.0008
        close_cost = position_value * 0.0008
        total_trading_cost = open_cost + close_cost

        break_even_days = total_trading_cost / daily_profit if daily_profit > 0 else float('inf')

        # V2.1: 获取预测信息
        prediction = None
        try:
            prediction = self.funding_rate_predictor.predict_next_rate(perp_symbol, periods_ahead=1)
            if prediction.get('predicted_rate') is not None:
                logger.debug(f"资金费率预测: {self.funding_rate_predictor.get_prediction_summary(perp_symbol)}")
        except Exception as e:
            logger.debug(f"资金费率预测失败: {e}")

        opportunity = {
            'symbol': perp_symbol,
            'spot_symbol': spot_symbol,
            'direction': direction,
            'funding_rate': funding_rate,
            'abs_funding_rate': abs_rate,
            'daily_funding_income': daily_funding,
            'annualized_return': annualized_return,
            'per_settlement_profit': per_settlement_profit,
            'daily_profit': daily_profit,
            'spot_price': spot_price,
            'perp_price': perp_price,
            'price_spread': price_spread,
            'position_value': position_value,
            'total_trading_cost': total_trading_cost,
            'break_even_days': break_even_days,
            'min_holding_periods': self.holding_periods,
            'profit_rate': daily_funding,
            'expected_profit': daily_profit * self.holding_periods / 3,
            'timestamp': time.time(),
            # V2.1: 预测信息
            '_prediction': prediction
        }

        logger.info(
            f"资金费率机会: {perp_symbol} rate={funding_rate:.4f}% "
            f"日收益=${daily_profit:.2f} 年化={annualized_return:.1f}% "
            f"回本={break_even_days:.1f}天"
        )

        return opportunity

    async def _get_funding_rate(self, symbol: str, exchange_manager) -> Optional[float]:
        """获取资金费率"""
        try:
            for ex_name, ex_instance in exchange_manager.exchanges.items():
                try:
                    if hasattr(ex_instance, 'fetch_funding_rate'):
                        rate_info = await ex_instance.fetch_funding_rate(symbol)
                        if rate_info:
                            rate = rate_info.get('fundingRate', 0)
                            return rate * 100
                except Exception as e:
                    logger.debug(f"从 {ex_name} 获取 {symbol} 资金费率失败: {e}")
                    continue
        except Exception as e:
            logger.error(f"获取资金费率失败: {e}")
        return None

    async def _get_price(self, symbol: str, exchange_manager) -> Optional[float]:
        """获取最新价格"""
        try:
            for ex_name in exchange_manager.exchanges.keys():
                ticker = await exchange_manager.get_ticker(ex_name, symbol)
                if ticker and ticker.get('last'):
                    return ticker['last']
        except Exception:
            pass
        return None

    async def execute_arbitrage(self, opportunity: Dict[str, Any]) -> bool:
        """执行资金费率套利交易"""
        exchange_manager = get_exchange_manager()
        if not exchange_manager:
            logger.error("交易所管理器未初始化")
            return False

        symbol = opportunity['symbol']
        spot_symbol = opportunity['spot_symbol']
        direction = opportunity['direction']
        position_value = opportunity['position_value']

        # Fix: 使用 preferred_exchange 代替硬编码
        ex_name = self._get_exchange_name(exchange_manager)
        if not ex_name:
            logger.error("无可用交易所")
            return False

        if direction == "long_spot_short_perp":
            spot_side = 'buy'
            perp_side = 'sell'
        else:
            spot_side = 'sell'
            perp_side = 'buy'

        logger.info(f"开始执行资金费率套利: {symbol} {direction}")

        try:
            spot_price = opportunity['spot_price']
            spot_amount = position_value / spot_price

            spot_order = await exchange_manager.place_order(
                ex_name, spot_symbol, 'market', spot_side, spot_amount
            )
            if not spot_order:
                logger.error("现货开仓失败")
                return False

            await asyncio.sleep(2)

            perp_price = opportunity['perp_price']
            perp_amount = position_value / perp_price

            perp_order = await exchange_manager.place_order(
                ex_name, symbol, 'market', perp_side, perp_amount
            )
            if not perp_order:
                logger.error("永续合约开仓失败，需要平掉现货仓位")
                await exchange_manager.place_order(
                    ex_name, spot_symbol, 'market',
                    'sell' if spot_side == 'buy' else 'buy', spot_amount
                )
                return False

            position = {
                'symbol': symbol,
                'spot_symbol': spot_symbol,
                'direction': direction,
                'spot_order_id': spot_order.get('id'),
                'perp_order_id': perp_order.get('id'),
                'position_value': position_value,
                'spot_amount': spot_amount,
                'perp_amount': perp_amount,
                'entry_funding_rate': opportunity['funding_rate'],
                'daily_profit': opportunity['daily_profit'],
                'settlements_collected': 0,
                'target_settlements': self.holding_periods,
                'status': 'open',
                'open_time': time.time(),
                'timestamp': time.time()
            }

            self.active_positions.append(position)
            logger.info(f"资金费率套利开仓成功: {symbol} {direction}")
            return True

        except Exception as e:
            logger.error(f"资金费率套利执行失败: {e}")
            return False

    async def monitor_positions(self) -> List[Dict[str, Any]]:
        """监控当前持仓，检查是否应该平仓"""
        close_list = []
        exchange_manager = get_exchange_manager()
        if not exchange_manager:
            return close_list

        for position in self.active_positions:
            if position.get('status') != 'open':
                continue

            symbol = position['symbol']
            current_rate = await self._get_funding_rate(symbol, exchange_manager)
            holding_hours = (time.time() - position['open_time']) / 3600
            expected_settlements = holding_hours / 8

            should_close = False
            close_reason = ""

            if current_rate is not None:
                abs_current = abs(current_rate)
                if abs_current < self.min_profit_rate * 0.5:
                    should_close = True
                    close_reason = f"资金费率下降: {current_rate:.4f}% < {self.min_profit_rate * 0.5:.4f}%"

                if (position['entry_funding_rate'] > 0 and current_rate < 0) or \
                   (position['entry_funding_rate'] < 0 and current_rate > 0):
                    should_close = True
                    close_reason = f"资金费率方向反转: {current_rate:.4f}%"

            if expected_settlements >= position['target_settlements']:
                should_close = True
                close_reason = f"达到目标持仓期: {expected_settlements:.1f}次结算"

            if should_close:
                close_list.append({
                    'position': position,
                    'reason': close_reason,
                    'current_funding_rate': current_rate
                })

        return close_list

    async def close_position(self, position: Dict[str, Any]) -> bool:
        """关闭持仓"""
        exchange_manager = get_exchange_manager()
        if not exchange_manager:
            return False

        try:
            ex_name = self._get_exchange_name(exchange_manager)
            if not ex_name:
                logger.error("无可用交易所")
                return False

            direction = position['direction']

            if direction == "long_spot_short_perp":
                await exchange_manager.place_order(
                    ex_name, position['spot_symbol'], 'market', 'sell', position['spot_amount']
                )
                await exchange_manager.place_order(
                    ex_name, position['symbol'], 'market', 'buy', position['perp_amount']
                )
            else:
                await exchange_manager.place_order(
                    ex_name, position['spot_symbol'], 'market', 'buy', position['spot_amount']
                )
                await exchange_manager.place_order(
                    ex_name, position['symbol'], 'market', 'sell', position['perp_amount']
                )

            position['status'] = 'closed'
            position['close_time'] = time.time()
            position['holding_hours'] = (position['close_time'] - position['open_time']) / 3600

            logger.info(f"资金费率持仓已关闭: {position['symbol']}")
            return True

        except Exception as e:
            logger.error(f"关闭持仓失败: {e}")
            return False

    def get_funding_rate_predictions(self, symbols: Optional[List[str]] = None) -> Dict[str, str]:
        """获取所有交易对的资金费率预测（V2.1）

        Args:
            symbols: 交易对列表，None 则返回所有

        Returns:
            预测摘要字典
        """
        target_symbols = symbols or list(self.funding_rate_predictor.history.keys())
        predictions = {}

        for symbol in target_symbols:
            try:
                summary = self.funding_rate_predictor.get_prediction_summary(symbol)
                predictions[symbol] = summary
            except Exception as e:
                predictions[symbol] = f"{symbol}: 预测失败 - {e}"

        return predictions

    def predict_funding_rate(self, symbol: str, periods_ahead: int = 1) -> Dict[str, Any]:
        """预测指定交易对的资金费率（V2.1）

        Args:
            symbol: 交易对
            periods_ahead: 向前预测的期数

        Returns:
            预测结果字典
        """
        return self.funding_rate_predictor.predict_next_rate(symbol, periods_ahead)
