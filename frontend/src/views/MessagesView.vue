<template>
  <div class="page-header">
    <h2>消息日志</h2>
  </div>

  <div class="stats-row">
    <div class="stat-card">
      <div class="stat-value">{{ msgStore.stats.total }}</div>
      <div class="stat-label">总数</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">{{ msgStore.stats.requests }}</div>
      <div class="stat-label">请求</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">{{ msgStore.stats.responses }}</div>
      <div class="stat-label">响应</div>
    </div>
    <div class="stat-card">
      <div class="stat-value" style="color: var(--danger-color)">{{ msgStore.stats.errors }}</div>
      <div class="stat-label">错误</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">{{ msgStore.stats.avg_duration_ms.toFixed(0) }}<span class="stat-unit">ms</span></div>
      <div class="stat-label">平均耗时</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">{{ msgStore.stats.max_duration_ms.toFixed(0) }}<span class="stat-unit">ms</span></div>
      <div class="stat-label">最大耗时</div>
    </div>
  </div>

  <el-card class="section-card" style="margin-top: 16px">
    <template #header>
      <div class="action-bar">
        <el-select v-model="filterDirection" placeholder="方向" clearable size="small" style="width: 120px">
          <el-option label="Request" value="request" />
          <el-option label="Response" value="response" />
          <el-option label="Notification" value="notification" />
        </el-select>
        <el-input v-model="filterMethod" placeholder="方法过滤" clearable size="small" style="width: 140px" />
        <el-input v-model="filterSearch" placeholder="搜索内容..." clearable size="small" style="width: 160px" />
        <el-button size="small" @click="applyFilter">应用</el-button>
        <div class="spacer" />
        <el-button size="small" @click="msgStore.exportJson">导出JSON</el-button>
        <el-button size="small" @click="msgStore.exportCsv">导出CSV</el-button>
        <el-button size="small" type="danger" @click="msgStore.clearMessages">清空</el-button>
      </div>
    </template>

    <el-collapse v-model="expandedMsgs">
      <el-collapse-item
        v-for="msg in displayedMessages"
        :key="msg.id"
        :name="msg.id"
      >
        <template #title>
          <span style="display: flex; align-items: center; gap: 8px; width: 100%">
            <span :style="{ color: directionColor(msg.direction) }">{{ directionIcon(msg.direction) }}</span>
            <span style="color: #86909c; font-size: 12px">{{ formatTime(msg.timestamp) }}</span>
            <span style="font-weight: 500">{{ msg.method || '-' }}</span>
            <el-tag v-if="msg.request_id" size="small" type="info">id:{{ msg.request_id }}</el-tag>
            <span v-if="msg.duration_ms" style="color: #86909c; font-size: 12px">{{ msg.duration_ms.toFixed(0) }}ms</span>
            <el-tag v-if="msg.error" size="small" type="danger">Error</el-tag>
          </span>
        </template>
        <pre class="json-viewer">{{ JSON.stringify(msg.data, null, 2) }}</pre>
      </el-collapse-item>
    </el-collapse>
    <el-empty v-if="displayedMessages.length === 0" description="暂无消息" />
  </el-card>

  <el-card class="section-card" style="margin-top: 16px">
    <template #header>
      <div class="action-bar">
        <span style="font-weight: 600">历史记录</span>
        <div class="spacer" />
        <el-button size="small" @click="loadHistoryList" :loading="historyLoading">刷新</el-button>
      </div>
    </template>

    <div v-if="activeHistoryFile" style="margin-bottom: 12px">
      <el-button size="small" @click="closeHistory">&larr; 返回列表</el-button>
      <span style="margin-left: 8px; color: #86909c">{{ activeHistoryFile }}</span>
    </div>

    <el-table
      v-if="!activeHistoryFile"
      :data="historyFiles"
      stripe
      size="small"
      v-loading="historyLoading"
      @row-click="loadHistoryFile"
      style="cursor: pointer"
    >
      <el-table-column prop="name" label="文件名" />
      <el-table-column prop="size" label="大小" width="120">
        <template #default="{ row }">{{ formatSize(row.size) }}</template>
      </el-table-column>
      <el-table-column prop="modified" label="修改时间" width="200">
        <template #default="{ row }">{{ new Date(row.modified).toLocaleString('zh-CN', { hour12: false }) }}</template>
      </el-table-column>
    </el-table>

    <el-empty v-if="!activeHistoryFile && historyFiles.length === 0 && !historyLoading" description="暂无历史记录" />
  </el-card>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useMessageStore } from '../stores/messages'
import { useConnectionStore } from '../stores/connection'
import { messagesApi, type MessageLog } from '../api/messages'

const connStore = useConnectionStore()
const msgStore = useMessageStore()

const filterDirection = ref('')
const filterMethod = ref('')
const filterSearch = ref('')
const expandedMsgs = ref<string[]>([])

const historyFiles = ref<Array<{ name: string; size: number; modified: string }>>([])
const historyLoading = ref(false)
const activeHistoryFile = ref<string | null>(null)
const historyMessages = ref<MessageLog[]>([])

const displayedMessages = computed(() => {
  if (activeHistoryFile.value) {
    return historyMessages.value.slice(0, 200)
  }
  return msgStore.messages.slice(0, 200)
})

function directionIcon(d: string) {
  if (d === 'request') return '\u2192'
  if (d === 'response') return '\u2190'
  return '\u2194'
}

function directionColor(d: string) {
  if (d === 'request') return '#409eff'
  if (d === 'response') return '#67c23a'
  return '#e6a23c'
}

function formatTime(ts: string) {
  return new Date(ts).toLocaleTimeString('zh-CN', { hour12: false, fractionalSecondDigits: 3 })
}

function formatSize(bytes: number) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

async function applyFilter() {
  await msgStore.loadMessages({
    direction: filterDirection.value || undefined,
    method: filterMethod.value || undefined,
    search_text: filterSearch.value || undefined,
  })
}

async function loadHistoryList() {
  historyLoading.value = true
  try {
    const res = await messagesApi.history()
    historyFiles.value = res.files
  } finally {
    historyLoading.value = false
  }
}

async function loadHistoryFile(row: { name: string }) {
  historyLoading.value = true
  try {
    const data = await messagesApi.getHistory(row.name)
    historyMessages.value = Array.isArray(data) ? data : []
    activeHistoryFile.value = row.name
    expandedMsgs.value = []
  } finally {
    historyLoading.value = false
  }
}

function closeHistory() {
  activeHistoryFile.value = null
  historyMessages.value = []
  expandedMsgs.value = []
}

watch(() => connStore.isConnected, (v) => {
  if (v) {
    msgStore.loadMessages()
    msgStore.loadStats()
  }
}, { immediate: true })

loadHistoryList()
</script>

<style scoped>
.stats-row {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 12px;
}

.stat-unit {
  font-size: 13px;
  font-weight: 400;
  color: #86909c;
  margin-left: 2px;
}
</style>
