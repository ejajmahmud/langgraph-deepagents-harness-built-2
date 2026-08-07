"""测试get_alert_history_tool的返回值"""
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

    print("Testing get_alert_history_tool:")
    try:
        result = agent.get_alert_history_tool.func(agent, 10)
        print(f"Result: {result}")
        print(f"Result type: {type(result)}")
        print(f"Result length: {len(result)}")
        print(f"Contains '告警历史': {'告警历史' in result}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test())
