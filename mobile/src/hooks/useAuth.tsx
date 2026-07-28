import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { api } from '../api/client';
import { login as apiLogin, getMe, getUserRole, type User } from '../api/auth';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>(null!);

const ALLOWED_ROLES = new Set(['master', 'admin']);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = api.getToken();
    if (token) {
      getMe()
        .then((u) => {
          const role = getUserRole(u);
          if (!ALLOWED_ROLES.has(role)) {
            api.setToken(null);
            setError('Доступ только для мастеров');
          } else {
            setUser(u);
          }
        })
        .catch(() => api.setToken(null))
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (username: string, password: string) => {
    setError(null);
    try {
      const res = await apiLogin(username, password);
      const role = getUserRole(res.user);
      if (!ALLOWED_ROLES.has(role)) {
        throw new Error('Доступ только для мастеров и администратора');
      }
      api.setToken(res.access_token);
      setUser(res.user);
    } catch (e: any) {
      setError(e.message || 'Ошибка входа');
      throw e;
    }
  };

  const logout = () => {
    api.setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, error, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
