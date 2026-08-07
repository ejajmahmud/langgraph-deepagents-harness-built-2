"""3D市场可视化

生成市场的3D可视化，包括：
- 价格-成交量-波动率 3D散点图
- 多币种对比 3D柱状图
- 市场趋势 3D曲面图

输出格式：Plotly JSON
"""

import numpy as np
from typing import Any, Dict, List


class Market3DVisualizer:
    """3D市场可视化生成器

    生成市场的3D交互式可视化图表。
    """

    def __init__(self):
        """初始化可视化生成器"""
        pass

    def generate_3d_chart(
        self,
        market_data: Dict[str, Any],
        chart_type: str = "scatter"
    ) -> Dict[str, Any]:
        """生成3D图表

        Args:
            market_data: 市场数据字典
                - dates: 日期列表
                - prices: 价格字典 {"BTC": [values]}
                - volumes: 成交量字典 {"BTC": [values]}
                - volatilities: 波动率字典 {"BTC": [values]}
            chart_type: 图表类型 (scatter/bar/surface)

        Returns:
            Plotly 3D图表数据
        """
        if chart_type == "scatter":
            return self.generate_scatter_3d(market_data)
        elif chart_type == "bar":
            return self.generate_bar_3d(market_data)
        elif chart_type == "surface":
            return self.generate_surface_3d(market_data)
        else:
            return {"data": [], "layout": {}}

    def generate_scatter_3d(
        self,
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成3D散点图（价格-成交量-波动率）

        Args:
            market_data: 市场数据字典

        Returns:
            Plotly 3D散点图数据
        """
        dates = market_data.get("dates", [])
        prices = market_data.get("prices", {})
        volumes = market_data.get("volumes", {})
        volatilities = market_data.get("volatilities", {})

        traces = []

        # 为每个币种生成轨迹
        for symbol in prices.keys():
            price_list = prices.get(symbol, [])
            volume_list = volumes.get(symbol, [])
            volatility_list = volatilities.get(symbol, [])

            if not price_list or not volume_list or not volatility_list:
                continue

            traces.append({
                "x": price_list,
                "y": volume_list,
                "z": volatility_list,
                "mode": "markers",
                "name": symbol,
                "marker": {
                    "size": 5,
                    "color": list(range(len(price_list))),
                    "colorscale": "Viridis",
                    "opacity": 0.8
                },
                "type": "scatter3d"
            })

        layout = {
            "title": "3D Market Analysis: Price - Volume - Volatility",
            "scene": {
                "xaxis": {"title": "Price ($)"},
                "yaxis": {"title": "Volume"},
                "zaxis": {"title": "Volatility"}
            },
            "margin": {"l": 0, "r": 0, "b": 0, "t": 40},
            "template": "plotly_dark"
        }

        return {
            "data": traces,
            "layout": layout
        }

    def generate_bar_3d(
        self,
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成3D柱状图（多币种对比）

        Args:
            market_data: 市场数据字典

        Returns:
            Plotly 3D柱状图数据
        """
        dates = market_data.get("dates", [])
        prices = market_data.get("prices", {})

        if not dates or not prices:
            return {"data": [], "layout": {}}

        # 限制显示的数据点
        max_dates = 20
        if len(dates) > max_dates:
            dates = dates[-max_dates:]
            for symbol in prices:
                prices[symbol] = prices[symbol][-max_dates:]

        # 生成x, y, z数据
        x = []
        y = []
        z = []
        text = []

        symbols = list(prices.keys())

        for i, date in enumerate(dates):
            for symbol in symbols:
                price = prices[symbol][i] if i < len(prices[symbol]) else 0
                x.append(date)
                y.append(symbol)
                z.append(price)
                text.append(f"{symbol}<br>{date}<br>Price: ${price:.2f}")

        traces = [{
            "x": x,
            "y": y,
            "z": z,
            "mode": "markers",
            "marker": {
                "size": 10,
                "color": z,
                "colorscale": "Viridis",
                "opacity": 0.8
            },
            "text": text,
            "type": "scatter3d"
        }]

        layout = {
            "title": "3D Multi-Coin Price Comparison",
            "scene": {
                "xaxis": {"title": "Date"},
                "yaxis": {"title": "Symbol"},
                "zaxis": {"title": "Price ($)"}
            },
            "margin": {"l": 0, "r": 0, "b": 0, "t": 40},
            "template": "plotly_dark"
        }

        return {
            "data": traces,
            "layout": layout
        }

    def generate_surface_3d(
        self,
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成3D曲面图（市场趋势）

        Args:
            market_data: 市场数据字典

        Returns:
            Plotly 3D曲面图数据
        """
        dates = market_data.get("dates", [])
        prices = market_data.get("prices", {})

        if not dates or not prices:
            return {"data": [], "layout": {}}

        # 选择第一个币种演示
        symbol = list(prices.keys())[0]
        price_list = prices[symbol]

        if len(price_list) < 2:
            return {"data": [], "layout": {}}

        # 创建网格
        # X: 日期
        # Y: 时间窗口
        # Z: 价格

        max_points = 30
        if len(price_list) > max_points:
            price_list = price_list[-max_points:]
            dates = dates[-max_points:]

        # 简单滑动窗口平滑
        window_size = 5
        smoothed_prices = []
        for i in range(len(price_list)):
            start = max(0, i - window_size // 2)
            end = min(len(price_list), i + window_size // 2 + 1)
            window = price_list[start:end]
            smoothed_prices.append(sum(window) / len(window))

        # 创建网格
        x = list(range(len(smoothed_prices)))
        y = list(range(1, 6))  # 5条曲线
        z = []

        for j in y:
            # 不同幅度的波动
            z_row = [p * (1 + (j - 3) * 0.05) for p in smoothed_prices]
            z.append(z_row)

        traces = [{
            "x": x,
            "y": y,
            "z": z,
            "type": "surface",
            "colorscale": "Viridis",
            "opacity": 0.9
        }]

        layout = {
            "title": f"3D Market Trend Surface: {symbol}",
            "scene": {
                "xaxis": {"title": "Time"},
                "yaxis": {"title": "Variation"},
                "zaxis": {"title": "Price ($)"}
            },
            "margin": {"l": 0, "r": 0, "b": 0, "t": 40},
            "template": "plotly_dark"
        }

        return {
            "data": traces,
            "layout": layout
        }

    def generate_ripple_chart(
        self,
        market_data: Dict[str, Any],
        center_symbol: str = "BTC"
    ) -> Dict[str, Any]:
        """生成涟漪图（价格涟漪效应）

        Args:
            market_data: 市场数据字典
            center_symbol: 中心币种

        Returns:
            Plotly 3D涟漪图数据
        """
        dates = market_data.get("dates", [])
        prices = market_data.get("prices", {})

        if center_symbol not in prices:
            return {"data": [], "layout": {}}

        center_prices = prices[center_symbol]

        traces = []

        # 中心币种
        traces.append({
            "x": list(range(len(center_prices))),
            "y": [0] * len(center_prices),
            "z": center_prices,
            "mode": "lines",
            "name": center_symbol,
            "line": {"width": 5, "color": "#FFD700"},
            "type": "scatter3d"
        })

        # 其他币种围绕中心
        other_symbols = [s for s in prices.keys() if s != center_symbol]

        for i, symbol in enumerate(other_symbols):
            symbol_prices = prices[symbol]

            # 计算偏移（圆形排列）
            angle = (i / len(other_symbols)) * 2 * 3.14159
            radius = 5

            x_offset = radius * np.cos(angle)
            y_offset = radius * np.sin(angle)

            traces.append({
                "x": [p + x_offset for p in range(len(symbol_prices))],
                "y": [y_offset] * len(symbol_prices),
                "z": symbol_prices,
                "mode": "lines",
                "name": symbol,
                "line": {"width": 2},
                "type": "scatter3d"
            })

        layout = {
            "title": "3D Ripple Chart: Market Correlations",
            "scene": {
                "xaxis": {"title": "Time"},
                "yaxis": {"title": "Correlation Space"},
                "zaxis": {"title": "Price ($)"}
            },
            "margin": {"l": 0, "r": 0, "b": 0, "t": 40},
            "template": "plotly_dark"
        }

        return {
            "data": traces,
            "layout": layout
        }

    def generate_portfolio_3d(
        self,
        portfolio_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成3D投资组合图

        Args:
            portfolio_data: 投资组合数据
                - holdings: 持仓字典 {"BTC": 0.5, "ETH": 0.3}
                - prices: 价格字典 {"BTC": 50000, "ETH": 3000}
                - profits: 收益字典 {"BTC": 1000, "ETH": 500}

        Returns:
            Plotly 3D投资组合图数据
        """
        holdings = portfolio_data.get("holdings", {})
        prices = portfolio_data.get("prices", {})
        profits = portfolio_data.get("profits", {})

        traces = []

        symbols = list(holdings.keys())

        for symbol in symbols:
            traces.append({
                "x": [prices.get(symbol, 0)],
                "y": [holdings.get(symbol, 0)],
                "z": [profits.get(symbol, 0)],
                "mode": "markers",
                "name": symbol,
                "marker": {
                    "size": 20,
                    "color": list(range(len(symbols))),
                    "colorscale": "Viridis",
                    "opacity": 0.8
                },
                "text": [f"{symbol}<br>Price: ${prices.get(symbol, 0):.2f}<br>Holding: {holdings.get(symbol, 0):.2%}<br>Profit: ${profits.get(symbol, 0):.2f}"],
                "type": "scatter3d"
            })

        layout = {
            "title": "3D Portfolio Analysis",
            "scene": {
                "xaxis": {"title": "Price ($)"},
                "yaxis": {"title": "Holding (%)"},
                "zaxis": {"title": "Profit ($)"}
            },
            "margin": {"l": 0, "r": 0, "b": 0, "t": 40},
            "template": "plotly_dark"
        }

        return {
            "data": traces,
            "layout": layout
        }


def create_market_3d_visualizer() -> Market3DVisualizer:
    """工厂函数：创建3D市场可视化生成器

    Returns:
        Market3DVisualizer实例
    """
    return Market3DVisualizer()
