import { useState, useEffect } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu, Badge, Avatar, Dropdown } from 'antd'
import {
  DashboardOutlined,
  LineChartOutlined,
  ThunderboltOutlined,
  HistoryOutlined,
  SafetyOutlined,
  AlertOutlined,
  SettingOutlined,
  UserOutlined,
  LogoutOutlined,
  BellOutlined,
} from '@ant-design/icons'
import { useAppStore } from '@/store'
import './Layout.css'

const { Header, Sider, Content } = Layout

const menuItems = [
  {
    key: '/dashboard',
    icon: <DashboardOutlined />,
    label: '仪表盘',
  },
  {
    key: '/market',
    icon: <LineChartOutlined />,
    label: '实时行情',
  },
  {
    key: '/strategies',
    icon: <ThunderboltOutlined />,
    label: '策略管理',
  },
  {
    key: '/trades',
    icon: <HistoryOutlined />,
    label: '交易历史',
  },
  {
    key: '/risk',
    icon: <SafetyOutlined />,
    label: '风险管理',
  },
  {
    key: '/monitoring',
    icon: <AlertOutlined />,
    label: '监控告警',
  },
  {
    key: '/settings',
    icon: <SettingOutlined />,
    label: '系统设置',
  },
]

const MainLayout: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const [collapsed, setCollapsed] = useState(false)

  const { unreadAlerts, fetchAlerts, wsConnected, isAgentRunning } = useAppStore()

  useEffect(() => {
    // 定期获取告警
    const interval = setInterval(() => {
      fetchAlerts()
    }, 30000) // 30秒

    fetchAlerts()

    return () => clearInterval(interval)
  }, [fetchAlerts])

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key)
  }

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    navigate('/login')
  }

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人信息',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ]

  return (
    <Layout className="main-layout">
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        theme="dark"
        className="layout-sider"
      >
        <div className="logo">
          <h1>CA</h1>
          <p>{collapsed ? '' : 'CryptoArbitrage'}</p>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>

      <Layout>
        <Header className="layout-header">
          <div className="header-left">
            <div className="status-badge">
              <span
                className={`status-dot ${isAgentRunning ? 'running' : 'stopped'}`}
              />
              <span>
                {isAgentRunning ? '系统运行中' : '系统已停止'}
              </span>
            </div>
            <div className="ws-badge">
              <span className={`ws-dot ${wsConnected ? 'connected' : 'disconnected'}`} />
              <span>
                {wsConnected ? 'WebSocket 已连接' : 'WebSocket 未连接'}
              </span>
            </div>
          </div>

          <div className="header-right">
            <Badge count={unreadAlerts} overflowCount={99}>
              <BellOutlined className="header-icon" />
            </Badge>

            <Dropdown
              menu={{ items: userMenuItems }}
              placement="bottomRight"
            >
              <Avatar icon={<UserOutlined />} className="header-avatar" />
            </Dropdown>
          </div>
        </Header>

        <Content className="layout-content">
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}

export default MainLayout
