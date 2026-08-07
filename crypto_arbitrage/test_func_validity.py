"""检查哪些工具有有效的func属性"""
import asyncio
from agents.main_agent import CryptoArbitrageAgent


async def test():
    config = {
        'model': 'anthropic:claude-sonnet-4-5-20250929',
        'exchanges': {},
        'mem0': {},
        'monitoring': {'enabled': True, 'alert_methods': ['console']}
    }
    agent = CryptoArbitrageAgent(config)

    print("=== Checking func validity for all tools ===")

    tool_names = [
        'scan_arbitrage_opportunities_tool',
        'get_risk_status_tool',
        'get_performance_stats_tool',
        'record_knowledge_tool',
        'search_knowledge_tool',
        'get_monitoring_status_tool',
        'get_alert_history_tool',
        'execute_arbitrage_tool',
    ]

    for tool_name in tool_names:
        tool_obj = getattr(agent, tool_name)
        has_func = hasattr(tool_obj, 'func') and tool_obj.func is not None
        has_coroutine = hasattr(tool_obj, 'coroutine') and tool_obj.coroutine is not None

        print(f"{tool_name}:")
        print(f"  has_func: {has_func}")
        print(f"  has_coroutine: {has_coroutine}")

        if has_func:
            print(f"  func type: {type(tool_obj.func)}")
        if has_coroutine:
            print(f"  coroutine type: {type(tool_obj.coroutine)}")


if __name__ == "__main__":
    asyncio.run(test())
