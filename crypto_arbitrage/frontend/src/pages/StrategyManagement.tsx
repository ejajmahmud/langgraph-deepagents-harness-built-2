import { useState } from 'react'
import { Row, Col, Card, Table, Switch, Button, Tag, Modal, Form, InputNumber, Space } from 'antd'
import { EditOutlined, PlayCircleOutlined, PauseCircleOutlined } from '@ant-design/icons'
import { useAppStore } from '@/store'
import { Strategy } from '@/types'

const StrategyManagement: React.FC = () => {
  const { strategies, fetchStrategies } = useAppStore()
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null)
  const [editModalVisible, setEditModalVisible] = useState(false)
  const [form] = Form.useForm()

  const handleToggleStrategy = async (strategy: Strategy) => {
    // TODO: 调用API切换策略状态
    console.log('Toggle strategy:', strategy.name, !strategy.enabled)
    fetchStrategies()
  }

  const handleEditStrategy = (strategy: Strategy) => {
    setSelectedStrategy(strategy)
    form.setFieldsValue({
      min_profit_rate: strategy.min_profit_rate,
      max_position_size: strategy.max_position_size,
    })
    setEditModalVisible(true)
  }

  const handleSaveStrategy = async () => {
    if (!selectedStrategy) return

    try {
      const values = await form.validateFields()

      // TODO: 调用API更新策略配置
      console.log('Update strategy:', selectedStrategy.name, values)

      setEditModalVisible(false)
      fetchStrategies()
    } catch (error) {
      console.error('表单验证失败:', error)
    }
  }

  const columns = [
    {
      title: '策略名称',
      dataIndex: 'name',
      key: 'name',
      width: 150,
    },
    {
      title: '策略类型',
      dataIndex: 'type',
      key: 'type',
      width: 120,
      render: (type: string) => {
        const typeMap: Record<string, string> = {
          cross_exchange: '跨交易所',
          triangular: '三角套利',
          basis_trading: '基差套利',
          funding_rate: '资金费率',
          statistical_arbitrage: '统计套利',
        }
        return typeMap[type] || type
      },
    },
    {
      title: '状态',
      dataIndex: 'state',
      key: 'state',
      width: 100,
      render: (state: string) => {
        const stateMap: Record<string, { text: string; color: string }> = {
          running: { text: '运行中', color: 'success' },
          paused: { text: '已暂停', color: 'warning' },
          stopped: { text: '已停止', color: 'default' },
          error: { text: '错误', color: 'error' },
        }
        const { text, color } = stateMap[state] || { text: state, color: 'default' }
        return <Tag color={color}>{text}</Tag>
      },
    },
    {
      title: '启用',
      dataIndex: 'enabled',
      key: 'enabled',
      width: 80,
      render: (enabled: boolean, record: Strategy) => (
        <Switch
          checked={enabled}
          onChange={() => handleToggleStrategy(record)}
        />
      ),
    },
    {
      title: '总交易数',
      dataIndex: ['performance', 'total_trades'],
      key: 'total_trades',
      width: 100,
    },
    {
      title: '总利润',
      dataIndex: ['performance', 'total_profit'],
      key: 'total_profit',
      width: 100,
      render: (profit: number) => (
        <span style={{ color: profit >= 0 ? '#52c41a' : '#ff4d4f' }}>
          ${profit.toFixed(2)}
        </span>
      ),
    },
    {
      title: '胜率',
      dataIndex: ['performance', 'success_rate'],
      key: 'success_rate',
      width: 80,
      render: (rate: number) => `${rate.toFixed(1)}%`,
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_: any, record: Strategy) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEditStrategy(record)}
          >
            编辑
          </Button>
          <Button
            type="link"
            icon={record.enabled ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
            onClick={() => handleToggleStrategy(record)}
          >
            {record.enabled ? '暂停' : '启动'}
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <div className="strategy-management">
      <h2 className="page-title">策略管理</h2>

      <Card>
        <Table
          columns={columns}
          dataSource={strategies}
          rowKey="name"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
          }}
        />
      </Card>

      <Modal
        title={`编辑策略 - ${selectedStrategy?.name}`}
        open={editModalVisible}
        onOk={handleSaveStrategy}
        onCancel={() => setEditModalVisible(false)}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            min_profit_rate: selectedStrategy?.min_profit_rate || 0.5,
            max_position_size: selectedStrategy?.max_position_size || 1000,
          }}
        >
          <Form.Item
            label="最小收益率 (%)"
            name="min_profit_rate"
            rules={[
              { required: true, message: '请输入最小收益率' },
              { type: 'number', min: 0, message: '收益率不能为负数' },
            ]}
          >
            <InputNumber
              min={0}
              max={100}
              step={0.1}
              precision={2}
              style={{ width: '100%' }}
            />
          </Form.Item>

          <Form.Item
            label="最大仓位大小 ($)"
            name="max_position_size"
            rules={[
              { required: true, message: '请输入最大仓位大小' },
              { type: 'number', min: 0, message: '仓位大小不能为负数' },
            ]}
          >
            <InputNumber
              min={0}
              step={100}
              precision={2}
              style={{ width: '100%' }}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default StrategyManagement
