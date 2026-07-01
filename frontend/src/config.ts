/**
 * Конфигурация приложения
 * Переменные из .env.local или .env (VITE_ префикс)
 */

export const config = {
  API_URL: (import.meta as any).env?.VITE_API_URL || 'http://127.0.0.1:8000/api',
  APP_NAME: 'CRM Сервисный центр',
} as const
