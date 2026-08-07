// 仪表板 JavaScript V3.3

// API 基础 URL
const API_BASE_URL = 'http://localhost:8000/api/v3.3/monitoring';

// WebSocket 连接
let ws = null;
let reconnectInterval = null;

// 图表实例
let profitChart = null;
let riskChart = null;
let performanceChart = null;

// 当前数据
let currentData = {
    overview: null,
    risk: null,
    trade: null,
    strategy: null,
    performance: null
};

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initialized');
    initializeNavigation();
    initializeWebSocket();
    initializeCharts();
    loadInitialData();
    setupEventListeners();
    startDataRefresh();
});

// 导航初始化
function initializeNavigation() {
    const navItems = document.querySelectorAll('.nav-item');

    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();

            // 更新导航状态
            navItems.forEach(nav => nav.classList.remove('active'));
            this.classList.add('active');

            // 显示对应页面
            const pageId = this.getAttribute('data-page');
            document.querySelectorAll('.page').forEach(page => {
                page.classList.remove('active');
                if (page.id === pageId) {
                    page.classList.add('active');
                }
            });

            // 加载页面数据
            loadPageData(pageId);
        });
    });
}

// WebSocket 初始化
function initializeWebSocket() {
    connectWebSocket();

    // 定期检查连接状态
    setInterval(checkWebSocketConnection, 10000);
}

function connectWebSocket() {
    try {
        ws = new WebSocket('ws://localhost:8000/api/v3.3/monitoring/ws');

        ws.onopen = function() {
            console.log('WebSocket connected');
            showToast('WebSocket connected', 'success');

            // 清除重连定时器
            if (reconnectInterval) {
                clearInterval(reconnectInterval);
                reconnectInterval = null;
            }
        };

        ws.onmessage = function(event) {
            try {
                const message = JSON.parse(event.data);
                handleWebSocketMessage(message);
            } catch (e) {
                console.error('Error parsing WebSocket message:', e);
            }
        };

        ws.onerror = function(error) {
            console.error('WebSocket error:', error);
            showToast('WebSocket error', 'error');
        };

        ws.onclose = function() {
            console.log('WebSocket disconnected');
            showToast('WebSocket disconnected', 'warning');

            // 5秒后重连
            if (!reconnectInterval) {
                reconnectInterval = setInterval(connectWebSocket, 5000);
            }
        };
    } catch (e) {
        console.error('Error creating WebSocket:', e);
        showToast('WebSocket connection failed', 'error');
    }
}

function checkWebSocketConnection() {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        console.warn('WebSocket not connected, attempting to reconnect...');
        if (!reconnectInterval) {
            connectWebSocket();
        }
    }
}

function handleWebSocketMessage(message) {
    console.log('Received WebSocket message:', message);

    if (message.type === 'initial' || message.type === 'update') {
        if (message.data) {
            updateDashboard(message.data);
        }
    } else if (message.type === 'heartbeat') {
        console.log('Heartbeat received');
    }
}

// 图表初始化
function initializeCharts() {
    // 收益曲线
    const profitCtx = document.getElementById('profit-chart').getContext('2d');
    profitChart = new Chart(profitCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: '累计盈亏',
                data: [],
                borderColor: 'rgb(37, 99, 235)',
                backgroundColor: 'rgba(37, 99, 235, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    display: false
                },
                y: {
                    beginAtZero: false
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });

    // 风险趋势
    const riskCtx = document.getElementById('risk-chart').getContext('2d');
    riskChart = new Chart(riskCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: '敞口风险',
                    data: [],
                    borderColor: 'rgb(239, 68, 68)',
                    tension: 0.4
                },
                {
                    label: '波动率风险',
                    data: [],
                    borderColor: 'rgb(245, 158, 11)',
                    tension: 0.4
                },
                {
                    label: '回撤风险',
                    data: [],
                    borderColor: 'rgb(37, 99, 235)',
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    display: false
                },
                y: {
                    beginAtZero: true,
                    max: 100
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            }
        }
    });

    // 性能趋势
    const perfCtx = document.getElementById('performance-chart').getContext('2d');
    performanceChart = new Chart(perfCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'CPU 使用率',
                    data: [],
                    borderColor: 'rgb(37, 99, 235)',
                    tension: 0.4
                },
                {
                    label: '内存使用率',
                    data: [],
                    borderColor: 'rgb(16, 185, 129)',
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    display: false
                },
                y: {
                    beginAtZero: true,
                    max: 100
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            }
        }
    });
}

