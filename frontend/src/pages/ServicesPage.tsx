import React, { useState, useEffect } from 'react'
import { 
  Table, Button, Input, message, Space, Tag, Popconfirm, Modal, Form, 
  Typography, Card, Select, Tooltip
} from 'antd'
import { 
  PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined, ToolOutlined 
} from '@ant-design/icons'
import { getServices, createService, updateService, deleteService } from '../api'

const { Text } = Typography

const ServicesPage: React.FC = () => {
  const [services, setServices] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string | undefined>()
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<any>(null)
  const [form] = Form.useForm()

  useEffect(() => { loadServices() }, [statusFilter])

  const loadServices = async () => {
    setLoading(true)
    try {
      const params: any = { status: statusFilter }
      if (search) params.search = search
      const data = await getServices(params)
      setServices(data.items || [])
      setTotal(data.total || 0)
    } catch { message.error('Ошибка загрузки') }
    setLoading(false)
  }

  const handleSave = async () => {
    const values = await form.validateFields()
    try {
      if (editing) {
        await updateService(editing.id, values)
        message.success('Услуга обновлена')
      } else {
        await createService(values)
        message.success('Услуга создана')
      }
      setModalOpen(false)
      setEditing(null)
      form.resetFields()
      loadServices()
    } catch (e: any) {
      message.error(e.response?.data?.detail || 'Ошибка')
    }
  }

  const openEdit = (svc?: any) => {
    setEditing(svc || null)
    if (svc) {
      form.setFieldsValue(svc)
    } else {
      form.resetFields()
      form.setFieldsValue({ status: 'active', price: 0 })
    }
    setModalOpen(true)
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 50 },
    { 
      title: 'Название', 
      dataIndex: 'name', 
      key: 'name',
      render: (v: string) => <Text strong style={{ fontSize: 13 }}>{v}</Text>
    },
    { 
      title: 'Описание', 
      dataIndex: 'description', 
      key: 'desc',
      render: (v: string) => <Text style={{ fontSize: 12, color: '#888' }}>{v || '—'}</Text>
    },
    { 
      title: 'Цена', 
      dataIndex: 'price', 
      key: 'price', 
      width: 120,
      render: (v: number) => <Text style={{ fontSize: 13, fontWeight: 600 }}>{v.toFixed(2)} ₽</Text>
    },
    { 
      title: 'Статус', 
      dataIndex: 'status', 
      key: 'status', 
      width: 90,
      render: (v: string) => (
        <Tag color={v === 'active' ? 'green' : 'default'}>
          {v === 'active' ? '✅ Активна' : '⏸️ Неактивна'}
        </Tag>
      )
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 100,
      render: (_: any, r: any) => (
        <Space>
          <Tooltip title="Редактировать">
            <Button size="small" icon={<EditOutlined />} onClick={() => openEdit(r)} />
          </Tooltip>
          <Popconfirm title="Удалить услугу?" onConfirm={async () => {
            try { await deleteService(r.id); message.success('Удалено'); loadServices() } catch {}
          }}>
            <Button size="small" icon={<DeleteOutlined />} danger />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Space>
          <ToolOutlined style={{ fontSize: 24 }} />
          <span style={{ fontSize: 20, fontWeight: 600 }}>Управление услугами</span>
          <Text type="secondary">Всего: {total}</Text>
        </Space>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => openEdit()}>Добавить услугу</Button>
      </div>

      <Card size="small" style={{ marginBottom: 16 }}>
        <Space>
          <Input 
            placeholder="Поиск..." 
            prefix={<SearchOutlined />} 
            value={search} 
            onChange={e => setSearch(e.target.value)} 
            onPressEnter={loadServices}
            style={{ width: 200 }}
          />
          <Select 
            placeholder="Статус" 
            allowClear 
            value={statusFilter} 
            onChange={setStatusFilter}
            style={{ width: 140 }}
            options={[
              { value: 'active', label: '✅ Активные' },
              { value: 'inactive', label: '⏸️ Неактивные' },
            ]}
          />
          <Button onClick={loadServices}>Обновить</Button>
        </Space>
      </Card>

      <Table
        dataSource={services}
        rowKey="id"
        loading={loading}
        columns={columns}
        pagination={false}
        size="small"
      />

      <Modal 
        title={editing ? 'Редактировать услугу' : 'Новая услуга'} 
        open={modalOpen} 
        onOk={handleSave} 
        onCancel={() => { setModalOpen(false); setEditing(null) }}
        width={500}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="Название" rules={[{ required: true }]}>
            <Input placeholder="Замена экрана" />
          </Form.Item>
          <Form.Item name="description" label="Описание">
            <Input.TextArea rows={2} placeholder="Замена дисплейного модуля" />
          </Form.Item>
          <Form.Item name="price" label="Цена" rules={[{ required: true }]}>
            <Input type="number" placeholder="3000" />
          </Form.Item>
          <Form.Item name="status" label="Статус">
            <Select options={[
              { label: '✅ Активна', value: 'active' },
              { label: '⏸️ Неактивна', value: 'inactive' },
            ]} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default ServicesPage
