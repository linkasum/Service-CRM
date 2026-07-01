"""
WebSocket endpoint для real-time обновлений
"""
import uuid
from fastapi import WebSocket, WebSocketDisconnect, Query
from core.websocket_manager import ws_manager
from core.security import decode_token
from core.logging import logger


async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
):
    """
    WebSocket подключение для real-time обновлений.
    
    Подключение: ws://host/ws?token=<jwt_token>
    
    Сообщения от клиента:
    - {"type": "ping"} — проверка соединения
    
    Сообщения сервера:
    - {"type": "connected", "connection_id": "..."} — подтверждение подключения
    - {"type": "order_status_changed", "order_id": N, "old_status": "...", "new_status": "...", "order": {...}}
    - {"type": "pong"} — ответ на ping
    """
    # Валидируем токен
    payload = decode_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id = payload.get("user_id") or payload.get("sub")
    if not user_id:
        await websocket.close(code=4001, reason="Invalid token payload")
        return

    connection_id = str(uuid.uuid4())

    await ws_manager.connect(websocket, connection_id, user_id)

    try:
        # Приветственное сообщение
        await websocket.send_json({
            "type": "connected",
            "connection_id": connection_id,
            "user_id": user_id,
        })

        # Основной цикл чтения сообщений
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        logger.info(f"WebSocket отключён: {connection_id} (user {user_id})")
    except Exception as e:
        logger.error(f"Ошибка WebSocket {connection_id}: {e}")
    finally:
        ws_manager.disconnect(connection_id, user_id)
