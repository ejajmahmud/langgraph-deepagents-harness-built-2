import { useEffect } from 'react'
import { Row, Col, Card, Statistic, Progress, Table, Tag, Space } from 'antd'
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  DollarOutlined,
  ThunderboltOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons'
import { useAppStore } from '@/store'
import './Dashboard.css'

const Dashboard: React.FC = () => {
  const {
    systemStatus,
    strategies,
    trades,
    totalProfit,
    winRate,
    totalTrades,
    v55Signals,
    v55Positions,
    exchangeStatus,
    fetchSystemStatus,
    fetchStrategies,
    fetchTrades,
    fetchV55Signals,
    fetchV55Positions,
    fetchExchangeStatus,
  } = useAppStore()

  useEffect(() => {
    // 初始化加载数据
    fetchSystemStatus()
    fetchStrategies()
    fetchTrades()
    // V56.2新增：加载V55套利数据
    fetchV55Signals()
    fetchV55Positions()
    fetchExchangeStatus()

    // 定期刷新数据
    const interval = setInterval(() => {
      fetchSystemStatus()
      fetchTrades()
      fetchV55Signals()
      fetchV55Positions()
    }, 15000) // 15秒

    return () => clearInterval(interval)
  }, [fetchSystemStatus, fetchStrategies, fetchTrades, fetchV55Signals, fetchV55Positions, fetchExchangeStatus])

  // 计算活跃策略数
  const activeStrategies = strategies.filter((s) => s.enabled && s.state === 'running').length

  // 计算运行时间
  const uptimeHours = systemStatus?.uptime_hours || 0

  // V56.2新增：计算V55状态
  const activeSignals = v55Signals.filter((s) => s.confidence > 0.5).length
  const totalPositionValue = v55Positions.reduce(
    (sum, p) => sum + p.size * p.current_price,
    0
  )
  const totalUnrealizedPnl = v55Positions.reduce(
    (sum, p) => sum + p.unrealized_pnl,
    0
  )

  // 最近交易
  const recentTrades = trades.slice(0, 5)

  const tradeColumns = [
    {
      title: '交易ID',
      dataIndex: 'id',
      key: 'id',
      width: 150,
    },
    {
      title: '策略',
      dataIndex: 'strategy',
      key: 'strategy',
      width: 120,
    },
    {
      title: '交易对',
      dataIndex: 'symbol',
      key: 'symbol',
      width: 100,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status: string) => {
        const statusMap: Record<string, { text: string; color: string }> = {
          completed: { text: '完成', color: 'success' },
          failed: { text: '失败', color: 'error' },
          rejected: { text: '拒绝', color: 'default' },
        }
        const { text, color } = statusMap[status] || { text: status, color: 'default' }
        return <Tag color={color}>{text}</Tag>
      },
    },
    {
      title: '利润',
      dataIndex: 'actual_profit',
      key: 'actual_profit',
      width: 100,
      render: (profit: number) => (
        <span style={{ color: profit >= 0 ? '#52c41a' : '#ff4d4f' }}>
          {profit >= 0 ? '+' : ''}${profit.toFixed(2)}
        </span>
      ),
    },
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 150,
      render: (timestamp: number) => new Date(timestamp * 1000).toLocaleString('zh-CN'),
    },
  ]

  return (
    <div className="dashboard">
      <h2 className="page-title">仪表盘</h2>

      <Row gutter={[16, 16]} className="stats-row">
        {/* 总利润 */}
        <Col xs={24} sm={12} md={8} lg={6}>
          <Card>
            <Statistic
              title="总利润"
              value={totalProfit}
              precision={2}
              prefix={<DollarOutlined />}
              valueStyle={{
                color: totalProfit >= 0 ? '#3f8600' : '#cf1322',
              }}
              suffix="$"
            />
            <div className="stat-footer">
              {totalProfit >= 0 ? (
                <span className="profit-positive">
                  <ArrowUpOutlined />
                  {' '}
                  {((totalProfit / (totalTrades || 1)) * 100).toFixed(2)}%
                </span>
              ) : (
                <span className="profit-negative">
                  <ArrowDownOutlined />
                  {' '}
                  {((Math.abs(totalProfit) / (totalTrades || 1)) * 100).toFixed(2)}%
                </span>
              )}
            </div>
          </Card>
        </Col>

        {/* 胜率 */}
        <Col xs={24} sm={12} md={8} lg={6}>
          <Card>
            <Statistic
              title="胜率"
              value={winRate}
              precision={2}
              prefix={<CheckCircleOutlined />}
              suffix="%"
            />
            <div className="stat-footer">
              <Progress
                percent={winRate}
                size="small"
                status={winRate >= 60 ? 'success' : 'normal'}
              />
            </div>
          </Card>
        </Col>

        {/* 总交易数 */}
        <Col xs={24} sm={12} md={8} lg={6}>
          <Card>
            <Statistic
              title="总交易数"
              value={totalTrades}
              prefix={<ThunderboltOutlined />}
            />
            <div className="stat-footer">
              <span>成功: {trades.filter((t) => t.status === 'completed').length}</span>
            </div>
          </Card>
        </Col>

        {/* 运行时间 */}
        <Col xs={24} sm={12} md={8} lg={6}>
          <Card>
            <Statistic
              title="运行时间"
              value={uptimeHours}
              precision={1}
              prefix={<ClockCircleOutlined />}
              suffix="小时"
            />
            <div className="stat-footer">
              <span>系统稳定运行中</span>
            </div>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} className="content-row">
        {/* 活跃策略 */}
        <Col xs={24} lg={12}>
          <Card title="活跃策略" className="strategy-card">
            <div className="strategy-grid">
              {strategies.map((strategy) => (
                <div
                  key={strategy.name}
                  className={`strategy-item ${strategy.enabled ? 'enabled' : 'disabled'}`}
                >
                  <div className="strategy-header">
                    <h4>{strategy.name}</h4>
                    <Tag color={strategy.enabled ? 'success' : 'default'}>
                      {strategy.enabled ? '启用' : '禁用'}
                    </Tag>
                  </div>
                  <div className="strategy-stats">
                    <div className="stat-item">
                      <span className="label">交易数:</span>
                      <span className="value">{strategy.performance.total_trades}</span>
                    </div>
                    <div className="stat-item">
                      <span className="label">利润:</span>
                      <span className="value" style={{ color: strategy.performance.total_profit >= 0 ? '#52c41a' : '#ff4d4f' }}>
                        ${strategy.performance.total_profit.toFixed(2)}
                      </span>
                    </div>
                    <div className="stat-item">
                      <span className="label">胜率:</span>
                      <span className="value">{strategy.performance.success_rate.toFixed(1)}%</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </Col>

        {/* 系统状态 */}
        <Col xs={24} lg={12}>
          <Card title="系统状态" className="status-card">
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              <div className="status-item">
                <span className="status-label">代理状态:</span>
                <span className={`status-value ${systemStatus?.agent_running ? 'running' : 'stopped'}`}>
                  {systemStatus?.agent_running ? '运行中' : '已停止'}
                </span>
              </div>
              <div className="status-item">
                <span className="status-label">策略数量:</span>
                <span className="status-value">{systemStatus?.strategies_count || 0}</span>
              </div>
              <div className="status-item">
                <span className="status-label">活跃策略:</span>
                <span className="status-value">{activeStrategies}</span>
              </div>
              <div className="status-item">
                <span className="status-label">总错误数:</span>
                <span className="status-value">{systemStatus?.total_errors || 0}</span>
              </div>
            </Space>
          </Card>
        </Col>
      </Row>

      {/* 最近交易 */}
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card title="最近交易" className="trades-card">
            <Table
              columns={tradeColumns}
              dataSource={recentTrades}
              rowKey="id"
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard
