<script setup lang="ts">
import { computed } from 'vue'
import { useWorkflowStore } from '../../stores/workflow'
import type { NodeResult } from '../../api/workflows'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
}>()

const workflowStore = useWorkflowStore()

const result = computed(() => workflowStore.runResult)

const statusIcon = computed(() => {
  if (!result.value) return ''
  return result.value.status === 'passed' ? '✅' : '❌'
})

const statusText = computed(() => {
  if (!result.value) return ''
  const map: Record<string, string> = {
    passed: '通过',
    failed: '失败',
    error: '错误',
    stopped: '已停止',
  }
  return map[result.value.status] || result.value.status
})

const durationText = computed(() => {
  if (!result.value) return ''
  const ms = result.value.duration_ms
  return ms >= 1000 ? `${(ms / 1000).toFixed(2)}s` : `${ms}ms`
})

const nodeResults = computed(() => {
  if (!result.value?.node_results) return []
  return Object.entries(result.value.node_results).map(([id, nr]) => ({
    id,
    ...(nr as NodeResult),
  }))
})

function formatResponse(response: any): string {
  if (!response) return ''
  if (response.content && Array.isArray(response.content)) {
    const parts: string[] = []
    for (const item of response.content) {
      if (item.type === 'text' && item.text) {
        let text = item.text
        try {
          const parsed = JSON.parse(text)
          text = JSON.stringify(parsed, null, 2)
        } catch {}
        parts.push(text)
      } else if (item.type === 'image' && item.data) {
        parts.push(`[Image: ${item.mimeType || 'unknown'}]`)
      } else if (item.type === 'resource' && item.resource) {
        parts.push(JSON.stringify(item.resource, null, 2))
      } else {
        parts.push(JSON.stringify(item, null, 2))
      }
    }
    const meta: any = { ...response }
    delete meta.content
    if (Object.keys(meta).length > 0) {
      parts.push(`---\n${JSON.stringify(meta, null, 2)}`)
    }
    return parts.join('\n\n')
  }
  return JSON.stringify(response, null, 2)
}

function nodeDuration(ms: number) {
  return ms >= 1000 ? `${(ms / 1000).toFixed(2)}s` : `${ms}ms`
}

function nodeStatusType(status: string) {
  const map: Record<string, string> = {
    passed: 'success',
    failed: 'danger',
    error: 'danger',
    running: 'warning',
    skipped: 'info',
  }
  return map[status] || 'info'
}

function nodeTypeIcon(type: string) {
  const map: Record<string, string> = {
    start: '▶',
    end: '⏹',
    tool_call: '🔧',
    resource_read: '📄',
    prompt_get: '💬',
    assertion: '✅',
    wait: '⏱',
    condition: '🔀',
    variable: '📦',
    loop: '🔄',
  }
  return map[type] || '📌'
}
</script>

<template>
  <el-dialog
    :model-value="visible"
    title="运行结果"
    width="720px"
    top="6vh"
    @update:model-value="emit('update:visible', $event)"
  >
    <template v-if="!result">
      <div class="empty-hint">暂无运行结果</div>
    </template>
    <template v-else>
      <div class="summary">
        <span class="summary-icon">{{ statusIcon }}</span>
        <span class="summary-status">{{ statusText }}</span>
        <span class="summary-divider">|</span>
        <span class="summary-duration">耗时 {{ durationText }}</span>
        <span class="summary-divider">|</span>
        <span class="summary-count">{{ nodeResults.length }} 个节点</span>
      </div>

      <el-collapse class="result-collapse">
        <el-collapse-item
          v-for="nr in nodeResults"
          :key="nr.id"
          :name="nr.id"
        >
          <template #title>
            <div class="node-result-title">
              <span class="nr-icon">{{ nodeTypeIcon(nr.node_type) }}</span>
              <span class="nr-label">{{ nr.node_label || nr.node_type }}</span>
              <el-tag :type="nodeStatusType(nr.status)" size="small" class="nr-badge">
                {{ nr.status }}
              </el-tag>
              <span class="nr-duration">{{ nodeDuration(nr.duration_ms) }}</span>
            </div>
          </template>
          <div class="node-result-content">
            <div v-if="nr.request" class="result-block">
              <div class="block-label">Request</div>
              <pre class="json-block">{{ JSON.stringify(nr.request, null, 2) }}</pre>
            </div>
            <div v-if="nr.response" class="result-block">
              <div class="block-label">Response</div>
              <pre class="json-block formatted">{{ formatResponse(nr.response) }}</pre>
            </div>
            <div v-if="nr.error_message" class="result-block">
              <div class="block-label error">Error</div>
              <pre class="json-block error">{{ nr.error_message }}</pre>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>

      <div v-if="result.variables_snapshot && Object.keys(result.variables_snapshot).length" class="snapshot-section">
        <div class="snapshot-title">变量快照</div>
        <div class="snapshot-grid">
          <div
            v-for="(val, key) in result.variables_snapshot"
            :key="key"
            class="snapshot-item"
          >
            <span class="snapshot-key">{{ key }}</span>
            <span class="snapshot-value">{{ typeof val === 'object' ? JSON.stringify(val) : val }}</span>
          </div>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<style scoped>
.empty-hint {
  text-align: center;
  color: #909399;
  padding: 40px 0;
  font-size: 14px;
}

.summary {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  font-size: 14px;
  color: #303133;
}

.summary-icon {
  font-size: 18px;
}

.summary-status {
  font-weight: 600;
}

.summary-divider {
  color: #dcdfe6;
}

.summary-duration,
.summary-count {
  color: #606266;
}

.result-collapse {
  border: none;
  max-height: 50vh;
  overflow-y: auto;
}

.node-result-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.nr-icon {
  font-size: 14px;
}

.nr-label {
  font-weight: 500;
  color: #303133;
}

.nr-badge {
  margin-left: 4px;
}

.nr-duration {
  color: #909399;
  font-size: 12px;
}

.node-result-content {
  padding: 4px 0;
}

.result-block {
  margin-bottom: 8px;
}

.block-label {
  font-size: 12px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 4px;
}

.block-label.error {
  color: #f56c6c;
}

.json-block {
  background: #f5f7fa;
  border-radius: 4px;
  padding: 8px;
  font-size: 12px;
  overflow-x: auto;
  max-height: 200px;
  overflow-y: auto;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
}

.json-block.error {
  background: #fef0f0;
  color: #f56c6c;
}

.snapshot-section {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #ebeef5;
}

.snapshot-title {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.snapshot-grid {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.snapshot-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.snapshot-key {
  color: #409eff;
  font-weight: 500;
  min-width: 100px;
}

.snapshot-value {
  color: #606266;
  word-break: break-all;
}
</style>
