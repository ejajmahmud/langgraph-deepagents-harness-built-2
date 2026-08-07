"""TradingAgents集成包装器

将TradingAgents多智能体LLM分析框架集成到CryptoArbitrage系统。
提供统一的接口用于加密货币市场分析和信号生成。

依赖：
- TradingAgents: D:/01_COINLAB/TradingAgents
- 需要配置至少一个LLM API Key (OpenAI/Google/Anthropic/xAI/OpenRouter/Ollama)
"""

import logging
import sys
from typing import Any, Dict, List, Optional

# 添加TradingAgents到Python路径
TA_ROOT = "D:/01_COINLAB/TradingAgents"
if TA_ROOT not in sys.path:
    sys.path.insert(0, TA_ROOT)

logger = logging.getLogger(__name__)


class TradingAgentsWrapper:
    """TradingAgents集成包装器

    封装TradingAgents多智能体LLM分析框架，提供加密货币市场分析能力。
    输出五级交易决策：BUY / OVERWEIGHT / HOLD / UNDERWEIGHT / SELL
    """

    def __init__(
        self,
        provider: str = "anthropic",
        model: str = "claude-sonnet-4-6",
        language: str = "Chinese",
        enabled: bool = True,
        preset: str = "standard"
    ):
        """初始化TradingAgents包装器

        Args:
            provider: LLM提供商 (openai/google/anthropic/xai/openrouter/ollama)
            model: 模型名称
            language: 输出语言 (English/Chinese)
            enabled: 是否启用
            preset: 预设模式 (quick/standard/deep)
        """
        self.provider = provider
        self.model = model
        self.language = language
        self.enabled = enabled
        self.preset = preset

        self._graph = None
        self._api_key_available = False

        if self.enabled:
            self._initialize_trading_agents()

    def _initialize_trading_agents(self) -> None:
        """初始化TradingAgents图

        检查API Key并初始化TradingAgentsGraph
        """
        try:
            # 检查API Key
            import os
            api_keys = {
                "openai": os.environ.get("OPENAI_API_KEY"),
                "google": os.environ.get("GOOGLE_API_KEY"),
                "anthropic": os.environ.get("ANTHROPIC_API_KEY"),
                "xai": os.environ.get("XAI_API_KEY"),
                "openrouter": os.environ.get("OPENROUTER_API_KEY")
            }

            if not api_keys.get(self.provider):
                logger.warning(
                    f"TradingAgents: {self.provider.upper()} API Key not found, "
                    "LLM analysis will be disabled"
                )
                self.enabled = False
                return

            self._api_key_available = True

            # 导入TradingAgents
            from tradingagents.default_config import DEFAULT_CONFIG
            from tradingagents.graph.trading_graph import TradingAgentsGraph

            # 配置TradingAgents
            config = DEFAULT_CONFIG.copy()
            config["llm_provider"] = self.provider
            config["output_language"] = self.language

            # 根据预设调整配置
            if self.preset == "quick":
                config["max_debate_rounds"] = 0
                config["max_risk_discuss_rounds"] = 0
                config["deep_think_llm"] = self.model
                config["quick_think_llm"] = self.model
            elif self.preset == "standard":
                config["max_debate_rounds"] = 1
                config["max_risk_discuss_rounds"] = 1
                config["deep_think_llm"] = self.model
                config["quick_think_llm"] = self.model
            elif self.preset == "deep":
                config["max_debate_rounds"] = 3
                config["max_risk_discuss_rounds"] = 2
                config["deep_think_llm"] = self.model
                config["quick_think_llm"] = self.model

            # 初始化图
            self._graph = TradingAgentsGraph(
                selected_analysts=["market", "social", "news", "fundamentals"],
                debug=False,
                config=config
            )

            logger.info(
                f"TradingAgents initialized: provider={self.provider}, "
                f"model={self.model}, preset={self.preset}"
            )

        except Exception as e:
            logger.error(f"TradingAgents initialization failed: {e}")
            self.enabled = False

    def is_enabled(self) -> bool:
        """检查是否启用"""
        return self.enabled and self._api_key_available

    def analyze_crypto(
        self,
        symbol: str,
        date: str,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """分析加密货币市场

        使用TradingAgents多智能体分析指定加密货币在特定日期的市场状况。

        Args:
            symbol: 加密货币代码 (BTC, ETH, BNB等)
            date: 分析日期 (YYYY-MM-DD格式)
            timeout: 超时时间（秒）

        Returns:
            分析结果字典，包含：
            - signal: 五级交易信号 (BUY/OVERWEIGHT/HOLD/UNDERWEIGHT/SELL)
            - score: 0-100评分
            - confidence: 置信度 (0-1)
            - analyst_reports: 各分析师报告
                - market: 市场分析报告
                - sentiment: 情绪分析报告
                - news: 新闻分析报告
                - fundamentals: 基本面分析报告
            - investment_plan: 投资组合经理计划
            - trader_plan: 交易员计划
            - final_decision: 最终决策全文
            - duration_seconds: 分析耗时
            - success: 是否成功
            - error: 错误信息（如果失败）
        """
        if not self.is_enabled():
            # 返回中性结果
            return {
                "signal": "HOLD",
                "score": 50,
                "confidence": 0.0,
                "analyst_reports": {},
                "investment_plan": "",
                "trader_plan": "",
                "final_decision": "TradingAgents is disabled",
                "duration_seconds": 0,
                "success": False,
                "error": "TradingAgents is disabled or API key not available"
            }

        start_time = time.time() if 'time' in globals() else __import__('time').time()

        try:
            # 调用TradingAgents进行分析
            final_state, decision = self._graph.propagate(symbol, date)

            # 提取分析师报告
            analyst_reports = {}
            for report_type in ["market", "sentiment", "news", "fundamentals"]:
                report_key = f"{report_type}_report"
                if report_key in final_state:
                    analyst_reports[report_type] = final_state[report_key]

            # 计算评分
            score = self._signal_to_score(decision)

            duration = (__import__('time').time() - start_time) if 'time' in globals() else 0

            # 提取计划
            investment_plan = final_state.get("investment_plan", "")
            trader_plan = final_state.get("trader_plan", "")
            final_decision_text = final_state.get("final_trade_decision", "")

            return {
                "signal": decision,
                "score": score,
                "confidence": self._estimate_confidence(decision, final_state),
                "analyst_reports": analyst_reports,
                "investment_plan": investment_plan,
                "trader_plan": trader_plan,
                "final_decision": final_decision_text,
                "duration_seconds": duration,
                "success": True,
                "error": None
            }

        except Exception as e:
            logger.error(f"TradingAgents analysis failed for {symbol} on {date}: {e}")
            return {
                "signal": "HOLD",
                "score": 50,
                "confidence": 0.0,
                "analyst_reports": {},
                "investment_plan": "",
                "trader_plan": "",
                "final_decision": f"Error: {str(e)}",
                "duration_seconds": 0,
                "success": False,
                "error": str(e)
            }

    def _signal_to_score(self, signal: str) -> int:
        """将五级信号转换为0-100评分

        Args:
            signal: 交易信号 (BUY/OVERWEIGHT/HOLD/UNDERWEIGHT/SELL)

        Returns:
            0-100评分
        """
        signal_map = {
            "BUY": 100,
            "OVERWEIGHT": 75,
            "HOLD": 50,
            "UNDERWEIGHT": 25,
            "SELL": 0
        }
        return signal_map.get(signal.upper(), 50)  # 默认HOLD

    def _estimate_confidence(self, signal: str, final_state: Dict) -> float:
        """估算置信度

        基于信号强度和分析师报告一致性估算置信度。

        Args:
            signal: 交易信号
            final_state: TradingAgents最终状态

        Returns:
            置信度 (0-1)
        """
        # 基础置信度基于信号强度
        base_confidence = {
            "BUY": 0.9,
            "SELL": 0.9,
            "OVERWEIGHT": 0.7,
            "UNDERWEIGHT": 0.7,
            "HOLD": 0.5
        }.get(signal, 0.5)

        # 检查分析师报告数量
        report_count = sum(1 for key in final_state.keys() if key.endswith("_report"))
        report_bonus = min(report_count / 4 * 0.1, 0.1)  # 最多增加0.1

        return min(base_confidence + report_bonus, 1.0)

    def batch_analyze(
        self,
        symbols: List[str],
        date: str,
        max_concurrent: int = 3
    ) -> Dict[str, Dict[str, Any]]:
        """批量分析多个加密货币

        Args:
            symbols: 加密货币代码列表
            date: 分析日期
            max_concurrent: 最大并发数

        Returns:
            字典，键为symbol，值为分析结果
        """
        results = {}
        import time

        for i, symbol in enumerate(symbols):
            logger.info(f"Analyzing {symbol} ({i+1}/{len(symbols)})")
            results[symbol] = self.analyze_crypto(symbol, date)

            # 控制并发
            if (i + 1) % max_concurrent == 0:
                time.sleep(1)  # 避免API速率限制

        return results

    def reflect_and_remember(self, returns_losses: Any) -> None:
        """反思并记住交易结果

        基于收益/亏损更新多智能体的记忆。

        Args:
            returns_losses: 收益/亏损（数字或字符串）
        """
        if self._graph is not None:
            self._graph.reflect_and_remember(returns_losses)
            logger.info(f"TradingAgents reflected on: {returns_losses}")


def create_trading_agents_wrapper(
    provider: str = "anthropic",
    model: str = "claude-sonnet-4-6",
    language: str = "Chinese",
    enabled: bool = True
) -> TradingAgentsWrapper:
    """工厂函数：创建TradingAgents包装器

    Args:
        provider: LLM提供商
        model: 模型名称
        language: 输出语言
        enabled: 是否启用

    Returns:
        TradingAgentsWrapper实例
    """
    return TradingAgentsWrapper(
        provider=provider,
        model=model,
        language=language,
        enabled=enabled
    )


def get_enabled_wrapper() -> Optional[TradingAgentsWrapper]:
    """获取已启用的TradingAgents包装器

    如果API Key配置正确，返回包装器；否则返回None。

    Returns:
        TradingAgentsWrapper实例或None
    """
    wrapper = TradingAgentsWrapper()
    if wrapper.is_enabled():
        return wrapper
    return None
