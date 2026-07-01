import React, { useState, useEffect, useContext } from 'react'
import {
  Form, Input, Button, Table, Modal, Space, Popconfirm, message,
  Card, Tag, Checkbox, Row, Col, Select, Alert, Divider, Radio, InputNumber, Menu, Typography
} from 'antd'
import {
  PlusOutlined, EditOutlined, DeleteOutlined, SaveOutlined,
  ToolOutlined, TeamOutlined, EyeOutlined, CodeOutlined,
  CheckCircleOutlined, CalculatorOutlined, ThunderboltOutlined,
  SettingOutlined, UserOutlined, LockOutlined, BankOutlined,
  ShopOutlined, TagsOutlined, ClusterOutlined, GlobalOutlined,
  IdcardOutlined, MobileOutlined, DollarOutlined, FileTextOutlined,
  EyeOutlined as EyeIcon,
  CloseOutlined,
  UploadOutlined, DownloadOutlined,
  DatabaseOutlined,
  ClockCircleOutlined,
  BellOutlined,
  AppstoreOutlined,
  ImportOutlined,
} from '@ant-design/icons'
import {
  getRoles, createRole, updateRole, deleteRole,
  getCompanySettings, updateCompanySettings,
  getTemplates, updateTemplate,
  getOrderNumbering, updateOrderNumbering,
} from '../api'
import api from '../api'
import PermissionsTab from './PermissionsTab'
import NotificationsTab from './NotificationsTab'
import BotSettingsPage from './BotSettingsPage'
import TemplateEditor from '../components/TemplateEditor'
import EmployeesTab from './EmployeesTab'
import SalaryConfigTab from './SalaryConfigTab'
import { StatusesTab, BrandsTab, CategoriesTab, ClientSourcesTab, AgeGroupsTab, DeviceModelsTab, CompanyExtendedTab, CashTab, AccessoryTemplatesTab } from './SettingsExtraTab'
import WorkingHoursTab from './WorkingHoursTab'
import dayjs from 'dayjs'
import HugerteEditor from '../components/HugerteEditor'
import AuthContext from '../contexts/AuthContext'
import ImportPage from './ImportPage'

const { TextArea } = Input
const { Title, Text } = Typography

// Доступные права для чекбоксов
const ALL_PERMISSIONS = [
  { key: 'order.create', label: 'Создание заказов' },
  { key: 'order.view', label: 'Просмотр заказов' },
  { key: 'order.edit', label: 'Редактирование заказов' },
  { key: 'order.delete', label: 'Удаление заказов' },
  { key: 'client.view', label: 'Просмотр клиентов' },
  { key: 'client.edit', label: 'Редактирование клиентов' },
  { key: 'part.create', label: 'Добавление запчастей' },
  { key: 'part.view', label: 'Просмотр склада' },
  { key: 'part.edit', label: 'Редактирование склада' },
  { key: 'part.delete', label: 'Удаление запчастей' },
  { key: 'salary.view', label: 'Просмотр зарплат' },
  { key: 'salary.edit', label: 'Управление зарплатами' },
  { key: 'salary.manage', label: 'Ведомости' },
  { key: 'report.view', label: 'Отчёты' },
  { key: 'role.manage', label: 'Управление ролями' },
  { key: 'user.manage', label: 'Управление пользователями' },
  { key: 'settings.manage', label: 'Настройки компании' },
]


const SettingsPage: React.FC = () => {
  const [activeKey, setActiveKey] = useState('employees')
  
  const menuItems = [
    { key: 'employees', icon: <TeamOutlined />, label: 'Сотрудники' },
    { key: 'working-hours', icon: <ClockCircleOutlined />, label: 'Рабочее время' },
    { key: 'statuses', icon: <TagsOutlined />, label: 'Статусы' },
    { key: 'brands', icon: <MobileOutlined />, label: 'Бренды' },
    { key: 'categories', icon: <ClusterOutlined />, label: 'Категории' },
    { key: 'accessories', icon: <AppstoreOutlined />, label: 'Комплектации' },
    { key: 'sources', icon: <GlobalOutlined />, label: 'Источники' },
    { key: 'age-groups', icon: <IdcardOutlined />, label: 'Возрасты' },
    { key: 'models', icon: <MobileOutlined />, label: 'Модели' },
    { key: 'cash', icon: <DollarOutlined />, label: 'Касса' },
    { key: 'order-numbering', icon: <SettingOutlined />, label: 'Нумерация заказов' },
    { key: 'company-ext', icon: <BankOutlined />, label: 'Реквизиты' },
    { key: 'roles', icon: <LockOutlined />, label: 'Роли' },
    { key: 'permissions', icon: <EyeOutlined />, label: 'Разрешения' },
    { key: 'bot', icon: <ToolOutlined />, label: 'Бот' },
    { key: 'notifications', icon: <BellOutlined />, label: 'Уведомления' },
    { key: 'salary', icon: <CalculatorOutlined />, label: 'Зарплаты' },
    { key: 'templates', icon: <FileTextOutlined />, label: 'Шаблоны' },
    { key: 'company', icon: <ShopOutlined />, label: 'Компания' },
    { key: 'database', icon: <DatabaseOutlined />, label: 'База данных' },
    { key: 'import', icon: <ImportOutlined />, label: 'Импорт' },
  ]

  const tabContent: Record<string, React.ReactNode> = {
    'employees': <EmployeesTab />,
    'working-hours': <WorkingHoursTab />,
    'statuses': <StatusesTab />,
    'brands': <BrandsTab />,
    'categories': <CategoriesTab />,
    'accessories': <AccessoryTemplatesTab />,
    'sources': <ClientSourcesTab />,
    'age-groups': <AgeGroupsTab />,
    'models': <DeviceModelsTab />,
    'cash': <CashTab />,
    'order-numbering': <OrderNumberingTab />,
    'company-ext': <CompanyExtendedTab />,
    'roles': <RolesTab />,
    'permissions': <PermissionsTab />,
    'bot': <BotSettingsPage />,
    'notifications': <NotificationsTab />,
    'salary': <SalaryConfigTab />,
    'templates': <TemplatesTab />,
    'company': <CompanyTab />,
    'database': <DatabaseTab />,
    'import': <ImportPage />,
  }

  return (
    <div style={{ width: '100%' }}>
      <Title level={3} style={{ marginBottom: 16 }}>⚙️ Настройки</Title>
      <Row gutter={[16, 16]} style={{ width: '100%', margin: 0 }}>
        <Col xs={24} xl={6} xxl={5}>
          <Card size="small" style={{ position: 'sticky', top: 16 }}>
            <Menu
              mode="inline"
              selectedKeys={[activeKey]}
              onClick={({ key }) => setActiveKey(key)}
              items={menuItems}
            />
          </Card>
        </Col>
        <Col xs={24} xl={18} xxl={19}>
          <Card size="small" style={{ width: '100%' }}>
            {tabContent[activeKey] || <Text>Раздел не найден</Text>}
          </Card>
        </Col>
      </Row>
    </div>
  )
}

