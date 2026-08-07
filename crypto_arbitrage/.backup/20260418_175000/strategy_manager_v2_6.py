"""StrategyManager V2.6 Mixin

基于V2.5，深度集成TradingAgents多智能体LLM分析和信号融合引擎。
新增功能：
1. TradingAgents集成 - 获取LLM市场分析信号
2. 信号融合 - 融合LLM/技术/套利/风险四种信号源
3. 智能决策增强 - 基于融合信号增强策略评分
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class StrategyManagerV26Mixin:
    """StrategyManager V2.6 Mixin

    为StrategyManager添加TradingAgents集成和信号融合能力。
    """

    def __init__(self, *args, **kwargs):
        """初始化V2.6增强"""
        super().__init__(*args, **kwargs)

        # V2.6: TradingAgents集成
        self._trading_agents = None
        self._trading_agents_enabled = kwargs.get('trading_agents_enabled', True)

        # V2.6: 信号融合引擎
        self._signal_fusion = None

        # 信号权重配置
        self._signal_weights = kwargs.get(
            'signal_weights',
            {"llm": 0.35, "technical": 0.25, "arbitrage": 0.25, "risk": 0.15}
        )

        # 是否使用动态权重
        self._use_dynamic_weights = kwargs.get('use_dynamic_weights', True)

        # LLM分析缓存（避免重复分析）
        self._llm_cache = {}
        self._cache_ttl = kwargs.get('llm_cache_ttl', 300)  # 5分钟

        if self._trading_agents_enabled:
            self._initialize_v26_components()

    def _initialize_v26_components(self) -> None:
        """初始化V2.6组件"""
        try:
            # 初始化TradingAgents
            from llm.trading_agents_wrapper import TradingAgentsWrapper
            provider = getattr(self, 'llm_provider', 'anthropic')
            model = getattr(self, 'llm_model', 'claude-sonnet-4-6')
            language = getattr(self, 'llm_language', 'Chinese')

            self._trading_agents = TradingAgentsWrapper(
                provider=provider,
                model=model,
                language=language,
                enabled=True
            )

            if self._trading_agents.is_enabled():
                logger.info("TradingAgents集成已启用 (V2.6)")
            else:
                logger.warning("TradingAgents未启用，API Key缺失或配置错误")
                self._trading_agents_enabled = False

        except Exception as e:
            logger.warning(f"TradingAgents初始化失败: {e}")
            self._trading_agents_enabled = False

        try:
            # 初始化信号融合引擎
            from llm.signal_fusion import SignalFusionEngine
            self._signal_fusion = SignalFusionEngine()
            logger.info("信号融合引擎已启用 (V2.6)")

        except Exception as e:
            logger.warning(f"信号融合引擎初始化失败: {e}")

    # ---------------------- LLM分析 ----------------------

    def get_llm_signal(
        self,
        symbol: str,
        use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """获取LLM市场分析信号

        Args:
            symbol: 交易对符号 (BTC/USDT)
            use_cache: 是否使用缓存

        Returns:
            LLM信号字典或None
        """
        if not self._trading_agents or not self._trading_agents.is_enabled():
            return None

        # 提取基础货币
        base_currency = symbol.split('/')[0]
        date = datetime.now().strftime("%Y-%m-%d")

        # 检查缓存
        if use_cache and base_currency in self._llm_cache:
            cached_time, cached_result = self._llm_cache[base_currency]
            import time
            if time.time() - cached_time < self._cache_ttl:
                return cached_result

        # 调用TradingAgents
        try:
            result = self._trading_agents.analyze_crypto(base_currency, date)

            # 缓存结果
            import time
            self._llm_cache[base_currency] = (time.time(), result)

            return result

        except Exception as e:
            logger.error(f"获取LLM信号失败 ({symbol}): {e}")
            return None

    # ---------------------- 信号融合 ----------------------

    def fuse_signals_for_opportunity(
        self,
        opportunity: Dict[str, Any],
        technical_indicators: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """为交易机会融合多种信号源

        Args:
            opportunity: 交易机会字典
            technical_indicators: 技术指标字典 (可选)

        Returns:
            融合后的信号字典
        """
        if not self._signal_fusion:
            return {
                "fused_signal": "HOLD",
                "fused_score": opportunity.get("_score", 50),
                "confidence": 0.0
            }

        # 1. 获取LLM信号
        llm_signal = self.get_llm_signal(opportunity.get("symbol", ""))
        if llm_signal:
            llm_signal = {
                "signal": llm_signal["signal"],
                "score": llm_signal["score"],
                "confidence": llm_signal["confidence"]
            }

        # 2. 获取技术指标信号
        technical_signal = None
        if technical_indicators:
            technical_signal = self._calculate_technical_signal(technical_indicators)

        # 3. 套利信号
        arbitrage_signal = {
            "signal": self._interpret_opportunity_score(opportunity.get("_score", 50)),
            "score": opportunity.get("_score", 50),
            "confidence": 0.7  # 基于机会检测的置信度
        }

        # 4. 风险信号
        risk_signal = self._calculate_risk_signal(opportunity)

        # 5. 融合信号
        fused = self._signal_fusion.fuse_signals(
            llm_signal=llm_signal,
            technical_signal=technical_signal,
            arbitrage_signal=arbitrage_signal,
            risk_signal=risk_signal,
            weights=self._signal_weights,
            use_dynamic_weights=self._use_dynamic_weights
        )

        return fused

    def _calculate_technical_signal(self, indicators: Dict) -> Dict[str, Any]:
        """计算技术指标信号

        Args:
            indicators: 技术指标字典

        Returns:
            技术信号字典
        """
        score = 50  # 中性
        confidence = 0.6

        # RSI信号
        if "rsi" in indicators:
            rsi = indicators["rsi"]
            if rsi < 30:
                score += 20  # 超卖
            elif rsi > 70:
                score -= 20  # 超买
            elif 30 <= rsi <= 70:
                score += 5  # 正常区间

        # MACD信号
        if "macd" in indicators:
            macd = indicators["macd"]
            if macd == "bullish":
                score += 15
            elif macd == "bearish":
                score -= 15

        # 布林带信号
        if "bollinger" in indicators:
            bollinger = indicators["bollinger"]
            if bollinger == "lower":
                score += 10
            elif bollinger == "upper":
                score -= 10

        # 限制评分范围
        score = max(0, min(100, score))

        signal = self._score_to_signal(score)

        return {
            "signal": signal,
            "score": score,
            "confidence": confidence
        }

    def _calculate_risk_signal(self, opportunity: Dict) -> Dict[str, Any]:
        """计算风险信号

        Args:
            opportunity: 交易机会字典

        Returns:
            风险信号字典
        """
        score = 50  # 中性
        confidence = 0.8

        # 基于机会评分调整风险信号
        opportunity_score = opportunity.get("_score", 50)

        # 高收益通常伴随高风险
        if opportunity_score > 80:
            score -= 10  # 风险较高
        elif opportunity_score < 30:
            score += 10  # 风险较低

        # 基于风险参数调整
        stop_loss = opportunity.get("_stop_loss")
        if stop_loss and stop_loss > 3.0:
            score -= 5  # 大止损，风险较高

        # 基于波动率调整
        volatility = opportunity.get("volatility", 0)
        if volatility > 0.05:  # 5%以上波动率
            score -= 10  # 高波动风险

        # 限制评分范围
        score = max(0, min(100, score))

        signal = self._score_to_signal(score)

        return {
            "signal": signal,
            "score": score,
            "confidence": confidence
        }

    def _interpret_opportunity_score(self, score: float) -> str:
        """解释机会评分

        Args:
            score: 机会评分

        Returns:
            交易信号
        """
        return self._score_to_signal(score)

    def _score_to_signal(self, score: float) -> str:
        """将评分转换为信号

        Args:
            score: 评分 (0-100)

        Returns:
            交易信号 (BUY/OVERWEIGHT/HOLD/UNDERWEIGHT/SELL)
        """
        if score >= 85:
            return "BUY"
        elif score >= 65:
            return "OVERWEIGHT"
        elif score >= 35:
            return "HOLD"
        elif score >= 15:
            return "UNDERWEIGHT"
        else:
            return "SELL"

    # ---------------------- 增强决策 ----------------------

    def _enhance_with_trading_agents(self, opportunity: Dict) -> float:
        """使用TradingAgents增强策略评分（V2.6新增）

        Args:
            opportunity: 交易机会字典

        Returns:
            增强后的评分
        """
        if not self._trading_agents_enabled:
            return opportunity.get("_score", 50)

        # 获取LLM信号
        llm_result = self.get_llm_signal(opportunity.get("symbol", ""))
        if not llm_result:
            return opportunity.get("_score", 50)

        # LLM信号权重
        llm_weight = 0.3
        llm_score = llm_result["score"]

        # 原始评分权重
        original_score = opportunity.get("_score", 50)
        original_weight = 0.7

        # 加权融合
        enhanced_score = (original_score * original_weight + llm_score * llm_weight)

        logger.info(
            f"Strategy评分增强: {original_score:.1f} → {enhanced_score:.1f} "
            f"(LLM: {llm_score:.1f}, Weight: {llm_weight:.0%})"
        )

        return enhanced_score

    def _enhance_with_signal_fusion(self, opportunity: Dict) -> float:
        """使用信号融合引擎增强策略评分（V2.6新增）

        Args:
            opportunity: 交易机会字典

        Returns:
            增强后的评分
        """
        if not self._signal_fusion:
            return opportunity.get("_score", 50)

        # 融合信号
        fused = self.fuse_signals_for_opportunity(opportunity)

        # 使用融合评分作为新评分
        fused_score = fused["fused_score"]

        logger.info(
            f"信号融合: {opportunity.get('_score', 50):.1f} → {fused_score:.1f} "
            f"(Signal: {fused['fused_signal']}, "
            f"Confidence: {fused['confidence']:.0%})"
        )

        return fused_score

    # ---------------------- 性能追踪 ----------------------

    def update_signal_performance(
        self,
        source: str,
        actual_profit: float,
        expected_profit: Optional[float] = None
    ) -> None:
        """更新信号源表现（V2.6新增）

        Args:
            source: 信号源名称 (llm/technical/arbitrage/risk)
            actual_profit: 实际收益
            expected_profit: 预期收益
        """
        if not self._signal_fusion:
            return

        # 判断是否正确（简单判断：盈利为正确）
        is_correct = actual_profit > 0

        self._signal_fusion.update_performance(source, is_correct)

        logger.info(
            f"信号源表现更新: {source}, "
            f"实际收益: {actual_profit:.2f}, "
            f"预测正确: {is_correct}"
        )

    def get_signal_performance_report(self) -> Optional[Dict[str, Any]]:
        """获取信号源表现报告（V2.6新增）

        Returns:
            表现报告字典或None
        """
        if not self._signal_fusion:
            return None

        return self._signal_fusion.get_performance_report()
