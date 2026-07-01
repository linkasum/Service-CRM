import React, { useState } from 'react'
import { Avatar, Button, Card, Col, Descriptions, Form, Input, message, Row, Space, Tag, Typography } from 'antd'
import { DollarOutlined, IdcardOutlined, LockOutlined, MessageOutlined, SaveOutlined, UserOutlined } from '@ant-design/icons'
import { useAuth } from '../contexts/AuthContext'

import { changePassword } from '../api'

const { Text, Title } = Typography

const ProfilePage: React.FC = () => {
  const { user } = useAuth()
  const [loading, setLoading] = useState(false)
  const [form] = Form.useForm()

  const handleChangePassword = async (values: { 
    current_password: string
    new_password: string
    confirm_password: string
  }) => {
    if (values.new_password !== values.confirm_password) {
      message.error('Пароли не совпадают')
      return
    }
    if (values.new_password.length < 6) {
      message.error('Минимум 6 символов')
      return
    }

    setLoading(true)
    try {
      await changePassword({
        current_password: values.current_password,
        new_password: values.new_password,
      })
      message.success('Пароль успешно изменён')
      form.resetFields()
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка смены пароля')
    } finally {
      setLoading(false)
    }
  }

  const handleLinkTelegram = async () => {
    const authCode = user?.username || ''
    message.info(
      `Откройте Telegram, найдите бота @${'ONServisbot'} и отправьте: /start ${authCode}`,
      8000
    )
  }

  if (!user) return null

  const displayName = user.full_name || user.username
  const initials = displayName[0]?.toUpperCase() || 'U'
  const roleColors: Record<string, string> = {
    admin: 'red',
    manager: 'blue',
    master: 'green',
    acceptor: 'orange',
  }
  const roleLabels: Record<string, string> = {
    admin: 'Администратор',
    manager: 'Менеджер',
    master: 'Мастер',
    acceptor: 'Приёмщик',
  }
  const roleName = user.role_name || 'Не назначена'
  const roleColor = roleColors[roleName] || 'default'
  const salaryText = user.salary_config_type === 'fixed'
    ? `${user.salary_fixed_amount ?? 0} ₽ / ${user.salary_period || '—'}`
    : user.salary_formula || 'Не назначена'
  const createdAt = user.created_at
    ? new Date(user.created_at).toLocaleString('ru-RU')
    : '—'

  return (
    <div style={{ width: '100%' }}>
      <Title level={3} style={{ marginBottom: 16 }}>Профиль</Title>

      <Card style={{ marginBottom: 16 }}>
        <Space size={16} align="center">
          <Avatar size={64} icon={<UserOutlined />} style={{ background: '#1677ff' }}>
            {initials}
          </Avatar>
          <div>
            <Title level={4} style={{ margin: 0 }}>{displayName}</Title>
            <Space wrap style={{ marginTop: 8 }}>
              <Tag color={roleColor}>{roleLabels[roleName] || roleName}</Tag>
              <Tag color={user.is_active ? 'green' : 'default'}>
                {user.is_active ? 'Активен' : 'Не активен'}
              </Tag>
              {user.telegram_chat_id ? <Tag color="cyan">Telegram ID: {user.telegram_chat_id}</Tag> : <Tag>Telegram не привязан</Tag>}
            </Space>
          </div>
        </Space>
      </Card>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={14}>
          <Card title={<Space><IdcardOutlined /> Данные сотрудника</Space>} style={{ height: '100%' }}>
            <Descriptions column={1} size="small" bordered>
              <Descriptions.Item label="ID">{user.id}</Descriptions.Item>
              <Descriptions.Item label="Логин">{user.username}</Descriptions.Item>
              <Descriptions.Item label="Имя">{user.full_name || '—'}</Descriptions.Item>
              <Descriptions.Item label="Email">{user.email || '—'}</Descriptions.Item>
              <Descriptions.Item label="Телефон">{user.phone || '—'}</Descriptions.Item>
              <Descriptions.Item label="Роль">
                <Space>
                  <Tag color={roleColor}>{roleLabels[roleName] || roleName}</Tag>
                  {user.role_id ? <Text type="secondary">ID {user.role_id}</Text> : null}
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="Статус">
                <Tag color={user.is_active ? 'green' : 'default'}>
                  {user.is_active ? 'Активен' : 'Не активен'}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Создан">{createdAt}</Descriptions.Item>
            </Descriptions>
          </Card>
        </Col>

        <Col xs={24} lg={10}>
          <Space direction="vertical" size={16} style={{ width: '100%' }}>
            <Card title={<Space><MessageOutlined /> Telegram</Space>}>
              <Descriptions column={1} size="small">
                <Descriptions.Item label="Telegram ID">
                  {user.telegram_chat_id ? <Tag color="cyan">{user.telegram_chat_id}</Tag> : '—'}
                </Descriptions.Item>
                <Descriptions.Item label="Команда для бота">
                  <Text code>/start {user.username}</Text>
                </Descriptions.Item>
              </Descriptions>
              <Button
                icon={<MessageOutlined />}
                type={user.telegram_chat_id ? 'default' : 'primary'}
                onClick={handleLinkTelegram}
              >
                {user.telegram_chat_id ? 'Перепривязать Telegram' : 'Привязать Telegram'}
              </Button>
            </Card>

            <Card title={<Space><DollarOutlined /> Зарплата</Space>}>
              <Descriptions column={1} size="small">
                <Descriptions.Item label="Формула ID">{user.salary_config_id || '—'}</Descriptions.Item>
                <Descriptions.Item label="Название">{user.salary_config_name || '—'}</Descriptions.Item>
                <Descriptions.Item label="Тип">{user.salary_config_type || '—'}</Descriptions.Item>
                <Descriptions.Item label="Расчёт">{salaryText}</Descriptions.Item>
              </Descriptions>
            </Card>
          </Space>
        </Col>
      </Row>

      <Card title="Смена пароля" style={{ marginTop: 16 }}>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleChangePassword}
          style={{ maxWidth: 400 }}
        >
          <Form.Item
            name="current_password"
            label="Текущий пароль"
            rules={[{ required: true, message: 'Введите текущий пароль' }]}
          >
            <Input.Password prefix={<LockOutlined />} />
          </Form.Item>
          <Form.Item
            name="new_password"
            label="Новый пароль"
            rules={[
              { required: true, message: 'Введите новый пароль' },
              { min: 6, message: 'Минимум 6 символов' },
            ]}
          >
            <Input.Password prefix={<LockOutlined />} />
          </Form.Item>
          <Form.Item
            name="confirm_password"
            label="Подтверждение пароля"
            rules={[{ required: true, message: 'Подтвердите пароль' }]}
          >
            <Input.Password prefix={<LockOutlined />} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={loading}>
              Сменить пароль
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}

export default ProfilePage
