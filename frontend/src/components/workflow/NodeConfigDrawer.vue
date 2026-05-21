<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useWorkflowStore } from '../../stores/workflow'
import type { NodeResult } from '../../api/workflows'
import ToolCallPanel from './panels/ToolCallPanel.vue'
import ConditionPanel from './panels/ConditionPanel.vue'
import VariablePanel from './panels/VariablePanel.vue'
import LoopPanel from './panels/LoopPanel.vue'

const props = defineProps<{
  visible: boolean
  nodeId: string | null
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  save: []
}>()

const workflowStore = useWorkflowStore()

const localData = ref<Record<string, any>>({})
const localLabel = ref('')
const activeTab = ref('config')

const nodeType = computed(() => {
  if (!props.nodeId || !workflowStore.currentWorkflow) return null
  return workflowStore.currentWorkflow.nodes.find(n => n.id === props.nodeId)?.type ?? null
})

const hasPanel = computed(() => {
  return ['tool_call', 'condition', 'variable', 'loop'].includes(nodeType.value ?? '')
})

const nodeResult = computed<NodeResult | null>(() => {
  if (!props.nodeId || !workflowStore.runResult?.node_results) return null
  return (workflowStore.runResult.node_results[props.nodeId] as NodeResult) ?? null
})

const knownVars = computed(() => {
  const vars = new Set<string>()
  if (!workflowStore.currentWorkflow) return []
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
  vars.add('last_result')
  vars.add('last_is_error')
  return Array.from(vars).sort()
})

const responsePaths = computed(() => {
  const paths = [
    'response',
    'response.content',
    'response.content[0].text',
    'response.isError',
  ]
  for (const m of inputMappings.value) {
    if (m.target_param && !paths.includes(m.target_param)) {
      paths.push(m.target_param)
    }
  }
  return paths
})

const inputParamNames = computed(() => {
  if (nodeType.value === 'start') {
    return inputMappings.value
      .map((m: any) => m.variable_name)
      .filter((v: string) => !!v)
  }
  return inputMappings.value
    .map((m: any) => m.target_param)
    .filter((v: string) => !!v)
})

const responseFieldPaths = computed(() => {
  if (!nodeResult.value?.response) return []
  const paths: { value: string; label: string }[] = []
  function walk(obj: any, prefix: string, depth = 0) {
    if (obj == null || depth > 6) return
    if (typeof obj !== 'object') return
    if (Array.isArray(obj)) {
      const len = Math.min(obj.length, 10)
      for (let i = 0; i < len; i++) {
        const key = `${prefix}[${i}]`
        const val = obj[i]
        const label = typeof val === 'object' && val !== null
          ? key
          : `${key} (${formatVal(val)})`
        paths.push({ value: key, label })
        walk(val, key, depth + 1)
      }
    } else {
      for (const [k, v] of Object.entries(obj)) {
        const key = prefix ? `${prefix}.${k}` : k
        const label = typeof v === 'object' && v !== null
          ? key
          : `${key} (${formatVal(v)})`
        paths.push({ value: key, label })
        walk(v, key, depth + 1)
      }
    }
  }
  function formatVal(v: any): string {
    if (v === null) return 'null'
    if (v === undefined) return 'undefined'
    if (typeof v === 'boolean') return String(v)
    if (typeof v === 'number') return String(v)
    if (typeof v === 'string') {
      return v.length > 30 ? `"${v.substring(0, 30)}..."` : `"${v}"`
    }
    return String(v)
  }
  walk(nodeResult.value.response, 'response')
  const content = nodeResult.value.response.content
  if (Array.isArray(content)) {
    for (let i = 0; i < Math.min(content.length, 5); i++) {
      const item = content[i]
      if (item?.type === 'text' && item.text) {
        const textPath = `response.content[${i}].text`
        let textLabel = textPath
        try {
          const parsed = JSON.parse(item.text)
          if (typeof parsed !== 'object' || parsed === null) {
            textLabel = `${textPath} (${formatVal(parsed)})`
          }
          walk(parsed, textPath)
        } catch {
          textLabel = `${textPath} (${formatVal(item.text)})`
        }
        paths.push({ value: textPath, label: textLabel })
      }
    }
  }
  return paths
})

