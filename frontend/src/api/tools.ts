import http from './index'

export interface ToolInfo {
  name: string
  description?: string
  inputSchema?: any
}

export interface ToolCallResult {
  content: Array<{ type: string; text?: string; data?: string; mimeType?: string }>
  is_error: boolean
  duration_ms: number
}

export interface ToolCallHistory {
  tool_name: string
  arguments: any
  duration_ms: number
  timestamp: string
  is_error: boolean
}

export const toolsApi = {
  list: (forceRefresh = false) =>
    http.get<any, { tools: ToolInfo[] }>('/api/tools', { params: { force_refresh: forceRefresh } }),
  get: (name: string) =>
    http.get<any, ToolInfo & { form_fields: any[] }>(`/api/tools/${name}`),
  call: (name: string, arguments_?: any) =>
    http.post<any, ToolCallResult>(`/api/tools/${name}/call`, { arguments: arguments_ }),
  history: (name: string) =>
    http.get<any, { history: ToolCallHistory[] }>(`/api/tools/${name}/history`),
}
