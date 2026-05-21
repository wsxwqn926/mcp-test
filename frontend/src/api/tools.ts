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
  list: (forceRefresh = false, configId?: string) =>
    http.get<any, { tools: ToolInfo[] }>('/api/tools', { params: { force_refresh: forceRefresh, config_id: configId } }),
  listAll: (forceRefresh = false) =>
    http.get<any, Record<string, { tools: ToolInfo[]; error?: string }>>('/api/tools/all', { params: { force_refresh: forceRefresh } }),
  get: (name: string, configId?: string) =>
    http.get<any, ToolInfo & { form_fields: any[] }>(`/api/tools/${name}`, { params: { config_id: configId } }),
  call: (name: string, arguments_?: any, configId?: string) =>
    http.post<any, ToolCallResult>(`/api/tools/${name}/call`, { arguments: arguments_, config_id: configId }),
  history: (name: string) =>
    http.get<any, { history: ToolCallHistory[] }>(`/api/tools/${name}/history`),
}
