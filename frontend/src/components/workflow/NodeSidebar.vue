<script setup lang="ts">
const nodeTypes = [
  { type: 'start', icon: '▶', label: '开始' },
  { type: 'end', icon: '⏹', label: '结束' },
  { type: 'tool_call', icon: '🔧', label: '调用工具' },
  { type: 'resource_read', icon: '📄', label: '读取资源' },
  { type: 'prompt_get', icon: '💬', label: '获取提示词' },
  { type: 'assertion', icon: '✅', label: '断言' },
  { type: 'wait', icon: '⏱', label: '等待' },
  { type: 'condition', icon: '🔀', label: '条件判断' },
  { type: 'variable', icon: '📦', label: '变量操作' },
  { type: 'loop', icon: '🔄', label: '循环' },
]

function onDragStart(event: DragEvent, nodeType: string) {
  if (event.dataTransfer) {
    event.dataTransfer.setData('application/vueflow', nodeType)
    event.dataTransfer.effectAllowed = 'move'
  }
}
</script>

<template>
  <div class="node-sidebar">
    <div class="sidebar-title">节点</div>
    <div class="node-list">
      <div
        v-for="item in nodeTypes"
        :key="item.type"
        class="node-item"
        draggable="true"
        @dragstart="onDragStart($event, item.type)"
      >
        <span class="node-icon">{{ item.icon }}</span>
        <span class="node-label">{{ item.label }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.node-sidebar {
  background: #1d1e2c;
  color: #e0e0e0;
  padding: 8px 12px;
  display: flex;
  flex-direction: column;
  user-select: none;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.sidebar-title {
  font-size: 12px;
  font-weight: 600;
  padding: 0 0 6px;
  color: #909399;
}

.node-list {
  display: flex;
  flex-direction: row;
  gap: 6px;
  overflow-x: auto;
}

.node-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: grab;
  font-size: 13px;
  transition: background 0.2s;
  background: rgba(255, 255, 255, 0.06);
  white-space: nowrap;
  flex-shrink: 0;
}

.node-item:hover {
  background: rgba(255, 255, 255, 0.15);
}

.node-item:active {
  cursor: grabbing;
}

.node-icon {
  font-size: 14px;
  flex-shrink: 0;
}

.node-label {
  white-space: nowrap;
}
</style>
