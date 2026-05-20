<template>
  <div class="page-header">
    <h2>连接管理</h2>
    <el-button type="primary" size="small" @click="showAddForm">添加连接</el-button>
  </div>

  <el-card v-if="formVisible" class="section-card">
    <template #header>
      <span>{{ editingId ? '修改连接' : '新建连接' }}</span>
    </template>
    <el-form :model="form" label-width="120px" size="default">
      <el-form-item label="名称">
        <el-input v-model="form.name" placeholder="连接名称" />
      </el-form-item>
      <el-form-item label="传输类型">
        <el-radio-group v-model="form.transport_type">
          <el-radio value="stdio">STDIO</el-radio>
          <el-radio value="http">HTTP</el-radio>
          <el-radio value="sse">SSE</el-radio>
        </el-radio-group>
      </el-form-item>

      <template v-if="form.transport_type === 'stdio'">
        <el-form-item label="命令">
          <el-input v-model="form.stdio.command" placeholder="例如 python, node, uvx" />
        </el-form-item>
        <el-form-item label="参数">
          <el-input v-model="stdioArgsText" placeholder="以空格分隔的参数" />
        </el-form-item>
        <el-form-item label="工作目录">
          <el-input v-model="form.stdio.cwd" placeholder="可选" />
        </el-form-item>
      </template>

      <template v-else>
        <el-form-item label="地址">
          <el-input v-model="form.http.url" placeholder="http://..." />
        </el-form-item>
        <el-form-item label="请求头 (JSON)">
          <el-input v-model="httpHeadersText" type="textarea" :rows="4" placeholder='{"Authorization": "Bearer ..."}' />
        </el-form-item>
        <el-form-item label="超时 (秒)">
          <el-input-number v-model="form.http.timeout" :min="5" :max="120" />
        </el-form-item>
      </template>

      <el-form-item>
        <template v-if="editingId">
          <el-button type="primary" @click="saveOnly">保存</el-button>
          <el-button @click="resetForm">取消</el-button>
        </template>
        <template v-else>
          <el-button type="primary" @click="saveAndConnect">保存并连接</el-button>
          <el-button @click="saveOnly">仅保存</el-button>
        </template>
      </el-form-item>
    </el-form>
  </el-card>

  <div class="section-title" style="margin-top: 24px">已保存的连接</div>
  <div v-if="Object.keys(connStore.configs).length === 0" class="empty-state">
    <el-empty description="暂无已保存的连接" :image-size="60" />
  </div>
  <div v-else class="conn-grid">
    <div
      v-for="cfg in Object.values(connStore.configs)"
      :key="cfg.id"
      class="conn-card"
    >
      <div class="conn-card-header">
        <span class="conn-card-name">{{ cfg.name }}</span>
        <el-tag size="small" effect="plain">{{ cfg.transport_type.toUpperCase() }}</el-tag>
      </div>
      <div class="conn-card-detail">{{ getConnectionDetail(cfg) }}</div>
      <div class="conn-card-actions">
        <el-button
          size="small"
          type="primary"
          :disabled="connStore.isConnected && connStore.connectedConfig?.id === cfg.id"
          @click="connectTo(cfg.id)"
        >
          连接
        </el-button>
        <el-button size="small" text @click="editConnection(cfg)">编辑</el-button>
        <el-button size="small" text type="danger" @click="deleteConnection(cfg.id)">删除</el-button>
      </div>
    </div>
  </div>

  <el-card v-if="connStore.isConnected && connStore.serverInfo" class="section-card" style="margin-top: 24px">
    <template #header>
      <span>服务器信息</span>
    </template>
    <el-descriptions :column="2" border>
      <el-descriptions-item label="名称">{{ connStore.serverInfo.name }}</el-descriptions-item>
      <el-descriptions-item label="版本">{{ connStore.serverInfo.version }}</el-descriptions-item>
      <el-descriptions-item label="协议版本">{{ connStore.serverInfo.protocol_version }}</el-descriptions-item>
      <el-descriptions-item label="能力">
        <template v-for="(val, key) in connStore.serverInfo.capabilities" :key="key">
          <el-tag v-if="val" size="small" type="success" style="margin-right: 4px">{{ key }}</el-tag>
        </template>
      </el-descriptions-item>
    </el-descriptions>
  </el-card>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { useConnectionStore } from '../stores/connection'
