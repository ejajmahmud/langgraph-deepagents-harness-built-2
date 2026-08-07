import { Card, Form, Input, Switch, Button, Divider, Alert } from 'antd'
import { UserOutlined, SettingOutlined } from '@ant-design/icons'

const Settings: React.FC = () => {
  const [form] = Form.useForm()

  // 保存系统设置
  const handleSaveSystemSettings = async () => {
    try {
      const values = await form.validateFields()
      console.log('Save system settings:', values)
      Alert.success('系统设置已保存', 3)
    } catch (error) {
      console.error('保存系统设置失败:', error)
      Alert.error('保存失败，请重试', 3)
    }
  }

  return (
    <div className="settings">
      <h2 className="page-title">系统设置</h2>

      <Card title="用户信息" className="settings-card">
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            username: 'admin',
            email: 'admin@example.com',
          }}
        >
          <Form.Item label="用户名" name="username">
            <Input disabled />
          </Form.Item>

          <Form.Item label="邮箱" name="email">
            <Input disabled />
          </Form.Item>
        </Form>
      </Card>

      <Card title="系统配置" className="settings-card">
        <Form
          layout="vertical"
          initialValues={{
            enable_notifications: true,
            enable_auto_trading: false,
            log_level: 'INFO',
          }}
        >
          <Form.Item
            label="启用通知"
            name="enable_notifications"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>

          <Form.Item
            label="启用自动交易"
            name="enable_auto_trading"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>

          <Form.Item
            label="日志级别"
            name="log_level"
          >
            <Input />
          </Form.Item>
        </Form>

        <Alert
          message="注意"
          description="启用自动交易后，系统将自动执行套利机会，请确保已正确配置交易所API密钥和风险参数。"
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />

        <Button type="primary" icon={<SettingOutlined />} onClick={handleSaveSystemSettings}>
          保存设置
        </Button>
      </Card>
    </div>
  )
}

export default Settings
