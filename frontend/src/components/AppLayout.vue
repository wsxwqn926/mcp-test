<template>
  <el-container class="app-layout">
    <el-aside width="220px" class="sidebar">
      <div class="sidebar-header">
        <h3>MCP Test</h3>
        <NotificationPanel />
      </div>
      <div class="sidebar-connection">
        <el-select
          v-model="selectedConfigId"
          placeholder="选择服务器"
          size="small"
          clearable
          style="width: 100%"
          @change="onConfigSelect"
        >
          <el-option
            v-for="cfg in Object.values(connStore.configs)"
            :key="cfg.id"
            :label="cfg.name"
            :value="cfg.id"
          >
            <span>{{ cfg.name }}</span>
            <span v-if="isConnected(cfg.id)" style="float: right; color: #67c23a; font-size: 12px">●</span>
          </el-option>
        </el-select>
        <div class="status-line">
          <span :class="['status-dot', stateClass]"></span>
          <span class="status-text">{{ stateLabel }}</span>
          <div class="conn-btns">
            <el-button
              v-if="!connStore.isConnected"
              link
              type="primary"
              size="small"
              :disabled="!selectedConfigId"
              @click="doConnect"
              :loading="connecting"
            >
              连接
            </el-button>
            <template v-else>
              <el-button link type="danger" size="small" @click="doDisconnect">断开</el-button>
              <el-button link type="warning" size="small" @click="doReconnect" :loading="connecting">重连</el-button>
            </template>
          </div>
        </div>
        <div v-if="connStore.connectedServers.length > 1" class="connection-list">
          <div
            v-for="srv in connStore.connectedServers"
            :key="srv.id"
            class="connection-item"
            :class="{ active: srv.id === connStore.primaryId }"
            @click="switchPrimary(srv.id)"
          >
            <span :class="['status-dot', srv.state === 'connected' ? 'connected' : 'disconnected']"></span>
            <span class="conn-name">{{ srv.name || srv.id.slice(0, 8) }}</span>
            <el-tag v-if="srv.id === connStore.primaryId" size="small" type="primary">主</el-tag>
            <el-button link type="danger" size="small" @click.stop="disconnectOne(srv.id)">×</el-button>
          </div>
        </div>
      </div>
      <el-menu
        :default-active="currentRoute"
        router
        class="sidebar-menu"
        background-color="#1d1e2c"
        text-color="#bfcbd9"
        active-text-color="#409eff"
      >
        <el-menu-item index="/connection">
          <el-icon><Link /></el-icon>
          <span>连接管理</span>
        </el-menu-item>
        <el-menu-item index="/tools" :disabled="!connStore.isConnected">
          <el-icon><SetUp /></el-icon>
          <span>工具</span>
        </el-menu-item>
        <el-menu-item index="/resources" :disabled="!connStore.isConnected">
          <el-icon><FolderOpened /></el-icon>
          <span>资源</span>
        </el-menu-item>
        <el-menu-item index="/prompts" :disabled="!connStore.isConnected">
          <el-icon><ChatDotSquare /></el-icon>
          <span>提示词</span>
        </el-menu-item>
        <el-menu-item index="/messages" :disabled="!connStore.isConnected">
          <el-icon><Document /></el-icon>
          <span>消息日志</span>
        </el-menu-item>
        <el-menu-item index="/tests">
          <el-icon><List /></el-icon>
          <span>自动化测试</span>
        </el-menu-item>
        <el-menu-item index="/workflows">
          <el-icon><Share /></el-icon>
          <span>自动化流程</span>
        </el-menu-item>
        <el-menu-item index="/validator" :disabled="!connStore.isConnected">
          <el-icon><CircleCheck /></el-icon>
          <span>协议验证</span>
        </el-menu-item>
        <el-menu-item index="/performance" :disabled="!connStore.isConnected">
          <el-icon><TrendCharts /></el-icon>
          <span>性能测试</span>
        </el-menu-item>
        <el-menu-item index="/compare">
          <el-icon><Connection /></el-icon>
          <span>多服务对比</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-main class="main-content">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useConnectionStore } from '../stores/connection'
import { useWebSocket } from '../composables/useWebSocket'
import NotificationPanel from './NotificationPanel.vue'

