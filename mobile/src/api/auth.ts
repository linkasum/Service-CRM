import { api } from './client';

export interface User {
  id: number;
  username: string;
  full_name: string;
  role_id: number;
  role?: string;
}

// Role mapping: 1=admin, 2=manager, 3=master, 4=acceptor, 5=courier
const ROLE_NAMES: Record<number, string> = { 1: 'admin', 2: 'manager', 3: 'master', 4: 'acceptor', 5: 'courier' };

export function getUserRole(user: User): string {
  return ROLE_NAMES[user.role_id] || 'unknown';
}

export interface LoginResponse {
  access_token: string;
  user: User;
}

export function login(username: string, password: string): Promise<LoginResponse> {
  return api.post<LoginResponse>('/api/auth/login', { username, password });
}

export function getMe(): Promise<User> {
  return api.get<User>('/api/auth/me');
}
