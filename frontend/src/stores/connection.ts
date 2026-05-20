import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { connectionsApi, type ServerConfig, type ConnectionStatus } from '../api/connections'
import { ElMessage } from 'element-plus'

export const useConnectionStore = defineStore('connection', () => {
  const configs = ref<Record<string, ServerConfig>>({})
  const status = ref<ConnectionStatus>({
    state: 'disconnected',
    config: null,
    server_info: null,
  })

  const isConnected = computed(() => status.value.state === 'connected')
  const connectedConfig = computed(() => status.value.config)
  const serverInfo = computed(() => status.value.server_info)

  async function loadConfigs() {
    const res = await connectionsApi.list()
    configs.value = res.configs
  }

  async function createConnection(data: any) {
    const cfg = await connectionsApi.create(data)
    configs.value[cfg.id] = cfg
    return cfg
  }

  async function updateConnection(id: string, data: any) {
    const cfg = await connectionsApi.update(id, data)
    configs.value[id] = cfg
    return cfg
  }

  async function deleteConnection(id: string) {
    await connectionsApi.delete(id)
    delete configs.value[id]
  }

  async function connect(id: string) {
    const res = await connectionsApi.connect(id)
    await refreshStatus()
    ElMessage.success('已连接')
    return res
  }

  async function disconnect() {
    await connectionsApi.disconnect()
    await refreshStatus()
    ElMessage.success('已断开')
  }

  async function refreshStatus() {
    status.value = await connectionsApi.status()
  }

  function updateStateFromWs(state: string, serverInfo?: any) {
    status.value = { ...status.value, state }
    if (serverInfo !== undefined) {
      status.value = { ...status.value, server_info: serverInfo }
    }
  }

  return {
    configs,
    status,
    isConnected,
    connectedConfig,
    serverInfo,
    loadConfigs,
    createConnection,
    updateConnection,
    deleteConnection,
    connect,
    disconnect,
    refreshStatus,
    updateStateFromWs,
  }
})