// === РОЛИ ===

const RolesTab: React.FC = () => {
  const [roles, setRoles] = useState<any[]>([])
  const [modalOpen, setModalOpen] = useState(false)
  const [editingRole, setEditingRole] = useState<any>(null)
  const [selectedPermissions, setSelectedPermissions] = useState<string[]>([])

  useEffect(() => { fetchRoles() }, [])

  const fetchRoles = async () => {
    try {
      const data = await getRoles()
      setRoles(data)
    } catch (error) {
      message.error('Ошибка загрузки ролей')
    }
  }

  const handleOpenModal = (role?: any) => {
    if (role) {
      setEditingRole(role)
      setSelectedPermissions(role.permissions || [])
    } else {
      setEditingRole(null)
      setSelectedPermissions([])
    }
    setModalOpen(true)
  }

  const handleSubmit = async () => {
    try {
      if (editingRole) {
        await updateRole(editingRole.id, { permissions: selectedPermissions })
        message.success('Роль обновлена')
      } else {
        message.info('Создание роли через API')
      }
      setModalOpen(false)
      fetchRoles()
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка сохранения')
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await deleteRole(id)
      message.success('Роль удалена')
      fetchRoles()
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка')
    }
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: 'Название', dataIndex: 'name', key: 'name' },
    { title: 'Описание', dataIndex: 'description', key: 'description' },
    { title: 'Права', key: 'permissions', render: (_: any, r: any) => (
      <Space wrap>
        {(r.permissions || []).map((p: string) => <Tag key={p}>{p}</Tag>)}
      </Space>
    )},
    { title: 'Действия', key: 'actions', width: 120, render: (_: any, r: any) => (
      <Space>
        <Button size="small" icon={<EditOutlined />} onClick={() => handleOpenModal(r)} />
        <Popconfirm title="Удалить?" onConfirm={() => handleDelete(r.id)}>
          <Button size="small" icon={<DeleteOutlined />} danger />
        </Popconfirm>
      </Space>
    )},
  ]

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Title level={4} style={{ margin: 0 }}>🔑 Роли</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => handleOpenModal()}>Добавить роль</Button>
      </div>
      <Table dataSource={roles} rowKey="id" columns={columns} pagination={false} size="small" />

      <Modal title={editingRole ? 'Редактировать роль' : 'Новая роль'} open={modalOpen} onOk={handleSubmit} onCancel={() => setModalOpen(false)}>
        <Form layout="vertical">
          <Form.Item label="Права доступа">
            <Checkbox.Group
              value={selectedPermissions}
              onChange={setSelectedPermissions}
              style={{ display: 'flex', flexDirection: 'column', gap: 8 }}
            >
              {ALL_PERMISSIONS.map(p => (
                <Checkbox key={p.key} value={p.key}>{p.label}</Checkbox>
              ))}
            </Checkbox.Group>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

// === КОМПАНИЯ ===

const CompanyTab: React.FC = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)

  useEffect(() => { loadSettings() }, [])

  const loadSettings = async () => {
    setLoading(true)
    try {
      const data = await getCompanySettings()
      form.setFieldsValue(data)
    } catch {
      message.error('Ошибка загрузки настроек')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      await updateCompanySettings(values)
      message.success('Настройки сохранены')
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка сохранения')
    }
  }

  return (
    <div>
      <Title level={4} style={{ marginBottom: 16 }}>🏢 Настройки компании</Title>
      <Form form={form} layout="vertical" onFinish={handleSubmit}>
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item label="Название компании" name="company_name" rules={[{ required: true }]}>
              <Input />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="ИНН" name="inn">
              <Input />
            </Form.Item>
          </Col>
        </Row>
        <Form.Item label="Адрес" name="address">
          <TextArea rows={2} />
        </Form.Item>
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item label="Телефон" name="phone">
              <Input />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="Email" name="email">
              <Input />
            </Form.Item>
          </Col>
        </Row>
        <Form.Item>
          <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={loading}>Сохранить</Button>
        </Form.Item>
      </Form>
    </div>
  )
}

// === НУМЕРАЦИЯ ЗАКАЗОВ ===

