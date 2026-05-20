import http from './index'

export interface MessageLog {
  id: string
  session_id: string
  direction: 'request' | 'response' | 'notification'
  timestamp: string
  method?: string
  request_id?: number | string
  data: any
  duration_ms?: number
  error?: any
}

export interface MessageStats {
  total: number
  requests: number
  responses: number
  notifications: number
  errors: number
  methods: Record<string, number>
  avg_duration_ms: number
  max_duration_ms: number
  min_duration_ms: number
}

export const messagesApi = {
  query: (params?: { direction?: string; method?: string; search_text?: string; limit?: number }) =>
    http.get<any, { messages: MessageLog[]; total: number }>('/api/messages', { params }),
  stats: () => http.get<any, MessageStats>('/api/messages/stats'),
  clear: () => http.delete('/api/messages'),
  exportJson: () => http.get('/api/messages/export/json', { responseType: 'blob' }),
  exportCsv: () => http.get('/api/messages/export/csv', { responseType: 'blob' }),
  history: () => http.get<any, { files: Array<{ name: string; size: number; modified: string }> }>('/api/messages/history'),
  getHistory: (filename: string) => http.get<any, MessageLog[]>(`/api/messages/history/${filename}`),
}
