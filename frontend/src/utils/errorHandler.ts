/**
 * Утилиты для обработки ошибок API
 */
import { message } from 'antd'
import { FormInstance } from 'antd/es/form'

interface ApiError {
  detail?: string
  errors?: Array<{
    field: string
    message: string
    type: string
  }>
}

/**
 * Обработка ошибки API с отображением сообщения
 */
export function handleApiError(error: any, customMessage?: string): void {
  const detail = error.response?.data?.detail
  const status = error.response?.status

  if (status === 401) {
    // Уже обрабатывается в интерцепторе
    return
  }

  if (status === 403) {
    message.error(detail || 'Нет прав доступа к этому действию')
    return
  }

  if (status === 404) {
    message.error(detail || 'Ресурс не найден')
    return
  }

  if (status === 422) {
    // Валидация — обрабатывается отдельно
    if (customMessage) {
      message.error(customMessage)
    }
    return
  }

  if (status === 500) {
    message.error('Внутренняя ошибка сервера. Попробуйте позже.')
    return
  }

  message.error(detail || customMessage || 'Произошла ошибка')
}

/**
 * Привязать ошибки валидации 422 к полям формы
 */
export function attachValidationErrors(error: any, form: FormInstance): boolean {
  const data: ApiError = error.response?.data
  if (!data || error.response?.status !== 422) {
    return false
  }

  if (data.errors) {
    const formErrors: Record<string, { errors: string[] }> = {}
    data.errors.forEach(err => {
      // field format: "body -> field_name" or just "field_name"
      const fieldName = err.field.split(' -> ').pop()?.trim()
      if (fieldName) {
        formErrors[fieldName] = { errors: [err.message] }
      }
    })
    form.setFields(
      Object.entries(formErrors).map(([name, errors]) => ({
        name,
        errors: errors.errors,
      }))
    )
    message.error('Пожалуйста, исправьте ошибки в форме')
    return true
  }

  return false
}

/**
 * Комбинированная обработка: валидация на форму + toast
 */
export function handleFormError(error: any, form: FormInstance, context?: string): void {
  if (!attachValidationErrors(error, form)) {
    handleApiError(error, context)
  }
}
