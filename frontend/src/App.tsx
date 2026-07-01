import React, { useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu, Typography, ConfigProvider, Switch, Drawer, Button, Result } from 'antd'
import {
  DashboardOutlined,
  OrderedListOutlined,
  ToolOutlined,
  TeamOutlined,
  DollarOutlined,
  SettingOutlined,
  BarChartOutlined,
  ImportOutlined,
  UserOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  MoonOutlined,
  SunOutlined,
  FileTextOutlined,
  CalendarOutlined,
} from '@ant-design/icons'

import { AuthProvider, useAuth } from './contexts/AuthContext'
import { ThemeProvider, useTheme } from './contexts/ThemeContext'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import OrdersPage from './pages/OrdersPage'
import OrderCreatePage from './pages/OrderCreatePage'
import OrderDetailPage from './pages/OrderDetailPage'
import PartsPage from './pages/PartsPage'
import ClientsPage from './pages/ClientsPage'
import SettingsPage from './pages/SettingsPage'
import ProfilePage from './pages/ProfilePage'
import ReportsPage from './pages/ReportsPage'
import ImportPage from './pages/ImportPage'
import ServicesPage from './pages/ServicesPage'
import DocumentsPage from './pages/DocumentsPage'
import { useWebSocket } from './hooks/useWebSocket'
import NotifyBell from './components/NotifyBell'
import GlobalSearch from './components/GlobalSearch'
import CashPage from './pages/CashPage'
import SalaryReportPage from './pages/SalaryReportPage'
import SchedulePage from './pages/SchedulePage'

const { Header, Sider, Content } = Layout
const { Title } = Typography

