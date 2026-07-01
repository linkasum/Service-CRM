import React, { useState, useEffect, useCallback } from 'react'
import {
  Card, Typography, Button, Modal, Checkbox, Tag, Spin, message, Space, Row, Col, Badge
} from 'antd'
import { Calendar } from 'antd'
import { LeftOutlined, RightOutlined } from '@ant-design/icons'
import dayjs, { Dayjs } from 'dayjs'
import 'dayjs/locale/ru'
import api from '../api'
import { useTheme } from '../contexts/ThemeContext'

dayjs.locale('ru')

const { Title, Text } = Typography

interface ScheduleItem {
  id: number
  user_id: number
  date: string
  user_name: string
  user_role: string
  created_at: string
}

interface User {
  id: number
  username: string
  full_name: string
  role_name: string
  is_active: boolean
}

const ROLE_COLORS: Record<string, string> = {
  master: 'blue',
  acceptor: 'green',
  admin: 'orange',
}

const ROLE_LABELS: Record<string, string> = {
  master: 'Мастер',
  acceptor: 'Приёмщик',
  admin: 'Админ',
}

function getRoleColor(role: string): string {
  const lower = (role || '').toLowerCase()
  for (const key of Object.keys(ROLE_COLORS)) {
    if (lower.includes(key)) return ROLE_COLORS[key]
  }
  return 'default'
}

function getRoleLabel(role: string): string {
  const lower = (role || '').toLowerCase()
  for (const key of Object.keys(ROLE_LABELS)) {
    if (lower.includes(key)) return ROLE_LABELS[key]
  }
  return role
}

const MONTH_NAMES = [
  'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
  'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь',
]

