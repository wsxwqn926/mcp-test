import { ref, onUnmounted } from 'vue'
import { useConnectionStore } from '../stores/connection'
import { useMessageStore } from '../stores/messages'
import { useNotificationStore } from '../stores/notification'

export interface WsMessage {
  type: string
  data: any
}

export function useWebSocket() {
  const ws = ref<WebSocket | null>(null)
  const connected = ref(false)
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null

  function connect() {
    if (ws.value && ws.value.readyState === WebSocket.OPEN) return

    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
    const url = `${protocol}//${location.host}/ws`
    ws.value = new WebSocket(url)

    ws.value.onopen = () => {
      connected.value = true
    }

    ws.value.onmessage = (event) => {
      try {
        const msg: WsMessage = JSON.parse(event.data)
        handleMessage(msg)
      } catch {}
    }

    ws.value.onclose = () => {
      connected.value = false
      reconnectTimer = setTimeout(connect, 3000)
    }

    ws.value.onerror = () => {
      ws.value?.close()
    }
  }

  function handleMessage(msg: WsMessage) {
    const connStore = useConnectionStore()
    const msgStore = useMessageStore()

    switch (msg.type) {
      case 'init':
        connStore.updateStateFromWs(
          msg.data.connection_state,
          msg.data.server_info,
        )
        break
      case 'connection_state':
        connStore.updateStateFromWs(
          msg.data.state,
          msg.data.server_info,
        )
        break
      case 'message_log':
        msgStore.addMessageFromWs(msg.data)
        break
      case 'pong':
        break
      case 'server_notification':
        useNotificationStore().addFromWs(msg.data)
        break
      case 'workflow_node_status':
        import('../stores/workflow').then(m => {
          m.useWorkflowStore().updateNodeStatus(msg.data)
        })
        break
      case 'workflow_run_complete':
        import('../stores/workflow').then(m => {
          m.useWorkflowStore().setRunComplete(msg.data)
        })
        break
    }
  }

  function disconnect() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    ws.value?.close()
    ws.value = null
    connected.value = false
  }

  function send(data: any) {
    if (ws.value && ws.value.readyState === WebSocket.OPEN) {
      ws.value.send(JSON.stringify(data))
    }
  }

  onUnmounted(() => {
    disconnect()
  })

  return {
    ws,
    connected,
    connect,
    disconnect,
    send,
  }
}
