<template>
  <div class="page-header">
    <h2>工具调试</h2>
  </div>

  <el-row :gutter="16">
    <el-col :span="8">
      <el-card class="section-card">
        <template #header><span>工具列表</span></template>
        <el-input v-model="search" placeholder="搜索工具..." clearable size="small" style="margin-bottom: 8px" />
        <div class="tool-list">
          <div
            v-for="tool in filteredTools"
            :key="tool.name"
            :class="['tool-item', { active: toolStore.selectedTool === tool.name }]"
            @click="selectTool(tool)"
          >
            <span class="tool-name">{{ tool.name }}</span>
            <span v-if="tool.description" class="tool-item-desc">{{ tool.description }}</span>
          </div>
          <el-empty v-if="filteredTools.length === 0" :image-size="40" description="暂无工具" />
        </div>
      </el-card>
    </el-col>

    <el-col :span="16">
      <el-card v-if="currentTool" class="section-card">
        <template #header>
          <div class="tool-header">
            <div>
              <span class="tool-title">{{ currentTool.name }}</span>
              <span v-if="currentTool.description" class="tool-header-desc">{{ currentTool.description }}</span>
            </div>
          </div>
        </template>

        <el-tabs v-model="inputMode">
          <el-tab-pane label="表单" name="form">
            <el-form label-width="120px" size="small">
              <el-form-item
                v-for="field in formFields"
                :key="field.name"
                :label="field.name"
                :required="field.required"
              >
                <el-input
                  v-if="field.widget === 'text_input'"
                  v-model="formValues[field.name]"
                  :placeholder="field.description || ''"
                />
                <el-input-number
                  v-else-if="field.widget === 'number_input'"
                  v-model="formValues[field.name]"
                  style="width: 100%"
                />
                <el-switch
                  v-else-if="field.widget === 'checkbox'"
                  v-model="formValues[field.name]"
                />
                <el-select
                  v-else-if="field.widget === 'selectbox'"
                  v-model="formValues[field.name]"
                  style="width: 100%"
                >
                  <el-option
                    v-for="opt in field.options || []"
                    :key="opt"
                    :label="opt"
                    :value="opt"
                  />
                </el-select>
                <el-input v-else v-model="formValues[field.name]" :placeholder="field.description || ''" />
              </el-form-item>
            </el-form>
          </el-tab-pane>
          <el-tab-pane label="JSON" name="json">
            <el-input
              v-model="jsonInput"
              type="textarea"
              :rows="8"
              placeholder='{"key": "value"}'
            />
          </el-tab-pane>
        </el-tabs>

        <div class="action-bar" style="margin-top: 12px">
          <el-button type="primary" @click="executeCall" :loading="calling">
            执行
          </el-button>
          <el-button @click="fillSample">
            填充示例数据
          </el-button>
        </div>
      </el-card>

      <el-card v-if="toolStore.callResult" class="section-card" style="margin-top: 16px">
        <template #header>
          <div class="action-bar">
            <span style="font-weight: 600">执行结果</span>
            <el-tag :type="toolStore.callResult.is_error ? 'danger' : 'success'" size="small">
              {{ toolStore.callResult.is_error ? '错误' : '成功' }}
            </el-tag>
            <span style="color: #86909c; font-size: 12px">
              {{ toolStore.callResult.duration_ms.toFixed(0) }}ms
            </span>
          </div>
        </template>
        <div v-for="(c, i) in toolStore.callResult.content" :key="i">
          <div v-if="c.type === 'text'" class="json-viewer">{{ formatContent(c.text || '') }}</div>
          <div v-else-if="c.type === 'image'">
            <img :src="`data:${c.mimeType};base64,${c.data}`" style="max-width: 100%" />
          </div>
          <div v-else>{{ c }}</div>
        </div>
      </el-card>

      <el-card
        v-if="toolStore.selectedTool && toolStore.callHistory[toolStore.selectedTool]"
        class="section-card"
        style="margin-top: 16px"
      >
        <template #header><span>调用历史</span></template>
        <el-collapse>
          <el-collapse-item
            v-for="(h, i) in toolStore.callHistory[toolStore.selectedTool]"
            :key="i"
            :title="`#${i + 1} ${h.timestamp} - ${h.is_error ? '错误' : '成功'} ${h.duration_ms.toFixed(0)}ms`"
            :name="i"
          >
            <p><strong>参数:</strong></p>
            <pre class="json-viewer">{{ JSON.stringify(h.arguments, null, 2) }}</pre>
          </el-collapse-item>
        </el-collapse>
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useToolStore } from '../stores/tools'
import { useConnectionStore } from '../stores/connection'
import type { ToolInfo } from '../api/tools'

const toolStore = useToolStore()
const connStore = useConnectionStore()

const search = ref('')
const inputMode = ref('form')
const jsonInput = ref('{}')
const formValues = ref<Record<string, any>>({})
const calling = ref(false)

const filteredTools = computed(() => {
  if (!search.value) return toolStore.tools
  const s = search.value.toLowerCase()
  return toolStore.tools.filter(t => t.name.toLowerCase().includes(s))
})

