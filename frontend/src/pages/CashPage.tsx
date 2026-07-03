import React, { useState, useEffect } from 'react'
import { 
  Card, Button, Input, InputNumber, Select, Table, Tag, Space, 
  Modal, Form, message, Typography, Row, Col, Statistic, Divider, 
  Tabs, Popconfirm, Badge, Alert, Spin, Checkbox, List, Empty
} from 'antd'
import { 
  PlusOutlined, CloseOutlined, PayCircleOutlined, MinusCircleOutlined,
  ReloadOutlined, DollarOutlined, ShoppingCartOutlined, EyeOutlined,
  WalletOutlined
} from '@ant-design/icons'
import dayjs from 'dayjs'
import api from '../api'
import { useTheme } from '../contexts/ThemeContext'
import { generateReceipt, generateWorkAct, downloadDocument, previewDocument, changeOrderStatus } from '../api'

const { Text, Title } = Typography

const TX_TYPES: Record<string, { label: string; icon: string; color: string }> = {
  income: { label: 'Приход', icon: '💰', color: 'green' },
  expense: { label: 'Расход', icon: '💸', color: 'red' },
  adjustment: { label: 'Корректировка', icon: '📝', color: 'orange' },
  cashout: { label: 'Инкассация', icon: '🏦', color: 'blue' },
}

