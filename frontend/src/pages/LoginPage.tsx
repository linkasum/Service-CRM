import React, { useState } from 'react'
import { Form, Input, Button, Card, Typography, Alert, ConfigProvider, theme } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { useAuth } from '../contexts/AuthContext'
import { useTheme } from '../contexts/ThemeContext'

const { Title, Text } = Typography

const LoginPage: React.FC = () => {
  const { login } = useAuth()
  const { mode, config } = useTheme()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true)
    setError(null)
    try {
      await login(values.username, values.password)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Неверное имя пользователя или пароль')
    } finally {
      setLoading(false)
    }
  }

  return (
    <ConfigProvider theme={config}>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: '100vh',
        background: mode === 'dark' 
          ? 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)'
          : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      }}>
        <Card 
          style={{ width: 400, maxWidth: '90vw', boxShadow: mode === 'dark' ? '0 8px 32px rgba(0,0,0,0.4)' : '0 8px 32px rgba(0,0,0,0.1)' }}
        >
          <div style={{ textAlign: 'center', marginBottom: 32 }}>
            <Title level={2}>🔧 CRM Сервис</Title>
            <Text type="secondary">Сервисный центр</Text>
          </div>

          {error && (
            <Alert message={error} type="error" showIcon style={{ marginBottom: 16 }} />
          )}

          <Form name="login" onFinish={onFinish} size="large" autoComplete="off">
            <Form.Item name="username" rules={[{ required: true, message: 'Введите имя пользователя' }]}>
              <Input prefix={<UserOutlined />} placeholder="Имя пользователя" autoFocus />
            </Form.Item>
            <Form.Item name="password" rules={[{ required: true, message: 'Введите пароль' }]}>
              <Input.Password prefix={<LockOutlined />} placeholder="Пароль" />
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit" loading={loading} block>
                Войти
              </Button>
            </Form.Item>
          </Form>
          <Text type="secondary" style={{ fontSize: 12 }}>
            По умолчанию: admin / admin
          </Text>
        </Card>
      </div>
    </ConfigProvider>
  )
}

export default LoginPage
