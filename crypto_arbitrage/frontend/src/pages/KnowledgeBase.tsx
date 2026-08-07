/**
 * 知识库页面 V2.5
 *
 * 展示Memo0知识库内容，支持：
 * 1. 知识概览统计
 * 2. 语义搜索
 * 3. 知识分类浏览
 * 4. 知识详情查看
 * 5. 手动添加知识
 */

import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Input, Button, Table, Tag, Modal, Form, Select, message, Tabs, Empty, Spin } from 'antd';
import { SearchOutlined, PlusOutlined, BookOutlined, ThunderboltOutlined, LineChartOutlined, AlertOutlined } from '@ant-design/icons';
import axios from 'axios';

const { TabPane } = Tabs;
const { Search } = Input;
const { Option } = Select;

interface Knowledge {
  id: string;
  content: string;
  category: string;
  score: number;
  metadata: Record<string, any>;
  created_at: string;
}

interface KnowledgeStats {
  total_count: number;
  recent_count: number;
  time_range: string;
  by_category: Record<string, number>;
  auto_accumulator_stats?: {
    total: number;
    by_category: Record<string, number>;
    by_type: Record<string, number>;
    recent_count: number;
  };
}

interface KnowledgeProfile {
  user_id: string;
  agent_id: string;
  total_memories: number;
  categories?: Record<string, number>;
}

