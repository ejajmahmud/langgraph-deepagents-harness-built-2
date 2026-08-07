"""测试通过func属性调用原始函数"""
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

    print("=== Testing func attribute ===")

    # Test all tools using func attribute
    tools_to_test = [
        ('scan_arbitrage_opportunities_tool', ["all"], True),
        ('get_risk_status_tool', [], False),
        ('get_performance_stats_tool', [], False),
        ('record_knowledge_tool', ['strategy', 'test'], False),
        ('search_knowledge_tool', ['test', 5], False),
        ('get_monitoring_status_tool', [], False),
        ('get_alert_history_tool', [10], False),
        ('execute_arbitrage_tool', [0, "cross_exchange"], True),
    ]

    for tool_name, args, is_async in tools_to_test:
        try:
            tool_obj = getattr(agent, tool_name)
            original_func = tool_obj.func

            if is_async:
                result = await original_func(agent, *args)
            else:
                result = original_func(agent, *args)

            print(f"✅ {tool_name}: Success ({len(result)} chars)")
        except Exception as e:
            print(f"❌ {tool_name}: Failed ({e})")


if __name__ == "__main__":
    asyncio.run(test())
