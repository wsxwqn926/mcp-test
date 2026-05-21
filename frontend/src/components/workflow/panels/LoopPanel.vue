<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ modelValue: Record<string, any> }>()
const emit = defineEmits<{ 'update:modelValue': [value: Record<string, any>] }>()

const data = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const loopType = computed({
  get: () => data.value.loop_type ?? 'count',
  set: (val: string) => {
    data.value = { ...data.value, loop_type: val }
  },
})

const count = computed({
  get: () => data.value.count ?? 1,
  set: (val: number) => {
    data.value = { ...data.value, count: val }
  },
})

const maxIterations = computed({
  get: () => data.value.max_iterations ?? 100,
  set: (val: number) => {
    data.value = { ...data.value, max_iterations: val }
  },
})

const expression = computed({
  get: () => data.value.expression ?? { variable: '', operator: 'eq', value: '' },
  set: (val) => {
    data.value = { ...data.value, expression: val }
  },
})

function updateExprField(field: string, value: string) {
  expression.value = { ...expression.value, [field]: value }
}

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

const variableOptions = ['last_result', 'loop_index', 'loop_count']
</script>

<template>
  <el-form label-width="80px">
    <el-form-item label="循环类型">
      <el-radio-group v-model="loopType">
        <el-radio value="count">固定次数</el-radio>
        <el-radio value="condition">条件循环</el-radio>
      </el-radio-group>
    </el-form-item>

    <el-form-item v-if="loopType === 'count'" label="次数">
      <el-input-number v-model="count" :min="1" />
    </el-form-item>

    <template v-if="loopType === 'condition'">
      <el-form-item label="变量">
        <el-select
          :model-value="expression.variable"
          placeholder="选择变量"
          style="width: 100%"
          @update:model-value="updateExprField('variable', $event)"
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
          @update:model-value="updateExprField('operator', $event)"
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
          @update:model-value="updateExprField('value', $event)"
        />
      </el-form-item>
    </template>

    <el-form-item label="最大迭代">
      <el-input-number v-model="maxIterations" :min="1" :max="10000" />
    </el-form-item>

    <el-form-item>
      <div class="hint">
        <div>内置变量: ${loop_index}, ${loop_count}</div>
      </div>
    </el-form-item>
  </el-form>
</template>

<style scoped>
.hint {
  font-size: 12px;
  color: #909399;
}
</style>
