import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { getOrders, type Order } from '../api/orders';
import { getStatuses, getStatusLabel, getStatusColor, type OrderStatus } from '../api/statuses';
import { getUserRole } from '../api/auth';
import { getTheme, setTheme } from '../hooks/useTheme';

export default function Orders() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [orders, setOrders] = useState<Order[]>([]);
  const [statuses, setStatuses] = useState<OrderStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('my');
  const [theme, setThemeState] = useState(getTheme());

  const role = user ? getUserRole(user) : '';

  const [error, setError] = useState<string | null>(null);

  const toggleTheme = () => {
    const next = theme === 'light' ? 'dark' : 'light';
    setTheme(next);
    setThemeState(next);
  };

  // Load statuses only after auth
  useEffect(() => {
    if (user) {
      getStatuses().then(setStatuses).catch(() => {});
    }
  }, [user]);

  const loadOrders = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (filter === 'my') {
        if (role === 'master') params.master_id = String(user.id);
      } else if (filter === 'ready') {
        if (role === 'master') params.master_id = String(user.id);
        params.status = 'ready';
      }
      let data = await getOrders(params);
      // Client-side status filter
      if (filter === 'my') {
        const activeSet = new Set(['new', 'diagnostics', 'agreed', 'repair', 'waiting_parts']);
        data = data.filter(o => activeSet.has((o.status || '').toLowerCase()));
      } else if (filter === 'active') {
        data = data.filter(o => (o.status || '').toLowerCase() === 'repair');
      }
      setOrders(data);
    } catch (e: any) {
      console.error(e);
      setError(e.message || 'Ошибка загрузки');
    } finally {
      setLoading(false);
    }
  }, [filter, user, role]);

  useEffect(() => { loadOrders(); }, [loadOrders]);

  const filters: { key: string; label: string }[] = role === 'master'
    ? [{ key: 'my', label: 'Мои' }, { key: 'active', label: 'В работе' }, { key: 'ready', label: 'Готов' }, { key: 'all', label: 'Все' }]
    : [{ key: 'my', label: 'В работе' }, { key: 'ready', label: 'Готов' }, { key: 'all', label: 'Все' }];

  return (
    <div className="orders-page">
      <header>
        <h2>📋 Заказы</h2>
        <div className="header-right">
          <button className="btn-sm theme-btn" onClick={toggleTheme}>
            {theme === 'light' ? '🌙' : '☀️'}
          </button>
          <span className="user-badge">{user?.full_name || user?.username}</span>
          <button className="btn-sm" onClick={logout}>Выйти</button>
        </div>
      </header>

      <div className="filter-bar">
        {filters.map((f) => (
          <button key={f.key} className={`filter-btn ${filter === f.key ? 'active' : ''}`} onClick={() => setFilter(f.key)}>
            {f.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="loader">Загрузка...</div>
      ) : error ? (
        <div className="empty" style={{ color: 'var(--danger)' }}>❌ {error}</div>
      ) : orders.length === 0 ? (
        <div className="empty">Нет заказов</div>
      ) : (
        <ul className="order-list">
          {orders.map((o) => (
            <li key={o.id} className="order-item" onClick={() => navigate(`/order/${o.id}`)}>
              <div className="order-top">
                <span className="order-num">№{o.order_number || o.id}</span>
                <span className="order-status" style={{ background: getStatusColor(o.status, statuses) }}>
                  {getStatusLabel(o.status, statuses)}
                </span>
              </div>
              <div className="order-client">{o.client_name}</div>
              <div className="order-device">
                {o.device_brand && `${o.device_brand} `}{o.device_model}
              </div>
              {o.has_delivery && <span className="delivery-badge">🚚 Доставка</span>}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