const inputMappings = computed({
  get: () => {
    const arr = localData.value._input_mappings ?? []
    if (nodeType.value === 'start') {
      return arr.map((m: any) => ({
        variable_name: m.variable_name ?? '',
        value: m.value ?? '',
      }))
    }
    return arr.map((m: any) => ({
      source_var: m.source_var ?? '',
      target_param: m.target_param ?? '',
    }))
  },
  set: (val: any[]) => {
    localData.value = { ...localData.value, _input_mappings: val }
  },
})

const outputMappings = computed({
  get: () => {
    const arr = localData.value._output_mappings ?? []
    return arr.map((m: any) => ({
      source_path: m.source_path ?? 'response',
      target_var: m.target_var ?? '',
    }))
  },
  set: (val: any[]) => {
    localData.value = { ...localData.value, _output_mappings: val }
  },
})

watch(() => props.nodeId, (id) => {
  if (!id || !workflowStore.currentWorkflow) return
  const node = workflowStore.currentWorkflow.nodes.find(n => n.id === id)
  if (node) {
    localData.value = { ...node.data }
    localLabel.value = node.label ?? ''
  }
  activeTab.value = 'config'
}, { immediate: true })

function handleSave() {
  if (!props.nodeId || !workflowStore.currentWorkflow) return
  const nodes = [...workflowStore.currentWorkflow.nodes]
  const idx = nodes.findIndex(n => n.id === props.nodeId)
  if (idx >= 0) {
    nodes[idx] = {
      ...nodes[idx],
      label: localLabel.value,
      data: { ...localData.value },
    }
    workflowStore.currentWorkflow = { ...workflowStore.currentWorkflow, nodes }
  }
  emit('save')
  emit('update:visible', false)
}

function handleCancel() {
  emit('update:visible', false)
}

function updateData(val: Record<string, any>) {
  localData.value = val
}

function addInputMapping() {
  if (nodeType.value === 'start') {
    inputMappings.value = [...inputMappings.value, { variable_name: '', value: '' }]
  } else {
    inputMappings.value = [...inputMappings.value, { source_var: '', target_param: '' }]
  }
}

function removeInputMapping(index: number) {
  const arr = [...inputMappings.value]
  arr.splice(index, 1)
  inputMappings.value = arr
}

function updateInputMapping(index: number, field: string, value: string) {
  const arr = [...inputMappings.value]
  arr[index] = { ...arr[index], [field]: value }
  inputMappings.value = arr
}

function addOutputMapping() {
  outputMappings.value = [...outputMappings.value, { source_path: 'response', target_var: '' }]
}

function removeOutputMapping(index: number) {
  const arr = [...outputMappings.value]
  arr.splice(index, 1)
  outputMappings.value = arr
}

function updateOutputMapping(index: number, field: 'source_path' | 'target_var', value: string) {
  const arr = [...outputMappings.value]
  arr[index] = { ...arr[index], [field]: value }
  outputMappings.value = arr
}

function nodeStatusType(status: string) {
  const map: Record<string, string> = {
    passed: 'success',
    failed: 'danger',
    error: 'danger',
    running: 'warning',
    skipped: 'info',
  }
  return map[status] || 'info'
}

function nodeDuration(ms: number) {
  return ms >= 1000 ? `${(ms / 1000).toFixed(2)}s` : `${ms}ms`
}

