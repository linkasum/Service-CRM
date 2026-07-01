import React, { useState, useEffect } from 'react'
import {
  Table, Button, Input, Select, Modal, Form, Space, Tag, Popconfirm, message,
  Card, Typography, Avatar, Row, Col, Checkbox
} from 'antd'
import {
  PlusOutlined, EditOutlined, DeleteOutlined, ReloadOutlined, TeamOutlined,
  UserOutlined, LockOutlined, DollarOutlined, MessageOutlined
} from '@ant-design/icons'
import {
  getUsers, createUser, updateUser, deactivateUser, hardDeleteUser, resetUserPassword,
  getRoles
} from '../api'
import api from '../api'

const { Text } = Typography

const EmployeesTab: React.FC = () => {
  const [users, setUsers] = useState<any[]>([])
  const [roles, setRoles] = useState<any[]>([])
  const [salaryConfigs, setSalaryConfigs] = useState<any[]>([])
  const [modalOpen, setModalOpen] = useState(false)
  const [editingUser, setEditingUser] = useState<any>(null)
  const [telegramLink, setTelegramLink] = useState<any>(null)
  const [telegramLinkOpen, setTelegramLinkOpen] = useState(false)
  const [telegramLinkLoading, setTelegramLinkLoading] = useState<number | null>(null)
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchUsers()
    fetchRoles()
    fetchSalaryConfigs()
  }, [])

  const fetchUsers = async () => {
    setLoading(true)
    try {
      const data = await getUsers()
      setUsers(data.items || data)
    } catch {
      message.error('Ошибка загрузки сотрудников')
    } finally {
      setLoading(false)
    }
  }

  const fetchRoles = async () => {
    try {
      const data = await getRoles()
      setRoles(data)
    } catch {}
  }

  const fetchSalaryConfigs = async () => {
    try {
      const res = await api.get('/salary/config')
      setSalaryConfigs(res.data || [])
    } catch {}
  }

  const handleCreate = () => {
    setEditingUser(null)
    form.resetFields()
    form.setFieldsValue({ is_active: true })
    setModalOpen(true)
  }

  const handleEdit = (record: any) => {
    setEditingUser(record)
    form.setFieldsValue({
      username: record.username,
      full_name: record.full_name || record.username,
      password: '',
      email: record.email || '',
      role_id: record.role_id,
      phone: record.phone || '',
      telegram_chat_id: record.telegram_chat_id ? String(record.telegram_chat_id) : '',
      salary_config_id: record.salary_config_id,
      is_active: record.is_active !== false,
    })
    setModalOpen(true)
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      const payload: any = {
        username: values.username,
        full_name: values.full_name || values.username,
        role_id: values.role_id,
        telegram_chat_id: values.telegram_chat_id ? Number(String(values.telegram_chat_id).trim()) : null,
        salary_config_id: values.salary_config_id,
        is_active: values.is_active,
      }
      if (values.password) payload.password = values.password
      if (values.email) payload.email = values.email
      if (values.phone) payload.phone = values.phone

      if (editingUser) {
        await updateUser(editingUser.id, payload)
        message.success('Сотрудник обновлён')
      } else {
        if (!values.password) {
          message.error('Пароль обязателен при создании')
          return
        }
        await createUser(payload)
        message.success('Сотрудник создан')
      }
      setModalOpen(false)
      form.resetFields()
      fetchUsers()
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка сохранения')
    }
  }

  const handleDeactivate = async (id: number) => {
    try {
      await deactivateUser(id)
      message.success('Сотрудник деактивирован')
      fetchUsers()
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка')
    }
  }

  const handleResetPassword = async (id: number) => {
    try {
      await resetUserPassword(id)
      message.success('Пароль сброшен')
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка')
    }
  }

  const handleCreateTelegramLink = async (record: any) => {
    setTelegramLinkLoading(record.id)
    try {
      const res = await api.post(`/bot/users/${record.id}/link-token`)
      setTelegramLink(res.data)
      setTelegramLinkOpen(true)
      message.success('Telegram-код создан')
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка создания Telegram-кода')
    } finally {
      setTelegramLinkLoading(null)
    }
  }

  const copyTelegramCommand = async () => {
    if (!telegramLink?.command) return
    if (!navigator.clipboard?.writeText) {
      message.info('Скопируйте команду вручную')
      return
    }
    await navigator.clipboard.writeText(telegramLink.command)
    message.success('Команда скопирована')
  }

  const handleDelete = async (id: number) => {
    try {
      await hardDeleteUser(id)
      message.success('Сотрудник удалён')
      fetchUsers()
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка удаления')
    }
  }

  const roleColors: Record<string, string> = {
    admin: 'red',
    manager: 'blue',
    master: 'green',
  }

  const roleLabels: Record<string, string> = {
    admin: 'Администратор',
    manager: 'Менеджер',
    master: 'Мастер',
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 50 },
    {
      title: 'Сотрудник',
      key: 'name',
      width: 200,
      render: (_: any, r: any) => (
        <Space>
          <Avatar size="small" style={{background: roleColors[r.role_name] || '#888'}}>
            {(r.full_name || r.username)[0]?.toUpperCase()}
          </Avatar>
          <div>
            <Text strong>{r.full_name || r.username}</Text>
            <br />
            <Text type="secondary" style={{ fontSize: 10 }}>Логин: {r.username}</Text>
          </div>
        </Space>
      ),
    },
    { title: 'Email', dataIndex: 'email', key: 'email', render: (v: string) => v || '—' },
    { title: 'Телефон', dataIndex: 'phone', key: 'phone', render: (v: string) => v || '—' },
    { title: 'Telegram ID', dataIndex: 'telegram_chat_id', key: 'telegram', width: 130, render: (v: number | null) => (
      v ? <Tag color="cyan">{v}</Tag> : <Text type="secondary">—</Text>
    )},
    { title: 'Роль', dataIndex: 'role_name', key: 'role', width: 120, render: (v: string) => (
      <Tag color={roleColors[v] || 'default'}>{roleLabels[v] || v}</Tag>
    )},
    { title: 'Зарплата', key: 'salary', width: 200, render: (_: any, r: any) => {
      const config = salaryConfigs.find((c: any) => c.id === r.salary_config_id)
      if (!config) return <Text type="secondary">Не назначена</Text>
      if (config.config_type === 'fixed') {
        return <Text>{config.fixed_amount} ₽ / {config.period}</Text>
      }
      return <Text code style={{fontSize: 11}}>{config.formula_string}</Text>
    }},
    { title: 'Статус', dataIndex: 'is_active', key: 'status', width: 80, render: (v: boolean) => (
      <Tag color={v !== false ? 'green' : 'default'}>{v !== false ? '✅' : '⏸️'}</Tag>
    )},
    { title: 'Действия', key: 'actions', width: 270, render: (_: any, r: any) => (
      <Space size={4}>
        <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(r)} />
        <Button
          size="small"
          icon={<MessageOutlined />}
          loading={telegramLinkLoading === r.id}
          onClick={() => handleCreateTelegramLink(r)}
        >
          TG
        </Button>
        <Popconfirm title="Сбросить пароль?" onConfirm={() => handleResetPassword(r.id)}>
          <Button size="small" icon={<ReloadOutlined />} />
        </Popconfirm>
        {r.is_active !== false && (
          <Popconfirm title="Деактивировать?" onConfirm={() => handleDeactivate(r.id)}>
            <Button size="small" icon={<LockOutlined />} danger />
          </Popconfirm>
        )}
        <Popconfirm
          title={`Удалить сотрудника "${r.full_name || r.username}"?`}
          description="Это действие удалит пользователя навсегда. Если есть связанные данные, сервер может запретить удаление."
          okText="Удалить"
          cancelText="Отмена"
          okButtonProps={{ danger: true }}
          onConfirm={() => handleDelete(r.id)}
        >
          <Button size="small" icon={<DeleteOutlined />} danger>
            Удалить
          </Button>
        </Popconfirm>
      </Space>
    )},
  ]

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Space>
          <TeamOutlined style={{ fontSize: 24 }} />
          <Text style={{ fontSize: 18, fontWeight: 600 }}>Сотрудники</Text>
          <Text type="secondary">Всего: {users.length}</Text>
        </Space>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>Добавить сотрудника</Button>
      </div>

      <Card size="small">
        <Table
          dataSource={users}
          rowKey="id"
          loading={loading}
          columns={columns}
          pagination={false}
          size="small"
        />
      </Card>

      <Modal
        title={editingUser ? 'Редактировать сотрудника' : 'Новый сотрудник'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => { setModalOpen(false); form.resetFields() }}
        width={480}
        okText={editingUser ? 'Сохранить' : 'Создать'}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 8 }}>
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item
                label="Логин"
                name="username"
                rules={[{ required: true, message: 'Введите логин' }]}
                extra="Используется для входа в систему"
              >
                <Input placeholder="ivanov" prefix={<UserOutlined />} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="Имя (отображаемое)"
                name="full_name"
                extra="Отображается в интерфейсе"
              >
                <Input placeholder="Иванов Иван" prefix={<TeamOutlined />} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            label="Пароль"
            name="password"
            rules={[{ required: !editingUser, message: 'Введите пароль' }]}
            extra={editingUser ? 'Оставьте пустым чтобы не менять' : undefined}
          >
            <Input.Password placeholder="••••••••" prefix={<LockOutlined />} />
          </Form.Item>

          <Row gutter={12}>
            <Col span={12}>
              <Form.Item label="Email" name="email">
                <Input placeholder="email@mail.ru" prefix={<UserOutlined />} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Роль" name="role_id" rules={[{ required: true, message: 'Выберите роль' }]}>
                <Select placeholder="Выберите роль">
                  {roles.map((r: any) => (
                    <Select.Option key={r.id} value={r.id}>{r.name}</Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={12}>
            <Col span={12}>
              <Form.Item label="Телефон" name="phone">
                <Input placeholder="+7 (999) 123-45-67" prefix={<UserOutlined />} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="Telegram ID"
                name="telegram_chat_id"
                rules={[{ pattern: /^-?\d+$/, message: 'Введите числовой Telegram ID' }]}
              >
                <Input placeholder="123456789" prefix={<MessageOutlined />} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={12}>
            <Col span={12}>
              <Form.Item label={<Space><DollarOutlined /> Зарплата</Space>} name="salary_config_id">
                <Select
                  placeholder="Выберите формулу"
                  allowClear
                  options={salaryConfigs.map((c: any) => ({
                    label: `${c.name} (${c.config_type === 'fixed' ? `${c.fixed_amount}₽/${c.period}` : c.formula_string})`,
                    value: c.id,
                  }))}
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="is_active" valuePropName="checked" initialValue={true}>
            <Checkbox>Активен</Checkbox>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="Telegram-привязка"
        open={telegramLinkOpen}
        onCancel={() => setTelegramLinkOpen(false)}
        footer={[
          <Button key="copy" type="primary" onClick={copyTelegramCommand}>Скопировать команду</Button>,
          <Button key="close" onClick={() => setTelegramLinkOpen(false)}>Закрыть</Button>,
        ]}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text>
            Отправьте эту команду сотруднику {telegramLink?.full_name || telegramLink?.username || ''}.
            Код действует 15 минут и привязывает Telegram только к выбранному сотруднику.
          </Text>
          <Input.TextArea value={telegramLink?.command || ''} readOnly autoSize />
          {telegramLink?.deep_link && (
            <Button href={telegramLink.deep_link} target="_blank">Открыть ссылку Telegram</Button>
          )}
        </Space>
      </Modal>
    </div>
  )
}

export default EmployeesTab