const currentTool = computed(() => {
  if (!toolStore.selectedTool) return null
  return toolStore.tools.find(t => t.name === toolStore.selectedTool) || null
})

const formFields = computed(() => {
  const schema = currentTool.value?.inputSchema
  if (!schema || !schema.properties) return []
  const required = schema.required || []
  return Object.entries(schema.properties).map(([name, def]: [string, any]) => {
    let widget = 'text_input'
    if (def.type === 'number' || def.type === 'integer') widget = 'number_input'
    else if (def.type === 'boolean') widget = 'checkbox'
    else if (def.enum) widget = 'selectbox'
    return {
      name,
      type: def.type,
      required: required.includes(name),
      description: def.description || '',
      default: def.default,
      widget,
      options: def.enum,
    }
  })
})

async function selectTool(tool: ToolInfo) {
  toolStore.selectedTool = tool.name
  formValues.value = {}
  if (tool.inputSchema?.properties) {
    for (const [k, v] of Object.entries(tool.inputSchema.properties as Record<string, any>)) {
      formValues.value[k] = v.default ?? (v.type === 'boolean' ? false : '')
    }
  }
  jsonInput.value = JSON.stringify(
    Object.fromEntries(Object.keys(tool.inputSchema?.properties || {}).map(k => [k, ''])),
    null,
    2,
  )
  await toolStore.loadHistory(tool.name)
}

async function executeCall() {
  if (!toolStore.selectedTool) return
  calling.value = true
  try {
    let args: any
    if (inputMode.value === 'json') {
      try { args = JSON.parse(jsonInput.value) } catch { args = undefined }
    } else {
      args = { ...formValues.value }
      for (const k of Object.keys(args)) {
        if (args[k] === '' || args[k] === undefined) delete args[k]
      }
    }
    await toolStore.callTool(toolStore.selectedTool, args)
  } finally {
    calling.value = false
  }
}

function generateSampleValue(def: any): any {
  if (def.default !== undefined) return def.default
  if (def.examples && def.examples.length > 0) return def.examples[0]
  if (def.enum && def.enum.length > 0) return def.enum[0]
  switch (def.type) {
    case 'string':
      if (def.format === 'date') return '2025-01-01'
      if (def.format === 'date-time') return '2025-01-01T00:00:00Z'
      if (def.format === 'email') return 'example@email.com'
      if (def.format === 'uri' || def.format === 'url') return 'https://example.com'
      if (/url|link|href/i.test(def.description || '')) return 'https://example.com'
      if (/path|file|dir/i.test(def.description || '')) return '/path/to/file'
      if (/color|colour/i.test(def.description || '')) return '#409EFF'
      if (/name/i.test(def.description || '')) return '示例名称'
      if (/title/i.test(def.description || '')) return '示例标题'
      if (/desc/i.test(def.description || '')) return '这是一段示例描述文字'
      if (/id/i.test(def.name || '')) return 'sample-id-001'
      if (/query|keyword|search/i.test(def.description || def.name || '')) return '搜索关键词'
      return '示例文本'
    case 'number':
    case 'integer':
      return def.minimum ?? 42
    case 'boolean':
      return true
    case 'array':
      if (def.items) {
        const sample = generateSampleValue(def.items)
        return [sample]
      }
      return []
    case 'object':
      if (def.properties) {
        const obj: Record<string, any> = {}
        for (const [k, v] of Object.entries(def.properties as Record<string, any>)) {
          obj[k] = generateSampleValue(v)
        }
        return obj
      }
      return {}
    default:
      return ''
  }
}

function fillSample() {
  const schema = currentTool.value?.inputSchema
  if (!schema?.properties) return
  const sample: Record<string, any> = {}
  for (const [name, def] of Object.entries(schema.properties as Record<string, any>)) {
    sample[name] = generateSampleValue(def)
  }
  formValues.value = { ...sample }
  jsonInput.value = JSON.stringify(sample, null, 2)
}

function formatContent(text: string): string {
  try {
    return JSON.stringify(JSON.parse(text), null, 2)
  } catch {
    return text
  }
}

watch(() => connStore.isConnected, async (v) => {
  if (v) await toolStore.loadTools()
  else toolStore.clear()
}, { immediate: true })
</script>

<style scoped>
.tool-list {
  max-height: 500px;
  overflow-y: auto;
}
.tool-item {
  padding: 8px 12px;
  cursor: pointer;
  border-radius: 6px;
  margin-bottom: 2px;
  transition: background 0.15s;
}
.tool-item:hover {
  background: #f2f3f5;
}
.tool-item.active {
  background: #e8f3ff;
}
.tool-item.active .tool-name {
  color: #409eff;
}
.tool-name {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #1d2129;
}
.tool-item-desc {
  display: block;
  font-size: 12px;
  color: #86909c;
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.tool-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.tool-title {
  font-weight: 600;
  font-size: 15px;
  color: #1d2129;
}
.tool-header-desc {
  display: block;
  font-size: 13px;
  color: #86909c;
  margin-top: 2px;
}
</style>