import type { ServerConfig } from '../api/connections'
import { ElMessage, ElMessageBox } from 'element-plus'

const connStore = useConnectionStore()

const form = reactive({
  name: '',
  transport_type: 'stdio' as 'stdio' | 'http' | 'sse',
  stdio: { command: '', args: [] as string[], cwd: '' },
  http: { url: '', headers: {}, timeout: 30 },
})

const stdioArgsText = ref('')
const httpHeadersText = ref('{}')
const formVisible = ref(false)
const editingId = ref<string | null>(null)

function resetForm() {
  form.name = ''
  form.transport_type = 'stdio'
  form.stdio = { command: '', args: [] as string[], cwd: '' }
  form.http = { url: '', headers: {}, timeout: 30 }
  stdioArgsText.value = ''
  httpHeadersText.value = '{}'
  editingId.value = null
  formVisible.value = false
}

function showAddForm() {
  resetForm()
  formVisible.value = true
}

async function saveAndConnect() {
  const cfg = await buildAndSave()
  if (cfg) await connStore.connect(cfg.id)
}

async function saveOnly() {
  await buildAndSave()
}

async function buildAndSave() {
  const data: any = {
    name: form.name,
    transport_type: form.transport_type,
  }
  if (form.transport_type === 'stdio') {
    data.stdio_config = {
      command: form.stdio.command,
      args: stdioArgsText.value ? stdioArgsText.value.split(/\s+/) : [],
      cwd: form.stdio.cwd || undefined,
    }
  } else {
    let headers = {}
    try { headers = JSON.parse(httpHeadersText.value || '{}') } catch {}
    data.http_config = {
      url: form.http.url,
      headers,
      timeout: form.http.timeout,
    }
  }
  try {
    let cfg
    if (editingId.value) {
      cfg = await connStore.updateConnection(editingId.value, data)
    } else {
      cfg = await connStore.createConnection(data)
    }
    resetForm()
    ElMessage.success('已保存')
    return cfg
  } catch {}
  return null
}

async function connectTo(id: string) {
  await connStore.connect(id)
}

async function deleteConnection(id: string) {
  await ElMessageBox.confirm('确认删除此连接？', '确认')
  await connStore.deleteConnection(id)
  ElMessage.success('已删除')
}

function editConnection(cfg: ServerConfig) {
  resetForm()
  formVisible.value = true
  editingId.value = cfg.id
  form.name = cfg.name
  form.transport_type = cfg.transport_type
  if (cfg.stdio_config) {
    form.stdio.command = cfg.stdio_config.command
    stdioArgsText.value = (cfg.stdio_config.args || []).join(' ')
    form.stdio.cwd = cfg.stdio_config.cwd || ''
  }
  if (cfg.http_config) {
    form.http.url = cfg.http_config.url
    httpHeadersText.value = JSON.stringify(cfg.http_config.headers || {}, null, 2)
    form.http.timeout = cfg.http_config.timeout || 30
  }
}

function getConnectionDetail(cfg: ServerConfig): string {
  if (cfg.stdio_config) return `${cfg.stdio_config.command} ${(cfg.stdio_config.args || []).join(' ')}`
  if (cfg.http_config) return cfg.http_config.url
  return ''
}

onMounted(() => {
  connStore.loadConfigs()
})
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #1d2129;
  margin-bottom: 12px;
}

.empty-state {
  padding: 32px 0;
}

.conn-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 12px;
}

.conn-card {
  background: #fff;
  border: 1px solid #e5e6eb;
  border-radius: var(--card-radius);
  padding: 16px;
  transition: all 0.2s ease;
}

.conn-card:hover {
  border-color: #c9cdd4;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.conn-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.conn-card-name {
  font-size: 15px;
  font-weight: 600;
  color: #1d2129;
}

.conn-card-detail {
  font-size: 13px;
  color: #86909c;
  margin-bottom: 12px;
  word-break: break-all;
  font-family: 'Cascadia Code', 'Consolas', monospace;
  line-height: 1.5;
}

.conn-card-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>
