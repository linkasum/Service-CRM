import React, { useState, useEffect, useRef } from 'react'
import { Input, List, Tag, Empty, Typography, Space, Spin } from 'antd'
import { SearchOutlined, PhoneOutlined, NumberOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { globalSearch } from '../api'

const { Text } = Typography

const GlobalSearch: React.FC = () => {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [showDropdown, setShowDropdown] = useState(false)
  const inputRef = useRef<any>(null)

  useEffect(() => {
    if (!query.trim() || query.length < 2) {
      setResults(null)
      setShowDropdown(false)
      return
    }

    setLoading(true)
    const timer = setTimeout(async () => {
      try {
        const data = await globalSearch(query.trim())
        setResults(data)
        setShowDropdown(true)
      } catch {
        setResults(null)
      }
      setLoading(false)
    }, 250)

    return () => clearTimeout(timer)
  }, [query])

  const handleNavigate = (type: string, id: number) => {
    setShowDropdown(false)
    setQuery('')
    if (type === 'order') navigate(`/orders/${id}`)
    else if (type === 'client') navigate(`/clients`)
    else if (type === 'part') navigate('/parts')
    else if (type === 'service') navigate('/services')
  }

  const statusColors: Record<string, string> = {
    new: 'blue', diagnostics: 'gold', agreed: 'orange', repair: 'purple',
    ready: 'green', issued: 'default', cancelled: 'red', waiting_parts: 'cyan',
    ready_pickup: 'green',
  }

  const sectionHeader = (label: string, count: number) => (
    <div style={{ padding: '6px 16px', background: '#f5f5f5', fontSize: 11, fontWeight: 600, color: '#666', borderTop: '1px solid #eee' }}>
      {label} ({count})
    </div>
  )

  const resultTotal = results
    ? (results.orders?.length || 0) + (results.clients?.length || 0) + (results.parts?.length || 0) + (results.services?.length || 0)
    : 0

  return (
    <div style={{ position: 'relative', width: 400 }}>
      <Input
        ref={inputRef}
        prefix={<SearchOutlined style={{ color: '#aaa' }} />}
        placeholder="Поиск: #заказ, телефон, клиент..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => { if (results && resultTotal > 0) setShowDropdown(true) }}
        allowClear
        style={{ borderRadius: 6 }}
      />

      {showDropdown && (
        <>
          <div
            style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, zIndex: 999 }}
            onClick={() => setShowDropdown(false)}
          />
          <div style={{
            position: 'absolute', top: 38, left: 0, width: 500, maxHeight: 460,
            overflow: 'auto', background: '#fff', borderRadius: 8,
            boxShadow: '0 6px 20px rgba(0,0,0,0.18)', zIndex: 1000,
          }}>
            {loading ? (
              <div style={{ padding: 24, textAlign: 'center' }}><Spin /></div>
            ) : resultTotal === 0 ? (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Ничего не найдено" style={{ padding: 24 }} />
            ) : (
              <>
                {results.orders?.length > 0 && (
                  <>
                    {sectionHeader('ЗАКАЗЫ', results.orders.length)}
                    {results.orders.map((o: any, i: number) => (
                      <div
                        key={`ord-${i}`}
                        onClick={() => handleNavigate('order', o.id)}
                        style={{ cursor: 'pointer', padding: '8px 16px', borderBottom: '1px solid #f5f5f5' }}
                      >
                        <Space>
                          <Tag color={statusColors[o.status] || 'default'}>#{o.id}</Tag>
                          <Text strong>{o.client}</Text>
                          {o.phone && <Text type="secondary" style={{ fontSize: 12 }}>{o.phone}</Text>}
                        </Space>
                        <div style={{ fontSize: 12, color: '#888', marginTop: 2 }}>
                          {o.device} {o.total_cost ? `• ${o.total_cost.toFixed(0)}₽` : ''}
                        </div>
                      </div>
                    ))}
                  </>
                )}

                {results.clients?.length > 0 && (
                  <>
                    {sectionHeader('КЛИЕНТЫ', results.clients.length)}
                    {results.clients.map((c: any, i: number) => (
                      <div
                        key={`cli-${i}`}
                        onClick={() => handleNavigate('client', 0)}
                        style={{ cursor: 'pointer', padding: '8px 16px', borderBottom: '1px solid #f5f5f5' }}
                      >
                        <Space>
                          <PhoneOutlined style={{ color: '#1890ff' }} />
                          <Text strong>{c.name}</Text>
                          <Text code style={{ fontSize: 12 }}>{c.phone}</Text>
                        </Space>
                        <div style={{ fontSize: 12, color: '#888', marginTop: 2 }}>
                          Последнее: {c.last_device} (#{c.last_order_id})
                        </div>
                      </div>
                    ))}
                  </>
                )}

                {results.parts?.length > 0 && (
                  <>
                    {sectionHeader('ЗАПЧАСТИ', results.parts.length)}
                    {results.parts.map((p: any, i: number) => (
                      <div
                        key={`part-${i}`}
                        onClick={() => handleNavigate('part', p.id)}
                        style={{ cursor: 'pointer', padding: '8px 16px', borderBottom: '1px solid #f5f5f5' }}
                      >
                        <Space>
                          <Tag color="blue">📦</Tag>
                          <Text strong>{p.name}</Text>
                          <Text type="secondary" style={{ fontSize: 12 }}>{p.article}</Text>
                        </Space>
                        <div style={{ fontSize: 12, color: '#888', marginTop: 2 }}>
                          Остаток: {p.quantity} • {p.sale_price}₽
                        </div>
                      </div>
                    ))}
                  </>
                )}

                {results.services?.length > 0 && (
                  <>
                    {sectionHeader('УСЛУГИ', results.services.length)}
                    {results.services.map((s: any, i: number) => (
                      <div
                        key={`svc-${i}`}
                        onClick={() => handleNavigate('service', s.id)}
                        style={{ cursor: 'pointer', padding: '8px 16px', borderBottom: '1px solid #f5f5f5' }}
                      >
                        <Space>
                          <Tag color="purple">🔧</Tag>
                          <Text strong>{s.name}</Text>
                          <Text style={{ fontSize: 13 }}>{s.price}₽</Text>
                        </Space>
                      </div>
                    ))}
                  </>
                )}

                <div style={{ padding: '6px 16px', textAlign: 'center', background: '#fafafa', fontSize: 11, color: '#aaa' }}>
                  Найдено: {resultTotal} • ESC чтобы закрыть
                </div>
              </>
            )}
          </div>
        </>
      )}
    </div>
  )
}

export default GlobalSearch
