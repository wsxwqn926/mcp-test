import http from './index'

export interface ResourceInfo {
  uri: string
  name?: string
  description?: string
  mimeType?: string
}

export interface ResourceContent {
  uri: string
  mimeType?: string
  text?: string
  blob?: string
}

export const resourcesApi = {
  list: (forceRefresh = false) =>
    http.get<any, { resources: ResourceInfo[] }>('/api/resources', { params: { force_refresh: forceRefresh } }),
  templates: (forceRefresh = false) =>
    http.get<any, { templates: any[] }>('/api/resources/templates', { params: { force_refresh: forceRefresh } }),
  read: (uri: string) =>
    http.post<any, { contents: ResourceContent[] }>('/api/resources/read', { uri }),
  subscribe: (uri: string) =>
    http.post('/api/resources/subscribe', { uri }),
  unsubscribe: (uri: string) =>
    http.post('/api/resources/unsubscribe', { uri }),
}
