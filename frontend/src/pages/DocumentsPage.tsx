import React, { useState, useEffect } from 'react'
import {
  Table, Button, Tag, Space, message, Card, Select, DatePicker, Input,
  Popconfirm, Tooltip, Typography, Row, Col, Divider
} from 'antd'
import {
  FilePdfOutlined, EyeOutlined, DeleteOutlined, ReloadOutlined,
  FileTextOutlined, FileDoneOutlined, FileSyncOutlined, StopOutlined,
  SearchOutlined
} from '@ant-design/icons'
import axios from 'axios'
import dayjs from 'dayjs'
import { useNavigate } from 'react-router-dom'

const { Title, Text } = Typography
const { RangePicker } = DatePicker

const api = axios.create({ baseURL: '/api' })
api.interceptors.request.use(c => {
  const t = localStorage.getItem('token')
  if (t) c.headers.Authorization = `Bearer ${t}`
  return c
})

const DOC_TYPES: Record<string, { label: string; icon: string; color: string }> = {
  receipt: { label: 'Квитанция', icon: '🧾', color: 'blue' },
  diagnostic_act: { label: 'Акт диагностики', icon: '🔍', color: 'orange' },
  work_act: { label: 'Акт работ', icon: '✅', color: 'green' },
  invoice: { label: 'Счёт', icon: '📄', color: 'purple' },
}

const STATUS_CONFIG: Record<string, { label: string; color: string }> = {
  generated: { label: 'Создан', color: 'blue' },
  sent: { label: 'Отправлен', color: 'cyan' },
  signed: { label: 'Подписан', color: 'green' },
  cancelled: { label: 'Отменён', color: 'default' },
}

