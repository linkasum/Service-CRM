import React, { useState, useEffect } from 'react'
import { Card, Table, Button, Space, message, Empty, Tag, Divider, List, Typography, Statistic, Row, Col, Badge, Spin } from 'antd'
import { EyeOutlined, DollarOutlined, WalletOutlined, MinusCircleOutlined, ReloadOutlined, HomeOutlined } from '@ant-design/icons'
import api from '../api'
import dayjs from 'dayjs'

const { Text, Title } = Typography

interface CashTransaction {
  id: number
  shift_id: number
  transaction_type: 'income' | 'expense' | 'cashout'
  payment_method?: 'cash' | 'card'
  amount: number
  comment: string
  order_id?: number
  created_at: string
  created_by?: number
}

const CashShiftsTab: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const [shifts, setShifts] = useState<any[]>([])
  const [selectedShift, setSelectedShift] = useState<any | null>(null)
  const [shiftTransactions, setShiftTransactions] = useState<CashTransaction[]>([])
  const [transactionsLoading, setTransactionsLoading] = useState(false)
  const [currentShift, setCurrentShift] = useState<any | null>(null)
  const [summary, setSummary] = useState<any>(null)

  useEffect(() => {
    loadAll()
  }, [])

  const loadAll = async () => {
    setLoading(true)
    try {
      const currResp = await api.get('/cash/shift/current')
      setCurrentShift(currResp.data || null)
      
      const histResp = await api.get('/cash/shift/history?limit=50')
      const historyData = histResp.data || { shifts: [], total_cash_in_cache: 0 }
      setShifts(historyData.shifts || [])
      
      const totalCash = historyData.total_cash_in_cache || 0
      setSummary({ totalShifts: (historyData.shifts || []).length, totalCash })
    } catch (e: any) {
      message.error('Ошибка загрузки данных кассы: ' + (e.message || ''))
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const loadShiftTransactions = async (shift: any) => {
    if (!shift || !shift.id) return
    
    setTransactionsLoading(true)
    setSelectedShift(shift)
    try {
      const resp = await api.get(`/cash/transactions?shift_id=${shift.id}&limit=200`)
      const txs = resp.data || []
      setShiftTransactions(Array.isArray(txs) ? txs : [])
    } catch (e: any) {
      message.error('Ошибка загрузки транзакций')
      console.error(e)
      setShiftTransactions([])
    } finally {
      setTransactionsLoading(false)
    }
  }

  const columns = [
    { title: 'Смена', dataIndex: 'id', key: 'id', width: 60, render: (id: number) => <Text strong>#{id}</Text> },
    { title: 'Статус', key: 'status', width: 80,
      render: (_: any, r: any) => r.is_open ? <Badge status="success" text="Открыта" /> : <Badge status="default" text="Закрыта" />
    },
    { title: 'Кто', key: 'who', width: 100,
      render: (_: any, r: any) => (
        <div>
          <div style={{ fontSize: 11 }}>{r.opened_by_username || '—'}</div>
          {!r.is_open && <div style={{ fontSize: 10, color: '#888' }}>→ {r.closed_by_username || '—'}</div>}
        </div>
      )
    },
    { title: 'Дата', key: 'date', width: 100,
      render: (_: any, r: any) => r.opened_at ? dayjs(r.opened_at).format('DD.MM') : '—'
    },
    { title: 'Начало', dataIndex: 'initial_amount', key: 'init', width: 80, align: 'right' as const,
      render: (v: number) => <Text>{(v||0).toFixed(0)}₽</Text> },
    { title: 'Наличные', key: 'cash', width: 80, align: 'right' as const,
      render: (_: any, r: any) => <Text style={{ color: '#52c41a' }}>+{(r.cash_income||0).toFixed(0)}₽</Text> },
    { title: 'Безнал', key: 'card', width: 80, align: 'right' as const,
      render: (_: any, r: any) => <Text style={{ color: '#1890ff' }}>+{(r.card_income||0).toFixed(0)}₽</Text> },
    { title: 'Итог (нал)', dataIndex: 'final_amount', key: 'final', width: 80, align: 'right' as const,
      render: (v: number) => <Text strong style={{ fontSize: 13 }}>{(v||0).toFixed(0)}₽</Text> },
    { title: '', key: 'actions', width: 60,
      render: (_: any, r: any) => (
        <Button size="small" type="text" icon={<EyeOutlined />} onClick={(e) => { e.stopPropagation(); loadShiftTransactions(r) }} />
      ),
    },
  ]

  const txsArray = Array.isArray(shiftTransactions) ? shiftTransactions : []
  const incomeTotal = txsArray.filter((t: any) => t.transaction_type === 'income').reduce((sum: number, t: any) => sum + (t.amount || 0), 0)
  const expenseTotal = txsArray.filter((t: any) => t.transaction_type !== 'income').reduce((sum: number, t: any) => sum + Math.abs(t.amount || 0), 0)

  return (
    <div>
      <Card 
        title={<><HomeOutlined /> Текущая смена</>}
        size="small"
        style={{ marginBottom: 16 }}
        extra={<Button icon={<ReloadOutlined />} onClick={loadAll}>Обновить</Button>}
      >
        {loading ? <Text>Загрузка...</Text> : currentShift?.is_open ? (
          <Row gutter={16}>
            <Col span={6}><Statistic title="Статус" value="🟢 Открыта" valueStyle={{ fontSize: 18 }} /></Col>
            <Col span={6}><Statistic title="Открыта" value={currentShift.opened_at ? dayjs(currentShift.opened_at).format('DD.MM HH:mm') : '—'} valueStyle={{ fontSize: 16 }} /></Col>
            <Col span={6}><Statistic title="Начальная сумма" value={currentShift.initial_amount || 0} precision={2} suffix="₽" valueStyle={{ fontSize: 16 }} /></Col>
            <Col span={6}><Statistic title="Смена #" value={currentShift.id || '—'} valueStyle={{ fontSize: 16 }} /></Col>
          </Row>
        ) : (
          <Text type="secondary">Смена закрыта. Откройте новую смену для работы.</Text>
        )}
      </Card>

      {summary && (
        <Card size="small" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={8}><Statistic title="Всего смен" value={summary.totalShifts || 0} /></Col>
            <Col span={8}><Statistic title="Текущий остаток" value={summary.totalCash || 0} precision={2} suffix="₽" valueStyle={{ color: '#1890ff' }} /></Col>
            <Col span={8}><Statistic title="Последняя смена" value={shifts[0]?.id ? `#${shifts[0].id}` : '—'} /></Col>
          </Row>
        </Card>
      )}

      <Card title="📋 История смен" size="small" extra={<Text type="secondary">Кликните на смену для просмотра транзакций</Text>}>
        <Table
          dataSource={shifts}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          size="middle"
          onRow={(record) => ({ onClick: () => loadShiftTransactions(record), style: { cursor: 'pointer' } })}
          columns={columns}
        />
      </Card>

      {selectedShift && (
        <Card 
          title={`💰 Транзакции смены #${selectedShift.id}`}
          size="small"
          style={{ marginTop: 16 }}
          extra={
            <Space>
              <Tag color={selectedShift.is_open ? 'green' : 'default'}>{selectedShift.is_open ? '🟢 Открыта' : '🔒 Закрыта'}</Tag>
              <Button size="small" icon={<ReloadOutlined />} onClick={() => loadShiftTransactions(selectedShift)}>Обновить</Button>
            </Space>
          }
        >
          {transactionsLoading ? (
            <div style={{ textAlign: 'center', padding: 40 }}><Spin tip="Загрузка..." /></div>
          ) : txsArray.length === 0 ? (
            <Empty description="Нет транзакций в этой смене" />
          ) : (
            <>
              <Row gutter={16} style={{ marginBottom: 16 }}>
                <Col span={6}>
                  <Card size="small"><Statistic title="Всего транзакций" value={txsArray.length} valueStyle={{ fontSize: 18 }} /></Card>
                </Col>
                <Col span={6}>
                  <Card size="small"><Statistic title="Приход" value={incomeTotal} precision={2} suffix="₽" valueStyle={{ color: '#52c41a', fontSize: 18 }} /></Card>
                </Col>
                <Col span={6}>
                  <Card size="small"><Statistic title="Расход" value={expenseTotal} precision={2} suffix="₽" valueStyle={{ color: '#f5222d', fontSize: 18 }} /></Card>
                </Col>
                <Col span={6}>
                  <Card size="small"><Statistic title="Оборот" value={incomeTotal + expenseTotal} precision={2} suffix="₽" valueStyle={{ color: '#1890ff', fontSize: 18 }} /></Card>
                </Col>
              </Row>

              <List
                itemLayout="horizontal"
                dataSource={txsArray}
                renderItem={(item: CashTransaction) => {
                  const isIncome = item.transaction_type === 'income'
                  const isSalary = item.comment?.includes('ЗП') || item.comment?.includes('зарплата')
                  const orderId = item.order_id
                  const paymentMethod = item.payment_method || 'cash'
                  
                  return (
                    <List.Item>
                      <List.Item.Meta
                        avatar={isIncome ? <DollarOutlined style={{ fontSize: 24, color: '#52c41a' }} /> : isSalary ? <WalletOutlined style={{ fontSize: 24, color: '#fa8c16' }} /> : <MinusCircleOutlined style={{ fontSize: 24, color: '#f5222d' }} />}
                        title={
                          <Space>
                            <Text strong style={{ color: isIncome ? '#52c41a' : '#f5222d', fontSize: 16 }}>{isIncome ? '+' : ''}{(item.amount || 0).toFixed(2)}₽</Text>
                            <Tag color={isIncome ? 'green' : isSalary ? 'orange' : 'red'}>{isIncome ? 'Приход' : isSalary ? 'Зарплата' : 'Расход'}</Tag>
                            {orderId && <Tag>Заказ #{orderId}</Tag>}
                            <Tag icon={<HomeOutlined />} color={paymentMethod === 'cash' ? 'blue' : 'purple'}>{paymentMethod === 'cash' ? '💵 Наличные' : '💳 Карта'}</Tag>
                            <Text type="secondary">{item.created_at ? dayjs(item.created_at).format('DD.MM HH:mm:ss') : '—'}</Text>
                          </Space>
                        }
                        description={
                          <div>
                            {item.comment && <div style={{ marginBottom: 4 }}>{item.comment}</div>}
                            {item.created_by && <Text type="secondary">Кассир: #{item.created_by}</Text>}
                          </div>
                        }
                      />
                    </List.Item>
                  )
                }}
              />
            </>
          )}
        </Card>
      )}
    </div>
  )
}

export default CashShiftsTab
