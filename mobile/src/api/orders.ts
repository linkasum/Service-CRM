import { api } from './client';

export interface Order {
  id: number;
  order_number: string | null;
  client_name: string;
  client_phone: string;
  device_model: string;
  device_brand: string;
  status: string;
  complaint: string;
  serial_number: string;
  master_id: number | null;
  master_username?: string;
  acceptor_username?: string;
  total_cost: number;
  created_at: string;
  ready_at: string | null;
  client_address?: string;
  has_delivery?: boolean;
  comment?: string;
  accessories?: string;
}

export interface OrderComment {
  id: number;
  text: string;
  author_name: string;
  created_at: string;
}

interface OrdersResponse {
  items: Order[];
  total: number;
  status_counts?: Record<string, number>;
}

export function getOrders(params?: Record<string, string>): Promise<Order[]> {
  const query = params ? '?' + new URLSearchParams(params).toString() : '';
  return api.get<OrdersResponse>(`/api/orders/${query}`).then(r => r.items);
}

export function getOrder(id: number): Promise<Order> {
  return api.get<Order>(`/api/orders/${id}`);
}

export function updateOrderStatus(id: number, status: string, comment?: string): Promise<Order> {
  return api.patch<Order>(`/api/orders/${id}/status`, { status, comment });
}

export function getOrderComments(orderId: number): Promise<OrderComment[]> {
  return api.get<OrderComment[]>(`/api/orders/${orderId}/comments/`);
}

export function addOrderComment(orderId: number, text: string): Promise<OrderComment> {
  return api.post<OrderComment>(`/api/orders/${orderId}/comments/`, { text });
}
