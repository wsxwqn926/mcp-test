<template>
  <div class="page-header">
    <h2>多服务对比</h2>
  </div>

  <el-card class="section-card">
    <template #header>
      <div class="action-bar">
        <span>连接管理</span>
        <div class="spacer" />
        <el-button type="primary" size="small" @click="loadCompare" :loading="loading">刷新对比</el-button>
      </div>
    </template>
    <p style="color:#86909c;font-size:13px;margin:0 0 16px">主连接通过侧边栏建立，其他连接在此处添加为副连接进行对比。</p>

    <div class="action-bar" style="margin-bottom:16px">
      <el-select v-model="selectedSecondary" placeholder="选择服务器" size="small" style="width:200px">
        <el-option
          v-for="cfg in availableForSecondary"
          :key="cfg.id"
          :label="cfg.name"
          :value="cfg.id"
        />
      </el-select>
      <el-button size="small" type="primary" @click="addSecondary" :disabled="!selectedSecondary" :loading="connecting">添加副连接</el-button>
    </div>

    <el-table :data="secondaries" stripe>
      <el-table-column prop="name" label="名称" />
      <el-table-column label="类型" width="100">
        <template #default="{ row }"><el-tag size="small">{{ row.transport }}</el-tag></template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }"><el-tag size="small" type="success">已连接</el-tag></template>
      </el-table-column>
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button size="small" type="danger" text @click="removeSecondary(row.id)">断开</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>

  <el-card v-if="compareData" class="section-card" style="margin-top:16px">
    <template #header><span style="font-weight: 600">工具对比</span></template>
    <el-row :gutter="16">
      <el-col v-for="(data, key) in compareData" :key="key" :span="Math.max(6, 24 / Object.keys(compareData).length)">
        <div class="compare-card">
          <div class="compare-header">
            <strong>{{ getConfigName(data.config_id) }}</strong>
            <el-tag v-if="key === 'primary'" size="small" style="margin-left:4px">主</el-tag>
            <el-tag v-else size="small" type="warning" style="margin-left:4px">副</el-tag>
          </div>
          <div v-if="data.error" style="color:#f56c6c">{{ data.error }}</div>
          <div v-else-if="data.tools" style="margin-top:8px">
            <el-tag v-for="t in data.tools" :key="t.name" size="small" style="margin:2px">{{ t.name }}</el-tag>
            <div v-if="!data.tools.length" style="color:#86909c">无工具</div>
          </div>
        </div>
      </el-col>
    </el-row>
  </el-card>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useConnectionStore } from '../stores/connection'
import { connectionsApi, type ServerConfig } from '../api/connections'
import { ElMessage } from 'element-plus'

const connStore = useConnectionStore()
const selectedSecondary = ref('')
const connecting = ref(false)
const loading = ref(false)
const secondaries = ref<Array<{id:string;name:string;transport:string}>>([])
const compareData = ref<Record<string, any> | null>(null)

const availableForSecondary = computed(() => {
  const primaryId = connStore.connectedConfig?.id
  const secondaryIds = new Set(secondaries.value.map(s => s.id))
  return Object.values(connStore.configs).filter(c => c.id !== primaryId && !secondaryIds.has(c.id))
})

function getConfigName(id: string | null) {
  if (!id) return '未知'
  return connStore.configs[id]?.name || id
}

async function addSecondary() {
  if (!selectedSecondary.value) return
  connecting.value = true
  try {
    await connectionsApi.connectSecondary(selectedSecondary.value)
    const cfg = connStore.configs[selectedSecondary.value]
    secondaries.value.push({ id: cfg.id, name: cfg.name, transport: cfg.transport_type.toUpperCase() })
    ElMessage.success(`已添加副连接: ${cfg.name}`)
    selectedSecondary.value = ''
    await loadCompare()
  } finally {
    connecting.value = false
  }
}

async function removeSecondary(id: string) {
  await connectionsApi.disconnectSecondary(id)
  secondaries.value = secondaries.value.filter(s => s.id !== id)
  ElMessage.success('已断开副连接')
  await loadCompare()
}

async function loadCompare() {
  loading.value = true
  try {
    compareData.value = await connectionsApi.compare()
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (connStore.isConnected) loadCompare()
})
</script>

<style scoped>
.compare-card {
  background: #f8f9fb;
  border-radius: var(--card-radius);
  padding: 16px;
}
.compare-header {
  display: flex;
  align-items: center;
}
</style>
