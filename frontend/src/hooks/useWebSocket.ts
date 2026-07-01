import { useEffect, useRef, useCallback, useState } from 'react'

interface WebSocketMessage {
  type: string
  [key: string]: any
}

interface UseWebSocketOptions {
  onMessage?: (message: WebSocketMessage) => void
  onConnected?: () => void
  onDisconnected?: () => void
  autoReconnect?: boolean
  reconnectInterval?: number
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const {
    onMessage,
    onConnected,
    onDisconnected,
    autoReconnect = true,
    reconnectInterval = 5000,
  } = options

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null)
  const [isConnected, setIsConnected] = useState(false)

  const connect = useCallback(() => {
    const token = localStorage.getItem('token')
    if (!token) return

    // Определяем URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.hostname
    // Для dev-сервера (5173) бэкенд на 8000
    const port = window.location.port === '5173' ? '8000' : window.location.port || '8000'
    const wsUrl = `${protocol}//${host}:${port}/ws?token=${token}`

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      setIsConnected(true)
      onConnected?.()
    }

    ws.onclose = () => {
      setIsConnected(false)
      wsRef.current = null
      onDisconnected?.()

      if (autoReconnect) {
        reconnectTimerRef.current = setTimeout(connect, reconnectInterval)
      }
    }

    ws.onerror = () => {
      ws.close()
    }

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data)
        onMessage?.(message)
      } catch (e) {
        console.error('WebSocket parse error:', e)
      }
    }
  }, [onMessage, onConnected, onDisconnected, autoReconnect, reconnectInterval])

  const disconnect = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current)
      reconnectTimerRef.current = null
    }
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setIsConnected(false)
  }, [])

  const send = useCallback((data: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
    }
  }, [])

  useEffect(() => {
    connect()
    return () => {
      disconnect()
    }
  }, [])

  return { isConnected, send, connect, disconnect }
}
