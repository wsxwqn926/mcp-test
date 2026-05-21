<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ modelValue: Record<string, any> }>()
const emit = defineEmits<{ 'update:modelValue': [value: Record<string, any>] }>()

const data = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const action = computed({
  get: () => data.value.action ?? 'set',
  set: (val: string) => {
    data.value = { ...data.value, action: val }
  },
})

const variableName = computed({
  get: () => data.value.variable_name ?? '',
  set: (val: string) => {
    data.value = { ...data.value, variable_name: val }
  },
})

const valueSource = computed({
  get: () => data.value.value_source ?? 'last_result',
  set: (val: string) => {
    data.value = { ...data.value, value_source: val }
  },
})

const valuePath = computed({
  get: () => data.value.value_path ?? '',
  set: (val: string) => {
    data.value = { ...data.value, value_path: val }
  },
})

const literalValue = computed({
  get: () => data.value.literal_value ?? '',
  set: (val: string) => {
    data.value = { ...data.value, literal_value: val }
  },
})

const valueSourceOptions = [
  { value: 'last_result', label: '上一步结果' },
  { value: 'literal', label: '字面量' },
  { value: 'variable', label: '变量' },
]
</script>

<template>
  <el-form label-width="80px">
    <el-form-item label="操作">
      <el-radio-group v-model="action">
        <el-radio value="set">设置变量</el-radio>
        <el-radio value="get">读取变量</el-radio>
      </el-radio-group>
    </el-form-item>
    <el-form-item label="变量名">
      <el-input v-model="variableName" placeholder="变量名称" />
    </el-form-item>
    <el-form-item v-if="action === 'set'" label="值来源">
      <el-select v-model="valueSource" placeholder="选择值来源" style="width: 100%">
        <el-option
          v-for="opt in valueSourceOptions"
          :key="opt.value"
          :label="opt.label"
          :value="opt.value"
        />
      </el-select>
    </el-form-item>
    <el-form-item v-if="action === 'set' && valueSource === 'last_result'" label="路径">
      <el-input v-model="valuePath" placeholder="如 result.data.name" />
    </el-form-item>
    <el-form-item v-if="action === 'set' && valueSource === 'literal'" label="字面量">
      <el-input v-model="literalValue" placeholder="输入字面量值" />
    </el-form-item>
  </el-form>
</template>

<style scoped>
</style>
