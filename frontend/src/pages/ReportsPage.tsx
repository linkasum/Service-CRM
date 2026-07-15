import React, { useState, useEffect, useCallback, useRef } from 'react'
import {
  Card, Row, Col, Statistic, Table, Tag, DatePicker, Space,
  Divider, Spin, List, Badge, Button, Typography, Modal, Input
} from 'antd'
const { Text } = Typography
import {
  DollarOutlined,
  RiseOutlined,
  UnorderedListOutlined,
  TeamOutlined,
  ToolOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  BarChartOutlined,
  WalletOutlined,
  CalendarOutlined,
  ScanOutlined,
  ClockCircleOutlined,
  UserOutlined,
  MinusOutlined,
  FilterOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, 
  CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area
} from 'recharts'
import { message } from 'antd'
import api, { getEmployeesSalaryReport, getEmployeeSalaryDetail, paySalary } from '../api'

const COLORS = ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1', '#13c2c2', '#eb2f96', '#fa8c16']

// ==================== ОТЧЁТЫ ====================

const OrdersAnalyticsReport: React.FC<{ data: any }> = ({ data }) => {
  if (!data) return <Spin />
  const statusData = Object.entries(data.by_status || {}).map(([k, v]) => ({ name: k, value: v as number }))
  const dayData = Object.entries(data.by_day || {}).sort((a, b) => a[0].localeCompare(b[0])).slice(-14).map(([date, count]) => ({ date, orders: count as number }))

  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col span={8}><Card><Statistic title="Всего заказов" value={data.total_orders} prefix={<UnorderedListOutlined />} /></Card></Col>
        <Col span={8}><Card><Statistic title="Среднее время (дни)" value={data.avg_completion_days} prefix={<ClockCircleOutlined />} /></Card></Col>
        <Col span={8}><Card><Statistic title="По мастерам" value={Object.keys(data.by_master || {}).length} prefix={<TeamOutlined />} /></Card></Col>
      </Row>
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card title="Заказы по статусам">
            <ResponsiveContainer width="100%" height={250}>
              <PieChart><Pie data={statusData} cx="50%" cy="50%" outerRadius={80} dataKey="value" label>{statusData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}</Pie><Tooltip /></PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col span={12}>
          <Card title="Заказы по дням">
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={dayData}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="date" /><YAxis /><Tooltip /><Bar dataKey="orders" fill="#1890ff" /></BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

const FinancialReport: React.FC<{ data: any }> = ({ data }) => {
  if (!data) return <Spin />
  const dayData = Array.isArray(data.by_day) ? data.by_day.slice(-14) : []
  const masterData = data.master_revenue || []
  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col span={6}><Card><Statistic title="Доход нал" value={data.cash_income} precision={0} suffix="₽" valueStyle={{ color: '#3f8600' }} /></Card></Col>
        <Col span={6}><Card><Statistic title="Доход безнал" value={data.card_income} precision={0} suffix="₽" valueStyle={{ color: '#1890ff' }} /></Card></Col>
        <Col span={6}><Card><Statistic title="Расходы" value={data.total_expense} precision={0} suffix="₽" valueStyle={{ color: '#cf1322' }} /></Card></Col>
        <Col span={6}><Card><Statistic title="ЗП выплачено" value={data.total_salary_paid} precision={0} suffix="₽" valueStyle={{ color: '#fa8c16' }} /></Card></Col>
      </Row>
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={6}><Card><Statistic title="Общий доход" value={data.total_income} precision={0} suffix="₽" valueStyle={{ color: '#52c41a' }} /></Card></Col>
        <Col span={6}><Card><Statistic title="Выручка с заказов" value={data.total_revenue} precision={0} suffix="₽" valueStyle={{ color: '#722ed1' }} /></Card></Col>
        <Col span={6}><Card><Statistic title="Запчасти" value={data.total_parts_cost} precision={0} suffix="₽" valueStyle={{ color: '#cf1322' }} /></Card></Col>
        <Col span={6}><Card><Statistic title="Прибыль компании" value={data.company_profit} precision={0} suffix="₽" valueStyle={{ color: data.company_profit >= 0 ? '#3f8600' : '#f5222d' }} /></Card></Col>
      </Row>
      <Card title="Доходы и расходы по дням" style={{ marginTop: 16 }}>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={dayData}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="date" /><YAxis /><Tooltip /><Legend />
            <Area type="monotone" dataKey="cash" stroke="#3f8600" fill="#3f8600" fillOpacity={0.3} name="Нал" />
            <Area type="monotone" dataKey="card" stroke="#1890ff" fill="#1890ff" fillOpacity={0.3} name="Безнал" />
            <Area type="monotone" dataKey="expense" stroke="#cf1322" fill="#cf1322" fillOpacity={0.2} name="Расход" />
            <Area type="monotone" dataKey="salary" stroke="#fa8c16" fill="#fa8c16" fillOpacity={0.2} name="ЗП" />
          </AreaChart>
        </ResponsiveContainer>
      </Card>
      {masterData.length > 0 && (
        <Card title="По мастерам" style={{ marginTop: 16 }} size="small">
          <Table dataSource={masterData} rowKey="name" pagination={false} columns={[
            { title: 'Мастер', dataIndex: 'name', key: 'name' },
            { title: 'Заказов', dataIndex: 'orders', key: 'orders' },
            { title: 'Выручка', dataIndex: 'revenue', key: 'revenue', render: (v: number) => `${v.toLocaleString('ru-RU')} ₽` },
            { title: 'Запчасти', dataIndex: 'parts', key: 'parts', render: (v: number) => `${v.toLocaleString('ru-RU')} ₽` },
          ]} />
        </Card>
      )}
    </div>
  )
}

