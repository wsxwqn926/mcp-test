<script setup lang="ts">
import { Handle, Position } from '@vue-flow/core'
import BaseNode from './BaseNode.vue'

defineProps<{ id: string; data: any }>()
</script>

<template>
  <BaseNode :id="id" :deletable="true">
    <div class="wf-node condition-node">
      <Handle type="target" :position="Position.Left" />
      <div class="node-content">
        <div class="node-title">🔀 {{ data?.label || '条件判断' }}</div>
        <div class="node-sub">{{ data?.expression?.variable || '' }} {{ data?.expression?.operator || '' }}</div>
      </div>
      <div class="handles-right">
        <div class="handle-group handle-top">
          <span class="handle-label">True</span>
          <Handle id="true" type="source" :position="Position.Right" class="handle-true" />
        </div>
        <div class="handle-group handle-bottom">
          <span class="handle-label">False</span>
          <Handle id="false" type="source" :position="Position.Right" class="handle-false" />
        </div>
      </div>
    </div>
  </BaseNode>
</template>

<style scoped>
.wf-node {
  display: flex;
  align-items: stretch;
  padding: 8px 14px;
  border-radius: 8px;
  background: #fff;
  border-left: 4px solid #f5a623;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  min-width: 140px;
  max-width: 180px;
  font-size: 13px;
}

.node-content { flex: 1; min-width: 0; display: flex; flex-direction: column; justify-content: center; }
.node-title { font-weight: 600; color: #303133; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.node-sub { font-size: 11px; color: #909399; margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.handles-right { display: flex; flex-direction: column; justify-content: space-between; margin-left: 8px; position: relative; }
.handle-group { display: flex; align-items: center; gap: 4px; position: relative; }
.handle-label { font-size: 10px; color: #909399; font-weight: 600; }
</style>