const KnowledgeBase: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<KnowledgeStats | null>(null);
  const [profile, setProfile] = useState<KnowledgeProfile | null>(null);
  const [searchResults, setSearchResults] = useState<Knowledge[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [selectedKnowledge, setSelectedKnowledge] = useState<Knowledge | null>(null);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [addModalVisible, setAddModalVisible] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  // 表单
  const [addForm] = Form.useForm();

  // API基础URL
  const API_BASE = 'http://localhost:8000/api';

  // 加载知识统计
  const loadStats = async (timeRange: string = '24h') => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE}/knowledge/stats?time_range=${timeRange}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      setStats(response.data);
    } catch (error: any) {
      message.error(`加载统计失败: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 加载知识概览
  const loadProfile = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE}/knowledge/profile`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      setProfile(response.data.profile);
    } catch (error: any) {
      message.error(`加载概览失败: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 搜索知识
  const handleSearch = async (value: string) => {
    if (!value.trim()) {
      message.warning('请输入搜索关键词');
      return;
    }

    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE}/knowledge/search`, {
        params: {
          query: value,
          category: selectedCategory || undefined,
          top_k: 10,
        },
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      setSearchResults(response.data.results);
      setActiveTab('search');
    } catch (error: any) {
      message.error(`搜索失败: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 加载历史知识
  const loadHistory = async (category?: string) => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE}/knowledge/history`, {
        params: {
          category: category || undefined,
          limit: 50,
          offset: 0,
        },
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      setSearchResults(response.data.results);
    } catch (error: any) {
      message.error(`加载历史失败: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 查看知识详情
  const handleViewDetail = (knowledge: Knowledge) => {
    setSelectedKnowledge(knowledge);
    setDetailModalVisible(true);
  };

  // 添加知识
  const handleAddKnowledge = async (values: any) => {
    try {
      setLoading(true);
      const response = await axios.post(`${API_BASE}/knowledge/add`, values, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.data.status === 'success') {
        message.success('知识添加成功');
        setAddModalVisible(false);
        addForm.resetFields();
        loadStats();
      }
    } catch (error: any) {
      message.error(`添加失败: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 初始化加载
  useEffect(() => {
    loadStats();
    loadProfile();
  }, []);

  // 类别颜色映射
  const getCategoryColor = (category: string): string => {
    const colors: Record<string, string> = {
      decision: 'blue',
      trade_result: 'green',
      market_pattern: 'purple',
      strategy_performance: 'orange',
      risk_event: 'red',
      alert: 'magenta',
    };
    return colors[category] || 'default';
  };

  // 表格列定义
  const columns = [
    {
      title: '类别',
      dataIndex: 'category',
      key: 'category',
      width: 120,
      render: (category: string) => (
        <Tag color={getCategoryColor(category)}>{category}</Tag>
      ),
    },
    {
      title: '内容摘要',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
      render: (content: string) => (
        <span style={{ fontSize: '12px' }}>
          {content.length > 100 ? content.substring(0, 100) + '...' : content}
        </span>
      ),
    },
    {
      title: '相关度',
      dataIndex: 'score',
      key: 'score',
      width: 100,
      render: (score: number) => (
        <span style={{ color: score > 0.8 ? '#52c41a' : score > 0.5 ? '#faad14' : '#ff4d4f' }}>
          {(score * 100).toFixed(1)}%
        </span>
      ),
    },
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (time: string) => new Date(time).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: any, record: Knowledge) => (
        <Button type="link" size="small" onClick={() => handleViewDetail(record)}>
          查看详情
        </Button>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ marginBottom: '24px' }}>
        <BookOutlined /> 知识库
      </h1>

      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        {/* 概览标签页 */}
        <TabPane tab="概览" key="overview">
          <Spin spinning={loading}>
            {/* 统计卡片 */}
            <Row gutter={16} style={{ marginBottom: '24px' }}>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="总知识数"
                    value={stats?.total_count || 0}
                    prefix={<BookOutlined />}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="最近24小时"
                    value={stats?.recent_count || 0}
                    prefix={<ThunderboltOutlined />}
                    valueStyle={{ color: '#3f8600' }}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="类别数"
                    value={Object.keys(stats?.by_category || {}).length}
                    prefix={<LineChartOutlined />}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="用户ID"
                    value={profile?.user_id || 'N/A'}
                  />
                </Card>
              </Col>
            </Row>

            {/* 分类统计 */}
            <Row gutter={16} style={{ marginBottom: '24px' }}>
              <Col span={24}>
                <Card title="知识分类">
                  <Row gutter={16}>
                    {Object.entries(stats?.by_category || {}).map(([category, count]) => (
                      <Col span={4} key={category}>
                        <Card size="small">
                          <Tag color={getCategoryColor(category)} style={{ fontSize: '14px', marginBottom: '8px' }}>
                            {category}
                          </Tag>
                          <Statistic value={count} valueStyle={{ fontSize: '20px' }} />
                        </Card>
                      </Col>
                    ))}
                  </Row>
                </Card>
              </Col>
            </Row>

            {/* 自动积累统计 */}
            {stats?.auto_accumulator_stats && (
              <Row gutter={16}>
                <Col span={24}>
                  <Card title="自动知识积累">
                    <Row gutter={16}>
                      <Col span={8}>
                        <Statistic
                          title="自动记录总数"
                          value={stats.auto_accumulator_stats.total || 0}
                          prefix={<ThunderboltOutlined />}
                        />
                      </Col>
                      <Col span={8}>
                        <Statistic
                          title="最近24小时"
                          value={stats.auto_accumulator_stats.recent_count || 0}
                          valueStyle={{ color: '#3f8600' }}
                        />
                      </Col>
                      <Col span={8}>
                        <Statistic
                          title="类型数"
                          value={Object.keys(stats.auto_accumulator_stats.by_type || {}).length}
                        />
                      </Col>
                    </Row>
                  </Card>
                </Col>
              </Row>
            )}
          </Spin>
        </TabPane>

        {/* 搜索标签页 */}
        <TabPane tab="搜索" key="search">
          <Card>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Input.Group compact>
                <Select
                  defaultValue="all"
                  style={{ width: '120px' }}
                  onChange={(value) => setSelectedCategory(value === 'all' ? null : value)}
                >
                  <Option value="all">全部类别</Option>
                  <Option value="decision">决策记录</Option>
                  <Option value="trade_result">交易结果</Option>
                  <Option value="market_pattern">市场模式</Option>
                  <Option value="strategy_performance">策略表现</Option>
                  <Option value="risk_event">风险事件</Option>
                  <Option value="alert">告警记录</Option>
                </Select>
                <Search
                  placeholder="搜索知识库..."
                  allowClear
                  enterButton={<SearchOutlined />}
                  size="large"
                  onSearch={handleSearch}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{ width: 'calc(100% - 120px)' }}
                />
              </Input.Group>

              {searchResults.length > 0 && (
                <Table
                  columns={columns}
                  dataSource={searchResults}
                  rowKey="id"
                  pagination={{ pageSize: 10 }}
                  size="small"
                />
              )}

              {searchResults.length === 0 && !loading && (
                <Empty description="暂无搜索结果，请尝试其他关键词" />
              )}
            </Space>
          </Card>
        </TabPane>

        {/* 历史标签页 */}
        <TabPane tab="历史" key="history">
          <Card
            title="知识历史"
            extra={
              <Space>
                <Select
                  defaultValue="all"
                  style={{ width: '150px' }}
                  onChange={(value) => {
                    setSelectedCategory(value === 'all' ? null : value);
                    loadHistory(value === 'all' ? undefined : value);
                  }}
                >
                  <Option value="all">全部类别</Option>
                  <Option value="decision">决策记录</Option>
                  <Option value="trade_result">交易结果</Option>
                  <Option value="market_pattern">市场模式</Option>
                  <Option value="strategy_performance">策略表现</Option>
                  <Option value="risk_event">风险事件</Option>
                  <Option value="alert">告警记录</Option>
                </Select>
                <Button icon={<PlusOutlined />} type="primary" onClick={() => setAddModalVisible(true)}>
                  添加知识
                </Button>
              </Space>
            }
          >
            <Spin spinning={loading}>
              {searchResults.length > 0 ? (
                <Table
                  columns={columns}
                  dataSource={searchResults}
                  rowKey="id"
                  pagination={{ pageSize: 10 }}
                  size="small"
                />
              ) : (
                <Empty description="暂无知识记录" />
              )}
            </Spin>
          </Card>
        </TabPane>
      </Tabs>

      {/* 知识详情弹窗 */}
      <Modal
        title="知识详情"
        visible={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>,
        ]}
        width={800}
      >
        {selectedKnowledge && (
          <div>
            <div style={{ marginBottom: '16px' }}>
              <Tag color={getCategoryColor(selectedKnowledge.category)}>{selectedKnowledge.category}</Tag>
              <span style={{ marginLeft: '8px', color: '#999' }}>
                {new Date(selectedKnowledge.created_at).toLocaleString('zh-CN')}
              </span>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <strong>内容：</strong>
              <div style={{
                marginTop: '8px',
                padding: '12px',
                background: '#f5f5f5',
                borderRadius: '4px',
                whiteSpace: 'pre-wrap',
                maxHeight: '300px',
                overflowY: 'auto'
              }}>
                {selectedKnowledge.content}
              </div>
            </div>

            {Object.keys(selectedKnowledge.metadata).length > 0 && (
              <div>
                <strong>元数据：</strong>
                <pre style={{
                  marginTop: '8px',
                  padding: '12px',
                  background: '#f5f5f5',
                  borderRadius: '4px',
                  maxHeight: '200px',
                  overflowY: 'auto',
                  fontSize: '12px'
                }}>
                  {JSON.stringify(selectedKnowledge.metadata, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </Modal>

      {/* 添加知识弹窗 */}
      <Modal
        title="添加知识"
        visible={addModalVisible}
        onCancel={() => setAddModalVisible(false)}
        onOk={() => addForm.submit()}
        okText="添加"
        cancelText="取消"
      >
        <Form
          form={addForm}
          layout="vertical"
          onFinish={handleAddKnowledge}
        >
          <Form.Item
            label="类别"
            name="category"
            rules={[{ required: true, message: '请选择类别' }]}
          >
            <Select placeholder="选择类别">
              <Option value="decision">决策记录</Option>
              <Option value="trade_result">交易结果</Option>
              <Option value="market_pattern">市场模式</Option>
              <Option value="strategy_performance">策略表现</Option>
              <Option value="risk_event">风险事件</Option>
              <Option value="alert">告警记录</Option>
            </Select>
          </Form.Item>

          <Form.Item
            label="内容"
            name="content"
            rules={[{ required: true, message: '请输入内容' }]}
          >
            <Input.TextArea rows={6} placeholder="输入知识内容..." />
          </Form.Item>

          <Form.Item label="元数据（可选）" name="metadata">
            <Input.TextArea rows={4} placeholder='JSON格式，例如: {"key": "value"}' />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default KnowledgeBase;
