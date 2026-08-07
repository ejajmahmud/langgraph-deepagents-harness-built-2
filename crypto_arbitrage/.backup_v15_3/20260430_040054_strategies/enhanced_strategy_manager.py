"""增强策略管理器 V2.9 - TradingAgents深度集成

在V2.8基础上，深度集成TradingAgents多智能体LLM分析系统：
1. LLM信号与传统策略评分融合
2. TradingAgents五级交易信号（BUY/OVERWEIGHT/HOLD/UNDERWEIGHT/SELL）
3. 动态权重调整和信心度评估
4. 多智能体分析报告存储到Memo0
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class EnhancedStrategyManager:
    """增强策略管理器 V2.9

    集成TradingAgents多智能体分析，实现LLM驱动策略优化。
    """

    def __init__(self, base_manager, trading_agents_config: Dict[str, Any]):
        """初始化增强策略管理器

        Args:
            base_manager: 基础StrategyManager实例
            trading_agents_config: TradingAgents配置
                - enabled: 是否启用
                - provider: LLM提供商
                - model: 模型名称
                - language: 语言
                - preset: 预设模式
                - signal_weight: LLM信号权重 (0-1)
        """
        self.base_manager = base_manager
        self.config = trading_agents_config

        # TradingAgents配置
        self.enabled = self.config.get('enabled', True)
        self.signal_weight = self.config.get('signal_weight', 0.35)  # 默认35%
        self.cache_ttl = self.config.get('cache_ttl', 300)  # 缓存5分钟

        # TradingAgents包装器
        self._trading_agents = None
        self._signal_cache: Dict[str, Any] = {}  # 信号缓存
        self._cache_timestamps: Dict[str, float] = {}  # 缓存时间戳

        if self.enabled:
            self._initialize_trading_agents()

    def _initialize_trading_agents(self) -> None:
        """初始化TradingAgents包装器"""
        try:
            from llm.trading_agents_wrapper import create_trading_agents_wrapper

            self._trading_agents = create_trading_agents_wrapper(
                provider=self.config.get('provider', 'anthropic'),
                model=self.config.get('model', 'claude-sonnet-4-6'),
                language=self.config.get('language', 'Chinese'),
                enabled=True
            )

            if self._trading_agents and self._trading_agents.is_enabled():
                logger.info("✅ TradingAgents多智能体分析已启用 (V2.9)")
            else:
                logger.warning("⚠️  TradingAgents未正确初始化，将使用降级模式")
                self.enabled = False

        except Exception as e:
            logger.warning(f"⚠️  TradingAgents初始化失败: {e}")
            self.enabled = False

    async def scan_with_llm_enhancement(
        self,
        price_data: Optional[List[float]] = None
    ) -> List[Dict[str, Any]]:
        """使用LLM增强扫描所有策略

        Args:
            price_data: 价格数据

        Returns:
            增强后的交易机会列表
        """
        # 1. 基础扫描
        opportunities = await self.base_manager.scan_all_strategies(price_data)

        if not opportunities or not self.enabled:
            return opportunities

        # 2. 对每个机会获取LLM分析
        enhanced_opportunities = []
        current_time = time.time()

        for opp in opportunities:
            symbol = opp.get('symbol', opp.get('pair', ''))
            strategy_name = opp.get('_strategy_name', 'unknown')

            # 获取或计算LLM信号
            llm_signal = await self._get_llm_signal(symbol, current_time)

            if llm_signal:
                # 融合LLM信号
                opp = self._fuse_signals(opp, llm_signal, strategy_name)
                enhanced_opportunities.append(opp)
            else:
                # LLM分析失败，保留原始机会
                enhanced_opportunities.append(opp)

        # 3. 重新排序（LLM增强后）
        enhanced_opportunities.sort(key=lambda x: x.get('_score', 0), reverse=True)

        logger.info(
            f"LLM增强扫描完成: {len(enhanced_opportunities)} 个机会, "
            f"LLM信号权重 {self.signal_weight:.0%}"
        )

        return enhanced_opportunities

    async def _get_llm_signal(
        self,
        symbol: str,
        current_time: float
    ) -> Optional[Dict[str, Any]]:
        """获取LLM信号（带缓存）

        Args:
            symbol: 交易对符号
            current_time: 当前时间戳

        Returns:
            LLM分析结果
        """
        if not self._trading_agents:
            return None

        # 检查缓存
        if symbol in self._signal_cache:
            cache_time = self._cache_timestamps.get(symbol, 0)
            if current_time - cache_time < self.cache_ttl:
                logger.debug(f"使用缓存的LLM信号: {symbol}")
                return self._signal_cache[symbol]

        # 获取最新LLM分析
        try:
            from datetime import datetime
            today = datetime.now().strftime('%Y-%m-%d')

            logger.info(f"🤖 TradingAgents分析中: {symbol}")

            # 调用TradingAgents分析
            result = self._trading_agents.analyze_crypto(
                symbol=symbol,
                date=today,
                timeout=120
            )

            if result.get('success'):
                # 缓存结果
                self._signal_cache[symbol] = result
                self._cache_timestamps[symbol] = current_time

                # 记录到Memo0
                self._record_llm_analysis(symbol, result)

                logger.info(
                    f"✅ {symbol} LLM分析完成: "
                    f"信号={result['signal']}, "
                    f"评分={result['score']}, "
                    f"置信度={result['confidence']:.1%}"
                )

                return result
            else:
                logger.warning(f"⚠️  {symbol} LLM分析失败: {result.get('error')}")
                return None

        except Exception as e:
            logger.error(f"❌ {symbol} LLM分析异常: {e}")
            return None

    def _fuse_signals(
        self,
        opportunity: Dict[str, Any],
        llm_signal: Dict[str, Any],
        strategy_name: str
    ) -> Dict[str, Any]:
        """融合传统策略信号和LLM信号

        Args:
            opportunity: 交易机会
            llm_signal: LLM分析结果
            strategy_name: 策略名称

        Returns:
            融合后的机会
        """
        # 提取信号
        traditional_score = opportunity.get('_score', 50.0)
        llm_score = llm_signal.get('score', 50.0)
        llm_confidence = llm_signal.get('confidence', 0.5)
        llm_signal_name = llm_signal.get('signal', 'HOLD')

        # 动态权重调整（基于LLM置信度）
        dynamic_weight = self.signal_weight * llm_confidence
        traditional_weight = 1.0 - dynamic_weight

        # 融合评分
        fused_score = (
            traditional_score * traditional_weight +
            llm_score * dynamic_weight
        )

        # 应用LLM信号调整
        signal_adjustment = self._get_signal_adjustment(llm_signal_name)
        fused_score = fused_score * (1.0 + signal_adjustment)

        # 更新机会
        opportunity['_score'] = max(0, min(100, fused_score))
        opportunity['_llm_enhanced'] = True
        opportunity['_llm_signal'] = llm_signal_name
        opportunity['_llm_score'] = llm_score
        opportunity['_llm_confidence'] = llm_confidence
        opportunity['_fused_score'] = fused_score

        # 记录融合信息
        fusion_info = {
            "strategy": strategy_name,
            "traditional_score": traditional_score,
            "llm_score": llm_score,
            "llm_signal": llm_signal_name,
            "llm_confidence": llm_confidence,
            "signal_weight": dynamic_weight,
            "traditional_weight": traditional_weight,
            "final_score": fused_score
        }

        if '_fusion_details' not in opportunity:
            opportunity['_fusion_details'] = []

        opportunity['_fusion_details'].append(fusion_info)

        return opportunity

    def _get_signal_adjustment(self, signal: str) -> float:
        """获取信号调整系数

        Args:
            signal: LLM信号

        Returns:
            调整系数 (-0.3 到 +0.3)
        """
        adjustments = {
            "BUY": 0.3,           # 强烈建议买入，评分提升30%
            "OVERWEIGHT": 0.15,   # 建议超配，评分提升15%
            "HOLD": 0.0,          # 持有，不调整
            "UNDERWEIGHT": -0.15, # 建议低配，评分降低15%
            "SELL": -0.3          # 强烈建议卖出，评分降低30%
        }

        return adjustments.get(signal.upper(), 0.0)

    def _record_llm_analysis(self, symbol: str, result: Dict[str, Any]) -> None:
        """记录LLM分析结果到Memo0

        Args:
            symbol: 交易对
            result: LLM分析结果
        """
        try:
            # 通过AutoKnowledgeAccumulator记录
            if self.base_manager._knowledge_accumulator:
                self.base_manager._knowledge_accumulator.record_pattern(
                    pattern_type="llm_signal",
                    pattern_name=f"{symbol}_LLM_{result['signal']}",
                    description=f"TradingAgents分析: {result['signal']}",
                    indicators={
                        "symbol": symbol,
                        "signal": result['signal'],
                        "score": result['score'],
                        "confidence": result['confidence'],
                        "analyst_reports": result.get('analyst_reports', {})
                    },
                    success_rate=result['confidence'],
                    notes=result.get('final_decision', '')
                )

        except Exception as e:
            logger.debug(f"LLM分析记录失败: {e}")

    async def execute_with_llm_validation(
        self,
        opportunities: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """使用LLM验证并执行最佳机会

        Args:
            opportunities: 交易机会列表

        Returns:
            执行结果
        """
        if not opportunities:
            return None

        best = opportunities[0]

        # LLM验证（如果启用）
        if self.enabled and best.get('_llm_enhanced'):
            llm_signal = best.get('_llm_signal', 'HOLD')

            # 如果LLM信号是SELL或UNDERWEIGHT，跳过执行
            if llm_signal in ['SELL', 'UNDERWEIGHT']:
                logger.warning(
                    f"⚠️  LLM信号 {llm_signal}，跳过执行: "
                    f"{best.get('symbol', best.get('pair', ''))}"
                )
                return {
                    'status': 'skipped',
                    'reason': f'LLM信号 {llm_signal}',
                    'opportunity': best
                }

        # 执行交易
        logger.info(
            f"执行LLM验证通过的机会: "
            f"评分={best.get('_score', 0):.0f}, "
            f"LLM信号={best.get('_llm_signal', 'N/A')}"
        )

        result = await self.base_manager.execute_best_opportunity([best])

        return result

    def get_llm_analyst_reports(self, symbol: str) -> Dict[str, Any]:
        """获取LLM分析师报告

        Args:
            symbol: 交易对

        Returns:
            分析师报告字典
        """
        if not self._trading_agents or not self.enabled:
            return {}

        # 从缓存获取
        cached = self._signal_cache.get(symbol)
        if cached:
            return cached.get('analyst_reports', {})

        return {}

    def get_signal_fusion_stats(self) -> Dict[str, Any]:
        """获取信号融合统计

        Returns:
            统计信息
        """
        return {
            "enabled": self.enabled,
            "signal_weight": self.signal_weight,
            "cached_signals": len(self._signal_cache),
            "cache_ttl": self.cache_ttl,
            "llm_provider": self.config.get('provider', 'anthropic'),
            "llm_model": self.config.get('model', 'claude-sonnet-4-6')
        }

    def clear_cache(self) -> None:
        """清除信号缓存"""
        self._signal_cache.clear()
        self._cache_timestamps.clear()
        logger.info("LLM信号缓存已清除")


def create_enhanced_strategy_manager(
    base_manager,
    trading_agents_config: Dict[str, Any]
) -> EnhancedStrategyManager:
    """工厂函数：创建增强策略管理器

    Args:
        base_manager: 基础StrategyManager实例
        trading_agents_config: TradingAgents配置

    Returns:
        EnhancedStrategyManager实例
    """
    return EnhancedStrategyManager(base_manager, trading_agents_config)
