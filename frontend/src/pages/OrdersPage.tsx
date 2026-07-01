import React, { useState, useEffect } from 'react'
import { 
  Table, Button, Input, Select, message, Space, Tag, Popconfirm, Tooltip, Badge, Card, Divider, Checkbox, Modal, List, Avatar, Typography, Form, Spin
} from 'antd'
import {
  PlusOutlined, EyeOutlined, EditOutlined, DeleteOutlined, ClockCircleOutlined,
  CheckCircleOutlined, FilterOutlined, SearchOutlined, SendOutlined, MessageOutlined,
  DownloadOutlined
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'
import axios from 'axios'
import {
  getOrders, deleteOrder, getUsers, changeOrderStatus,
  exportOrders, getOrderStatuses
} from '../api'
import { Order, OrderStatus, ORDER_STATUS_CONFIG } from '../types'
import { useTheme } from '../contexts/ThemeContext'
import { useWebSocket } from '../hooks/useWebSocket'

const { Text } = Typography
const commentsApi = axios.create({ baseURL: '/api/orders' })
commentsApi.interceptors.request.use(c => {
  const t = localStorage.getItem('token')
  if (t) c.headers.Authorization = `Bearer ${t}`
  return c
})

// Fallback статусы на случай если база пуста
const DEFAULT_STATUSES = [
  { value: 'new', label: 'Новый', color: '#e6f7ff', border: '#1890ff' },
  { value: 'diagnostics', label: 'Диагностика', color: '#fffbe6', border: '#faad14' },
  { value: 'agreed', label: 'Согласован', color: '#fff7e6', border: '#fa8c16' },
  { value: 'repair', label: 'В работе', color: '#f9f0ff', border: '#722ed1' },
  { value: 'waiting_parts', label: 'Ожидает запчасти', color: '#e6fffb', border: '#13c2c2' },
  { value: 'ready', label: 'Готов', color: '#f6ffed', border: '#52c41a' },
  { value: 'ready_pickup', label: 'На выдаче', color: '#fff0f6', border: '#eb2f96' },
  { value: 'issued', label: 'Выдан', color: '#fafafa', border: '#d9d9d9' },
  { value: 'issued_br', label: 'Выдан БР', color: '#f5f5f5', border: '#484949' },
  { value: 'cancelled', label: 'Отменён', color: '#fff1f0', border: '#f5222d' },
]

// Конвертируем статусы из БД в формат для UI
const convertStatuses = (statuses: any[]) => {
  if (!statuses || statuses.length === 0) return DEFAULT_STATUSES
  
  // Убираем дубликаты по code, оставляем первый (дефолтный если есть)
  const seen = new Set()
  return statuses
    .filter(s => s.is_active !== false) // Только активные
    .sort((a, b) => (b.is_default ? 1 : 0) - (a.is_default ? 1 : 0)) // Сначала дефолтные
    .map(s => ({
      value: s.code || s.name.toLowerCase().replace(/\s+/g, '_').replace(/ё/g, 'е'),
      label: s.name,
      color: s.color || '#1890ff',
      border: s.color || '#1890ff',
    }))
    .filter(s => {
      if (seen.has(s.value)) return false
      seen.add(s.value)
      return true
    })
}

const getStatusColor = (order: Order, statusList: any[]) => {
  if (order.is_warranty) return { bg: '#fff1f0', border: '#f5222d' } // Гарантия — красный
  const s = statusList.find(st => st.value === order.status)
  return s ? { bg: s.color, border: s.border } : { bg: '#fafafa', border: '#d9d9d9' }
}

const OrdersPage: React.FC = () => {
  const navigate = useNavigate()
  const { mode } = useTheme()
  const isDark = mode === 'dark'
  const [loading, setLoading] = useState(false)
  const [orders, setOrders] = useState<Order[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [searchText, setSearchText] = useState('')
  const [statusFilter, setStatusFilter] = useState<string | undefined>()
  const [masters, setMasters] = useState<any[]>([])
  const [masterFilter, setMasterFilter] = useState<number | undefined>()
  const [activeStatuses, setActiveStatuses] = useState<string[]>([])
  const [activeMasters, setActiveMasters] = useState<number[]>([])
  const [commentModal, setCommentModal] = useState<{open: boolean, orderId: number | null, orderName: string}>({open: false, orderId: null, orderName: ''})
  const [comments, setComments] = useState<any[]>([])
  const [commentText, setCommentText] = useState('')
  const [commentsLoading, setCommentsLoading] = useState(false)
  const [statusList, setStatusList] = useState<any[]>(DEFAULT_STATUSES)

  // Загружаем статусы из БД при старте
  useEffect(() => {
    loadStatuses()
  }, [])

  const loadStatuses = async () => {
    try {
      const data = await getOrderStatuses()
      const converted = convertStatuses(data)
      setStatusList(converted)
      // Активные статусы для фильтра
      setActiveStatuses(converted.map(s => s.value))
    } catch (e: any) {
      console.error('Ошибка загрузки статусов:', e)
      setStatusList(DEFAULT_STATUSES)
      setActiveStatuses(DEFAULT_STATUSES.map(s => s.value))
    }
  }

  // WebSocket для real-time обновлений
  const handleWebSocketMessage = (wsMsg: any) => {
    if (window.CustomEvent) try { window.dispatchEvent(new CustomEvent("crm-notify", { detail: wsMsg })) } catch(e) {}
    if (wsMsg.type === 'order_status_changed') {
      // Обновляем заказ в таблице
      setOrders(prev => prev.map(o => o.id === wsMsg.order_id ? wsMsg.order : o))
      message.success(`Заказ #${wsMsg.order_id}: статус изменён на "${wsMsg.order.status}"`)
    }
  }

  useWebSocket({
    onMessage: handleWebSocketMessage,
    autoReconnect: true,
    reconnectInterval: 5000,
  })

  useEffect(() => { fetchOrders(); loadMasters() }, [statusFilter, masterFilter, page, pageSize])

  const loadMasters = async () => {
    try {
      const data = await getUsers()
      const items = data.items || data
      setMasters(items.filter((u: any) => u.role_name === 'master'))
    } catch {}
  }

  const fetchOrders = async () => {
    setLoading(true)
    try {
      const params: any = { skip: (page - 1) * pageSize, limit: pageSize }
      if (statusFilter) params.status = statusFilter
      if (masterFilter) params.master_id = masterFilter
      if (searchText) params.search = searchText
      const data = await getOrders(params)
      if (data.items) { setOrders(data.items); setTotal(data.total) }
      else { setOrders(data); setTotal(data.length) }
    } catch { message.error('Ошибка загрузки заказов') }
    finally { setLoading(false) }
  }

  const handleStatusChange = async (orderId: number, newStatus: string) => {
    try {
      await changeOrderStatus(orderId, newStatus, `Статус изменён через таблицу`)
      message.success('Статус обновлён')
      fetchOrders()
    } catch (e: any) {
      message.error(e.response?.data?.detail || 'Ошибка смены статуса')
    }
  }

  const openComments = async (orderId: number, orderName: string) => {
    setCommentModal({ open: true, orderId, orderName })
    setCommentText('')
    setCommentsLoading(true)
    try {
      const res = await commentsApi.get(`/${orderId}/comments/`)
      setComments(res.data)
    } catch {}
    setCommentsLoading(false)
  }

  const sendComment = async () => {
    if (!commentText.trim() || !commentModal.orderId) return
    try {
      const res = await commentsApi.post(`/${commentModal.orderId}/comments/`, { text: commentText })
      setComments(prev => [res.data, ...prev])
      setCommentText('')
    } catch (e: any) { message.error('Ошибка отправки') }
  }

  const getQuickFilters = () => {
    const counts: Record<string, number> = {}
    orders.forEach(o => { counts[o.status] = (counts[o.status] || 0) + 1 })
    return statusList.map(s => ({
      value: s.value,
      label: s.label,
      color: s.border,
      count: counts[s.value] || 0,
      active: activeStatuses.includes(s.value) || activeStatuses.length === 0,
    }))
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 50,
      render: (id: number, record: Order) => <a onClick={() => navigate(`/orders/${record.id}`)}>#{id}</a>,
    },
    { title: 'Клиент', key: 'client', width: 140,
      render: (_: any, r: Order) => (
        <div onClick={() => navigate(`/orders/${r.id}`)} style={{ cursor: 'pointer' }}>
          <div style={{ fontSize: 12, fontWeight: 600, lineHeight: 1.2 }}>{r.client_name?.split(' ').slice(0, 2).join(' ') || '—'}</div>
          <div style={{ fontSize: 11, opacity: 0.7 }}>{r.client_phone}</div>
        </div>
      ),
    },
    { title: 'Устройство', key: 'device', width: 140,
      render: (_: any, r: Order) => (
        <div onClick={() => navigate(`/orders/${r.id}`)} style={{ cursor: 'pointer', fontSize: 12 }}>
          <div>{r.device_brand} {r.device_model?.split(' ').slice(0, 2).join(' ')}</div>
        </div>
      ),
    },
    { title: 'Неисправность', key: 'complaint', width: 160,
      render: (_: any, r: Order) => (
        <Text style={{ fontSize: 11 }}>{r.complaint?.substring(0, 40)}{r.complaint?.length > 40 ? '...' : ''}</Text>
      ),
    },
    { title: 'Статус', key: 'status', width: 140,
      render: (_: any, r: Order) => {
        const sc = statusList.find(s => s.value === r.status)
        return (
          <Select value={r.status} size="small" style={{ width: '100%', fontSize: 11 }}
            onChange={(v) => handleStatusChange(r.id, v)}
            options={statusList.map(s => ({ value: s.value, label: (
              <Space><span style={{display:'inline-block',width:6,height:6,borderRadius:'50%',background:s.border}}/>{s.label}</Space>
            ), key: s.value }))}
          />
        )
      },
    },
    { title: 'Мастер', dataIndex: 'master_username', key: 'master', width: 80,
      render: (v: string) => <span style={{fontSize: 11}}>{v || '—'}</span>
    },
    { title: 'Сумма', dataIndex: 'total_cost', key: 'total', width: 75,
      render: (v: number) => <span style={{fontSize: 11, fontWeight: 600}}>{v ? `${v.toFixed(0)}₽` : '—'}</span>
    },
    { title: 'Запчасти', dataIndex: 'parts_cost', key: 'parts', width: 75,
      render: (v: number) => <span style={{fontSize: 11}}>{v ? `${v.toFixed(0)}₽` : '—'}</span>
    },
    { title: 'Гарантия', key: 'warranty', width: 60,
      render: (_: any, r: Order) => r.is_warranty ? <Tag color="red" style={{margin:0,fontSize:10}}>🛡{r.warranty_days}д</Tag> : <span style={{fontSize:11,opacity:0.5}}>—</span>
    },
    { title: 'Дата', dataIndex: 'created_at', key: 'created', width: 55,
      render: (v: string) => <span style={{fontSize: 11}}>{v ? dayjs(v).format('DD.MM') : '—'}</span>
    },
    { title: '💬', key: 'comments', width: 36,
      render: (_: any, r: Order) => (
        <Tooltip title="Комментарии">
          <Button size="small" icon={<MessageOutlined />} style={{fontSize: 10, padding: '0 4px'}}
            onClick={(e) => { e.stopPropagation(); openComments(r.id, `${r.client_name} #${r.id}`) }} />
        </Tooltip>
      ),
    },
    { title: '⚡', key: 'actions', width: 60,
      render: (_: any, r: Order) => (
        <Space size={2}>
          <Tooltip title="Открыть"><Button size="small" icon={<EyeOutlined />} style={{fontSize:10,padding:'0 4px'}} onClick={() => navigate(`/orders/${r.id}`)} /></Tooltip>
          <Popconfirm title="Удалить?" onConfirm={async () => { try { await deleteOrder(r.id); message.success('Удалено'); fetchOrders() } catch {} }}>
            <Button size="small" icon={<DeleteOutlined />} danger style={{fontSize:10,padding:'0 4px'}} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ margin: 0 }}>📋 Заказы</h1>
        <Space>
          <Button icon={<DownloadOutlined />} onClick={async () => {
            const token = localStorage.getItem('token')
            try {
              const res = await fetch(exportOrders(), {
                headers: { Authorization: `Bearer ${token || ''}` }
              })
              const blob = await res.blob()
              const url = URL.createObjectURL(blob)
              const a = document.createElement('a')
              a.href = url
              a.download = `orders_${new Date().toISOString().slice(0,10)}.xlsx`
              a.click()
              URL.revokeObjectURL(url)
              message.success('Excel скачан')
            } catch { message.error('Ошибка экспорта') }
          }}>📥 Excel</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/orders/create')}>Новый заказ</Button>
        </Space>
      </div>

      {/* Быстрые фильтры */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Space wrap>
          <Tag color="default" style={{ cursor: 'pointer' }} onClick={() => { setActiveStatuses([]); setStatusFilter(undefined) }}>
            Все ({orders.length})
          </Tag>
          {getQuickFilters().map(f => (
            <Tag key={f.value} color={f.color} style={{ cursor: 'pointer', opacity: f.active ? 1 : 0.4 }}
              onClick={() => {
                if (activeStatuses.includes(f.value)) setActiveStatuses(prev => prev.filter(s => s !== f.value))
                else setActiveStatuses(prev => [...prev, f.value])
                setStatusFilter(activeStatuses.includes(f.value) ? undefined : f.value)
              }}>
              {f.label}: {f.count}
            </Tag>
          ))}
        </Space>
      </Card>

      {/* Поиск и фильтры */}
      <div style={{ marginBottom: 16, display: 'flex', gap: 8 }}>
        <Input placeholder="Поиск..." prefix={<SearchOutlined />} value={searchText}
          onChange={e => setSearchText(e.target.value)} onPressEnter={fetchOrders} style={{ width: 250 }} />
        <Select placeholder="Статус" allowClear value={statusFilter} onChange={setStatusFilter} style={{ width: 150 }}
          options={statusList.map(s => ({ value: s.value, label: s.label }))} />
        <Select placeholder="Мастер" allowClear value={masterFilter} onChange={setMasterFilter} style={{ width: 150 }}
          options={masters.map(m => ({ value: m.id, label: m.username }))} />
        <Button icon={<FilterOutlined />} onClick={fetchOrders}>Обновить</Button>
      </div>

      <Table
        dataSource={orders} rowKey="id" loading={loading}
        pagination={{ current: page, pageSize, total, showSizeChanger: true, onChange: (p, ps) => { setPage(p); setPageSize(ps) } }}
        columns={columns}
        size="small"
        onRow={(record) => {
          const sc = getStatusColor(record, statusList)
          return {
            onDoubleClick: () => navigate(`/orders/${record.id}`),
            style: {
              cursor: 'pointer',
              background: isDark ? `${sc.bg}22` : sc.bg,
              borderLeft: `3px solid ${sc.border}`,
            },
          }
        }}
      />

      {/* Модальное окно комментариев */}
      <Modal
        title={`💬 Комментарии — ${commentModal.orderName}`}
        open={commentModal.open}
        onCancel={() => setCommentModal({ open: false, orderId: null, orderName: '' })}
        footer={null}
        width={600}
      >
        <div style={{ maxHeight: 400, overflowY: 'auto', marginBottom: 12 }}>
          <Spin spinning={commentsLoading}>
            <List
              dataSource={comments}
              renderItem={(c: any) => (
                <List.Item style={{ flexDirection: 'column', alignItems: 'flex-start', padding: '8px 0' }}>
                  <div style={{ width: '100%' }}>
                    <Space>
                      <Avatar size="small" style={{ background: c.is_system ? '#faad14' : '#1890ff' }}>
                        {c.username?.[0]?.toUpperCase()}
                      </Avatar>
                      <Text strong>{c.username}</Text>
                      <Text type="secondary">{c.role_name}</Text>
                      <Text type="secondary">{dayjs(c.created_at).format('DD.MM HH:mm')}</Text>
                      {c.is_system && <Tag color="orange">системное</Tag>}
                    </Space>
                    <div style={{ marginLeft: 36, marginTop: 4 }}>
                      <Text>{c.text}</Text>
                    </div>
                  </div>
                </List.Item>
              )}
            />
          </Spin>
        </div>
        <Space.Compact style={{ width: '100%' }}>
          <Input
            value={commentText}
            onChange={e => setCommentText(e.target.value)}
            onPressEnter={sendComment}
            placeholder="Написать комментарий..."
          />
          <Button type="primary" icon={<SendOutlined />} onClick={sendComment} disabled={!commentText.trim()}>
          </Button>
        </Space.Compact>
      </Modal>
    </div>
  )
}

export default OrdersPage
