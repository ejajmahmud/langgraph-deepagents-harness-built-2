import { useState } from 'react'
import { Card, Table, Tag, Input, DatePicker, Button, Space, Modal } from 'antd'
import { SearchOutlined, ExportOutlined } from '@ant-design/icons'
import { useAppStore } from '@/store'
import { Trade } from '@/types'
import dayjs from 'dayjs'

const TradeHistory: React.FC = () => {
  const { trades, fetchTrades } = useAppStore()
  const [filteredTrades, setFilteredTrades] = useState<Trade[]>(trades)
  const [searchText, setSearchText] = useState('')
  const [selectedTrade, setSelectedTrade] = useState<Trade | null>(null)
  const [detailModalVisible, setDetailModalVisible] = useState(false)

  // 搜索和过滤
  const handleSearch = (value: string) => {
    setSearchText(value)

    if (!value) {
      setFilteredTrades(trades)
      return
    }

    const filtered = trades.filter(
      (trade) =>
        trade.id.toLowerCase().includes(value.toLowerCase()) ||
        trade.strategy.toLowerCase().includes(value.toLowerCase()) ||
        trade.symbol.toLowerCase().includes(value.toLowerCase())
    )

    setFilteredTrades(filtered)
  }

  // 查看交易详情
  const handleViewDetail = (trade: Trade) => {
    setSelectedTrade(trade)
    setDetailModalVisible(true)
  }

  // 导出交易历史
  const handleExport = async () => {
    // TODO: 调用API导出CSV
    console.log('Export trades')
  }

  const columns = [
    {
      title: '交易ID',
      dataIndex: 'id',
      key: 'id',
      width: 150,
      sorter: (a: Trade, b: Trade) => a.id.localeCompare(b.id),
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
      title: '预期利润',
      dataIndex: 'expected_profit',
      key: 'expected_profit',
      width: 100,
      render: (profit: number) => `$${profit.toFixed(2)}`,
    },
    {
      title: '实际利润',
      dataIndex: 'actual_profit',
      key: 'actual_profit',
      width: 100,
      render: (profit: number) => (
        <span style={{ color: profit >= 0 ? '#52c41a' : '#ff4d4f' }}>
          ${profit.toFixed(2)}
        </span>
      ),
      sorter: (a: Trade, b: Trade) => a.actual_profit - b.actual_profit,
    },
    {
      title: '收益率',
      dataIndex: 'actual_profit_rate',
      key: 'actual_profit_rate',
      width: 100,
      render: (rate: number) => `${rate.toFixed(3)}%`,
      sorter: (a: Trade, b: Trade) => a.actual_profit_rate - b.actual_profit_rate,
    },
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 150,
      render: (timestamp: number) => dayjs(timestamp * 1000).format('YYYY-MM-DD HH:mm:ss'),
      sorter: (a: Trade, b: Trade) => a.timestamp - b.timestamp,
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: any, record: Trade) => (
        <Button type="link" onClick={() => handleViewDetail(record)}>
          详情
        </Button>
      ),
    },
  ]

  return (
    <div className="trade-history">
      <div className="page-header">
        <h2 className="page-title">交易历史</h2>
        <Button icon={<ExportOutlined />} onClick={handleExport}>
          导出CSV
        </Button>
      </div>

      <Card>
        <div className="search-bar">
          <Input
            placeholder="搜索交易ID、策略或交易对..."
            prefix={<SearchOutlined />}
            value={searchText}
            onChange={(e) => handleSearch(e.target.value)}
            style={{ width: 300 }}
            allowClear
          />
        </div>

        <Table
          columns={columns}
          dataSource={filteredTrades.length > 0 ? filteredTrades : trades}
          rowKey="id"
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条记录`,
          }}
        />
      </Card>

      {/* 交易详情模态框 */}
      <Modal
        title="交易详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={800}
      >
        {selectedTrade && (
          <div className="trade-detail">
            <div className="detail-row">
              <span className="label">交易ID:</span>
              <span className="value">{selectedTrade.id}</span>
            </div>
            <div className="detail-row">
              <span className="label">策略:</span>
              <span className="value">{selectedTrade.strategy}</span>
            </div>
            <div className="detail-row">
              <span className="label">交易对:</span>
              <span className="value">{selectedTrade.symbol}</span>
            </div>
            <div className="detail-row">
              <span className="label">状态:</span>
              <span className="value">
                <Tag color={
                  selectedTrade.status === 'completed' ? 'success' :
                  selectedTrade.status === 'failed' ? 'error' : 'default'
                }>
                  {selectedTrade.status}
                </Tag>
              </span>
            </div>
            <div className="detail-row">
              <span className="label">预期利润:</span>
              <span className="value">${selectedTrade.expected_profit.toFixed(2)}</span>
            </div>
            <div className="detail-row">
              <span className="label">实际利润:</span>
              <span className="value" style={{ color: selectedTrade.actual_profit >= 0 ? '#52c41a' : '#ff4d4f' }}>
                ${selectedTrade.actual_profit.toFixed(2)}
              </span>
            </div>
            <div className="detail-row">
              <span className="label">收益率:</span>
              <span className="value">{selectedTrade.actual_profit_rate.toFixed(3)}%</span>
            </div>
            <div className="detail-row">
              <span className="label">时间:</span>
              <span className="value">
                {dayjs(selectedTrade.timestamp * 1000).format('YYYY-MM-DD HH:mm:ss')}
              </span>
            </div>
            {selectedTrade.error && (
              <div className="detail-row">
                <span className="label">错误信息:</span>
                <span className="value error">{selectedTrade.error}</span>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}

export default TradeHistory
