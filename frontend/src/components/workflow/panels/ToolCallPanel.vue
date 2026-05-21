<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useConnectionStore } from '../../../stores/connection'
import { useToolStore } from '../../../stores/tools'
import { useWorkflowStore } from '../../../stores/workflow'
import type { ToolInfo } from '../../../api/tools'

const props = defineProps<{ modelValue: Record<string, any> }>()
const emit = defineEmits<{ 'update:modelValue': [value: Record<string, any>] }>()

const connectionStore = useConnectionStore()
const toolStore = useToolStore()
const workflowStore = useWorkflowStore()

const data = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const configId = computed({
  get: () => data.value.config_id ?? '',
  set: (val: string) => {
    data.value = { ...data.value, config_id: val, tool_name: '', arguments: {} }
  },
})

const toolName = computed({
  get: () => data.value.tool_name ?? '',
  set: (val: string) => {
    data.value = { ...data.value, tool_name: val, arguments: {} }
  },
})

const selectedTool = computed<ToolInfo | null>(() => {
  if (!toolName.value) return null
  return toolStore.tools.find(t => t.name === toolName.value) ?? null
})

const schemaProps = computed(() => {
  const schema = selectedTool.value?.inputSchema
  if (!schema?.properties) return []
  const required = schema.required ?? []
  return Object.entries(schema.properties).map(([key, prop]: [string, any]) => ({
    key,
    type: prop.type ?? 'string',
    description: prop.description ?? '',
    required: required.includes(key),
    enum: prop.enum ?? undefined,
    default: prop.default ?? undefined,
  }))
})

const showSchemaForm = computed(() => schemaProps.value.length > 0)

const knownVars = computed(() => {
  const vars = new Set<string>()
  vars.add('last_result')
  vars.add('last_is_error')
  if (!workflowStore.currentWorkflow) return Array.from(vars).sort()
  for (const node of workflowStore.currentWorkflow.nodes) {
    if (node.data?._output_mappings) {
      for (const m of node.data._output_mappings) {
        if (m.target_var) vars.add(m.target_var)
      }
    }
    if (node.data?._input_mappings) {
      for (const m of node.data._input_mappings) {
        if (m.source_var) vars.add(m.source_var)
        if (m.variable_name) vars.add(m.variable_name)
      }
    }
    if (node.type === 'variable' && node.data?.variable_name) {
      vars.add(node.data.variable_name)
    }
  }
  return Array.from(vars).sort()
})

function getArgValue(key: string): any {
  return ensureArgsDict()[key] ?? ''
}

function getDisplayValue(key: string): string {
  const val = ensureArgsDict()[key] ?? ''
  if (typeof val === 'string') {
    const m = val.match(/^\$\{(.+)\}$/)
    if (m) return m[1]
  }
  return val
}

function ensureArgsDict(): Record<string, any> {
  const raw = data.value.arguments
  if (!raw) return {}
  if (typeof raw === 'object' && !Array.isArray(raw)) return { ...raw }
  if (typeof raw === 'string') {
    try {
      const parsed = JSON.parse(raw)
      if (typeof parsed === 'object' && !Array.isArray(parsed)) return { ...parsed }
    } catch {}
  }
  return {}
}

function setArgValue(key: string, value: any) {
  const args = ensureArgsDict()
  if (value === '' || value === undefined) {
    delete args[key]
  } else {
    args[key] = value
  }
  data.value = { ...data.value, arguments: args }
}

function onArgSelect(key: string, value: string) {
  const isKnown = knownVars.value.includes(value)
  setArgValue(key, isKnown ? `\${${value}}` : value)
}

function isVarRef(val: any): boolean {
  return typeof val === 'string' && /^\$\{.+\}$/.test(val)
}

function fillDefaults() {
  if (!selectedTool.value?.inputSchema?.properties) return
  const args = ensureArgsDict()
  for (const [key, prop] of Object.entries(selectedTool.value.inputSchema.properties) as [string, any][]) {
    if (!(key in args) && prop.default !== undefined) {
      args[key] = prop.default
    }
  }
  data.value = { ...data.value, arguments: args }
}

const argumentsStr = computed({
  get: () => {
    const args = ensureArgsDict()
    if (Object.keys(args).length === 0) return '{}'
    return JSON.stringify(args, null, 2)
  },
  set: (val: string) => {
    const placeholders: string[] = []
    const sanitized = val.replace(/\$\{[^}]+\}/g, (m) => {
      placeholders.push(m)
      return `"__PH${placeholders.length - 1}__"`
    })
    try {
      let parsed = JSON.parse(sanitized)
      const raw = JSON.stringify(parsed)
      const restored = raw.replace(/"__PH(\d+)__"/g, (_m, idx) => placeholders[parseInt(idx)])
      parsed = JSON.parse(restored)
      for (const key of Object.keys(parsed)) {
        const v = parsed[key]
        if (typeof v === 'string') {
          parsed[key] = v.replace(/"__PH(\d+)__"/g, (_m, idx) => placeholders[parseInt(idx)])
        }
      }
      data.value = { ...data.value, arguments: parsed }
    } catch {
      data.value = { ...data.value, arguments: val }
    }
  },
})

