<template>
  <div class="page-header">
    <h2>性能测试</h2>
  </div>

  <el-card class="section-card">
    <el-tabs v-model="testType">
      <el-tab-pane label="延迟测试" name="latency">
        <el-form :model="config" label-width="130px" size="small" style="max-width: 600px">
          <el-form-item label="工具名称">
            <el-input v-model="config.tool_name" placeholder="工具名称" />
          </el-form-item>
          <el-form-item label="参数 (JSON)">
            <el-input v-model="config.arguments_json" type="textarea" :rows="3" />
          </el-form-item>
          <el-form-item label="迭代次数">
            <el-input-number v-model="config.iterations" :min="10" :max="1000" />
          </el-form-item>
          <el-form-item label="预热次数">
            <el-input-number v-model="config.warmup" :min="0" :max="20" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="runLatency" :loading="loading">开始</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="并发测试" name="concurrency">
        <el-form :model="config" label-width="130px" size="small" style="max-width: 600px">
          <el-form-item label="工具名称">
            <el-input v-model="config.tool_name" placeholder="工具名称" />
          </el-form-item>
          <el-form-item label="参数 (JSON)">
            <el-input v-model="config.arguments_json" type="textarea" :rows="3" />
          </el-form-item>
          <el-form-item label="并发数">
            <el-input-number v-model="config.concurrency" :min="1" :max="50" />
          </el-form-item>
          <el-form-item label="每 worker 请求数">
            <el-input-number v-model="config.requests_per_worker" :min="1" :max="100" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="runConcurrency" :loading="loading">开始</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>
  </el-card>

  <template v-if="report">
    <el-card class="section-card" style="margin-top: 16px">
      <template #header><span style="font-weight: 600">测试结果</span></template>
      <div class="stats-row" style="margin-bottom: 16px">
        <div class="stat-card">
          <div class="stat-value">{{ report.total_requests }}</div>
          <div class="stat-label">总请求数</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" style="color: var(--success-color)">{{ report.successful_requests }}</div>
          <div class="stat-label">成功</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" style="color: var(--danger-color)">{{ report.failed_requests }}</div>
          <div class="stat-label">失败</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ report.qps?.toFixed(1) || '-' }}</div>
          <div class="stat-label">QPS</div>
        </div>
      </div>

      <el-descriptions :column="4" border size="small" style="margin-bottom: 16px">
        <el-descriptions-item label="Min">{{ report.latency_stats.min_ms.toFixed(1) }}ms</el-descriptions-item>
        <el-descriptions-item label="Avg">{{ report.latency_stats.avg_ms.toFixed(1) }}ms</el-descriptions-item>
        <el-descriptions-item label="P50">{{ report.latency_stats.p50_ms.toFixed(1) }}ms</el-descriptions-item>
        <el-descriptions-item label="P95">{{ report.latency_stats.p95_ms.toFixed(1) }}ms</el-descriptions-item>
        <el-descriptions-item label="Max">{{ report.latency_stats.max_ms.toFixed(1) }}ms</el-descriptions-item>
        <el-descriptions-item label="P99">{{ report.latency_stats.p99_ms.toFixed(1) }}ms</el-descriptions-item>
        <el-descriptions-item label="StdDev">{{ report.latency_stats.std_dev_ms.toFixed(1) }}ms</el-descriptions-item>
      </el-descriptions>

      <div v-if="report.raw_latencies?.length" style="height: 350px">
        <v-chart :option="chartOption" autoresize style="height: 100%" />
      </div>

      <div v-if="report.errors?.length" style="margin-top: 12px">
        <h4>错误</h4>
        <div v-for="(err, i) in report.errors" :key="i" style="color: #f56c6c; font-size: 13px">{{ err }}</div>
      </div>
    </el-card>
  </template>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { performanceApi, type PerformanceReport } from '../api/performance'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, TitleComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

use([LineChart, GridComponent, TooltipComponent, TitleComponent, CanvasRenderer])

const testType = ref('latency')
const loading = ref(false)
const report = ref<PerformanceReport | null>(null)

const config = ref({
  tool_name: '',
  arguments_json: '{}',
  iterations: 50,
  warmup: 3,
  concurrency: 5,
  requests_per_worker: 10,
})

function parseArgs() {
  try { return JSON.parse(config.value.arguments_json) } catch { return undefined }
}

async function runLatency() {
  loading.value = true
  try {
    report.value = await performanceApi.latency({
      tool_name: config.value.tool_name,
      arguments: parseArgs(),
      iterations: config.value.iterations,
      warmup: config.value.warmup,
    })
  } finally {
    loading.value = false
  }
}

async function runConcurrency() {
  loading.value = true
  try {
    report.value = await performanceApi.concurrency({
      tool_name: config.value.tool_name,
      arguments: parseArgs(),
      concurrency: config.value.concurrency,
      requests_per_worker: config.value.requests_per_worker,
    })
  } finally {
    loading.value = false
  }
}

const chartOption = computed(() => {
  if (!report.value?.raw_latencies) return {}
  const data = report.value.raw_latencies
  return {
    title: { text: '请求延迟分布', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: data.map((_, i) => i + 1), name: '请求序号' },
    yAxis: { type: 'value', name: '延迟 (ms)' },
    series: [{
      type: 'line',
      data: data,
      smooth: true,
      lineStyle: { width: 1.5 },
      itemStyle: { color: '#409eff' },
    }],
    grid: { left: 60, right: 20, top: 40, bottom: 40 },
  }
})
</script>

<style scoped>
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}
</style>