const EmployeesReport: React.FC<{ data: any }> = ({ data }) => {
  if (!data) return <Spin />
  const masterData = Object.entries(data.masters || {}).map(([name, v]: [string, any]) => ({ name, ...v }))
  const masterColumns = [
    { title: 'Мастер', dataIndex: 'name', key: 'name' },
    { title: 'Выполнено', dataIndex: 'completed', key: 'completed' },
    { title: 'В работе', dataIndex: 'in_progress', key: 'in_progress' },
    { title: 'Выручка', dataIndex: 'revenue', key: 'revenue', render: (v: number) => `${v.toFixed(2)} ₽` },
  ]
  return <Card title="Эффективность мастеров"><Table columns={masterColumns} dataSource={masterData} rowKey="name" pagination={false} /></Card>
}

const ClientsAnalyticsReport: React.FC<{ data: any }> = ({ data }) => {
  if (!data) return <Spin />
  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col span={12}><Card><Statistic title="Уникальные клиенты" value={data.unique_clients ?? 0} prefix={<TeamOutlined />} /></Card></Col>
        <Col span={12}><Card><Statistic title="Повторные клиенты" value={data.repeat_clients ?? 0} prefix={<CheckCircleOutlined />} /></Card></Col>
      </Row>
      {(data.top_clients?.length ?? 0) > 0 && (
        <Card title="Топ клиенты" style={{ marginTop: 16 }}>
          <List dataSource={data.top_clients} renderItem={(item: any) => (<List.Item><List.Item.Meta title={item.phone} description={`Заказов: ${item.orders}`} /><Badge count={item.orders} /></List.Item>)} />
        </Card>
      )}
    </div>
  )
}

const DevicesAnalyticsReport: React.FC<{ data: any }> = ({ data }) => {
  if (!data) return <Spin />
  const catData = Object.entries(data.by_category || {}).map(([name, v]: any) => ({ name, value: v.count }))
  const brandData = Object.entries(data.by_brand || {}).map(([name, v]: any) => ({ name, value: v.count }))
  const catTable = Object.entries(data.by_category || {}).map(([name, v]: any) => ({ name, count: v.count, revenue: v.revenue }))
  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col span={12}>
          <Card title="По категориям">
            <ResponsiveContainer width="100%" height={250}>
              <PieChart><Pie data={catData} cx="50%" cy="50%" outerRadius={80} dataKey="value" label>{catData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}</Pie><Tooltip /></PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col span={12}>
          <Card title="По брендам">
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={brandData}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" /><YAxis /><Tooltip /><Bar dataKey="value" fill="#722ed1" /></BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>
      <Card title="Категории: заказы и выручка" style={{ marginTop: 16 }} size="small">
        <Table dataSource={catTable} rowKey="name" pagination={false} columns={[
          { title: 'Категория', dataIndex: 'name', key: 'name' },
          { title: 'Заказов', dataIndex: 'count', key: 'count', sorter: (a: any, b: any) => a.count - b.count },
          { title: 'Выручка', dataIndex: 'revenue', key: 'revenue', render: (v: number) => `${v.toLocaleString('ru-RU')} ₽`, sorter: (a: any, b: any) => a.revenue - b.revenue },
          { title: 'Средний чек', key: 'avg', render: (_: any, r: any) => r.count > 0 ? `${Math.round(r.revenue / r.count).toLocaleString('ru-RU')} ₽` : '—' },
        ]} />
      </Card>
      {(data.top_models?.length ?? 0) > 0 && (
        <Card title="Топ-10 моделей" style={{ marginTop: 16 }} size="small">
          <List dataSource={data.top_models.slice(0, 10)} renderItem={(item: any) => (<List.Item><List.Item.Meta title={item[0]} /><Tag color="blue">{item[1]}</Tag></List.Item>)} />
        </Card>
      )}
    </div>
  )
}

