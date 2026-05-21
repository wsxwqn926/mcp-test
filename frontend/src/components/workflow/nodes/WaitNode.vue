<script setup lang="ts">
import { Handle, Position } from '@vue-flow/core'
import BaseNode from './BaseNode.vue'

defineProps<{ id: string; data: any }>()
</script>

<template>
  <BaseNode :id="id" :deletable="true">
    <div class="wf-node wait-node">
      <Handle type="target" :position="Position.Left" />
      <div class="node-content">
        <div class="node-title">Wait</div>
        <div class="node-sub">{{ data?.seconds != null ? `${data.seconds}s` : '' }}</div>
      </div>
      <Handle type="source" :position="Position.Right" />
    </div>
  </BaseNode>
</template>

<style scoped>
.wf-node {
  display: flex;
  align-items: center;
  padding: 8px 14px;
  border-radius: 8px;
  background: #fff;
  border-left: 4px solid #909399;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  min-width: 120px;
  max-width: 180px;
  font-size: 13px;
}

.node-content { flex: 1; min-width: 0; }
.node-title { font-weight: 600; color: #303133; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.node-sub { font-size: 11px; color: #909399; margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
</style>