const SchedulePage: React.FC = () => {
  const { mode } = useTheme()
  const isDark = mode === 'dark'

  const [currentMonth, setCurrentMonth] = useState<Dayjs>(dayjs().startOf('month'))
  const [scheduleItems, setScheduleItems] = useState<ScheduleItem[]>([])
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(false)
  const [usersLoading, setUsersLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [selectedDate, setSelectedDate] = useState<Dayjs | null>(null)
  const [modalLoading, setModalLoading] = useState(false)
  const [checkedUserIds, setCheckedUserIds] = useState<number[]>([])
  const [originalUserIds, setOriginalUserIds] = useState<number[]>([])

  const loadSchedule = useCallback(async (month: Dayjs) => {
    setLoading(true)
    try {
      const monthStr = month.format('YYYY-MM')
      const resp = await api.get(`/work-schedule?month=${monthStr}`)
      setScheduleItems(resp.data?.items ?? [])
    } catch {
      // API may not be ready yet
    } finally {
      setLoading(false)
    }
  }, [])

  const loadUsers = useCallback(async () => {
    setUsersLoading(true)
    try {
      // Primary endpoint for the schedule page (available for authenticated users).
      const resp = await api.get('/work-schedule/users')
      const data = resp.data
      const items: User[] = (data?.items ?? (Array.isArray(data) ? data : [])) as User[]
      setUsers(items.filter(u => u.is_active !== false))
    } catch {
      try {
        // Fallback for older backend versions.
        const resp = await api.get('/users/', { params: { is_active: true } })
        const data = resp.data
        const items: User[] = (data?.items ?? (Array.isArray(data) ? data : [])) as User[]
        setUsers(items.filter(u => u.is_active !== false))
      } catch {
        // API may not be ready yet
        setUsers([])
      }
    } finally {
      setUsersLoading(false)
    }
  }, [])

  useEffect(() => {
    loadUsers()
  }, [loadUsers])

  useEffect(() => {
    loadSchedule(currentMonth)
  }, [currentMonth, loadSchedule])

  // Map date string -> ScheduleItems
  const scheduleByDate = React.useMemo(() => {
    const map: Record<string, ScheduleItem[]> = {}
    for (const item of scheduleItems) {
      if (!map[item.date]) map[item.date] = []
      map[item.date].push(item)
    }
    return map
  }, [scheduleItems])

  const handlePrevMonth = () => setCurrentMonth(m => m.subtract(1, 'month'))
  const handleNextMonth = () => setCurrentMonth(m => m.add(1, 'month'))

  const handleDayClick = (date: Dayjs) => {
    setSelectedDate(date)
    const dateStr = date.format('YYYY-MM-DD')
    const assigned = (scheduleByDate[dateStr] ?? []).map(i => i.user_id)
    setCheckedUserIds(assigned)
    setOriginalUserIds(assigned)
    setModalOpen(true)
  }

  const handleModalOk = async () => {
    if (!selectedDate) return
    setModalLoading(true)
    const dateStr = selectedDate.format('YYYY-MM-DD')
    const toAdd = checkedUserIds.filter(id => !originalUserIds.includes(id))
    const toRemove = originalUserIds.filter(id => !checkedUserIds.includes(id))

    try {
      // Add new assignments
      for (const userId of toAdd) {
        await api.post('/work-schedule', { user_id: userId, date: dateStr })
      }
      // Remove removed assignments
      for (const userId of toRemove) {
        const item = scheduleItems.find(i => i.user_id === userId && i.date === dateStr)
        if (item) {
          await api.delete(`/work-schedule/${item.id}`)
        }
      }
      message.success('График обновлён')
      await loadSchedule(currentMonth)
      setModalOpen(false)
    } catch {
      message.error('Ошибка при сохранении')
    } finally {
      setModalLoading(false)
    }
  }

  const handleModalCancel = () => {
    setModalOpen(false)
    setSelectedDate(null)
  }

  const dateCellRender = (value: Dayjs) => {
    const dateStr = value.format('YYYY-MM-DD')
    const items = scheduleByDate[dateStr] ?? []
    // Only render for current visible month
    if (value.month() !== currentMonth.month()) return null
    return (
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
        {items.map(item => (
          <Tag
            key={item.id}
            color={getRoleColor(item.user_role)}
            style={{ fontSize: 11, padding: '0 4px', marginBottom: 2, lineHeight: '18px' }}
          >
            {item.user_name}
          </Tag>
        ))}
      </div>
    )
  }

  const cellRender = (current: Dayjs, info: { type: string }) => {
    if (info.type === 'date') return dateCellRender(current)
    return null
  }

  const isWeekend = (d: Dayjs) => {
    const dow = d.day()
    return dow === 0 || dow === 6
  }

  const fullCellRender = (value: Dayjs, info: { type: string }) => {
    if (info.type !== 'date') return info.originNode
    const dateStr = value.format('YYYY-MM-DD')
    const items = scheduleByDate[dateStr] ?? []
    const isCurrentMonth = value.month() === currentMonth.month()
    const weekend = isWeekend(value)
    const isToday = value.isSame(dayjs(), 'day')
    const count = items.length

    return (
      <div
        onClick={() => isCurrentMonth && handleDayClick(value)}
        style={{
          minHeight: 90,
          padding: '2px 4px',
          cursor: isCurrentMonth ? 'pointer' : 'default',
          backgroundColor: isToday ? (isDark ? '#1a3a5c' : '#e6f4ff') :
            isCurrentMonth ? (weekend ? (isDark ? '#2a1a1a' : '#fff5f5') : undefined) :
            isDark ? '#1a1a1a' : '#fafafa',
          borderRadius: 4,
          border: isToday ? '2px solid #1677ff' : isCurrentMonth ? `1px solid ${isDark ? '#333' : '#e8e8e8'}` : `1px solid ${isDark ? '#222' : '#f0f0f0'}`,
          opacity: isCurrentMonth ? 1 : 0.4,
        }}
        title={isCurrentMonth ? `${count} чел: ${items.map(i => i.user_name).join(', ')}` : ''}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 2 }}>
          <span style={{ fontWeight: isToday ? 700 : 500, fontSize: 13, color: isToday ? '#1677ff' : isDark ? '#ccc' : '#555' }}>
            {value.date()}
          </span>
          {count > 0 && (
            <Badge count={count} size="small" style={{ backgroundColor: '#1677ff' }} />
          )}
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 1, maxHeight: 60, overflow: 'hidden' }}>
          {items.slice(0, 8).map(item => (
            <span
              key={item.id}
              style={{
                fontSize: 10,
                padding: '1px 4px',
                borderRadius: 3,
                backgroundColor: getRoleColor(item.user_role),
                color: '#fff',
                whiteSpace: 'nowrap',
                lineHeight: '16px',
              }}
            >
              {item.user_name}
            </span>
          ))}
          {count > 8 && <span style={{ fontSize: 10, color: '#888' }}>+{count - 8}</span>}
        </div>
      </div>
    )
  }

  const formatModalDate = (d: Dayjs) => {
    return d.format('D MMMM YYYY')
  }

  return (
    <div>
      <Card
        bordered={false}
        style={{ marginBottom: 16 }}
        bodyStyle={{ paddingBottom: 8 }}
      >
        <Row align="middle" gutter={16}>
          <Col>
            <Title level={3} style={{ margin: 0 }}>График работы</Title>
          </Col>
          <Col flex={1} />
          <Col>
            <Space>
              <Button icon={<LeftOutlined />} onClick={handlePrevMonth} />
              <Text strong style={{ fontSize: 16, minWidth: 160, display: 'inline-block', textAlign: 'center' }}>
                {MONTH_NAMES[currentMonth.month()]} {currentMonth.year()}
              </Text>
              <Button icon={<RightOutlined />} onClick={handleNextMonth} />
            </Space>
          </Col>
        </Row>
      </Card>

      <Card bordered={false}>
        <Spin spinning={loading}>
          <Calendar
            value={currentMonth.date(1)}
            fullscreen
            fullCellRender={fullCellRender}
            headerRender={() => null}
            onSelect={(date, info) => {
              if (info?.source === 'date' && date.month() === currentMonth.month()) {
                handleDayClick(date)
              }
            }}
            validRange={[currentMonth.startOf('month'), currentMonth.endOf('month').add(6, 'day')]}
          />
        </Spin>
      </Card>

      <Modal
        title={selectedDate ? `Сотрудники на ${formatModalDate(selectedDate)}` : 'Назначение'}
        open={modalOpen}
        onOk={handleModalOk}
        onCancel={handleModalCancel}
        confirmLoading={modalLoading}
        okText="Сохранить"
        cancelText="Отмена"
        width={500}
      >
        <Spin spinning={usersLoading}>
          {users.length === 0 ? (
            <Text type="secondary">Нет сотрудников</Text>
          ) : (
            <div style={{ maxHeight: 400, overflow: 'auto' }}>
              <Checkbox.Group value={checkedUserIds} onChange={(vals) => setCheckedUserIds(vals as number[])}>
                {['admin', 'acceptor', 'master'].map(role => {
                  const roleUsers = users.filter(u => (u.role_name || '').toLowerCase().includes(role))
                  if (!roleUsers.length) return null
                  return (
                    <div key={role} style={{ marginBottom: 12 }}>
                      <div style={{ fontWeight: 600, marginBottom: 4, fontSize: 13, color: isDark ? '#aaa' : '#666' }}>
                        {getRoleLabel(role)}
                      </div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                        {roleUsers.map(user => (
                          <Checkbox key={user.id} value={user.id}>
                            {user.full_name || user.username}
                          </Checkbox>
                        ))}
                      </div>
                    </div>
                  )
                })}
              </Checkbox.Group>
            </div>
          )}
        </Spin>
      </Modal>
    </div>
  )
}

export default SchedulePage
