import http from './index'

export interface ValidationReport {
  server_name: string
  server_version: string
  protocol_version: string
  timestamp: string
  total_checks: number
  passed: number
  failed: number
  warnings: number
  results: Array<{
    check_id: string
    category: string
    description: string
    status: 'passed' | 'failed' | 'warning' | 'skipped'
    details?: string
  }>
  overall_status: 'compliant' | 'partial' | 'non_compliant'
}

export const validatorApi = {
  run: () => http.post<any, ValidationReport>('/api/validator/run'),
}