const OrderNumberingTab: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [state, setState] = useState<any>(null)
  const [nextNumber, setNextNumber] = useState<number | null>(null)

  useEffect(() => { loadNumbering() }, [])

  const loadNumbering = async () => {
    setLoading(true)
    try {
      const data = await getOrderNumbering()
      setState(data)
      setNextNumber(data.next_order_number)
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка загрузки нумерации')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!nextNumber) {
      message.error('Укажите следующий номер заказа')
      return
    }
    if (state?.min_allowed_next_order_number && nextNumber < state.min_allowed_next_order_number) {
      message.error(`Номер не может быть меньше ${state.min_allowed_next_order_number}`)
      return
    }

    setSaving(true)
    try {
      const data = await updateOrderNumbering(nextNumber)
      setState(data)
      setNextNumber(data.next_order_number)
      message.success(`Следующий заказ будет создан с номером ${data.next_order_number}`)
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка сохранения нумерации')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div>
      <Title level={4} style={{ marginBottom: 16 }}>🔢 Нумерация заказов</Title>
      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
        message="Настройка стартового номера заказов"
        description="Здесь можно задать номер, который получит следующий новый заказ. Удобно при установке CRM новой компании или переносе с другой системы."
      />

      <Card loading={loading} size="small">
        <Row gutter={16}>
          <Col xs={24} md={12}>
            <Form layout="vertical">
              <Form.Item
                label="Следующий номер заказа"
                tooltip="Новый заказ получит именно этот номер."
                required
              >
                <InputNumber
                  min={state?.min_allowed_next_order_number || 1}
                  precision={0}
                  style={{ width: '100%' }}
                  value={nextNumber}
                  onChange={(value) => setNextNumber(typeof value === 'number' ? value : null)}
                />
              </Form.Item>
              <Space>
                <Button type="primary" icon={<SaveOutlined />} loading={saving} onClick={handleSave}>
                  Сохранить номер
                </Button>
                <Button onClick={loadNumbering} loading={loading}>
                  Обновить
                </Button>
              </Space>
            </Form>
          </Col>

          <Col xs={24} md={12}>
            <Space direction="vertical" size={8} style={{ width: '100%' }}>
              <Text>Текущий следующий номер: <Text strong>{state?.next_order_number || '—'}</Text></Text>
              <Text>Максимальный номер в базе: <Text strong>{state?.max_order_id || 0}</Text></Text>
              <Text>Минимально допустимый следующий номер: <Text strong>{state?.min_allowed_next_order_number || 1}</Text></Text>
              <Text type="secondary" style={{ fontSize: 12 }}>
                Система не позволит поставить номер ниже уже существующего максимального заказа, чтобы не получить конфликт ID.
              </Text>
            </Space>
          </Col>
        </Row>
      </Card>
    </div>
  )
}

// === ШАБЛОНЫ ===

const TPL_VARIABLES = [
  { var: '{client_name}', desc: 'Имя клиента' },
  { var: '{client_phone}', desc: 'Телефон клиента' },
  { var: '{client_email}', desc: 'Email клиента' },
  { var: '{device_category}', desc: 'Вид устройства (телефон, ноутбук...)' },
  { var: '{device_brand}', desc: 'Бренд устройства' },
  { var: '{device_model}', desc: 'Модель устройства' },
  { var: '{serial_number}', desc: 'Серийный номер / IMEI' },
  { var: '{complaint}', desc: 'Причина обращения / описание поломки' },
  { var: '{diagnostics}', desc: 'Результат диагностики' },
  { var: '{total_cost}', desc: 'Общая стоимость ремонта' },
  { var: '{parts_cost}', desc: 'Стоимость запчастей' },
  { var: '{work_cost}', desc: 'Стоимость работ' },
  { var: '{order_id}', desc: 'Номер заказа' },
  { var: '{order_date}', desc: 'Дата приёма' },
  { var: '{order_status}', desc: 'Текущий статус' },
  { var: '{company_name}', desc: 'Название компании' },
  { var: '{company_inn}', desc: 'ИНН компании' },
  { var: '{company_address}', desc: 'Адрес компании' },
  { var: '{company_phone}', desc: 'Телефон компании' },
  { var: '{company_email}', desc: 'Email компании' },
  { var: '{master_name}', desc: 'ФИО мастера' },
  { var: '{warranty_days}', desc: 'Гарантийный срок (дни)' },
  { var: '{accessories}', desc: 'Комплектация (что сдал клиент)' },
  { var: '{items_table}', desc: 'Таблица запчастей и услуг (авто)' },
]

const QUILL_MODULES = {
  toolbar: [
    [{ header: [1, 2, 3, 4, 5, 6, false] }],
    ['bold', 'italic', 'underline', 'strike'],
    [{ color: [] }, { background: [] }],
    [{ align: [] }],
    [{ list: 'ordered' }, { list: 'bullet' }],
    [{ indent: '-1' }, { indent: '+1' }],
    ['link', 'image'],
    ['clean'],
    ['code-block'],
  ],
  table: false,  // Отключено - используйте кнопку ниже для вставки таблицы
}

// Функция вставки таблицы
const insertTableTemplate = (quillRef: any, rows: number, cols: number) => {
  if (!quillRef) return
  const editor = quillRef.getEditor()
  if (!editor) return
  
  let table = ''
  for (let r = 0; r < rows; r++) {
    const cells = []
    for (let c = 0; c < cols; c++) {
      cells.push(r === 0 ? `Заголовок${c+1}` : `Ячейка${r}-${c+1}`)
    }
    table += cells.join(' | ') + '\n'
  }
  
  const range = editor.getSelection()
  if (range) {
    editor.insertText(range.index, table)
  } else {
    editor.insertText(0, table)
  }
}

