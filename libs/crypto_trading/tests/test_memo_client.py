"""Tests for memo client module."""

import pytest

import pandas as pd

from deepagents_crypto_trading.memo_client import KnowledgeBase, Memo0Client
from deepagents_crypto_trading.types import (
    ArbitrageType,
    OrderSide,
    Position,
    PositionStatus,
    TradingConfig,
)


class TestMemo0Client:
    """Tests for Memo0Client."""

    def test_creation(self) -> None:
        """Test memo0 client creation."""
        config = TradingConfig()
        client = Memo0Client(config)
        assert not client.is_enabled()

    def test_creation_with_api_key(self) -> None:
        """Test creation with API key (mock)."""
        import os

        os.environ["MEM0_API_KEY"] = "test_key"
        config = TradingConfig(memo0_enabled=True)
        client = Memo0Client(config)
        assert client.is_enabled()
        assert client.is_using_real_api()
        del os.environ["MEM0_API_KEY"]

    @pytest.mark.asyncio
    async def test_save_trade(self) -> None:
        """Test saving trade."""
        config = TradingConfig()
        client = Memo0Client(config)
        position = Position(
            id="test-1",
            arbitrage_type=ArbitrageType.CROSS_EXCHANGE,
            trading_pairs=[],
            entry_price=100.0,
            current_price=105.0,
            size=1.0,
            side=OrderSide.BUY,
            status=PositionStatus.CLOSED,
            pnl=5.0,
            opened_at=pd.Timestamp.now(),
        )
        result = await client.save_trade(position)
        assert result is True

    @pytest.mark.asyncio
    async def test_save_knowledge(self) -> None:
        """Test saving knowledge."""
        config = TradingConfig()
        client = Memo0Client(config)
        result = await client.save_knowledge("test-key", "test content")
        assert result is True

    @pytest.mark.asyncio
    async def test_save_progress(self) -> None:
        """Test saving progress."""
        config = TradingConfig()
        client = Memo0Client(config)
        result = await client.save_progress(
            "0.2.0",
            "completed",
            ["feature1", "feature2"],
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_load_trades(self) -> None:
        """Test loading trades."""
        config = TradingConfig()
        client = Memo0Client(config)
        trades = await client.load_trades()
        assert isinstance(trades, list)

    @pytest.mark.asyncio
    async def test_search_memories(self) -> None:
        """Test searching memories."""
        config = TradingConfig()
        client = Memo0Client(config)
        # Save some data first
        await client.save_knowledge("test-key", "test content")
        results = await client.search_memories("test")
        assert isinstance(results, list)

    def test_get_stats(self) -> None:
        """Test getting stats."""
        config = TradingConfig()
        client = Memo0Client(config)
        stats = client.get_stats()
        assert "enabled" in stats
        assert "using_real_api" in stats
        assert stats["using_real_api"] is False


class TestKnowledgeBase:
    """Tests for KnowledgeBase."""

    @pytest.mark.asyncio
    async def test_creation(self) -> None:
        """Test knowledge base creation."""
        config = TradingConfig()
        client = Memo0Client(config)
        kb = KnowledgeBase(client)
        assert kb.current_version == "0.1.0"

    @pytest.mark.asyncio
    async def test_record_progress(self) -> None:
        """Test recording progress."""
        config = TradingConfig()
        client = Memo0Client(config)
        kb = KnowledgeBase(client)
        result = await kb.record_progress(["feature1", "feature2"])
        assert result is True

    @pytest.mark.asyncio
    async def test_save_feature(self) -> None:
        """Test saving feature."""
        config = TradingConfig()
        client = Memo0Client(config)
        kb = KnowledgeBase(client)
        result = await kb.save_feature("test-feature", "Test feature desc")
        assert result is True