const CashPage: React.FC = () => {
  const { mode } = useTheme()
  const isDark = mode === 'dark'
  const [currentShift, setCurrentShift] = useState<any>(null)
  const [shiftOpenModal, setShiftOpenModal] = useState(false)
  const [shiftCloseModal, setShiftCloseModal] = useState(false)
  const [txModal, setTxModal] = useState(false)
  const [txType, setTxType] = useState('income')
  const [transactions, setTransactions] = useState<any[]>([])
  const [readyOrders, setReadyOrders] = useState<any[]>([])
  const [shiftHistory, setShiftHistory] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [openForm] = Form.useForm()
  const [closeForm] = Form.useForm()
  const [txForm] = Form.useForm()
  const [prevBalance, setPrevBalance] = useState<number | null>(null)
  const [loadingPrevBalance, setLoadingPrevBalance] = useState(false)
  const [paymentModal, setPaymentModal] = useState(false)
  const [selectedOrder, setSelectedOrder] = useState<any>(null)
  const [paymentForm] = Form.useForm()
  const [printing, setPrinting] = useState(false)
  const [activeTab, setActiveTab] = useState('ready')
  const [selectedShift, setSelectedShift] = useState<any>(null)
  const [shiftTransactions, setShiftTransactions] = useState<any[]>([])
  const [orderSearch, setOrderSearch] = useState('')
  const [orderList, setOrderList] = useState<any[]>([])
  const [transactionsLoading, setTransactionsLoading] = useState(false)
  const [monthlySummary, setMonthlySummary] = useState<{ month: string; cash_total: number; card_total: number; grand_total: number; refund_total: number; net_total: number; current_cash: number } | null>(null)

  useEffect(() => {
    loadShift()
    loadReadyOrders()
    loadMonthlySummary()
  }, [])

  useEffect(() => {
    if (currentShift && !loading) {
      loadTransactions()
    }
  }, [currentShift, activeTab])

  const loadShift = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await api.get('/cash/shift/current')
      setCurrentShift(res.data)
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Ошибка загрузки смены')
    } finally {
      setLoading(false)
    }
  }

  const loadTransactions = async () => {
    try {
      const res = await api.get('/cash/transactions', { params: { limit: 50 } })
      setTransactions(res.data || [])
    } catch { setTransactions([]) }
  }

  const loadReadyOrders = async () => {
    try {
      const res = await api.get('/cash/orders/ready')
      setReadyOrders(res.data || [])
    } catch { setReadyOrders([]) }
  }

  const loadMonthlySummary = async () => {
    try {
      const res = await api.get('/cash/monthly-summary')
      setMonthlySummary(res.data)
    } catch { setMonthlySummary(null) }
  }

  const searchOrders = async (q: string) => {
    setOrderSearch(q)
    try {
      const params = new URLSearchParams({ limit: '20' })
      if (q && q.length >= 2) params.set('search', q)
      const res = await api.get(`/orders?${params}`)
      const data = Array.isArray(res.data) ? res.data : (res.data?.items || res.data || [])
      setOrderList(data)
    } catch { setOrderList([]) }
  }

  const loadShiftHistory = async () => {
    try {
      const res = await api.get('/cash/shift/history')
      setShiftHistory(Array.isArray(res.data) ? res.data : res.data?.shifts || [])
    } catch { setShiftHistory([]) }
  }

  const loadShiftTransactions = async (shift: any) => {
    setTransactionsLoading(true)
    setSelectedShift(shift)
    try {
      const res = await api.get(`/cash/transactions?shift_id=${shift.id}&limit=200`)
      setShiftTransactions(Array.isArray(res.data) ? res.data : [])
    } catch {
      message.error('Ошибка загрузки транзакций')
      setShiftTransactions([])
    } finally {
      setTransactionsLoading(false)
    }
  }

  const handleOpenShift = async () => {
    try {
      await api.post('/cash/shift/open', {})
      message.success('Смена открыта')
      setShiftOpenModal(false)
      loadShift()
    } catch (e: any) {
      message.error(e.response?.data?.detail || 'Ошибка')
    }
  }

  const openShiftModal = async () => {
    setShiftOpenModal(true)
    setLoadingPrevBalance(true)
    try {
      const res = await api.get('/cash/shift/history', { params: { limit: 1 } })
      const shifts = Array.isArray(res.data) ? res.data : res.data?.shifts || []
      const lastClosed = shifts.find((s: any) => !s.is_open)
      setPrevBalance(lastClosed ? lastClosed.final_amount : 0)
    } catch {
      setPrevBalance(0)
    } finally {
      setLoadingPrevBalance(false)
    }
  }

  const handleCloseShift = async () => {
    const values = await closeForm.validateFields()
    try {
      const res = await api.post('/cash/shift/close', { final_amount: values.final_amount })
      const diff = res.data.difference
      if (Math.abs(diff) > 0.01) {
        message.warning(`Разница: ${diff.toFixed(2)}₽`)
      } else {
        message.success('Смена закрыта')
      }
      setShiftCloseModal(false)
      closeForm.resetFields()
      loadShift()
      loadShiftHistory()
    } catch (e: any) {
      message.error(e.response?.data?.detail || 'Ошибка')
    }
  }

  const handleTransaction = async () => {
    const values = await txForm.validateFields()
    try {
      await api.post('/cash/transaction', {
        transaction_type: txType,
        amount: values.amount,
        order_id: values.order_id,
        comment: values.comment,
        is_parts: values.is_parts || false,
      })
      message.success(`${TX_TYPES[txType].label} проведён`)
      setTxModal(false)
      txForm.resetFields()
      loadShift()
      loadTransactions()
    } catch (e: any) {
      message.error(e.response?.data?.detail || 'Ошибка')
    }
  }

  const openTxModal = (type: string) => {
    setTxType(type)
    txForm.resetFields()
    txForm.setFieldsValue({ transaction_type: type })
    if (type === 'income' || type === 'expense') {
      searchOrders('')
    }
    setTxModal(true)
  }

  const openPaymentModal = (order: any) => {
    setSelectedOrder(order)
    paymentForm.resetFields()
    paymentForm.setFieldsValue({ method: 'card', amount: order.total_cost })
    setPaymentModal(true)
  }

  const handlePayment = async () => {
    if (!selectedOrder) return
    const values = await paymentForm.validateFields()
    
    try {
      setPrinting(true)
      
      const token = localStorage.getItem('token') || ''
      const orderId = selectedOrder.id
      
      const methodLabel = values.method === 'card' ? 'Карта' : values.method === 'transfer' ? 'Перевод' : values.method === 'invoice' ? 'Счёт' : 'Наличные'

      // Создаём платёж (бэкенд сам создаст cash-транзакцию и OrderPayment)
      await api.post('/payments/', {
        order_id: orderId,
        amount: values.amount,
        payment_type: 'final',
        method: values.method === 'cash' ? 'cash' : 'card',
        comment: `Оплата через кассу (${methodLabel})`,
      })

      // Обновляем сумму заказа перед сменой статуса
      await api.patch(`/orders/${orderId}`, {
        total_cost: values.amount,
        paid_amount: values.amount,
      })
      
      // Меняем статус на "Выдан" (бэкенд сам начислит зарплату)
      await changeOrderStatus(orderId, 'issued', 'Выдан через кассу')

      // Печать через <a> клик (обходит popup blocker)
      const docTemplates: Record<string, string> = {
        print_receipt: 'receipt',
        print_diagnostic: 'diagnostic_act',
        print_act: 'work_act',
        print_invoice: 'invoice',
      }
      for (const [key, template] of Object.entries(docTemplates)) {
        if (values[key]) {
          const a = document.createElement('a')
          a.href = `/api/documents/print/${orderId}/${template}?token=${token}`
          a.target = '_blank'
          a.rel = 'noopener noreferrer'
          document.body.appendChild(a)
          a.click()
          document.body.removeChild(a)
        }
      }
      
      message.success(`Заказ #${orderId} выдан, оплата ${values.amount}₽ проведена`)
      setPaymentModal(false)
      paymentForm.resetFields()
      
      // Обновляем данные
      loadShift()
      loadReadyOrders()
    } catch (e: any) {
      message.error(e.response?.data?.detail || 'Ошибка проведения оплаты')
    } finally {
      setPrinting(false)
    }
  }

  const txColumns = [
    { title: 'Тип', key: 'type', width: 130, render: (_: any, r: any) => {
      const tx = TX_TYPES[r.transaction_type] || { label: r.transaction_type, icon: '?', color: 'default' }
      return <Tag color={tx.color}>{tx.icon} {tx.label}</Tag>
    }},
    { title: 'Сумма', key: 'amount', dataIndex: 'amount', width: 100, render: (v: number) => (
      <Text strong style={{ color: v >= 0 ? '#52c41a' : '#f5222d' }}>
        {v >= 0 ? '+' : ''}{Number(v || 0).toFixed(2)}₽
      </Text>
    )},
    { title: 'Заказ', key: 'order', width: 70, render: (_: any, r: any) => r.order_id ? `#${r.order_id}` : '—' },
    { title: 'Комментарий', dataIndex: 'comment', key: 'comment', render: (v: string) => <Text style={{fontSize: 12}}>{v || '—'}</Text> },
    { title: 'Дата', dataIndex: 'created_at', key: 'date', width: 140, render: (v: string) => v ? dayjs(v).format('DD.MM HH:mm') : '—' },
  ]

  const readyColumns = [
    { title: '#', dataIndex: 'id', key: 'id', width: 50, render: (v: number) => <Text strong>#{v}</Text> },
    { title: 'Клиент', key: 'client', render: (_: any, r: any) => <div><Text strong>{r.client_name}</Text><br/><Text type="secondary">{r.client_phone}</Text></div> },
    { title: 'Устройство', dataIndex: 'device_model', key: 'device' },
    { title: 'Сумма', dataIndex: 'total_cost', key: 'total', width: 80, render: (v: number) => <Text strong style={{color:'#1890ff'}}>{v?.toFixed(0)}₽</Text> },
    { title: 'Мастер', dataIndex: 'master_username', key: 'master', width: 80, render: (v: string) => v || '—' },
    { title: 'На выдаче с', dataIndex: 'ready_at', key: 'ready', width: 120, render: (v: string) => v ? dayjs(v).format('DD.MM HH:mm') : '—' },
    { title: 'Действие', key: 'action', width: 100, render: (_: any, r: any) => (
      <Button type="primary" size="small" onClick={() => openPaymentModal(r)}>💰 Оплатить</Button>
    )},
  ]

  const historyColumns = [
    { title: 'Смена', dataIndex: 'id', key: 'id', width: 60, render: (v: number, r: any) => (
      <Space><Text strong>#{v}</Text>{r.is_open && <Badge status="processing" text="Открыта" />}</Space>
    )},
    { title: 'Открыта', dataIndex: 'opened_at', key: 'opened', width: 140, render: (v: string) => v ? dayjs(v).format('DD.MM HH:mm') : '—' },
    { title: 'Закрыта', dataIndex: 'closed_at', key: 'closed', width: 140, render: (v: string) => v ? dayjs(v).format('DD.MM HH:mm') : '—' },
    { title: 'Начало', dataIndex: 'initial_amount', key: 'initial', width: 80, render: (v: number) => `${(v||0).toFixed(0)}₽` },
    { title: 'Приход', dataIndex: 'income', key: 'income', width: 80, render: (v: number) => <Text style={{color:'#52c41a'}}>+{(v||0).toFixed(0)}₽</Text> },
    { title: 'Расход', dataIndex: 'expense', key: 'expense', width: 80, render: (v: number) => <Text style={{color:'#f5222d'}}>-{(v||0).toFixed(0)}₽</Text> },
    { title: 'Итог', dataIndex: 'final_amount', key: 'final', width: 80, render: (v: number) => <Text strong>{(v||0).toFixed(0)}₽</Text> },
  ]

  const bg = isDark ? '#1a1a2e' : '#fff'
  const cardBg = isDark ? '#1e1e36' : '#fff'
  const borderColor = isDark ? '#2a2a4a' : '#e8e8e8'
  const textColor = isDark ? '#e8e8e8' : '#1a1a1a'

  if (loading && !currentShift) {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: bg }}><Spin size="large" /></div>
  }

  return (
    <div style={{ background: bg, minHeight: '100vh', padding: '16px 24px' }}>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={3} style={{ margin: 0, color: textColor }}>💵 Касса</Title>
        <Space>
          {!currentShift ? (
            <Button type="primary" icon={<PlusOutlined />} onClick={openShiftModal}>Открыть смену</Button>
          ) : (
            <Button danger icon={<CloseOutlined />} onClick={() => { closeForm.setFieldsValue({ final_amount: currentShift.cash_balance || 0 }); setShiftCloseModal(true) }}>Закрыть смену</Button>
          )}
        </Space>
      </div>

      {error && <Alert message={error} type="error" showIcon closable onClose={() => setError(null)} style={{ marginBottom: 16 }} />}

      {currentShift && (
        <Card size="small" style={{ marginBottom: 16, background: cardBg, border: `1px solid ${borderColor}` }}>
          <Row gutter={16}>
            <Col span={6}><Statistic title="Нач. баланс (нал)" value={currentShift.initial_amount || 0} precision={0} suffix="₽" valueStyle={{fontSize: 14, color: textColor}} /></Col>
            <Col span={6}><Statistic title="Приход (нал)" value={currentShift.cash_income || 0} precision={0} suffix="₽" valueStyle={{color:'#52c41a',fontSize: 14}} /></Col>
            <Col span={6}><Statistic title="Расход (нал)" value={currentShift.cash_expense || 0} precision={0} suffix="₽" valueStyle={{color:'#f5222d',fontSize: 14}} /></Col>
            <Col span={6}><Statistic title="Наличные в кассе" value={currentShift.cash_balance || 0} precision={0} suffix="₽" valueStyle={{color:'#1890ff',fontSize: 16,fontWeight:'bold'}} /></Col>
          </Row>
          <Divider style={{margin:'12px 0', borderColor}} />
          <Row gutter={16} style={{marginBottom: 8}}>
            <Col span={8}><Statistic title="Безнал за смену" value={currentShift.card_income || 0} precision={0} suffix="₽" valueStyle={{color:'#722ed1',fontSize: 14}} /></Col>
            <Col span={8}><Statistic title="Всего приход" value={(currentShift.income || 0)} precision={0} suffix="₽" valueStyle={{color:'#52c41a',fontSize: 14}} /></Col>
            <Col span={8}><Statistic title="Общий оборот" value={(currentShift.income || 0) - (currentShift.expense || 0)} precision={0} suffix="₽" valueStyle={{color:'#faad14',fontSize: 16,fontWeight:'bold'}} /></Col>
          </Row>
          <Divider style={{margin:'12px 0', borderColor}} />
          <Space size={8}>
            <Button size="small" icon={<PayCircleOutlined />} onClick={() => openTxModal('income')}>Приход</Button>
            <Button size="small" icon={<MinusCircleOutlined />} onClick={() => openTxModal('expense')}>Расход</Button>
            <Button size="small" icon={<ReloadOutlined />} onClick={() => openTxModal('cashout')}>Инкассация</Button>
            <Button size="small" icon={<ReloadOutlined />} onClick={loadShift}>🔄</Button>
          </Space>
        </Card>
      )}

      {!currentShift && !error && (
        <Alert message="Смена не открыта" description="Откройте кассовую смену чтобы проводить операции" type="warning" showIcon style={{marginBottom: 16}} />
      )}

      {monthlySummary && (
        <Card
          size="small"
          title={<Space><WalletOutlined /> <Text strong>Приходы за {monthlySummary.month}</Text></Space>}
          style={{ marginBottom: 16, background: cardBg, border: `1px solid ${borderColor}` }}
        >
          <Row gutter={16}>
            <Col span={6}>
              <Statistic title="Выручка нал" value={monthlySummary.cash_total} precision={0} suffix="₽" valueStyle={{ color: '#52c41a', fontSize: 14 }} />
            </Col>
            <Col span={6}>
              <Statistic title="Выручка безнал" value={monthlySummary.card_total} precision={0} suffix="₽" valueStyle={{ color: '#1890ff', fontSize: 14 }} />
            </Col>
            <Col span={6}>
              <Statistic title="Общий приход" value={monthlySummary.grand_total} precision={0} suffix="₽" valueStyle={{ color: '#faad14', fontSize: 14 }} />
            </Col>
            <Col span={6}>
              <Statistic title="Возвраты" value={monthlySummary.refund_total || 0} precision={0} suffix="₽" valueStyle={{ color: '#f5222d', fontSize: 14 }} />
            </Col>
          </Row>
          <Divider style={{ margin: '8px 0', borderColor }} />
          <Row gutter={16}>
            <Col span={12}>
              <Statistic title="Чистый приход" value={monthlySummary.net_total} precision={0} suffix="₽" valueStyle={{ color: '#52c41a', fontSize: 18, fontWeight: 'bold' }} />
            </Col>
            <Col span={12}>
              <Statistic title="Наличные в кассе" value={monthlySummary.current_cash || 0} precision={0} suffix="₽" valueStyle={{ color: '#1890ff', fontSize: 18, fontWeight: 'bold' }} />
            </Col>
          </Row>
        </Card>
      )}

      <Tabs activeKey={activeTab} onChange={setActiveTab} items={[
        { key: 'ready', label: <Space>📦 На выдаче <Badge count={readyOrders.length} style={{background:'#52c41a'}} /></Space>, children: (
          <Card size="small" style={{ background: cardBg, border: `1px solid ${borderColor}` }}>
            <Table dataSource={readyOrders} rowKey="id" columns={readyColumns} pagination={false} size="small" locale={{emptyText: 'Нет заказов на выдаче'}} />
          </Card>
        )},
        { key: 'shift', label: '💵 Смена', children: (
          <Card size="small" title={<Space><DollarOutlined /> Транзакции</Space>} style={{ background: cardBg, border: `1px solid ${borderColor}` }}>
            <Table dataSource={transactions} rowKey="id" columns={txColumns} pagination={{pageSize: 10}} size="small" locale={{emptyText: 'Нет транзакций'}} />
          </Card>
        )},
        { key: 'history', label: '📜 История смен', children: (
          <Card size="small" style={{ background: cardBg, border: `1px solid ${borderColor}` }}>
            <div style={{ marginBottom: 8, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Button size="small" onClick={loadShiftHistory}>Обновить</Button>
              {selectedShift && (
                <Text type="secondary" style={{ fontSize: 12 }}>Выбрана смена #{selectedShift.id} — кликните другую строку чтобы сменить</Text>
              )}
            </div>
            <Table
              dataSource={shiftHistory}
              rowKey="id"
              columns={historyColumns}
              pagination={{ pageSize: 10 }}
              size="small"
              locale={{ emptyText: 'Нет истории смен' }}
              onRow={(record) => ({
                onClick: () => loadShiftTransactions(record),
                style: {
                  cursor: 'pointer',
                  background: selectedShift?.id === record.id
                    ? (isDark ? '#2a2a4a' : '#e6f4ff')
                    : undefined,
                },
              })}
            />

            {selectedShift && (
              <Card
                size="small"
                title={
                  <Space>
                    <DollarOutlined />
                    <Text>Транзакции смены #{selectedShift.id}</Text>
                    <Tag color={selectedShift.is_open ? 'green' : 'default'}>
                      {selectedShift.is_open ? '🟢 Открыта' : '🔒 Закрыта'}
                    </Tag>
                  </Space>
                }
                style={{ marginTop: 16, background: cardBg, border: `1px solid ${borderColor}` }}
                extra={
                  <Button size="small" icon={<ReloadOutlined />} onClick={() => loadShiftTransactions(selectedShift)}>
                    Обновить
                  </Button>
                }
              >
                {transactionsLoading ? (
                  <div style={{ textAlign: 'center', padding: 32 }}><Spin tip="Загрузка..." /></div>
                ) : shiftTransactions.length === 0 ? (
                  <Empty description="Нет транзакций в этой смене" />
                ) : (
                  <Table
                    dataSource={shiftTransactions}
                    rowKey="id"
                    columns={txColumns}
                    pagination={{ pageSize: 20 }}
                    size="small"
                    locale={{ emptyText: 'Нет транзакций' }}
                  />
                )}
              </Card>
            )}
          </Card>
        )},
      ]} />

      {/* Модалка открытия смены */}
      <Modal
        title="Открыть кассовую смену"
        open={shiftOpenModal}
        onOk={handleOpenShift}
        onCancel={() => setShiftOpenModal(false)}
        okText="Открыть смену"
      >
        {loadingPrevBalance ? (
          <div style={{ textAlign: 'center', padding: 24 }}><Spin tip="Загрузка..." /></div>
        ) : (
          <Alert
            type="info"
            showIcon
            message={`Начальный баланс: ${(prevBalance ?? 0).toFixed(2)}₽`}
            description={prevBalance ? 'Остаток с предыдущей смены будет установлен автоматически.' : 'Предыдущих смен нет — смена начнётся с 0₽.'}
          />
        )}
      </Modal>

      {/* Модалка закрытия смены */}
      <Modal title="Закрыть кассовую смену" open={shiftCloseModal} onOk={handleCloseShift} onCancel={() => setShiftCloseModal(false)}>
        <Form form={closeForm} layout="vertical">
          <Form.Item label="Фактический остаток наличных" name="final_amount" rules={[{required: true, message: 'Введите фактический остаток наличных в кассе'}]}>
            <InputNumber min={0} style={{width: '100%'}} placeholder="0" />
          </Form.Item>
          {currentShift && (
            <div style={{marginBottom: 12, padding: '8px 12px', background: isDark ? 'rgba(255,255,255,0.05)' : '#f5f5f5', borderRadius: 6, border: `1px solid ${borderColor}` }}>
              <Row gutter={8}>
                <Col span={12}>
                  <Text type="secondary" style={{fontSize:11}}>Нач. баланс</Text><br/>
                  <Text strong style={{color: textColor, fontSize:14}}>{(currentShift.initial_amount || 0).toFixed(0)}₽</Text>
                </Col>
                <Col span={12}>
                  <Text type="secondary" style={{fontSize:11}}>Приход (нал + безнал)</Text><br/>
                  <Text strong style={{color:'#52c41a', fontSize:14}}>{(currentShift.income || 0).toFixed(0)}₽</Text>
                </Col>
              </Row>
              <Row gutter={8} style={{marginTop: 4}}>
                <Col span={12}>
                  <Text type="secondary" style={{fontSize:11}}>Расчётный нал</Text><br/>
                  <Text strong style={{color:'#1890ff', fontSize:16}}>{(currentShift.cash_balance || 0).toFixed(0)}₽</Text>
                </Col>
                <Col span={12}>
                  <Text type="secondary" style={{fontSize:11}}>Безнал за смену</Text><br/>
                  <Text strong style={{color:'#722ed1', fontSize:16}}>{(currentShift.card_income || 0).toFixed(0)}₽</Text>
                </Col>
              </Row>
            </div>
          )}
        </Form>
      </Modal>

      {/* Модалка транзакции */}
      <Modal title={`${TX_TYPES[txType].icon} ${TX_TYPES[txType].label}`} open={txModal} onOk={handleTransaction} onCancel={() => setTxModal(false)}>
        <Form form={txForm} layout="vertical">
          <Form.Item label="Сумма" name="amount" rules={[{required: true, message: 'Введите сумму'}]}>
            <InputNumber min={txType === 'adjustment' ? undefined : 0.01} style={{width: '100%'}} placeholder="0.00" />
          </Form.Item>
          {txType === 'income' && (
            <Form.Item label="Заказ (для начисления ЗП мастеру)" name="order_id">
              <Select
                showSearch
                placeholder="Выберите заказ или оставьте пустым"
                filterOption={false}
                onSearch={searchOrders}
                allowClear
                options={orderList.map((o: any) => ({
                  value: o.id,
                  label: `#${o.id} ${o.client_name || ''} — ${o.device_model || ''} (${o.master_username || 'без мастера'})`
                }))}
              />
            </Form.Item>
          )}
          {txType === 'expense' && (
            <>
              <Form.Item name="is_parts" valuePropName="checked">
                <Checkbox onChange={(e) => { if (!e.target.checked) txForm.setFieldValue('order_id', undefined) }}>
                  Запчасти для мастера (вычет из ЗП 40%)
                </Checkbox>
              </Form.Item>
              <Form.Item noStyle shouldUpdate={(prev, cur) => prev.is_parts !== cur.is_parts}>
                {({ getFieldValue }) => getFieldValue('is_parts') ? (
                  <Form.Item label="Заказ и мастер" name="order_id">
                    <Select
                      showSearch
                      placeholder="Выберите заказ"
                      filterOption={false}
                      onSearch={searchOrders}
                      allowClear
                      options={orderList.map((o: any) => ({
                        value: o.id,
                        label: `#${o.id} ${o.client_name || ''} — ${o.device_model || ''} (${o.master_username || 'без мастера'})`
                      }))}
                    />
                  </Form.Item>
                ) : null}
              </Form.Item>
            </>
          )}
          <Form.Item label="Комментарий" name="comment">
            <Input placeholder="Описание операции..." />
          </Form.Item>
        </Form>
      </Modal>

      {/* Модалка приёма оплаты */}
      <Modal
        title={`💰 Оплата заказа #${selectedOrder?.id || ''}`}
        open={paymentModal}
        onOk={handlePayment}
        onCancel={() => setPaymentModal(false)}
        confirmLoading={printing}
        okText="Провести оплату и выдать"
        width={500}
      >
        {selectedOrder && (
          <>
            <Card size="small" style={{marginBottom: 16, background: isDark ? '#1e1e36' : '#f5f5f5'}}>
              <Row gutter={12}>
                <Col span={12}><Text type="secondary">Клиент:</Text><br/><Text strong>{selectedOrder.client_name}</Text></Col>
                <Col span={12}><Text type="secondary">Телефон:</Text><br/><Text>{selectedOrder.client_phone}</Text></Col>
              </Row>
              <Row gutter={12} style={{marginTop: 8}}>
                <Col span={12}><Text type="secondary">Устройство:</Text><br/><Text>{selectedOrder.device_model}</Text></Col>
                <Col span={12}><Text type="secondary">Мастер:</Text><br/><Text>{selectedOrder.master_username || '—'}</Text></Col>
              </Row>
              <Divider style={{margin: '8px 0'}} />
              <Row>
                <Col span={12}><Text type="secondary">К оплате:</Text></Col>
                <Col span={12}><Text strong style={{fontSize: 18, color: '#1890ff'}}>{selectedOrder.total_cost?.toFixed(2)}₽</Text></Col>
              </Row>
            </Card>

            <Form form={paymentForm} layout="vertical">
              <Form.Item label="Сумма оплаты" name="amount" rules={[{required: true}]}>
                <InputNumber min={0} style={{width: '100%'}} size="large" />
              </Form.Item>

              <Form.Item label="Способ оплаты" name="method" initialValue="cash">
                <Select size="large">
                  <Select.Option value="cash">💵 Наличные</Select.Option>
                  <Select.Option value="card">💳 Карта</Select.Option>
                  <Select.Option value="transfer">📱 Перевод</Select.Option>
                  <Select.Option value="invoice">🧾 Счёт</Select.Option>
                </Select>
              </Form.Item>

              <Divider style={{margin: '12px 0'}} />

              <Form.Item label={<Text strong>Печать документов</Text>}>
                <Space direction="vertical">
                  <Form.Item name="print_receipt" valuePropName="checked" initialValue={true} style={{margin: 0}}>
                    <Checkbox>📄 Квитанция приёма</Checkbox>
                  </Form.Item>
                  <Form.Item name="print_diagnostic" valuePropName="checked" style={{margin: 0}}>
                    <Checkbox>🔍 Акт диагностики</Checkbox>
                  </Form.Item>
                  <Form.Item name="print_act" valuePropName="checked" initialValue={true} style={{margin: 0}}>
                    <Checkbox>📋 Акт выполненных работ</Checkbox>
                  </Form.Item>
                  <Form.Item name="print_invoice" valuePropName="checked" style={{margin: 0}}>
                    <Checkbox>💰 Счёт</Checkbox>
                  </Form.Item>
                </Space>
              </Form.Item>

              <Form.Item label={<Text strong>Предпросмотр</Text>}>
                <Space direction="vertical">
                  <Button size="small" icon={<EyeOutlined />} onClick={() => {
                    const t = localStorage.getItem('token') || ''
                    window.open(`/api/documents/print/${selectedOrder?.id}/receipt?token=${t}`, '_blank')
                  }}>👁️ Квитанция</Button>
                  <Button size="small" icon={<EyeOutlined />} onClick={() => {
                    const t = localStorage.getItem('token') || ''
                    window.open(`/api/documents/print/${selectedOrder?.id}/diagnostic_act?token=${t}`, '_blank')
                  }}>👁️ Диагностика</Button>
                  <Button size="small" icon={<EyeOutlined />} onClick={() => {
                    const t = localStorage.getItem('token') || ''
                    window.open(`/api/documents/print/${selectedOrder?.id}/work_act?token=${t}`, '_blank')
                  }}>👁️ Акт</Button>
                  <Button size="small" icon={<EyeOutlined />} onClick={() => {
                    const t = localStorage.getItem('token') || ''
                    window.open(`/api/documents/print/${selectedOrder?.id}/invoice?token=${t}`, '_blank')
                  }}>👁️ Счёт</Button>
                </Space>
              </Form.Item>

              <Alert
                message="После оплаты статус заказа изменится на «Выдан»"
                type="info"
                showIcon
                style={{marginTop: 8}}
              />
            </Form>
          </>
        )}
      </Modal>
    </div>
  )
}

export default CashPage
