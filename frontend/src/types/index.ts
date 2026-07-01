/**
 * TypeScript интерфейсы для всех данных API
 * Согласованы с SQLModel моделями бэкенда
 */

// === Заказ ===

export type OrderStatus = 'new' | 'diagnostics' | 'agreed' | 'repair' | 'waiting_parts' | 'ready' | 'ready_pickup' | 'issued' | 'issued_br' | 'cancelled'
export type ClientType = 'individual' | 'business'
export type DeviceType = 'phone' | 'laptop' | 'tv' | 'appliance' | 'tablet' | 'other'

export interface Order {
  id: number
  client_name: string
  client_phone: string
  client_type?: ClientType
  device_type?: DeviceType
  device_brand?: string
  device_model: string
  brand?: string
  serial_number?: string
  complaint: string
  accessories?: string[]       // Комплектация: ЗУ, Чехол, Коробка...
  exterior_condition?: string  // Внешний вид (царапины, вмятины)
  status: OrderStatus
  is_warranty?: boolean        // Гарантия
  master_id?: number
  master_username?: string
  acceptor_id?: number
  acceptor_username?: string
  created_at: string
  ready_at?: string
  issued_at?: string
  total_cost?: number
  parts_cost: number
  work_cost: number
  refunds_amount?: number      // Сумма возвратов
  diagnostic_act_text?: string
  warranty_days?: number
  warranty_until?: string
}

export interface OrderCreate {
  client_name: string
  client_phone: string
  client_type?: ClientType
  device_type?: DeviceType
  device_model: string
  brand?: string
  serial_number?: string
  complaint: string
  accessories?: string[]
  exterior_condition?: string
  master_id?: number
  ready_at?: string
}

export interface OrderStatusChange {
  status: OrderStatus
  comment?: string
}

export interface OrderListResponse {
  items: Order[]
  total: number
}

// === Пользователь ===

export interface User {
  id: number
  username: string
  role_id?: number
  role_name?: string
  telegram_chat_id?: number
  is_active: boolean
  created_at: string
  permissions: string[]
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

// === Запчасть ===

export interface Part {
  id: number
  name: string
  article: string
  quantity: number
  cost_price: number
  sale_price: number
  created_at: string
  updated_at: string
}

export interface PartMovement {
  type: 'income' | 'expense' | 'write_off'
  quantity: number
  order_id?: number
}

// === Клиент ===

export interface Client {
  name: string
  phone: string
  total_orders: number
  last_order_date?: string
}

export interface ClientDetail extends Client {
  orders: Array<{
    id: number
    device_model: string
    status: OrderStatus
    created_at: string
    total_cost?: number
  }>
}

// === Зарплата ===

export interface SalaryConfig {
  id: number
  formula_string: string
  description?: string
  is_active: boolean
  created_at: string
}

export interface SalaryRecord {
  id: number
  user_id: number
  username: string
  order_id?: number
  calculated_amount: number
  status: 'accrued' | 'paid' | 'advance'
  period_start: string
  period_end: string
  comment?: string
  created_at: string
}

export interface SalaryCalculationPreview {
  order_id: number
  total: number
  parts: number
  work: number
  warranty: number
  formula: string
  result: number
}

// === Уведомления ===

export interface NotificationTask {
  id: number
  order_id: number
  client_phone?: string
  chat_id?: number
  message_text: string
  send_at: string
  is_sent: boolean
  created_at: string
}

// === Настройки компании ===

export interface CompanySettings {
  id: number
  company_name: string
  inn?: string
  address?: string
  phone?: string
  email?: string
  logo_path?: string
  review_link?: string
  updated_at: string
}

// === Роли ===

export interface Role {
  id: number
  name: string
  description?: string
  permissions: string[]
}

// === Шаблоны документов ===

export interface DocumentTemplate {
  id: number
  type: 'receipt' | 'diagnostic_act' | 'work_act' | 'invoice'
  content_template: string
  updated_at: string
}

// === Дашборд ===

export interface DashboardData {
  period: { from: string; to: string }
  total_orders: number
  total_revenue: number
  total_salary_paid: number
  status_breakdown: Record<string, number>
  overdue_orders: number
  warranty_orders: number
  masters_efficiency: Array<{
    master_id: number
    master_name: string
    orders_completed: number
    revenue: number
  }>
  daily_orders?: Array<{ date: string; count: number }>
  daily_revenue?: Array<{ date: string; amount: number }>
}

// === Ошибки ===

export interface ApiError {
  detail: string
  errors?: Array<{
    field: string
    message: string
    type: string
  }>
}

// === Константы статусов ===

export const ORDER_STATUS_CONFIG: Record<OrderStatus, { label: string; color: string }> = {
  new: { label: 'Новый', color: 'blue' },
  diagnostics: { label: 'Диагностика', color: 'gold' },
  agreed: { label: 'Согласован', color: 'orange' },
  repair: { label: 'В ремонте', color: 'purple' },
  ready: { label: 'Готов', color: 'green' },
  issued: { label: 'Выдан', color: 'default' },
  cancelled: { label: 'Отменён', color: 'red' },
}

export const DEVICE_TYPES: { value: DeviceType; label: string }[] = [
  { value: 'phone', label: '📱 Телефон' },
  { value: 'laptop', label: '💻 Ноутбук' },
  { value: 'tv', label: '📺 Телевизор' },
  { value: 'appliance', label: '🔌 Бытовая техника' },
  { value: 'tablet', label: '📟 Планшет' },
  { value: 'other', label: '🔧 Другое' },
]

export const ACCESSORIES_LIST: string[] = [
  'Зарядное устройство (ЗУ)',
  'Чехол',
  'Коробка',
  'Документы',
  'Сим-карта',
  'Наушники',
  'Аккумулятор',
]