const WarrantyReport: React.FC<{ data: any }> = ({ data }) => {
  if (!data) return <Spin />
  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col span={12}><Card><Statistic title="Всего гарантийных" value={data.total ?? 0} prefix={<CheckCircleOutlined />} valueStyle={{ color: '#1890ff' }} /></Card></Col>
        <Col span={12}><Card><Statistic title="Гарантия истекла" value={data.expired_warranty ?? 0} prefix={<WarningOutlined />} valueStyle={{ color: '#faad14' }} /></Card></Col>
      </Row>
      {(data.orders?.length ?? 0) > 0 && (
        <Card title="Гарантийные заказы" style={{ marginTop: 16 }}>
          <Table dataSource={data.orders} rowKey="id" pagination={false} columns={[
            { title: 'Заказ', dataIndex: 'id', key: 'id', width: 60, render: (v: number) => `#${v}` },
            { title: 'Клиент', dataIndex: 'client', key: 'client' },
            { title: 'Устройство', dataIndex: 'device', key: 'device' },
            { title: 'Статус', dataIndex: 'status', key: 'status' },
            { title: 'Гарантия', dataIndex: 'warranty_days', key: 'warranty_days', width: 80, render: (v: number) => v > 0 ? `${v} д.` : '—' },
            { title: 'До', dataIndex: 'warranty_until', key: 'warranty_until', render: (v: string) => v ? new Date(v).toLocaleDateString('ru-RU') : '—' },
            { title: 'Осталось', dataIndex: 'days_left', key: 'days_left', render: (v: number) => v > 0 ? <Tag color={v <= 7 ? 'red' : v <= 14 ? 'orange' : 'green'}>{v} дн.</Tag> : <Tag>—</Tag> },
          ]} />
        </Card>
      )}
    </div>
  )
}

const TimeAnalyticsReport: React.FC<{ data: any }> = ({ data }) => {
  if (!data) return <Spin />
  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col span={8}><Card><Statistic title="Выдано заказов" value={data.total_issued ?? 0} valueStyle={{ color: '#1890ff' }} /></Card></Col>
         <Col span={8}><Card><Statistic title="Средний срок ремонта" value={data.avg_repair_days ?? 0} suffix="дней" valueStyle={{ color: '#52c41a' }} /></Card></Col>
        <Col span={8}><Card><Statistic title="Средний срок (часы)" value={data.avg_repair_hours ?? 0} suffix="ч" precision={1} valueStyle={{ color: '#722ed1' }} /></Card></Col>
      </Row>
      {(data.masters_avg?.length ?? 0) > 0 && (
        <Card title="Средний срок по мастерам" style={{ marginTop: 16 }} size="small">
          <Table dataSource={data.masters_avg} rowKey="master_id" pagination={false} columns={[
            { title: 'Мастер', dataIndex: 'master_name', key: 'master' },
            { title: 'Заказов', dataIndex: 'orders', key: 'orders' },
            { title: 'Средний срок', dataIndex: 'avg_days', key: 'avg', render: (v: number) => `${v} дн.` },
          ]} />
        </Card>
      )}
      <Card title={`Динамика (${data.period})`} style={{ marginTop: 16 }}>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data.data || []}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="date" /><YAxis /><Tooltip /><Legend /><Line type="monotone" dataKey="orders" stroke="#1890ff" name="Заказы" strokeWidth={2} /><Line type="monotone" dataKey="revenue" stroke="#52c41a" name="Выручка" strokeWidth={2} /></LineChart>
        </ResponsiveContainer>
      </Card>
    </div>
  )
}

import { useNavigate } from 'react-router-dom'

