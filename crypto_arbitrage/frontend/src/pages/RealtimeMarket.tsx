import { useState, useEffect } from 'react'
import { Row, Col, Card, Statistic, Spin, Empty, Button, Space } from 'antd'
import { ReloadOutlined } from '@ant-design/icons'
import { useAppStore } from '@/store'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

const RealtimeMarket: React.FC = () => {
  const { marketData, selectedSymbol, setSelectedSymbol, fetchMarketData } = useAppStore()
  const [priceHistory, setPriceHistory] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  const symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'DOGE/USDT']

  useEffect(() => {
    loadMarketData()

    // 定期刷新
    const interval = setInterval(() => {
      loadMarketData()
    }, 5000) // 5秒

    return () => clearInterval(interval)
  }, [])

  const loadMarketData = async () => {
    try {
      setLoading(true)
      await fetchMarketData(symbols)

      // 模拟价格历史数据（实际应从API获取）
      const currentPrice = marketData[selectedSymbol]?.price || 50000
      const history = Array.from({ length: 50 }, (_, i) => ({
        time: i,
        price: currentPrice * (1 + (Math.random() - 0.5) * 0.02),
      }))
      setPriceHistory(history)
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = () => {
    loadMarketData()
  }

  const handleSymbolSelect = (symbol: string) => {
    setSelectedSymbol(symbol)
    // 重新加载历史数据
    const currentPrice = marketData[symbol]?.price || 0
    const history = Array.from({ length: 50 }, (_, i) => ({
      time: i,
      price: currentPrice * (1 + (Math.random() - 0.5) * 0.02),
    }))
    setPriceHistory(history)
  }

  return (
    <div className="realtime-market">
      <div className="page-header">
        <h2 className="page-title">实时行情</h2>
        <Button icon={<ReloadOutlined />} onClick={handleRefresh} loading={loading}>
          刷新
        </Button>
      </div>

      {/* 交易对价格卡片 */}
      <Row gutter={[16, 16]} className="price-cards">
        {symbols.map((symbol) => {
          const data = marketData[symbol]
          if (!data) return null

          const isPositive = data.change_24h >= 0

          return (
            <Col key={symbol} xs={12} sm={8} md={6} lg={4}>
              <Card
                className={`price-card ${selectedSymbol === symbol ? 'selected' : ''}`}
                hoverable
                onClick={() => handleSymbolSelect(symbol)}
              >
                <div className="price-symbol">{symbol}</div>
                <Statistic
                  value={data.price}
                  precision={2}
                  prefix="$"
                  valueStyle={{
                    fontSize: '24px',
                    fontWeight: 'bold',
                  }}
                />
                <div className={`price-change ${isPositive ? 'positive' : 'negative'}`}>
                  {isPositive ? '+' : ''}{data.change_24h.toFixed(2)}%
                </div>
                <div className="price-volume">
                  24H 量: {(data.volume_24h / 1000000).toFixed(2)}M
                </div>
              </Card>
            </Col>
          )
        })}
      </Row>

      {/* 价格图表 */}
      <Row gutter={[16, 16]} className="chart-row">
        <Col span={24}>
          <Card title={`${selectedSymbol} 价格走势`} className="chart-card">
            {priceHistory.length > 0 ? (
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={priceHistory}>
                  <XAxis dataKey="time" />
                  <YAxis domain={['dataMin', 'dataMax']} />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey="price"
                    stroke="#1890ff"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <Empty description="暂无价格数据" />
            )}
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default RealtimeMarket
