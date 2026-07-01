import React, { useState, useEffect } from 'react'
import {
  Table, Card, Space, Button, Input, DatePicker, Select, message,
  Typography, Row, Col, Statistic, Tag
} from 'antd'
import {
  DollarOutlined, TeamOutlined, ExportOutlined, ReloadOutlined,
  CalendarOutlined, UserOutlined
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { getSalaryReport, getUsers } from '../api'
import { useTheme } from '../contexts/ThemeContext'

const { Text, Title } = Typography
const { RangePicker } = DatePicker

const SalaryReportPage: React.FC = () => {
  const { mode } = useTheme()
  const isDark = mode === 'dark'
  
  const [loading, setLoading] = useState(false)
  const [report, setReport] = useState<any>({ records: [], total: 0, total_amount: 0 })
  const [users, setUsers] = useState<any[]>([])
  const [filters, setFilters] = useState({
    user_id: undefined as number | undefined,
    date_range: undefined as [dayjs.Dayjs, dayjs.Dayjs] | undefined,
    status: undefined as string | undefined,
  })

  useEffect(() => {
    loadUsers()
    loadReport()
  }, [])

  const loadUsers = async () => {
    try {
      const data = await getUsers()
      setUsers(data.filter((u: any) => u.role_name === 'master'))
    } catch {}
  }

  const loadReport = async () => {
    setLoading(true)
    try {
      const params: any = { limit: 100 }
      if (filters.user_id) params.user_id = filters.user_id
      if (filters.date_range) {
        params.date_from = filters.date_range[0].toISOString()
        params.date_to = filters.date_range[1].toISOString()
      }
      if (filters.status) params.status = filters.status
      
      const data = await getSalaryReport(params)
      setReport(data)
    } catch (e: any) {
      message.error('Ошибка загрузки отчёта')
    } finally {
      setLoading(false)
    }
  }

  const handleExport = () => {
    const csv = [
      ['Мастер', 'Заказ', 'Сумма', 'Статус', 'Дата', 'Комментарий'],
      ...report.records.map((r: any) => [
        r.user_name,
        r.order ? `#${r.order.id} ${r.order.client_name}` : '—',
        r.calculated_amount.toFixed(2),
        r.status,
        dayjs(r.created_at).format('DD.MM.YYYY HH:mm'),
        r.comment || ''
      ])
    ].map(row => row.join(';')).join('\n')
    
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `salary_report_${dayjs().format('YYYYMMDD')}.csv`
    link.click()
    message.success('Отчёт экспортирован')
  }

  const columns = [
    {
      title: 'Мастер',
      dataIndex: 'user_name',
      key: 'user_name',
      width: 150,
      render: (v: string, r: any) => (
        <Space>
          <UserOutlined />
          <Text strong>{v}</Text>
        </Space>
      ),
    },
    {
      title: 'Заказ',
      key: 'order',
      width: 200,
      render: (_: any, r: any) => r.order ? (
        <div>
          <Text strong>#{r.order.id}</Text>
          <br />
          <Text type="secondary" style={{ fontSize: 11 }}>
            {r.order.client_name} — {r.order.device_model}
          </Text>
        </div>
      ) : <Text type="secondary">—</Text>,
    },
    {
      title: 'Сумма',
      dataIndex: 'calculated_amount',
      key: 'calculated_amount',
      width: 100,
      render: (v: number) => (
        <Text strong style={{ color: v >= 0 ? '#52c41a' : '#f5222d' }}>
          {v >= 0 ? '+' : ''}{v.toFixed(2)}₽
        </Text>
      ),
    },
    {
      title: 'Статус',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (v: string) => {
        const colors: Record<string, string> = {
          accrued: 'blue',
          paid: 'green',
          advance: 'orange',
        }
        const labels: Record<string, string> = {
          accrued: 'Начислено',
          paid: 'Выплачено',
          advance: 'Аванс',
        }
        return <Tag color={colors[v] || 'default'}>{labels[v] || v}</Tag>
      },
    },
    {
      title: 'Дата',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 140,
      render: (v: string) => v ? dayjs(v).format('DD.MM.YYYY HH:mm') : '—',
    },
    {
      title: 'Комментарий',
      dataIndex: 'comment',
      key: 'comment',
      ellipsis: true,
    },
  ]

  const bg = isDark ? '#1a1a2e' : '#fff'
  const cardBg = isDark ? '#1e1e36' : '#fff'
  const textColor = isDark ? '#e8e8e8' : '#1a1a1a'

  return (
    <div style={{ background: bg, minHeight: '100vh', padding: '24px' }}>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={3} style={{ margin: 0, color: textColor }}>
          <DollarOutlined /> Отчёт по зарплате мастеров
        </Title>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={loadReport}>Обновить</Button>
          <Button icon={<ExportOutlined />} onClick={handleExport}>Экспорт CSV</Button>
        </Space>
      </div>

      {/* Фильтры */}
      <Card size="small" style={{ marginBottom: 16, background: cardBg, border: `1px solid ${isDark ? '#2a2a4a' : '#e8e8e8'}` }}>
        <Row gutter={16} align="middle">
          <Col>
            <Text>Мастер:</Text>
          </Col>
          <Col>
            <Select
              style={{ width: 200 }}
              placeholder="Все мастера"
              allowClear
              value={filters.user_id}
              onChange={(v) => setFilters({ ...filters, user_id: v })}
              options={users.map(u => ({ label: u.username, value: u.id }))}
            />
          </Col>
          <Col>
            <Text>Период:</Text>
          </Col>
          <Col>
            <RangePicker
              value={filters.date_range}
              onChange={(v) => setFilters({ ...filters, date_range: v as any })}
            />
          </Col>
          <Col>
            <Text>Статус:</Text>
          </Col>
          <Col>
            <Select
              style={{ width: 150 }}
              placeholder="Все статусы"
              allowClear
              value={filters.status}
              onChange={(v) => setFilters({ ...filters, status: v })}
              options={[
                { label: 'Начислено', value: 'accrued' },
                { label: 'Выплачено', value: 'paid' },
                { label: 'Аванс', value: 'advance' },
              ]}
            />
          </Col>
          <Col flex="auto" />
          <Col>
            <Button type="primary" onClick={loadReport}>Применить</Button>
          </Col>
        </Row>
      </Card>

      {/* Статистика */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={8}>
          <Card size="small" style={{ background: cardBg, border: `1px solid ${isDark ? '#2a2a4a' : '#e8e8e8'}` }}>
            <Statistic 
              title="Всего записей" 
              value={report.total} 
              prefix={<TeamOutlined />}
              valueStyle={{ color: textColor }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card size="small" style={{ background: cardBg, border: `1px solid ${isDark ? '#2a2a4a' : '#e8e8e8'}` }}>
            <Statistic 
              title="Общая сумма" 
              value={report.total_amount || 0} 
              precision={2}
              suffix="₽"
              prefix={<DollarOutlined />}
              valueStyle={{ color: (report.total_amount || 0) >= 0 ? '#52c41a' : '#f5222d' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card size="small" style={{ background: cardBg, border: `1px solid ${isDark ? '#2a2a4a' : '#e8e8e8'}` }}>
            <Statistic 
              title="Мастеров" 
              value={new Set(report.records?.map((r: any) => r.user_id)).size} 
              prefix={<UserOutlined />}
              valueStyle={{ color: textColor }}
            />
          </Card>
        </Col>
      </Row>

      {/* Таблица */}
      <Card 
        title={`📊 Записи (${report.records?.length || 0})`}
        size="small"
        style={{ background: cardBg, border: `1px solid ${isDark ? '#2a2a4a' : '#e8e8e8'}` }}
      >
        <Table
          columns={columns}
          dataSource={report.records}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 20, showSizeChanger: true }}
          size="small"
          scroll={{ x: 1000 }}
        />
      </Card>
    </div>
  )
}

export default SalaryReportPage
