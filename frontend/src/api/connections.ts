import http from './index'

export interface ServerConfig {
  id: string
  name: string
  transport_type: 'stdio' | 'http' | 'sse'
  stdio_config?: { command: string; args: string[]; env?: Record<string, string>; cwd?: string }
  http_config?: { url: string; headers?: Record<string, string>; timeout?: number }
  created_at: string
  updated_at: string
}

export interface ConnectionStatus {
  state: string
  config: ServerConfig | null
  server_info: {
    name: string
    version: string
    protocol_version: string
    capabilities: Record<string, any>
  } | null
}

export const connectionsApi = {
  list: () => http.get<any, { configs: Record<string, ServerConfig> }>('/api/connections'),
  create: (data: any) => http.post<any, ServerConfig>('/api/connections', data),
  get: (id: string) => http.get<any, ServerConfig>(`/api/connections/${id}`),
  update: (id: string, data: any) => http.put<any, ServerConfig>(`/api/connections/${id}`, data),
  delete: (id: string) => http.delete(`/api/connections/${id}`),
  connect: (id: string) => http.post<any, { connected: boolean; server_info: any }>(`/api/connections/${id}/connect`),
  disconnect: () => http.post('/api/connections/disconnect'),
  status: () => http.get<any, ConnectionStatus>('/api/connections/status'),
  connectSecondary: (id: string) => http.post<any, { connected: boolean; server_info: any }>(`/api/connections/${id}/connect-secondary`),
  disconnectSecondary: (id: string) => http.post(`/api/connections/${id}/disconnect-secondary`),
  compare: () => http.get<any, Record<string, any>>('/api/connections/compare'),
}
