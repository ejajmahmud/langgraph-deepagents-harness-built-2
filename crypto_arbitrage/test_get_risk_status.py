"""测试get_risk_status_tool的返回值"""
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

    print("Testing get_risk_status_tool:")
    try:
        result = agent.get_risk_status_tool.func(agent)
        print(f"Result: {result}")
        print(f"Result type: {type(result)}")
        print(f"Result length: {len(result)}")
        print(f"Contains '当前风险状态': {'当前风险状态' in result}")
        print(f"Contains '当前敞口': {'当前敞口' in result}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test())
