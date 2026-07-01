import React, { useState, useEffect } from 'react'
import { 
  Card, Row, Col, Statistic, DatePicker, Spin, message, Space, Button, Tag, Divider 
} from 'antd'
import { 
  DollarOutlined, 
  ClockCircleOutlined, 
  CheckCircleOutlined,
  UnorderedListOutlined,
  RiseOutlined,
  ToolOutlined,
  TeamOutlined,
  CalendarOutlined,
  PlusOutlined,
  UserAddOutlined,
  ProfileOutlined,
  SettingOutlined,
  UserOutlined,
  FileTextOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'
import { 
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, PieChart, Pie, Cell
} from 'recharts'
import { getDashboard } from '../api'
import { useAuth } from '../contexts/AuthContext'
import { ORDER_STATUS_CONFIG } from '../types'

const { RangePicker } = DatePicker

// Цвета для графиков
const CHART_COLORS = ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1', '#13c2c2', '#eb2f96']

// Статусы для круговой диаграммы
const STATUS_COLORS: Record<string, string> = {
  new: '#1890ff',
  diagnostics: '#faad14',
  agreed: '#fa8c16',
  repair: '#722ed1',
  ready: '#52c41a',
  issued: '#d9d9d9',
  cancelled: '#f5222d',
}

const DashboardPage: React.FC = () => {
  const { user, hasPermission } = useAuth()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<any>(null)
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs]>([
    dayjs().startOf('month'),
    dayjs(),
  ])

  useEffect(() => {
    fetchDashboard()
  }, [dateRange])

  const fetchDashboard = async () => {
    setLoading(true)
    try {
      const result = await getDashboard(
        dateRange[0].format('YYYY-MM-DD'),
        dateRange[1].format('YYYY-MM-DD')
      )
      setData(result)
    } catch (error) {
      message.error('Ошибка загрузки дашборда')
    } finally {
      setLoading(false)
    }
  }

  if (loading || !data) {
    return <div style={{ textAlign: 'center', padding: 40 }}><Spin size="large" /></div>
  }

  const role = user?.role_name || ''

  // ===== Дашборд Мастера =====
  const MasterDashboard = () => (
    <>
      <div style={{ marginBottom: 16 }}>
        <h1 style={{ margin: 0 }}>
          📊 Статистика мастера
          <Tag color="blue" style={{ marginLeft: 8 }}>{user?.username}</Tag>
        </h1>
        <div style={{ color: '#888', fontSize: 14 }}>{dayjs().format('DD.MM.YYYY')}</div>
      </div>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic 
              title="Текущие заказы" 
              value={data.total_orders || 0} 
              prefix={<UnorderedListOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic 
              title="Общий баланс" 
              value={data.total_revenue || 0} 
              precision={2}
              prefix={<DollarOutlined />}
              suffix="₽"
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic 
              title="Выполнено в этом месяце" 
              value={data.masters_efficiency?.find((m: any) => m.master_id === user?.id)?.orders_completed || 0}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic 
              title="Гарантийные" 
              value={data.warranty_orders || 0} 
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
      </Row>
    </>
  )

  // ===== Дашборд Менеджера/Приёмщика =====
  const ManagerDashboard = () => (
    <>
      <div style={{ marginBottom: 16 }}>
        <h1 style={{ margin: 0 }}>
          📊 Статистика менеджера
          <Tag color="green" style={{ marginLeft: 8 }}>{user?.username}</Tag>
        </h1>
        <div style={{ color: '#888', fontSize: 14 }}>{dayjs().format('DD.MM.YYYY')}</div>
      </div>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic 
              title="На согласовании" 
              value={data.status_breakdown?.agreed || 0} 
              prefix={<CalendarOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic 
              title="Сумма заказов" 
              value={data.total_revenue || 0} 
              precision={2}
              prefix={<DollarOutlined />}
              suffix="₽"
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic 
              title="Обработано сегодня" 
              value={data.total_orders || 0}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic 
              title="Сумма обработок" 
              value={data.total_revenue || 0} 
              precision={2}
              prefix={<RiseOutlined />}
              suffix="₽"
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>
    </>
  )

  // ===== Общий дашборд (Админ) =====
  const AdminDashboard = () => {
    const statusData = Object.entries(data.status_breakdown || {}).map(([status, count]) => ({
      name: ORDER_STATUS_CONFIG[status]?.label || status,
      value: count,
      color: STATUS_COLORS[status] || '#d9d9d9',
    }))

    const mastersData = (data.masters_efficiency || []).map((m: any) => ({
      name: m.master_name,
      orders: m.orders_completed,
      revenue: m.revenue,
    }))

    const dailyOrdersData = data.daily_orders || []
    const dailyRevenueData = data.daily_revenue || []

    return (
      <>
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h1 style={{ margin: 0 }}>📊 Общая статистика</h1>
          <RangePicker 
            value={dateRange}
            onChange={(dates) => {
              if (dates && dates[0] && dates[1]) {
                setDateRange([dates[0], dates[1]])
              }
            }}
          />
        </div>

        {/* Основные KPI */}
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic 
                title="Всего заказов" 
                value={data.total_orders} 
                prefix={<UnorderedListOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic 
                title="Общая выручка" 
                value={data.total_revenue} 
                precision={2}
                prefix={<DollarOutlined />}
                suffix="₽"
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic 
                title="Активных мастеров" 
                value={data.masters_efficiency?.length || 0}
                prefix={<ToolOutlined />}
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic 
                title="Доход сегодня" 
                value={data.total_revenue || 0}
                precision={2}
                prefix={<RiseOutlined />}
                suffix="₽"
                valueStyle={{ color: '#13c2c2' }}
              />
            </Card>
          </Col>
        </Row>

        {/* Доп. метрики */}
        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col xs={24} sm={12} lg={8}>
            <Card>
              <Statistic 
                title="Текущих заказов" 
                value={data.total_orders}
                prefix={<UnorderedListOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={8}>
            <Card>
              <Statistic 
                title="Просрочено" 
                value={data.overdue_orders} 
                prefix={<ClockCircleOutlined />}
                valueStyle={{ color: data.overdue_orders > 0 ? '#f5222d' : '#3f8600' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={8}>
            <Card>
              <Statistic 
                title="На гарантии" 
                value={data.warranty_orders} 
                prefix={<CheckCircleOutlined />}
                valueStyle={{ color: '#faad14' }}
              />
            </Card>
          </Col>
        </Row>

        {/* Графики */}
        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col xs={24} lg={12}>
            <Card title="📈 Поступление заказов">
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={dailyOrdersData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis allowDecimals={false} />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="count" stroke="#1890ff" name="Заказы" strokeWidth={2} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            </Card>
          </Col>
          <Col xs={24} lg={12}>
            <Card title="💰 Выручка по дням">
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={dailyRevenueData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip formatter={(val: number) => `${val.toFixed(2)} ₽`} />
                  <Legend />
                  <Bar dataKey="amount" fill="#3f8600" name="Выручка" />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          </Col>
        </Row>

        {/* Статусы и мастера */}
        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col xs={24} lg={8}>
            <Card title="Заказы по статусам">
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={statusData}
                    cx="50%"
                    cy="50%"
                    innerRadius={40}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {statusData.map((entry: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
              <div style={{ textAlign: 'center', marginTop: 8 }}>
                {statusData.map((s: any, i: number) => (
                  <Tag key={i} color={s.color} style={{ marginBottom: 4 }}>
                    {s.name}: {s.value}
                  </Tag>
                ))}
              </div>
            </Card>
          </Col>
          <Col xs={24} lg={16}>
            <Card title="Эффективность мастеров">
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={mastersData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="orders" fill="#1890ff" name="Заказы" />
                  <Bar dataKey="revenue" fill="#52c41a" name="Выручка" />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          </Col>
        </Row>
      </>
    )
  }

  // ===== Быстрые действия =====
  const QuickActions = () => (
    <Card title="⚡ Быстрые действия" size="small" style={{ marginTop: 16 }}>
      <Space wrap>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/orders/create')}>
          Новый заказ
        </Button>
        <Button icon={<UserAddOutlined />} onClick={() => navigate('/clients')}>
          Новый клиент
        </Button>
        <Button icon={<ToolOutlined />} onClick={() => navigate('/parts')}>
          Склад запчастей
        </Button>
        {hasPermission('report.view') && (
          <Button icon={<FileTextOutlined />} onClick={() => navigate('/dashboard')}>
            Отчеты
          </Button>
        )}
        <Button icon={<UserOutlined />} onClick={() => navigate('/profile')}>
          Профиль
        </Button>
        {hasPermission('user.manage') && (
          <Button icon={<SettingOutlined />} onClick={() => navigate('/settings')}>
            Настройки
          </Button>
        )}
      </Space>
    </Card>
  )

  // ===== Выбор дашборда по роли =====
  const renderDashboard = () => {
    if (role === 'master') return <MasterDashboard />
    if (role === 'manager' || role === 'acceptor') return <ManagerDashboard />
    return <AdminDashboard />
  }

  return (
    <div>
      {renderDashboard()}
      <QuickActions />

      {/* Профиль */}
      <Card title="👤 Мой профиль" size="small" style={{ marginTop: 16 }}>
        <Row gutter={16}>
          <Col span={6}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ 
                width: 64, height: 64, borderRadius: '50%', background: '#1890ff', 
                color: 'white', fontSize: 28, lineHeight: '64px', margin: '0 auto 8px' 
              }}>
                {user?.username?.charAt(0).toUpperCase()}
              </div>
              <div style={{ fontWeight: 'bold' }}>{user?.username}</div>
              <Tag color="blue">{user?.role_name}</Tag>
            </div>
          </Col>
          <Col span={18}>
            <Row gutter={[8, 8]}>
              <Col span={8}>
                <div style={{ color: '#888' }}>Логин</div>
                <div>{user?.username}</div>
              </Col>
              <Col span={8}>
                <div style={{ color: '#888' }}>Заказов</div>
                <div>{data.total_orders || 0}</div>
              </Col>
              <Col span={8}>
                {hasPermission('salary.view') && (
                  <>
                    <div style={{ color: '#888' }}>Настройки зарплаты</div>
                    <Button size="small" onClick={() => navigate('/settings')}>Открыть</Button>
                  </>
                )}
              </Col>
            </Row>
          </Col>
        </Row>
      </Card>
    </div>
  )
}

export default DashboardPage
