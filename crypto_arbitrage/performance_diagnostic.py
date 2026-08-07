"""性能诊断工具 V5.0

分析系统初始化和运行时的性能瓶颈
"""

import asyncio
import time
import logging
from typing import Dict, List, Tuple
from functools import wraps

logger = logging.getLogger(__name__)


class PerformanceProfiler:
    """性能分析器"""

    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}
        self.call_stack: List[str] = []

    def profile(self, name: str):
        """装饰器：分析函数执行时间

        Args:
            name: 性能指标名称
        """
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start = time.perf_counter()
                self.call_stack.append(name)
                try:
                    result = await func(*args, **kwargs)
                    elapsed = time.perf_counter() - start
                    self._record_metric(name, elapsed)
                    return result
                finally:
                    self.call_stack.pop()

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start = time.perf_counter()
                self.call_stack.append(name)
                try:
                    result = func(*args, **kwargs)
                    elapsed = time.perf_counter() - start
                    self._record_metric(name, elapsed)
                    return result
                finally:
                    self.call_stack.pop()

            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator

    def _record_metric(self, name: str, elapsed: float):
        """记录性能指标"""
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(elapsed)

        # 记录详细日志
        indent = "  " * len(self.call_stack)
        logger.info(f"{indent}[TIME] {name}: {elapsed*1000:.2f}ms")

    def get_report(self) -> str:
        """生成性能报告

        Returns:
            性能报告文本
        """
        lines = ["\n" + "="*60]
        lines.append("[PERFORMANCE] Performance Diagnostic Report")
        lines.append("="*60)

        # 总体统计
        total_time = sum(sum(times) for times in self.metrics.values())
        total_calls = sum(len(times) for times in self.metrics.values())

        lines.append(f"\n[STATS] Overall Statistics:")
        lines.append(f"  Total Time: {total_time:.3f}s ({total_time*1000:.2f}ms)")
        lines.append(f"  Total Calls: {total_calls}")

        # 详细指标
        lines.append(f"\n[DETAILS] Detailed Metrics (sorted by time):")
        sorted_metrics = sorted(
            self.metrics.items(),
            key=lambda x: sum(x[1]),
            reverse=True
        )

        for name, times in sorted_metrics:
            total = sum(times)
            avg = total / len(times)
            max_time = max(times)
            min_time = min(times)

            lines.append(f"\n  [METRIC] {name}:")
            lines.append(f"     Total: {total*1000:.2f}ms")
            lines.append(f"     Average: {avg*1000:.2f}ms")
            lines.append(f"     Max: {max_time*1000:.2f}ms")
            lines.append(f"     Min: {min_time*1000:.2f}ms")
            lines.append(f"     Calls: {len(times)}")

        # 瓶颈分析
        lines.append(f"\n[BOTTLENECK] Analysis:")
        bottleneck = sorted_metrics[0] if sorted_metrics else None
        if bottleneck:
            name, times = bottleneck
            bottleneck_pct = (sum(times) / total_time) * 100 if total_time > 0 else 0
            lines.append(f"  Main Bottleneck: {name}")
            lines.append(f"  Percentage: {bottleneck_pct:.1f}%")
            lines.append(f"  Recommendation: Optimize this component first")

        # 性能评级
        lines.append(f"\n[RATING] Performance Rating:")
        if total_time < 3.0:
            lines.append(f"  Rating: EXCELLENT (< 3s)")
        elif total_time < 5.0:
            lines.append(f"  Rating: GOOD (3-5s)")
        else:
            lines.append(f"  Rating: NEEDS OPTIMIZATION (> 5s)")

        lines.append("\n" + "="*60)
        return "\n".join(lines)


def create_performance_diagnostic_config() -> Dict:
    """创建性能诊断配置

    Returns:
        性能诊断配置
    """
    return {
        'model': 'anthropic:claude-sonnet-4-5-20250929',
        'exchanges': {},
        'mem0': {},
        'monitoring': {'enabled': True, 'alert_methods': ['console']},
        'enhanced_low_risk_engine': {
            'enabled': True,
            'enable_risk_prediction': True,
            'enable_health_monitoring': True,
            'enable_intelligent_decision': True
        },
        'trading_agents': {
            'enabled': False,  # 性能诊断时禁用以减少 LLM 调用
        }
    }


async def run_performance_diagnostic():
    """运行性能诊断

    Returns:
        性能报告
    """
    profiler = PerformanceProfiler()

    @profiler.profile("total_initialization")
    async def test_initialization():
        """测试初始化性能"""

        @profiler.profile("agent_import")
        def test_import():
            from agents.main_agent import CryptoArbitrageAgent
            return CryptoArbitrageAgent

        CryptoArbitrageAgent = test_import()

        @profiler.profile("agent_creation")
        def create_agent():
            config = create_performance_diagnostic_config()
            return CryptoArbitrageAgent(config)

        agent = create_agent()

        @profiler.profile("component_check")
        def check_components():
            """检查组件初始化状态"""
            return {
                'has_exchange_manager': agent.exchange_manager is not None,
                'has_risk_manager': agent.risk_manager is not None,
                'has_monitoring': agent.monitoring is not None,
                'has_strategy_manager': agent.strategy_manager is not None,
                'has_enhanced_engine': agent.enhanced_low_risk_engine is not None,
                'total_tools': len([attr for attr in dir(agent) if 'tool' in attr.lower()])
            }

        components = check_components()

        @profiler.profile("memory_check")
        def check_memory():
            """检查内存使用"""
            import sys
            agent_size = sys.getsizeof(agent)
            return agent_size

        memory_usage = check_memory()

        return agent, components, memory_usage

    agent, components, memory_usage = await test_initialization()

    # 生成报告
    report = profiler.get_report()

    # 附加信息
    report += f"\n[COMPONENTS] Component Status:"
    for key, value in components.items():
        status = "[OK]" if value else "[MISSING]"
        report += f"\n  {status} {key}: {value}"

    report += f"\n\n[MEMORY] Memory Usage: {memory_usage / 1024:.2f} KB"

    return report, agent


def print_bottleneck_analysis(report: str):
    """打印瓶颈分析

    Args:
        report: 性能报告
    """
    print("\n" + "="*60)
    print("[BOTTLENECK] Analysis and Optimization Suggestions")
    print("="*60)

    # 解析报告中的瓶颈信息
    lines = report.split('\n')
    bottleneck_section = False
    for line in lines:
        if 'BOTTLENECK' in line:
            bottleneck_section = True
            print(line)
        elif bottleneck_section:
            if line.strip().startswith('[RATING]'):
                print(line)
                break
            print(line)

    print("\n[OPTIMIZATION] Suggestions:")
    print("  1. Lazy Loading: Load non-critical components on demand")
    print("  2. Cache Optimization: Add query and computation result caching")
    print("  3. Concurrent Optimization: Use async concurrent init")
    print("  4. Config Optimization: Disable unnecessary components")
    print("  5. Code Optimization: Optimize hot path code logic")
    print("="*60)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    async def main():
        """主函数"""
        print("Starting performance diagnostic...")

        report, agent = await run_performance_diagnostic()

        print("\n" + report)
        print_bottleneck_analysis(report)

        print(f"\n[COMPLETE] Diagnostic finished, Agent instance created")

    asyncio.run(main())
