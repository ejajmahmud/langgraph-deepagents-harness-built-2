"""测试工具调用方式"""
import asyncio
from agents.main_agent import CryptoArbitrageAgent


async def test_tool_invoke():
    """测试不同方式调用工具"""
    config = {
        'model': 'anthropic:claude-sonnet-4-5-20250929',
        'exchanges': {},
        'mem0': {},
        'monitoring': {'enabled': True, 'alert_methods': ['console']}
    }

    agent = CryptoArbitrageAgent(config)

    print("Test 1: Direct method call")
    try:
        result = await agent.scan_arbitrage_opportunities_tool("all")
        print(f"OK: Direct call succeeded: {len(result)} chars")
    except Exception as e:
        print(f"FAIL: Direct call failed: {e}")

    print("\nTest 2: Use .invoke() method with self parameter")
    try:
        result = await agent.scan_arbitrage_opportunities_tool.invoke({
            "self": agent,
            "strategy_type": "all"
        })
        print(f"OK: invoke() with self succeeded: {len(result)} chars")
    except Exception as e:
        print(f"FAIL: invoke() with self failed: {e}")

    print("\nTest 3: Access tool properties")
    try:
        tool_obj = agent.scan_arbitrage_opportunities_tool
        print(f"Tool type: {type(tool_obj)}")
        print(f"Tool name: {tool_obj.name}")
        print(f"Tool description: {tool_obj.description}")
        print(f"Tool args schema: {tool_obj.args_schema}")
        print(f"Tool func: {tool_obj.func}")
        print(f"All attributes: {[attr for attr in dir(tool_obj) if not attr.startswith('_')]}")
    except Exception as e:
        print(f"FAIL: Access tool properties failed: {e}")

    print("\nTest 4: Call via coroutine")
    try:
        # 访问coroutine属性
        coro = agent.scan_arbitrage_opportunities_tool.coroutine
        result = await coro(agent, "all")
        print(f"OK: coroutine call succeeded: {len(result)} chars")
        print(f"Result preview: {result[:100]}...")
    except Exception as e:
        print(f"FAIL: coroutine call failed: {e}")

    print("\nTest 5: Call via ainvoke with agent bound")
    try:
        # 使用ainvoke方法，将agent绑定
        result = await agent.scan_arbitrage_opportunities_tool.ainvoke(
            {"strategy_type": "all"},
            config={"run_name": "test"}
        )
        print(f"OK: ainvoke succeeded: {len(result)} chars")
        print(f"Result preview: {result[:100]}...")
    except Exception as e:
        print(f"FAIL: ainvoke failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_tool_invoke())
