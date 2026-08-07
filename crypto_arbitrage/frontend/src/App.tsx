import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout, ConfigProvider, theme } from 'antd'
import {
  DashboardOutlined,
  LineChartOutlined,
  ThunderboltOutlined,
  HistoryOutlined,
  SafetyOutlined,
  AlertOutlined,
  SettingOutlined,
  UserOutlined,
} from '@ant-design/icons'
import MainLayout from './components/Layout'
import Dashboard from './pages/Dashboard'
import RealtimeMarket from './pages/RealtimeMarket'
import StrategyManagement from './pages/StrategyManagement'
import TradeHistory from './pages/TradeHistory'
import RiskManagement from './pages/RiskManagement'
import MonitoringAlerts from './pages/MonitoringAlerts'
import Settings from './pages/Settings'
import Login from './pages/Login'
import ProtectedRoute from './components/ProtectedRoute'

function App() {
  return (
    <ConfigProvider
      theme={{
        algorithm: theme.defaultAlgorithm,
        token: {
          colorPrimary: '#1890ff',
          borderRadius: 6,
        },
      }}
    >
      <Routes>
        <Route path="/login" element={<Login />} />

        <Route
          path="/"
          element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="market" element={<RealtimeMarket />} />
          <Route path="strategies" element={<StrategyManagement />} />
          <Route path="trades" element={<TradeHistory />} />
          <Route path="risk" element={<RiskManagement />} />
          <Route path="monitoring" element={<MonitoringAlerts />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </ConfigProvider>
  )
}

export default App
