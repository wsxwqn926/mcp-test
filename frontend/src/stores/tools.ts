import { defineStore } from 'pinia'
import { ref } from 'vue'
import { toolsApi, type ToolInfo, type ToolCallResult, type ToolCallHistory } from '../api/tools'

export const useToolStore = defineStore('tools', () => {
  const tools = ref<ToolInfo[]>([])
  const selectedTool = ref<string>('')
  const callResult = ref<ToolCallResult | null>(null)
  const callHistory = ref<Record<string, ToolCallHistory[]>>({})
  const allTools = ref<Record<string, { tools: ToolInfo[]; error?: string }>>({})

  async function loadTools(forceRefresh = false, configId?: string) {
    const res = await toolsApi.list(forceRefresh, configId)
    tools.value = res.tools
  }

  async function loadAllTools(forceRefresh = false) {
    const res = await toolsApi.listAll(forceRefresh)
    allTools.value = res
  }

  async function callTool(name: string, args?: any, configId?: string) {
    const res = await toolsApi.call(name, args, configId)
    callResult.value = res
    await loadHistory(name)
    return res
  }

  async function loadHistory(name: string) {
    const res = await toolsApi.history(name)
    callHistory.value = { ...callHistory.value, [name]: res.history }
  }

  function clear() {
    tools.value = []
    selectedTool.value = ''
    callResult.value = null
    callHistory.value = {}
    allTools.value = {}
  }

  return {
    tools,
    selectedTool,
    callResult,
    callHistory,
    allTools,
    loadTools,
    loadAllTools,
    callTool,
    loadHistory,
    clear,
  }
})