const DocumentsPage: React.FC = () => {
  const navigate = useNavigate()
  const [documents, setDocuments] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)

  // Фильтры
  const [docType, setDocType] = useState<string | undefined>(undefined)
  const [status, setStatus] = useState<string | undefined>(undefined)
  const [dateRange, setDateRange] = useState<any>(null)
  const [search, setSearch] = useState('')

  useEffect(() => { loadDocuments() }, [page, pageSize, docType, status, dateRange])

  const loadDocuments = async () => {
    setLoading(true)
    try {
      const params: any = {
        skip: (page - 1) * pageSize,
        limit: pageSize,
      }
      if (docType) params.document_type = docType
      if (status) params.status = status
      if (dateRange) {
        params.date_from = dateRange[0].format('YYYY-MM-DD')
        params.date_to = dateRange[1].format('YYYY-MM-DD')
      }
      if (search) params.search = search

      const res = await api.get('/documents/', { params })
      setDocuments(res.data.items || [])
      setTotal(res.data.total || 0)
    } catch { message.error('Ошибка загрузки документов') }
    finally { setLoading(false) }
  }

  const handleStatusChange = async (docId: number, newStatus: string) => {
    try {
      await api.patch(`/documents/${docId}/status`, { status: newStatus })
      message.success(`Статус изменён на "${STATUS_CONFIG[newStatus]?.label}"`)
      loadDocuments()
    } catch { message.error('Ошибка обновления статуса') }
  }

  const handleDelete = async (docId: number) => {
    try {
      await api.delete(`/documents/${docId}`)
      message.success('Документ удалён')
      loadDocuments()
    } catch { message.error('Ошибка удаления') }
  }

  const handleDownload = (filename: string) => {
    window.open(`/api/documents/download?filename=${encodeURIComponent(filename)}`, '_blank')
  }

  const handleGenerate = async (orderId: number, type: string) => {
    try {
      const endpointMap: Record<string, string> = {
        receipt: `documents/receipt/${orderId}`,
        diagnostic_act: `documents/diagnostic-act/${orderId}`,
        work_act: `documents/work-act/${orderId}`,
        invoice: `documents/invoice/${orderId}`,
      }
      const res = await api.post(`/${endpointMap[type]}`)
      message.success('Документ сгенерирован')
      loadDocuments()
      return res.data
    } catch (e: any) { message.error(e.response?.data?.detail || 'Ошибка генерации') }
  }

  const columns = [
    {
      title: '№',
      key: 'index',
      width: 50,
      render: (_: any, __: any, idx: number) => (page - 1) * pageSize + idx + 1,
    },
    {
      title: 'Дата',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 140,
      render: (v: string) => (
        <Text style={{ fontSize: 12 }}>
          {dayjs(v).format('DD.MM.YYYY')}<br />
          <Text type="secondary" style={{ fontSize: 10 }}>{dayjs(v).format('HH:mm')}</Text>
        </Text>
      ),
    },
    {
      title: 'Заказ',
      key: 'order',
      width: 90,
      render: (_: any, r: any) => (
        <a onClick={() => navigate(`/orders/${r.order_id}`)} style={{ fontSize: 13, fontWeight: 600 }}>
          #{r.order_id}
        </a>
      ),
    },
    {
      title: 'Клиент',
      key: 'client',
      width: 160,
      render: (_: any, r: any) => (
        <div>
          <Text style={{ fontSize: 12, fontWeight: 500 }}>{r.order?.client_name || '—'}</Text>
          <br />
          <Text type="secondary" style={{ fontSize: 11 }}>{r.order?.client_phone || ''}</Text>
        </div>
      ),
    },
    {
      title: 'Тип',
      dataIndex: 'document_type',
      key: 'document_type',
      width: 150,
      render: (type: string) => {
        const cfg = DOC_TYPES[type] || { label: type, icon: '📄', color: 'default' }
        return (
          <Tag color={cfg.color} style={{ margin: 0 }}>
            {cfg.icon} {cfg.label}
          </Tag>
        )
      },
    },
    {
      title: 'Статус',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (s: string) => {
        const cfg = STATUS_CONFIG[s] || { label: s, color: 'default' }
        return <Tag color={cfg.color}>{cfg.label}</Tag>
      },
    },
    {
      title: 'Сумма',
      key: 'amount',
      width: 100,
      render: (_: any, r: any) => (
        <Text style={{ fontWeight: 600, fontSize: 13 }}>
          {r.order?.total_cost ? `${r.order.total_cost.toFixed(0)} ₽` : '—'}
        </Text>
      ),
    },
    {
      title: 'Устройство',
      key: 'device',
      width: 180,
      ellipsis: true,
      render: (_: any, r: any) => (
        <Text style={{ fontSize: 12 }}>{r.order?.device_model || '—'}</Text>
      ),
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 180,
      fixed: 'right' as const,
      render: (_: any, r: any) => (
        <Space size={4} wrap>
          <Tooltip title="Скачать PDF">
            <Button
              size="small"
              icon={<FilePdfOutlined />}
              onClick={() => handleDownload(r.filename)}
            />
          </Tooltip>

          <Tooltip title="Статус: Отправлен">
            <Button
              size="small"
              icon={<FileSyncOutlined />}
              disabled={r.status === 'sent' || r.status === 'signed'}
              onClick={() => handleStatusChange(r.id, 'sent')}
            />
          </Tooltip>

          <Tooltip title="Статус: Подписан">
            <Button
              size="small"
              icon={<FileDoneOutlined />}
              disabled={r.status === 'signed'}
              onClick={() => handleStatusChange(r.id, 'signed')}
            />
          </Tooltip>

          <Popconfirm
            title="Удалить документ?"
            onConfirm={() => handleDelete(r.id)}
          >
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={3} style={{ margin: 0 }}>📄 Документы</Title>
        <Button icon={<ReloadOutlined />} onClick={loadDocuments}>Обновить</Button>
      </div>

      {/* Фильтры */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={[12, 12]} align="middle">
          <Col xs={24} sm={12} md={6} lg={4}>
            <Select
              allowClear
              placeholder="Тип документа"
              style={{ width: '100%' }}
              value={docType}
              onChange={v => { setDocType(v); setPage(1) }}
              options={Object.entries(DOC_TYPES).map(([k, v]) => ({ label: `${v.icon} ${v.label}`, value: k }))}
            />
          </Col>
          <Col xs={24} sm={12} md={6} lg={4}>
            <Select
              allowClear
              placeholder="Статус"
              style={{ width: '100%' }}
              value={status}
              onChange={v => { setStatus(v); setPage(1) }}
              options={Object.entries(STATUS_CONFIG).map(([k, v]) => ({ label: v.label, value: k }))}
            />
          </Col>
          <Col xs={24} sm={12} md={8} lg={6}>
            <RangePicker
              style={{ width: '100%' }}
              value={dateRange}
              onChange={v => { setDateRange(v); setPage(1) }}
            />
          </Col>
          <Col xs={24} sm={12} md={8} lg={6}>
            <Input
              placeholder="Поиск по клиенту или заказу..."
              prefix={<SearchOutlined />}
              value={search}
              onChange={e => setSearch(e.target.value)}
              onPressEnter={() => { setPage(1); loadDocuments() }}
              allowClear
            />
          </Col>
          <Col xs={24} sm={12} md={6} lg={4}>
            <Button
              type="primary"
              onClick={() => { setPage(1); loadDocuments() }}
              style={{ width: '100%' }}
            >
              Применить
            </Button>
          </Col>
        </Row>
      </Card>

      {/* Статистика */}
      <Row gutter={12} style={{ marginBottom: 16 }}>
        {Object.entries(DOC_TYPES).map(([key, cfg]) => {
          const count = documents.filter(d => d.document_type === key).length
          return (
            <Col span={6} key={key}>
              <Card size="small">
                <Text type="secondary" style={{ fontSize: 11 }}>{cfg.icon} {cfg.label}</Text>
                <br />
                <Text style={{ fontSize: 20, fontWeight: 600 }}>{count}</Text>
                <Text type="secondary" style={{ fontSize: 11 }}> / {total}</Text>
              </Card>
            </Col>
          )
        })}
      </Row>

      {/* Таблица */}
      <Card size="small">
        <Table
          dataSource={documents}
          loading={loading}
          rowKey="id"
          columns={columns}
          scroll={{ x: 1200 }}
          pagination={{
            current: page,
            pageSize,
            total,
            showSizeChanger: true,
            showTotal: t => `Всего: ${t} документов`,
            onChange: (p, ps) => { setPage(p); setPageSize(ps) },
          }}
          locale={{ emptyText: 'Документы не найдены. Сгенерируйте документы из заказов.' }}
        />
      </Card>
    </div>
  )
}

export default DocumentsPage
