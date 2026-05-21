<script setup lang="ts">
import { computed } from 'vue'
import { useWorkflowStore } from '../../../stores/workflow'

const props = defineProps<{ modelValue: Record<string, any> }>()
const emit = defineEmits<{ 'update:modelValue': [value: Record<string, any>] }>()

const workflowStore = useWorkflowStore()

const data = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const expression = computed({
  get: () => data.value.expression ?? { variable: '', operator: 'eq', value: '' },
  set: (val) => {
    data.value = { ...data.value, expression: val }
  },
})

function updateField(field: string, value: string) {
  expression.value = { ...expression.value, [field]: value }
}

const variableOptions = computed(() => {
  const builtIn = ['last_result', 'loop_index', 'loop_count']
  const customVars = workflowStore.currentWorkflow?.variables
    ? Object.keys(workflowStore.currentWorkflow.variables)
    : []
  return [...builtIn, ...customVars]
})

const operatorOptions = [
  { value: 'eq', label: '等于' },
  { value: 'ne', label: '不等于' },
  { value: 'gt', label: '大于' },
  { value: 'lt', label: '小于' },
  { value: 'gte', label: '大于等于' },
  { value: 'lte', label: '小于等于' },
  { value: 'contains', label: '包含' },
  { value: 'not_contains', label: '不包含' },
  { value: 'is_empty', label: '为空' },
  { value: 'is_not_empty', label: '不为空' },
]
</script>

<template>
  <el-form label-width="80px">
    <el-form-item label="变量">
      <el-select
        :model-value="expression.variable"
        placeholder="选择变量"
        style="width: 100%"
        @update:model-value="updateField('variable', $event)"
      >
        <el-option
          v-for="v in variableOptions"
          :key="v"
          :label="v"
          :value="v"
        />
      </el-select>
    </el-form-item>
    <el-form-item label="运算符">
      <el-select
        :model-value="expression.operator"
        placeholder="选择运算符"
        style="width: 100%"
        @update:model-value="updateField('operator', $event)"
      >
        <el-option
          v-for="op in operatorOptions"
          :key="op.value"
          :label="op.label"
          :value="op.value"
        />
      </el-select>
    </el-form-item>
    <el-form-item v-if="expression.operator !== 'is_empty' && expression.operator !== 'is_not_empty'" label="值">
      <el-input
        :model-value="expression.value"
        placeholder="比较值"
        @update:model-value="updateField('value', $event)"
      />
    </el-form-item>
    <el-form-item>
      <div class="hint">
        <div>✅ True → 走上方连线</div>
        <div>❌ False → 走下方连线</div>
      </div>
    </el-form-item>
  </el-form>
</template>

<style scoped>
.hint {
  font-size: 12px;
  color: #909399;
  line-height: 1.8;
}
</style>
