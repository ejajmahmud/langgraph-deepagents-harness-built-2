"""Multi-timeframe analysis module.

This module provides:
- Timeframe: Timeframe enumeration
- TimeframeData: Data for a specific timeframe
- MultiTimeframeConfig: Configuration for multi-timeframe analysis
- CrossTimeframeSignal: Signals across timeframes
- TimeframeAnalyzer: Multi-timeframe analysis engine
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

import pandas as pd
import numpy as np


class Timeframe(str, Enum):
    """Trading timeframe."""

    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1w"

    def to_minutes(self) -> int:
        """Convert to minutes.

        Returns:
            Number of minutes.
        """
        mapping = {
            "1m": 1,
            "5m": 5,
            "15m": 15,
            "30m": 30,
            "1h": 60,
            "4h": 240,
            "1d": 1440,
            "1w": 10080,
        }
        return mapping.get(self.value, 60)

    def to_seconds(self) -> int:
        """Convert to seconds.

        Returns:
            Number of seconds.
        """
        return self.to_minutes() * 60


@dataclass
class TimeframeData:
    """Data for a specific timeframe."""

    timeframe: Timeframe
    df: pd.DataFrame = field(default_factory=pd.DataFrame)
    signals: list[int] = field(default_factory=list)
    indicators: dict = field(default_factory=dict)
    last_update: Optional[datetime] = None

    @property
    def is_empty(self) -> bool:
        """Check if data is empty."""
        return self.df.empty

    @property
    def last_price(self) -> Optional[float]:
        """Get last price."""
        if self.df.empty:
            return None
        return float(self.df.iloc[-1]["close"])

    @property
    def trend(self) -> str:
        """Get trend direction (bullish/bearish/neutral)."""
        if self.df.empty or len(self.df) < 2:
            return "neutral"

        current = self.df.iloc[-1]["close"]
        previous = self.df.iloc[-2]["close"]

        if current > previous * 1.01:
            return "bullish"
        elif current < previous * 0.99:
            return "bearish"
        else:
            return "neutral"

    @property
    def momentum(self) -> float:
        """Calculate momentum (0-100)."""
        if self.df.empty or len(self.df) < 14:
            return 50.0

        # RSI-style momentum
        deltas = self.df["close"].diff()
        gains = deltas.where(deltas > 0, 0.0)
        losses = -deltas.where(deltas < 0, 0.0)

        avg_gain = gains.rolling(14).mean()
        avg_loss = losses.rolling(14).mean()

        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))

        return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0

    @property
    def volatility(self) -> float:
        """Calculate volatility (annualized)."""
        if self.df.empty or len(self.df) < 20:
            return 0.0

        returns = self.df["close"].pct_change()
        std = returns.rolling(20).std().iloc[-1]

        if pd.isna(std):
            return 0.0

        # Annualize
        periods = {"1m": 525600, "5m": 105120, "15m": 35040, "30m": 17520,
                  "1h": 8760, "4h": 2190, "1d": 365, "1w": 52}
        factor = periods.get(self.timeframe.value, 8760)

        return float(std * np.sqrt(factor) * 100)


@dataclass
class MultiTimeframeConfig:
    """Configuration for multi-timeframe analysis."""

    symbol: str = "BTCUSDT"
    timeframes: list[Timeframe] = field(
        default_factory=lambda: [Timeframe.M15, Timeframe.H1, Timeframe.H4]
    )
    alignment_threshold: float = 0.7  # Signal alignment required
    use_stronger_tf: bool = True  # Use stronger timeframe for signals
    require_higher_tf_confirmation: bool = True


@dataclass
class CrossTimeframeSignal:
    """Signal from multi-timeframe analysis."""

    symbol: str
    signal: int  # -1 (sell), 0 (neutral), 1 (buy)
    confidence: float  # 0-100
    timeframes: list[Timeframe]
    trend: str  # bullish/bearish/neutral
    momentum: float  # 0-100
    reasons: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


class TimeframeAnalyzer:
    """Multi-timeframe analysis engine.

    Analyzes market data across multiple timeframes to generate
    aligned trading signals.
    """

    def __init__(self, config: Optional[MultiTimeframeConfig] = None) -> None:
        """Initialize timeframe analyzer.

        Args:
            config: Configuration.
        """
        self.config = config or MultiTimeframeConfig()
        self._data: dict[Timeframe, TimeframeData] = {}
        self._initialize_data()

    def _initialize_data(self) -> None:
        """Initialize data structures for each timeframe."""
        for tf in self.config.timeframes:
            self._data[tf] = TimeframeData(timeframe=tf)

    def add_data(self, timeframe: Timeframe, df: pd.DataFrame) -> None:
        """Add data for a timeframe.

        Args:
            timeframe: Timeframe.
            df: OHLCV data.
        """
        if timeframe not in self._data:
            self._data[timeframe] = TimeframeData(timeframe=timeframe)

        self._data[timeframe].df = df
        self._data[timeframe].last_update = datetime.now()

        # Calculate indicators
        self._calculate_indicators(timeframe, df)

    def _calculate_indicators(self, timeframe: Timeframe, df: pd.DataFrame) -> None:
        """Calculate indicators for timeframe.

        Args:
            timeframe: Timeframe.
            df: OHLCV data.
        """
        if df.empty:
            return

        data = self._data[timeframe]

        # Moving averages
        data.indicators["sma_20"] = df["close"].rolling(20).mean()
        data.indicators["sma_50"] = df["close"].rolling(50).mean()
        data.indicators["sma_200"] = df["close"].rolling(200).mean()

        # EMA
        data.indicators["ema_12"] = df["close"].ewm(span=12).mean()
        data.indicators["ema_26"] = df["close"].ewm(span=26).mean()

        # MACD
        macd = data.indicators["ema_12"] - data.indicators["ema_26"]
        signal = macd.ewm(span=9).mean()
        data.indicators["macd"] = macd
        data.indicators["macd_signal"] = signal
        data.indicators["macd_histogram"] = macd - signal

        # Bollinger Bands
        sma = df["close"].rolling(20).mean()
        std = df["close"].rolling(20).std()
        data.indicators["bb_upper"] = sma + (std * 2)
        data.indicators["bb_middle"] = sma
        data.indicators["bb_lower"] = sma - (std * 2)

        # RSI
        delta = df["close"].diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        data.indicators["rsi"] = 100 - (100 / (1 + rs))

        # Generate signals
        data.signals = self._generate_signals(timeframe)

    def _generate_signals(self, timeframe: Timeframe) -> list[int]:
        """Generate signals for timeframe.

        Args:
            timeframe: Timeframe.

        Returns:
            List of signals (-1, 0, 1).
        """
        data = self._data.get(timeframe)
        if not data or not data.indicators:
            return []

        signals = []
        close = data.df["close"]

        # Use multiple indicators
        for i in range(len(close)):
            if i < 50:
                signals.append(0)
                continue

            # MACD signal
            macd = data.indicators["macd"].iloc[i]
            macd_signal = data.indicators["macd_signal"].iloc[i]
            macd_hist = data.indicators["macd_histogram"].iloc[i]

            # RSI
            rsi = data.indicators["rsi"].iloc[i]

            # Moving averages
            sma_20 = data.indicators["sma_20"].iloc[i]
            sma_50 = data.indicators["sma_50"].iloc[i]

            price = close.iloc[i]

            # Signal logic
            score = 0

            # MACD crossover
            if pd.notna(macd) and pd.notna(macd_signal):
                if macd > macd_signal and macd_hist > 0:
                    score += 1
                elif macd < macd_signal and macd_hist < 0:
                    score -= 1

            # Trend
            if pd.notna(sma_20) and pd.notna(sma_50):
                if price > sma_20 > sma_50:
                    score += 1
                elif price < sma_20 < sma_50:
                    score -= 1

            # RSI
            if pd.notna(rsi):
                if rsi > 70:
                    score -= 1
                elif rsi < 30:
                    score += 1

            if score >= 2:
                signals.append(1)
            elif score <= -2:
                signals.append(-1)
            else:
                signals.append(0)

        return signals

    def get_signal(self) -> CrossTimeframeSignal:
        """Get multi-timeframe signal.

        Returns:
            Cross-timeframe signal.
        """
        symbol = self.config.symbol
        signals = []
        trends = []
        momentum_values = []

        for tf in self.config.timeframes:
            data = self._data.get(tf)
            if data and not data.is_empty:
                if data.signals:
                    signals.append(data.signals[-1])
                trends.append(data.trend)
                momentum_values.append(data.momentum)

        if not signals:
            return CrossTimeframeSignal(
                symbol=symbol,
                signal=0,
                confidence=0.0,
                timeframes=self.config.timeframes,
                trend="neutral",
                momentum=50.0,
                reasons=["No data available"],
            )

        # Calculate alignment
        alignment = sum(1 for s in signals if s == signals[0]) / len(signals)

        # Determine final signal
        final_signal = 0
        if alignment >= self.config.alignment_threshold:
            final_signal = signals[0]

        # Check stronger timeframe
        if self.config.use_stronger_tf and self.config.timeframes:
            higher_tf = self.config.timeframes[-1]
            higher_data = self._data.get(higher_tf)
            if higher_data and higher_data.signals:
                if higher_data.signals[-1] != 0:
                    final_signal = higher_data.signals[-1]

        # Higher timeframe confirmation
        if self.config.require_higher_tf_confirmation:
            higher_tf = self.config.timeframes[-1] if self.config.timeframes else None
            if higher_tf:
                higher_data = self._data.get(higher_tf)
                if higher_data and higher_data.signals:
                    # Higher TF must confirm
                    if final_signal != higher_data.signals[-1]:
                        final_signal = 0

        # Calculate confidence
        confidence = alignment * 100

        # Determine trend
        trend_counts = {}
        for t in trends:
            trend_counts[t] = trend_counts.get(t, 0) + 1
        trend = max(trend_counts, key=trend_counts.get) if trend_counts else "neutral"

        # Average momentum
        momentum = np.mean(momentum_values) if momentum_values else 50.0

        # Generate reasons
        reasons = []
        if alignment >= self.config.alignment_threshold:
            reasons.append(f"Signal alignment: {alignment*100:.0f}%")
        for tf, data in self._data.items():
            if data and not data.is_empty:
                if data.trend == "bullish":
                    reasons.append(f"{tf.value}: bullish trend")
                elif data.trend == "bearish":
                    reasons.append(f"{tf.value}: bearish trend")

                if data.momentum > 60:
                    reasons.append(f"{tf.value}: strong momentum")
                elif data.momentum < 40:
                    reasons.append(f"{tf.value}: weak momentum")

        return CrossTimeframeSignal(
            symbol=symbol,
            signal=final_signal,
            confidence=confidence,
            timeframes=self.config.timeframes,
            trend=trend,
            momentum=momentum,
            reasons=reasons,
        )

    def get_data(self, timeframe: Timeframe) -> Optional[TimeframeData]:
        """Get data for timeframe.

        Args:
            timeframe: Timeframe.

        Returns:
            Timeframe data or None.
        """
        return self._data.get(timeframe)

    def get_all_data(self) -> dict[Timeframe, TimeframeData]:
        """Get all timeframe data.

        Returns:
            Dictionary of timeframe data.
        """
        return self._data.copy()

    def get_summary(self) -> dict:
        """Get summary of all timeframes.

        Returns:
            Summary dictionary.
        """
        summary = {
            "symbol": self.config.symbol,
            "timeframes": [tf.value for tf in self.config.timeframes],
            "signals": {},
            "trends": {},
            "momentum": {},
        }

        for tf, data in self._data.items():
            if not data.is_empty:
                summary["signals"][tf.value] = data.signals[-1] if data.signals else 0
                summary["trends"][tf.value] = data.trend
                summary["momentum"][tf.value] = data.momentum
                summary[f"{tf.value}_price"] = data.last_price

        signal = self.get_signal()
        summary["final_signal"] = signal.signal
        summary["confidence"] = signal.confidence
        summary["final_trend"] = signal.trend
        summary["final_momentum"] = signal.momentum

        return summary


class MultiTimeframeManager:
    """Manages multiple timeframe analyzers."""

    def __init__(self) -> None:
        """Initialize manager."""
        self._analyzers: dict[str, TimeframeAnalyzer] = {}

    def create_analyzer(
        self,
        symbol: str,
        timeframes: Optional[list[Timeframe]] = None,
    ) -> TimeframeAnalyzer:
        """Create analyzer for symbol.

        Args:
            symbol: Trading symbol.
            timeframes: List of timeframes.

        Returns:
            Timeframe analyzer.
        """
        if timeframes is None:
            timeframes = [Timeframe.M15, Timeframe.H1, Timeframe.H4]

        config = MultiTimeframeConfig(
            symbol=symbol,
            timeframes=timeframes,
        )

        analyzer = TimeframeAnalyzer(config)
        self._analyzers[symbol] = analyzer
        return analyzer

    def get_analyzer(self, symbol: str) -> Optional[TimeframeAnalyzer]:
        """Get analyzer for symbol.

        Args:
            symbol: Trading symbol.

        Returns:
            Analyzer or None.
        """
        return self._analyzers.get(symbol)

    def get_all_signals(self) -> dict[str, CrossTimeframeSignal]:
        """Get signals for all symbols.

        Returns:
            Dictionary of signals.
        """
        signals = {}
        for symbol, analyzer in self._analyzers.items():
            signals[symbol] = analyzer.get_signal()
        return signals

    def remove_analyzer(self, symbol: str) -> bool:
        """Remove analyzer for symbol.

        Args:
            symbol: Trading symbol.

        Returns:
            True if removed.
        """
        if symbol in self._analyzers:
            del self._analyzers[symbol]
            return True
        return False