watch(configId, async (id) => {
  if (id) {
    await toolStore.loadTools(false, id)
  }
}, { immediate: false })

watch(toolName, () => {
  fillDefaults()
})

onMounted(() => {
  if (configId.value) {
    toolStore.loadTools(false, configId.value)
  }
})
</script>

<template>
  <div class="tool-call-panel">
    <el-form label-width="80px">
      <el-form-item label="服务器">
        <el-select v-model="configId" placeholder="选择连接的服务器" style="width: 100%">
          <el-option
            v-for="srv in connectionStore.connectedServers"
            :key="srv.id"
            :label="srv.name"
            :value="srv.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="工具">
        <el-select v-model="toolName" placeholder="选择工具" filterable style="width: 100%">
          <el-option
            v-for="tool in toolStore.tools"
            :key="tool.name"
            :label="tool.name"
            :value="tool.name"
          >
            <span>{{ tool.name }}</span>
            <span v-if="tool.description" style="color: #909399; font-size: 11px; margin-left: 8px">{{ tool.description.substring(0, 40) }}</span>
          </el-option>
        </el-select>
      </el-form-item>
    </el-form>

    <div v-if="selectedTool?.description" class="tool-desc">
      {{ selectedTool.description }}
    </div>

    <template v-if="showSchemaForm">
      <el-divider content-position="left">工具参数</el-divider>
      <el-form label-width="100px" size="small">
        <el-form-item
          v-for="prop in schemaProps"
          :key="prop.key"
          :label="prop.key"
          :required="prop.required"
        >
          <el-select
            v-if="prop.enum"
            :model-value="getArgValue(prop.key)"
            @update:model-value="setArgValue(prop.key, $event)"
            :placeholder="prop.description || '请选择'"
            style="width: 100%"
            clearable
          >
            <el-option v-for="opt in prop.enum" :key="opt" :label="opt" :value="opt" />
          </el-select>
          <el-input-number
            v-else-if="prop.type === 'number' || prop.type === 'integer'"
            :model-value="getArgValue(prop.key)"
            @update:model-value="setArgValue(prop.key, $event)"
            :placeholder="prop.description"
            controls-position="right"
            style="width: 100%"
          />
          <el-switch
            v-else-if="prop.type === 'boolean'"
            :model-value="getArgValue(prop.key)"
            @update:model-value="setArgValue(prop.key, $event)"
          />
          <el-select
            v-else
            :model-value="getDisplayValue(prop.key)"
            @update:model-value="onArgSelect(prop.key, $event)"
            :placeholder="prop.description || (prop.required ? '必填 - 可选择变量或手动输入' : '选填 - 可选择变量或手动输入')"
            style="width: 100%"
            filterable
            allow-create
            default-first-option
            clearable
          >
            <el-option
              v-if="getArgValue(prop.key) && !isVarRef(getArgValue(prop.key))"
              :label="String(getArgValue(prop.key))"
              :value="String(getArgValue(prop.key))"
            />
            <el-option-group label="上下文变量">
              <el-option v-for="v in knownVars" :key="v" :label="v" :value="v" />
            </el-option-group>
          </el-select>
          <div v-if="prop.description" class="prop-hint">{{ prop.description }}</div>
        </el-form-item>
      </el-form>
    </template>

    <el-divider content-position="left">
      原始 JSON
      <el-tooltip content="可直接编辑 JSON，支持 ${变量名} 引用上下文变量">
        <el-icon style="margin-left: 4px; cursor: help;"><span>?</span></el-icon>
      </el-tooltip>
    </el-divider>
    <el-input
      v-model="argumentsStr"
      type="textarea"
      :rows="4"
      placeholder="JSON 格式参数"
    />
    <div class="hint">支持 ${变量名} 引用上下文变量</div>
  </div>
</template>

<style scoped>
.tool-call-panel {
}

.tool-desc {
  background: #f5f7fa;
  border-radius: 4px;
  padding: 8px 12px;
  font-size: 12px;
  color: #606266;
  margin-bottom: 8px;
  line-height: 1.5;
}

.prop-hint {
  font-size: 11px;
  color: #909399;
  margin-top: 2px;
  line-height: 1.4;
}

.hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