const QUILL_FORMATS = [
  'header', 'bold', 'italic', 'underline', 'strike',
  'color', 'background', 'align', 'list', 'bullet', 'indent',
  'link', 'image', 'code-block',
]

const EDITOR_HEIGHT = 500

const TemplatesTab: React.FC = () => {
  const [templates, setTemplates] = useState<any[]>([])
  const [saving, setSaving] = useState(false)
  const [previewOpen, setPreviewOpen] = useState(false)
  const [previewContent, setPreviewContent] = useState('')
  const [previewTitle, setPreviewTitle] = useState('')
  const [addModal, setAddModal] = useState(false)
  const [newType, setNewType] = useState('')
  const [newTypeName, setNewTypeName] = useState('')
  const [newContent, setNewContent] = useState('')

  // Назначения шаблонов
  const [assignments, setAssignments] = useState<Record<string, any>>({})
  const [assignLoading, setAssignLoading] = useState(false)

  // Модалка редактирования
  const [editModalOpen, setEditModalOpen] = useState(false)
  const [editingTemplate, setEditingTemplate] = useState<any>(null)
  const [editContent, setEditContent] = useState('')

  useEffect(() => { 
    fetchTemplates()
    fetchAssignments()
  }, [])

  const fetchTemplates = async () => {
    try {
      const data = await getTemplates()
      setTemplates(data)
    } catch (error) {
      message.error('Ошибка загрузки шаблонов')
    }
  }

  const fetchAssignments = async () => {
    try {
      const { getTemplateAssignments } = await import('../api')
      const data = await getTemplateAssignments()
      const assigns: Record<string, any> = {}
      data.forEach((a: any) => {
        assigns[a.document_type] = a.template_id
      })
      setAssignments(assigns)
    } catch (error) {
      console.error('Error fetching assignments:', error)
    }
  }

  const handleAssign = async (documentType: string, templateId: number) => {
    setAssignLoading(true)
    try {
      const { assignTemplate } = await import('../api')
      await assignTemplate(documentType, templateId)
      message.success(`Шаблон назначен на "${documentType}"`)
      fetchAssignments()
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка назначения')
    } finally {
      setAssignLoading(false)
    }
  }

  const handleEdit = (tmpl: any) => {
    setEditingTemplate(tmpl)
    setEditContent(tmpl.content_template)
    setEditModalOpen(true)
  }

  const handleSave = async () => {
    if (!editingTemplate) return
    setSaving(true)
    try {
      await updateTemplate(editingTemplate.type, { content_template: editContent })
      message.success('Шаблон сохранён')
      setEditModalOpen(false)
      setEditingTemplate(null)
      fetchTemplates()
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка сохранения')
    } finally {
      setSaving(false)
    }
  }

  const handlePreview = (tmpl: any) => {
    const info = templateInfo[tmpl.type] || { name: tmpl.type }
    setPreviewTitle(`${info.name} — ${tmpl.type}`)
    setPreviewContent(tmpl.content_template)
    setPreviewOpen(true)
  }

  const handleAddTemplate = async () => {
    if (!newType.trim()) { message.error('Введите тип шаблона'); return }
    try {
      const { createTemplate } = await import('../api')
      await createTemplate({ type: newType.trim(), content_template: newContent })
      message.success('Шаблон создан')
      setAddModal(false)
      setNewType('')
      setNewTypeName('')
      setNewContent('')
      fetchTemplates()
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка создания')
    }
  }

  const templateInfo: Record<string, { name: string; icon: string; color: string; desc: string }> = {
    receipt: { name: 'Квитанция приёма', icon: '🧾', color: 'blue', desc: 'Выдаётся клиенту при приёме устройства' },
    diagnostic_act: { name: 'Акт диагностики', icon: '🔍', color: 'orange', desc: 'Результаты диагностики устройства' },
    work_act: { name: 'Акт выполненных работ', icon: '✅', color: 'green', desc: 'Подтверждение выполненных работ' },
    invoice: { name: 'Счёт для юрлица', icon: '📄', color: 'purple', desc: 'Счёт для юридических лиц' },
  }

  const columns = [
    {
      title: '№',
      key: 'index',
      width: 50,
      render: (_: any, __: any, idx: number) => idx + 1,
    },
    {
      title: 'Название',
      key: 'name',
      width: 180,
      render: (_: any, r: any) => {
        const info = templateInfo[r.type] || { name: r.type, icon: '📄', color: 'default', desc: r.type }
        return (
          <div>
            <Tag color={info.color}>{info.icon} {info.name}</Tag>
            <br />
            <Text type="secondary" style={{ fontSize: 11 }}>{info.desc}</Text>
          </div>
        )
      },
    },
    {
      title: 'Тип',
      dataIndex: 'type',
      key: 'type',
      width: 120,
      render: (v: string) => <Tag>{v}</Tag>,
    },
    {
      title: 'Содержимое',
      key: 'content',
      render: (_: any, r: any) => (
        <iframe
          srcDoc={r.content_template}
          sandbox=""
          style={{
            width: '100%', height: 60,
            background: '#fafafa', borderRadius: 4,
            border: '1px solid #f0f0f0',
          }}
        />
      ),
    },
    {
      title: 'Обновлён',
      dataIndex: 'updated_at',
      key: 'updated_at',
      width: 120,
      render: (v: string) => v ? dayjs(v).format('DD.MM.YYYY HH:mm') : '—',
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 140,
      render: (_: any, r: any) => (
        <Space direction="vertical" size={4}>
          <Button
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handlePreview(r)}
            block
          >
            Просмотр
          </Button>
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(r)}
            block
          >
            Редактировать
          </Button>
        </Space>
      ),
    },
  ]

  // Шаблон для нового типа
  const renderQuillEditor = (value: string, onChange: (v: string) => void) => (
    <div style={{ display: 'flex', gap: 12 }}>
      <div style={{ flex: 1 }}>
        <HugerteEditor
          value={value}
          onChange={onChange}
          height="500px"
        />
      </div>
      <div style={{ width: 220, flexShrink: 0 }}>
        <Text strong style={{ fontSize: 12 }}>📌 Переменные:</Text>
        <div style={{
          maxHeight: 300, overflow: 'auto', marginTop: 6,
          background: '#f5f5f5', borderRadius: 6, padding: 8,
          border: '1px solid #e8e8e8',
        }}>
          {TPL_VARIABLES.map(v => (
            <div key={v.var} style={{ marginBottom: 4 }}>
              <Tag
                color="blue"
                style={{ cursor: 'pointer', fontSize: 10, marginBottom: 2 }}
                onClick={() => {
                  onChange(value + v.var)
                  message.success(`${v.var} добавлен`)
                }}
              >
                {v.var}
              </Tag>
              <Text type="secondary" style={{ fontSize: 10, display: 'block' }}>{v.desc}</Text>
            </div>
          ))}
        </div>
        
        <Divider style={{ margin: '8px 0' }} />
        
        <Text strong style={{ fontSize: 11 }}>📊 Таблицы:</Text>
        <Space direction="vertical" size={2} style={{ marginTop: 4 }}>
          <Button size="small" block onClick={() => onChange(value + '\n| Заголовок 1 | Заголовок 2 | Заголовок 3 |\n| --- | --- | --- |\n| | | | |\n')}>
            3 колонки
          </Button>
          <Button size="small" block onClick={() => onChange(value + '\n| Заголовок 1 | Заголовок 2 | Заголовок 3 | Заголовок 4 |\n| --- | --- | --- | --- |\n| | | | | |\n')}>
            4 колонки
          </Button>
        </Space>
      </div>
    </div>
  )

  // Редактор внутри модалки
  const renderEditEditor = () => (
    <div style={{ display: 'flex', gap: 12, height: '65vh' }}>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
        <div style={{ marginBottom: 8, display: 'flex', gap: 8, alignItems: 'center', flexShrink: 0 }}>
          <Button
            size="small"
            icon={<UploadOutlined />}
            onClick={() => {
              const input = document.createElement('input')
              input.type = 'file'
              input.accept = '.html,.htm,.txt'
              input.onchange = (e) => {
                const file = (e.target as HTMLInputElement).files?.[0]
                if (file) {
                  const reader = new FileReader()
                  reader.onload = (event) => {
                    const content = event.target?.result as string
                    setEditContent(content)
                    message.success(`Шаблон загружен из файла: ${file.name}`)
                  }
                  reader.readAsText(file)
                }
              }
              input.click()
            }}
          >
            Импорт HTML
          </Button>
          <Button
            size="small"
            icon={<DownloadOutlined />}
            onClick={() => {
              const blob = new Blob([editContent], { type: 'text/html' })
              const url = URL.createObjectURL(blob)
              const a = document.createElement('a')
              a.href = url
              a.download = `template_${editingTemplate?.type || 'export'}.html`
              a.click()
              URL.revokeObjectURL(url)
              message.success('Шаблон экспортирован в файл')
            }}
          >
            Экспорт HTML
          </Button>
          <Text type="secondary" style={{ fontSize: 12 }}>
            💡 Кнопка "Code" в редакторе покажет HTML код
          </Text>
        </div>
        <div style={{ flex: 1, minHeight: 0 }}>
          <HugerteEditor
            value={editContent}
            onChange={setEditContent}
            height="100%"
          />
        </div>
      </div>
      <div style={{ width: 240, flexShrink: 0, display: 'flex', flexDirection: 'column' }}>
        <Text strong style={{ fontSize: 13, marginBottom: 8 }}>📌 Переменные (кликните для вставки):</Text>
        <div style={{
          flex: 1, overflow: 'auto',
          background: '#f5f5f5', borderRadius: 6, padding: 12,
          border: '1px solid #e8e8e8',
        }}>
          {TPL_VARIABLES.map(v => (
            <div key={v.var} style={{ marginBottom: 6 }}>
              <Tag
                color="blue"
                style={{ cursor: 'pointer', fontSize: 11, marginBottom: 2 }}
                onClick={() => {
                  setEditContent(prev => prev + v.var)
                  message.success(`${v.var} добавлен`)
                }}
              >
                {v.var}
              </Tag>
              <Text type="secondary" style={{ fontSize: 10, display: 'block', lineHeight: 1.2 }}>{v.desc}</Text>
            </div>
          ))}
        </div>
        
        <Divider style={{ margin: '12px 0' }} />
        
        <Text strong style={{ fontSize: 12 }}>📊 Вставка таблицы:</Text>
        <Space direction="vertical" size={4} style={{ marginTop: 8 }}>
          <Button 
            size="small" 
            block
            onClick={() => {
              const table = '\n| Заголовок 1 | Заголовок 2 | Заголовок 3 |\n| --- | --- | --- |\n| Ячейка 1 | Ячейка 2 | Ячейка 3 |\n'
              setEditContent(prev => prev + table)
              message.success('Таблица 3x2 добавлена')
            }}
          >
            3x2 (3 колонки)
          </Button>
          <Button 
            size="small" 
            block
            onClick={() => {
              const table = '\n| Заголовок 1 | Заголовок 2 | Заголовок 3 | Заголовок 4 |\n| --- | --- | --- | --- |\n| Ячейка 1 | Ячейка 2 | Ячейка 3 | Ячейка 4 |\n'
              setEditContent(prev => prev + table)
              message.success('Таблица 4x2 добавлена')
            }}
          >
            4x2 (4 колонки)
          </Button>
          <Button 
            size="small" 
            block
            onClick={() => {
              const table = '\n| Позиция | Артикул | Гарантия | Цена | Скидка | Кол-во | Сумма |\n| --- | --- | --- | --- | --- | --- | --- |\n| | | | | | | |\n'
              setEditContent(prev => prev + table)
              message.success('Таблица работ добавлена')
            }}
          >
            Таблица работ
          </Button>
          <Button 
            size="small" 
            block
            type="primary"
            onClick={() => {
              setEditContent(prev => prev + '{items_table}')
              message.success('Авто-таблица добавлена')
            }}
          >
            📋 Авто-таблица (запчасти+услуги)
          </Button>
        </Space>
      </div>
    </div>
  )

  return (
    <div style={{ width: '100%', minWidth: 0 }}>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
        <Title level={4} style={{ margin: 0 }}>📄 Шаблоны документов</Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setAddModal(true)}
        >
          Добавить шаблон
        </Button>
      </div>
      <Alert
        message="Подсказка"
        description="Используйте переменные для автозаполнения данных заказа. Кликните по переменной справа от редактора чтобы вставить её."
        type="info"
        showIcon
        style={{ marginBottom: 16, fontSize: 12, width: '100%' }}
      />
      
      {/* Панель назначений шаблонов */}
      <Card 
        title="📌 Назначения шаблонов на типы документов" 
        size="small"
        style={{ marginBottom: 16, width: '100%' }}
      >
        <Space direction="vertical" size={12} style={{ width: '100%' }}>
          <div style={{ marginBottom: 4 }}>
            <Text strong style={{ display: 'block', marginBottom: 4 }}>🧾 Квитанция приёма:</Text>
            <Select
              style={{ width: '100%' }}
              value={assignments['receipt']}
              onChange={(val) => handleAssign('receipt', val)}
              loading={assignLoading}
              options={templates.map((t: any) => ({
                value: t.id,
                label: `${t.type} — ${t.content_template?.substring(0, 50) || ''}...`
              }))}
              placeholder="Выберите шаблон"
              allowClear
            />
          </div>
          <div style={{ marginBottom: 4 }}>
            <Text strong style={{ display: 'block', marginBottom: 4 }}>🔍 Акт диагностики:</Text>
            <Select
              style={{ width: '100%' }}
              value={assignments['diagnostic_act']}
              onChange={(val) => handleAssign('diagnostic_act', val)}
              loading={assignLoading}
              options={templates.map((t: any) => ({
                value: t.id,
                label: `${t.type} — ${t.content_template?.substring(0, 50) || ''}...`
              }))}
              placeholder="Выберите шаблон"
              allowClear
            />
          </div>
          <div style={{ marginBottom: 4 }}>
            <Text strong style={{ display: 'block', marginBottom: 4 }}>✅ Акт выполненных работ:</Text>
            <Select
              style={{ width: '100%' }}
              value={assignments['work_act']}
              onChange={(val) => handleAssign('work_act', val)}
              loading={assignLoading}
              options={templates.map((t: any) => ({
                value: t.id,
                label: `${t.type} — ${t.content_template?.substring(0, 50) || ''}...`
              }))}
              placeholder="Выберите шаблон"
              allowClear
            />
          </div>
          <div style={{ marginBottom: 4 }}>
            <Text strong style={{ display: 'block', marginBottom: 4 }}>📄 Счёт на оплату:</Text>
            <Select
              style={{ width: '100%' }}
              value={assignments['invoice']}
              onChange={(val) => handleAssign('invoice', val)}
              loading={assignLoading}
              options={templates.map((t: any) => ({
                value: t.id,
                label: `${t.type} — ${t.content_template?.substring(0, 50) || ''}...`
              }))}
              placeholder="Выберите шаблон"
              allowClear
            />
          </div>
        </Space>
        <Text type="secondary" style={{ display: 'block', marginTop: 12, fontSize: 11 }}>
          💡 Если назначение не установлено, используется шаблон по типу (например, шаблон с типом "receipt" для квитанции)
        </Text>
      </Card>
      
      <Table
        dataSource={templates}
        rowKey="id"
        columns={columns}
        pagination={false}
        size="middle"
        style={{ width: '100%' }}
        scroll={{ x: '100%' }}
      />

      {/* Модалка предпросмотра */}
      <Modal
        title={`👁️ Предпросмотр: ${previewTitle}`}
        open={previewOpen}
        onCancel={() => setPreviewOpen(false)}
        width={900}
        footer={[
          <Button key="close" onClick={() => setPreviewOpen(false)}>Закрыть</Button>,
        ]}
      >
        <iframe
          srcDoc={previewContent}
          sandbox=""
          style={{
            width: '100%',
            height: 500,
            background: '#fff',
            border: '1px solid #e8e8e8',
            borderRadius: 4,
          }}
        />
        <style>{`
          .ant-modal-body table {
            border-collapse: collapse;
            width: 100%;
            margin: 10px 0;
          }
          .ant-modal-body td, .ant-modal-body th {
            border: 1px solid #000;
            padding: 8px;
          }
          .ant-modal-body h1 { font-size: 24px; margin: 10px 0; }
          .ant-modal-body h2 { font-size: 20px; margin: 10px 0; }
          .ant-modal-body h3 { font-size: 16px; margin: 10px 0; }
          .ant-modal-body p { margin: 8px 0; }
          .ant-modal-body ol, .ant-modal-body ul { margin: 10px 0; padding-left: 20px; }
          .ant-modal-body li { margin: 4px 0; }
        `}</style>
      </Modal>

      {/* Модалка редактирования шаблона */}
      <Modal
        title={`✏️ Редактирование: ${editingTemplate ? (templateInfo[editingTemplate.type]?.name || editingTemplate.type) : ''}`}
        open={editModalOpen}
        onOk={handleSave}
        onCancel={() => { setEditModalOpen(false); setEditingTemplate(null) }}
        width={1400}
        style={{ top: 20 }}
        bodyStyle={{ padding: '12px', height: '70vh', display: 'flex', flexDirection: 'column' }}
        okText="Сохранить"
        cancelText="Отмена"
        okButtonProps={{ loading: saving }}
      >
        {renderEditEditor()}
      </Modal>

      {/* Модалка добавления шаблона */}
      <Modal
        title="➕ Добавить шаблон"
        open={addModal}
        onOk={handleAddTemplate}
        onCancel={() => { setAddModal(false); setNewType(''); setNewTypeName(''); setNewContent('') }}
        width={1000}
        okText="Создать"
        cancelText="Отмена"
      >
        <Form layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="Тип шаблона (лат.)" required>
                <Input
                  value={newType}
                  onChange={e => setNewType(e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, ''))}
                  placeholder="например: warranty_act"
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Название (рус.)">
                <Input
                  value={newTypeName}
                  onChange={e => setNewTypeName(e.target.value)}
                  placeholder="например: Гарантийный акт"
                />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item label="Содержимое шаблона">
            {renderQuillEditor(newContent, setNewContent)}
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