// 加载初始数据
async function loadInitialData() {
    try {
        await Promise.all([
            loadOverviewData(),
            loadRiskData(),
            loadTradeData(),
            loadStrategyData(),
            loadPerformanceData()
        ]);
        showToast('Initial data loaded', 'success');
    } catch (e) {
        console.error('Error loading initial data:', e);
        showToast('Failed to load initial data', 'error');
    }
}

// 加载页面数据
function loadPageData(pageId) {
    switch(pageId) {
        case 'overview':
            loadOverviewData();
            break;
        case 'risk':
            loadRiskData();
            break;
        case 'trade':
            loadTradeData();
            break;
        case 'strategy':
            loadStrategyData();
            break;
        case 'performance':
            loadPerformanceData();
            break;
        case 'alerts':
            loadAlertsData();
            break;
    }
}

// API 调用函数
async function fetchAPI(endpoint) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Error fetching ${endpoint}:`, error);
        throw error;
    }
}

// 加载总览数据
async function loadOverviewData() {
    try {
        const data = await fetchAPI('/overview');
        currentData.overview = data;
        updateOverviewDisplay(data);
    } catch (e) {
        console.error('Error loading overview data:', e);
    }
}

// 更新总览显示
function updateOverviewDisplay(data) {
    if (!data) return;

    // 更新系统信息
    if (data.uptime) {
        const uptime = formatUptime(data.uptime);
        document.getElementById('uptime').textContent = uptime;
    }

    if (data.system_status) {
        document.getElementById('last-update').textContent =
            data.system_status.last_update || '--';
    }

    // 更新交易统计
    if (data.trade_stats) {
        const stats = data.trade_stats;
        document.getElementById('total-trades').textContent = stats.total_trades || 0;
        document.getElementById('trade-rate').textContent =
            `胜率 ${stats.win_rate?.toFixed(2) || 0}%`;
    }

    // 更新风险等级
    if (data.risk_metrics) {
        document.getElementById('risk-level').textContent =
            data.risk_metrics.risk_level || 'LOW';
    }

    // 更新盈亏
    if (data.trade_stats) {
        const profit = data.trade_stats.total_profit - data.trade_stats.total_loss;
        document.getElementById('total-profit-loss').textContent =
            `$${profit.toFixed(2)}`;
    }
}

// 加载风险数据
async function loadRiskData() {
    try {
        const data = await fetchAPI('/risk');
        currentData.risk = data;
        updateRiskDisplay(data);
    } catch (e) {
        console.error('Error loading risk data:', e);
    }
}

// 更新风险显示
function updateRiskDisplay(data) {
    if (!data || !data.current_metrics) return;

    const metrics = data.current_metrics;

    // 更新风险指标
    updateRiskBar('exposure', metrics.exposure, 10000);
    updateRiskBar('volatility', metrics.volatility * 100, 100);
    updateRiskBar('liquidity', metrics.liquidity_score * 100, 100, true);
    updateRiskBar('drawdown', metrics.drawdown * 100, 100);
    updateRiskBar('correlation', metrics.correlation_risk * 100, 100);
    updateRiskBar('concentration', metrics.concentration_risk * 100, 100);

    // 更新风险等级
    const riskLevel = metrics.risk_level || 'LOW';
    document.getElementById('risk-level').textContent = riskLevel;
}

function updateRiskBar(id, value, max, inverted = false) {
    const bar = document.getElementById(`${id}-bar`);
    const valueEl = document.getElementById(`${id}-value`);

    if (bar && valueEl) {
        const percentage = Math.min((value / max) * 100, 100);
        bar.style.width = `${percentage}%`;

        // 设置颜色
        bar.classList.remove('warning', 'danger');
        if (percentage > 80) {
            bar.classList.add('danger');
        } else if (percentage > 60) {
            bar.classList.add('warning');
        }

        valueEl.textContent = `${value.toFixed(2)}%`;
    }
}

// 加载交易数据
async function loadTradeData() {
    try {
        const data = await fetchAPI('/trade');
        currentData.trade = data;
        updateTradeDisplay(data);
    } catch (e) {
        console.error('Error loading trade data:', e);
    }
}

// 更新交易显示
function updateTradeDisplay(data) {
    if (!data) return;

    // 更新交易统计
    if (data.trade_stats) {
        const stats = data.trade_stats;
        document.getElementById('stat-total-trades').textContent = stats.total_trades || 0;
        document.getElementById('stat-success-trades').textContent = stats.successful_trades || 0;
        document.getElementById('stat-failed-trades').textContent = stats.failed_trades || 0;
        document.getElementById('stat-win-rate').textContent = `${stats.win_rate?.toFixed(2) || 0}%`;
        document.getElementById('stat-total-profit').textContent = `$${stats.total_profit?.toFixed(2) || 0}`;
        document.getElementById('stat-total-loss').textContent = `$${stats.total_loss?.toFixed(2) || 0}`;
    }

    // 更新交易历史表格
    if (data.trade_history && data.trade_history.length > 0) {
        updateTradeTable(data.trade_history);
    }
}

function updateTradeTable(trades) {
    const tbody = document.getElementById('trade-table-body');
    if (!tbody) return;

    tbody.innerHTML = '';

    trades.slice(0, 10).forEach(trade => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${formatTimestamp(trade.timestamp)}</td>
            <td>${trade.strategy || '-'}</td>
            <td>${trade.symbol || '-'}</td>
            <td class="${trade.success ? 'status-success' : 'status-failed'}">
                ${trade.success ? '成功' : '失败'}
            </td>
            <td class="${trade.profit >= 0 ? 'status-success' : 'status-failed'}">
                $${(trade.profit || 0).toFixed(2)}
            </td>
            <td>${trade.execution_time || '-'}</td>
            <td>${trade.risk_level || '-'}</td>
        `;
        tbody.appendChild(row);
    });
}

