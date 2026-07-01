import React, { useState, useEffect } from 'react'
import {
  Card, Table, Button, Modal, Form, Input, Tag, Space, Popconfirm,
  message, Switch, Row, Col, Statistic, Select, Spin, Alert, Empty
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, SaveOutlined, LockOutlined, UnlockOutlined, KeyOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import axios from 'axios'
import CashShiftsTab from './CashShiftsTab'

const api = axios.create({ baseURL: '/api/settings' })
api.interceptors.request.use(c => {
  const t = localStorage.getItem('token')
  if (t) c.headers.Authorization = `Bearer ${t}`
  return c
})

// Response interceptor — логируем ошибки
api.interceptors.response.use(
  r => r,
  err => {
    console.error('[Settings API Error]', err.response?.status, err.response?.data || err.message)
    return Promise.reject(err)
  }
)

// === СТАТУСЫ ===

const StatusesTab: React.FC = () => {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [modal, setModal] = useState(false)
  const [edit, setEdit] = useState<any>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    let cancelled = false
    api.get<any[]>('statuses')
      .then(r => { if (!cancelled) { setData(r.data); setLoading(false) } })
      .catch(e => { if (!cancelled) { setError(e.response?.data?.detail || e.message); setLoading(false) } })
    return () => { cancelled = true }
  }, [])

  const submit = async () => {
    try {
      const v = await form.validateFields()
      if (edit) await api.patch(`statuses/${edit.id}`, v)
      else await api.post('statuses', v)
      message.success('Сохранено')
      setModal(false)
      loadData()
    } catch (e: any) {
      if (!e.errorFields) message.error(e.response?.data?.detail || 'Ошибка сохранения')
    }
  }

  const loadData = () => {
    setLoading(true)
    setError(null)
    api.get<any[]>('statuses')
      .then(r => { setData(r.data); setLoading(false) })
      .catch(e => { setError(e.response?.data?.detail || e.message); setLoading(false) })
  }

  if (loading) return <Spin tip="Загрузка..." />
  if (error) return <Alert type="error" message="Ошибка загрузки" description={error} action={<Button size="small" onClick={loadData}>Повторить</Button>} />

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h3 style={{ margin: 0 }}>Список статусов</h3>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEdit(null); form.resetFields(); setModal(true) }}>Добавить статус</Button>
      </div>
      {data.length === 0 ? <Empty description="Нет статусов" /> : (
        <Table dataSource={data} rowKey="id" pagination={false} columns={[
          { title: 'Название', dataIndex: 'name', key: 'name' },
          { title: 'Цвет', dataIndex: 'color', key: 'color', render: (c: string) => <Tag color={c}>{c}</Tag> },
          { title: 'По умолч.', dataIndex: 'is_default', key: 'is_default', render: (v: boolean) => v ? '✅' : '—' },
          { title: 'Активный', dataIndex: 'is_active', key: 'is_active', render: (v: boolean) => v ? '✅' : '❌' },
          { title: 'Действия', key: 'actions', render: (_: any, r: any) => (
            <Space>
              <Button size="small" icon={<EditOutlined />} onClick={() => { setEdit(r); form.setFieldsValue(r); setModal(true) }} />
              <Popconfirm title="Удалить?" onConfirm={async () => { try { await api.delete(`statuses/${r.id}`); message.success('Удалено'); loadData() } catch (e: any) { message.error(e.response?.data?.detail || 'Ошибка') } }}>
                <Button size="small" icon={<DeleteOutlined />} danger />
              </Popconfirm>
            </Space>
          )},
        ]} />
      )}
      <Modal title={edit ? 'Редактировать статус' : 'Добавить статус'} open={modal} onOk={submit} onCancel={() => setModal(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="Название" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="color" label="Цвет">
            <Input type="color" />
          </Form.Item>
          <Form.Item name="is_default" label="По умолчанию" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="is_active" label="Активный" valuePropName="checked">
            <Switch defaultChecked />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

// === БРЕНДЫ ===

const BrandsTab: React.FC = () => {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [modal, setModal] = useState(false)
  const [edit, setEdit] = useState<any>(null)
  const [form] = Form.useForm()
  const [searchText, setSearchText] = useState<string>('')

  useEffect(() => {
    loadData()
  }, [])

  const loadData = () => {
    setLoading(true)
    setError(null)
    api.get<any[]>('brands')
      .then(r => { setData(r.data); setLoading(false) })
      .catch(e => { setError(e.response?.data?.detail || e.message); setLoading(false) })
  }

  const submit = async () => {
    try {
      const v = await form.validateFields()
      if (edit) await api.patch(`brands/${edit.id}`, v)
      else await api.post('brands', v)
      message.success('Сохранено')
      setModal(false)
      loadData()
    } catch (e: any) {
      if (!e.errorFields) message.error(e.response?.data?.detail || 'Ошибка сохранения')
    }
  }

  // Фильтрация брендов по поиску
  const filteredData = searchText
    ? data.filter(item => item.name.toLowerCase().includes(searchText.toLowerCase()))
    : data

  if (loading) return <Spin tip="Загрузка..." />
  if (error) return <Alert type="error" message="Ошибка загрузки" description={error} action={<Button size="small" onClick={loadData}>Повторить</Button>} />

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ margin: 0 }}>Список брендов ({filteredData.length})</h3>
        <Space>
          <Input.Search
            placeholder="Поиск бренда"
            allowClear
            onSearch={setSearchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 250 }}
          />
          <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEdit(null); form.resetFields(); setModal(true) }}>Добавить бренд</Button>
        </Space>
      </div>
      {filteredData.length === 0 ? <Empty description={searchText ? "Бренды не найдены" : "Нет брендов"} /> : (
        <Table 
          dataSource={filteredData} 
          rowKey="id" 
          pagination={{ pageSize: 50, showSizeChanger: true, showTotal: (total) => `Всего ${total} брендов` }} 
          scroll={{ y: 600 }}
          columns={[
          { title: 'Название', dataIndex: 'name', key: 'name' },
          { title: 'Статус', dataIndex: 'is_active', key: 'is_active', render: (v: boolean) => <Tag color={v ? 'green' : 'red'}>{v ? 'Активен' : 'Неактивен'}</Tag> },
          { title: 'Действия', key: 'actions', render: (_: any, r: any) => (
            <Space>
              <Button size="small" icon={<EditOutlined />} onClick={() => { setEdit(r); form.setFieldsValue(r); setModal(true) }} />
              <Popconfirm title="Удалить?" onConfirm={async () => { try { await api.delete(`brands/${r.id}`); message.success('Удалено'); loadData() } catch (e: any) { message.error(e.response?.data?.detail || 'Ошибка') } }}>
                <Button size="small" icon={<DeleteOutlined />} danger />
              </Popconfirm>
            </Space>
          )},
        ]} />
      )}
      <Modal title={edit ? 'Редактировать бренд' : 'Добавить бренд'} open={modal} onOk={submit} onCancel={() => setModal(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="Название" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="is_active" label="Активный" valuePropName="checked">
            <Switch defaultChecked />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

// === КАТЕГОРИИ ===

const CategoriesTab: React.FC = () => {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [modal, setModal] = useState(false)
  const [edit, setEdit] = useState<any>(null)
  const [form] = Form.useForm()
  const [searchText, setSearchText] = useState<string>('')

  useEffect(() => {
    loadData()
  }, [])

  const loadData = () => {
    setLoading(true)
    setError(null)
    api.get<any[]>('categories')
      .then(r => { setData(r.data); setLoading(false) })
      .catch(e => { setError(e.response?.data?.detail || e.message); setLoading(false) })
  }

  const submit = async () => {
    try {
      const v = await form.validateFields()
      if (edit) await api.patch(`categories/${edit.id}`, v)
      else await api.post('categories', v)
      message.success('Сохранено')
      setModal(false)
      loadData()
    } catch (e: any) {
      if (!e.errorFields) message.error(e.response?.data?.detail || 'Ошибка сохранения')
    }
  }

  // Фильтрация категорий по поиску
  const filteredData = searchText
    ? data.filter(item => item.name.toLowerCase().includes(searchText.toLowerCase()))
    : data

  if (loading) return <Spin tip="Загрузка..." />
  if (error) return <Alert type="error" message="Ошибка загрузки" description={error} action={<Button size="small" onClick={loadData}>Повторить</Button>} />

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ margin: 0 }}>Список категорий ({filteredData.length})</h3>
        <Space>
          <Input.Search
            placeholder="Поиск категории"
            allowClear
            onSearch={setSearchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 250 }}
          />
          <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEdit(null); form.resetFields(); setModal(true) }}>Добавить категорию</Button>
        </Space>
      </div>
      {filteredData.length === 0 ? <Empty description={searchText ? "Категории не найдены" : "Нет категорий"} /> : (
        <Table 
          dataSource={filteredData} 
          rowKey="id" 
          pagination={{ pageSize: 50, showSizeChanger: true, showTotal: (total) => `Всего ${total} категорий` }} 
          scroll={{ y: 600 }}
          columns={[
          { title: 'Название', dataIndex: 'name', key: 'name' },
          { title: 'Статус', dataIndex: 'is_active', key: 'is_active', render: (v: boolean) => <Tag color={v ? 'green' : 'red'}>{v ? 'Активен' : 'Неактивен'}</Tag> },
          { title: 'Действия', key: 'actions', render: (_: any, r: any) => (
            <Space>
              <Button size="small" icon={<EditOutlined />} onClick={() => { setEdit(r); form.setFieldsValue(r); setModal(true) }} />
              <Popconfirm title="Удалить?" onConfirm={async () => { try { await api.delete(`categories/${r.id}`); message.success('Удалено'); loadData() } catch (e: any) { message.error(e.response?.data?.detail || 'Ошибка') } }}>
                <Button size="small" icon={<DeleteOutlined />} danger />
              </Popconfirm>
            </Space>
          )},
        ]} />
      )}
      <Modal title={edit ? 'Редактировать категорию' : 'Добавить категорию'} open={modal} onOk={submit} onCancel={() => setModal(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="Название" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="is_active" label="Активная" valuePropName="checked">
            <Switch defaultChecked />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

// === ИСТОЧНИКИ КЛИЕНТОВ ===

const ClientSourcesTab: React.FC = () => {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [modal, setModal] = useState(false)
  const [edit, setEdit] = useState<any>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    let cancelled = false
    api.get<any[]>('client-sources')
      .then(r => { if (!cancelled) { setData(r.data); setLoading(false) } })
      .catch(e => { if (!cancelled) { setError(e.response?.data?.detail || e.message); setLoading(false) } })
    return () => { cancelled = true }
  }, [])

  const submit = async () => {
    try {
      const v = await form.validateFields()
      if (edit) await api.patch(`client-sources/${edit.id}`, v)
      else await api.post('client-sources', v)
      message.success('Сохранено')
      setModal(false)
      loadData()
    } catch (e: any) {
      if (!e.errorFields) message.error(e.response?.data?.detail || 'Ошибка сохранения')
    }
  }

  const loadData = () => {
    setLoading(true)
    setError(null)
    api.get<any[]>('client-sources')
      .then(r => { setData(r.data); setLoading(false) })
      .catch(e => { setError(e.response?.data?.detail || e.message); setLoading(false) })
  }

  if (loading) return <Spin tip="Загрузка..." />
  if (error) return <Alert type="error" message="Ошибка загрузки" description={error} action={<Button size="small" onClick={loadData}>Повторить</Button>} />

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h3 style={{ margin: 0 }}>Список источников</h3>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEdit(null); form.resetFields(); setModal(true) }}>Добавить источник</Button>
      </div>
      {data.length === 0 ? <Empty description="Нет источников" /> : (
        <Table dataSource={data} rowKey="id" pagination={false} columns={[
          { title: 'Название', dataIndex: 'name', key: 'name' },
          { title: 'Статус', dataIndex: 'is_active', key: 'is_active', render: (v: boolean) => <Tag color={v ? 'green' : 'red'}>{v ? 'Активен' : 'Неактивен'}</Tag> },
          { title: 'Действия', key: 'actions', render: (_: any, r: any) => (
            <Space>
              <Button size="small" icon={<EditOutlined />} onClick={() => { setEdit(r); form.setFieldsValue(r); setModal(true) }} />
              <Popconfirm title="Удалить?" onConfirm={async () => { try { await api.delete(`client-sources/${r.id}`); message.success('Удалено'); loadData() } catch (e: any) { message.error(e.response?.data?.detail || 'Ошибка') } }}>
                <Button size="small" icon={<DeleteOutlined />} danger />
              </Popconfirm>
            </Space>
          )},
        ]} />
      )}
      <Modal title={edit ? 'Редактировать источник' : 'Добавить источник'} open={modal} onOk={submit} onCancel={() => setModal(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="Название" rules={[{ required: true }]}>
            <Input placeholder="Google, Рекомендация, Прямой визит..." />
          </Form.Item>
          <Form.Item name="is_active" label="Активный" valuePropName="checked">
            <Switch defaultChecked />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

// === ВОЗРАСТНЫЕ ГРУППЫ ===

const AgeGroupsTab: React.FC = () => {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [modal, setModal] = useState(false)
  const [edit, setEdit] = useState<any>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    let cancelled = false
    api.get<any[]>('age-groups')
      .then(r => { if (!cancelled) { setData(r.data); setLoading(false) } })
      .catch(e => { if (!cancelled) { setError(e.response?.data?.detail || e.message); setLoading(false) } })
    return () => { cancelled = true }
  }, [])

  const submit = async () => {
    try {
      const v = await form.validateFields()
      if (edit) await api.patch(`age-groups/${edit.id}`, v)
      else await api.post('age-groups', v)
      message.success('Сохранено')
      setModal(false)
      loadData()
    } catch (e: any) {
      if (!e.errorFields) message.error(e.response?.data?.detail || 'Ошибка сохранения')
    }
  }

  const loadData = () => {
    setLoading(true)
    setError(null)
    api.get<any[]>('age-groups')
      .then(r => { setData(r.data); setLoading(false) })
      .catch(e => { setError(e.response?.data?.detail || e.message); setLoading(false) })
  }

  if (loading) return <Spin tip="Загрузка..." />
  if (error) return <Alert type="error" message="Ошибка загрузки" description={error} action={<Button size="small" onClick={loadData}>Повторить</Button>} />

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h3 style={{ margin: 0 }}>Список возрастных групп</h3>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEdit(null); form.resetFields(); setModal(true) }}>Добавить возрастную группу</Button>
      </div>
      {data.length === 0 ? <Empty description="Нет возрастных групп" /> : (
        <Table dataSource={data} rowKey="id" pagination={false} columns={[
          { title: 'Название', dataIndex: 'name', key: 'name' },
          { title: 'Статус', dataIndex: 'is_active', key: 'is_active', render: (v: boolean) => <Tag color={v ? 'green' : 'red'}>{v ? 'Активна' : 'Неактивна'}</Tag> },
          { title: 'Действия', key: 'actions', render: (_: any, r: any) => (
            <Space>
              <Button size="small" icon={<EditOutlined />} onClick={() => { setEdit(r); form.setFieldsValue(r); setModal(true) }} />
              <Popconfirm title="Удалить?" onConfirm={async () => { try { await api.delete(`age-groups/${r.id}`); message.success('Удалено'); loadData() } catch (e: any) { message.error(e.response?.data?.detail || 'Ошибка') } }}>
                <Button size="small" icon={<DeleteOutlined />} danger />
              </Popconfirm>
            </Space>
          )},
        ]} />
      )}
      <Modal title={edit ? 'Редактировать группу' : 'Добавить возрастную группу'} open={modal} onOk={submit} onCancel={() => setModal(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="Название" rules={[{ required: true }]}>
            <Input placeholder="0-20, Студент, Взрослый, Пенсионер..." />
          </Form.Item>
          <Form.Item name="is_active" label="Активная" valuePropName="checked">
            <Switch defaultChecked />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

// === МОДЕЛИ УСТРОЙСТВ ===

const DeviceModelsTab: React.FC = () => {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [brands, setBrands] = useState<any[]>([])
  const [brandsLoading, setBrandsLoading] = useState(false)
  const [modal, setModal] = useState(false)
  const [edit, setEdit] = useState<any>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    let cancelled = false
    api.get<any[]>('device-models')
      .then(r => { if (!cancelled) { setData(r.data); setLoading(false) } })
      .catch(e => { if (!cancelled) { setError(e.response?.data?.detail || e.message); setLoading(false) } })
    return () => { cancelled = true }
  }, [])

  useEffect(() => {
    setBrandsLoading(true)
    api.get<any[]>('brands')
      .then(r => { setBrands(r.data); setBrandsLoading(false) })
      .catch(() => setBrandsLoading(false))
  }, [])

  const submit = async () => {
    try {
      const v = await form.validateFields()
      if (edit) await api.patch(`device-models/${edit.id}`, v)
      else await api.post('device-models', v)
      message.success('Сохранено')
      setModal(false)
      loadData()
    } catch (e: any) {
      if (!e.errorFields) message.error(e.response?.data?.detail || 'Ошибка сохранения')
    }
  }

  const loadData = () => {
    setLoading(true)
    setError(null)
    api.get<any[]>('device-models')
      .then(r => { setData(r.data); setLoading(false) })
      .catch(e => { setError(e.response?.data?.detail || e.message); setLoading(false) })
  }

  const getBrandName = (id: number) => brands.find(b => b.id === id)?.name || `#${id}`

  if (loading) return <Spin tip="Загрузка..." />
  if (error) return <Alert type="error" message="Ошибка загрузки" description={error} action={<Button size="small" onClick={loadData}>Повторить</Button>} />

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h3 style={{ margin: 0 }}>Список моделей</h3>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEdit(null); form.resetFields(); setModal(true) }}>Добавить модель</Button>
      </div>
      {data.length === 0 ? <Empty description="Нет моделей" /> : (
        <Table dataSource={data} rowKey="id" pagination={{ pageSize: 20 }} columns={[
          { title: 'Бренд', dataIndex: 'brand_id', key: 'brand_id', render: (id: number) => getBrandName(id) },
          { title: 'Модель', dataIndex: 'name', key: 'name' },
          { title: 'Статус', dataIndex: 'is_active', key: 'is_active', render: (v: boolean) => <Tag color={v ? 'green' : 'red'}>{v ? 'Активна' : 'Неактивна'}</Tag> },
          { title: 'Действия', key: 'actions', render: (_: any, r: any) => (
            <Space>
              <Button size="small" icon={<EditOutlined />} onClick={() => { setEdit(r); form.setFieldsValue(r); setModal(true) }} />
              <Popconfirm title="Удалить?" onConfirm={async () => { try { await api.delete(`device-models/${r.id}`); message.success('Удалено'); loadData() } catch (e: any) { message.error(e.response?.data?.detail || 'Ошибка') } }}>
                <Button size="small" icon={<DeleteOutlined />} danger />
              </Popconfirm>
            </Space>
          )},
        ]} />
      )}
      <Modal title={edit ? 'Редактировать модель' : 'Добавить модель'} open={modal} onOk={submit} onCancel={() => setModal(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="brand_id" label="Бренд" rules={[{ required: true }]}>
            <Select loading={brandsLoading}>
              {brands.map(b => <Select.Option key={b.id} value={b.id}>{b.name}</Select.Option>)}
            </Select>
          </Form.Item>
          <Form.Item name="name" label="Название модели" rules={[{ required: true }]}>
            <Input placeholder="iPhone 14 Pro, Galaxy S23..." />
          </Form.Item>
          <Form.Item name="is_active" label="Активная" valuePropName="checked">
            <Switch defaultChecked />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

// === РЕКВИЗИТЫ ===

const CompanyExtendedTab: React.FC = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [fetching, setFetching] = useState(true)

  useEffect(() => {
    let cancelled = false
    api.get('company-extended')
      .then(r => { if (!cancelled) { form.setFieldsValue(r.data); setFetching(false) } })
      .catch(() => { if (!cancelled) setFetching(false) })
    return () => { cancelled = true }
  }, [])

  const submit = async () => {
    setLoading(true)
    try {
      await api.patch('company-extended', await form.validateFields())
      message.success('Реквизиты сохранены')
    } catch (e: any) {
      if (!e.errorFields) message.error(e.response?.data?.detail || 'Ошибка')
    }
    setLoading(false)
  }

  if (fetching) return <Spin tip="Загрузка..." />

  return (
    <Form form={form} layout="vertical" onFinish={submit} style={{ maxWidth: 600 }}>
      <Card title="Реквизиты компании" size="small">
        <Form.Item name="company_name" label="Наименование" rules={[{ required: true }]}><Input /></Form.Item>
        <Form.Item name="address" label="Адрес"><Input /></Form.Item>
        <Row gutter={16}>
          <Col span={12}><Form.Item name="inn" label="ИНН"><Input /></Form.Item></Col>
          <Col span={12}><Form.Item name="kpp" label="КПП"><Input /></Form.Item></Col>
        </Row>
        <Form.Item name="director" label="Директор"><Input /></Form.Item>
        <Form.Item name="bank" label="Банк"><Input /></Form.Item>
        <Row gutter={16}>
          <Col span={12}><Form.Item name="account" label="Расчетный счет"><Input /></Form.Item></Col>
          <Col span={12}><Form.Item name="bik" label="БИК"><Input /></Form.Item></Col>
        </Row>
        <Row gutter={16}>
          <Col span={12}><Form.Item name="phone" label="Телефон"><Input /></Form.Item></Col>
          <Col span={12}><Form.Item name="email" label="Email"><Input /></Form.Item></Col>
        </Row>
        <Form.Item><Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={loading}>Сохранить</Button></Form.Item>
      </Card>
    </Form>
  )
}

// === СОТРУДНИКИ ===

const EmployeesTab: React.FC = () => {
  const [data, setData] = useState<any[]>([])
  const [roles, setRoles] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [modal, setModal] = useState(false)
  const [edit, setEdit] = useState<any>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    loadData()
    loadRoles()
  }, [])

  const loadData = () => {
    setLoading(true)
    setError(null)
    api.get<any[]>('users/')
      .then(r => { setData(r.data.items || []); setLoading(false) })
      .catch(e => { setError(e.response?.data?.detail || e.message); setLoading(false) })
  }

  const loadRoles = () => {
    api.get<any[]>('settings/roles/')
      .then(r => { setRoles(r.data.items || r.data || []); })
      .catch(() => {})
  }

  const submit = async () => {
    try {
      const v = await form.validateFields()
      if (edit) await api.patch(`users/${edit.id}`, v)
      else await api.post('users/', v)
      message.success('Сохранено')
      setModal(false)
      loadData()
    } catch (e: any) {
      if (!e.errorFields) message.error(e.response?.data?.detail || 'Ошибка сохранения')
    }
  }

  const handleDelete = async (id: number, username: string) => {
    try {
      await api.delete(`users/${id}/hard`)
      message.success(`Сотрудник "${username}" удалён навсегда`)
      loadData()
    } catch (e: any) {
      message.error(e.response?.data?.detail || 'Ошибка удаления')
    }
  }

  const handleDeactivate = async (id: number, username: string, is_active: boolean) => {
    try {
      await api.patch(`users/${id}`, { is_active: !is_active })
      message.success(`Сотрудник "${username}" ${is_active ? 'деактивирован' : 'активирован'}`)
      loadData()
    } catch (e: any) {
      message.error(e.response?.data?.detail || 'Ошибка')
    }
  }

  const handleResetPassword = async (id: number, username: string) => {
    try {
      await api.post(`users/${id}/reset-password`)
      message.success(`Пароль сотрудника "${username}" сброшен на "12345"`)
    } catch (e: any) {
      message.error(e.response?.data?.detail || 'Ошибка сброса пароля')
    }
  }

  if (loading) return <Spin tip="Загрузка..." />
  if (error) return <Alert type="error" message="Ошибка загрузки" description={error} action={<Button size="small" onClick={loadData}>Повторить</Button>} />

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h3 style={{ margin: 0 }}>Сотрудники ({data.length})</h3>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEdit(null); form.resetFields(); setModal(true) }}>Добавить сотрудника</Button>
      </div>
      <Table
        dataSource={data}
        rowKey="id"
        pagination={{ pageSize: 50, showSizeChanger: true }}
        scroll={{ y: 600 }}
        columns={[
          {
            title: 'Пользователь',
            dataIndex: 'username',
            key: 'username',
            width: '15%',
            render: (username: string, r: any) => (
              <div>
                <div style={{ fontWeight: 600 }}>{username}</div>
                {r.full_name && <div style={{ fontSize: 12, opacity: 0.7 }}>{r.full_name}</div>}
              </div>
            )
          },
          {
            title: 'Роль',
            dataIndex: 'role_name',
            key: 'role_name',
            width: '12%',
            render: (roleName: string) => {
              const colors: Record<string, string> = { admin: 'red', manager: 'blue', master: 'green', acceptor: 'orange' }
              return <Tag color={colors[roleName?.toLowerCase()] || 'default'}>{roleName || '—'}</Tag>
            }
          },
          {
            title: 'Telegram',
            dataIndex: 'telegram_chat_id',
            key: 'telegram_chat_id',
            width: '12%',
            render: (id: number | null) => id ? <a href={`https://t.me/${id}`} target="_blank" rel="noreferrer">@{id}</a> : '—'
          },
          {
            title: 'Email',
            dataIndex: 'email',
            key: 'email',
            width: '15%',
            ellipsis: true
          },
          {
            title: 'Телефон',
            dataIndex: 'phone',
            key: 'phone',
            width: '12%'
          },
          {
            title: 'Зарплата',
            dataIndex: 'salary_config_name',
            key: 'salary_config_name',
            width: '12%',
            render: (name: string, r: any) => name || r.salary_formula || '—'
          },
          {
            title: 'Статус',
            dataIndex: 'is_active',
            key: 'is_active',
            width: '8%',
            render: (v: boolean) => v ? <Tag color="green">✅ Активен</Tag> : <Tag color="red">❌ Не активен</Tag>
          },
          {
            title: 'Действия',
            key: 'actions',
            width: '18%',
            fixed: 'right' as const,
            render: (_: any, r: any) => (
              <Space direction="vertical" size="small">
                <Space>
                  <Button
                    size="small"
                    icon={<EditOutlined />}
                    onClick={() => { setEdit(r); form.setFieldsValue(r); setModal(true) }}
                  >
                    Редактировать
                  </Button>
                  <Button
                    size="small"
                    icon={<KeyOutlined />}
                    onClick={() => handleResetPassword(r.id, r.username)}
                  >
                    Сброс пароля
                  </Button>
                </Space>
                <Space>
                  <Button
                    size="small"
                    icon={r.is_active ? <LockOutlined /> : <UnlockOutlined />}
                    onClick={() => handleDeactivate(r.id, r.username, r.is_active)}
                  >
                    {r.is_active ? 'Деактивировать' : 'Активировать'}
                  </Button>
                  <Popconfirm
                    title={`Удалить "${r.username}" НАВСЕГДА?`}
                    description="Это действие нельзя отменить!"
                    onConfirm={() => handleDelete(r.id, r.username)}
                    okText="Удалить"
                    cancelText="Отмена"
                  >
                    <Button size="small" icon={<DeleteOutlined />} danger>
                      Удалить
                    </Button>
                  </Popconfirm>
                </Space>
              </Space>
            )
          },
        ]}
      />
      <Modal
        title={edit ? 'Редактировать сотрудника' : 'Добавить сотрудника'}
        open={modal}
        onOk={submit}
        onCancel={() => setModal(false)}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="username" label="Имя пользователя *" rules={[{ required: true }]}>
                <Input placeholder="login" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="full_name" label="Полное имя">
                <Input placeholder="Иванов Иван" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="role_id" label="Роль *" rules={[{ required: true }]}>
                <Select placeholder="Выберите роль">
                  {roles.map(role => (
                    <Select.Option key={role.id} value={role.id}>{role.name}</Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="telegram_chat_id" label="Telegram Chat ID">
                <Input type="number" placeholder="123456789" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="email" label="Email">
                <Input type="email" placeholder="email@example.com" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="phone" label="Телефон">
                <Input placeholder="+7 (999) 123-45-67" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="salary_config_id" label="Формула зарплаты">
                <Select placeholder="Выберите формулу" allowClear>
                  <Select.Option value={30}>30% от работ</Select.Option>
                  <Select.Option value={31}>Фиксированная</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="is_active" label="Статус" valuePropName="checked" initialValue={true}>
                <Switch checkedChildren="✅ Активен" unCheckedChildren="❌ Не активен" />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>
    </div>
  )
}

// === КАССА ===

const CashTab: React.FC = () => {
  return <CashShiftsTab />
}

// === КОМПЛЕКТАЦИИ ===

const AccessoryTemplatesTab: React.FC = () => {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [modal, setModal] = useState(false)
  const [edit, setEdit] = useState<any>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    loadTemplates()
  }, [])

  const loadTemplates = () => {
    setLoading(true)
    setError(null)
    api.get<any[]>('accessory-templates')
      .then(r => { setData(r.data); setLoading(false) })
      .catch(e => { setError(e.response?.data?.detail || e.message); setLoading(false) })
  }

  const submit = async () => {
    try {
      const v = await form.validateFields()
      if (edit) await api.patch(`accessory-templates/${edit.id}`, v)
      else await api.post('accessory-templates', v)
      message.success('Сохранено')
      setModal(false)
      loadTemplates()
    } catch (e: any) {
      if (!e.errorFields) message.error(e.response?.data?.detail || 'Ошибка сохранения')
    }
  }

  if (loading) return <Spin tip="Загрузка..." />
  if (error) return <Alert type="error" message="Ошибка загрузки" description={error} action={<Button size="small" onClick={loadTemplates}>Повторить</Button>} />

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h3 style={{ margin: 0 }}>Справочник комплектаций ({data.length})</h3>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEdit(null); form.resetFields(); setModal(true) }}>Добавить комплектацию</Button>
      </div>
      {data.length === 0 ? <Empty description="Нет комплектаций" /> : (
        <Table 
          dataSource={data} 
          rowKey="id" 
          pagination={{ pageSize: 50, showSizeChanger: true }} 
          scroll={{ y: 600 }}
          columns={[
            { 
              title: 'Название', 
              dataIndex: 'name', 
              key: 'name',
              width: '60%',
              sorter: (a, b) => a.name.localeCompare(b.name),
            },
            { 
              title: 'Активна', 
              dataIndex: 'is_active', 
              key: 'is_active',
              width: '10%',
              render: (v: boolean) => v ? <Tag color="green">✅</Tag> : <Tag color="red">❌</Tag>
            },
            { 
              title: 'Действия', 
              key: 'actions', 
              width: '30%',
              render: (_: any, r: any) => (
                <Space>
                  <Button 
                    size="small" 
                    icon={<EditOutlined />} 
                    onClick={() => { setEdit(r); form.setFieldsValue(r); setModal(true) }} 
                  />
                  <Popconfirm 
                    title="Удалить комплектацию?" 
                    onConfirm={async () => {
                      try {
                        await api.delete(`accessory-templates/${r.id}`)
                        message.success('Удалено')
                        loadTemplates()
                      } catch (e: any) {
                        message.error(e.response?.data?.detail || 'Ошибка удаления')
                      }
                    }}
                  >
                    <Button size="small" icon={<DeleteOutlined />} danger />
                  </Popconfirm>
                </Space>
              )
            },
          ]} 
        />
      )}
      <Modal 
        title={edit ? 'Редактировать комплектацию' : 'Добавить комплектацию'} 
        open={modal} 
        onOk={submit} 
        onCancel={() => setModal(false)}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="Название комплектации" rules={[{ required: true }]}>
            <Input placeholder="Например: Зарядное устройство, Кабель, Чехол" />
          </Form.Item>
          <Form.Item name="is_active" label="Активна" valuePropName="checked" initialValue={true}>
            <Switch checkedChildren="✅" unCheckedChildren="❌" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export { StatusesTab, BrandsTab, CategoriesTab, ClientSourcesTab, AgeGroupsTab, DeviceModelsTab, CompanyExtendedTab, CashTab, AccessoryTemplatesTab, EmployeesTab }
