import React, { useState, useEffect } from 'react'
import {
  Table, Button, Modal, Form, Input, InputNumber, message, Space,
  Popconfirm, Select, Tag, Tabs, Drawer, Descriptions, Typography, Checkbox
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, SwapOutlined, DownloadOutlined } from '@ant-design/icons'
import { getParts, createPart, updatePart, deletePart, partMovement, exportParts, getPartsWriteOffs, getUsers } from '../api'

const { Link } = Typography

interface WriteOff {
  id: number
  part_name: string
  article: string
  quantity: number
  price: number
  total: number
  order_id: number
  master_id: number
  master_name: string
  created_at: string
}

interface User {
  id: number
  full_name: string
  username: string
  role: string
}

const PartsPage: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const [parts, setParts] = useState<any[]>([])
  const [modalOpen, setModalOpen] = useState(false)
  const [movementModalOpen, setMovementModalOpen] = useState(false)
  const [editingPart, setEditingPart] = useState<any>(null)
  const [selectedPartForMovement, setSelectedPartForMovement] = useState<any>(null)
  const [form] = Form.useForm()
  const [movementForm] = Form.useForm()
  const [searchText, setSearchText] = useState('')

  // Masters
  const [masters, setMasters] = useState<User[]>([])

  // Write-off immediately checkbox state
  const [writeOffImmediately, setWriteOffImmediately] = useState(false)

  // Movement type watch
  const [movementType, setMovementType] = useState<string>('')

  // Drawer state
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [drawerPart, setDrawerPart] = useState<any>(null)
  const [drawerWriteOffs, setDrawerWriteOffs] = useState<WriteOff[]>([])
  const [drawerLoading, setDrawerLoading] = useState(false)

  // Write-offs tab state
  const [activeTab, setActiveTab] = useState('stock')
  const [writeOffs, setWriteOffs] = useState<WriteOff[]>([])
  const [writeOffsLoading, setWriteOffsLoading] = useState(false)

  useEffect(() => {
    fetchParts()
    fetchMasters()
  }, [])

  const fetchMasters = async () => {
    try {
      const data = await getUsers()
      setMasters(Array.isArray(data) ? data : data.items || data.data?.items || [])
    } catch {
      // non-critical
    }
  }

  const fetchParts = async () => {
    setLoading(true)
    try {
      const params: any = {}
      if (searchText) params.search = searchText
      const data = await getParts(params)
      setParts(data)
    } catch {
      message.error('Ошибка загрузки запчастей')
    } finally {
      setLoading(false)
    }
  }

  const fetchWriteOffs = async () => {
    setWriteOffsLoading(true)
    try {
      const data = await getPartsWriteOffs()
      setWriteOffs(data)
    } catch {
      message.error('Ошибка загрузки списаний')
    } finally {
      setWriteOffsLoading(false)
    }
  }

  const handleTabChange = (key: string) => {
    setActiveTab(key)
    if (key === 'writeoffs' && writeOffs.length === 0) {
      fetchWriteOffs()
    }
  }

  const handleCreate = () => {
    setEditingPart(null)
    form.resetFields()
    setWriteOffImmediately(false)
    setModalOpen(true)
  }

  const handleEdit = (record: any) => {
    setEditingPart(record)
    form.setFieldsValue(record)
    setWriteOffImmediately(false)
    setModalOpen(true)
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      if (editingPart) {
        await updatePart(editingPart.id, values)
        message.success('Запчасть обновлена')
        setModalOpen(false)
        fetchParts()
      } else {
        // Create part
        const { writeoff_master_id, writeoff_order_id, writeoff_quantity, ...partData } = values
        const newPart = await createPart(partData)

        if (writeOffImmediately) {
          await partMovement(
            newPart.id,
            'write_off',
            writeoff_quantity ?? partData.quantity,
            writeoff_order_id,
            writeoff_master_id
          )
          message.success('Запчасть добавлена и списана на мастера')
        } else {
          message.success('Запчасть добавлена')
        }

        setModalOpen(false)
        fetchParts()
      }
    } catch {
      message.error('Ошибка сохранения')
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await deletePart(id)
      message.success('Запчасть удалена')
      fetchParts()
    } catch {
      message.error('Ошибка удаления')
    }
  }

  const handleMovement = (record: any, defaultType?: string) => {
    setSelectedPartForMovement(record)
    movementForm.resetFields()
    const initialType = defaultType || ''
    movementForm.setFieldsValue({ quantity: 1, ...(defaultType ? { type: defaultType } : {}) })
    setMovementType(initialType)
    setMovementModalOpen(true)
  }

  const handleMovementSubmit = async () => {
    try {
      const values = await movementForm.validateFields()
      await partMovement(
        selectedPartForMovement.id,
        values.type,
        values.quantity,
        values.order_id,
        values.master_id
      )
      message.success('Движение выполнено')
      setMovementModalOpen(false)
      fetchParts()
      // Refresh drawer history if open for same part
      if (drawerPart && drawerPart.id === selectedPartForMovement.id) {
        loadDrawerWriteOffs(selectedPartForMovement.id)
      }
    } catch {
      message.error('Ошибка выполнения движения')
    }
  }

  const loadDrawerWriteOffs = async (partId: number) => {
    setDrawerLoading(true)
    try {
      const data = await getPartsWriteOffs({ part_id: partId })
      setDrawerWriteOffs(data)
    } catch {
      message.error('Ошибка загрузки истории списаний')
    } finally {
      setDrawerLoading(false)
    }
  }

  const openDrawer = async (record: any) => {
    setDrawerPart(record)
    setDrawerOpen(true)
    setDrawerWriteOffs([])
    await loadDrawerWriteOffs(record.id)
  }

  const columns = [
    { title: 'Артикул', dataIndex: 'article', key: 'article', width: 120 },
    { title: 'Название', dataIndex: 'name', key: 'name' },
    {
      title: 'Кол-во',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 80,
      render: (val: number) => (
        <Tag color={val > 10 ? 'green' : val > 0 ? 'orange' : 'red'}>{val}</Tag>
      ),
    },
    { title: 'Закупка', dataIndex: 'cost_price', key: 'cost_price', width: 100, render: (v: number) => `${v.toFixed(2)} ₽` },
    { title: 'Продажа', dataIndex: 'sale_price', key: 'sale_price', width: 100, render: (v: number) => `${v.toFixed(2)} ₽` },
    {
      title: 'Действия',
      key: 'actions',
      width: 180,
      render: (_: any, record: any) => (
        <Space>
          <Button icon={<SwapOutlined />} onClick={(e) => { e.stopPropagation(); handleMovement(record) }} title="Движение" />
          <Button icon={<EditOutlined />} onClick={(e) => { e.stopPropagation(); handleEdit(record) }} />
          <Popconfirm title="Удалить?" onConfirm={(e) => { e?.stopPropagation(); handleDelete(record.id) }} onCancel={(e) => e?.stopPropagation()}>
            <Button icon={<DeleteOutlined />} danger onClick={(e) => e.stopPropagation()} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const writeOffColumns = [
    { title: 'Запчасть', dataIndex: 'part_name', key: 'part_name' },
    { title: 'Артикул', dataIndex: 'article', key: 'article', width: 120 },
    { title: 'Кол-во', dataIndex: 'quantity', key: 'quantity', width: 80 },
    { title: 'Цена', dataIndex: 'price', key: 'price', width: 100, render: (v: number) => `${v.toFixed(2)} ₽` },
    { title: 'Сумма', dataIndex: 'total', key: 'total', width: 110, render: (v: number) => `${v.toFixed(2)} ₽` },
    {
      title: 'Заказ',
      dataIndex: 'order_id',
      key: 'order_id',
      width: 80,
      render: (id: number) => id ? <Link href={`/orders/${id}`}>#{id}</Link> : '—',
    },
    { title: 'Мастер', dataIndex: 'master_name', key: 'master_name', width: 130 },
    {
      title: 'Дата',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (v: string) => new Date(v).toLocaleString('ru-RU'),
    },
  ]

  const drawerHistoryColumns = [
    {
      title: 'Заказ',
      dataIndex: 'order_id',
      key: 'order_id',
      width: 70,
      render: (id: number) => id ? <Link href={`/orders/${id}`}>#{id}</Link> : '—',
    },
    { title: 'Мастер', dataIndex: 'master_name', key: 'master_name' },
    { title: 'Кол-во', dataIndex: 'quantity', key: 'quantity', width: 70 },
    { title: 'Сумма', dataIndex: 'total', key: 'total', width: 100, render: (v: number) => `${v.toFixed(2)} ₽` },
    {
      title: 'Дата',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (v: string) => new Date(v).toLocaleString('ru-RU'),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Space>
          <h1 style={{ margin: 0 }}>🔧 Склад запчастей</h1>
          <Button icon={<DownloadOutlined />} onClick={async () => {
            const token = localStorage.getItem('token')
            try {
              const res = await fetch(exportParts(), { headers: { Authorization: `Bearer ${token || ''}` } })
              const blob = await res.blob()
              const url = URL.createObjectURL(blob)
              const a = document.createElement('a'); a.href = url; a.download = 'parts.xlsx'; a.click()
              URL.revokeObjectURL(url)
              message.success('Excel скачан')
            } catch { message.error('Ошибка экспорта') }
          }}>📥 Excel</Button>
          <Input.Search
            placeholder="Поиск по названию или артикулу"
            style={{ width: 300 }}
            onSearch={(val) => { setSearchText(val); setTimeout(fetchParts, 0) }}
          />
        </Space>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          Добавить запчасть
        </Button>
      </div>

      <Tabs
        activeKey={activeTab}
        onChange={handleTabChange}
        items={[
          {
            key: 'stock',
            label: 'На складе',
            children: (
              <Table
                columns={columns}
                dataSource={parts}
                loading={loading}
                rowKey="id"
                pagination={{ pageSize: 20 }}
                onRow={(record) => ({
                  onClick: () => openDrawer(record),
                  style: {
                    cursor: 'pointer',
                    background: drawerPart?.id === record.id ? '#e6f4ff' : undefined,
                  },
                })}
              />
            ),
          },
          {
            key: 'writeoffs',
            label: 'Списанные',
            children: (
              <Table
                columns={writeOffColumns}
                dataSource={writeOffs}
                loading={writeOffsLoading}
                rowKey="id"
                pagination={{ pageSize: 20 }}
              />
            ),
          },
        ]}
      />

      {/* Drawer: детали запчасти */}
      <Drawer
        title={drawerPart ? `${drawerPart.name} (${drawerPart.article})` : ''}
        open={drawerOpen}
        onClose={() => { setDrawerOpen(false); setDrawerPart(null) }}
        width={600}
      >
        {drawerPart && (
          <>
            <Descriptions column={2} bordered size="small" style={{ marginBottom: 16 }}>
              <Descriptions.Item label="Название">{drawerPart.name}</Descriptions.Item>
              <Descriptions.Item label="Артикул">{drawerPart.article}</Descriptions.Item>
              <Descriptions.Item label="Кол-во на складе">
                <Tag color={drawerPart.quantity > 10 ? 'green' : drawerPart.quantity > 0 ? 'orange' : 'red'}>
                  {drawerPart.quantity}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Цена закупки">{drawerPart.cost_price?.toFixed(2)} ₽</Descriptions.Item>
              <Descriptions.Item label="Цена продажи">{drawerPart.sale_price?.toFixed(2)} ₽</Descriptions.Item>
            </Descriptions>

            <Space style={{ marginBottom: 16 }}>
              <Button type="primary" onClick={() => handleMovement(drawerPart, 'income')}>📥 Приход</Button>
              <Button danger onClick={() => handleMovement(drawerPart, 'write_off')}>🗑 Списать</Button>
            </Space>

            <h3>История списаний</h3>
            <Table
              columns={drawerHistoryColumns}
              dataSource={drawerWriteOffs}
              loading={drawerLoading}
              rowKey="id"
              size="small"
              pagination={{ pageSize: 10 }}
            />
          </>
        )}
      </Drawer>

      {/* Модалка запчасти */}
      <Modal
        title={editingPart ? 'Редактировать запчасть' : 'Новая запчасть'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="Название" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="article" label="Артикул" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="quantity" label="Количество" rules={[{ required: true }]}>
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="cost_price" label="Цена закупки" rules={[{ required: true }]}>
            <InputNumber min={0} step={0.01} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="sale_price" label="Цена продажи" rules={[{ required: true }]}>
            <InputNumber min={0} step={0.01} style={{ width: '100%' }} />
          </Form.Item>

          {/* Only show write-off option when creating */}
          {!editingPart && (
            <>
              <Form.Item>
                <Checkbox
                  checked={writeOffImmediately}
                  onChange={(e) => setWriteOffImmediately(e.target.checked)}
                >
                  Сразу списать на мастера
                </Checkbox>
              </Form.Item>

              {writeOffImmediately && (
                <>
                  <Form.Item
                    name="writeoff_master_id"
                    label="Мастер"
                    rules={[{ required: true, message: 'Выберите мастера' }]}
                  >
                    <Select placeholder="Выберите мастера" showSearch optionFilterProp="children">
                      {masters.map((m) => (
                        <Select.Option key={m.id} value={m.id}>
                          {m.full_name || m.username}
                        </Select.Option>
                      ))}
                    </Select>
                  </Form.Item>
                  <Form.Item
                    name="writeoff_order_id"
                    label="№ заказа"
                    rules={[{ required: true, message: 'Укажите номер заказа' }]}
                  >
                    <InputNumber style={{ width: '100%' }} min={1} />
                  </Form.Item>
                  <Form.Item name="writeoff_quantity" label="Количество для списания">
                    <InputNumber min={1} style={{ width: '100%' }} placeholder="По умолчанию — всё количество" />
                  </Form.Item>
                </>
              )}
            </>
          )}
        </Form>
      </Modal>

      {/* Модалка движения */}
      <Modal
        title={`Движение: ${selectedPartForMovement?.name}`}
        open={movementModalOpen}
        onOk={handleMovementSubmit}
        onCancel={() => setMovementModalOpen(false)}
      >
        <Form
          form={movementForm}
          layout="vertical"
          onValuesChange={(changed) => {
            if ('type' in changed) setMovementType(changed.type)
          }}
        >
          <Form.Item name="type" label="Тип движения" rules={[{ required: true }]}>
            <Select>
              <Select.Option value="income">📥 Приход</Select.Option>
              <Select.Option value="expense">📤 Расход</Select.Option>
              <Select.Option value="write_off">🗑 Списание в заказ</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="quantity" label="Количество" rules={[{ required: true }]}>
            <InputNumber min={1} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            name="order_id"
            label="№ заказа"
            rules={movementType === 'write_off' ? [{ required: true, message: 'Укажите номер заказа' }] : []}
          >
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>
          {movementType === 'write_off' && (
            <Form.Item
              name="master_id"
              label="Мастер"
              rules={[{ required: true, message: 'Выберите мастера' }]}
            >
              <Select placeholder="Выберите мастера" showSearch optionFilterProp="children">
                {masters.map((m) => (
                  <Select.Option key={m.id} value={m.id}>
                    {m.full_name || m.username}
                  </Select.Option>
                ))}
              </Select>
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  )
}

export default PartsPage