// 加载策略数据
async function loadStrategyData() {
    try {
        const data = await fetchAPI('/strategy');
        currentData.strategy = data;
        updateStrategyDisplay(data);
    } catch (e) {
        console.error('Error loading strategy data:', e);
    }
}

// 更新策略显示
function updateStrategyDisplay(data) {
    if (!data) return;

    const container = document.getElementById('strategy-cards');
    if (!container) return;

    container.innerHTML = '';

    if (data.strategy_performance) {
        Object.entries(data.strategy_performance).forEach(([name, perf]) => {
            const card = document.createElement('div');
            card.className = 'strategy-card';
            card.innerHTML = `
                <h3>${name}</h3>
                <div class="strategy-stats">
                    <div class="strategy-stat">
                        <div class="strategy-stat-label">执行次数</div>
                        <div class="strategy-stat-value">${perf.executions}</div>
                    </div>
                    <div class="strategy-stat">
                        <div class="strategy-stat-label">成功率</div>
                        <div class="strategy-stat-value">${perf.success_rate.toFixed(2)}%</div>
                    </div>
                    <div class="strategy-stat">
                        <div class="strategy-stat-label">总盈亏</div>
                        <div class="strategy-stat-value ${perf.total_profit >= 0 ? 'status-success' : 'status-failed'}">
                            $${perf.total_profit.toFixed(2)}
                        </div>
                    </div>
                    <div class="strategy-stat">
                        <div class="strategy-stat-label">平均盈利</div>
                        <div class="strategy-stat-value">$${perf.avg_profit.toFixed(2)}</div>
                    </div>
                </div>
            `;
            container.appendChild(card);
        });
    }
}

// 加载性能数据
async function loadPerformanceData() {
    try {
        const data = await fetchAPI('/performance');
        currentData.performance = data;
        updatePerformanceDisplay(data);
    } catch (e) {
        console.error('Error loading performance data:', e);
    }
}

