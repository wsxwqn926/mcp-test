<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useWorkflowStore } from '../../stores/workflow'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  confirm: [variables: Record<string, any>]
}>()

const workflowStore = useWorkflowStore()

const inputParams = computed(() => {
  if (!workflowStore.currentWorkflow) return []
  const startNode = workflowStore.currentWorkflow.nodes.find(n => n.type === 'start')
  if (!startNode) return []
  return (startNode.data._input_mappings ?? []).filter((m: any) => m.variable_name)
})

const formValues = ref<Record<string, any>>({})

watch(() => props.visible, (v) => {
  if (v) {
    const vals: Record<string, any> = {}
    for (const p of inputParams.value) {
      vals[p.variable_name] = p.value ?? ''
    }
    formValues.value = vals
  }
})

function handleConfirm() {
  emit('confirm', { ...formValues.value })
  emit('update:visible', false)
}

function handleCancel() {
  emit('update:visible', false)
}
</script>

<template>
  <el-dialog
    :model-value="visible"
    title="运行参数"
    width="480px"
    @update:model-value="emit('update:visible', $event)"
  >
    <template v-if="inputParams.length === 0">
      <div class="empty-hint">开始节点未定义输入参数</div>
    </template>
    <template v-else>
      <div class="run-desc">请确认或修改运行参数：</div>
      <el-form label-width="120px">
        <el-form-item
          v-for="p in inputParams"
          :key="p.variable_name"
          :label="p.variable_name"
        >
          <el-input
            v-model="formValues[p.variable_name]"
            :placeholder="`默认值: ${p.value || '(空)'}`"
          />
        </el-form-item>
      </el-form>
    </template>

    <template #footer>
      <el-button @click="handleCancel">取消</el-button>
      <el-button type="primary" @click="handleConfirm">运行</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.empty-hint {
  text-align: center;
  color: #909399;
  padding: 20px 0;
  font-size: 14px;
}

.run-desc {
  font-size: 13px;
  color: #606266;
  margin-bottom: 16px;
}
</style>
