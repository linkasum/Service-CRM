import React, { useEffect, useState } from 'react'
import { Table, Tag } from 'antd'
import dayjs from 'dayjs'
import api from '../api'

const eventColors: Record<string, string> = {
  order_created: 'blue', order_status_changed: 'orange',
  comment_added: 'green', payment_added: 'purple',
}
const eventLabels: Record<string, string> = {
  order_created: 'Новый заказ', order_status_changed: 'Смена статуса',
  comment_added: 'Комментарий', payment_added: 'Платёж',
}

const NotificationsTab: React.FC = () => {
  const [logs, setLogs] = useState<any[]>([])

  const load = async () => {
    try { const r = await api.get('/notifications', { params: { limit: 100 } }); setLogs(r.data || []) } catch {}
  }

  useEffect(() => { load() }, [])

  useEffect(() => {
    const h = () => load()
    window.addEventListener('crm-notify', h)
    return () => window.removeEventListener('crm-notify', h)
  }, [])

  return (
    <div>
      <h3>Лог уведомлений ({logs.length})</h3>
      <Table dataSource={logs} rowKey="id" size="small" pagination={{ pageSize: 20 }}
        columns={[
          { title: 'Время', dataIndex: 'created_at', width: 140, render: (v: string) => dayjs(v).format('DD.MM HH:mm') },
          { title: 'Тип', dataIndex: 'event_type', width: 130, render: (v: string) => <Tag color={eventColors[v] || 'default'}>{eventLabels[v] || v}</Tag> },
          { title: 'Кто', dataIndex: 'username', width: 100 },
          { title: 'Сообщение', dataIndex: 'message' },
          { title: 'Заказ', dataIndex: 'order_id', width: 60, render: (v: number) => v ? `#${v}` : '' },
        ]}
      />
    </div>
  )
}

export default NotificationsTab
