import http from './index'

export interface TestStepData {
  id: string
  type: 'tool_call' | 'resource_read' | 'prompt_get' | 'assertion' | 'wait'
  name?: string
  tool_name?: string
  arguments?: any
  resource_uri?: string
  prompt_name?: string
  prompt_arguments?: any
  assertion?: { type: string; expected?: any; path?: string; negate?: boolean }
  wait_seconds?: number
}

export interface TestCaseData {
  id: string
  name: string
  description?: string
  server_config_id?: string
  steps: TestStepData[]
  tags: string[]
  created_at: string
  updated_at: string
}

export interface TestRunResult {
  id: string
  test_case_id: string
  test_case_name: string
  status: 'passed' | 'failed' | 'error' | 'skipped'
  started_at: string
  finished_at: string
  duration_ms: number
  total_steps: number
  passed_steps: number
  failed_steps: number
  step_results: any[]
  error_message?: string
}

export const testsApi = {
  list: () => http.get<any, { test_cases: Record<string, TestCaseData> }>('/api/tests'),
  create: (data: any) => http.post<any, TestCaseData>('/api/tests', data),
  get: (id: string) => http.get<any, TestCaseData>(`/api/tests/${id}`),
  update: (id: string, data: any) => http.put<any, TestCaseData>(`/api/tests/${id}`, data),
  delete: (id: string) => http.delete(`/api/tests/${id}`),
  run: (id: string) => http.post<any, TestRunResult>(`/api/tests/${id}/run`),
  record: () => http.post<any, { steps: TestStepData[]; count: number }>('/api/tests/record'),
}
