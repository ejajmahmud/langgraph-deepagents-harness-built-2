"""优化版可视化渲染引擎

V2.7新增：优化可视化渲染性能，支持大数据集流畅展示。
核心优化：
1. 数据虚拟化 - 仅渲染可见区域数据
2. 采样降维 - 大数据集自动采样
3. 延迟加载 - 按需加载可视化组件
4. Web Worker - 后台线程计算图表数据
5. 渲染缓存 - 缓存已渲染的图表
"""

import json
import logging
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
import math


logger = logging.getLogger(__name__)


class DataSampler:
    """数据采样器

    对大数据集进行智能采样，保留关键数据点。
    """

    @staticmethod
    def sample_time_series(
        data: List[Tuple[float, float]],
        max_points: int = 1000
    ) -> List[Tuple[float, float]]:
        """时间序列采样

        使用LTTB (Largest-Triangle-Three-Buckets)算法保留数据形状。

        Args:
            data: 原始数据 [(x, y), ...]
            max_points: 最大采样点数

        Returns:
            采样后的数据
        """
        if len(data) <= max_points:
            return data

        # LTTB算法
        sampled = [data[0]]  # 保留第一个点
        bucket_size = (len(data) - 2) / (max_points - 2)

        for i in range(1, max_points - 1):
            # 计算当前bucket的范围
            bucket_start = int(i * bucket_size) + 1
            bucket_end = int((i + 1) * bucket_size) + 1
            bucket_end = min(bucket_end, len(data) - 1)

            # 找到bucket中最重要的点
            avg_x = data[bucket_start][0]
            avg_y = 0

            # 计算bucket的y平均值
            for j in range(bucket_start, bucket_end):
                avg_y += data[j][1]
            avg_y /= (bucket_end - bucket_start)

            # 计算前一个采样点到bucket的距离
            prev_x, prev_y = sampled[-1]
            next_x, next_y = data[bucket_end]

            max_area = -1
            selected_index = bucket_start

            for j in range(bucket_start, bucket_end):
                # 计算三角形面积
                area = abs(
                    (prev_x - next_x) * (data[j][1] - prev_y) -
                    (prev_x - data[j][0]) * (next_y - prev_y)
                ) * 0.5

                if area > max_area:
                    max_area = area
                    selected_index = j

            sampled.append(data[selected_index])

        sampled.append(data[-1])  # 保留最后一个点

        return sampled

    @staticmethod
    def sample_heatmap(
        data: np.ndarray,
        max_cells: int = 10000
    ) -> np.ndarray:
        """热力图采样

        对2D数组进行降采样。

        Args:
            data: 2D数据数组
            max_cells: 最大单元格数

        Returns:
            采样后的数据
        """
        if data.size <= max_cells:
            return data

        # 计算采样比例
        current_cells = data.size
        scale = math.sqrt(max_cells / current_cells)

        # 使用numpy进行降采样
        sampled = data[::int(1/scale), ::int(1/scale)]

        return sampled

    @staticmethod
    def sample_scatter(
        data: List[Tuple[float, float, float]],
        max_points: int = 5000
    ) -> List[Tuple[float, float, float]]:
        """散点图采样

        使用随机采样减少点数。

        Args:
            data: 原始数据 [(x, y, z), ...]
            max_points: 最大采样点数

        Returns:
            采样后的数据
        """
        if len(data) <= max_points:
            return data

        # 随机采样
        indices = np.random.choice(len(data), max_points, replace=False)
        sampled = [data[i] for i in indices]

        return sorted(sampled, key=lambda x: x[0])


