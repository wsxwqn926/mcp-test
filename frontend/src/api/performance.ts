import http from './index'

export interface PerformanceReport {
  test_type: string
  tool_name: string
  arguments?: any
  started_at: string
  finished_at: string
  total_requests: number
  successful_requests: number
  failed_requests: number
  qps: number | null
  latency_stats: {
    min_ms: number
    max_ms: number
    avg_ms: number
    p50_ms: number
    p95_ms: number
    p99_ms: number
    std_dev_ms: number
  }
  raw_latencies: number[]
  errors: string[]
}

export const performanceApi = {
  latency: (data: { tool_name: string; arguments?: any; iterations?: number; warmup?: number }) =>
    http.post<any, PerformanceReport>('/api/performance/latency', data),
  concurrency: (data: { tool_name: string; arguments?: any; concurrency?: number; requests_per_worker?: number }) =>
    http.post<any, PerformanceReport>('/api/performance/concurrency', data),
}
