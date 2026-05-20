<template>
  <div class="page-header">
    <h2>协议验证</h2>
  </div>

  <el-card class="section-card">
    <el-button
      type="primary"
      @click="runValidation"
      :loading="loading"
      :disabled="!connStore.isConnected"
    >
      开始验证
    </el-button>
  </el-card>

  <template v-if="report">
    <el-card class="section-card" style="margin-top: 16px">
      <template #header>
        <div class="action-bar">
          <span style="font-weight: 600">验证报告</span>
          <el-tag :type="overallTagType" size="large">{{ report.overall_status }}</el-tag>
          <span style="color: #86909c; font-size: 13px">{{ report.server_name }} v{{ report.server_version }}</span>
        </div>
      </template>

      <div class="stats-row" style="margin-bottom: 16px">
        <div class="stat-card">
          <div class="stat-value">{{ report.total_checks }}</div>
          <div class="stat-label">检查总数</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" style="color: var(--success-color)">{{ report.passed }}</div>
          <div class="stat-label">通过</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" style="color: var(--danger-color)">{{ report.failed }}</div>
          <div class="stat-label">失败</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" style="color: var(--warning-color)">{{ report.warnings }}</div>
          <div class="stat-label">警告</div>
        </div>
      </div>

      <el-table :data="categorizedResults" stripe>
        <el-table-column prop="category" label="分类" width="160" />
        <el-table-column prop="check_id" label="检查项" width="200" />
        <el-table-column prop="description" label="描述" min-width="250" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="checkTagType(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="details" label="详情" min-width="200" />
      </el-table>
    </el-card>
  </template>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { validatorApi, type ValidationReport } from '../api/validator'
import { useConnectionStore } from '../stores/connection'

const connStore = useConnectionStore()
const loading = ref(false)
const report = ref<ValidationReport | null>(null)

const overallTagType = computed(() => {
  if (!report.value) return 'info'
  const s = report.value.overall_status
  if (s === 'compliant') return 'success'
  if (s === 'partial') return 'warning'
  return 'danger'
})

const categorizedResults = computed(() => report.value?.results || [])

function checkTagType(status: string) {
  if (status === 'passed') return 'success'
  if (status === 'failed') return 'danger'
  if (status === 'warning') return 'warning'
  return 'info'
}

async function runValidation() {
  loading.value = true
  try {
    report.value = await validatorApi.run()
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}
</style>
