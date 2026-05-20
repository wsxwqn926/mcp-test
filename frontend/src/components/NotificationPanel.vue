<template>
  <el-popover placement="bottom" :width="400" trigger="click">
    <template #reference>
      <el-badge :value="notifStore.unreadCount" :hidden="notifStore.unreadCount === 0" :max="99">
        <el-button :icon="Bell" circle size="small" />
      </el-badge>
    </template>
    <div class="notif-header">
      <span>通知</span>
      <el-button link size="small" @click="notifStore.clear()">清空</el-button>
    </div>
    <el-scrollbar max-height="300px">
      <div v-for="n in notifStore.recentNotifications" :key="n.id" class="notif-item">
        <div class="notif-title">
          <el-tag :type="n.type" size="small" style="margin-right: 4px">{{ typeLabel(n.type) }}</el-tag>
          <span>{{ n.title }}</span>
        </div>
        <div class="notif-time">{{ formatTime(n.timestamp) }}</div>
      </div>
      <el-empty v-if="notifStore.notifications.length === 0" description="暂无通知" :image-size="40" />
    </el-scrollbar>
  </el-popover>
</template>

<script setup lang="ts">
import { Bell } from '@element-plus/icons-vue'
import { useNotificationStore } from '../stores/notification'

const notifStore = useNotificationStore()

function typeLabel(type: string) {
  const map: Record<string, string> = { info: '信息', warning: '警告', error: '错误', success: '成功' }
  return map[type] || type
}

function formatTime(ts: string) {
  return new Date(ts).toLocaleTimeString('zh-CN', { hour12: false })
}
</script>

<style scoped>
.notif-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-weight: 600;
}
.notif-item {
  padding: 6px 0;
  border-bottom: 1px solid #f0f0f0;
}
.notif-item:last-child {
  border-bottom: none;
}
.notif-title {
  font-size: 13px;
}
.notif-time {
  font-size: 11px;
  color: #999;
  margin-top: 2px;
}
</style>
