import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { connectionsApi, type ServerConfig, type ConnectionStatus, type ConnectedServer } from '../api/connections'
import { ElMessage } from 'element-plus'

export const useConnectionStore = defineStore('connection', () => {
  const configs = ref<Record<string, ServerConfig>>({})
  const status = ref<ConnectionStatus>({
    state: 'disconnected',
    config: null,
    server_info: null,
    primary_id: null,
    connections: [],
  })

  const isConnected = computed(() => status.value.state === 'connected')
  const connectedConfig = computed(() => status.value.config)
  const serverInfo = computed(() => status.value.server_info)
  const connectedServers = computed(() => status.value.connections)
  const primaryId = computed(() => status.value.primary_id)

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

  async function connect(id: string, setPrimary = true) {
    const res = await connectionsApi.connect(id, { set_primary: setPrimary })
    await refreshStatus()
    ElMessage.success('已连接')
    return res
  }

  async function disconnect() {
    await connectionsApi.disconnect()
    await refreshStatus()
    ElMessage.success('已断开')
  }

  async function disconnectOne(id: string) {
    await connectionsApi.disconnectOne(id)
    await refreshStatus()
    ElMessage.success('已断开')
  }

  async function setPrimary(id: string) {
    await connectionsApi.setPrimary(id)
    await refreshStatus()
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

  function updateConnectionsFromWs(connections: ConnectedServer[]) {
    status.value = { ...status.value, connections }
  }

  return {
    configs,
    status,
    isConnected,
    connectedConfig,
    serverInfo,
    connectedServers,
    primaryId,
    loadConfigs,
    createConnection,
    updateConnection,
    deleteConnection,
    connect,
    disconnect,
    disconnectOne,
    setPrimary,
    refreshStatus,
    updateStateFromWs,
    updateConnectionsFromWs,
  }
})
