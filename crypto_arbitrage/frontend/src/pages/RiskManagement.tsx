import { useState } from 'react'
import { Card, Form, InputNumber, Button, Alert, Progress, Statistic } from 'antd'
import { SafetyOutlined, DollarOutlined, ShieldOutlined } from '@ant-design/icons'
import { useAppStore } from '@/store'
import { riskAPI } from '@/api'

const RiskManagement: React.FC = () => {
  const { systemStatus } = useAppStore()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [currentRisk, setCurrentRisk] = useState<any>(null)

  // 初始化风险配置
  const loadRiskConfig = async () => {
    try {
      const response = await riskAPI.getConfig()
      setCurrentRisk(response.data)
      form.setFieldsValue(response.data)
    } catch (error) {
      console.error('加载风险配置失败:', error)
    }
  }

  // 保存风险配置
  const handleSave = async () => {
    try {
      setLoading(true)
      const values = await form.validateFields()

      await riskAPI.updateConfig(values)

      Alert.success('风险配置已更新', 3)
      loadRiskConfig()
    } catch (error) {
      console.error('保存风险配置失败:', error)
      Alert.error('保存失败，请重试', 3)
    } finally {
      setLoading(false)
    }
  }

  // 重置为默认值
  const handleReset = () => {
    form.setFieldsValue({
      max_daily_loss: 500,
      max_position_size: 1000,
      max_total_exposure: 5000,
      max_drawdown: 10.0,
      base_stop_loss: 2.0,
      base_take_profit: 1.0,
      trailing_stop: 0.5,
      risk_reward_ratio: 2.0,
    })
  }

  return (
    <div className="risk-management">
      <h2 className="page-title">风险管理</h2>

      <Card title="当前风险状态" className="risk-status-card">
        <div className="risk-metrics">
          <Statistic
            title="总错误数"
            value={systemStatus?.total_errors || 0}
            prefix={<SafetyOutlined />}
            valueStyle={{ color: systemStatus?.total_errors > 10 ? '#ff4d4f' : '#52c41a' }}
          />
          <Statistic
            title="每日最大损失限制"
            value={currentRisk?.max_daily_loss || 500}
            prefix={<DollarOutlined />}
            suffix="$"
          />
          <Statistic
            title="最大持仓限制"
            value={currentRisk?.max_position_size || 1000}
            prefix={<DollarOutlined />}
            suffix="$"
          />
        </div>

        {systemStatus?.total_errors > 0 && (
          <Alert
            message={`系统检测到 ${systemStatus.total_errors} 个错误，请检查日志`}
            type="warning"
            showIcon
            style={{ marginTop: 16 }}
          />
        )}
      </Card>

      <Card title="风险参数配置" className="risk-config-card">
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            max_daily_loss: 500,
            max_position_size: 1000,
            max_total_exposure: 5000,
            max_drawdown: 10.0,
            base_stop_loss: 2.0,
            base_take_profit: 1.0,
            trailing_stop: 0.5,
            risk_reward_ratio: 2.0,
          }}
        >
          <div className="form-row">
            <Form.Item
              label="每日最大损失限制 ($)"
              name="max_daily_loss"
              rules={[
                { required: true, message: '请输入每日最大损失限制' },
                { type: 'number', min: 0, message: '不能为负数' },
              ]}
            >
              <InputNumber min={0} style={{ width: '100%' }} />
            </Form.Item>

            <Form.Item
              label="最大持仓大小 ($)"
              name="max_position_size"
              rules={[
                { required: true, message: '请输入最大持仓大小' },
                { type: 'number', min: 0, message: '不能为负数' },
              ]}
            >
              <InputNumber min={0} style={{ width: '100%' }} />
            </Form.Item>
          </div>

          <div className="form-row">
            <Form.Item
              label="最大总风险敞口 ($)"
              name="max_total_exposure"
              rules={[
                { required: true, message: '请输入最大总风险敞口' },
                { type: 'number', min: 0, message: '不能为负数' },
              ]}
            >
              <InputNumber min={0} style={{ width: '100%' }} />
            </Form.Item>

            <Form.Item
              label="最大回撤限制 (%)"
              name="max_drawdown"
              rules={[
                { required: true, message: '请输入最大回撤限制' },
                { type: 'number', min: 0, max: 100, message: '范围为0-100' },
              ]}
            >
              <InputNumber min={0} max={100} style={{ width: '100%' }} />
            </Form.Item>
          </div>

          <div className="form-row">
            <Form.Item
              label="基础止损比例 (%)"
              name="base_stop_loss"
              rules={[
                { required: true, message: '请输入基础止损比例' },
                { type: 'number', min: 0, message: '不能为负数' },
              ]}
            >
              <InputNumber min={0} style={{ width: '100%' }} />
            </Form.Item>

            <Form.Item
              label="基础止盈比例 (%)"
              name="base_take_profit"
              rules={[
                { required: true, message: '请输入基础止盈比例' },
                { type: 'number', min: 0, message: '不能为负数' },
              ]}
            >
              <InputNumber min={0} style={{ width: '100%' }} />
            </Form.Item>
          </div>

          <div className="form-row">
            <Form.Item
              label="追踪止损比例 (%)"
              name="trailing_stop"
              rules={[
                { required: true, message: '请输入追踪止损比例' },
                { type: 'number', min: 0, message: '不能为负数' },
              ]}
            >
              <InputNumber min={0} style={{ width: '100%' }} />
            </Form.Item>

            <Form.Item
              label="风险回报比"
              name="risk_reward_ratio"
              rules={[
                { required: true, message: '请输入风险回报比' },
                { type: 'number', min: 0, message: '不能为负数' },
              ]}
            >
              <InputNumber min={0} step={0.1} precision={1} style={{ width: '100%' }} />
            </Form.Item>
          </div>

          <div className="form-actions">
            <Button type="primary" onClick={handleSave} loading={loading} icon={<ShieldOutlined />}>
              保存配置
            </Button>
            <Button onClick={handleReset}>
              重置默认
            </Button>
          </div>
        </Form>
      </Card>
    </div>
  )
}

export default RiskManagement