const ProtectedRoute: React.FC<{ children: React.ReactNode; permission?: string }> = ({ children, permission }) => {
  const { hasPermission, user } = useAuth()
  if (permission && !hasPermission(permission)) {
    return <div style={{ padding: 24, textAlign: 'center' }}>
      <Result status="403" title="Нет доступа" subTitle={`Требуется право: ${permission}`} />
    </div>
  }
  return <>{children}</>
}
const AppLayout: React.FC = () => {
  const { user, logout, hasPermission } = useAuth()
  const { mode, toggle, config } = useTheme()
  const [collapsed, setCollapsed] = useState(false)
  const [mobileDrawer, setMobileDrawer] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const isMobile = window.innerWidth < 768

  if (!user) return <LoginPage />

  const canView = (perm: string) => hasPermission(perm)
  useWebSocket({ onMessage: (msg: any) => { try { window.dispatchEvent(new CustomEvent("crm-notify", { detail: msg })) } catch {} } })


  const menuItems = [
    { key: '/dashboard', icon: <DashboardOutlined />, label: 'Дашборд' },
    { key: '/cash', icon: <DollarOutlined />, label: 'Касса', hidden: !canView('cash:view') },
    { key: '/schedule', icon: <CalendarOutlined />, label: 'График работы', hidden: !canView('dashboard:view') },
    { key: '/orders', icon: <OrderedListOutlined />, label: 'Заказы' },
    { key: '/documents', icon: <FileTextOutlined />, label: 'Документы', hidden: !canView('orders:view') },
    { key: '/parts', icon: <ToolOutlined />, label: 'Склад', hidden: !canView('parts:view') },
    { key: '/clients', icon: <TeamOutlined />, label: 'Клиенты' },
    { key: '/reports', icon: <BarChartOutlined />, label: 'Отчёты', hidden: !canView('settings.manage') },
    { key: '/import', icon: <ImportOutlined />, label: 'Импорт', hidden: true },
    { key: '/services', icon: <ToolOutlined />, label: 'Услуги', hidden: !canView('services:view') },
    { key: '/settings', icon: <SettingOutlined />, label: 'Настройки', hidden: !canView('role.manage') && !canView('settings.manage') },
    { key: '/profile', icon: <UserOutlined />, label: 'Профиль' },
  ].filter(item => !item.hidden)

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key)
    setMobileDrawer(false)
  }

  const menuContent = (
    <Menu
      theme={mode === 'dark' ? 'dark' : 'light'}
      mode="inline"
      selectedKeys={[location.pathname.startsWith('/orders/') ? '/orders' : location.pathname]}
      items={menuItems}
      onClick={handleMenuClick}
    />
  )

  return (
    <ConfigProvider theme={config}>
      <Layout style={{ minHeight: '100vh', width: '100%' }}>
        {isMobile ? (
          <>
            <Header style={{ padding: '0 16px', display: 'flex', alignItems: 'center', gap: 12, zIndex: 100 }}>
              <Button type="text" icon={<MenuUnfoldOutlined />} onClick={() => setMobileDrawer(true)} />
              <Title level={4} style={{ color: mode === 'dark' ? '#fff' : '#fff', margin: 0 }}>CRM</Title>
              <div style={{ flex: 1 }} />
              <Switch
                checkedChildren={<MoonOutlined />}
                unCheckedChildren={<SunOutlined />}
                checked={mode === 'dark'}
                onChange={toggle}
                size="small"
              />
            </Header>
            <Drawer
              title="Меню"
              placement="left"
              onClose={() => setMobileDrawer(false)}
              open={mobileDrawer}
              width={250}
            >
              {menuContent}
            </Drawer>
          </>
        ) : (
          <>
            <Sider trigger={null} collapsible collapsed={collapsed} theme={mode === 'dark' ? 'dark' : 'light'}>
              <div style={{ padding: '16px', textAlign: 'center' }}>
                <Title level={4} style={{ color: mode === 'dark' ? '#fff' : '#1a1a1a', margin: 0 }}>
                  {collapsed ? 'CRM' : 'CRM Сервис'}
                </Title>
              </div>
              {menuContent}
            </Sider>
          </>
        )}
        <Layout>
          {!isMobile && (
            <Header style={{ 
              padding: '0 16px', 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center',
              background: mode === 'dark' ? '#1a1a2e' : '#fff',
              borderBottom: mode === 'dark' ? '1px solid #2a2a4a' : '1px solid #e8e8e8',
            }}>
              {React.createElement(collapsed ? MenuUnfoldOutlined : MenuFoldOutlined, {
                onClick: () => setCollapsed(!collapsed),
                style: { fontSize: '18px', cursor: 'pointer', color: mode === 'dark' ? '#e8e8e8' : '#333' },
              })}
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flex: 1, marginLeft: 24 }}>
            <NotifyBell /><GlobalSearch />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <Switch
                  checkedChildren={<MoonOutlined />}
                  unCheckedChildren={<SunOutlined />}
                  checked={mode === 'dark'}
                  onChange={toggle}
                  style={{ background: mode === 'dark' ? '#16213e' : '#d9d9d9' }}
                />
                <span style={{ cursor: 'pointer', color: mode === 'dark' ? '#e8e8e8' : '#333' }} onClick={() => navigate('/profile')}>
                  {user.username} ({user.role_name})
                </span>
                <LogoutOutlined onClick={logout} style={{ cursor: 'pointer', fontSize: '18px', color: mode === 'dark' ? '#e8e8e8' : '#333' }} title="Выйти" />
              </div>
            </Header>
          )}
          <Content style={{ margin: isMobile ? '8px' : '16px', padding: isMobile ? '8px' : '16px', minHeight: 280 }}>
            <Routes>
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/orders" element={<ProtectedRoute permission="orders:view"><OrdersPage /></ProtectedRoute>} />
              <Route path="/orders/create" element={<ProtectedRoute permission="orders:create"><OrderCreatePage /></ProtectedRoute>} />
              <Route path="/orders/:id" element={<ProtectedRoute permission="orders:view"><OrderDetailPage /></ProtectedRoute>} />
              <Route path="/documents" element={<ProtectedRoute permission="orders:view"><DocumentsPage /></ProtectedRoute>} />
              <Route path="/parts" element={<ProtectedRoute permission="parts:view"><PartsPage /></ProtectedRoute>} />
              <Route path="/clients" element={<ClientsPage />} />
              <Route path="/reports" element={<ProtectedRoute permission="settings.manage"><ReportsPage /></ProtectedRoute>} />
              <Route path="/import" element={<ProtectedRoute permission="settings.manage"><ImportPage /></ProtectedRoute>} />
              <Route path="/services" element={<ProtectedRoute permission="services:view"><ServicesPage /></ProtectedRoute>} />
              <Route path="/cash" element={<ProtectedRoute permission="cash:view"><CashPage /></ProtectedRoute>} />
              <Route path="/schedule" element={<SchedulePage />} />
              <Route path="/salary-report" element={<ProtectedRoute permission="settings.manage"><SalaryReportPage /></ProtectedRoute>} />
              <Route path="/settings" element={<ProtectedRoute permission="settings.manage"><SettingsPage /></ProtectedRoute>} />
              <Route path="/profile" element={<ProfilePage />} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </Content>
        </Layout>
      </Layout>
    </ConfigProvider>
  )
}

const AppContent: React.FC = () => {
  const { isAuthenticated } = useAuth()
  if (!isAuthenticated) return <LoginPage />
  return <AppLayout />
}

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <AppContent />
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  )
}

export default App
