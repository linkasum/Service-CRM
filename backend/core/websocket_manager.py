"""
Менеджер WebSocket подключений
Управляет активными WebSocket-соединениями и рассылкой уведомлений
"""
from typing import Dict, Set, Any
from fastapi import WebSocket
from core.logging import logger


class WebSocketManager:
    """Управление WebSocket подключениями"""

    def __init__(self):
        # {connection_id: websocket}
        self.active_connections: Dict[str, WebSocket] = {}
        # {user_id: set[connection_id]}
        self.user_connections: Dict[int, Set[str]] = {}

    async def connect(self, websocket: WebSocket, connection_id: str, user_id: int):
        """Принять новое WebSocket подключение"""
        await websocket.accept()
        self.active_connections[connection_id] = websocket

        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(connection_id)

        logger.info(f"WebSocket подключён: {connection_id} (user {user_id}), всего: {len(self.active_connections)}")

    def disconnect(self, connection_id: str, user_id: int | None = None):
        """Отключить WebSocket"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            logger.info(f"WebSocket отключён: {connection_id}, осталось: {len(self.active_connections)}")

        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(connection_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

    async def send_to_connection(self, connection_id: str, message: dict):
        """Отправить сообщение конкретному подключению"""
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send_json(message)
            except Exception as e:
                logger.error(f"Ошибка отправки в {connection_id}: {e}")
                self.disconnect(connection_id)

    async def broadcast(self, message: dict, exclude_user_id: int | None = None):
        """Отправить сообщение всем подключённым клиентам"""
        disconnected = []
        for conn_id, websocket in list(self.active_connections.items()):
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Ошибка рассылки {conn_id}: {e}")
                disconnected.append(conn_id)

        # Чистим мёртвые подключения
        for conn_id in disconnected:
            if conn_id in self.active_connections:
                del self.active_connections[conn_id]

    async def send_to_user(self, user_id: int, message: dict):
        """Отправить сообщение всем подключениям конкретного пользователя"""
        if user_id in self.user_connections:
            for conn_id in list(self.user_connections[user_id]):
                await self.send_to_connection(conn_id, message)


# Глобальный экземпляр
ws_manager = WebSocketManager()
