import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { messagesApi, type MessageLog, type MessageStats } from '../api/messages'

export const useMessageStore = defineStore('messages', () => {
  const messages = ref<MessageLog[]>([])
  const stats = ref<MessageStats>({
    total: 0,
    requests: 0,
    responses: 0,
    notifications: 0,
    errors: 0,
    methods: {},
    avg_duration_ms: 0,
    max_duration_ms: 0,
    min_duration_ms: 0,
  })

  const total = computed(() => stats.value.total)

  async function loadMessages(params?: { direction?: string; method?: string; search_text?: string; limit?: number }) {
    const res = await messagesApi.query(params)
    messages.value = res.messages
  }

  async function loadStats() {
    stats.value = await messagesApi.stats()
  }

  async function clearMessages() {
    await messagesApi.clear()
    messages.value = []
    stats.value = {
      total: 0, requests: 0, responses: 0, notifications: 0, errors: 0,
      methods: {}, avg_duration_ms: 0, max_duration_ms: 0, min_duration_ms: 0,
    }
  }

  async function exportJson() {
    const res = await messagesApi.exportJson()
    downloadBlob(res as any, 'messages.json', 'application/json')
  }

  async function exportCsv() {
    const res = await messagesApi.exportCsv()
    downloadBlob(res as any, 'messages.csv', 'text/csv')
  }

  function addMessageFromWs(msg: MessageLog) {
    messages.value.unshift(msg)
    stats.value.total++
    if (msg.direction === 'request') stats.value.requests++
    else if (msg.direction === 'response') stats.value.responses++
    else if (msg.direction === 'notification') stats.value.notifications++
    if (msg.error) stats.value.errors++
  }

  function downloadBlob(blob: Blob, filename: string, mimeType: string) {
    const url = URL.createObjectURL(new Blob([blob], { type: mimeType }))
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }

  return {
    messages,
    stats,
    total,
    loadMessages,
    loadStats,
    clearMessages,
    exportJson,
    exportCsv,
    addMessageFromWs,
  }
})
