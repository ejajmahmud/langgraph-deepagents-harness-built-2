import { useState, useEffect } from 'react'
import { Card, List, Tag, Badge, Empty, Button } from 'antd'
import { AlertOutlined, CheckCircleOutlined, ClockCircleOutlined } from '@ant-design/icons'
import { useAppStore } from '@/store'
import { Alert } from '@/types'
import dayjs from 'dayjs'

const MonitoringAlerts: React.FC = () => {
  const { alerts, fetchAlerts, setAlerts } = useAppStore()
  const [filter, setFilter] = useState<'all' | 'unread'>('all')

  useEffect(() => {
    loadAlerts()

    // 定期刷新
    const interval = setInterval(() => {
      loadAlerts()
    }, 30000) // 30秒

    return () => clearInterval(interval)
  }, [])

  const loadAlerts = async () => {
    await fetchAlerts()
  }

  // 确认告警
  const handleAcknowledge = async (alertId: string) => {
    try {
      // TODO: 调用API确认告警
      const updatedAlerts = alerts.map((a) =>
        a.id === alertId ? { ...a, acknowledged: true } : a
      )
      setAlerts(updatedAlerts)
    } catch (error) {
      console.error('确认告警失败:', error)
    }
  }

  // 批量确认所有
  const handleAcknowledgeAll = async () => {
    try {
      // TODO: 调用API批量确认
      const updatedAlerts = alerts.map((a) => ({ ...a, acknowledged: true }))
      setAlerts(updatedAlerts)
    } catch (error) {
      console.error('批量确认失败:', error)
    }
  }

  // 获取显示的告警列表
  const displayedAlerts = filter === 'unread'
    ? alerts.filter((a) => !a.acknowledged)
    : alerts

  // 未读告警数
  const unreadCount = alerts.filter((a) => !a.acknowledged).length

  return (
    <div className="monitoring-alerts">
      <div className="page-header">
        <h2 className="page-title">监控告警</h2>
        <div className="header-actions">
          <Badge count={unreadCount}>
            <Button
              type={filter === 'unread' ? 'primary' : 'default'}
              onClick={() => setFilter('unread')}
            >
              未读
            </Button>
          </Badge>
          <Button
            type={filter === 'all' ? 'primary' : 'default'}
            onClick={() => setFilter('all')}
          >
            全部
          </Button>
          {unreadCount > 0 && (
            <Button onClick={handleAcknowledgeAll}>
              全部已读
            </Button>
          )}
        </div>
      </div>

      <Card>
        {displayedAlerts.length === 0 ? (
          <Empty description="暂无告警" />
        ) : (
          <List
            dataSource={displayedAlerts}
            renderItem={(alert) => (
              <List.Item
                className={`alert-item ${alert.level} ${!alert.acknowledged ? 'unread' : ''}`}
                actions={[
                  !alert.acknowledged && (
                    <Button
                      type="link"
                      size="small"
                      icon={<CheckCircleOutlined />}
                      onClick={() => handleAcknowledge(alert.id)}
                    >
                      确认
                    </Button>
                  ),
                ]}
              >
                <List.Item.Meta
                  avatar={<AlertOutlined className={`alert-icon alert-${alert.level}`} />}
                  title={
                    <div className="alert-header">
                      <Tag color={getLevelColor(alert.level)}>
                        {getLevelText(alert.level)}
                      </Tag>
                      <span className="alert-source">{alert.source}</span>
                      {!alert.acknowledged && <Badge status="processing" />}
                    </div>
                  }
                  description={
                    <div className="alert-content">
                      <p className="alert-message">{alert.message}</p>
                      <p className="alert-time">
                        <ClockCircleOutlined />
                        {' '}
                        {dayjs(alert.timestamp).format('YYYY-MM-DD HH:mm:ss')}
                      </p>
                    </div>
                  }
                />
              </List.Item>
            )}
          />
        )}
      </Card>
    </div>
  )
}

// 辅助函数：获取级别颜色
const getLevelColor = (level: string): string => {
  const colorMap: Record<string, string> = {
    info: 'blue',
    warning: 'orange',
    error: 'red',
    critical: 'red',
  }
  return colorMap[level] || 'default'
}

// 辅助函数：获取级别文本
const getLevelText = (level: string): string => {
  const textMap: Record<string, string> = {
    info: '信息',
    warning: '警告',
    error: '错误',
    critical: '严重',
  }
  return textMap[level] || level
}

export default MonitoringAlerts