// 更新性能显示
function updatePerformanceDisplay(data) {
    if (!data || !data.current_metrics) return;

    const metrics = data.current_metrics;

    // 更新性能指标
    updatePerfBar('cpu', metrics.cpu_usage, 100);
    updatePerfBar('memory', metrics.memory_usage, 100);
    updatePerfBar('disk', metrics.disk_usage, 100);
    updatePerfBar('api-latency', metrics.api_latency, 1000);
    updatePerfBar('processing-time', metrics.processing_time, 1000);
}

function updatePerfBar(id, value, max) {
    const bar = document.getElementById(`${id}-bar`);
    const valueEl = document.getElementById(`${id}-value`);

    if (bar && valueEl) {
        const percentage = Math.min((value / max) * 100, 100);
        bar.style.width = `${percentage}%`;
        valueEl.textContent = id.includes('latency') || id.includes('time') ?
            `${value.toFixed(0)}ms` : `${value.toFixed(0)}%`;
    }
}

// 加载告警数据
async function loadAlertsData() {
    try {
        const data = await fetchAPI('/risk');
        if (data && data.alerts) {
            updateAlertsDisplay(data.alerts);
        }
    } catch (e) {
        console.error('Error loading alerts data:', e);
    }
}

// 更新告警显示
function updateAlertsDisplay(alerts) {
    const tbody = document.getElementById('alerts-table-body');
    if (!tbody) return;

    tbody.innerHTML = '';

    // 更新统计
    let critical = 0, warning = 0, info = 0;
    alerts.forEach(alert => {
        if (alert.severity === 'critical') critical++;
        else if (alert.severity === 'warning') warning++;
        else info++;
    });

    document.getElementById('critical-count').textContent = critical;
    document.getElementById('warning-count').textContent = warning;
    document.getElementById('info-count').textContent = info;

    // 更新表格
    alerts.slice(0, 10).forEach(alert => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${formatTimestamp(alert.timestamp)}</td>
            <td class="status-${alert.severity}">${alert.severity.toUpperCase()}</td>
            <td>${alert.category || '-'}</td>
            <td>${alert.message || '-'}</td>
            <td>
                <button class="btn btn-secondary" onclick="dismissAlert('${alert.id}')">消除</button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// 更新仪表板
function updateDashboard(data) {
    updateOverviewDisplay(data);
    updateRiskDisplay(data);
    updateTradeDisplay(data);
    updateStrategyDisplay(data);
    updatePerformanceDisplay(data);
}

// 设置事件监听器
function setupEventListeners() {
    document.getElementById('refresh-btn').addEventListener('click', loadInitialData);
    document.getElementById('export-btn').addEventListener('click', exportData);
    document.getElementById('clear-alerts-btn').addEventListener('click', clearAlerts);
}

// 开始数据刷新
function startDataRefresh() {
    setInterval(loadOverviewData, 5000);  // 每5秒刷新总览
    setInterval(loadRiskData, 5000);      // 每5秒刷新风险
    setInterval(loadPerformanceData, 5000);  // 每5秒刷新性能
}

// 导出数据
async function exportData() {
    try {
        const data = await fetchAPI('/export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ data_type: 'overview', format: 'json' })
        });

        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `dashboard_export_${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);

        showToast('Data exported successfully', 'success');
    } catch (e) {
        console.error('Error exporting data:', e);
        showToast('Failed to export data', 'error');
    }
}

// 清除告警
function clearAlerts() {
    // TODO: 实现清除告警逻辑
    showToast('Alerts cleared', 'success');
}

// 显示 Toast 通知
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    container.appendChild(toast);

    // 3秒后自动消失
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// 格式化运行时间
function formatUptime(seconds) {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (days > 0) {
        return `${days}d ${hours}h ${minutes}m`;
    } else if (hours > 0) {
        return `${hours}h ${minutes}m`;
    } else {
        return `${minutes}m`;
    }
}

// 格式化时间戳
function formatTimestamp(timestamp) {
    if (!timestamp) return '-';

    try {
        const date = new Date(timestamp);
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    } catch (e) {
        return timestamp;
    }
}

// 消除告警
function dismissAlert(alertId) {
    // TODO: 实现消除告警逻辑
    showToast(`Alert ${alertId} dismissed`, 'success');
}
