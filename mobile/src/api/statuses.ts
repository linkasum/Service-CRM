import { api } from './client';

export interface OrderStatus {
  id: number;
  name: string;
  code: string;
  color: string;
  is_default: boolean;
  is_active: boolean;
}

let cachedStatuses: OrderStatus[] | null = null;

export function getStatuses(): Promise<OrderStatus[]> {
  if (cachedStatuses) return Promise.resolve(cachedStatuses);
  return api.get<OrderStatus[]>('/api/settings/statuses').then(data => {
    cachedStatuses = data;
    return data;
  });
}

export function getStatusLabel(code: string, statuses: OrderStatus[]): string {
  const s = statuses.find(st => st.code === code);
  return s?.name || code;
}

export function getStatusColor(code: string, statuses: OrderStatus[]): string {
  const s = statuses.find(st => st.code === code);
  return s?.color || '#999';
}
