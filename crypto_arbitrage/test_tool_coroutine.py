"""检查工具的coroutine属性"""
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

    print("Checking coroutine attributes:")
    print(f"scan_arbitrage_opportunities_tool coroutine: {agent.scan_arbitrage_opportunities_tool.coroutine}")
    print(f"get_risk_status_tool coroutine: {agent.get_risk_status_tool.coroutine}")
    print(f"get_performance_stats_tool coroutine: {agent.get_performance_stats_tool.coroutine}")
    print(f"record_knowledge_tool coroutine: {agent.record_knowledge_tool.coroutine}")
    print(f"search_knowledge_tool coroutine: {agent.search_knowledge_tool.coroutine}")
    print(f"get_monitoring_status_tool coroutine: {agent.get_monitoring_status_tool.coroutine}")
    print(f"get_alert_history_tool coroutine: {agent.get_alert_history_tool.coroutine}")
    print(f"execute_arbitrage_tool coroutine: {agent.execute_arbitrage_tool.coroutine}")


if __name__ == "__main__":
    asyncio.run(test())
