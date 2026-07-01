import React, { useState, useEffect } from 'react'
import { Table, Form, Input, InputNumber, Switch, Button, Space, message, Card, Typography, Tag, Divider, List, Empty, Drawer, Statistic, Row, Col } from 'antd'
import { SaveOutlined, ClockCircleOutlined, DollarOutlined, MinusCircleOutlined, WalletOutlined, EyeOutlined } from '@ant-design/icons'
import api from '../api'
import dayjs from 'dayjs'

const { Text, Title } = Typography

interface DaySchedule {
  id: number | null
  day_of_week: number
  day_name: string
  is_working_day: boolean
  start_time: string
  end_time: string
  lunch_start: string | null
  lunch_end: string | null
  description: string
}

const DAYS = [
  'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье'
]

const WorkingHoursTab: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const [schedule, setSchedule] = useState<DaySchedule[]>([])
  const [summary, setSummary] = useState<any>(null)
  const [editingId, setEditingId] = useState<number | null>(null)

  // Для истории смен
  const [shiftsDrawerOpen, setShiftsDrawerOpen] = useState(false)
  const [shifts, setShifts] = useState<any[]>([])
  const [selectedShift, setSelectedShift] = useState<any>(null)
  const [shiftTransactions, setShiftTransactions] = useState<any[]>([])
  const [transactionsLoading, setTransactionsLoading] = useState(false)

  useEffect(() => {
    loadSchedule()
  }, [])

  const loadSchedule = async () => {
    setLoading(true)
    try {
      const resp = await api.get('/settings/working-hours')
      const days = resp.data
      
      const scheduleData: DaySchedule[] = DAYS.map((name, idx) => {
        const day = days.find((d: any) => d.day_of_week === idx + 1)
        return {
          id: day?.id || null,
          day_of_week: idx + 1,
          day_name: name,
          is_working_day: day?.is_working_day ?? true,
          start_time: day?.start_time || '10:00',
          end_time: day?.end_time || '20:00',
          lunch_start: day?.lunch_start || null,
          lunch_end: day?.lunch_end || null,
          description: day?.description || '',
        }
      })
      
      setSchedule(scheduleData)
      
      // Загружаем сводку
      const summaryResp = await api.get('/settings/working-hours/schedule')
      setSummary(summaryResp.data)
    } catch (e: any) {
      message.error('Ошибка загрузки графика')
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const loadShifts = async () => {
    try {
      const resp = await api.get('/cash/shift/history?limit=50')
      setShifts(Array.isArray(resp.data) ? resp.data : resp.data.shifts || [])
      setShiftsDrawerOpen(true)
    } catch (e: any) {
      message.error('Ошибка загрузки смен')
      console.error(e)
    }
  }

  const loadShiftTransactions = async (shift: any) => {
    setTransactionsLoading(true)
    setSelectedShift(shift)
    try {
      const resp = await api.get(`/cash/transactions?shift_id=${shift.id}&limit=200`)
      setShiftTransactions(resp.data)
    } catch (e: any) {
      message.error('Ошибка загрузки транзакций')
      console.error(e)
    } finally {
      setTransactionsLoading(false)
    }
  }

  const handleSave = async (record: DaySchedule) => {
    try {
      const data = {
        day_of_week: record.day_of_week,
        day_name: record.day_name,
        is_working_day: record.is_working_day,
        start_time: record.start_time,
        end_time: record.end_time,
        lunch_start: record.lunch_start,
        lunch_end: record.lunch_end,
        description: record.description,
      }
      
      if (record.id) {
        await api.patch(`/settings/working-hours/${record.id}`, data)
        message.success('День обновлён')
      } else {
        await api.post('/settings/working-hours', data)
        message.success('День создан')
      }
      
      setEditingId(null)
      loadSchedule()
    } catch (e: any) {
      message.error(e.response?.data?.detail || 'Ошибка сохранения')
    }
  }

  const handleCancel = () => {
    setEditingId(null)
    loadSchedule()
  }

  const columns = [
    {
      title: 'День',
      dataIndex: 'day_name',
      key: 'day_name',
      width: 140,
    },
    {
      title: 'Рабочий?',
      dataIndex: 'is_working_day',
      key: 'is_working_day',
      width: 100,
      render: (isWorking: boolean, record: DaySchedule) => {
        if (editingId === record.id) {
          return (
            <Switch
              checked={isWorking}
              onChange={(checked) => {
                const newSchedule = schedule.map(s =>
                  s.id === record.id ? { ...s, is_working_day: checked } : s
                )
                setSchedule(newSchedule)
              }}
            />
          )
        }
        return isWorking ? <Tag color="green">✅ Да</Tag> : <Tag color="default">❌ Выходной</Tag>
      },
    },
    {
      title: 'Начало',
      dataIndex: 'start_time',
      key: 'start_time',
      width: 100,
      render: (time: string, record: DaySchedule) => {
        if (editingId === record.id) {
          return (
            <Input
              value={time}
              onChange={(e) => {
                const newSchedule = schedule.map(s =>
                  s.id === record.id ? { ...s, start_time: e.target.value } : s
                )
                setSchedule(newSchedule)
              }}
              placeholder="HH:MM"
              style={{ width: 80 }}
            />
          )
        }
        return <Text code>{time}</Text>
      },
    },
    {
      title: 'Конец',
      dataIndex: 'end_time',
      key: 'end_time',
      width: 100,
      render: (time: string, record: DaySchedule) => {
        if (editingId === record.id) {
          return (
            <Input
              value={time}
              onChange={(e) => {
                const newSchedule = schedule.map(s =>
                  s.id === record.id ? { ...s, end_time: e.target.value } : s
                )
                setSchedule(newSchedule)
              }}
              placeholder="HH:MM"
              style={{ width: 80 }}
            />
          )
        }
        return <Text code>{time}</Text>
      },
    },
    {
      title: 'Обед',
      key: 'lunch',
      width: 140,
      render: (_: any, record: DaySchedule) => {
        if (editingId === record.id) {
          return (
            <Space size="small">
              <Input
                value={record.lunch_start || ''}
                onChange={(e) => {
                  const newSchedule = schedule.map(s =>
                    s.id === record.id ? { ...s, lunch_start: e.target.value || null } : s
                  )
                  setSchedule(newSchedule)
                }}
                placeholder="Начало"
                style={{ width: 70 }}
              />
              <Input
                value={record.lunch_end || ''}
                onChange={(e) => {
                  const newSchedule = schedule.map(s =>
                    s.id === record.id ? { ...s, lunch_end: e.target.value || null } : s
                  )
                  setSchedule(newSchedule)
                }}
                placeholder="Конец"
                style={{ width: 70 }}
              />
            </Space>
          )
        }
        return record.lunch_start ? (
          <Text type="secondary">{record.lunch_start}—{record.lunch_end}</Text>
        ) : (
          <Text type="secondary">—</Text>
        )
      },
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 120,
      render: (_: any, record: DaySchedule) => {
        if (editingId === record.id) {
          return (
            <Space>
              <Button
                type="primary"
                size="small"
                icon={<SaveOutlined />}
                onClick={() => handleSave(record)}
              >
                Сохранить
              </Button>
              <Button size="small" onClick={handleCancel}>
                Отмена
              </Button>
            </Space>
          )
        }
        return (
          <Button
            size="small"
            icon={<ClockCircleOutlined />}
            onClick={() => setEditingId(record.id)}
          >
            Изменить
          </Button>
        )
      },
    },
  ]

  return (
    <div>
      <Card
        title="🕒 Настройки рабочего времени"
        extra={
          <Space>
            <Button 
              icon={<EyeOutlined />} 
              onClick={loadShifts}
            >
              📋 История смен
            </Button>
            {summary && (
              <Space split={<Divider type="vertical" />}>
                <Statistic title="Рабочих дней" value={summary.work_days_count} valueStyle={{ fontSize: 16 }} />
                <Statistic title="Часов в неделю" value={summary.total_hours_per_week} valueStyle={{ fontSize: 16 }} />
              </Space>
            )}
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={schedule}
          rowKey="day_of_week"
          pagination={false}
          loading={loading}
          size="middle"
        />
      </Card>

      <Card title="💡 Подсказки" size="small" style={{ marginTop: 16 }}>
        <ul>
          <li>Формат времени: <Text code>ЧЧ:ММ</Text> (например, <Text code>10:00</Text>, <Text code>20:00</Text>)</li>
          <li>Обед не обязателен — оставьте пустым если нет перерыва</li>
          <li>Часы в неделю считаются автоматически с учётом обеденных перерывов</li>
          <li>Настройки влияют на расчёт зарплаты для сотрудников с фиксированной ставкой</li>
        </ul>
      </Card>

      {/* Выдвижная панель с историей смен */}
      <Drawer
        title="📋 История кассовых смен"
        placement="right"
        width={900}
        open={shiftsDrawerOpen}
        onClose={() => {
          setShiftsDrawerOpen(false)
          setSelectedShift(null)
          setShiftTransactions([])
        }}
      >
        <Title level={5}>Смены</Title>
        <Table
          dataSource={shifts}
          rowKey="id"
          pagination={{ pageSize: 8 }}
          size="small"
          onRow={(record) => ({
            onClick: () => loadShiftTransactions(record),
            style: { cursor: 'pointer' }
          })}
          columns={[
            { title: '#', dataIndex: 'id', key: 'id', width: 60, render: (id: number) => `#${id}` },
            { 
              title: 'Статус', 
              key: 'status', 
              width: 90,
              render: (_: any, r: any) => r.is_open ? <Tag color="green">🟢</Tag> : <Tag>🔒</Tag>
            },
            { title: 'Открыта', dataIndex: 'opened_at', key: 'opened_at', width: 130, render: (v: string) => dayjs(v).format('DD.MM HH:mm') },
            { title: 'Закрыта', dataIndex: 'closed_at', key: 'closed_at', width: 130, render: (v: string) => v ? dayjs(v).format('DD.MM HH:mm') : '—' },
            { 
              title: 'Начало', 
              dataIndex: 'initial_amount', 
              key: 'initial_amount', 
              width: 80,
              align: 'right' as const,
              render: (v: number) => `${v.toFixed(0)}₽`
            },
            { 
              title: 'Конец', 
              dataIndex: 'final_amount', 
              key: 'final_amount', 
              width: 80,
              align: 'right' as const,
              render: (v: number) => `${v.toFixed(0)}₽`
            },
            { 
              title: 'Приход', 
              key: 'income', 
              width: 80,
              align: 'right' as const,
              render: (_: any, r: any) => <Text style={{ color: '#52c41a' }}>+{r.income?.toFixed(0) || 0}₽</Text>
            },
            { 
              title: 'Расход', 
              key: 'expense', 
              width: 80,
              align: 'right' as const,
              render: (_: any, r: any) => <Text style={{ color: '#f5222d' }}>-{r.expense?.toFixed(0) || 0}₽</Text>
            },
          ]}
        />

        {selectedShift && (
          <>
            <Divider />
            <Title level={5}>
              Транзакции смены #{selectedShift.id} 
              {selectedShift.is_open && <Tag color="green">Открыта</Tag>}
            </Title>
            
            {transactionsLoading ? (
              <div style={{ textAlign: 'center', padding: 40 }}><Empty description="Загрузка..." /></div>
            ) : shiftTransactions.length === 0 ? (
              <Empty description="Нет транзакций" />
            ) : (
              <List
                itemLayout="horizontal"
                dataSource={shiftTransactions}
                renderItem={(item: any) => {
                  const isIncome = item.transaction_type === 'income'
                  const orderId = item.order_id
                  
                  return (
                    <List.Item>
                      <List.Item.Meta
                        avatar={
                          isIncome ? 
                            <DollarOutlined style={{ fontSize: 20, color: '#52c41a' }} /> :
                            item.comment?.includes('ЗП') ?
                              <WalletOutlined style={{ fontSize: 20, color: '#fa8c16' }} /> :
                              <MinusCircleOutlined style={{ fontSize: 20, color: '#f5222d' }} />
                        }
                        title={
                          <Space>
                            <Text strong style={{ color: isIncome ? '#52c41a' : '#f5222d' }}>
                              {isIncome ? '+' : ''}{item.amount.toFixed(2)}₽
                            </Text>
                            <Tag color={isIncome ? 'green' : item.comment?.includes('ЗП') ? 'orange' : 'red'}>
                              {isIncome ? 'Приход' : item.comment?.includes('ЗП') ? 'Зарплата' : 'Расход'}
                            </Tag>
                            {orderId && (
                              <Tag>Заказ #{orderId}</Tag>
                            )}
                            <Text type="secondary">{dayjs(item.created_at).format('DD.MM HH:mm:ss')}</Text>
                          </Space>
                        }
                        description={
                          <div>
                            {item.comment && <div>{item.comment}</div>}
                            {item.created_by && <Text type="secondary">Кассир: #{item.created_by}</Text>}
                          </div>
                        }
                      />
                    </List.Item>
                  )
                }}
              />
            )}
          </>
        )}
      </Drawer>
    </div>
  )
}

export default WorkingHoursTab
