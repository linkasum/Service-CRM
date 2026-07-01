import React, { useState, useEffect } from 'react'
import { 
  Card, Descriptions, Tag, Button, Space, Modal, Form, Input, 
  message, Badge, Timeline, Spin, Select, List, Avatar, Typography, Row, Col, Tabs, Divider,
  Popconfirm, Table, Progress, Statistic, Checkbox
} from 'antd'
import { 
  ArrowLeftOutlined, FilePdfOutlined, PrinterOutlined,
  CheckCircleOutlined, ClockCircleOutlined, SendOutlined, MessageOutlined,
  UserOutlined, DollarOutlined, ShoppingCartOutlined, PaperClipOutlined, CameraOutlined,
  EditOutlined, PlusOutlined, CheckCircleFilled, DeleteOutlined, PayCircleOutlined,
  MinusCircleOutlined, ReloadOutlined, EyeOutlined, SearchOutlined
} from '@ant-design/icons'
import { useParams, useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'
import axios from 'axios'
import {
  getOrder, changeOrderStatus, updateOrder,
  generateReceipt, generateDiagnosticAct, generateWorkAct, generateInvoice,
  listOrderDocuments, downloadDocument, previewDocument, printDocument,
  getClientInfo,
  getPayments, createPayment, deletePayment, getPaymentSummary,
  getParts, partMovement,
  getServices, createService as createOrderService,
  getOrderStatuses,
  recalculateOrderSalary
} from '../api'
import api from '../api'
import { Order, OrderStatus, ORDER_STATUS_CONFIG } from '../types'
import { useTheme } from '../contexts/ThemeContext'

const { Text, Title } = Typography
const { TextArea } = Input

const commentsApi = axios.create({ baseURL: '/api/orders' })
commentsApi.interceptors.request.use(c => {
  const t = localStorage.getItem('token')
  if (t) c.headers.Authorization = `Bearer ${t}`
  return c
})

// Fallback статусы на случай если база пуста
const DEFAULT_STATUSES = [
  { value: 'new', label: '🆕 Новый', color: '#1890ff' },
  { value: 'diagnostics', label: '🔍 Диагностика', color: '#faad14' },
  { value: 'agreed', label: '✅ Согласование', color: '#fa8c16' },
  { value: 'repair', label: '🔧 В работе', color: '#722ed1' },
  { value: 'waiting_parts', label: '⏳ Ждёт запчасти', color: '#13c2c2' },
  { value: 'ready', label: '✨ Готов', color: '#52c41a' },
  { value: 'ready_pickup', label: '📦 На выдаче', color: '#eb2f96' },
  { value: 'issued', label: '✅ Выдан', color: '#d9d9d9' },
  { value: 'issued_br', label: '📋 Выдан БР', color: '#484949' },
  { value: 'cancelled', label: '❌ Отменён', color: '#f5222d' },
]

// Конвертируем статусы из БД в формат для UI
const convertStatuses = (statuses: any[]) => {
  if (!statuses || statuses.length === 0) return DEFAULT_STATUSES
  
  // Убираем дубликаты по code, оставляем первый (дефолтный если есть)
  const seen = new Set()
  return statuses
    .filter(s => s.is_active !== false)
    .sort((a, b) => (b.is_default ? 1 : 0) - (a.is_default ? 1 : 0)) // Сначала дефолтные
    .map(s => ({
      value: s.code || s.name.toLowerCase().replace(/\s+/g, '_').replace(/ё/g, 'е'),
      label: s.name,
      color: s.color || '#1890ff',
    }))
    .filter(s => {
      if (seen.has(s.value)) return false
      seen.add(s.value)
      return true
    })
}

const OrderDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { mode } = useTheme()
  const isDark = mode === 'dark'
  
  // Тема: светлая — чистые цвета, тёмная — тёмные
  const bg = isDark ? '#1a1a2e' : '#f0f2f5'
  const sideBg = isDark ? '#16213e' : '#ffffff'
  const mainBg = isDark ? '#1a1a2e' : '#ffffff'
  const borderColor = isDark ? '#2a2a4a' : '#e8e8e8'
  const textColor = isDark ? '#e8e8e8' : '#1a1a1a'
  const textSecondary = isDark ? '#999' : '#8c8c8c'
  const cardBg = isDark ? '#1e1e36' : '#ffffff'
  const inputBg = isDark ? '#2a2a4a' : '#ffffff'
  const headerBg = isDark ? '#0f0f23' : '#ffffff'
  const hoverBg = isDark ? '#2a2a4a' : '#f5f5f5'

  const [order, setOrder] = useState<Order | null>(null)
  const [loading, setLoading] = useState(true)
  const [orderDocs, setOrderDocs] = useState<any[]>([])
  const [comments, setComments] = useState<any[]>([])
  const [commentText, setCommentText] = useState('')
  const [commentsLoading, setCommentsLoading] = useState(false)
  const [clientInfo, setClientInfo] = useState<any>(null)
  const [clientLoading, setClientLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('general')
  const [payments, setPayments] = useState<any[]>([])
  const [paymentsLoading, setPaymentsLoading] = useState(false)
  const [paymentSummary, setPaymentSummary] = useState<any>(null)
  const [paymentModal, setPaymentModal] = useState(false)
  const [paymentForm] = Form.useForm()
  const [printing, setPrinting] = useState(false)
  const [paymentType, setPaymentType] = useState('prepayment')
  const [orderParts, setOrderParts] = useState<any[]>([])
  const [addPartModal, setAddPartModal] = useState(false)
  const [availableParts, setAvailableParts] = useState<any[]>([])
  const [addPartForm] = Form.useForm()
  const [availableServices, setAvailableServices] = useState<any[]>([])
  const [addServiceModal, setAddServiceModal] = useState(false)
  const [addServiceForm] = Form.useForm()

  // Модалки редактирования
  const [editClientModal, setEditClientModal] = useState(false)
  const [editClientForm] = Form.useForm()
  const [editOrderModal, setEditOrderModal] = useState(false)
  const [editOrderForm] = Form.useForm()
  const [editAssignmentModal, setEditAssignmentModal] = useState(false)
  const [editAssignmentForm] = Form.useForm()
  const [users, setUsers] = useState<any[]>([])
  const [statusList, setStatusList] = useState<any[]>(DEFAULT_STATUSES)
  const [ageGroups, setAgeGroups] = useState<any[]>([])
  const [sources, setSources] = useState<any[]>([])

  // Загружаем статусы из БД при старте
  useEffect(() => {
    loadStatuses()
    loadAgeGroups()
    loadSources()
  }, [])

  const loadStatuses = async () => {
    try {
      const data = await getOrderStatuses()
      const converted = convertStatuses(data)
      setStatusList(converted)
    } catch (e: any) {
      console.error('Ошибка загрузки статусов:', e)
      setStatusList(DEFAULT_STATUSES)
    }
  }

  useEffect(() => {
    if (id) {
      loadOrder()
      loadDocuments()
      loadComments()
      loadPayments()
      loadOrderParts()
      loadUsers()
    }
  }, [id])

  const loadUsers = async () => {
    try {
      const { getUsers } = await import('../api')
      const data = await getUsers()
      setUsers((data.items || data).filter((u: any) => u.is_active))
    } catch {}
  }

  const loadAgeGroups = async () => {
    try {
      const res = await api.get('/settings/age-groups')
      const data = Array.isArray(res.data) ? res.data : (res.data.items || [])
      setAgeGroups(data.map((g: any) => ({ value: g.name || g.value, label: g.name || g.label || g.value })))
    } catch { /* API недоступен — используем пустой список */ }
  }

  const loadSources = async () => {
    try {
      const res = await api.get('/settings/client-sources')
      const data = Array.isArray(res.data) ? res.data : (res.data.items || [])
      setSources(data.map((s: any) => ({ value: s.name || s.value, label: s.name || s.label || s.value })))
    } catch { /* API недоступен — используем пустой список */ }
  }

  const loadOrder = async () => {
    setLoading(true)
    try {
      const data = await getOrder(Number(id))
      setOrder(data)
      if ((data as any).client_phone) loadClientInfo((data as any).client_phone)
    } catch { message.error('Ошибка загрузки заказа') }
    finally { setLoading(false) }
  }

  const loadComments = async () => {
    if (!id) return
    setCommentsLoading(true)
    try {
      const res = await commentsApi.get(`/${id}/comments/`)
      setComments(res.data)
    } catch {}
    setCommentsLoading(false)
  }

  const sendComment = async () => {
    if (!commentText.trim() || !id) return
    try {
      const res = await commentsApi.post(`/${id}/comments/`, { text: commentText })
      setComments(prev => [res.data, ...prev])
      setCommentText('')
    } catch { message.error('Ошибка отправки') }
  }

  const loadClientInfo = async (phone: string) => {
    setClientLoading(true)
    try {
      const data = await getClientInfo(phone)
      setClientInfo(data)
    } catch {}
    setClientLoading(false)
  }

  const loadDocuments = async () => {
    try {
      const docs = await listOrderDocuments(Number(id))
      setOrderDocs(docs)
    } catch {}
  }

  const loadPayments = async () => {
    if (!id) return
    setPaymentsLoading(true)
    try {
      const [payList, summary] = await Promise.all([
        getPayments({ order_id: Number(id) }),
        getPaymentSummary(Number(id)),
      ])
      setPayments(payList)
      setPaymentSummary(summary)
    } catch {}
    setPaymentsLoading(false)
  }

  const handlePayment = async (type: string) => {
    paymentForm.resetFields()
    setPaymentType(type)
    const remaining = paymentSummary?.remaining || 0
    const totalCost = paymentSummary?.total_cost || 0
    const totalPaid = paymentSummary?.total_paid || 0
    
    let defaultAmount = 0
    if (type === 'final') {
      defaultAmount = remaining > 0 ? remaining : totalCost
    } else if (type === 'prepayment') {
      defaultAmount = remaining > 0 ? remaining : totalCost
    } else if (type === 'refund') {
      defaultAmount = totalPaid > 0 ? totalPaid : 0
    }
    
    paymentForm.setFieldsValue({ payment_type: type, method: 'cash', amount: defaultAmount || 0 })
    setPaymentModal(true)
  }

  const getPaymentModalTitle = (type: string) => {
    const titles: Record<string, string> = {
      prepayment: '💰 Предоплата',
      final: '💵 Оплата заказа',
      refund: '↩️ Возврат средств',
      expense: '📋 Расход',
    }
    return titles[type] || '💰 Платёж'
  }

  const submitPayment = async () => {
    const values = await paymentForm.validateFields()
    const pType = values.payment_type
    setPrinting(true)
    
    try {
      const token = localStorage.getItem('token') || ''
      const oid = Number(id)

      // Создаём платёж (бэкенд сам создаст cash-транзакцию и обработает возврат/зарплату)
      await createPayment({ order_id: oid, ...values })
      
      // Финальная оплата: выдача заказа
      if (pType === 'final') {
        try { await changeOrderStatus(oid, 'issued') } catch {}
        
        // Авто-начисление зарплаты
        try {
          const salaryRes = await api.post(`/salary/assignment/auto-assign/${id}`)
          if (salaryRes.data.salary_amount > 0) {
            message.success(`Зарплата: ${salaryRes.data.salary_amount}₽`)
          }
        } catch {}
      }
      
      // Печать документов через <a> клик (обходит popup blocker)
      const docTemplates: Record<string, string> = {
        print_receipt: 'receipt',
        print_diagnostic: 'diagnostic_act',
        print_act: 'work_act',
        print_invoice: 'invoice',
      }
      for (const [key, template] of Object.entries(docTemplates)) {
        if (values[key]) {
          const a = document.createElement('a')
          a.href = `/api/documents/print/${oid}/${template}?token=${token}`
          a.target = '_blank'
          a.rel = 'noopener noreferrer'
          document.body.appendChild(a)
          a.click()
          document.body.removeChild(a)
        }
      }
      
      message.success('Платёж проведён')
      setPaymentModal(false)
      loadPayments()
      loadOrder()
      loadComments()
    } catch (e: any) {
      message.error(e.response?.data?.detail || 'Ошибка платежа')
    } finally {
      setPrinting(false)
    }
  }

  const handleDeletePayment = async (payId: number) => {
    try {
      await deletePayment(payId)
      message.success('Платёж удалён')
      loadPayments()
      loadOrder()
      loadComments()
    } catch { message.error('Ошибка удаления') }
  }

  const loadOrderParts = async () => {
    if (!id) return
    try {
      const parts = await getParts()
      const items = parts.items || parts
      setAvailableParts(items.filter((p: any) => p.quantity > 0))
    } catch {}
  }

  const [serviceNameInput, setServiceNameInput] = useState('')

  const loadServicesForOrder = async () => {
    try {
      const data = await getServices({ status: 'active' })
      setAvailableServices(data.items || [])
    } catch {}
  }

  const handleAddService = async () => {
    const values = await addServiceForm.validateFields()
    let serviceId = values.service_id
    let serviceName = ''
    let servicePrice = 0

    const existingSvc = availableServices.find((s: any) => s.id === serviceId)
    if (existingSvc) {
      serviceName = existingSvc.name
      servicePrice = existingSvc.price
    } else {
      // Creating new service on the fly
      const name = (values.service_id || '').toString().trim()
      if (!name) return
      try {
        const createRes = await axios.post('/api/services/', {
          name, price: values.price || 0, status: 'active',
        }, { headers: { Authorization: 'Bearer ' + (localStorage.getItem('token') || '') } })
        serviceId = createRes.data.id
        serviceName = createRes.data.name
        servicePrice = createRes.data.price
        setAvailableServices(prev => [...prev, createRes.data])
        message.success('Услуга создана и добавлена')
      } catch (e: any) {
        message.error(e.response?.data?.detail || 'Ошибка создания услуги')
        return
      }
    }

    try {
      await axios.post('/api/order-services/', {
        order_id: Number(id),
        service_id: serviceId,
        service_name: serviceName,
        price_at_order: values.price || servicePrice,
        quantity: values.quantity || 1,
        comment: values.comment,
      }, { headers: { Authorization: 'Bearer ' + (localStorage.getItem('token') || '') } })
      message.success('Услуга добавлена')
      setAddServiceModal(false)
      addServiceForm.resetFields()
      loadOrder()
      loadComments()
    } catch (e: any) {
      message.error(e.response?.data?.detail || 'Ошибка')
    }
  }

  const handleAddPart = async () => {
    const values = await addPartForm.validateFields()
    try {
      await partMovement(values.part_id, 'write_off', values.quantity, Number(id))
      message.success('Запчасть добавлена')
      setAddPartModal(false)
      addPartForm.resetFields()
      loadOrderParts()
      loadOrder()
      loadComments()
    } catch (e: any) {
      message.error(e.response?.data?.detail || 'Ошибка')
    }
  }

  const handleRecalculateSalary = async () => {
    if (!order?.master_id) {
      message.warning('Мастер не назначен')
      return
    }
    try {
      const result = await recalculateOrderSalary(Number(id))
      message.success(`💰 ${result.message}`)
    } catch (e: any) {
      message.error(e.response?.data?.detail || 'Ошибка начисления зарплаты')
    }
  }

  const handleStatusChange = async (newStatus: string) => {
    if (!order || !id) return
    try {
      await changeOrderStatus(Number(id), newStatus, `Статус изменён через карточку`)
      message.success('Статус обновлён')
      loadOrder()
      loadComments()
    } catch (e: any) { message.error(e.response?.data?.detail || 'Ошибка') }
  }

  // === Редактирование клиента ===
  const openEditClient = () => {
    editClientForm.setFieldsValue({
      client_name: (order as any)?.client_name,
      client_phone: (order as any)?.client_phone,
      client_email: (order as any)?.client_email,
      age_group: (order as any)?.age_group,
      source: (order as any)?.source,
    })
    setEditClientModal(true)
  }

  const submitEditClient = async () => {
    try {
      const v = await editClientForm.validateFields()
      await updateOrder(Number(id), v)
      message.success('Данные клиента обновлены')
      setEditClientModal(false)
      loadOrder()
      loadComments()
    } catch (e: any) { message.error(e.response?.data?.detail || 'Ошибка') }
  }

  // === Редактирование заказа (описание, устройство) ===
  const openEditOrder = () => {
    editOrderForm.setFieldsValue({
      complaint: (order as any)?.complaint,
      device_category: (order as any)?.device_category,
      device_brand: (order as any)?.device_brand,
      device_model: (order as any)?.device_model,
      serial_number: (order as any)?.serial_number,
      accessories: (order as any)?.accessories,
      appearance: (order as any)?.appearance,
      has_delivery: (order as any)?.has_delivery,
      is_warranty: (order as any)?.is_warranty,
      order_type: (order as any)?.order_type,
    })
    setEditOrderModal(true)
  }

  const submitEditOrder = async () => {
    try {
      const v = await editOrderForm.validateFields()
      await updateOrder(Number(id), v)
      message.success('Данные заказа обновлены')
      setEditOrderModal(false)
      loadOrder()
      loadComments()
    } catch (e: any) { message.error(e.response?.data?.detail || 'Ошибка') }
  }

  // === Назначение мастера/менеджера ===
  const openEditAssignment = () => {
    editAssignmentForm.setFieldsValue({
      master_id: (order as any)?.master_id,
      manager_id: (order as any)?.manager_id,
    })
    setEditAssignmentModal(true)
  }

  const submitEditAssignment = async () => {
    try {
      const v = await editAssignmentForm.validateFields()
      await updateOrder(Number(id), v)
      message.success('Исполнители обновлены')
      setEditAssignmentModal(false)
      loadOrder()
      loadComments()
    } catch (e: any) { message.error(e.response?.data?.detail || 'Ошибка') }
  }

  if (loading) return <Spin style={{ display: 'block', margin: '40px auto' }} />
  if (!order) return <div style={{ padding: 40, color: textColor }}>Заказ не найден</div>

  // Cast to any to bypass strict type checks on extended order fields
  const o = order as any

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 64px)', background: bg }}>
      
      {/* ===== ЛЕВАЯ ПАНЕЛЬ: История комментариев ===== */}
      <div style={{ width: 280, flexShrink: 0, background: sideBg, borderRight: `1px solid ${borderColor}`, display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '12px 12px 8px', borderBottom: `1px solid ${borderColor}` }}>
          <Space>
            <Title level={5} style={{ margin: 0, color: textColor }}>История</Title>
            <PaperClipOutlined style={{ color: textSecondary }} />
            <CameraOutlined style={{ color: textSecondary }} />
          </Space>
        </div>
        
        <div style={{ padding: '8px 12px' }}>
          <TextArea
            value={commentText}
            onChange={e => setCommentText(e.target.value)}
            onPressEnter={(e: any) => { if (!e.shiftKey) { e.preventDefault(); sendComment() } }}
            placeholder="Комментарий..."
            rows={2}
            style={{ background: inputBg, border: `1px solid ${borderColor}`, color: textColor, fontSize: 13, resize: 'none' }}
          />
          <Button type="primary" size="small" block icon={<SendOutlined />} onClick={sendComment} disabled={!commentText.trim()}
            style={{ marginTop: 6 }}>
            Отправить
          </Button>
        </div>

        <Divider style={{ margin: '4px 0', borderColor }} />

        <div style={{ flex: 1, overflow: 'auto', padding: '0 12px' }}>
          <Spin spinning={commentsLoading}>
            <List
              dataSource={comments}
              locale={{ emptyText: <Text style={{color: textSecondary}}>Нет комментариев</Text> }}
              renderItem={(c: any) => (
                <List.Item style={{ border: 'none', padding: '10px 0', flexDirection: 'column', alignItems: 'flex-start' }}>
                  <div style={{ width: '100%' }}>
                    <Space size={4} wrap>
                      <Text style={{ color: textColor, fontWeight: 500, fontSize: 13 }}>{c.username}</Text>
                      {c.is_system && <Tag color="blue" style={{ margin: 0, fontSize: 10 }}>системное</Tag>}
                    </Space>
                    <div style={{ marginTop: 4, color: textColor, fontSize: 12, lineHeight: 1.4 }}>{c.text}</div>
                    <Text style={{ color: textSecondary, fontSize: 10 }}>{dayjs(c.created_at).format('DD.MM, HH:mm')}</Text>
                  </div>
                </List.Item>
              )}
            />
          </Spin>
        </div>
      </div>

      {/* ===== ОСНОВНОЙ КОНТЕНТ ===== */}
      <div style={{ flex: 1, overflow: 'auto', background: bg }}>
        {/* Шапка заказа */}
        <div style={{ padding: '16px 24px', borderBottom: `1px solid ${borderColor}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: headerBg }}>
          <Space size={16}>
            <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/orders')} 
              style={{ background: hoverBg, border: `1px solid ${borderColor}`, color: textColor }} />
            <Title level={4} style={{ margin: 0, color: textColor }}>
              Заказ #{o.id}{o.order_number ? ` (№${o.order_number})` : ''}
            </Title>
            <Text style={{ color: textColor, fontSize: 18, fontWeight: 600 }}>{o.total_cost ? `${o.total_cost.toFixed(2)} ₽` : '0,00 ₽'}</Text>
            <Select
              value={o.status}
              onChange={handleStatusChange}
              size="large"
              style={{ width: 180 }}
              options={statusList.map(s => ({ value: s.value, label: s.label }))}
            />
          </Space>
          <Space>
            <Button icon={<PrinterOutlined />} onClick={() => {
              const token = localStorage.getItem('token')
              window.open(`/api/documents/print/${o.id}/receipt?token=${token}`, '_blank', 'noopener,noreferrer')
            }}>Квитанция</Button>
            <Button icon={<PrinterOutlined />} onClick={() => {
              const token = localStorage.getItem('token')
              window.open(`/api/documents/print/${o.id}/diagnostic_act?token=${token}`, '_blank', 'noopener,noreferrer')
            }}>Диагностика</Button>
            <Button icon={<PrinterOutlined />} onClick={() => {
              const token = localStorage.getItem('token')
              window.open(`/api/documents/print/${o.id}/work_act?token=${token}`, '_blank', 'noopener,noreferrer')
            }}>Акт</Button>
            <Button icon={<PrinterOutlined />} onClick={() => {
              const token = localStorage.getItem('token')
              window.open(`/api/documents/print/${o.id}/invoice?token=${token}`, '_blank', 'noopener,noreferrer')
            }}>Счёт</Button>
          </Space>
        </div>

        {/* Табы */}
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          tabBarStyle={{ padding: '0 24px', marginBottom: 0, background: headerBg }}
          items={[
            { key: 'general', label: <Text style={{ color: textColor }}>Общая информация</Text> },
            { key: 'financial', label: <Text style={{ color: textColor }}>💰 Финансы</Text> },
          ]}
        />

        <div style={{ padding: '16px 24px' }}>
          {activeTab === 'general' && (
            <Row gutter={[16, 16]}>
              {/* Товары и услуги */}
              <Col span={24}>
                <Card 
                  title={<Space><ShoppingCartOutlined /><Text style={{ color: textColor }}>Товары и услуги</Text></Space>} 
                  size="small" 
                  style={{ background: cardBg, border: `1px solid ${borderColor}` }}
                  extra={
                    <Space size={4}>
                      <Button size="small" icon={<PlusOutlined />} onClick={() => { setAddPartModal(true); addPartForm.resetFields(); loadOrderParts() }}>+ Запчасть</Button>
                      <Button size="small" icon={<PlusOutlined />} onClick={() => { loadServicesForOrder(); setAddServiceModal(true); addServiceForm.resetFields() }}>+ Услуга</Button>
                    </Space>
                  }
                >
                  {/* Услуги */}
                  {o.service_items && o.service_items.length > 0 && (
                    <>
                      <Text style={{ color: textSecondary, fontSize: 11, fontWeight: 600 }}>УСЛУГИ</Text>
                      <Table
                        dataSource={o.service_items}
                        size="small"
                        pagination={false}
                        rowKey="id"
                        style={{ marginBottom: 12 }}
                        columns={[
                          { title: '', key: 'icon', width: 30, render: () => '🔧' },
                          { title: 'Название', dataIndex: 'service_name', key: 'name', render: (v: string) => <Text style={{fontSize: 12, color: textColor}}>{v}</Text> },
                          { title: 'Кол-во', dataIndex: 'quantity', key: 'qty', width: 50, render: (v: number) => <Text style={{fontSize: 12, color: textColor}}>{v}</Text> },
                          { title: 'Цена', dataIndex: 'price_at_order', key: 'price', width: 70, render: (v: number) => <Text style={{fontSize: 12, color: textColor}}>{v.toFixed(0)}₽</Text> },
                          { title: 'Сумма', key: 'total', width: 70, render: (_: any, r: any) => <Text style={{fontSize: 12, color: textColor, fontWeight: 600}}>{(r.quantity * r.price_at_order).toFixed(0)}₽</Text> },
                          { title: '', key: 'del', width: 40, render: (_: any, r: any) => (
                            <Popconfirm title="Удалить услугу?" onConfirm={async () => {
                              try { await axios.delete(`/api/order-services/${r.id}`, { headers: { Authorization: 'Bearer ' + (localStorage.getItem('token') || '') } }); message.success('Удалено'); loadOrder() } catch {}
                            }}>
                              <Button size="small" danger icon={<DeleteOutlined />} style={{padding: '0 4px'}} />
                            </Popconfirm>
                          )},
                        ]}
                      />
                    </>
                  )}

                  {/* Запчасти */}
                  {o.parts && o.parts.length > 0 && (
                    <>
                      <Text style={{ color: textSecondary, fontSize: 11, fontWeight: 600 }}>ЗАПЧАСТИ</Text>
                      <Table
                        dataSource={o.parts}
                        size="small"
                        pagination={false}
                        rowKey="id"
                        columns={[
                          { title: '', key: 'icon', width: 30, render: () => '📦' },
                          { title: 'Название', dataIndex: 'part_name', key: 'name', render: (v: string) => <Text style={{fontSize: 12, color: textColor}}>{v || '—'}</Text> },
                          { title: 'Кол-во', dataIndex: 'quantity', key: 'qty', width: 50, render: (v: number) => <Text style={{fontSize: 12, color: textColor}}>{v}</Text> },
                          { title: 'Цена', dataIndex: 'price_at_order', key: 'price', width: 70, render: (v: number) => <Text style={{fontSize: 12, color: textColor}}>{v ? `${v.toFixed(0)}₽` : '—'}</Text> },
                          { title: 'Сумма', key: 'total', width: 70, render: (_: any, r: any) => <Text style={{fontSize: 12, color: textColor, fontWeight: 600}}>{r.quantity && r.price_at_order ? `${(r.quantity * r.price_at_order).toFixed(0)}₽` : '—'}</Text> },
                          { title: '', key: 'del', width: 40, render: (_: any, r: any) => (
                            <Popconfirm title="Удалить запчасть?" onConfirm={async () => {
                              try { await axios.delete(`/api/order-parts/${r.id}`, { headers: { Authorization: 'Bearer ' + (localStorage.getItem('token') || '') } }); message.success('Удалено'); loadOrder() } catch {}
                            }}>
                              <Button size="small" danger icon={<DeleteOutlined />} style={{padding: '0 4px'}} />
                            </Popconfirm>
                          )},
                        ]}
                      />
                    </>
                  )}

                  {!o.parts?.length && !o.service_items?.length && (
                    <Text style={{ color: textSecondary, fontSize: 12 }}>Нет товаров и услуг</Text>
                  )}

                  {/* Итого */}
                  {(o.parts?.length > 0 || o.service_items?.length > 0) && (
                    <Divider style={{ borderColor, margin: '8px 0' }} />
                  )}
                  {(o.parts?.length > 0 || o.service_items?.length > 0) && (
                    <div style={{ textAlign: 'right' }}>
                      <Text style={{ color: textSecondary, fontSize: 11 }}>Запчасти: </Text>
                      <Text style={{ color: textColor, fontSize: 12 }}>{o.parts_cost || 0}₽</Text>
                      <Text style={{ color: textSecondary, fontSize: 11, marginLeft: 16 }}>Услуги: </Text>
                      <Text style={{ color: textColor, fontSize: 12 }}>{o.work_cost || 0}₽</Text>
                      <Text style={{ color: '#1890ff', fontSize: 14, fontWeight: 600, marginLeft: 16 }}>
                        Итого: {(o.total_cost || 0).toFixed(0)}₽
                      </Text>
                    </div>
                  )}
                </Card>
              </Col>

              {/* Платежи */}
              <Col span={24}>
                <Card 
                  title={<Space><DollarOutlined /><Text style={{ color: textColor }}>Платежи</Text></Space>} 
                  size="small" 
                  style={{ background: cardBg, border: `1px solid ${borderColor}` }}
                  extra={
                    <Space size={4}>
                      <Button size="small" icon={<PayCircleOutlined />} onClick={() => handlePayment('prepayment')}>Предоплата</Button>
                      <Button size="small" icon={<PayCircleOutlined />} onClick={() => handlePayment('final')}>Оплата</Button>
                      <Button size="small" icon={<MinusCircleOutlined />} onClick={() => handlePayment('refund')}>Возврат</Button>
                      <Button size="small" icon={<ReloadOutlined />} onClick={loadPayments} />
                    </Space>
                  }
                >
                  {/* Сводка */}
                  {paymentSummary && (
                    <div style={{ marginBottom: 12 }}>
                      <Row gutter={16}>
                        <Col span={6}>
                          <Statistic title="Стоимость" value={paymentSummary.total_cost} precision={0} suffix="₽" valueStyle={{ color: '#1890ff', fontSize: 14 }} />
                        </Col>
                        <Col span={6}>
                          <Statistic title="Оплачено" value={paymentSummary.total_paid} precision={0} suffix="₽" valueStyle={{ color: '#52c41a', fontSize: 14 }} />
                        </Col>
                        <Col span={6}>
                          <Statistic title="Остаток" value={paymentSummary.remaining} precision={0} suffix="₽" valueStyle={{ color: paymentSummary.remaining > 0 ? '#f5222d' : '#52c41a', fontSize: 14 }} />
                        </Col>
                        <Col span={6}>
                          <Progress percent={paymentSummary.paid_percent} size="small" strokeColor={paymentSummary.is_fully_paid ? '#52c41a' : '#1890ff'} />
                        </Col>
                      </Row>
                    </div>
                  )}

                  {/* Список платежей */}
                  <Spin spinning={paymentsLoading}>
                    <List
                      dataSource={payments}
                      locale={{ emptyText: <Text style={{color: textSecondary}}>Нет платежей</Text> }}
                      renderItem={(p: any) => {
                        const typeIcons: Record<string, string> = { prepayment: '💰', final: '✅', refund: '↩️', expense: '📋' }
                        const typeColors: Record<string, string> = { prepayment: 'blue', final: 'green', refund: 'orange', expense: 'default' }
                        return (
                          <List.Item
                            actions={[
                              <Popconfirm title="Удалить платёж?" onConfirm={() => handleDeletePayment(p.id)}>
                                <Button size="small" icon={<DeleteOutlined />} danger />
                              </Popconfirm>,
                            ]}
                          >
                            <List.Item.Meta
                              avatar={<Tag color={typeColors[p.payment_type]}>{typeIcons[p.payment_type] || ''}</Tag>}
                              title={
                                <Space>
                                  <Text style={{ color: textColor, fontWeight: 500 }}>
                                    {p.payment_type === 'prepayment' ? 'Предоплата' : p.payment_type === 'final' ? 'Оплата' : p.payment_type === 'refund' ? 'Возврат' : 'Расход'}
                                  </Text>
                                  <Text style={{ color: p.amount < 0 ? '#f5222d' : '#52c41a', fontWeight: 600 }}>
                                    {p.amount < 0 ? '-' : ''}{Math.abs(p.amount).toFixed(0)}₽
                                  </Text>
                                </Space>
                              }
                              description={
                                <Space size={8}>
                                  <Text style={{ color: textSecondary, fontSize: 11 }}>{dayjs(p.created_at).format('DD.MM.YYYY HH:mm')}</Text>
                                  <Tag style={{ fontSize: 10, margin: 0 }}>{p.method === 'cash' ? '💵 Наличные' : p.method === 'card' ? '💳 Карта' : ' Перевод'}</Tag>
                                  {p.comment && <Text style={{ color: textSecondary, fontSize: 11 }}>{p.comment}</Text>}
                                </Space>
                              }
                            />
                          </List.Item>
                        )
                      }}
                    />
                  </Spin>
                </Card>
              </Col>

              <Col span={12}>
                <Card title={<Space><EditOutlined /><Text style={{ color: textColor }}>Информация</Text><Button type="link" size="small" icon={<EditOutlined />} onClick={openEditOrder} style={{ marginLeft: 8, padding: 0 }}>Изменить</Button></Space>} size="small"
                  style={{ background: cardBg, border: `1px solid ${borderColor}` }}>
                  <Descriptions column={1} size="small" labelStyle={{ color: textSecondary, width: 140 }}>
                    <Descriptions.Item label="Причина обращения"><Text style={{ color: textColor }}>{o.complaint || '—'}</Text></Descriptions.Item>
                    <Descriptions.Item label="Внешний вид"><Text style={{ color: textColor }}>{o.appearance || '—'}</Text></Descriptions.Item>
                    <Descriptions.Item label="Вид устройства"><Text style={{ color: textColor }}>{o.device_category}</Text></Descriptions.Item>
                    <Descriptions.Item label="IMEI / SN"><Text style={{ color: textColor }}>{o.serial_number || '—'}</Text></Descriptions.Item>
                    <Descriptions.Item label="Бренд"><Text style={{ color: textColor }}>{o.device_brand}</Text></Descriptions.Item>
                    <Descriptions.Item label="Модель"><Text style={{ color: textColor }}>{o.device_model}</Text></Descriptions.Item>
                    <Descriptions.Item label="Комплектация"><Text style={{ color: textColor }}>{o.accessories || '—'}</Text></Descriptions.Item>
                    <Descriptions.Item label="Доставка"><Text style={{ color: textColor }}>{o.has_delivery ? '✅' : '—'}</Text></Descriptions.Item>
                    <Descriptions.Item label="По гарантии"><Text style={{ color: textColor }}>{o.is_warranty ? '✅' : '—'}</Text></Descriptions.Item>
                  </Descriptions>
                </Card>
              </Col>

              <Col span={12}>
                <Card title={<Space><UserOutlined /><Text style={{ color: textColor }}>Клиент</Text><Button type="link" size="small" icon={<EditOutlined />} onClick={openEditClient} style={{ marginLeft: 8, padding: 0 }}>Изменить</Button></Space>} size="small"
                  style={{ background: cardBg, border: `1px solid ${borderColor}` }}>
                  <Descriptions column={1} size="small" labelStyle={{ color: textSecondary, width: 120 }}>
                    <Descriptions.Item label="Имя"><Text style={{ color: textColor }}>{o.client_name}</Text></Descriptions.Item>
                    <Descriptions.Item label="Телефон"><a href={`tel:${o.client_phone}`} style={{ color: '#1890ff' }}>{o.client_phone}</a></Descriptions.Item>
                    <Descriptions.Item label="Почта"><Text style={{ color: textColor }}>{o.client_email || '—'}</Text></Descriptions.Item>
                    <Descriptions.Item label="Возраст клиента"><Text style={{ color: textColor }}>{o.age_group || '—'}</Text></Descriptions.Item>
                    <Descriptions.Item label="Откуда узнал"><Text style={{ color: textColor }}>{o.source || '—'}</Text></Descriptions.Item>
                  </Descriptions>

                  <Divider style={{ borderColor }} />
                  <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                    <Text style={{ color: textColor, fontWeight: 600 }}>Назначение</Text>
                    <Button type="link" size="small" icon={<EditOutlined />} onClick={openEditAssignment} style={{ padding: 0 }}>Изменить</Button>
                  </Space>
                  <Descriptions column={1} size="small" labelStyle={{ color: textSecondary, width: 120 }} style={{ marginTop: 8 }}>
                    <Descriptions.Item label="Тип заказа"><Text style={{ color: textColor }}>{o.order_type || 'Ремонт'}</Text></Descriptions.Item>
                    <Descriptions.Item label="Менеджер"><Text style={{ color: textColor }}>{o.manager_name || '—'}</Text></Descriptions.Item>
                    <Descriptions.Item label="Приёмщик"><Text style={{ color: textColor }}>{o.acceptor_username || '—'}</Text></Descriptions.Item>
                    <Descriptions.Item label="Исполнитель">
                      <Space>
                        <Text style={{ color: textColor }}>{o.master_username || 'Не назначен'}</Text>
                        {o.master_id && o.status === 'issued' && (
                          <Button
                            size="small"
                            icon={<DollarOutlined />}
                            onClick={handleRecalculateSalary}
                            title="Пересчитать зарплату"
                          />
                        )}
                      </Space>
                    </Descriptions.Item>
                    <Descriptions.Item label="Создан"><Text style={{ color: textColor }}>{dayjs(o.created_at).format('DD.MM.YYYY, HH:mm')}</Text></Descriptions.Item>
                    <Descriptions.Item label="Закрыт"><Text style={{ color: textColor }}>{o.issued_at ? dayjs(o.issued_at).format('DD.MM.YYYY, HH:mm') : '—'}</Text></Descriptions.Item>
                  </Descriptions>
                </Card>
              </Col>
            </Row>
          )}

          {activeTab === 'financial' && (
            <Card size="small" style={{ background: cardBg, border: `1px solid ${borderColor}` }}>
              <Descriptions column={2} size="middle" labelStyle={{ color: textSecondary, width: 200 }}>
                <Descriptions.Item label="Стоимость запчастей">
                  <Text style={{ color: '#fa8c16', fontSize: 16 }}>{o.parts_cost != null ? `${o.parts_cost.toFixed(2)} ₽` : '—'}</Text>
                </Descriptions.Item>
                <Descriptions.Item label="Стоимость работ">
                  <Text style={{ color: '#52c41a', fontSize: 16 }}>{o.work_cost != null ? `${o.work_cost.toFixed(2)} ₽` : '—'}</Text>
                </Descriptions.Item>
                <Descriptions.Item label="Общая сумма">
                  <Text strong style={{ color: '#1890ff', fontSize: 20 }}>{o.total_cost != null ? `${o.total_cost.toFixed(2)} ₽` : '—'}</Text>
                </Descriptions.Item>
                <Descriptions.Item label="Возвраты">
                  <Text style={{ color: '#f5222d', fontSize: 16 }}>
                    {o.refunds_amount ? `-${o.refunds_amount.toFixed(2)} ₽` : '—'}
                  </Text>
                </Descriptions.Item>
                <Descriptions.Item label="Оплачено">
                  <Text style={{ color: '#52c41a', fontSize: 16 }}>{o.paid_amount != null ? `${o.paid_amount.toFixed(2)} ₽` : '—'}</Text>
                </Descriptions.Item>
                <Descriptions.Item label="Прибыль (без возвратов)">
                  <Text style={{ color: '#722ed1', fontSize: 16 }}>
                    {o.total_cost != null && o.parts_cost != null ? `${(o.total_cost - o.parts_cost).toFixed(2)} ₽` : '—'}
                  </Text>
                </Descriptions.Item>
                <Descriptions.Item label="Прибыль (с возвратами)">
                  <Text style={{ 
                    color: o.total_cost != null && o.parts_cost != null && o.refunds_amount 
                      ? (o.total_cost - o.parts_cost - o.refunds_amount) > 0 ? '#52c41a' : '#f5222d'
                      : '#722ed1',
                    fontSize: 16,
                    fontWeight: 600
                  }}>
                    {o.total_cost != null && o.parts_cost != null ? `${(o.total_cost - o.parts_cost - (o.refunds_amount || 0)).toFixed(2)} ₽` : '—'}
                  </Text>
                </Descriptions.Item>
              </Descriptions>
            </Card>
          )}
        </div>
      </div>

      {/* ===== ПРАВАЯ ПАНЕЛЬ: Информация о клиенте ===== */}
      <div style={{ width: 300, flexShrink: 0, background: sideBg, borderLeft: `1px solid ${borderColor}`, overflow: 'auto', padding: 16 }}>
        <Spin spinning={clientLoading}>
          {clientInfo ? (
            <>
              <div style={{ textAlign: 'center', marginBottom: 16 }}>
                <Tag color={clientInfo.loyalty_color} style={{ fontSize: 14, padding: '6px 16px', marginBottom: 12 }}>
                  {clientInfo.loyalty}
                </Tag>
                <div>
                  <Text style={{ color: textSecondary, fontSize: 12 }}>Заказов</Text>
                  <div><Text style={{ color: '#1890ff', fontSize: 28, fontWeight: 'bold' }}>{clientInfo.total_orders}</Text></div>
                </div>
                <div style={{ marginTop: 8 }}>
                  <Text style={{ color: textSecondary, fontSize: 12 }}>Средний чек</Text>
                  <div><Text style={{ color: '#52c41a', fontSize: 20, fontWeight: 'bold' }}>{clientInfo.avg_check.toFixed(0)} ₽</Text></div>
                </div>
                <div style={{ marginTop: 8 }}>
                  <Text style={{ color: textSecondary, fontSize: 12 }}>Общая выручка</Text>
                  <div><Text style={{ color: '#faad14', fontSize: 16 }}>{clientInfo.total_revenue.toFixed(0)} ₽</Text></div>
                </div>
              </div>

              <Divider style={{ borderColor }} />

              <div style={{ marginBottom: 16 }}>
                <Text style={{ color: textColor, fontWeight: 600, fontSize: 13 }}>Статусы заказов</Text>
                <div style={{ marginTop: 8 }}>
                  {Object.entries(clientInfo.by_status || {}).map(([status, count]) => {
                    const sc = statusList.find(s => s.value === status)
                    return (
                      <div key={status} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, alignItems: 'center' }}>
                        <span style={{ color: textColor, fontSize: 12 }}>{sc?.label || status}</span>
                        <Tag color={sc?.color || 'default'} style={{ margin: 0 }}>{String(count)}</Tag>
                      </div>
                    )
                  })}
                </div>
              </div>

              <Divider style={{ borderColor }} />

              {clientInfo.devices && clientInfo.devices.length > 0 && (
                <div style={{ marginBottom: 16 }}>
                  <Text style={{ color: textColor, fontWeight: 600, fontSize: 13 }}>Устройства</Text>
                  <div style={{ marginTop: 8 }}>
                    {clientInfo.devices.map((d: string, i: number) => (
                      <div key={i} style={{ marginBottom: 6, color: textColor, fontSize: 12 }}>📱 {d}</div>
                    ))}
                  </div>
                </div>
              )}

              <Divider style={{ borderColor }} />

              <div>
                <Text style={{ color: textColor, fontWeight: 600, fontSize: 13 }}>История заказов</Text>
                <List
                  dataSource={(clientInfo.orders || []).slice(0, 15)}
                  locale={{ emptyText: <Text style={{color: textSecondary}}>Нет заказов</Text> }}
                  style={{ marginTop: 8 }}
                  renderItem={(o: any) => {
                    const sc = statusList.find(s => s.value === o.status)
                    return (
                      <List.Item style={{ border: 'none', padding: '8px 0', flexDirection: 'column', alignItems: 'flex-start' }}>
                        <Space size={4}>
                          <a onClick={() => navigate(`/orders/${o.id}`)} style={{ color: '#1890ff', fontSize: 12 }}>#{o.id}</a>
                          <Tag color={sc?.color || 'default'} style={{ margin: 0, fontSize: 10 }}>{sc?.label || o.status}</Tag>
                        </Space>
                        <Text style={{ color: textSecondary, fontSize: 11 }}>{o.device_model}</Text>
                        <Text style={{ color: '#52c41a', fontSize: 11 }}>{o.total_cost ? `${o.total_cost} ₽` : ''}</Text>
                      </List.Item>
                    )
                  }}
                />
              </div>
            </>
          ) : (
            <Text style={{ color: textSecondary }}>Нет данных о клиенте</Text>
          )}
        </Spin>
      </div>

      {/* ===== Модальные окна ===== */}

      {/* Модалка платежа */}
      <Modal 
        title={getPaymentModalTitle(paymentType)} 
        open={paymentModal} 
        onOk={submitPayment} 
        onCancel={() => setPaymentModal(false)} 
        confirmLoading={printing}
        okText={printing ? 'Проводим...' : 'Провести'}
        width={440}
      >
        <Form form={paymentForm} layout="vertical">
          <Form.Item name="payment_type" hidden><Input /></Form.Item>
          
          <Form.Item label="Сумма" name="amount" rules={[{ required: true, message: 'Введите сумму' }]}>
            <Input type="number" placeholder="0.00" autoFocus />
          </Form.Item>
          
          <Form.Item label="Способ оплаты" name="method">
            <Select options={[
              { label: '💵 Наличные', value: 'cash' },
              { label: '💳 Карта', value: 'card' },
              { label: '📱 Перевод', value: 'transfer' },
              { label: '🧾 Счёт', value: 'invoice' },
            ]} />
          </Form.Item>
          
          <Form.Item label="Комментарий" name="comment">
            <Input placeholder="Примечание" />
          </Form.Item>
          
          {paymentSummary && (
            <div style={{ marginBottom: 12, padding: '8px 12px', background: isDark ? 'rgba(255,255,255,0.05)' : '#fafafa', borderRadius: 6, border: `1px solid ${borderColor}` }}>
              <Row gutter={8}>
                <Col span={8}><Text type="secondary" style={{ fontSize: 11 }}>Стоимость</Text><br/><Text strong style={{ color: textColor }}>{paymentSummary.total_cost?.toFixed(0)}₽</Text></Col>
                <Col span={8}><Text type="secondary" style={{ fontSize: 11 }}>Оплачено</Text><br/><Text strong style={{ color: '#52c41a' }}>{paymentSummary.total_paid?.toFixed(0)}₽</Text></Col>
                <Col span={8}><Text type="secondary" style={{ fontSize: 11 }}>Остаток</Text><br/><Text strong style={{ color: paymentSummary.remaining > 0 ? '#f5222d' : '#52c41a' }}>{paymentSummary.remaining?.toFixed(0)}₽</Text></Col>
              </Row>
            </div>
          )}
          
          <Form.Item name="print_receipt" valuePropName="checked" initialValue={true}>
            <Checkbox>📄 Квитанция</Checkbox>
          </Form.Item>
          
          <Form.Item name="print_diagnostic" valuePropName="checked">
            <Checkbox>🔍 Акт диагностики</Checkbox>
          </Form.Item>
          
          <Form.Item name="print_act" valuePropName="checked" initialValue={true}>
            <Checkbox>📋 Акт работ</Checkbox>
          </Form.Item>
          
          <Form.Item name="print_invoice" valuePropName="checked">
            <Checkbox>💰 Счёт</Checkbox>
          </Form.Item>

          <div style={{ marginTop: 8 }}>
            <Text type="secondary" style={{ fontSize: 11 }}>Предпросмотр: </Text>
            <Button size="small" type="link" onClick={() => {
              const t = localStorage.getItem('token') || ''
              window.open(`/api/documents/print/${id}/receipt?token=${t}`, '_blank')
            }}>Квитанция</Button>
            <Button size="small" type="link" onClick={() => {
              const t = localStorage.getItem('token') || ''
              window.open(`/api/documents/print/${id}/diagnostic_act?token=${t}`, '_blank')
            }}>Диагностика</Button>
            <Button size="small" type="link" onClick={() => {
              const t = localStorage.getItem('token') || ''
              window.open(`/api/documents/print/${id}/work_act?token=${t}`, '_blank')
            }}>Акт</Button>
            <Button size="small" type="link" onClick={() => {
              const t = localStorage.getItem('token') || ''
              window.open(`/api/documents/print/${id}/invoice?token=${t}`, '_blank')
            }}>Счёт</Button>
          </div>
        </Form>
      </Modal>

      {/* Модалка добавления запчасти */}
      <Modal title="🔧 Добавить запчасть" open={addPartModal} onOk={handleAddPart} onCancel={() => setAddPartModal(false)} width={400}>
        <Form form={addPartForm} layout="vertical">
          <Form.Item label="Запчасть" name="part_id" rules={[{ required: true }]}>
            <Select options={availableParts.map((p: any) => ({ label: `${p.name} (ост: ${p.quantity})`, value: p.id }))} />
          </Form.Item>
          <Form.Item label="Количество" name="quantity" rules={[{ required: true }]} initialValue={1}>
            <Input type="number" min={1} />
          </Form.Item>
        </Form>
      </Modal>

      {/* Модалка добавления услуги */}
      <Modal title="Добавить услугу" open={addServiceModal} onOk={handleAddService} onCancel={() => setAddServiceModal(false)} width={420}>
        <Form form={addServiceForm} layout="vertical">
          <Form.Item label="Услуга" name="service_id" rules={[{ required: true, message: 'Выберите или введите название' }]}>
            <Select
              showSearch
              placeholder="Выберите или введите новую..."
              filterOption={(input, option) => (option?.label as string || '').toLowerCase().includes(input.toLowerCase())}
              onSearch={(val) => setServiceNameInput(val)}
              onBlur={() => setTimeout(() => setServiceNameInput(''), 200)}
              onChange={(val) => { addServiceForm.setFieldsValue({ service_id: val }) }}
              dropdownRender={(menu) => (
                <>
                  {menu}
                  {serviceNameInput && !availableServices.some((s: any) =>
                    s.name.toLowerCase().includes(serviceNameInput.toLowerCase())
                  ) && (
                    <div style={{ borderTop: '1px solid #f0f0f0', padding: '8px 12px' }}>
                      <Button
                        type="link"
                        block
                        onClick={() => addServiceForm.setFieldsValue({ service_id: serviceNameInput })}
                      >
                        ➕ Создать &quot;{serviceNameInput}&quot;
                      </Button>
                    </div>
                  )}
                </>
              )}
              options={availableServices.map((s: any) => ({ label: `${s.name} — ${s.price}₽`, value: s.id }))}
            />
          </Form.Item>
          <Form.Item label="Цена" name="price">
            <Input type="number" min={0} placeholder="0" />
          </Form.Item>
          <Form.Item label="Количество" name="quantity" rules={[{ required: true }]} initialValue={1}>
            <Input type="number" min={1} />
          </Form.Item>
          <Form.Item label="Комментарий" name="comment">
            <Input />
          </Form.Item>
        </Form>
      </Modal>

      {/* ===== Модалка: Редактирование клиента ===== */}
      <Modal title="✏️ Редактирование клиента" open={editClientModal} onOk={submitEditClient} onCancel={() => setEditClientModal(false)} width={500}>
        <Form form={editClientForm} layout="vertical">
          <Form.Item label="Имя клиента" name="client_name" rules={[{ required: true, message: 'Введите имя' }]}>
            <Input />
          </Form.Item>
          <Form.Item label="Телефон" name="client_phone" rules={[{ required: true, message: 'Введите телефон' }]}>
            <Input />
          </Form.Item>
          <Form.Item label="Email" name="client_email">
            <Input />
          </Form.Item>
          <Form.Item label="Возрастная группа" name="age_group">
            <Select allowClear placeholder="—" options={ageGroups} />
          </Form.Item>
          <Form.Item label="Источник" name="source">
            <Select allowClear placeholder="—" options={sources} />
          </Form.Item>
        </Form>
      </Modal>

      {/* ===== Модалка: Редактирование заказа ===== */}
      <Modal title="✏️ Редактирование заказа" open={editOrderModal} onOk={submitEditOrder} onCancel={() => setEditOrderModal(false)} width={600}>
        <Form form={editOrderForm} layout="vertical">
          <Form.Item label="Причина обращения / Описание поломки" name="complaint" rules={[{ required: true, message: 'Опишите проблему' }]}>
            <TextArea rows={4} />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="Внешний вид" name="appearance">
                <Select allowClear placeholder="—">
                  <Select.Option value="Б/У">Б/У</Select.Option>
                  <Select.Option value="Новый">Новый</Select.Option>
                  <Select.Option value="Как новый">Как новый</Select.Option>
                  <Select.Option value="С царапинами">С царапинами</Select.Option>
                  <Select.Option value="С повреждениями">С повреждениями</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Вид устройства" name="device_category">
                <Select>
                  <Select.Option value="phone">📱 Телефон</Select.Option>
                  <Select.Option value="laptop">💻 Ноутбук</Select.Option>
                  <Select.Option value="tablet">📋 Планшет</Select.Option>
                  <Select.Option value="tv">📺 Телевизор</Select.Option>
                  <Select.Option value="pc">🖥️ Компьютер</Select.Option>
                  <Select.Option value="appliance">🏠 Бытовая техника</Select.Option>
                  <Select.Option value="other">Другое</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Бренд" name="device_brand">
                <Input />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="Модель" name="device_model">
                <Input />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="IMEI / Серийный номер" name="serial_number">
                <Input />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item label="Комплектация" name="accessories">
            <Input placeholder="Например: зарядка, чехол, коробка" />
          </Form.Item>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item label="Тип заказа" name="order_type">
                <Select>
                  <Select.Option value="Ремонт">Ремонт</Select.Option>
                  <Select.Option value="Диагностика">Диагностика</Select.Option>
                  <Select.Option value="Консультация">Консультация</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="По гарантии" name="is_warranty" valuePropName="checked">
                <Select>
                  <Select.Option value={false}>Нет</Select.Option>
                  <Select.Option value={true}>Да</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="Доставка" name="has_delivery" valuePropName="checked">
                <Select>
                  <Select.Option value={false}>Нет</Select.Option>
                  <Select.Option value={true}>Да</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      {/* ===== Модалка: Назначение мастера/менеджера ===== */}
      <Modal title="👥 Назначение исполнителей" open={editAssignmentModal} onOk={submitEditAssignment} onCancel={() => setEditAssignmentModal(false)} width={400}>
        <Form form={editAssignmentForm} layout="vertical">
          <Form.Item label="Мастер (исполнитель)" name="master_id">
            <Select allowClear placeholder="Не назначен">
              {users.filter((u: any) => u.role_name === 'master').map((u: any) => (
                <Select.Option key={u.id} value={u.id}>{u.full_name || u.username}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item label="Менеджер" name="manager_id">
            <Select allowClear placeholder="Не назначен">
              {users.filter((u: any) => u.role_name === 'manager').map((u: any) => (
                <Select.Option key={u.id} value={u.id}>{u.full_name || u.username}</Select.Option>
              ))}
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default OrderDetailPage
