<script setup lang="ts">
import { computed } from 'vue'
import { useWorkflowStore } from '../../stores/workflow'
import { ElMessageBox } from 'element-plus'

const emit = defineEmits<{
  run: []
  stop: []
  save: []
  create: []
  delete: []
  showResult: []
}>()

const workflowStore = useWorkflowStore()

const hasNodes = computed(() => {
  return (workflowStore.currentWorkflow?.nodes?.length ?? 0) > 0
})

const hasResult = computed(() => !!workflowStore.runResult)

const resultHighlight = computed(() => !!workflowStore.runResult && !workflowStore.isRunning && !workflowStore.resultViewed)

const workflowList = computed(() => {
  return Object.values(workflowStore.workflows)
})

const selectedId = computed({
  get: () => workflowStore.currentWorkflow?.id || '',
  set: (id: string) => {
    if (id && workflowStore.workflows[id]) {
      workflowStore.currentWorkflow = workflowStore.workflows[id]
    }
  },
})

async function onDelete() {
  const wf = workflowStore.currentWorkflow
  if (!wf) return
  await ElMessageBox.confirm(`确定删除流程「${wf.name}」？`, '删除', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning',
  })
  emit('delete')
}
</script>

<template>
  <div class="run-toolbar">
    <div class="toolbar-actions">
      <el-button
        type="primary"
        :disabled="workflowStore.isRunning || !hasNodes"
        @click="emit('run')"
      >
        ▶ 运行
      </el-button>
      <el-button
        type="danger"
        :disabled="!workflowStore.isRunning"
        @click="emit('stop')"
      >
        ⏹ 停止
      </el-button>
      <el-button type="success" @click="emit('save')">
        💾 保存
      </el-button>
      <el-button @click="emit('create')">
        新建
      </el-button>
      <el-button
        type="danger"
        plain
        :disabled="!workflowStore.currentWorkflow"
        @click="onDelete"
      >
        删除流程
      </el-button>
      <el-button
        :disabled="!hasResult"
        :class="{ 'result-flash': resultHighlight }"
        @click="emit('showResult')"
      >
        📊 运行结果
      </el-button>
    </div>
    <div class="toolbar-spacer" />
    <el-select
      v-model="selectedId"
      placeholder="选择流程"
      size="small"
      style="width: 200px"
      clearable
    >
      <el-option
        v-for="wf in workflowList"
        :key="wf.id"
        :label="wf.name"
        :value="wf.id"
      />
    </el-select>
  </div>
</template>

<style scoped>
.run-toolbar {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  gap: 12px;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toolbar-spacer {
  flex: 1;
}

.result-flash {
  animation: btn-flash 1s ease-in-out infinite;
  color: #409eff !important;
  border-color: #409eff !important;
}

@keyframes btn-flash {
  0%, 100% { box-shadow: 0 0 4px rgba(64, 158, 255, 0.3); }
  50% { box-shadow: 0 0 12px rgba(64, 158, 255, 0.7); }
}
</style>
