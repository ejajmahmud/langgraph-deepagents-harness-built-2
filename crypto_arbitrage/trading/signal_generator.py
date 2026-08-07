"""信号生成器 - Phase 13核心模块

生成交易信号，支持多个交易策略的信号生成和综合评估。

核心功能：
1. 多策略信号生成 - 支持多个交易策略的信号生成
2. 信号综合评估 - 综合多个策略的信号
3. 信号置信度计算 - 计算信号的置信度
4. 信号历史管理 - 管理信号历史和性能
5. 信号过滤 - 过滤低质量信号

创建时间：2026-04-19 23:08:00
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class SignalAction(Enum):
    """信号动作"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class SignalQuality(Enum):
    """信号质量"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    INVALID = "invalid"


class SignalGenerator:
    """信号生成器

    生成交易信号。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化信号生成器

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 策略管理
        self.strategies: Dict[str, Dict] = {}
        self.active_strategies: List[str] = []
        self.strategy_performance: Dict[str, Dict] = defaultdict(dict)

        # 信号历史
        self.signal_history: List[Dict] = []
        self.max_signal_history = 1000

        # 信号配置
        self.min_confidence_threshold = self.config.get('min_confidence_threshold', 0.6)
        self.enable_signal_filtering = self.config.get('enable_signal_filtering', True)
        self.max_signals_per_cycle = self.config.get('max_signals_per_cycle', 10)

        # 信号统计
        self.stats = {
            'total_signals': 0,
            'buy_signals': 0,
            'sell_signals': 0,
            'hold_signals': 0,
            'high_confidence_signals': 0,
            'avg_confidence': 0.0,
        }

        # 市场数据缓存
        self.market_data_cache: Dict[str, Any] = {}
        self.market_data_ttl = self.config.get('market_data_ttl', 5)  # 秒

        # 存储引用
        self.storage: Optional[Any] = None

        logger.info("✅ 信号生成器初始化完成")

    async def initialize(self) -> bool:
        """初始化策略

        Returns:
            是否成功
        """
        logger.info("🚀 初始化信号生成器...")

        try:
            # 注册默认策略
            await self._register_default_strategies()

            # 启用所有策略
            self.active_strategies = list(self.strategies.keys())
            logger.info(f"✅ 已启用 {len(self.active_strategies)} 个策略")

            logger.info("✅ 信号生成器初始化完成")
            return True

        except Exception as e:
            logger.error(f"❌ 信号生成器初始化失败: {e}")
            return False

    async def generate_signals(
        self,
        market_data: Dict[str, Any]
    ) -> Optional[List[Dict[str, Any]]]:
        """生成信号

        Args:
            market_data: 市场数据

        Returns:
            信号列表
        """
        try:
            # 更新市场数据缓存
            self._update_market_data_cache(market_data)

            # 为每个活动策略生成信号
            all_signals = []

            for strategy_name in self.active_strategies:
                strategy_signals = await self._generate_strategy_signals(
                    strategy_name,
                    market_data
                )
                if strategy_signals:
                    all_signals.extend(strategy_signals)

            # 评估信号
            evaluated_signals = await self.evaluate_signals(all_signals)

            # 过滤信号
            if self.enable_signal_filtering:
                filtered_signals = self.filter_signals(evaluated_signals)
            else:
                filtered_signals = evaluated_signals

            # 限制信号数量
            filtered_signals = filtered_signals[:self.max_signals_per_cycle]

            # 记录信号
            self._record_signals(filtered_signals)

            # 更新统计
            self._update_stats(filtered_signals)

            return filtered_signals

        except Exception as e:
            logger.error(f"生成信号失败: {e}")
            return None

    async def evaluate_signals(
        self,
        signals: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """评估信号

        Args:
            signals: 信号列表

        Returns:
            评估后的信号列表
        """
        try:
            evaluated_signals = []

            for signal in signals:
                # 评估信号质量
                quality = self._assess_signal_quality(signal)
                signal['quality'] = quality.value

                # 检查信号一致性
                consistency = self._check_signal_consistency(signal)
                signal['consistency'] = consistency

                # 验证信号
                is_valid = self._validate_signal(signal)
                signal['is_valid'] = is_valid

                # 计算置信度
                if is_valid:
                    confidence = self._calculate_confidence(signal, quality)
                    signal['confidence'] = confidence
                else:
                    signal['confidence'] = 0.0

                evaluated_signals.append(signal)

            return evaluated_signals

        except Exception as e:
            logger.error(f"评估信号失败: {e}")
            return signals

    def filter_signals(
        self,
        signals: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """过滤信号

        Args:
            signals: 信号列表

        Returns:
            过滤后的信号列表
        """
        try:
            filtered_signals = []

            for signal in signals:
                # 检查有效性
                if not signal.get('is_valid', False):
                    continue

                # 检查置信度
                if signal.get('confidence', 0) < self.min_confidence_threshold:
                    continue

                # 按置信度过滤
                if signal.get('quality') in [SignalQuality.POOR.value, SignalQuality.INVALID.value]:
                    continue

                filtered_signals.append(signal)

            return filtered_signals

        except Exception as e:
            logger.error(f"过滤信号失败: {e}")
            return signals

    def get_signal_history(
        self,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取信号历史

        Args:
            limit: 返回数量限制

        Returns:
            信号历史列表
        """
        return self.signal_history[-limit:]

    def register_strategy(
        self,
        name: str,
        strategy_config: Dict[str, Any]
    ) -> None:
        """注册策略

        Args:
            name: 策略名称
            strategy_config: 策略配置
        """
        self.strategies[name] = strategy_config
        logger.info(f"注册策略: {name}")

    def remove_strategy(self, name: str) -> None:
        """移除策略

        Args:
            name: 策略名称
        """
        if name in self.strategies:
            del self.strategies[name]
            if name in self.active_strategies:
                self.active_strategies.remove(name)
            logger.info(f"移除策略: {name}")

    def enable_strategy(self, name: str) -> bool:
        """启用策略

        Args:
            name: 策略名称

        Returns:
            是否成功
        """
        if name not in self.strategies:
            logger.error(f"策略不存在: {name}")
            return False

        if name not in self.active_strategies:
            self.active_strategies.append(name)
            logger.info(f"启用策略: {name}")
            return True

        return False

    def disable_strategy(self, name: str) -> bool:
        """禁用策略

        Args:
            name: 策略名称

        Returns:
            是否成功
        """
        if name in self.active_strategies:
            self.active_strategies.remove(name)
            logger.info(f"禁用策略: {name}")
            return True

        return False

    def get_strategy_performance(
        self,
        name: str
    ) -> Optional[Dict[str, Any]]:
        """获取策略性能

        Args:
            name: 策略名称

        Returns:
            性能字典
        """
        return self.strategy_performance.get(name)

    # ========== 私有方法 ==========

    async def _register_default_strategies(self) -> None:
        """注册默认策略"""
        # 注册价格趋势策略
        self.register_strategy('price_trend', {
            'type': 'price_trend',
            'enabled': True,
            'lookback_periods': [5, 10, 20],
            'threshold': 0.02,  # 2%
        })

        # 注册均值回归策略
        self.register_strategy('mean_reversion', {
            'type': 'mean_reversion',
            'enabled': True,
            'lookback_period': 20,
            'std_multiplier': 2.0,
        })

        # 注册动量策略
        self.register_strategy('momentum', {
            'type': 'momentum',
            'enabled': True,
            'lookback_period': 14,
            'threshold': 0.03,  # 3%
        })

        # 注册波动率策略
        self.register_strategy('volatility', {
            'type': 'volatility',
            'enabled': True,
            'lookback_period': 20,
            'high_vol_threshold': 0.02,  # 2%
            'low_vol_threshold': 0.005,  # 0.5%
        })

    async def _generate_strategy_signals(
        self,
        strategy_name: str,
        market_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成策略信号

        Args:
            strategy_name: 策略名称
            market_data: 市场数据

        Returns:
            信号列表
        """
        try:
            strategy = self.strategies.get(strategy_name)
            if not strategy:
                logger.error(f"策略不存在: {strategy_name}")
                return []

            strategy_type = strategy.get('type')
            symbols_data = market_data.get('symbols', {})

            signals = []

            # 为每个交易对生成信号
            for symbol, data in symbols_data.items():
                if 'price' not in data:
                    continue

                price_data = data['price']
                current_price = price_data.get('price', 0)

                if current_price <= 0:
                    continue

                # 根据策略类型生成信号
                if strategy_type == 'price_trend':
                    signal = self._generate_price_trend_signal(
                        strategy_name,
                        symbol,
                        current_price,
                        strategy
                    )
                elif strategy_type == 'mean_reversion':
                    signal = self._generate_mean_reversion_signal(
                        strategy_name,
                        symbol,
                        current_price,
                        strategy
                    )
                elif strategy_type == 'momentum':
                    signal = self._generate_momentum_signal(
                        strategy_name,
                        symbol,
                        current_price,
                        strategy
                    )
                elif strategy_type == 'volatility':
                    signal = self._generate_volatility_signal(
                        strategy_name,
                        symbol,
                        current_price,
                        strategy
                    )
                else:
                    logger.warning(f"未知策略类型: {strategy_type}")
                    continue

                if signal:
                    signal['strategy'] = strategy_name
                    signal['symbol'] = symbol
                    signal['generated_at'] = datetime.now().isoformat()
                    signals.append(signal)

            return signals

        except Exception as e:
            logger.error(f"生成策略信号失败: {e}")
            return []

    def _generate_price_trend_signal(
        self,
        strategy_name: str,
        symbol: str,
        current_price: float,
        strategy: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """生成价格趋势信号

        Args:
            strategy_name: 策略名称
            symbol: 交易对
            current_price: 当前价格
            strategy: 策略配置

        Returns:
            信号字典
        """
        try:
            # 模拟历史价格
            historical_prices = self._get_simulated_historical_prices(
                symbol,
                current_price,
                20
            )

            lookback_periods = strategy.get('lookback_periods', [5, 10, 20])
            threshold = strategy.get('threshold', 0.02)

            buy_count = 0
            sell_count = 0

            for period in lookback_periods:
                if len(historical_prices) < period:
                    continue

                recent_prices = historical_prices[-period:]
                avg_price = sum(recent_prices) / len(recent_prices)

                # 计算价格变化
                price_change = (current_price - avg_price) / avg_price

                if price_change > threshold:
                    buy_count += 1
                elif price_change < -threshold:
                    sell_count += 1

            # 确定信号
            if buy_count > sell_count:
                action = SignalAction.BUY.value
                confidence = min(1.0, buy_count / len(lookback_periods))
            elif sell_count > buy_count:
                action = SignalAction.SELL.value
                confidence = min(1.0, sell_count / len(lookback_periods))
            else:
                action = SignalAction.HOLD.value
                confidence = 0.0

            return {
                'action': action,
                'price': current_price,
                'confidence': confidence,
                'reason': f'Price trend: {buy_count} buy vs {sell_count} sell',
                'metadata': {
                    'buy_count': buy_count,
                    'sell_count': sell_count,
                    'lookback_periods': lookback_periods,
                },
            }

        except Exception as e:
            logger.error(f"生成价格趋势信号失败: {e}")
            return None

    def _generate_mean_reversion_signal(
        self,
        strategy_name: str,
        symbol: str,
        current_price: float,
        strategy: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """生成均值回归信号

        Args:
            strategy_name: 策略名称
            symbol: 交易对
            current_price: 当前价格
            strategy: 策略配置

        Returns:
            信号字典
        """
        try:
            # 模拟历史价格
            historical_prices = self._get_simulated_historical_prices(
                symbol,
                current_price,
                strategy.get('lookback_period', 20)
            )

            if len(historical_prices) < 20:
                return None

            # 计算均值和标准差
            mean_price = sum(historical_prices) / len(historical_prices)
            variance = sum((p - mean_price) ** 2 for p in historical_prices) / len(historical_prices)
            std_dev = variance ** 0.5

            std_multiplier = strategy.get('std_multiplier', 2.0)
            upper_band = mean_price + std_multiplier * std_dev
            lower_band = mean_price - std_multiplier * std_dev

            # 确定信号
            if current_price < lower_band:
                # 价格低于下轨，买入
                action = SignalAction.BUY.value
                distance = (lower_band - current_price) / current_price
                confidence = min(1.0, distance / (std_multiplier * std_dev / current_price))
            elif current_price > upper_band:
                # 价格高于上轨，卖出
                action = SignalAction.SELL.value
                distance = (current_price - upper_band) / current_price
                confidence = min(1.0, distance / (std_multiplier * std_dev / current_price))
            else:
                # 价格在区间内，持有
                action = SignalAction.HOLD.value
                confidence = 0.0

            return {
                'action': action,
                'price': current_price,
                'confidence': confidence,
                'reason': f'Mean reversion: price={current_price:.2f}, mean={mean_price:.2f}, std={std_dev:.2f}',
                'metadata': {
                    'mean': mean_price,
                    'std_dev': std_dev,
                    'upper_band': upper_band,
                    'lower_band': lower_band,
                },
            }

        except Exception as e:
            logger.error(f"生成均值回归信号失败: {e}")
            return None

    def _generate_momentum_signal(
        self,
        strategy_name: str,
        symbol: str,
        current_price: float,
        strategy: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """生成动量信号

        Args:
            strategy_name: 策略名称
            symbol: 交易对
            current_price: 当前价格
            strategy: 策略配置

        Returns:
            信号字典
        """
        try:
            # 模拟历史价格
            historical_prices = self._get_simulated_historical_prices(
                symbol,
                current_price,
                strategy.get('lookback_period', 14)
            )

            if len(historical_prices) < 14:
                return None

            # 计算动量（RSI简化版）
            gains = []
            losses = []

            for i in range(1, len(historical_prices)):
                change = historical_prices[i] - historical_prices[i - 1]
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(change))

            avg_gain = sum(gains) / len(gains) if gains else 0
            avg_loss = sum(losses) / len(losses) if losses else 0

            if avg_loss == 0:
                rsi = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))

            threshold = strategy.get('threshold', 0.03)  # 3%

            # 确定信号
            if rsi < 30:
                # 超卖，买入
                action = SignalAction.BUY.value
                confidence = (30 - rsi) / 30
            elif rsi > 70:
                # 超买，卖出
                action = SignalAction.SELL.value
                confidence = (rsi - 70) / 30
            else:
                action = SignalAction.HOLD.value
                confidence = 0.0

            return {
                'action': action,
                'price': current_price,
                'confidence': confidence,
                'reason': f'Momentum (RSI): {rsi:.2f}',
                'metadata': {
                    'rsi': rsi,
                    'avg_gain': avg_gain,
                    'avg_loss': avg_loss,
                },
            }

        except Exception as e:
            logger.error(f"生成动量信号失败: {e}")
            return None

    def _generate_volatility_signal(
        self,
        strategy_name: str,
        symbol: str,
        current_price: float,
        strategy: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """生成波动率信号

        Args:
            strategy_name: 策略名称
            symbol: 交易对
            current_price: 当前价格
            strategy: 策略配置

        Returns:
            信号字典
        """
        try:
            # 模拟历史价格
            historical_prices = self._get_simulated_historical_prices(
                symbol,
                current_price,
                strategy.get('lookback_period', 20)
            )

            if len(historical_prices) < 20:
                return None

            # 计算波动率（标准差）
            mean_price = sum(historical_prices) / len(historical_prices)
            variance = sum((p - mean_price) ** 2 for p in historical_prices) / len(historical_prices)
            volatility = variance ** 0.5
            volatility_percent = volatility / mean_price

            high_vol_threshold = strategy.get('high_vol_threshold', 0.02)
            low_vol_threshold = strategy.get('low_vol_threshold', 0.005)

            # 确定信号
            if volatility_percent < low_vol_threshold:
                # 低波动率，避免交易
                action = SignalAction.HOLD.value
                confidence = 0.0
            elif volatility_percent > high_vol_threshold:
                # 高波动率，谨慎交易
                action = SignalAction.HOLD.value
                confidence = 0.0
            else:
                # 正常波动率，使用其他策略信号
                action = SignalAction.HOLD.value
                confidence = 0.0

            return {
                'action': action,
                'price': current_price,
                'confidence': confidence,
                'reason': f'Volatility: {volatility_percent:.2%}',
                'metadata': {
                    'volatility': volatility,
                    'volatility_percent': volatility_percent,
                },
            }

        except Exception as e:
            logger.error(f"生成波动率信号失败: {e}")
            return None

    def _assess_signal_quality(self, signal: Dict[str, Any]) -> SignalQuality:
        """评估信号质量

        Args:
            signal: 信号字典

        Returns:
            信号质量
        """
        try:
            confidence = signal.get('confidence', 0)
            action = signal.get('action')

            # 检查必要字段
            required_fields = ['action', 'price', 'confidence']
            for field in required_fields:
                if field not in signal:
                    return SignalQuality.INVALID

            # 检查价格
            if signal.get('price', 0) <= 0:
                return SignalQuality.INVALID

            # 评估置信度
            if confidence >= 0.8:
                return SignalQuality.EXCELLENT
            elif confidence >= 0.6:
                return SignalQuality.GOOD
            elif confidence >= 0.4:
                return SignalQuality.FAIR
            elif confidence > 0:
                return SignalQuality.POOR
            else:
                return SignalQuality.INVALID

        except Exception as e:
            logger.error(f"评估信号质量失败: {e}")
            return SignalQuality.INVALID

    def _check_signal_consistency(self, signal: Dict[str, Any]) -> float:
        """检查信号一致性

        Args:
            signal: 信号字典

        Returns:
            一致性评分（0-1）
        """
        try:
            # 获取同一交易对最近的信号
            symbol = signal.get('symbol')
            if not symbol:
                return 1.0

            recent_signals = [
                s for s in self.signal_history[-20:]
                if s.get('symbol') == symbol
            ]

            if not recent_signals:
                return 1.0

            # 计算一致性
            same_action_count = sum(
                1 for s in recent_signals
                if s.get('action') == signal.get('action')
            )

            consistency = same_action_count / len(recent_signals)
            return consistency

        except Exception as e:
            logger.error(f"检查信号一致性失败: {e}")
            return 0.0

    def _validate_signal(self, signal: Dict[str, Any]) -> bool:
        """验证信号

        Args:
            signal: 信号字典

        Returns:
            是否有效
        """
        try:
            # 检查必要字段
            required_fields = ['action', 'price', 'confidence']
            for field in required_fields:
                if field not in signal:
                    return False

            # 检查价格
            if signal.get('price', 0) <= 0:
                return False

            # 检查置信度
            if not (0 <= signal.get('confidence', 0) <= 1):
                return False

            # 检查动作
            if signal.get('action') not in [
                SignalAction.BUY.value,
                SignalAction.SELL.value,
                SignalAction.HOLD.value,
            ]:
                return False

            return True

        except Exception as e:
            logger.error(f"验证信号失败: {e}")
            return False

    def _calculate_confidence(
        self,
        signal: Dict[str, Any],
        quality: SignalQuality
    ) -> float:
        """计算置信度

        Args:
            signal: 信号字典
            quality: 信号质量

        Returns:
            置信度（0-1）
        """
        try:
            base_confidence = signal.get('confidence', 0)
            consistency = signal.get('consistency', 1.0)

            # 根据质量调整置信度
            quality_multiplier = {
                SignalQuality.EXCELLENT: 1.2,
                SignalQuality.GOOD: 1.0,
                SignalQuality.FAIR: 0.8,
                SignalQuality.POOR: 0.5,
                SignalQuality.INVALID: 0.0,
            }

            adjusted_confidence = (
                base_confidence *
                quality_multiplier.get(quality, 0.5) *
                consistency
            )

            # 限制在0-1之间
            return max(0.0, min(1.0, adjusted_confidence))

        except Exception as e:
            logger.error(f"计算置信度失败: {e}")
            return 0.0

    def _record_signals(self, signals: List[Dict[str, Any]]) -> None:
        """记录信号

        Args:
            signals: 信号列表
        """
        for signal in signals:
            self.signal_history.append(signal)

        # 限制历史大小
        if len(self.signal_history) > self.max_signal_history:
            self.signal_history = self.signal_history[-self.max_signal_history:]

    def _update_stats(self, signals: List[Dict[str, Any]]) -> None:
        """更新统计信息

        Args:
            signals: 信号列表
        """
        self.stats['total_signals'] += len(signals)

        for signal in signals:
            action = signal.get('action')
            if action == SignalAction.BUY.value:
                self.stats['buy_signals'] += 1
            elif action == SignalAction.SELL.value:
                self.stats['sell_signals'] += 1
            elif action == SignalAction.HOLD.value:
                self.stats['hold_signals'] += 1

            confidence = signal.get('confidence', 0)
            if confidence >= 0.8:
                self.stats['high_confidence_signals'] += 1

        # 计算平均置信度
        if signals:
            avg_confidence = sum(
                s.get('confidence', 0) for s in signals
            ) / len(signals)

            total_signals = self.stats['total_signals']
            old_avg = self.stats['avg_confidence']
            self.stats['avg_confidence'] = (
                (old_avg * (total_signals - len(signals)) + avg_confidence * len(signals)) /
                total_signals
            )

    def _get_simulated_historical_prices(
        self,
        symbol: str,
        current_price: float,
        period: int
    ) -> List[float]:
        """获取模拟历史价格

        Args:
            symbol: 交易对
            current_price: 当前价格
            period: 周期

        Returns:
            历史价格列表
        """
        import random

        prices = []
        price = current_price

        for _ in range(period):
            # 添加随机波动
            change_percent = random.uniform(-0.02, 0.02)  # ±2%
            price = price * (1 + change_percent)
            prices.append(price)

        prices.reverse()  # 最新的价格在最后
        prices.append(current_price)

        return prices

    def _update_market_data_cache(self, market_data: Dict[str, Any]) -> None:
        """更新市场数据缓存

        Args:
            market_data: 市场数据字典
        """
        self.market_data_cache = {
            'data': market_data,
            'timestamp': datetime.now(),
        }

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息

        Returns:
            统计信息字典
        """
        return {
            **self.stats,
            'active_strategies': len(self.active_strategies),
            'total_strategies': len(self.strategies),
            'signal_history_size': len(self.signal_history),
        }


# ========== 全局信号生成器实例 ==========

_signal_generator_instance: Optional[SignalGenerator] = None


def get_signal_generator() -> SignalGenerator:
    """获取信号生成器单例

    Returns:
        信号生成器实例
    """
    global _signal_generator_instance
    if _signal_generator_instance is None:
        _signal_generator_instance = SignalGenerator()
    return _signal_generator_instance