function formatResponse(response: any): string {
  if (!response) return ''
  if (response.content && Array.isArray(response.content)) {
    const parts: string[] = []
    for (const item of response.content) {
      if (item.type === 'text' && item.text) {
        let text = item.text
        try {
          const parsed = JSON.parse(text)
          text = JSON.stringify(parsed, null, 2)
        } catch {}
        parts.push(text)
      } else if (item.type === 'image' && item.data) {
        parts.push(`[Image: ${item.mimeType || 'unknown'}]`)
      } else if (item.type === 'resource' && item.resource) {
        parts.push(JSON.stringify(item.resource, null, 2))
      } else {
        parts.push(JSON.stringify(item, null, 2))
      }
    }
    const meta: any = { ...response }
    delete meta.content
    if (Object.keys(meta).length > 0) {
      parts.push(`---\n${JSON.stringify(meta, null, 2)}`)
    }
    return parts.join('\n\n')
  }
  return JSON.stringify(response, null, 2)
}
</script>

<template>
  <el-drawer
    :model-value="visible"
    title="配置节点"
    direction="rtl"
    size="480px"
    @update:model-value="emit('update:visible', $event)"
  >
    <template v-if="nodeType">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="配置" name="config">
          <el-form label-width="80px">
            <el-form-item label="节点名称">
              <el-input v-model="localLabel" placeholder="输入节点名称" />
            </el-form-item>
          </el-form>

          <ToolCallPanel
            v-if="nodeType === 'tool_call'"
            v-model="localData"
          />
          <ConditionPanel
            v-else-if="nodeType === 'condition'"
            v-model="localData"
          />
          <VariablePanel
            v-else-if="nodeType === 'variable'"
            v-model="localData"
          />
          <LoopPanel
            v-else-if="nodeType === 'loop'"
            v-model="localData"
          />
        </el-tab-pane>

        <el-tab-pane label="输入参数" name="input">
          <template v-if="nodeType === 'start'">
            <div class="tab-desc">
              定义流程的输入/输出变量。这些变量会注入上下文，供后续所有节点引用。运行流程时可修改实际值。
            </div>
            <div v-for="(m, i) in inputMappings" :key="i" class="mapping-row">
              <el-input
                :model-value="m.variable_name"
                @update:model-value="updateInputMapping(i, 'variable_name', $event)"
                placeholder="变量名"
                size="small"
                style="flex: 1"
              />
              <span class="mapping-eq">=</span>
              <el-input
                :model-value="m.value"
                @update:model-value="updateInputMapping(i, 'value', $event)"
                placeholder="默认值"
                size="small"
                style="flex: 1.5"
              />
              <el-button type="danger" link size="small" @click="removeInputMapping(i)">删除</el-button>
            </div>
          </template>
          <template v-else>
            <div class="tab-desc">
              将上下文变量映射到本节点的输入参数。留空则使用节点配置的默认值。支持选择已有变量或手动输入。
            </div>
            <div v-for="(m, i) in inputMappings" :key="i" class="mapping-row">
              <el-select
                :model-value="m.source_var"
                @update:model-value="updateInputMapping(i, 'source_var', $event)"
                placeholder="来源变量"
                size="small"
                style="flex: 1"
                filterable
                allow-create
                default-first-option
                clearable
              >
                <el-option v-for="v in knownVars" :key="v" :label="v" :value="v" />
              </el-select>
              <span class="mapping-arrow">→</span>
              <el-input
                :model-value="m.target_param"
                @update:model-value="updateInputMapping(i, 'target_param', $event)"
                placeholder="目标参数名"
                size="small"
                style="flex: 1"
              />
              <el-button type="danger" link size="small" @click="removeInputMapping(i)">删除</el-button>
            </div>
          </template>
          <el-button type="primary" link @click="addInputMapping" style="margin-top: 8px">+ 添加输入参数</el-button>
        </el-tab-pane>

        <el-tab-pane v-if="nodeType !== 'start'" label="输出参数" name="output">
          <div class="tab-desc">
            将本节点的执行结果保存为上下文变量，供后续节点引用。支持选择已有路径或手动输入。
          </div>
          <div v-for="(m, i) in outputMappings" :key="i" class="mapping-row">
            <el-select
              :model-value="m.source_path"
              @update:model-value="updateOutputMapping(i, 'source_path', $event)"
              placeholder="来源"
              size="small"
              style="flex: 1"
              filterable
              allow-create
              default-first-option
              clearable
            >
              <el-option-group label="常用路径">
                <el-option value="response" label="response" />
                <el-option value="response.content" label="response.content" />
                <el-option value="response.content[0].text" label="response.content[0].text" />
                <el-option value="response.isError" label="response.isError" />
              </el-option-group>
              <el-option-group v-if="responseFieldPaths.length" label="运行结果字段">
                <el-option v-for="p in responseFieldPaths" :key="p.value" :label="p.label" :value="p.value" />
              </el-option-group>
              <el-option-group v-if="inputParamNames.length" label="输入参数">
                <el-option v-for="p in inputParamNames" :key="p" :label="p" :value="p" />
              </el-option-group>
            </el-select>
            <span class="mapping-arrow">→</span>
            <el-select
              :model-value="m.target_var"
              @update:model-value="updateOutputMapping(i, 'target_var', $event)"
              placeholder="保存为变量名"
              size="small"
              style="flex: 1"
              filterable
              allow-create
              default-first-option
              clearable
            >
              <el-option v-for="v in knownVars" :key="v" :label="v" :value="v" />
            </el-select>
            <el-button type="danger" link size="small" @click="removeOutputMapping(i)">删除</el-button>
          </div>
          <el-button type="primary" link @click="addOutputMapping" style="margin-top: 8px">+ 添加输出映射</el-button>
        </el-tab-pane>

        <el-tab-pane v-if="nodeResult" label="运行结果" name="result" class="result-tab">
          <div class="result-header">
            <el-tag :type="nodeStatusType(nodeResult.status)" size="small">{{ nodeResult.status }}</el-tag>
            <span class="result-duration">{{ nodeDuration(nodeResult.duration_ms) }}</span>
          </div>
          <div v-if="nodeResult.request" class="result-block">
            <div class="block-label">Request</div>
            <pre class="json-block">{{ JSON.stringify(nodeResult.request, null, 2) }}</pre>
          </div>
          <div v-if="nodeResult.response" class="result-block result-block-response">
            <div class="block-label">Response</div>
            <pre class="json-block json-block-response">{{ formatResponse(nodeResult.response) }}</pre>
          </div>
          <div v-if="nodeResult.error_message" class="result-block">
            <div class="block-label error">Error</div>
            <pre class="json-block error">{{ nodeResult.error_message }}</pre>
          </div>
        </el-tab-pane>
      </el-tabs>
    </template>

    <template #footer>
      <el-button @click="handleCancel">取消</el-button>
      <el-button type="primary" @click="handleSave">确定</el-button>
    </template>
  </el-drawer>
