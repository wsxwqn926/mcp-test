import http from './index'

export type NodeType = 'start' | 'end' | 'tool_call' | 'resource_read' | 'prompt_get'
  | 'assertion' | 'wait' | 'condition' | 'variable' | 'loop'

export interface WorkflowNode {
  id: string
  type: NodeType
  position: { x: number; y: number }
  label?: string
  data: Record<string, any>
}

export interface WorkflowEdge {
  id: string
  source: string
  target: string
  sourceHandle?: string
  label?: string
  data?: Record<string, any>
}

export interface Workflow {
  id: string
  name: string
  description?: string
  nodes: WorkflowNode[]
  edges: WorkflowEdge[]
  variables: Record<string, any>
  tags: string[]
  created_at: string
  updated_at: string
}

export interface NodeResult {
  node_id: string
  node_type: string
  node_label?: string
  status: string
  duration_ms: number
  request?: Record<string, any>
  response?: Record<string, any>
  error_message?: string
  assertion_results: any[]
}

export interface WorkflowRunResult {
  id: string
  workflow_id: string
  workflow_name: string
  status: string
  duration_ms: number
  node_results: Record<string, NodeResult>
  variables_snapshot: Record<string, any>
  error_message?: string
}

export const workflowsApi = {
  list: () => http.get<any, { workflows: Record<string, Workflow> }>('/api/workflows'),
  create: (data: any) => http.post<any, Workflow>('/api/workflows', data),
  get: (id: string) => http.get<any, Workflow>(`/api/workflows/${id}`),
  update: (id: string, data: any) => http.put<any, Workflow>(`/api/workflows/${id}`, data),
  delete: (id: string) => http.delete(`/api/workflows/${id}`),
  run: (id: string, variables?: Record<string, any>) =>
    http.post<any, WorkflowRunResult>(`/api/workflows/${id}/run`, { variables }),
  stop: (id: string) => http.post(`/api/workflows/${id}/stop`),
  getResult: (id: string) => http.get<any, { result: WorkflowRunResult | null }>(`/api/workflows/${id}/result`),
}
