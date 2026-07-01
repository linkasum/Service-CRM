import React from 'react'
import { Badge, Popover, List, Typography, Button, Space } from 'antd'
import { BellOutlined, SoundOutlined } from '@ant-design/icons'
import api from '../api'
import dayjs from 'dayjs'

const { Text } = Typography
const AudioContext = window.AudioContext || (window as any).webkitAudioContext

function playBeep(type: string) {
  try {
    const ctx = new AudioContext()
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.connect(gain); gain.connect(ctx.destination); gain.gain.value = 0.06
    switch (type) {
      case 'order_created':
        osc.frequency.value = 600; osc.type = 'sine'
        gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.2)
        osc.start(); osc.stop(ctx.currentTime + 0.3)
        break
      case 'order_status_changed':
        osc.frequency.value = 500; osc.type = 'triangle'
        gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.1)
        osc.start(); osc.stop(ctx.currentTime + 0.15)
        break
      case 'ready':
        osc.frequency.value = 800; osc.type = 'sine'
        osc.start(); osc.stop(ctx.currentTime + 0.1)
        setTimeout(() => { const o=ctx.createOscillator(); const g=ctx.createGain(); o.connect(g); g.connect(ctx.destination); g.gain.value=0.06; o.frequency.value=1000; o.start(); o.stop(ctx.currentTime+.1) }, 100)
        setTimeout(() => { const o=ctx.createOscillator(); const g=ctx.createGain(); o.connect(g); g.connect(ctx.destination); g.gain.value=0.06; o.frequency.value=1200; o.start(); o.stop(ctx.currentTime+.15) }, 200)
        break
      default: osc.frequency.value = 440; osc.start(); osc.stop(ctx.currentTime + 0.1)
    }
  } catch {}
}

const NotifyBell: React.FC = () => {
  const [notifications, setNotifications] = React.useState<any[]>([])
  const [unread, setUnread] = React.useState(0)
  const [muted, setMuted] = React.useState(false)
  const [open, setOpen] = React.useState(false)

  const loadLogs = async () => {
    try { const r = await api.get('/notifications', { params: { limit: 20 } }); setNotifications(r.data || []) } catch {}
  }

  React.useEffect(() => { loadLogs() }, [])

  React.useEffect(() => {
    const handler = (e: any) => {
      const data = e.detail || {}
      const type = data.type || ''
      if (!muted) {
        if (type === 'ready_pickup' || type === 'ready') playBeep('ready')
        else if (type) playBeep(type)
      }
      setUnread(u => u + 1)
      loadLogs()
    }
    window.addEventListener('crm-notify', handler)
    return () => window.removeEventListener('crm-notify', handler)
  }, [muted])

  return (
    <Popover content={
      <div style={{ width: 380, maxHeight: 400, overflow: 'auto' }}>
        <Space style={{ padding: '8px 0' }}>
          <Button size="small" icon={<SoundOutlined />} onClick={() => setMuted(!muted)} type={muted ? 'default' : 'primary'}>
            {muted ? 'Вкл звук' : 'Выкл звук'}
          </Button>
        </Space>
        {notifications.length === 0 ? <Text type="secondary">Нет уведомлений</Text> :
        <List size="small" dataSource={notifications} renderItem={(item: any) => (
          <List.Item style={{ padding: '4px 8px' }}>
            <Text style={{ fontSize: 11, color: '#888', width: 40 }}>{dayjs(item.created_at).format('HH:mm')}</Text>
            <Text style={{ flex: 1, fontSize: 12 }}>{item.message}</Text>
          </List.Item>
        )} />}
      </div>
    } trigger="click" open={open} onOpenChange={(v) => { setOpen(v); if (!v) setUnread(0) }}>
      <Badge count={unread} size="small" offset={[-2, 2]}>
        <BellOutlined style={{ cursor: 'pointer', fontSize: 18, color: '#666' }} />
      </Badge>
    </Popover>
  )
}

export default NotifyBell
