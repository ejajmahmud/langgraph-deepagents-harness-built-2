"""Charts Module - Price and P&L Visualization.

Provides chart data generation for dashboard visualization.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from deepagents_crypto_trading.types import TradingPair


class ChartType(Enum):
    """Chart types."""
    LINE = "line"
    CANDLESTICK = "candlestick"
    AREA = "area"
    BAR = "bar"


class ChartTimeframe(Enum):
    """Chart timeframes."""
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1w"


@dataclass
class ChartDataPoint:
    """Single chart data point."""
    timestamp: float
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: float = 0.0
    value: float = 0.0

    @property
    def date(self) -> str:
        """ISO date string."""
        return datetime.fromtimestamp(self.timestamp).isoformat()


@dataclass
class ChartSeries:
    """Chart data series."""
    name: str
    data: list[ChartDataPoint] = field(default_factory=list)
    color: str = "#3b82f6"

    def add_point(self, point: ChartDataPoint) -> None:
        """Add data point."""
        self.data.append(point)

    def to_chartjs(self) -> dict:
        """Convert to Chart.js format."""
        return {
            "label": self.name,
            "data": [
                {
                    "x": p.timestamp * 1000,  # JavaScript timestamp
                    "o": p.open,
                    "h": p.high,
                    "l": p.low,
                    "c": p.close,
                    "v": p.volume,
                }
                for p in self.data
            ],
            "borderColor": self.color,
            "backgroundColor": self.color + "20",
        }


@dataclass
class ChartConfig:
    """Chart configuration."""
    chart_type: ChartType = ChartType.LINE
    timeframe: ChartTimeframe = ChartTimeframe.H1
    show_volume: bool = True
    show_ma: bool = True
    ma_periods: list[int] = field(default_factory=lambda: [7, 25, 99])
    height: int = 400
    width: int = 800


class PriceChart:
    """Price chart data generator.

    Features:
    - OHLCV data storage
    - Moving average calculation
    - Chart.js export
    - Multiple timeframe support
    """

    def __init__(
        self,
        trading_pair: TradingPair,
        config: Optional[ChartConfig] = None,
    ) -> None:
        """Initialize price chart.

        Args:
            trading_pair: Trading pair for the chart.
            config: Chart configuration.
        """
        self.trading_pair = trading_pair
        self.config = config or ChartConfig()
        self._data: list[ChartDataPoint] = []
        self._series: dict[str, ChartSeries] = {}

    def add_price(
        self,
        timestamp: float,
        price: float,
        volume: float = 0.0,
    ) -> None:
        """Add price data point.

        Args:
            timestamp: Unix timestamp.
            price: Current price.
            volume: Trading volume.
        """
        # For simple line/area charts
        point = ChartDataPoint(
            timestamp=timestamp,
            close=price,
            open=price,
            high=price,
            low=price,
            volume=volume,
            value=price,
        )
        self._data.append(point)

        # Update series
        if "price" not in self._series:
            self._series["price"] = ChartSeries(
                name=f"{self.trading_pair.symbol} Price",
                color="#3b82f6",
            )
        self._series["price"].add_point(point)

    def add_ohlcv(
        self,
        timestamp: float,
        open: float,
        high: float,
        low: float,
        close: float,
        volume: float = 0.0,
    ) -> None:
        """Add OHLCV data point.

        Args:
            timestamp: Unix timestamp.
            open: Open price.
            high: High price.
            low: Low price.
            close: Close price.
            volume: Volume.
        """
        point = ChartDataPoint(
            timestamp=timestamp,
            open=open,
            high=high,
            low=low,
            close=close,
            volume=volume,
            value=close,
        )
        self._data.append(point)

        # Update series
        if "ohlc" not in self._series:
            self._series["ohlc"] = ChartSeries(
                name=f"{self.trading_pair.symbol} OHLC",
                color="#10b981",
            )
        self._series["ohlc"].add_point(point)

    def calculate_ma(self, period: int) -> list[float]:
        """Calculate simple moving average.

        Args:
            period: MA period.

        Returns:
            List of MA values (aligned to data points).
        """
        if len(self._data) < period:
            return []

        ma_values = []
        for i in range(len(self._data)):
            if i < period - 1:
                ma_values.append(0.0)
            else:
                avg = sum(d.close for d in self._data[i - period + 1:i + 1]) / period
                ma_values.append(avg)

        return ma_values

    def calculate_ema(self, period: int) -> list[float]:
        """Calculate exponential moving average.

        Args:
            period: EMA period.

        Returns:
            List of EMA values.
        """
        if len(self._data) < period:
            return []

        k = 2 / (period + 1)
        ema_values = []

        for i in range(len(self._data)):
            if i < period - 1:
                ema_values.append(0.0)
            elif i == period - 1:
                # First EMA is SMA
                avg = sum(d.close for d in self._data[:period]) / period
                ema_values.append(avg)
            else:
                prev_ema = ema_values[-1]
                ema = self._data[i].close * k + prev_ema * (1 - k)
                ema_values.append(ema)

        return ema_values

    def get_chart_data(self) -> dict:
        """Get chart data in Chart.js format.

        Returns:
            Dictionary for Chart.js rendering.
        """
        if not self._data:
            return {"labels": [], "datasets": []}

        labels = [datetime.fromtimestamp(d.timestamp).strftime("%Y-%m-%d %H:%M")
                 for d in self._data]

        datasets = []

        # Price/OHLC data
        if self.config.show_volume and any(d.volume > 0 for d in self._data):
            datasets.append({
                "label": "Volume",
                "data": [d.volume for d in self._data],
                "type": "bar",
                "backgroundColor": "#3b82f620",
                "yAxisID": "y1",
            })

        # Price line
        datasets.append({
            "label": f"{self.trading_pair.symbol} Price",
            "data": [d.close for d in self._data],
            "type": self.config.chart_type.value,
            "borderColor": "#3b82f6",
            "backgroundColor": "#3b82f620",
            "fill": self.config.chart_type == ChartType.AREA,
            "yAxisID": "y0",
        })

        # Moving averages
        if self.config.show_ma:
            colors = ["#10b981", "#f59e0b", "#ef4444"]
            for i, period in enumerate(self.config.ma_periods):
                ma_values = self.calculate_ma(period)
                if any(v > 0 for v in ma_values):
                    datasets.append({
                        "label": f"MA{period}",
                        "data": ma_values,
                        "type": "line",
                        "borderColor": colors[i % len(colors)],
                        "borderWidth": 1,
                        "fill": False,
                        "pointRadius": 0,
                        "yAxisID": "y0",
                    })

        return {
            "labels": labels,
            "datasets": datasets,
            "options": {
                "responsive": True,
                "maintainAspectRatio": False,
                "scales": {
                    "y0": {
                        "type": "linear",
                        "display": True,
                        "position": "left",
                        "title": {"display": True, "text": "Price"},
                    },
                    "y1": {
                        "type": "linear",
                        "display": True,
                        "position": "right",
                        "title": {"display": True, "text": "Volume"},
                        "grid": {"drawOnChartArea": False},
                    },
                },
            },
        }

    def to_html(self) -> str:
        """Generate HTML chart with Chart.js.

        Returns:
            HTML string.
        """
        chart_data = self.get_chart_data()

        return f"""<canvas id="chart-{self.trading_pair.symbol.replace('/', '-')}"
    width="{self.config.width}" height="{self.config.height}"></canvas>
