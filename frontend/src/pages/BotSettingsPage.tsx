import React, { useEffect, useState } from 'react'
import {
  Alert,
  Button,
  Card,
  Col,
  Descriptions,
  Divider,
  Form,
  Input,
  List,
  Modal,
  Popconfirm,
  Row,
  Space,
  Statistic,
  Switch,
  Tag,
  Typography,
  message,
} from 'antd'
import {
  CheckCircleOutlined,
  DeleteOutlined,
  InfoCircleOutlined,
  RocketOutlined,
  SaveOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import api from '../api'

const { Text, Title } = Typography

const BotSettingsPage: React.FC = () => {
  const [form] = Form.useForm()
  const [webhookForm] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [settingsLoaded, setSettingsLoaded] = useState(false)
  const [stats, setStats] = useState<any>(null)
  const [webhookInfo, setWebhookInfo] = useState<any>(null)
  const [botInfo, setBotInfo] = useState<any>(null)
  const [showWebhookModal, setShowWebhookModal] = useState(false)
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  useEffect(() => {
    loadSettings()
  }, [])

  useEffect(() => {
    if (!settingsLoaded) return
    loadStats()
    loadBotInfo(false)
    checkWebhook(false)
  }, [settingsLoaded])

  const loadSettings = async () => {
    try {
      const res = await api.get('/bot/settings')
      const data = res.data
      form.setFieldsValue({
        bot_name: data.bot_name || '',
        bot_username: data.bot_username || '',
        admin_chat_id: data.admin_chat_id || '',
        webhook_url: data.webhook_url || '',
        webhook_domain: data.webhook_domain || '',
        notify_new_orders: data.notify_new_orders,
        notify_status_change: data.notify_status_change,
        notify_comments: data.notify_comments,
        notify_warranty: data.notify_warranty,
        is_active: data.is_active,
      })
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка загрузки настроек бота')
    } finally {
      setSettingsLoaded(true)
    }
  }

  const loadStats = async () => {
    try {
      const res = await api.get('/bot/stats')
      setStats(res.data)
    } catch {}
  }

  const checkWebhook = async (showMessage = true) => {
    try {
      const res = await api.get('/bot/webhook/info')
      setWebhookInfo(res.data)
      if (showMessage) message.success('Webhook проверен')
    } catch (error: any) {
      if (showMessage) message.error(error.response?.data?.detail || 'Ошибка проверки webhook')
    }
  }

  const loadBotInfo = async (showMessage = true) => {
    try {
      const res = await api.get('/bot/bot/info')
      setBotInfo(res.data)
      form.setFieldsValue({
        bot_username: res.data.username || form.getFieldValue('bot_username'),
        bot_name: res.data.first_name || form.getFieldValue('bot_name'),
      })
      if (showMessage) message.success(`Бот: @${res.data.username}`)
    } catch (error: any) {
      if (showMessage) message.error(error.response?.data?.detail || 'Ошибка проверки бота')
    }
  }

  const handleSave = async () => {
    setLoading(true)
    try {
      const values = await form.validateFields()
      await api.patch('/bot/settings', values)
      message.success('Настройки сохранены')
      loadSettings()
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка сохранения настроек')
    } finally {
      setLoading(false)
    }
  }

  const handleSetWebhook = async () => {
    const values = await webhookForm.validateFields()
    setActionLoading('webhook')
    try {
      await api.post('/bot/webhook/set', { webhook_url: values.webhook_url })
      message.success('Webhook установлен')
      setShowWebhookModal(false)
      checkWebhook(false)
      loadSettings()
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка установки webhook')
    } finally {
      setActionLoading(null)
    }
  }

  const handleDeleteWebhook = async () => {
    setActionLoading('delete')
    try {
      await api.post('/bot/webhook/delete')
      message.success('Webhook удален')
      setWebhookInfo(null)
      loadSettings()
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка удаления webhook')
    } finally {
      setActionLoading(null)
    }
  }

  const botCommands = [
    { command: '/start', description: 'Меню или привязка по коду из CRM' },
    { command: '/menu', description: 'Главное меню' },
    { command: '/orders', description: 'Активные заказы или мои заказы мастера' },
    { command: '/ping', description: 'Проверка связи' },
  ]

  return (
    <div>
      <Title level={3}><SettingOutlined /> Настройки Telegram бота</Title>

      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
        message="Бот работает в polling-режиме"
        description="Токен хранится на сервере в .env и не вводится в браузере. Для привязки сотрудников используйте кнопку TG во вкладке Сотрудники."
      />

      <Row gutter={[16, 16]}>
        <Col xs={24} md={16}>
          <Card title="Основные настройки">
            <Form form={form} layout="vertical">
              <Row gutter={12}>
                <Col xs={24} md={12}>
                  <Form.Item name="bot_name" label="Имя бота">
                    <Input placeholder="OnServis" />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item name="bot_username" label="Username бота">
                    <Input prefix="@" placeholder="OnServis_telegram_bot" />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={12}>
                <Col xs={24} md={12}>
                  <Form.Item name="admin_chat_id" label="Chat ID администратора">
                    <Input type="number" placeholder="123456789" />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item name="webhook_domain" label="Домен webhook" tooltip="Не нужен для polling, можно оставить пустым">
                    <Input placeholder="example.com" />
                  </Form.Item>
                </Col>
              </Row>

              <Divider />

              <Title level={5}>Уведомления</Title>
              <Row gutter={12}>
                <Col xs={24} md={12}>
                  <Form.Item name="notify_new_orders" label="Новые заказы" valuePropName="checked">
                    <Switch />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item name="notify_status_change" label="Смена статусов" valuePropName="checked">
                    <Switch />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item name="notify_comments" label="Комментарии" valuePropName="checked">
                    <Switch />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item name="notify_warranty" label="Гарантия" valuePropName="checked">
                    <Switch />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item name="is_active" label="Бот активен" valuePropName="checked">
                <Switch />
              </Form.Item>
            </Form>

            <Space wrap>
              <Button type="primary" icon={<SaveOutlined />} onClick={handleSave} loading={loading}>
                Сохранить настройки
              </Button>
              <Button icon={<InfoCircleOutlined />} onClick={() => loadBotInfo()}>
                Проверить бота
              </Button>
            </Space>
          </Card>
        </Col>

        <Col xs={24} md={8}>
          <Card title="Статистика" size="small" style={{ marginBottom: 16 }}>
            <Row gutter={[8, 8]}>
              <Col span={12}><Statistic title="Подключено" value={stats?.connected_users || 0} prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />} /></Col>
              <Col span={12}><Statistic title="Сотрудников" value={stats?.total_users || 0} /></Col>
              <Col span={12}><Statistic title="Заказов сегодня" value={stats?.orders_today || 0} /></Col>
              <Col span={12}><Statistic title="Готово" value={stats?.ready_orders || 0} prefix={<RocketOutlined style={{ color: '#1890ff' }} />} /></Col>
            </Row>
            <Button style={{ marginTop: 12 }} onClick={loadStats}>Обновить</Button>
          </Card>

          <Card title="Webhook" size="small">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Text>
                Статус: {webhookInfo?.url ? <Tag color="orange">Установлен</Tag> : <Tag color="green">Не установлен</Tag>}
              </Text>
              {webhookInfo?.url && <Text copyable>{webhookInfo.url}</Text>}
              {webhookInfo?.last_error_message && <Alert type="error" message={webhookInfo.last_error_message} />}
              <Space wrap>
                <Button onClick={() => checkWebhook()}>Проверить</Button>
                <Button onClick={() => setShowWebhookModal(true)}>Установить</Button>
                {webhookInfo?.url && (
                  <Popconfirm title="Удалить webhook?" onConfirm={handleDeleteWebhook}>
                    <Button danger icon={<DeleteOutlined />} loading={actionLoading === 'delete'}>Удалить</Button>
                  </Popconfirm>
                )}
              </Space>
            </Space>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} md={12}>
          <Card title="Команды бота" size="small">
            <List
              dataSource={botCommands}
              renderItem={(item) => (
                <List.Item>
                  <List.Item.Meta title={<Text code>{item.command}</Text>} description={item.description} />
                </List.Item>
              )}
            />
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card title="Информация о боте" size="small">
            {botInfo ? (
              <Descriptions column={1} size="small">
                <Descriptions.Item label="ID">{botInfo.id}</Descriptions.Item>
                <Descriptions.Item label="Username">@{botInfo.username}</Descriptions.Item>
                <Descriptions.Item label="Имя">{botInfo.first_name}</Descriptions.Item>
                <Descriptions.Item label="Группы">{botInfo.can_join_groups ? 'Да' : 'Нет'}</Descriptions.Item>
              </Descriptions>
            ) : (
              <Text type="secondary">Нажмите Проверить бота</Text>
            )}
          </Card>
        </Col>
      </Row>

      <Modal
        title="Установить webhook"
        open={showWebhookModal}
        onOk={handleSetWebhook}
        onCancel={() => setShowWebhookModal(false)}
        confirmLoading={actionLoading === 'webhook'}
      >
        <Alert
          type="warning"
          showIcon
          style={{ marginBottom: 12 }}
          message="Обычно webhook не нужен"
          description="Сейчас бот работает через polling. Установка webhook может остановить получение сообщений polling-ботом."
        />
        <Form form={webhookForm} layout="vertical">
          <Form.Item name="webhook_url" label="Webhook URL" rules={[{ required: true, message: 'Введите URL' }]}>
            <Input placeholder="https://your-domain.com/api/telegram/webhook" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default BotSettingsPage
