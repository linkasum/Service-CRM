/**
 * API клиент для взаимодействия с бэкендом
 */
import axios from 'axios'
import { config } from '../config'

const api = axios.create({
  baseURL: config.API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

let isRefreshing = false
let failedQueue: Array<{ resolve: (value: any) => void; reject: (error: any) => void }> = []

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(prom => {
    if (error) prom.reject(error)
    else prom.resolve(token)
  })
  failedQueue = []
}

// Перехватчик для добавления JWT токена
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Перехватчик для обработки 401 — автоматический refresh токена
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // Если уже пытались refresh — не пробуем снова
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // Ждём пока токен обновится
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then(token => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          return api(originalRequest)
        }).catch(err => Promise.reject(err))
      }

      const refreshToken = localStorage.getItem('refresh_token')
      if (!refreshToken) {
        // Нет refresh token — редирект на логин
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        window.location.href = '/login'
        return Promise.reject(error)
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const response = await axios.post(`${config.API_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        })
        const { access_token } = response.data

        localStorage.setItem('token', access_token)
        processQueue(null, access_token)

        originalRequest.headers.Authorization = `Bearer ${access_token}`
        return api(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError, null)
        localStorage.removeItem('token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    // 403 — нет прав
    if (error.response?.status === 403) {
      const detail = error.response?.data?.detail || 'Нет прав доступа к этому действию'
      if (!error._handled) {
        import('antd').then(({ message }) => message.error(detail))
      }
    }

    return Promise.reject(error)
  }
)

// === Auth ===

export const login = async (username: string, password: string) => {
  const response = await api.post('/auth/login', { username, password })
  return response.data
}

export const getMe = async () => {
  const response = await api.get('/auth/me')
  return response.data
}

export const changePassword = async (data: { current_password: string; new_password: string }) => {
  const response = await api.post('/auth/change-password', data)
  return response.data
}

// === Orders ===

export const getOrders = async (params: Record<string, any> = {}) => {
  const response = await api.get('/orders/', { params })
  return response.data
}

export const getOrder = async (id: number) => {
  const response = await api.get(`/orders/${id}`)
  return response.data
}

export const createOrder = async (data: Record<string, any>) => {
  const response = await api.post('/orders/', data)
  return response.data
}

export const updateOrder = async (id: number, data: Record<string, any>) => {
  const response = await api.patch(`/orders/${id}`, data)
  return response.data
}

export const changeOrderStatus = async (id: number, status: string, comment?: string, payment_method?: string) => {
  const body: any = { status, comment }
  if (payment_method) body.payment_method = payment_method
  const response = await api.patch(`/orders/${id}/status`, body)
  return response.data
}

export const deleteOrder = async (id: number) => {
  const response = await api.delete(`/orders/${id}`)
  return response.data
}

// === Parts ===

export const getParts = async (params: Record<string, any> = {}) => {
  const response = await api.get('/parts/', { params })
  return response.data
}

export const createPart = async (data: Record<string, any>) => {
  const response = await api.post('/parts/', data)
  return response.data
}

export const updatePart = async (id: number, data: Record<string, any>) => {
  const response = await api.patch(`/parts/${id}`, data)
  return response.data
}

export const partMovement = async (id: number, type: string, quantity: number, order_id?: number, master_id?: number) => {
  const response = await api.post(`/parts/${id}/movement`, { type, quantity, order_id, master_id })
  return response.data
}

export const deletePart = async (id: number) => {
  const response = await api.delete(`/parts/${id}`)
  return response.data
}

// === Clients ===

export const getClients = async (params: Record<string, any> = {}) => {
  const response = await api.get('/clients/', { params })
  return response.data
}

export const getClient = async (phone: string) => {
  const response = await api.get(`/clients/${phone}`)
  return response.data
}

export const searchClientByPhone = async (phone: string) => {
  const response = await api.get('/clients/search/by-phone', { params: { phone } })
  return response.data
}

export const getClientInfo = async (phone: string) => {
  const response = await api.get(`/clients/${phone}/info`)
  return response.data
}

// === Reports ===

export const getDashboard = async (dateFrom?: string, dateTo?: string) => {
  const params: Record<string, string> = {}
  if (dateFrom) params.date_from = dateFrom
  if (dateTo) params.date_to = dateTo
  const response = await api.get('/reports/dashboard', { params })
  return response.data
}

export const getSalarySummary = async (periodStart?: string, periodEnd?: string) => {
  const params: Record<string, string> = {}
  if (periodStart) params.period_start = periodStart
  if (periodEnd) params.period_end = periodEnd
  const response = await api.get('/reports/salary-summary', { params })
  return response.data
}

// === Salary ===

export const getSalaryConfigs = async () => {
  const response = await api.get('/salary/config')
  return response.data
}

export const createSalaryConfig = async (data: Record<string, any>) => {
  const response = await api.post('/salary/config', data)
  return response.data
}

export const activateSalaryConfig = async (id: number) => {
  const response = await api.post(`/salary/config/${id}/activate`)
  return response.data
}

export const calculateSalaryPreview = async (orderId: number) => {
  const response = await api.get(`/salary/calculate/${orderId}`)
  return response.data
}

export const getSalaryRecords = async (params: Record<string, any> = {}) => {
  const response = await api.get('/salary/records', { params })
  return response.data
}

export const createSalaryPeriod = async (data: Record<string, any>) => {
  const response = await api.post('/salary/records', data)
  return response.data
}

export const updateSalaryRecord = async (id: number, status: string) => {
  const response = await api.patch(`/salary/records/${id}`, null, { params: { status } })
  return response.data
}

// === Бренды и категории ===

export const getBrands = async () => {
  const response = await api.get('/settings/brands')
  return response.data
}

export const createBrand = async (name: string) => {
  const response = await api.post('/settings/brands', { name })
  return response.data
}

export const getCategories = async () => {
  const response = await api.get('/settings/categories')
  return response.data
}

export const createCategory = async (name: string) => {
  const response = await api.post('/settings/categories', { name })
  return response.data
}

// === Модели устройств ===

export const getDeviceModels = async (params: { brand_id?: number; search?: string } = {}) => {
  const response = await api.get('/models/', { params })
  return response.data
}

export const getDeviceModel = async (id: number) => {
  const response = await api.get(`/models/${id}`)
  return response.data
}

export const createDeviceModel = async (data: { name: string; brand_id?: number; category?: string }) => {
  const response = await api.post('/models/', data)
  return response.data
}

export const updateDeviceModel = async (id: number, data: { name?: string; brand_id?: number; is_active?: boolean; category?: string }) => {
  const response = await api.patch(`/models/${id}`, data)
  return response.data
}

export const deleteDeviceModel = async (id: number) => {
  const response = await api.delete(`/models/${id}`)
  return response.data
}

// === Комплектации ===

export const getAccessoryTemplates = async (search?: string) => {
  const response = await api.get('/settings/accessory-templates', { params: { search } })
  return response.data
}

export const createAccessoryTemplate = async (data: { name: string }) => {
  const response = await api.post('/settings/accessory-templates', data)
  return response.data
}

export const deleteAccessoryTemplate = async (id: number) => {
  const response = await api.delete(`/settings/accessory-templates/${id}`)
  return response.data
}

export const getUser = async (id: number) => {
  const response = await api.get(`/users/${id}`)
  return response.data
}

export const getRoles = async () => {
  const response = await api.get('/settings/roles')
  return response.data
}

// === Settings ===

export const createRole = async (data: Record<string, any>) => {
  const response = await api.post('/settings/roles', data)
  return response.data
}

export const updateRole = async (id: number, data: Record<string, any>) => {
  const response = await api.patch(`/settings/roles/${id}`, data)
  return response.data
}

export const deleteRole = async (id: number) => {
  const response = await api.delete(`/settings/roles/${id}`)
  return response.data
}

export const getCompanySettings = async () => {
  const response = await api.get('/settings/company')
  return response.data
}

export const updateCompanySettings = async (data: Record<string, any>) => {
  const response = await api.patch('/settings/company', data)
  return response.data
}

export const getOrderNumbering = async () => {
  const response = await api.get('/settings/order-numbering')
  return response.data
}

export const updateOrderNumbering = async (nextOrderNumber: number) => {
  const response = await api.patch('/settings/order-numbering', {
    next_order_number: nextOrderNumber,
  })
  return response.data
}

export const getTemplates = async () => {
  const response = await api.get('/settings/templates')
  return response.data
}

export const getTemplate = async (type: string) => {
  const response = await api.get(`/settings/templates/${type}`)
  return response.data
}

export const updateTemplate = async (type: string, data: Record<string, any>) => {
  const response = await api.patch(`/settings/templates/${type}`, data)
  return response.data
}

// === Статусы заказов ===

export const getOrderStatuses = async () => {
  const response = await api.get('/settings/statuses')
  return response.data
}

export const createOrderStatus = async (data: { name: string; color: string; is_default?: boolean; is_active?: boolean }) => {
  const response = await api.post('/settings/statuses', data)
  return response.data
}

export const updateOrderStatus = async (id: number, data: { name?: string; color?: string; is_default?: boolean; is_active?: boolean }) => {
  const response = await api.patch(`/settings/statuses/${id}`, data)
  return response.data
}

export const deleteOrderStatus = async (id: number) => {
  const response = await api.delete(`/settings/statuses/${id}`)
  return response.data
}

// === Зарплата: начисление ===

export const recalculateOrderSalary = async (orderId: number) => {
  const response = await api.post(`/salary/assignment/recalculate/${orderId}`)
  return response.data
}

// === Зарплата: отчёты ===

export const getEmployeesSalaryReport = async (dateFrom?: string, dateTo?: string) => {
  const params = new URLSearchParams()
  if (dateFrom) params.append('date_from', dateFrom)
  if (dateTo) params.append('date_to', dateTo)
  const response = await api.get(`/salary/records/employees?${params.toString()}`)
  return response.data
}

export const getEmployeeSalaryDetail = async (userId: number, dateFrom?: string, dateTo?: string) => {
  const params = new URLSearchParams()
  if (dateFrom) params.append('date_from', dateFrom)
  if (dateTo) params.append('date_to', dateTo)
  const response = await api.get(`/salary/records/employees/${userId}?${params.toString()}`)
  return response.data
}

export const paySalary = async (userId: number, amount: number, comment?: string) => {
  const response = await api.post(`/salary/records/${userId}/pay`, null, {
    params: { amount, comment }
  })
  return response.data
}

export const createTemplate = async (data: Record<string, any>) => {
  const response = await api.post('/settings/templates', data)
  return response.data
}

// === Template Assignments ===

export const getTemplateAssignments = async () => {
  const response = await api.get('/settings/template-assignments')
  return response.data
}

export const assignTemplate = async (documentType: string, templateId: number) => {
  const response = await api.post('/settings/template-assignments', {
    document_type: documentType,
    template_id: templateId
  })
  return response.data
}

// === Documents ===

export const generateReceipt = async (orderId: number) => {
  const response = await api.post(`/documents/from-template/${orderId}/receipt`)
  return response.data
}

export const generateDiagnosticAct = async (orderId: number) => {
  const response = await api.post(`/documents/from-template/${orderId}/diagnostic_act`)
  return response.data
}

export const generateWorkAct = async (orderId: number) => {
  const response = await api.post(`/documents/from-template/${orderId}/work_act`)
  return response.data
}

export const generateInvoice = async (orderId: number) => {
  const response = await api.post(`/documents/from-template/${orderId}/invoice`)
  return response.data
}

/**
 * Открыть документ для печати в браузере (новая вкладка)
 */
export const printDocument = async (orderId: number, templateType: string) => {
  const token = localStorage.getItem('token')
  const url = `/api/documents/print/${orderId}/${templateType}`
  
  window.open(url, '_blank', 'noopener,noreferrer')
}

/**
 * Скачать PDF документ — открывает в новой вкладке
 */
export const downloadDocument = async (filename: string) => {
  const token = localStorage.getItem('token')
  const url = `/api/documents/download?filename=${encodeURIComponent(filename)}`
  
  try {
    const response = await fetch(url, {
      headers: { Authorization: `Bearer ${token || ''}` },
    })
    if (!response.ok) throw new Error('Ошибка скачивания')
    const blob = await response.blob()
    const blobUrl = URL.createObjectURL(blob)
    window.open(blobUrl, '_blank')
    setTimeout(() => URL.revokeObjectURL(blobUrl), 1000)
  } catch (error) {
    // Fallback: открыть напрямую
    window.open(url, '_blank')
  }
}

/**
 * Предпросмотр PDF документа — открывает в новой вкладке без скачивания
 */
export const previewDocument = async (filename: string) => {
  const token = localStorage.getItem('token')
  const url = `/api/documents/download?filename=${encodeURIComponent(filename)}`
  
  try {
    const response = await fetch(url, {
      headers: { Authorization: `Bearer ${token || ''}` },
    })
    if (!response.ok) throw new Error('Ошибка предпросмотра')
    const blob = await response.blob()
    const blobUrl = URL.createObjectURL(blob)
    window.open(blobUrl, '_blank')
    setTimeout(() => URL.revokeObjectURL(blobUrl), 1000)
  } catch (error) {
    // Fallback: открыть напрямую
    window.open(url, '_blank')
  }
}

/**
 * Получить список документов заказа
 */
export const listOrderDocuments = async (orderId: number) => {
  const response = await api.get(`/documents/list/${orderId}`)
  return response.data
}

export default api

// === Users (Сотрудники) ===

export const getUsers = async (params: Record<string, any> = {}) => {
  const response = await api.get('/users/', { params })
  return response.data
}

export const createUser = async (data: Record<string, any>) => {
  const response = await api.post('/users/', data)
  return response.data
}

export const updateUser = async (id: number, data: Record<string, any>) => {
  const response = await api.patch(`/users/${id}`, data)
  return response.data
}

export const deactivateUser = async (id: number) => {
  const response = await api.delete(`/users/${id}`)
  return response.data
}

export const hardDeleteUser = async (id: number) => {
  const response = await api.delete(`/users/${id}/hard`)
  return response.data
}

export const resetUserPassword = async (id: number) => {
  const response = await api.post(`/users/${id}/reset-password`)
  return response.data
}

// === Permissions ===

export const getPermissionGroups = async () => {
  const response = await api.get('/permissions/groups')
  return response.data
}

export const createPermissionGroup = async (data: Record<string, any>) => {
  const response = await api.post('/permissions/groups', data)
  return response.data
}

export const updatePermissionGroup = async (id: number, data: Record<string, any>) => {
  const response = await api.patch(`/permissions/groups/${id}`, data)
  return response.data
}

export const deletePermissionGroup = async (id: number) => {
  const response = await api.delete(`/permissions/groups/${id}`)
  return response.data
}

export const getRolePermissions = async (params: Record<string, any> = {}) => {
  const response = await api.get('/permissions/role-permissions', { params })
  return response.data
}

export const addRolePermission = async (data: Record<string, any>) => {
  const response = await api.post('/permissions/role-permissions', data)
  return response.data
}

export const removeRolePermission = async (id: number) => {
  const response = await api.delete(`/permissions/role-permissions/${id}`)
  return response.data
}

export const batchAddRolePermissions = async (data: Record<string, any>) => {
  const response = await api.post('/permissions/role-permissions/batch', data)
  return response.data
}

export const getIndividualPermissions = async (params: Record<string, any> = {}) => {
  const response = await api.get('/permissions/individual', { params })
  return response.data
}

export const addIndividualPermission = async (data: Record<string, any>) => {
  const response = await api.post('/permissions/individual', data)
  return response.data
}

export const removeIndividualPermission = async (id: number) => {
  const response = await api.delete(`/permissions/individual/${id}`)
  return response.data
}

export const getAllPermissionsGrouped = async () => {
  const response = await api.get('/permissions/all-grouped')
  return response.data
}

// === Платежи ===
export const getPayments = (params?: { order_id?: number; skip?: number; limit?: number }) =>
  api.get('/payments/', { params }).then(r => r.data)

export const createPayment = (data: { order_id: number; amount: number; payment_type: string; method?: string; comment?: string }) =>
  api.post('/payments/', data).then(r => r.data)

export const deletePayment = (id: number) =>
  api.delete(`/payments/${id}`).then(r => r.data)

export const getPaymentSummary = (orderId: number) =>
  api.get(`/payments/order/${orderId}/summary`).then(r => r.data)

// === Услуги ===
export const getServices = (params?: { status?: string; search?: string }) =>
  api.get('/services/', { params }).then(r => r.data)

export const createService = (data: { name: string; description?: string; price: number; status?: string }) =>
  api.post('/services/', data).then(r => r.data)

export const updateService = (id: number, data: { name?: string; description?: string; price?: number; status?: string }) =>
  api.patch(`/services/${id}`, data).then(r => r.data)

export const deleteService = (id: number) =>
  api.delete(`/services/${id}`).then(r => r.data)

// === Поиск ===
export const globalSearch = (q: string) =>
  api.get(`/search/?q=${encodeURIComponent(q)}`).then(r => r.data)

export const getPartsWriteOffs = async (params: Record<string, any> = {}) => {
  const response = await api.get('/parts/write-offs', { params })
  return response.data
}

// === Экспорт ===
const API_BASE = '/api'
export const exportOrders = (params?: { status?: string; date_from?: string; date_to?: string }) => {
  const qs = new URLSearchParams(params as any).toString()
  return `${API_BASE}/export/orders?${qs}`
}
export const exportParts = () => `${API_BASE}/export/parts`
export const exportServices = () => `${API_BASE}/export/services`
export const exportClients = () => `${API_BASE}/export/clients`

// === Salary Report ===

export const getSalaryReport = (params?: {
  user_id?: number;
  date_from?: string;
  date_to?: string;
  status?: string;
  skip?: number;
  limit?: number;
}) => api.get('/salary/records/report', { params }).then(r => r.data)
