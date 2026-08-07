"""策略回测可视化

生成策略回测结果的交互式图表，包括：
- 权益曲线
- 回撤曲线
- 收益分布
- 交易历史
- 月度/年度收益

输出格式：Plotly JSON（支持前端渲染）
"""

import json
from typing import Any, Dict, List, Optional

import pandas as pd


class BacktestVisualization:
    """策略回测可视化生成器

    生成回测结果的多种图表数据，用于前端展示。
    """

    def __init__(self):
        """初始化可视化生成器"""
        pass

    def generate_equity_curve_chart(
        self,
        backtest_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成权益曲线图表

        Args:
            backtest_results: 回测结果字典
                - dates: 日期列表
                - equity_curve: 权益曲线
                - drawdown: 回撤曲线
                - benchmark: 基准收益（可选）

        Returns:
            Plotly图表数据（JSON格式）
        """
        dates = backtest_results.get("dates", [])
        equity_curve = backtest_results.get("equity_curve", [])
        drawdown = backtest_results.get("drawdown", [])
        benchmark = backtest_results.get("benchmark", None)

        # 交易数据
        traces = []

        # 权益曲线
        if dates and equity_curve:
            traces.append({
                "x": dates,
                "y": equity_curve,
                "mode": "lines",
                "name": "Strategy Equity",
                "line": {"color": "#00D4FF", "width": 2}
            })

        # 基准曲线
        if benchmark and dates:
            traces.append({
                "x": dates,
                "y": benchmark,
                "mode": "lines",
                "name": "Benchmark",
                "line": {"color": "#FF6B6B", "width": 2, "dash": "dash"}
            })

        # 初始资金线
        if dates and equity_curve:
            initial_equity = equity_curve[0]
            traces.append({
                "x": [dates[0], dates[-1]],
                "y": [initial_equity, initial_equity],
                "mode": "lines",
                "name": "Initial Capital",
                "line": {"color": "#808080", "width": 1, "dash": "dot"}
            })

        layout = {
            "title": "Equity Curve",
            "xaxis": {"title": "Date"},
            "yaxis": {"title": "Equity ($)"},
            "hovermode": "x unified",
            "showlegend": True,
            "template": "plotly_dark"
        }

        return {
            "data": traces,
            "layout": layout
        }

    def generate_drawdown_chart(
        self,
        backtest_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成回撤图表

        Args:
            backtest_results: 回测结果字典

        Returns:
            Plotly图表数据
        """
        dates = backtest_results.get("dates", [])
        drawdown = backtest_results.get("drawdown", [])

        traces = []

        if dates and drawdown:
            traces.append({
                "x": dates,
                "y": drawdown,
                "mode": "lines",
                "name": "Drawdown",
                "fill": "tozeroy",
                "line": {"color": "#FF4757", "width": 1}
            })

        layout = {
            "title": "Drawdown Chart",
            "xaxis": {"title": "Date"},
            "yaxis": {"title": "Drawdown (%)"},
            "hovermode": "x unified",
            "showlegend": False,
            "template": "plotly_dark"
        }

        return {
            "data": traces,
            "layout": layout
        }

    def generate_returns_distribution(
        self,
        backtest_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成收益分布直方图

        Args:
            backtest_results: 回测结果字典

        Returns:
            Plotly图表数据
        """
        daily_returns = backtest_results.get("daily_returns", [])

        traces = []

        if daily_returns:
            traces.append({
                "x": daily_returns,
                "type": "histogram",
                "name": "Daily Returns",
                "marker": {"color": "#00D4FF"}
            })

        layout = {
            "title": "Returns Distribution",
            "xaxis": {"title": "Daily Return (%)"},
            "yaxis": {"title": "Frequency"},
            "hovermode": "x unified",
            "showlegend": False,
            "template": "plotly_dark"
        }

        return {
            "data": traces,
            "layout": layout
        }

    def generate_monthly_returns_heatmap(
        self,
        backtest_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成月度收益热力图

        Args:
            backtest_results: 回测结果字典

        Returns:
            Plotly图表数据
        """
        # 简化实现：直接使用daily_returns计算月度收益
        dates = backtest_results.get("dates", [])
        daily_returns = backtest_results.get("daily_returns", [])

        if not dates or not daily_returns:
            return {"data": [], "layout": {}}

        # 转换为DataFrame
        df = pd.DataFrame({
            "date": pd.to_datetime(dates),
            "return": daily_returns
        })

        # 提取年月
        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.month

        # 计算月度收益
        monthly_returns = df.groupby(["year", "month"])["return"].sum().reset_index()

        # 创建热力图数据
        years = sorted(monthly_returns["year"].unique())
        months = list(range(1, 13))

        # 填充数据矩阵
        z = []
        for year in years:
            row = []
            for month in months:
                match = monthly_returns[
                    (monthly_returns["year"] == year) &
                    (monthly_returns["month"] == month)
                ]
                if not match.empty:
                    row.append(match["return"].values[0] * 100)
                else:
                    row.append(0)
            z.append(row)

        traces = [{
            "z": z,
            "x": ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
            "y": [str(year) for year in years],
            "type": "heatmap",
            "colorscale": "RdYlGn"
        }]

        layout = {
            "title": "Monthly Returns Heatmap (%)",
            "hovermode": "closest",
            "showlegend": False,
            "template": "plotly_dark"
        }

        return {
            "data": traces,
            "layout": layout
        }

    def generate_trades_table(
        self,
        backtest_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成交易历史表格数据

        Args:
            backtest_results: 回测结果字典

        Returns:
            交易历史列表
        """
        trades = backtest_results.get("trades", [])

        table_data = []
        for trade in trades:
            table_data.append({
                "date": trade.get("date", ""),
                "symbol": trade.get("symbol", ""),
                "action": trade.get("action", ""),
                "price": trade.get("price", 0),
                "quantity": trade.get("quantity", 0),
                "profit": trade.get("profit", 0),
                "profit_pct": trade.get("profit_pct", 0)
            })

        return table_data

    def generate_summary_metrics(
        self,
        backtest_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成汇总指标

        Args:
            backtest_results: 回测结果字典

        Returns:
            汇总指标字典
        """
        equity_curve = backtest_results.get("equity_curve", [])
        drawdown = backtest_results.get("drawdown", [])
        trades = backtest_results.get("trades", [])

        if not equity_curve:
            return {}

        # 计算指标
        initial_equity = equity_curve[0]
        final_equity = equity_curve[-1]
        total_return = (final_equity - initial_equity) / initial_equity * 100

        # 最大回撤
        max_drawdown = min(drawdown) if drawdown else 0

        # 交易统计
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.get("profit", 0) > 0])
        losing_trades = total_trades - winning_trades
        win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0

        # 平均收益
        profits = [t.get("profit", 0) for t in trades]
        avg_profit = sum(profits) / len(profits) if profits else 0

        return {
            "total_return": total_return,
            "max_drawdown": max_drawdown,
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
            "avg_profit": avg_profit
        }

    def generate_dashboard_data(
        self,
        backtest_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成完整的仪表盘数据

        Args:
            backtest_results: 回测结果字典

        Returns:
            完整仪表盘数据字典
        """
        return {
            "equity_curve": self.generate_equity_curve_chart(backtest_results),
            "drawdown_chart": self.generate_drawdown_chart(backtest_results),
            "returns_distribution": self.generate_returns_distribution(backtest_results),
            "monthly_returns": self.generate_monthly_returns_heatmap(backtest_results),
            "trades_table": self.generate_trades_table(backtest_results),
            "summary_metrics": self.generate_summary_metrics(backtest_results)
        }


def create_backtest_visualization() -> BacktestVisualization:
    """工厂函数：创建回测可视化生成器

    Returns:
        BacktestVisualization实例
    """
    return BacktestVisualization()