<script>
const ctx = document.getElementById('chart-{self.trading_pair.symbol.replace('/', '-')}');
new Chart(ctx, {json.dumps(chart_data)});
</script>"""

    def get_data_points(self) -> list[ChartDataPoint]:
        """Get all data points.

        Returns:
            List of data points.
        """
        return self._data

    def get_latest_price(self) -> Optional[float]:
        """Get latest price.

        Returns:
            Latest price or None.
        """
        if self._data:
            return self._data[-1].close
        return None


class PnLChart:
    """P&L chart for portfolio performance.

    Features:
    - Cumulative P&L tracking
    - Daily P&L bar chart
    - Equity curve
    """

    def __init__(self) -> None:
        """Initialize P&L chart."""
        self._snapshots: list[dict] = []
        self._equity_curve: list[float] = []
        self._initial_value: float = 0.0

    def set_initial_value(self, value: float) -> None:
        """Set initial portfolio value.

        Args:
            value: Initial value.
        """
        self._initial_value = value
        self._equity_curve.append(value)

    def add_snapshot(
        self,
        timestamp: float,
        total_value: float,
        unrealized_pnl: float = 0.0,
        realized_pnl: float = 0.0,
    ) -> None:
        """Add portfolio snapshot.

        Args:
            timestamp: Unix timestamp.
            total_value: Total portfolio value.
            unrealized_pnl: Unrealized P&L.
            realized_pnl: Realized P&L.
        """
        snapshot = {
            "timestamp": timestamp,
            "total_value": total_value,
            "unrealized_pnl": unrealized_pnl,
            "realized_pnl": realized_pnl,
            "total_pnl": unrealized_pnl + realized_pnl,
        }
        self._snapshots.append(snapshot)
        self._equity_curve.append(total_value)

    def get_equity_curve(self) -> list[dict]:
        """Get equity curve data.

        Returns:
            List of equity curve points.
        """
        return [
            {
                "x": s["timestamp"] * 1000,
                "y": s["total_value"],
            }
            for s in self._snapshots
        ]

    def get_pnl_curve(self) -> list[dict]:
        """Get cumulative P&L curve.

        Returns:
            List of P&L points.
        """
        return [
            {
                "x": s["timestamp"] * 1000,
                "y": s["total_pnl"],
            }
            for s in self._snapshots
        ]

    def get_daily_pnl(self) -> list[dict]:
        """Get daily P&L bar chart data.

        Returns:
            List of daily P&L points.
        """
        daily = []
        for i in range(1, len(self._snapshots)):
            prev_val = self._snapshots[i - 1]["total_value"]
            curr_val = self._snapshots[i]["total_value"]
            daily.append({
                "x": self._snapshots[i]["timestamp"] * 1000,
                "y": curr_val - prev_val,
            })
        return daily

    def get_chart_data(self) -> dict:
        """Get P&L chart data.

        Returns:
            Dictionary for Chart.js.
        """
        return {
            "equity_curve": self.get_equity_curve(),
            "pnl_curve": self.get_pnl_curve(),
            "daily_pnl": self.get_daily_pnl(),
        }

    def calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown.

        Returns:
            Max drawdown percentage.
        """
        if not self._equity_curve:
            return 0.0

        peak = self._equity_curve[0]
        max_dd = 0.0

        for value in self._equity_curve:
            if value > peak:
                peak = value
            dd = (peak - value) / peak if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd

        return max_dd * 100

    def calculate_sharpe_ratio(self, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio.

        Args:
            risk_free_rate: Annual risk-free rate.

        Returns:
            Sharpe ratio.
        """
        if len(self._snapshots) < 2:
            return 0.0

        returns = []
        for i in range(1, len(self._snapshots)):
            prev_val = self._snapshots[i - 1]["total_value"]
            curr_val = self._snapshots[i]["total_value"]
            if prev_val > 0:
                ret = (curr_val - prev_val) / prev_val
                returns.append(ret)

        if not returns:
            return 0.0

        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        std_dev = variance ** 0.5

        if std_dev == 0:
            return 0.0

        return (mean_return - risk_free_rate / 365) / std_dev


# Type aliases
__all__ = [
    "ChartType",
    "ChartTimeframe",
    "ChartDataPoint",
    "ChartSeries",
    "ChartConfig",
    "PriceChart",
    "PnLChart",
]