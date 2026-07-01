import React, { useState, useEffect } from 'react'
import { Table, Input, Drawer, Descriptions, message, Tag, Spin } from 'antd'
import { EyeOutlined, SearchOutlined } from '@ant-design/icons'
import { getClients, getClient } from '../api'

const statusLabels: Record<string, string> = {
  new: 'Новый',
  diagnostics: 'Диагностика',
  agreed: 'Согласован',
  repair: 'В ремонте',
  ready: 'Готов',
  issued: 'Выдан',
  cancelled: 'Отменён',
}

const clientTypeLabels: Record<string, string> = {
  individual: 'Физ. лицо',
  company: 'Юр. лицо',
}

const ClientsPage: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const [clients, setClients] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [drawerVisible, setDrawerVisible] = useState(false)
  const [selectedClient, setSelectedClient] = useState<any>(null)
  const [drawerLoading, setDrawerLoading] = useState(false)
  const [searchText, setSearchText] = useState('')

  const pageSize = 50

  useEffect(() => {
    fetchClients()
  }, [page, searchText])

  const fetchClients = async () => {
    setLoading(true)
    try {
      const params: any = {
        skip: (page - 1) * pageSize,
        limit: pageSize,
      }
      if (searchText) params.search = searchText
      const data = await getClients(params)
      setClients(data.clients || [])
      setTotal(data.total || 0)
    } catch (error) {
      message.error('Ошибка загрузки клиентов')
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = () => {
    setPage(1)
    fetchClients()
  }

  const handleViewClient = async (record: any) => {
    setDrawerLoading(true)
    setDrawerVisible(true)
    try {
      const data = await getClient(record.phone)
      setSelectedClient(data)
    } catch (error) {
      message.error('Ошибка загрузки информации о клиенте')
    } finally {
      setDrawerLoading(false)
    }
  }

  const columns = [
    { title: 'Имя', dataIndex: 'name', key: 'name' },
    { title: 'Телефон', dataIndex: 'phone', key: 'phone' },
    { 
      title: 'Тип', 
      dataIndex: 'client_type', 
      key: 'client_type',
      render: (type: string) => clientTypeLabels[type] || type || '—',
    },
    { title: 'Заказов', dataIndex: 'total_orders', key: 'total_orders', width: 100 },
    { 
      title: 'Последний заказ', 
      dataIndex: 'last_order_date', 
      key: 'last_order_date',
      width: 150,
      render: (date: string) => date ? new Date(date).toLocaleDateString('ru-RU') : '—',
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 100,
      render: (_: any, record: any) => (
        <EyeOutlined 
          onClick={() => handleViewClient(record)} 
          style={{ cursor: 'pointer', fontSize: 18 }} 
        />
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <h1 style={{ margin: 0 }}>👥 Клиенты</h1>
        <Input 
          placeholder="Поиск по имени или телефону" 
          style={{ width: 300, marginTop: 8 }}
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          onPressEnter={handleSearch}
          suffix={<SearchOutlined style={{ cursor: 'pointer' }} onClick={handleSearch} />}
        />
      </div>

      <Table 
        columns={columns} 
        dataSource={clients} 
        loading={loading} 
        rowKey="phone" 
        pagination={{ 
          current: page,
          pageSize: pageSize,
          total: total,
          onChange: (p) => setPage(p),
        }} 
      />

      <Drawer
        title={`Клиент: ${selectedClient?.name || 'Загрузка...'}`}
        width={600}
        open={drawerVisible}
        onClose={() => setDrawerVisible(false)}
      >
        {drawerLoading ? (
          <Spin />
        ) : selectedClient && (
          <>
            <Descriptions bordered column={1}>
              <Descriptions.Item label="Имя">{selectedClient.name}</Descriptions.Item>
              <Descriptions.Item label="Телефон">{selectedClient.phone}</Descriptions.Item>
              <Descriptions.Item label="Тип">{clientTypeLabels[selectedClient.client_type] || selectedClient.client_type}</Descriptions.Item>
              <Descriptions.Item label="Всего заказов">{selectedClient.total_orders}</Descriptions.Item>
            </Descriptions>

            <h3 style={{ marginTop: 16 }}>История заказов:</h3>
            <Table
              dataSource={selectedClient.orders || []}
              rowKey="id"
              pagination={false}
              size="small"
              columns={[
                { title: '№', dataIndex: 'id', key: 'id', width: 60 },
                { title: 'Устройство', dataIndex: 'device_model', key: 'device_model' },
                { 
                  title: 'Статус', 
                  dataIndex: 'status', 
                  key: 'status',
                  render: (s: string) => <Tag>{statusLabels[s] || s}</Tag>,
                },
                { 
                  title: 'Сумма', 
                  dataIndex: 'total_cost', 
                  key: 'total_cost',
                  render: (v: number) => v ? `${v.toFixed(2)} ₽` : '—',
                },
              ]}
            />
          </>
        )}
      </Drawer>
    </div>
  )
}

export default ClientsPage