import { defineStore } from 'pinia'
import { ref } from 'vue'
import { toolsApi, type ToolInfo, type ToolCallResult, type ToolCallHistory } from '../api/tools'

export const useToolStore = defineStore('tools', () => {
  const tools = ref<ToolInfo[]>([])
  const selectedTool = ref<string>('')
  const callResult = ref<ToolCallResult | null>(null)
  const callHistory = ref<Record<string, ToolCallHistory[]>>({})

  async function loadTools(forceRefresh = false) {
    const res = await toolsApi.list(forceRefresh)
    tools.value = res.tools
  }

  async function callTool(name: string, args?: any) {
    const res = await toolsApi.call(name, args)
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
  }

  return {
    tools,
    selectedTool,
    callResult,
    callHistory,
    loadTools,
    callTool,
    loadHistory,
    clear,
  }
})
