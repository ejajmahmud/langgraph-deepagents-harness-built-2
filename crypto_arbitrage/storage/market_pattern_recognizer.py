"""市场模式识别器 V2.2 - 基于Memo0的市场周期学习

利用Memo0存储的历史市场数据，识别市场模式:
- 学习市场周期模式 (牛市/熊市/震荡)
- 识别异常市场状态
- 与历史模式对比
- 提供市场状态预测

V2.2 新增: 市场模式智能识别和预测
"""

import logging
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class MarketState(str):
    """市场状态枚举"""
    BULL = "bull"          # 牛市
    BEAR = "bear"          # 熊市
    SIDEWAYS = "sideways"   # 震荡
    VOLATILE = "volatile"   # 高波动
    CALM = "calm"          # 平静


class MarketPatternRecognizer:
    """市场模式识别器

    基于历史数据和Memo0知识库，识别市场模式。
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化市场模式识别器

        Args:
            config: 配置字典
        """
        self.config = config
        self.enabled = config.get('enable_pattern_recognition', True)
        self.lookback_period = config.get('pattern_lookback_days', 30)

        # 历史模式缓存
        self._historical_patterns: Dict[str, List[Dict]] = defaultdict(list)
        self._pattern_cache_ttl = 3600  # 1小时
        self._last_cache_update = 0

        # 当前状态追踪
        self._current_state = MarketState.SIDEWAYS
        self._state_duration = 0
        self._state_history: List[Tuple[MarketState, float]] = []

        logger.info("市场模式识别器初始化完成")

    async def recognize_market_state(
        self,
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """识别当前市场状态

        Args:
            market_data: 市场数据
                - price: 当前价格
                - price_change_24h: 24小时价格变化
                - volatility: 波动率
                - volume: 交易量
                - volume_change: 交易量变化

        Returns:
            市场状态识别结果:
                - state: 当前市场状态
                - confidence: 置信度
                - duration: 当前状态持续时间
                - transition_probability: 状态转换概率
                - recommendations: 交易建议
        """
        if not self.enabled:
            return self._default_state()

        try:
            # 基于技术指标识别状态
            state = self._identify_state_indicators(market_data)

            # 搜索历史相似状态
            historical_context = self._find_historical_patterns(state, market_data)

            # 计算状态持续时间
            duration = self._update_state_duration(state)

            # 预测状态转换
            transition_prob = self._predict_transition(state, duration)

            # 生成交易建议
            recommendations = self._generate_state_recommendations(state, market_data)

            # 获取状态值（处理字符串和枚举两种情况）
            state_value = state if isinstance(state, str) else state.value

            return {
                "state": state_value,
                "confidence": 0.8,
                "duration": duration,
                "transition_probability": transition_prob,
                "historical_context": historical_context,
                "recommendations": recommendations,
                "timestamp": time.time()
            }
        except Exception as e:
            logger.warning(f"市场状态识别失败: {e}")
            return self._default_state()

    async def detect_market_cycles(
        self,
        price_history: List[float],
        window_days: int = 30
    ) -> Dict[str, Any]:
        """检测市场周期

        Args:
            price_history: 价格历史数据
            window_days: 分析窗口天数

        Returns:
            周期分析结果:
                - current_cycle: 当前周期阶段
                - cycle_duration: 周期持续时间
                - cycle_strength: 周期强度
                - predicted_turning_point: 预测转折点
        """
        if not self.enabled or len(price_history) < 50:
            return {}

        try:
            # 简单的移动平均交叉分析
            short_ma = sum(price_history[-10:]) / 10
            long_ma = sum(price_history[-30:]) / 30

            # 判断趋势
            if short_ma > long_ma:
                if price_history[-1] > price_history[-5]:
                    current_phase = "bullish_acceleration"
                else:
                    current_phase = "bullish_consolidation"
            else:
                if price_history[-1] < price_history[-5]:
                    current_phase = "bearish_acceleration"
                else:
                    current_phase = "bearish_consolidation"

            # 搜索历史类似周期
            from storage.mem0_storage import search_trading_knowledge
            similar_cycles = search_trading_knowledge(
                query=f"市场周期 {current_phase} 表现 策略",
                knowledge_type="market_cycle",
                top_k=5
            )

            return {
                "current_cycle": current_phase,
                "cycle_strength": abs(short_ma - long_ma) / long_ma,
                "historical_performance": similar_cycles,
                "timestamp": time.time()
            }
        except Exception as e:
            logger.warning(f"周期检测失败: {e}")
            return {}

    async def detect_anomalies(
        self,
        current_data: Dict[str, Any],
        historical_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """检测市场异常

        Args:
            current_data: 当前市场数据
            historical_data: 历史数据

        Returns:
            异常列表
        """
        if not self.enabled or not historical_data:
            return []

        anomalies = []

        try:
            # 检查价格异常
            price = current_data.get('price', 0)
            avg_price = sum(d.get('price', 0) for d in historical_data) / len(historical_data)
            price_deviation = abs(price - avg_price) / avg_price if avg_price > 0 else 0

            if price_deviation > 0.05:  # 超过5%偏差
                anomalies.append({
                    "type": "price_anomaly",
                    "severity": "high" if price_deviation > 0.10 else "medium",
                    "description": f"价格异常: 偏离均值 {price_deviation*100:.1f}%",
                    "current_value": price,
                    "expected_value": avg_price
                })

            # 检查交易量异常
            volume = current_data.get('volume', 0)
            avg_volume = sum(d.get('volume', 0) for d in historical_data) / len(historical_data)
            volume_ratio = volume / avg_volume if avg_volume > 0 else 1

            if volume_ratio > 3.0 or volume_ratio < 0.33:
                anomalies.append({
                    "type": "volume_anomaly",
                    "severity": "high" if volume_ratio > 5.0 or volume_ratio < 0.2 else "medium",
                    "description": f"交易量异常: 是平均值的 {volume_ratio:.1f}倍",
                    "current_value": volume,
                    "expected_value": avg_volume
                })

            # 检查波动率异常
            volatility = current_data.get('volatility', 0)
            avg_volatility = sum(d.get('volatility', 0) for d in historical_data) / len(historical_data)

            if volatility > avg_volatility * 2:
                anomalies.append({
                    "type": "volatility_anomaly",
                    "severity": "high",
                    "description": f"波动率异常: {volatility:.2f}% (平均: {avg_volatility:.2f}%)",
                    "current_value": volatility,
                    "expected_value": avg_volatility
                })

            # 搜索历史类似异常
            if anomalies:
                from storage.mem0_storage import search_trading_knowledge
                for anomaly in anomalies:
                    query = f"{anomaly['type']} 后果 影响"
                    similar = search_trading_knowledge(
                        query=query,
                        knowledge_type="market_anomaly",
                        top_k=3
                    )
                    if similar:
                        anomaly["historical_impact"] = similar

            return anomalies
        except Exception as e:
            logger.warning(f"异常检测失败: {e}")
            return []

    async def get_market_sentiment(
        self,
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """获取市场情绪

        基于多个指标综合判断市场情绪。

        Args:
            market_data: 市场数据

        Returns:
            情绪分析结果:
                - sentiment: 情绪 (positive/negative/neutral)
                - confidence: 置信度
                - indicators: 各指标贡献
        """
        if not self.enabled:
            return {"sentiment": "neutral", "confidence": 0.5}

        try:
            # 基于多个指标判断
            indicators = {}

            # 价格趋势
            price_change = market_data.get('price_change_24h', 0)
            if price_change > 2:
                indicators['price_trend'] = 'positive'
            elif price_change < -2:
                indicators['price_trend'] = 'negative'
            else:
                indicators['price_trend'] = 'neutral'

            # 波动率
            volatility = market_data.get('volatility', 0)
            if volatility < 1:
                indicators['volatility'] = 'positive'  # 低波动是好事
            elif volatility > 4:
                indicators['volatility'] = 'negative'
            else:
                indicators['volatility'] = 'neutral'

            # 交易量
            volume_change = market_data.get('volume_change', 0)
            if volume_change > 0.2:
                indicators['volume'] = 'positive'
            elif volume_change < -0.2:
                indicators['volume'] = 'negative'
            else:
                indicators['volume'] = 'neutral'

            # 综合判断
            positive_count = sum(1 for v in indicators.values() if v == 'positive')
            negative_count = sum(1 for v in indicators.values() if v == 'negative')

            if positive_count > negative_count:
                sentiment = 'positive'
                confidence = 0.7
            elif negative_count > positive_count:
                sentiment = 'negative'
                confidence = 0.7
            else:
                sentiment = 'neutral'
                confidence = 0.5

            return {
                "sentiment": sentiment,
                "confidence": confidence,
                "indicators": indicators,
                "timestamp": time.time()
            }
        except Exception as e:
            logger.warning(f"情绪分析失败: {e}")
            return {"sentiment": "neutral", "confidence": 0.5}

    # -------------------- 私有方法 --------------------

    def _identify_state_indicators(self, market_data: Dict[str, Any]) -> MarketState:
        """基于指标识别市场状态"""
        price_change = market_data.get('price_change_24h', 0)
        volatility = market_data.get('volatility', 0)

        # 优先判断极端状态
        if volatility > 5.0:
            return MarketState.VOLATILE
        elif volatility < 0.5:
            return MarketState.CALM

        # 判断趋势状态
        if price_change > 3:
            return MarketState.BULL
        elif price_change < -3:
            return MarketState.BEAR
        else:
            return MarketState.SIDEWAYS

    def _update_state_duration(self, new_state: MarketState) -> float:
        """更新状态持续时间"""
        now = time.time()

        # 确保比较的是字符串值
        new_state_value = new_state if isinstance(new_state, str) else new_state.value
        current_state_value = self._current_state if isinstance(self._current_state, str) else self._current_state.value

        if new_state_value == current_state_value:
            self._state_duration = now - (self._last_state_change or now)
        else:
            # 状态改变，记录历史
            self._state_history.append((self._current_state, self._state_duration))
            self._current_state = new_state
            self._state_duration = 0
            self._last_state_change = now

        return self._state_duration

    def _find_historical_patterns(
        self,
        state: MarketState,
        market_data: Dict[str, Any]
    ) -> List[Dict]:
        """查找历史相似模式"""
        try:
            from storage.mem0_storage import search_trading_knowledge

            # 获取状态的值（处理字符串和枚举两种情况）
            state_value = state if isinstance(state, str) else state.value

            query = (
                f"市场状态 {state_value} "
                f"波动率 {market_data.get('volatility', 0)} "
                f"趋势 {market_data.get('price_change_24h', 0)} "
                f"最佳策略 表现"
            )

            patterns = search_trading_knowledge(
                query=query,
                knowledge_type="market_pattern",
                top_k=5
            )

            return patterns
        except Exception as e:
            logger.warning(f"查找历史模式失败: {e}")
            return []

    def _predict_transition(
        self,
        current_state: MarketState,
        duration: float
    ) -> Dict[str, float]:
        """预测状态转换概率"""
        # 基于历史数据计算转换概率
        # 简化实现：基于持续时间
        duration_hours = duration / 3600

        # 获取当前状态的值（处理字符串和枚举两种情况）
        current_state_value = current_state if isinstance(current_state, str) else current_state.value

        # 获取所有可能的状态值（MarketState.BULL本身就是字符串值）
        all_states = [MarketState.BULL, MarketState.BEAR, MarketState.SIDEWAYS,
                      MarketState.VOLATILE, MarketState.CALM]

        if duration_hours < 2:
            # 短时间，不太可能转换
            return {s: 0.1 for s in all_states if s != current_state_value}
        elif duration_hours < 24:
            # 中等时间，有一定转换概率
            return {s: 0.2 for s in all_states if s != current_state_value}
        else:
            # 长时间，转换概率增加
            return {s: 0.3 for s in all_states if s != current_state_value}

    def _generate_state_recommendations(
        self,
        state: MarketState,
        market_data: Dict[str, Any]
    ) -> List[str]:
        """生成状态相关的交易建议"""
        recommendations = []

        # 处理字符串和枚举两种情况
        state_value = state if isinstance(state, str) else state.value

        if state_value == MarketState.BULL:
            recommendations.extend([
                "可考虑增加仓位",
                "关注追涨策略",
                "注意市场过热信号"
            ])
        elif state_value == MarketState.BEAR:
            recommendations.extend([
                "建议减少仓位",
                "考虑避险策略",
                "等待市场企稳"
            ])
        elif state_value == MarketState.SIDEWAYS:
            recommendations.extend([
                "适合区间交易策略",
                "使用限价单",
                "避免追涨杀跌"
            ])
        elif state_value == MarketState.VOLATILE:
            recommendations.extend([
                "严格控制风险",
                "使用更小仓位",
                "设置更紧的止损"
            ])
        elif state_value == MarketState.CALM:
            recommendations.extend([
                "可适当增加仓位",
                "市场流动性较好",
                "适合套利策略"
            ])

        return recommendations

    def _default_state(self) -> Dict[str, Any]:
        """默认市场状态"""
        return {
            "state": "sideways",
            "confidence": 0.5,
            "duration": 0,
            "transition_probability": {},
            "historical_context": [],
            "recommendations": ["保持谨慎"],
            "timestamp": time.time()
        }

    # -------------------- 初始化属性 --------------------

    _last_state_change: Optional[float] = None