// === БАЗА ДАННЫХ (просмотр таблиц) ===

interface TableInfo {
  name: string
  columns: { name: string; type: string }[]
}

interface TableData {
  table: string
  columns: { name: string; type: string }[]
  data: Record<string, any>[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

interface QueryResult {
  columns: { name: string; type: string }[]
  data: Record<string, any>[]
  row_count: number
}

const DatabaseTab: React.FC = () => {
  const { user } = useContext(AuthContext)
  const isAdmin = user?.role_name === 'admin'

  const [tables, setTables] = useState<TableInfo[]>([])
  const [selectedTable, setSelectedTable] = useState<string>('')
  const [tableData, setTableData] = useState<TableData | null>(null)
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(50)
  const [queryText, setQueryText] = useState('')
  const [queryResult, setQueryResult] = useState<QueryResult | null>(null)
  const [queryLoading, setQueryLoading] = useState(false)
  const [activeSubTab, setActiveSubTab] = useState<'tables' | 'query'>('tables')

  // Маппинг названий таблиц на русский
  const TABLE_NAMES: Record<string, string> = {
    'users': 'Пользователи',
    'roles': 'Роли',
    'orders': 'Заказы',
    'order_comments': 'Комментарии к заказам',
    'order_payments': 'Платежи по заказам',
    'order_parts': 'Запчасти в заказах',
    'order_services': 'Услуги в заказах',
    'parts': 'Запчасти',
    'part_movements': 'Движение запчастей',
    'clients': 'Клиенты',
    'salary_configs': 'Настройки зарплаты',
    'salary_records': 'Записи зарплаты',
    'cash_shifts': 'Кассовые смены',
    'cash_transactions': 'Кассовые транзакции',
    'custom_statuses': 'Статусы заказов',
    'brands': 'Бренды устройств',
    'categories': 'Категории устройств',
    'device_models': 'Модели устройств',
    'client_sources': 'Источники клиентов',
    'age_groups': 'Возрастные группы',
    'bot_settings': 'Настройки бота',
    'notification_tasks': 'Задачи уведомлений',
    'document_templates': 'Шаблоны документов',
    'company_settings': 'Настройки компании',
    'permission_groups': 'Группы прав',
    'role_permissions': 'Права ролей',
    'individual_permissions': 'Индивидуальные права',
  }

  const getTableName = (tableName: string): string => {
    return TABLE_NAMES[tableName] || tableName
  }

  useEffect(() => {
    if (isAdmin) {
      fetchTables()
    }
  }, [isAdmin])

  const fetchTables = async () => {
    try {
      const response = await api.get('/database/tables')
      setTables(response.data)
    } catch (error) {
      message.error('Ошибка загрузки списка таблиц')
    }
  }

  const fetchTableData = async (tableName: string, pageNum: number = 1) => {
    setLoading(true)
    try {
      const response = await api.get(`/database/table/${tableName}`, {
        params: { page: pageNum, page_size: pageSize }
      })
      setTableData(response.data)
      setPage(pageNum)
      setSelectedTable(tableName)
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка загрузки данных')
    } finally {
      setLoading(false)
    }
  }

  const executeQuery = async () => {
    if (!queryText.trim()) {
      message.error('Введите SQL запрос')
      return
    }

    setQueryLoading(true)
    try {
      const response = await api.post('/database/query', { query: queryText })
      setQueryResult(response.data)
      message.success(`Запрос выполнен, найдено ${response.data.row_count} записей`)
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка выполнения запроса')
      setQueryResult(null)
    } finally {
      setQueryLoading(false)
    }
  }

  if (!isAdmin) {
    return (
      <Alert
        message="Доступ запрещён"
        description="Просмотр базы данных доступен только администраторам"
        type="warning"
        showIcon
        style={{ marginTop: 16 }}
      />
    )
  }

  return (
    <div>
      <Title level={4} style={{ marginBottom: 16 }}>🗄 База данных</Title>
      
      <Card size="small" style={{ marginBottom: 16 }}>
        <Menu
          mode="horizontal"
          selectedKeys={[activeSubTab]}
          onClick={({ key }) => setActiveSubTab(key as 'tables' | 'query')}
          items={[
            { key: 'tables', label: '📊 Таблицы' },
            { key: 'query', label: '✏️ SQL запрос' },
          ]}
        />
      </Card>

      {activeSubTab === 'tables' && (
        <Row gutter={[12, 12]} align="top">
          <Col xs={24} lg={10} xl={7} xxl={6}>
            <Card
              title="Таблицы"
              size="small"
              bodyStyle={{ padding: 8, maxHeight: 560, overflow: 'auto' }}
              style={{ width: '100%' }}
            >
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {tables.map(t => {
                  const isSelected = selectedTable === t.name
                  return (
                    <div
                      key={t.name}
                      role="button"
                      tabIndex={0}
                      onClick={() => fetchTableData(t.name, 1)}
                      onKeyDown={(event) => {
                        if (event.key === 'Enter' || event.key === ' ') {
                          event.preventDefault()
                          fetchTableData(t.name, 1)
                        }
                      }}
                      style={{
                        padding: '10px 12px',
                        borderRadius: 8,
                        border: isSelected ? '1px solid #1677ff' : '1px solid transparent',
                        background: isSelected ? 'rgba(22, 119, 255, 0.14)' : 'transparent',
                        cursor: 'pointer',
                      }}
                    >
                      <div
                        title={t.name}
                        style={{
                          fontWeight: 500,
                          fontSize: 13,
                          lineHeight: 1.3,
                          whiteSpace: 'normal',
                          wordBreak: 'break-word',
                        }}
                      >
                        {getTableName(t.name)}
                      </div>
                    </div>
                  )
                })}
              </div>
            </Card>
          </Col>
          <Col xs={24} lg={14} xl={17} xxl={18}>
            <Card
              title={selectedTable ? `${getTableName(selectedTable)} (${selectedTable})` : 'Выберите таблицу'}
              size="small"
              style={{ width: '100%' }}
              bodyStyle={{ overflow: 'hidden' }}
              extra={tableData && (
                <Text type="secondary">
                  {tableData.total} записей | Стр. {tableData.page} из {tableData.total_pages}
                </Text>
              )}
            >
              {!selectedTable ? (
                <Text type="secondary">Выберите таблицу из списка слева</Text>
              ) : loading ? (
                <Text>Загрузка...</Text>
              ) : tableData ? (
                <>
                  <Table
                    columns={tableData.columns.map(col => ({
                      title: col.name,
                      dataIndex: col.name,
                      key: col.name,
                      ellipsis: true,
                      width: 150,
                      render: (val: any) => (
                        <div style={{ minHeight: '24px', display: 'flex', alignItems: 'center' }}>
                          {val === null ? <span style={{ color: '#999' }}>null</span> :
                           typeof val === 'boolean' ? (val ? '✓' : '✗') :
                           typeof val === 'object' ? JSON.stringify(val) :
                           String(val)}
                        </div>
                      )
                    }))}
                    dataSource={tableData.data.map((row, idx) => ({ ...row, key: idx }))}
                    pagination={{
                      current: tableData.page,
                      pageSize: tableData.page_size,
                      total: tableData.total,
                      showSizeChanger: false,
                      onChange: (p) => fetchTableData(selectedTable, p)
                    }}
                    size="small"
                    scroll={{ x: Math.max(tableData.columns.length * 160, 800) }}
                  />
                </>
              ) : null}
            </Card>
          </Col>
        </Row>
      )}

      {activeSubTab === 'query' && (
        <Card title="Выполнить SQL запрос (только SELECT)" size="small">
          <Alert
            message="⚠️ Безопасность"
            description="Разрешены только SELECT запросы. Запросы DROP, DELETE, UPDATE, INSERT запрещены."
            type="warning"
            showIcon
            style={{ marginBottom: 16 }}
          />
          <TextArea
            value={queryText}
            onChange={(e) => setQueryText(e.target.value)}
            placeholder="SELECT * FROM orders LIMIT 10"
            rows={6}
            style={{ fontFamily: 'monospace', fontSize: 13 }}
          />
          <div style={{ marginTop: 12, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <Button
              type="primary"
              onClick={executeQuery}
              loading={queryLoading}
            >
              Выполнить
            </Button>
            <Button
              onClick={() => {
                setQueryText('SELECT * FROM orders ORDER BY id DESC LIMIT 50')
              }}
            >
              Пример: заказы
            </Button>
            <Button
              onClick={() => {
                setQueryText('SELECT * FROM users')
              }}
            >
              Пример: пользователи
            </Button>
            <Button
              onClick={() => {
                setQueryText('SELECT * FROM parts')
              }}
            >
              Пример: запчасти
            </Button>
          </div>

          {queryResult && (
            <Card title={`Результат (${queryResult.row_count} записей)`} size="small" style={{ marginTop: 16 }}>
              <Table
                columns={queryResult.columns.map(col => ({
                  title: col.name,
                  dataIndex: col.name,
                  key: col.name,
                  ellipsis: true,
                  width: 150,
                  render: (val: any) => (
                    <div style={{ minHeight: '24px', display: 'flex', alignItems: 'center' }}>
                      {val === null ? <span style={{ color: '#999' }}>null</span> :
                       typeof val === 'boolean' ? (val ? '✓' : '✗') :
                       typeof val === 'object' ? JSON.stringify(val) :
                       String(val)}
                    </div>
                  )
                }))}
                dataSource={queryResult.data.map((row, idx) => ({ ...row, key: idx }))}
                pagination={false}
                size="small"
                scroll={{ x: Math.max(queryResult.columns.length * 160, 800) }}
              />
            </Card>
          )}
        </Card>
      )}
    </div>
  )
}

export default SettingsPage
