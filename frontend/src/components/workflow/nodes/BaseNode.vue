<script setup lang="ts">
import { computed } from 'vue'
import { useWorkflowStore } from '../../../stores/workflow'

const props = defineProps<{
  id: string
  deletable?: boolean
}>()

const workflowStore = useWorkflowStore()

const statusClass = computed(() => {
  const status = workflowStore.nodeStatusMap[props.id]
  return status ? `node-${status}` : 'node-idle'
})

function handleDelete(e: MouseEvent) {
  e.stopPropagation()
  if (!workflowStore.currentWorkflow) return
  workflowStore.currentWorkflow = {
    ...workflowStore.currentWorkflow,
    nodes: workflowStore.currentWorkflow.nodes.filter(n => n.id !== props.id),
    edges: workflowStore.currentWorkflow.edges.filter(e => e.source !== props.id && e.target !== props.id),
  }
}
</script>

<template>
  <div class="base-node-wrapper" :class="statusClass">
    <button
      v-if="deletable"
      class="node-delete-btn"
      title="删除节点"
      @click="handleDelete"
    >×</button>
    <slot />
  </div>
</template>

<style scoped>
.base-node-wrapper {
  position: relative;
  transition: all 0.3s ease;
}

.node-delete-btn {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: none;
  background: #f56c6c;
  color: #fff;
  font-size: 12px;
  line-height: 1;
  cursor: pointer;
  display: none;
  align-items: center;
  justify-content: center;
  z-index: 10;
  padding: 0;
}

.base-node-wrapper:hover .node-delete-btn {
  display: flex;
}

.node-delete-btn:hover {
  background: #e6363a;
}

.node-idle {
}

.node-running {
  animation: pulse-blue 1.5s infinite;
}

.node-passed {
  box-shadow: 0 0 8px rgba(103, 194, 58, 0.4);
}

.node-failed {
  box-shadow: 0 0 8px rgba(245, 108, 108, 0.4);
}

.node-error {
  animation: shake 0.5s;
}

.node-skipped {
  opacity: 0.6;
}

@keyframes pulse-blue {
  0% { box-shadow: 0 0 4px rgba(64, 158, 255, 0.3); }
  50% { box-shadow: 0 0 14px rgba(64, 158, 255, 0.6); }
  100% { box-shadow: 0 0 4px rgba(64, 158, 255, 0.3); }
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-4px); }
  75% { transform: translateX(4px); }
}
</style>