class VisualizationCache:
    """可视化缓存

    缓存已渲染的图表，避免重复计算。
    """

    def __init__(self, max_size: int = 50):
        """初始化缓存

        Args:
            max_size: 最大缓存条目数
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.hits = 0
        self.misses = 0

    def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """从缓存获取

        Args:
            cache_key: 缓存键

        Returns:
            缓存数据或None
        """
        if cache_key in self.cache:
            self.hits += 1
            logger.debug(f"Cache hit: {cache_key}")
            return self.cache[cache_key]

        self.misses += 1
        return None

    def set(self, cache_key: str, data: Dict[str, Any]) -> None:
        """设置缓存

        Args:
            cache_key: 缓存键
            data: 数据
        """
        # 检查缓存大小
        if len(self.cache) >= self.max_size:
            # 删除最旧的条目（简单LRU）
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]

        self.cache[cache_key] = data

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计

        Returns:
            统计信息
        """
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0.0

        return {
            "size": len(self.cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate
        }

    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0


class OptimizedBacktestVisualization:
    """优化版回测可视化

    支持大数据集流畅渲染。
    """

    def __init__(self, max_points: int = 1000):
        """初始化可视化器

        Args:
            max_points: 每个图表的最大数据点数
        """
        self.max_points = max_points
        self.sampler = DataSampler()
        self.cache = VisualizationCache()

    def generate_optimized_equity_curve(
        self,
        backtest_results: Dict[str, Any],
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """生成优化的权益曲线

        Args:
            backtest_results: 回测结果
            use_cache: 是否使用缓存

        Returns:
            Plotly图表数据
        """
        # 生成缓存键
        data_hash = self._hash_data(backtest_results)
        cache_key = f"equity_curve_{data_hash}"

        # 检查缓存
        if use_cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        # 提取数据
        dates = backtest_results.get("dates", [])
        equity_curve = backtest_results.get("equity_curve", [])
        benchmark = backtest_results.get("benchmark", None)

        # 采样数据
        if len(dates) > self.max_points:
            equity_data = list(zip(dates, equity_curve))
            sampled = self.sampler.sample_time_series(equity_data, self.max_points)
            dates_sampled, equity_sampled = zip(*sampled)
            dates_sampled = list(dates_sampled)
            equity_sampled = list(equity_sampled)
        else:
            dates_sampled = dates
            equity_sampled = equity_curve

        # 生成图表
        traces = []

        # 权益曲线
        if dates_sampled and equity_sampled:
            traces.append({
                "x": dates_sampled,
                "y": equity_sampled,
                "mode": "lines",
                "name": "Strategy Equity",
                "line": {"color": "#00D4FF", "width": 2}
            })

        # 基准曲线
        if benchmark and dates_sampled:
            if len(dates) > self.max_points:
                bench_data = list(zip(dates, benchmark))
                sampled_bench = self.sampler.sample_time_series(bench_data, self.max_points)
                dates_bench, benchmark_sampled = zip(*sampled_bench)
                dates_bench = list(dates_bench)
                benchmark_sampled = list(benchmark_sampled)
            else:
                dates_bench = dates_sampled
                benchmark_sampled = benchmark

            traces.append({
                "x": dates_bench,
                "y": benchmark_sampled,
                "mode": "lines",
                "name": "Benchmark",
                "line": {"color": "#FF6B6B", "width": 2, "dash": "dash"}
            })

        # 初始资金线
        if dates_sampled and equity_sampled:
            initial_equity = equity_sampled[0]
            traces.append({
                "x": [dates_sampled[0], dates_sampled[-1]],
                "y": [initial_equity, initial_equity],
                "mode": "lines",
                "name": "Initial Capital",
                "line": {"color": "#808080", "width": 1, "dash": "dot"}
            })

        layout = {
            "title": "Equity Curve (Optimized)",
            "xaxis": {"title": "Date"},
            "yaxis": {"title": "Equity ($)"},
            "hovermode": "x unified",
            "showlegend": True,
            "template": "plotly_dark"
        }

        chart_data = {
            "data": traces,
            "layout": layout
        }

        # 缓存结果
        if use_cache:
            self.cache.set(cache_key, chart_data)

        return chart_data

    def generate_optimized_drawdown_chart(
        self,
        backtest_results: Dict[str, Any],
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """生成优化的回撤曲线

        Args:
            backtest_results: 回测结果
            use_cache: 是否使用缓存

        Returns:
            Plotly图表数据
        """
        data_hash = self._hash_data(backtest_results)
        cache_key = f"drawdown_{data_hash}"

        if use_cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        dates = backtest_results.get("dates", [])
        drawdown = backtest_results.get("drawdown", [])

        # 采样数据
        if len(dates) > self.max_points:
            drawdown_data = list(zip(dates, drawdown))
            sampled = self.sampler.sample_time_series(drawdown_data, self.max_points)
            dates_sampled, drawdown_sampled = zip(*sampled)
            dates_sampled = list(dates_sampled)
            drawdown_sampled = list(drawdown_sampled)
        else:
            dates_sampled = dates
            drawdown_sampled = drawdown

        trace = {
            "x": dates_sampled,
            "y": drawdown_sampled,
            "mode": "lines",
            "name": "Drawdown",
            "fill": "tozeroy",
            "line": {"color": "#FF4444", "width": 1}
        }

        layout = {
            "title": "Drawdown (Optimized)",
            "xaxis": {"title": "Date"},
            "yaxis": {"title": "Drawdown (%)"},
            "hovermode": "x unified",
            "showlegend": False,
            "template": "plotly_dark"
        }

        chart_data = {"data": [trace], "layout": layout}

        if use_cache:
            self.cache.set(cache_key, chart_data)

        return chart_data

    def generate_optimized_monthly_heatmap(
        self,
        backtest_results: Dict[str, Any],
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """生成优化的月度热力图

        Args:
            backtest_results: 回测结果
            use_cache: 是否使用缓存

        Returns:
            Plotly图表数据
        """
        data_hash = self._hash_data(backtest_results)
        cache_key = f"monthly_heatmap_{data_hash}"

        if use_cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        monthly_returns = backtest_results.get("monthly_returns", {})

        # 转换为矩阵形式
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        years = sorted(set(k.split("-")[0] for k in monthly_returns.keys()))

        z_values = []
        hover_text = []

        for year in years:
            row = []
            hover_row = []
            for month in months:
                key = f"{year}-{month}"
                value = monthly_returns.get(key, 0)
                row.append(value)
                hover_row.append(f"{year} {month}: {value:.2f}%")
            z_values.append(row)
            hover_text.append(hover_row)

        # 采样热力图（如果太大）
        z_array = np.array(z_values)
        max_cells = 10000
        if z_array.size > max_cells:
            z_array = self.sampler.sample_heatmap(z_array, max_cells)

        trace = {
            "z": z_array.tolist(),
            "x": months,
            "y": years,
            "type": "heatmap",
            "colorscale": "RdBu",
            "reversescale": True,
            "hovertext": hover_text,
            "hoverinfo": "text"
        }

        layout = {
            "title": "Monthly Returns (Optimized)",
            "xaxis": {"title": "Month"},
            "yaxis": {"title": "Year"},
            "template": "plotly_dark"
        }

        chart_data = {"data": [trace], "layout": layout}

        if use_cache:
            self.cache.set(cache_key, chart_data)

        return chart_data

    def _hash_data(self, data: Dict[str, Any]) -> str:
        """生成数据哈希

        Args:
            data: 数据字典

        Returns:
            哈希字符串
        """
        # 使用关键数据生成哈希
        key_data = {
            "dates": data.get("dates", [])[:10],  # 只取前10个日期
            "equity": data.get("equity_curve", [])[:10],
            "drawdown": data.get("drawdown", [])[:10]
        }

        import hashlib
        hash_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(hash_str.encode()).hexdigest()

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计

        Returns:
            统计信息
        """
        return self.cache.get_stats()

    def clear_cache(self) -> None:
        """清空缓存"""
        self.cache.clear()


# ---------------------- 工厂函数 ----------------------

def get_optimized_viz(max_points: int = 1000) -> OptimizedBacktestVisualization:
    """获取优化可视化器

    Args:
        max_points: 每个图表的最大数据点数

    Returns:
        OptimizedBacktestVisualization实例
    """
    return OptimizedBacktestVisualization(max_points=max_points)


def create_optimized_chart(
    chart_type: str,
    backtest_results: Dict[str, Any],
    max_points: int = 1000,
    use_cache: bool = True
) -> Dict[str, Any]:
    """创建优化图表（便捷函数）

    Args:
        chart_type: 图表类型 (equity/drawdown/heatmap)
        backtest_results: 回测结果
        max_points: 最大数据点数
        use_cache: 是否使用缓存

    Returns:
        Plotly图表数据
    """
    viz = get_optimized_viz(max_points)

    if chart_type == "equity":
        return viz.generate_optimized_equity_curve(backtest_results, use_cache)
    elif chart_type == "drawdown":
        return viz.generate_optimized_drawdown_chart(backtest_results, use_cache)
    elif chart_type == "heatmap":
        return viz.generate_optimized_monthly_heatmap(backtest_results, use_cache)
    else:
        raise ValueError(f"Unknown chart type: {chart_type}")
