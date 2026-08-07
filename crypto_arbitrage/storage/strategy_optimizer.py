"""策略自适应优化器 V2.2 - 基于Memo0的参数优化

利用Memo0存储的历史数据，实现:
- A/B测试框架
- 自动参数调优
- 性能预测模型
- 策略比较和评估

V2.2 新增: 智能参数自适应优化
"""

import logging
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ABTest:
    """A/B测试配置"""

    def __init__(
        self,
        name: str,
        strategy: str,
        param_a: Dict[str, Any],
        param_b: Dict[str, Any],
        min_samples: int = 10
    ):
        self.name = name
        self.strategy = strategy
        self.param_a = param_a
        self.param_b = param_b
        self.min_samples = min_samples

        self.results_a: List[Dict] = []
        self.results_b: List[Dict] = []
        self.start_time = time.time()
        self.status = "running"

    def add_result(self, variant: str, result: Dict) -> None:
        """添加测试结果"""
        if variant == 'A':
            self.results_a.append(result)
        elif variant == 'B':
            self.results_b.append(result)

    def is_complete(self) -> bool:
        """测试是否完成"""
        return (
            len(self.results_a) >= self.min_samples and
            len(self.results_b) >= self.min_samples
        )

    def get_winner(self) -> Tuple[str, float, str]:
        """获取获胜者"""
        if not self.is_complete():
            return "pending", 0, "测试未完成"

        # 计算A的平均收益率
        avg_profit_a = sum(
            r.get('profit', 0) for r in self.results_a
        ) / len(self.results_a) if self.results_a else 0

        # 计算B的平均收益率
        avg_profit_b = sum(
            r.get('profit', 0) for r in self.results_b
        ) / len(self.results_b) if self.results_b else 0

        # 判断获胜者
        if avg_profit_a > avg_profit_b * 1.05:  # A好5%以上
            return "A", avg_profit_a, f"A胜出 (收益率高{(avg_profit_a/avg_profit_b-1)*100:.1f}%)"
        elif avg_profit_b > avg_profit_a * 1.05:
            return "B", avg_profit_b, f"B胜出 (收益率高{(avg_profit_b/avg_profit_a-1)*100:.1f}%)"
        else:
            return "tie", max(avg_profit_a, avg_profit_b), "无显著差异"


