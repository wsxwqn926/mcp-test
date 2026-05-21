<script setup lang="ts">
import { Handle, Position } from '@vue-flow/core'
import BaseNode from './BaseNode.vue'

defineProps<{ id: string; data: any }>()
</script>

<template>
  <BaseNode :id="id" :deletable="false">
    <div class="wf-node end-node">
      <Handle type="target" :position="Position.Left" />
      <div class="node-icon">⏹</div>
      <div class="node-label">结束</div>
    </div>
  </BaseNode>
</template>

<style scoped>
.wf-node {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border-radius: 8px;
  background: #fff;
  border-left: 4px solid #f56c6c;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  min-width: 80px;
  max-width: 120px;
  font-size: 13px;
}

.node-icon { font-size: 14px; color: #f56c6c; }
.node-label { font-weight: 600; color: #303133; white-space: nowrap; }
</style>