const SalaryReport: React.FC = () => {
  const navigate = useNavigate()
  const [employees, setEmployees] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedEmployee, setSelectedEmployee] = useState<number | null>(null)
  const [detailData, setDetailData] = useState<any>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [payModalOpen, setPayModalOpen] = useState(false)
  const [payAmount, setPayAmount] = useState<string>('')
  const [payComment, setPayComment] = useState('')
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs]>([
    dayjs().startOf('month'),
    dayjs()
  ])

  // Загрузка списка сотрудников
  useEffect(() => {
    loadEmployees()
  }, [dateRange])

  const loadEmployees = async () => {
    setLoading(true)
    try {
      const data = await getEmployeesSalaryReport(
        dateRange[0].format('YYYY-MM-DD'),
        dateRange[1].format('YYYY-MM-DD')
      )
      setEmployees(data || [])
    } catch (e: any) {
      message.error('Ошибка загрузки отчёта по зарплате')
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  // Загрузка детализации по сотруднику
  const loadEmployeeDetail = async (userId: number) => {
    setDetailLoading(true)
    try {
      const data = await getEmployeeSalaryDetail(
        userId,
        dateRange[0].format('YYYY-MM-DD'),
        dateRange[1].format('YYYY-MM-DD')
      )
      setDetailData(data)
      setSelectedEmployee(userId)
    } catch (e: any) {
      message.error('Ошибка загрузки детализации')
      console.error(e)
    } finally {
      setDetailLoading(false)
    }
  }

  const handlePaySalary = async () => {
    if (!selectedEmployee || !payAmount) return
    
    const amount = parseFloat(payAmount)
    if (isNaN(amount) || amount <= 0) {
      message.error('Введите корректную сумму')
      return
    }
    
    try {
      const result = await paySalary(selectedEmployee, amount, payComment || undefined)
      message.success(`✅ ${result.message}`)
      setPayModalOpen(false)
      setPayAmount('')
      setPayComment('')
      // Перезагружаем детализацию заново с теми же датами
      setDetailLoading(true)
      const updatedData = await getEmployeeSalaryDetail(
        selectedEmployee,
        dateRange[0].format('YYYY-MM-DD'),
        dateRange[1].format('YYYY-MM-DD')
      )
      setDetailData(updatedData)
      setDetailLoading(false)
    } catch (e: any) {
      message.error(e.response?.data?.detail || 'Ошибка выплаты')
      setDetailLoading(false)
    }
  }

  const handleDateChange = (dates: any) => {
    if (dates && dates[0] && dates[1]) {
      setDateRange([dates[0], dates[1]])
    }
  }

  const columns = [
    { title: 'Сотрудник', dataIndex: 'username', key: 'username', width: 150 },
    { title: 'Роль', dataIndex: 'role', key: 'role', width: 120 },
    { title: 'Заказов', dataIndex: 'orders_count', key: 'orders_count', width: 100, align: 'center' as const },
    {
      title: 'Начислено',
      dataIndex: 'total_accrued',
      key: 'total_accrued',
      width: 120,
      align: 'right' as const,
      render: (v: number) => <span style={{ color: '#52c41a', fontWeight: 600 }}>+{v.toFixed(2)} ₽</span>,
    },
    {
      title: 'Удержания',
      dataIndex: 'total_deductions',
      key: 'total_deductions',
      width: 120,
      align: 'right' as const,
      render: (v: number) => <span style={{ color: '#f5222d', fontWeight: 600 }}>-{v.toFixed(2)} ₽</span>,
    },
    {
      title: 'К выплате',
      dataIndex: 'net_amount',
      key: 'net_amount',
      width: 130,
      align: 'right' as const,
      render: (v: number) => (
        <span style={{ color: v >= 0 ? '#1890ff' : '#f5222d', fontWeight: 'bold', fontSize: 14 }}>
          {v.toFixed(2)} ₽
        </span>
      ),
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 100,
      render: (_: any, r: any) => (
        <Button size="small" onClick={() => loadEmployeeDetail(r.user_id)}>
          Детализация
        </Button>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Space>
          <Text strong>Период:</Text>
          <DatePicker.RangePicker
            value={dateRange}
            onChange={handleDateChange}
            presets={[
              { label: 'Сегодня', value: [dayjs(), dayjs()] },
              { label: 'Неделя', value: [dayjs().subtract(7, 'day'), dayjs()] },
              { label: 'Месяц', value: [dayjs().startOf('month'), dayjs()] },
              { label: 'Квартал', value: [dayjs().startOf('quarter'), dayjs()] },
              { label: 'Год', value: [dayjs().startOf('year'), dayjs()] },
            ]}
          />
        </Space>
        <Button onClick={loadEmployees} icon={<ReloadOutlined />}>Обновить</Button>
      </div>

      <Card title="Сотрудники">
        {loading ? <Spin /> : (
          <Table
            columns={columns}
            dataSource={employees}
            rowKey="user_id"
            pagination={false}
            size="middle"
            summary={(rows) => {
              const totalAccrued = rows.reduce((sum, r) => sum + r.total_accrued, 0)
              const totalDeductions = rows.reduce((sum, r) => sum + r.total_deductions, 0)
              const totalNet = rows.reduce((sum, r) => sum + r.net_amount, 0)
              const totalOrders = rows.reduce((sum, r) => sum + r.orders_count, 0)
              return (
                <Table.Summary fixed>
                  <Table.Summary.Row style={{ background: 'rgba(0,0,0,0.03)', fontWeight: 600 }}>
                    <Table.Summary.Cell index={0} colSpan={2}>Итого:</Table.Summary.Cell>
                    <Table.Summary.Cell index={1}>{totalOrders}</Table.Summary.Cell>
                    <Table.Summary.Cell index={2}><span style={{ color: '#52c41a' }}>+{totalAccrued.toFixed(2)} ₽</span></Table.Summary.Cell>
                    <Table.Summary.Cell index={3}><span style={{ color: '#f5222d' }}>-{totalDeductions.toFixed(2)} ₽</span></Table.Summary.Cell>
                    <Table.Summary.Cell index={4}><span style={{ color: '#1890ff', fontSize: 15 }}>{totalNet.toFixed(2)} ₽</span></Table.Summary.Cell>
                    <Table.Summary.Cell index={5}></Table.Summary.Cell>
                  </Table.Summary.Row>
                </Table.Summary>
              )
            }}
          />
        )}
      </Card>

      {/* Модальное окно с детализацией */}
      <Modal
        title={
          <Space>
            <span>📋 Детализация зарплаты</span>
            {detailData && <Tag color="blue">{detailData.username || employees.find(e => e.user_id === selectedEmployee)?.username || ''}</Tag>}
          </Space>
        }
        open={!!selectedEmployee}
        onCancel={() => { setSelectedEmployee(null); setDetailData(null) }}
        width={900}
        footer={
          <Space>
            <Button onClick={() => { setSelectedEmployee(null); setDetailData(null) }}>Закрыть</Button>
            {detailData?.summary?.balance > 0 && (
              <Button 
                type="primary" 
                danger 
                onClick={async () => {
                  // Сначала обновляем данные
                  setDetailLoading(true)
                  try {
                    const updatedData = await getEmployeeSalaryDetail(
                      selectedEmployee,
                      dateRange[0].format('YYYY-MM-DD'),
                      dateRange[1].format('YYYY-MM-DD')
                    )
                    setDetailData(updatedData)
                    setPayAmount(updatedData.summary.balance.toFixed(2))
                    setPayModalOpen(true)
                  } catch (e: any) {
                    message.error('Ошибка обновления данных')
                  } finally {
                    setDetailLoading(false)
                  }
                }}
              >
                💵 Выплатить {detailData.summary.balance.toFixed(2)} ₽
              </Button>
            )}
          </Space>
        }
      >
        {detailLoading ? <Spin /> : detailData && (
          <div>
            {/* Итоги */}
            <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
              <Col span={6}>
                <Card size="small">
                  <Statistic title="Начислено" value={detailData.summary?.total_accrued || 0} precision={2} suffix="₽" valueStyle={{ color: '#52c41a', fontSize: 18 }} />
                </Card>
              </Col>
              <Col span={6}>
                <Card size="small">
                  <Statistic title="Удержано" value={Math.abs(detailData.summary?.total_deducted || 0)} precision={2} suffix="₽" valueStyle={{ color: '#f5222d', fontSize: 18 }} />
                </Card>
              </Col>
              <Col span={6}>
                <Card size="small">
                  <Statistic title="Выплачено" value={detailData.summary?.total_paid || 0} precision={2} suffix="₽" valueStyle={{ color: '#fa8c16', fontSize: 18 }} />
                </Card>
              </Col>
              <Col span={6}>
                <Card size="small">
                  <Statistic 
                    title="К выплате" 
                    value={detailData.summary?.balance || 0} 
                    precision={2} 
                    suffix="₽" 
                    valueStyle={{ color: (detailData.summary?.balance || 0) >= 0 ? '#1890ff' : '#f5222d', fontSize: 18 }} 
                  />
                </Card>
              </Col>
            </Row>

            {/* Таблица записей */}
            <Table
              dataSource={detailData.records || []}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              size="small"
              columns={[
                { title: 'Дата', dataIndex: 'created_at', key: 'created_at', width: 100, render: (v: string) => v?.split('T')[0] || '—' },
                {
                  title: 'Заказ', key: 'order', width: 120,
                  render: (_: any, r: any) => r.order ? (
                    <div>
                      <Text strong>#{r.order.id}</Text><br />
                      <Text type="secondary" style={{ fontSize: 11 }}>{r.order.client_name}</Text>
                    </div>
                  ) : <Text type="secondary">—</Text>,
                },
                { title: 'Период', key: 'period', width: 150, render: (_: any, r: any) =>
                  r.period_start && r.period_end ? `${r.period_start.split('T')[0]} — ${r.period_end.split('T')[0]}` : '—'
                },
                { title: 'Тип', dataIndex: 'status', key: 'status', width: 100, render: (s: string) => {
                  const config: any = { accrued: { color: 'green', text: 'Начислено' }, deducted: { color: 'red', text: 'Удержано' }, paid: { color: 'orange', text: 'Выплачено' } }
                  return <Tag color={config[s]?.color}>{config[s]?.text || s}</Tag>
                }},
                { title: 'Сумма', dataIndex: 'calculated_amount', key: 'amount', width: 100, align: 'right' as const, render: (v: number) => (
                  <Text strong style={{ color: v >= 0 ? '#52c41a' : '#f5222d' }}>{v >= 0 ? '+' : ''}{v.toFixed(2)} ₽</Text>
                )},
                {
                  title: 'Комментарий',
                  dataIndex: 'comment',
                  key: 'comment',
                  ellipsis: true,
                  render: (comment: string, r: any) => {
                    // Ищем ссылки на заказы в формате "заказ #9" или "заказ 9"
                    const orderMatch = comment?.match(/заказ\s*#?\s*(\d+)/i)
                    if (orderMatch) {
                      const orderId = parseInt(orderMatch[1])
                      return (
                        <a onClick={() => navigate(`/orders/${orderId}`)} style={{ cursor: 'pointer' }}>
                          {comment}
                        </a>
                      )
                    }
                    return comment || '—'
                  },
                },
              ]}
            />
          </div>
        )}
      </Modal>

      {/* Модальное окно выплаты */}
      <Modal
        title="💵 Выплата зарплаты"
        open={payModalOpen}
        onCancel={() => { setPayModalOpen(false); setPayAmount(''); setPayComment('') }}
        onOk={handlePaySalary}
        okText="Выплатить"
        cancelText="Отмена"
      >
        <div style={{ marginBottom: 16 }}>
          <Text strong>Сотрудник:</Text>{' '}
          <Tag color="blue">{employees.find(e => e.user_id === selectedEmployee)?.username}</Tag>
        </div>
        <div style={{ marginBottom: 16 }}>
          <Text strong>К выплате:</Text>{' '}
          <Text style={{ color: '#1890ff', fontSize: 18, fontWeight: 'bold' }}>
            {detailData?.summary?.balance?.toFixed(2) || '0.00'} ₽
          </Text>
        </div>
        <div style={{ marginBottom: 16 }}>
          <Text strong>Сумма:</Text>
          <Input
            value={payAmount}
            onChange={(e) => setPayAmount(e.target.value)}
            placeholder="Введите сумму"
            type="number"
            size="large"
            addonAfter="₽"
            style={{ marginTop: 8 }}
          />
        </div>
        <div style={{ marginBottom: 16 }}>
          <Text strong>Комментарий:</Text>
          <Input.TextArea
            value={payComment}
            onChange={(e) => setPayComment(e.target.value)}
            placeholder="Например: Выплата зарплаты за апрель 2026"
            rows={3}
            style={{ marginTop: 8 }}
          />
        </div>
      </Modal>
    </div>
  )
}

const DashboardSummaryReport: React.FC<{ data: any }> = ({ data }) => {
  if (!data || Object.keys(data).length === 0) return <div style={{textAlign:'center',padding:40}}>Нет данных</div>
  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col span={6}><Card><Statistic title="Заказов" value={data.total_orders || 0} prefix={<UnorderedListOutlined />} /></Card></Col>
        <Col span={6}><Card><Statistic title="Выдано" value={data.issued_orders || 0} prefix={<CheckCircleOutlined />} valueStyle={{ color: '#52c41a' }} /></Card></Col>
        <Col span={6}><Card><Statistic title="Выручка" value={data.total_revenue || 0} precision={2} prefix={<DollarOutlined />} suffix="₽" valueStyle={{ color: '#3f8600' }} /></Card></Col>
        <Col span={6}><Card><Statistic title="Ср. чек" value={data.avg_order_value || 0} precision={2} prefix={<RiseOutlined />} suffix="₽" /></Card></Col>
      </Row>
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={8}><Card><Statistic title="Мастеров" value={data.active_masters || 0} prefix={<ToolOutlined />} /></Card></Col>
        <Col span={8}><Card><Statistic title="Запчастей на складе" value={data.total_parts || 0} prefix={<ScanOutlined />} /></Card></Col>
        <Col span={8}><Card><Statistic title="Стоимость склада" value={data.parts_value || 0} precision={2} prefix={<WalletOutlined />} suffix="₽" /></Card></Col>
      </Row>
    </div>
  )
}

// ==================== ГЛАВНАЯ СТРАНИЦА ====================

const MarketingReport: React.FC<{ dateFrom?: string; dateTo?: string }> = ({ dateFrom, dateTo }) => {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setLoading(true)
    api.get('/reports/marketing', { params: { date_from: dateFrom, date_to: dateTo } })
      .then(r => setData(r.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [dateFrom, dateTo])

  if (loading) return <div style={{ padding: 24, textAlign: 'center' }}><Spin /></div>
  if (!data) return null

  const columns = [
    { title: 'Группа', dataIndex: 'name', key: 'name' },
    { title: 'Заказов', dataIndex: 'count', key: 'count', align: 'right' as const },
    { title: 'Выручка', dataIndex: 'revenue', key: 'revenue', align: 'right' as const, render: (v: number) => `${v.toFixed(0)} ₽` },
    { title: 'Средний чек', dataIndex: 'avg_check', key: 'avg', align: 'right' as const, render: (v: number) => `${v.toFixed(0)} ₽` },
    { title: 'Доля', dataIndex: 'share_pct', key: 'share', align: 'right' as const, render: (v: number) => `${v}%` },
  ]

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={12}><Statistic title="Всего заказов" value={data.total_orders} /></Col>
        <Col span={12}><Statistic title="Общая выручка" value={data.total_revenue} precision={0} suffix="₽" valueStyle={{ color: '#1890ff' }} /></Col>
      </Row>
      <Card title="По возрасту" size="small" style={{ marginBottom: 16 }}>
        <Table dataSource={data.age_groups} columns={columns} rowKey="name" pagination={false} size="small" />
      </Card>
      <Card title="По источникам" size="small">
        <Table dataSource={data.sources} columns={columns} rowKey="name" pagination={false} size="small" />
      </Card>
    </div>
  )
}

const REPORTS_CONFIG = [
  { key: 'dashboard', label: '📊 Дашборд', icon: <BarChartOutlined />, component: DashboardSummaryReport },
  { key: 'orders', label: '📋 Заказы', icon: <UnorderedListOutlined />, component: OrdersAnalyticsReport },
  { key: 'financial', label: '💰 Финансы', icon: <DollarOutlined />, component: FinancialReport },
  { key: 'employees', label: '👥 Сотрудники', icon: <TeamOutlined />, component: EmployeesReport },
  { key: 'salary', label: '💵 Зарплата', icon: <DollarOutlined />, component: SalaryReport },
  { key: 'clients', label: '👤 Клиенты', icon: <UserOutlined />, component: ClientsAnalyticsReport },
  { key: 'devices', label: '📱 Устройства', icon: <ScanOutlined />, component: DevicesAnalyticsReport },
  { key: 'warranty', label: '🛡 Гарантия', icon: <CheckCircleOutlined />, component: WarrantyReport },
  { key: 'time', label: '📅 Временная', icon: <CalendarOutlined />, component: TimeAnalyticsReport },
  { key: 'marketing', label: '📢 Маркетинг', icon: <TeamOutlined />, component: MarketingReport },
]

const ReportsPage: React.FC = () => {
  const [activeReport, setActiveReport] = useState('dashboard')
  const [loading, setLoading] = useState(false)
  const [reportData, setReportData] = useState<any>({})
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs]>([
    dayjs().startOf('month'),
    dayjs()
  ])
  const requestSeqRef = useRef(0)

  const loadData = useCallback(async () => {
    // Зарплатный отчёт использует свой компонент и собственную загрузку.
    if (activeReport === 'salary') {
      setReportData({})
      setLoading(false)
      return
    }

    const currentSeq = ++requestSeqRef.current
    setLoading(true)
    try {
      let result: any
      const params: Record<string, string> = {}
      if (dateRange[0]) params.date_from = dateRange[0].format('YYYY-MM-DD')
      if (dateRange[1]) params.date_to = dateRange[1].format('YYYY-MM-DD')
      
      switch (activeReport) {
        case 'dashboard':
          result = await api.get('/reports/dashboard-summary', { params })
          break
        case 'orders':
          result = await api.get('/reports/orders-analytics', { params })
          break
        case 'financial':
          result = await api.get('/reports/financial', { params })
          break
        case 'employees':
          result = await api.get('/reports/employees', { params })
          break
        case 'clients':
          result = await api.get('/reports/clients-analytics')
          break
        case 'devices':
          result = await api.get('/reports/devices-analytics')
          break
        case 'warranty':
          result = await api.get('/reports/warranty')
          break
        case 'time':
          result = await api.get('/reports/time-analytics', { params: { ...params, period: 'day' } })
          break
        case 'marketing':
          result = await api.get('/reports/marketing', { params })
          break
        default:
          result = { data: {} }
      }

      if (currentSeq === requestSeqRef.current) {
        setReportData(result.data)
      }
    } catch (error: any) {
      if (currentSeq === requestSeqRef.current) {
        message.error(error.response?.data?.detail || 'Ошибка загрузки отчёта')
        setReportData({})
      }
    } finally {
      if (currentSeq === requestSeqRef.current) {
        setLoading(false)
      }
    }
  }, [activeReport, dateRange])

  // Загрузка данных
  useEffect(() => {
    loadData()
  }, [loadData])

  const handleDateChange = (dates: any) => {
    if (dates && dates[0] && dates[1]) {
      setDateRange([dates[0], dates[1]])
    }
  }

  const dateFrom = dateRange[0]?.format('YYYY-MM-DD')
  const dateTo = dateRange[1]?.format('YYYY-MM-DD')

  const config = REPORTS_CONFIG.find(r => r.key === activeReport)
  const Component = config?.component || (() => <div>Отчёт не найден</div>)

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
        <h1 style={{ margin: 0 }}>📊 Отчёты</h1>
        <Space wrap>
          <DatePicker.RangePicker
            value={dateRange}
            onChange={handleDateChange}
            presets={[
              { label: 'Сегодня', value: [dayjs(), dayjs()] },
              { label: 'Неделя', value: [dayjs().subtract(7, 'day'), dayjs()] },
              { label: 'Месяц', value: [dayjs().startOf('month'), dayjs()] },
              { label: 'Квартал', value: [dayjs().subtract(3, 'month'), dayjs()] },
              { label: 'Год', value: [dayjs().startOf('year'), dayjs()] },
            ]}
          />
          <Button icon={<FilterOutlined />} onClick={loadData}>Обновить</Button>
        </Space>
      </div>
      <Row gutter={[16, 16]}>
        <Col xs={24} md={6}>
          <Card size="small">
            <List dataSource={REPORTS_CONFIG} renderItem={(item) => (
              <List.Item style={{ cursor: 'pointer', background: activeReport === item.key ? '#e6f7ff' : 'transparent', padding: '8px 12px', borderRadius: 4, marginBottom: 4 }} onClick={() => setActiveReport(item.key)}>
                <Space>{item.icon}<span style={{ fontWeight: activeReport === item.key ? 'bold' : 'normal' }}>{item.label}</span></Space>
              </List.Item>
            )} />
          </Card>
        </Col>
        <Col xs={24} md={18}>
          <Spin spinning={loading}><Component data={reportData} dateFrom={dateFrom} dateTo={dateTo} /></Spin>
        </Col>
      </Row>
    </div>
  )
}

export default ReportsPage