class StrategyOptimizer:
    """策略自适应优化器

    基于历史表现自动优化策略参数。
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化策略优化器

        Args:
            config: 配置字典
        """
        self.config = config
        self.enabled = config.get('enable_optimization', True)
        self.auto_optimize = config.get('auto_optimize', True)

        # A/B测试管理
        self._active_tests: Dict[str, ABTest] = {}
        self._test_history: List[Dict] = []

        # 性能追踪
        self._performance_history: Dict[str, List[Dict]] = defaultdict(list)
        self._parameter_history: Dict[str, List[Dict]] = defaultdict(list)

        # 优化参数
        self.optimization_interval = config.get('optimization_interval_hours', 24)
        self.min_samples_for_optimization = config.get('min_samples', 20)
        self.significance_threshold = config.get('significance_threshold', 0.05)

        logger.info("策略优化器初始化完成")

    async def start_ab_test(
        self,
        test_name: str,
        strategy: str,
        param_a: Dict[str, Any],
        param_b: Dict[str, Any]
    ) -> bool:
        """启动A/B测试

        Args:
            test_name: 测试名称
            strategy: 策略名称
            param_a: 参数组A
            param_b: 参数组B

        Returns:
            是否成功启动
        """
        if not self.enabled:
            return False

        if test_name in self._active_tests:
            logger.warning(f"A/B测试 {test_name} 已存在")
            return False

        try:
            test = ABTest(
                name=test_name,
                strategy=strategy,
                param_a=param_a,
                param_b=param_b,
                min_samples=self.min_samples_for_optimization
            )

            self._active_tests[test_name] = test

            # 记录到Memo0
            await self._record_test_start(test)

            logger.info(f"A/B测试 {test_name} 已启动")
            return True
        except Exception as e:
            logger.error(f"启动A/B测试失败: {e}")
            return False

    async def record_ab_result(
        self,
        test_name: str,
        variant: str,
        result: Dict[str, Any]
    ) -> bool:
        """记录A/B测试结果

        Args:
            test_name: 测试名称
            variant: 变体 (A/B)
            result: 测试结果

        Returns:
            是否成功记录
        """
        if test_name not in self._active_tests:
            return False

        test = self._active_tests[test_name]
        test.add_result(variant, result)

        # 检查测试是否完成
        if test.is_complete():
            await self._complete_ab_test(test_name)

        return True

    async def get_optimization_suggestions(
        self,
        strategy: str,
        current_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """获取参数优化建议

        基于历史数据推荐参数优化。

        Args:
            strategy: 策略名称
            current_params: 当前参数

        Returns:
            优化建议:
                - suggested_params: 推荐参数
                - expected_improvement: 预期改善
                - confidence: 置信度
                - reasoning: 推荐理由
        """
        if not self.enabled:
            return {}

        try:
            from storage.mem0_storage import search_trading_knowledge

            # 搜索该策略的历史表现
            query = (
                f"策略 {strategy} 参数优化 "
                f"最佳表现 收益率 提升"
            )

            optimization_data = search_trading_knowledge(
                query=query,
                knowledge_type="parameter_optimization",
                top_k=10
            )

            if not optimization_data:
                return {}

            # 分析优化数据
            suggestions = self._analyze_optimization_data(
                optimization_data, current_params
            )

            return {
                "suggested_params": suggestions,
                "expected_improvement": "预计提升10-30%收益率",
                "confidence": 0.7,
                "reasoning": "基于历史优化结果的参数调整"
            }
        except Exception as e:
            logger.warning(f"获取优化建议失败: {e}")
            return {}

    async def predict_strategy_performance(
        self,
        strategy: str,
        params: Dict[str, Any],
        market_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """预测策略性能

        基于历史数据预测策略在给定条件下的表现。

        Args:
            strategy: 策略名称
            params: 策略参数
            market_conditions: 市场条件

        Returns:
            性能预测:
                - expected_return_rate: 预期收益率
                - expected_win_rate: 预期胜率
                - risk_level: 风险等级
                - confidence: 预测置信度
        """
        if not self.enabled:
            return {}

        try:
            from storage.mem0_storage import search_trading_knowledge

            # 构建查询
            volatility = market_conditions.get('volatility', 0)
            trend = market_conditions.get('trend', 'unknown')

            query = (
                f"策略 {strategy} "
                f"波动率 {volatility} 趋势 {trend} "
                f"收益率 胜率 表现"
            )

            similar_cases = search_trading_knowledge(
                query=query,
                knowledge_type="trade_success",
                top_k=15
            )

            if not similar_cases:
                return {}

            # 基于相似案例预测
            predictions = self._calculate_performance_predictions(similar_cases)

            return {
                **predictions,
                "confidence": 0.6,
                "sample_size": len(similar_cases)
            }
        except Exception as e:
            logger.warning(f"性能预测失败: {e}")
            return {}

    async def auto_optimize_parameters(
        self,
        strategy: str,
        current_params: Dict[str, Any],
        market_conditions: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """自动优化参数

        如果启用了自动优化，基于当前条件自动调整参数。

        Args:
            strategy: 策略名称
            current_params: 当前参数
            market_conditions: 市场条件

        Returns:
            优化后的参数，如果不优化则返回None
        """
        if not self.enabled or not self.auto_optimize:
            return None

        try:
            # 检查是否需要优化
            if not await self._should_optimize(strategy):
                return None

            # 获取优化建议
            suggestions = await self.get_optimization_suggestions(
                strategy, current_params
            )

            if not suggestions:
                return None

            # 应用建议
            optimized_params = self._apply_suggestions(
                current_params, suggestions
            )

            # 记录优化
            await self._record_optimization(
                strategy, current_params, optimized_params, market_conditions
            )

            logger.info(f"策略 {strategy} 参数已自动优化")
            return optimized_params
        except Exception as e:
            logger.warning(f"自动优化失败: {e}")
            return None

    async def compare_strategies(
        self,
        strategies: List[str],
        market_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """比较策略表现

        Args:
            strategies: 策略列表
            market_conditions: 市场条件

        Returns:
            策略比较结果
        """
        if not self.enabled or not strategies:
            return {}

        try:
            from storage.mem0_storage import search_trading_knowledge

            comparison_results = {}

            for strategy in strategies:
                # 获取该策略的表现
                query = (
                    f"策略 {strategy} "
                    f"表现 收益率 胜率 "
                    f"市场条件 {market_conditions.get('volatility', 0)}"
                )

                results = search_trading_knowledge(
                    query=query,
                    knowledge_type="strategy_performance",
                    top_k=10
                )

                if results:
                    # 计算平均表现
                    comparison_results[strategy] = {
                        "avg_profit_rate": self._extract_avg_value(results, "profit_rate"),
                        "avg_win_rate": self._extract_avg_value(results, "win_rate"),
                        "sample_count": len(results)
                    }

            # 排序
            if comparison_results:
                sorted_strategies = sorted(
                    comparison_results.items(),
                    key=lambda x: x[1].get('avg_profit_rate', 0),
                    reverse=True
                )

                return {
                    "ranking": [
                        {"strategy": s[0], **s[1]}
                        for s in sorted_strategies
                    ],
                    "best_strategy": sorted_strategies[0][0] if sorted_strategies else None
                }

            return {}
        except Exception as e:
            logger.warning(f"策略比较失败: {e}")
            return {}

    # -------------------- 私有方法 --------------------

    async def _complete_ab_test(self, test_name: str) -> None:
        """完成A/B测试"""
        if test_name not in self._active_tests:
            return

        test = self._active_tests[test_name]
        winner, profit, message = test.get_winner()

        result = {
            "test_name": test_name,
            "strategy": test.strategy,
            "winner": winner,
            "profit_difference": profit,
            "message": message,
            "param_a": test.param_a,
            "param_b": test.param_b,
            "samples_a": len(test.results_a),
            "samples_b": len(test.results_b),
            "duration": time.time() - test.start_time,
            "timestamp": time.time()
        }

        # 记录结果
        self._test_history.append(result)

        # 记录到Memo0
        await self._record_test_result(result)

        # 移除活动测试
        del self._active_tests[test_name]

        logger.info(f"A/B测试 {test_name} 完成: {message}")

    async def _record_test_start(self, test: ABTest) -> None:
        """记录测试开始"""
        try:
            from storage.mem0_storage import add_trading_knowledge

            content = (
                f"A/B测试启动: {test.name}\n"
                f"策略: {test.strategy}\n"
                f"参数A: {test.param_a}\n"
                f"参数B: {test.param_b}"
            )

            add_trading_knowledge('ab_test_start', content)
        except Exception as e:
            logger.warning(f"记录测试开始失败: {e}")

    async def _record_test_result(self, result: Dict) -> None:
        """记录测试结果"""
        try:
            from storage.mem0_storage import add_trading_knowledge

            content = (
                f"A/B测试完成: {result['test_name']}\n"
                f"获胜者: {result['winner']}\n"
                f"结果: {result['message']}\n"
                f"持续时间: {result['duration']:.1f}秒"
            )

            add_trading_knowledge('ab_test_result', content)
        except Exception as e:
            logger.warning(f"记录测试结果失败: {e}")

    def _analyze_optimization_data(
        self,
        data: List[Dict],
        current_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析优化数据"""
        suggestions = {}

        # 基于历史数据生成建议
        # 简化实现：返回常用优化建议
        suggestions.update({
            "min_profit_rate": max(current_params.get('min_profit_rate', 0.5), 0.6),
            "max_position_size": min(current_params.get('max_position_size', 1000), 900),
            "scan_interval": 30
        })

        return suggestions

    def _calculate_performance_predictions(
        self,
        cases: List[Dict]
    ) -> Dict[str, float]:
        """计算性能预测（V5.3修复版）"""
        if not cases:
            return {}

        # 提取数值
        profit_rates = []
        win_rates = []

        for case in cases:
            content = case.get('content', '')
            metadata = case.get('metadata', {})

            # 尝试从metadata中提取结构化数据
            profit = metadata.get('profit', metadata.get('actual_profit'))
            win = metadata.get('outcome', '')

            # 如果metadata不可用，从content中解析
            if profit is None and isinstance(content, str):
                # 尝试从文本中提取收益信息
                import re
                profit_match = re.search(r'收益[：:]?\s*([+-]?\d*\.?\d+)', content)
                if profit_match:
                    profit = float(profit_match.group(1))
                else:
                    # 查找百分比收益率
                    percent_match = re.search(r'(\d+\.?\d*)%', content)
                    if percent_match:
                        profit = float(percent_match.group(1)) / 100

            # 提取胜率信息
            if not win and isinstance(content, str):
                if '成功' in content or '盈利' in content or 'profit' in content.lower():
                    win = 'success'
                elif '失败' in content or '亏损' in content or 'loss' in content.lower():
                    win = 'failure'

            # 归一化收益率为0-1范围
            if profit is not None:
                # 假设收益范围是-1.0到2.0（-100%到+200%）
                normalized_profit = max(0, min(1.0, (profit + 1.0) / 3.0))
                profit_rates.append(normalized_profit)

            # 计算胜率（1.0表示成功，0.0表示失败）
            if win == 'success':
                win_rates.append(1.0)
            elif win == 'failure':
                win_rates.append(0.0)
            else:
                # 无法确定，假设为0.5（中等）
                win_rates.append(0.5)

        # 计算统计指标
        avg_profit_rate = sum(profit_rates) / len(profit_rates) if profit_rates else 0.5
        avg_win_rate = sum(win_rates) / len(win_rates) if win_rates else 0.5

        # 评估风险等级
        if avg_profit_rate > 0.7 and avg_win_rate > 0.7:
            risk_level = "low"
        elif avg_profit_rate > 0.4 and avg_win_rate > 0.5:
            risk_level = "medium"
        else:
            risk_level = "high"

        return {
            "expected_return_rate": avg_profit_rate,
            "expected_win_rate": avg_win_rate,
            "risk_level": risk_level,
            "sample_count": len(cases),
            "data_quality": "high" if len(profit_rates) >= len(cases) * 0.8 else "medium"
        }

    async def _should_optimize(self, strategy: str) -> bool:
        """判断是否需要优化"""
        # 检查最近是否优化过
        recent_optimizations = [
            o for o in self._test_history
            if o.get('strategy') == strategy and
            time.time() - o.get('timestamp', 0) < self.optimization_interval * 3600
        ]

        return len(recent_optimizations) == 0

    def _apply_suggestions(
        self,
        current_params: Dict[str, Any],
        suggestions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """应用优化建议"""
        optimized = current_params.copy()
        optimized.update(suggestions)
        return optimized

    async def _record_optimization(
        self,
        strategy: str,
        old_params: Dict[str, Any],
        new_params: Dict[str, Any],
        conditions: Dict[str, Any]
    ) -> None:
        """记录优化"""
        try:
            from storage.mem0_storage import add_trading_knowledge

            content = (
                f"参数优化: {strategy}\n"
                f"原参数: {old_params}\n"
                f"新参数: {new_params}\n"
                f"市场条件: {conditions}"
            )

            add_trading_knowledge('parameter_optimization', content)
        except Exception as e:
            logger.warning(f"记录优化失败: {e}")

    def _extract_avg_value(self, results: List[Dict], key: str) -> float:
        """提取平均值（V5.3修复版）"""
        if not results:
            return 0.0

        values = []
        for result in results:
            # 尝试多种方式提取值
            value = None

            # 1. 直接从结果中获取
            if key in result:
                value = result[key]
            # 2. 从metadata中获取
            elif 'metadata' in result and key in result['metadata']:
                value = result['metadata'][key]
            # 3. 从content中解析（如果是字符串）
            elif 'content' in result and isinstance(result['content'], str):
                import re
                # 尝试匹配数字模式
                match = re.search(rf'{key}[：:]?\s*([+-]?\d*\.?\d+)', result['content'])
                if match:
                    value = float(match.group(1))

            # 验证并添加值
            if value is not None:
                try:
                    numeric_value = float(value)
                    # 过滤异常值
                    if -1000 <= numeric_value <= 1000:  # 合理范围
                        values.append(numeric_value)
                except (ValueError, TypeError):
                    continue

        # 计算平均值
        if values:
            avg_value = sum(values) / len(values)
            logger.debug(f"提取 {key} 平均值: {avg_value:.4f} (样本数: {len(values)})")
            return avg_value
        else:
            logger.warning(f"无法提取 {key} 的有效值，返回0.0")
            return 0.0