const route = useRoute()
const connStore = useConnectionStore()
const { connect: wsConnect } = useWebSocket()

const selectedConfigId = ref<string>('')
const connecting = ref(false)

const currentRoute = computed(() => route.path)

const stateClass = computed(() => {
  const s = connStore.status.state
  if (s === 'connected') return 'connected'
  if (s === 'error') return 'error'
  if (s === 'connecting' || s === 'initializing') return 'connecting'
  return 'disconnected'
})

const stateLabel = computed(() => {
  const s = connStore.status.state
  const map: Record<string, string> = {
    disconnected: '未连接',
    connecting: '连接中...',
    initializing: '初始化中...',
    connected: '已连接',
    disconnecting: '断开中...',
    error: '错误',
  }
  return map[s] || s
})

function isConnected(configId: string) {
  return connStore.connectedServers.some(s => s.id === configId && s.state === 'connected')
}

async function onConfigSelect(newId: string) {
  if (!newId) return
  if (isConnected(newId)) {
    await connStore.setPrimary(newId)
    return
  }
  connecting.value = true
  try {
    await connStore.connect(newId)
  } finally {
    connecting.value = false
  }
}

async function doConnect() {
  if (!selectedConfigId.value) return
  connecting.value = true
  try {
    await connStore.connect(selectedConfigId.value)
  } finally {
    connecting.value = false
  }
}

async function doDisconnect() {
  await connStore.disconnect()
}

async function doReconnect() {
  if (!selectedConfigId.value) return
  connecting.value = true
  try {
    await connStore.disconnect()
    await connStore.connect(selectedConfigId.value)
  } finally {
    connecting.value = false
  }
}

async function switchPrimary(id: string) {
  await connStore.setPrimary(id)
  selectedConfigId.value = id
}

async function disconnectOne(id: string) {
  await connStore.disconnectOne(id)
}

onMounted(async () => {
  wsConnect()
  await connStore.loadConfigs()
  await connStore.refreshStatus()
  const cfg = connStore.status.config
  if (cfg) {
    selectedConfigId.value = cfg.id
  }
})

watch(() => connStore.connectedConfig, (cfg) => {
  if (cfg) {
    selectedConfigId.value = cfg.id
  }
})
</script>

<style scoped>
.app-layout {
  height: 100vh;
}

.sidebar {
  background: var(--sidebar-bg);
  color: var(--sidebar-text);
  border-right: none;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.sidebar-header {
  padding: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.sidebar-header h3 {
  margin: 0;
  font-size: 16px;
  color: #fff;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.sidebar-connection {
  padding: 12px 16px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.connection-list {
  margin-top: 8px;
  max-height: 150px;
  overflow-y: auto;
}

.connection-item {
  display: flex;
  align-items: center;
  font-size: 12px;
  color: var(--sidebar-text);
  padding: 4px 6px;
  border-radius: 4px;
  cursor: pointer;
  gap: 4px;
}

.connection-item:hover {
  background: rgba(255,255,255,0.06);
}

.connection-item.active {
  background: rgba(64, 158, 255, 0.12);
}

.conn-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status-line {
  margin-top: 8px;
  display: flex;
  align-items: center;
  font-size: 13px;
  color: var(--sidebar-text);
}
.status-text {
  margin-left: 4px;
}

.conn-btns {
  margin-left: auto;
  display: flex;
  gap: 2px;
}

.sidebar-menu {
  border-right: none;
  flex: 1;
  background: transparent;
}

.sidebar-menu .el-menu-item {
  color: var(--sidebar-text);
  height: 42px;
  line-height: 42px;
  font-size: 13px;
}
.sidebar-menu .el-menu-item:hover {
  background: rgba(255,255,255,0.04);
  color: #fff;
}
.sidebar-menu .el-menu-item.is-active {
  background: rgba(64, 158, 255, 0.12);
  color: var(--sidebar-active);
  border-right: 2px solid var(--sidebar-active);
}
.sidebar-menu .el-menu-item.is-disabled {
  opacity: 0.35;
}

.main-content {
  background: #f0f2f5;
  overflow-y: auto;
  padding: 24px 28px;
}
</style>
