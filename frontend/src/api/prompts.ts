import http from './index'

export interface PromptInfo {
  name: string
  description?: string
  arguments: Array<{ name: string; description?: string; required: boolean }>
}

export interface PromptResult {
  description?: string
  messages: Array<{ role: string; type: string; content: string; mime?: string }>
}

export const promptsApi = {
  list: (forceRefresh = false) =>
    http.get<any, { prompts: PromptInfo[] }>('/api/prompts', { params: { force_refresh: forceRefresh } }),
  get: (name: string, arguments_?: Record<string, string>) =>
    http.post<any, PromptResult>(`/api/prompts/${name}/get`, { arguments: arguments_ }),
}
