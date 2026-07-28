import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import {
  getOrder, getOrderComments, addOrderComment, updateOrderStatus,
  type Order, type OrderComment,
} from '../api/orders';
import { getStatuses, getStatusLabel, type OrderStatus } from '../api/statuses';
import { getUserRole } from '../api/auth';

export default function OrderDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [order, setOrder] = useState<Order | null>(null);
  const [comments, setComments] = useState<OrderComment[]>([]);
  const [statuses, setStatuses] = useState<OrderStatus[]>([]);
  const [newComment, setNewComment] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user) {
      getStatuses().then(setStatuses).catch(() => {});
    }
  }, [user]);

  const load = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const [o, c] = await Promise.all([getOrder(+id), getOrderComments(+id)]);
      setOrder(o);
      setComments(c);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [id]);

  const handleStatusChange = async (newCode: string) => {
    try {
      const updated = await updateOrderStatus(order!.id, newCode);
      setOrder(updated);
      load();
    } catch (e: any) {
      alert(e.message);
    }
  };

  const handleAddComment = async () => {
    if (!newComment.trim()) return;
    try {
      await addOrderComment(order!.id, newComment.trim());
      setNewComment('');
      load();
    } catch (e: any) {
      alert(e.message);
    }
  };

  if (loading) return <div className="loader">Загрузка...</div>;
  if (!order) return <div className="empty">Заказ не найден</div>;

  const s = (order.status || '').toLowerCase();
  const currentStatus = statuses.find(st => st.code === s);

  // Build transitions from statuses: show all statuses except current as possible targets
  // (backend validates anyway)
  const transitions = statuses.filter(st =>
    st.is_active && st.code !== s &&
    !['issued_br', 'cancelled'].includes(st.code) // hide terminal/special statuses
  );

  const role = user ? getUserRole(user) : '';
  const isMaster = role === 'master' || role === 'admin' || role === 'manager';
  const isCourier = role === 'courier';

  return (
    <div className="detail-page">
      <header>
        <button className="back-btn" onClick={() => navigate('/')}>← Назад</button>
        <h3>Заказ №{order.order_number || order.id}</h3>
      </header>

      <div className="detail-card">
        <div className="detail-row">
          <span className="label">Клиент</span>
          <span>{order.client_name}</span>
        </div>
        <div className="detail-row">
          <span className="label">Телефон</span>
          <a href={`tel:${order.client_phone}`}>{order.client_phone}</a>
        </div>
        <div className="detail-row">
          <span className="label">Устройство</span>
          <span>{[order.device_brand, order.device_model].filter(Boolean).join(' ') || '—'}</span>
        </div>
        <div className="detail-row">
          <span className="label">Серийный</span>
          <span>{order.serial_number || '—'}</span>
        </div>
        <div className="detail-row">
          <span className="label">Проблема</span>
          <span>{order.complaint || '—'}</span>
        </div>
        <div className="detail-row">
          <span className="label">Мастер</span>
          <span>{order.master_username || 'Не назначен'}</span>
        </div>
        <div className="detail-row">
          <span className="label">Приёмщик</span>
          <span>{order.acceptor_username || '—'}</span>
        </div>
        <div className="detail-row">
          <span className="label">Статус</span>
          <span className="status-badge" style={{ background: currentStatus?.color || '#999' }}>
            {getStatusLabel(order.status, statuses)}
          </span>
        </div>
        {order.has_delivery && (
          <div className="detail-row">
            <span className="label">Адрес доставки</span>
            <span>{order.client_address || '—'}</span>
          </div>
        )}
        {order.accessories && (
          <div className="detail-row">
            <span className="label">Комплектация</span>
            <span>{order.accessories}</span>
          </div>
        )}
        <div className="detail-row">
          <span className="label">Создан</span>
          <span>{new Date(order.created_at).toLocaleDateString('ru')}</span>
        </div>
      </div>

      {/* Status transitions */}
      {isMaster && transitions.length > 0 && (
        <div className="status-actions">
          <h4>Сменить статус:</h4>
          <div className="btn-group">
            {transitions.map((st) => (
              <button
                key={st.code}
                onClick={() => handleStatusChange(st.code)}
                style={{ background: st.color }}
              >
                {st.name}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Delivery action for couriers */}
      {isCourier && (s === 'ready_pickup' || s === 'ready') && (
        <div className="status-actions">
          <button className="btn-primary" onClick={() => handleStatusChange('issued')}>
            ✅ Отметить доставленным
          </button>
        </div>
      )}

      {/* Comments */}
      <div className="comments-section">
        <h4>Комментарии</h4>
        {comments.length === 0 && <p className="empty-sm">Нет комментариев</p>}
        {comments.map((c) => (
          <div key={c.id} className="comment">
            <div className="comment-meta">
              <strong>{c.author_name}</strong>
              <span>{new Date(c.created_at).toLocaleString('ru')}</span>
            </div>
            <p>{c.text}</p>
          </div>
        ))}

        <div className="comment-input">
          <textarea
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder="Добавить комментарий..."
            rows={2}
          />
          <button onClick={handleAddComment} disabled={!newComment.trim()}>
            Отправить
          </button>
        </div>
      </div>
    </div>
  );
}