</template>

<style scoped>
.tab-desc {
  font-size: 12px;
  color: #909399;
  margin-bottom: 12px;
  line-height: 1.6;
  background: #f5f7fa;
  padding: 8px 12px;
  border-radius: 4px;
}

.mapping-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}

.mapping-arrow {
  color: #c0c4cc;
  font-size: 14px;
  flex-shrink: 0;
}

.mapping-eq {
  color: #c0c4cc;
  font-size: 14px;
  font-weight: 600;
  flex-shrink: 0;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.result-duration {
  font-size: 12px;
  color: #909399;
}

.result-block {
  margin-bottom: 8px;
}

.block-label {
  font-size: 12px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 4px;
}

.block-label.error {
  color: #f56c6c;
}

.json-block {
  background: #f5f7fa;
  border-radius: 4px;
  padding: 8px;
  font-size: 12px;
  overflow-x: auto;
  max-height: 200px;
  overflow-y: auto;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
}

.json-block.error {
  background: #fef0f0;
  color: #f56c6c;
}

.result-tab {
  display: flex;
  flex-direction: column;
  height: 100%;
}

:deep(.el-tabs__content) {
  flex: 1;
  min-height: 0;
  overflow: auto;
}

:deep(.el-tabs) {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.result-block-response {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.json-block-response {
  flex: 1;
  max-height: none;
}
</style>
