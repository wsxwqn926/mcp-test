<template>
  <div class="page-header">
    <h2>自动化测试</h2>
  </div>

  <div style="margin-bottom: 12px; display: flex; gap: 8px">
    <el-button type="primary" @click="showNewTestDialog">新建用例</el-button>
    <el-button @click="recordFromHistory" :disabled="!connStore.isConnected">
      从历史录制
    </el-button>
  </div>

  <el-table :data="testList" stripe style="width: 100%">
    <el-table-column prop="name" label="名称" min-width="200" />
    <el-table-column prop="steps.length" label="步骤" width="80" />
    <el-table-column label="标签" width="200">
      <template #default="{ row }">
        <el-tag v-for="tag in row.tags" :key="tag" size="small" style="margin-right: 4px">{{ tag }}</el-tag>
      </template>
    </el-table-column>
    <el-table-column label="最近结果" width="120">
      <template #default="{ row }">
        <el-tag
          v-if="testStore.runResults[row.id]"
          :type="resultTagType(testStore.runResults[row.id].status)"
          size="small"
        >
          {{ testStore.runResults[row.id].status.toUpperCase() }}
        </el-tag>
      </template>
    </el-table-column>
    <el-table-column label="操作" width="260">
      <template #default="{ row }">
        <el-button size="small" type="primary" @click="runTest(row.id)" :loading="runningId === row.id">
          执行
        </el-button>
        <el-button size="small" @click="editTest(row)">编辑</el-button>
        <el-button size="small" type="danger" @click="deleteTest(row.id)">删除</el-button>
      </template>
    </el-table-column>
  </el-table>

  <el-card v-if="selectedResult" style="margin-top: 16px">
    <template #header>
      <span>结果：{{ selectedResult.test_case_name }}</span>
      <el-tag :type="resultTagType(selectedResult.status)" style="margin-left: 8px">
        {{ selectedResult.status.toUpperCase() }}
      </el-tag>
      <span style="margin-left: 8px; color: #909399">{{ selectedResult.duration_ms.toFixed(0) }}ms</span>
    </template>
    <el-collapse>
      <el-collapse-item
        v-for="(sr, i) in selectedResult.step_results"
        :key="i"
        :name="i"
      >
        <template #title>
          <span style="display: flex; align-items: center; gap: 8px">
            <span>{{ stepIcon(sr.status) }}</span>
            <span>{{ sr.step_name || sr.step_type }}</span>
            <span style="color: #909399; font-size: 12px">{{ sr.duration_ms.toFixed(0) }}ms</span>
          </span>
        </template>
        <div v-if="sr.error_message" style="color: #f56c6c">{{ sr.error_message }}</div>
        <div v-if="sr.assertion_results?.length">
          <div v-for="(ar, j) in sr.assertion_results" :key="j" style="margin: 4px 0">
            <span>{{ ar.passed ? '\u2705' : '\u274c' }} {{ ar.assertion_type }}: {{ ar.message }}</span>
          </div>
        </div>
      </el-collapse-item>
    </el-collapse>
  </el-card>

  <el-dialog v-model="editorVisible" :title="editingId ? '编辑测试用例' : '新建测试用例'" width="700px" destroy-on-close>
    <el-form :model="editForm" label-width="100px" size="small">
      <el-form-item label="名称">
        <el-input v-model="editForm.name" />
      </el-form-item>
      <el-form-item label="描述">
        <el-input v-model="editForm.description" type="textarea" :rows="2" />
      </el-form-item>
      <el-form-item label="标签">
        <el-select v-model="editForm.tags" multiple filterable allow-create style="width: 100%">
        </el-select>
      </el-form-item>
    </el-form>

    <h4 style="margin: 12px 0 8px">步骤</h4>
    <div v-for="(step, i) in editForm.steps" :key="step.id" class="step-editor">
      <el-row :gutter="8" align="middle">
        <el-col :span="4">
          <el-select v-model="step.type" size="small">
            <el-option label="工具调用" value="tool_call" />
            <el-option label="资源读取" value="resource_read" />
            <el-option label="提示词" value="prompt_get" />
            <el-option label="断言" value="assertion" />
            <el-option label="等待" value="wait" />
          </el-select>
        </el-col>
        <el-col :span="16">
          <template v-if="step.type === 'tool_call'">
            <el-input v-model="step.tool_name" placeholder="工具名称" size="small" />
            <el-input v-model="step.arguments_json" placeholder='{"key":"value"}' size="small" style="margin-top: 4px" />
          </template>
          <template v-else-if="step.type === 'resource_read'">
            <el-input v-model="step.resource_uri" placeholder="资源URI" size="small" />
          </template>
          <template v-else-if="step.type === 'prompt_get'">
            <el-input v-model="step.prompt_name" placeholder="提示词名称" size="small" />
          </template>
          <template v-else-if="step.type === 'assertion'">
            <el-select v-model="step.assertion_type" size="small" style="width: 200px">
              <el-option label="状态成功" value="status_success" />
              <el-option label="内容包含" value="content_contains" />
              <el-option label="内容匹配" value="content_matches" />
              <el-option label="内容非空" value="content_not_empty" />
              <el-option label="响应时间 <" value="response_time_lt" />
              <el-option label="JSON字段相等" value="json_field_equals" />
              <el-option label="Schema验证" value="content_schema_valid" />
            </el-select>
            <el-input v-model="step.assertion_expected" placeholder="期望值" size="small" style="margin-top: 4px" />
            <el-input v-model="step.assertion_path" placeholder="JSON路径（可选）" size="small" style="margin-top: 4px" />
            <el-checkbox v-model="step.assertion_negate" size="small" style="margin-top: 4px">取反</el-checkbox>
          </template>
          <template v-else-if="step.type === 'wait'">
            <el-input-number v-model="step.wait_seconds" :min="0.1" :max="60" size="small" />
            <span style="margin-left: 4px">秒</span>
          </template>
        </el-col>
        <el-col :span="4">
          <el-button size="small" type="danger" @click="editForm.steps.splice(i, 1)">删除</el-button>
        </el-col>
      </el-row>
    </div>
    <el-button size="small" @click="addStep('tool_call')">+ 工具调用</el-button>
    <el-button size="small" @click="addStep('assertion')">+ 断言</el-button>
    <el-button size="small" @click="addStep('resource_read')">+ 资源读取</el-button>
    <el-button size="small" @click="addStep('prompt_get')">+ 提示词</el-button>
    <el-button size="small" @click="addStep('wait')">+ 等待</el-button>

    <template #footer>
      <el-button @click="editorVisible = false">取消</el-button>
      <el-button type="primary" @click="saveTestCase">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useTestStore } from '../stores/tests'
import { useConnectionStore } from '../stores/connection'
import { ElMessage, ElMessageBox } from 'element-plus'

const testStore = useTestStore()
const connStore = useConnectionStore()

const runningId = ref('')
const editorVisible = ref(false)
const editingId = ref('')
const selectedResultId = ref('')

const testList = computed(() => Object.values(testStore.testCases))
const selectedResult = computed(() => selectedResultId.value ? testStore.runResults[selectedResultId.value] : null)

interface EditStep {
  id: string
  type: string
  tool_name: string
  arguments_json: string
  resource_uri: string
  prompt_name: string
  assertion_type: string
  assertion_expected: string
  assertion_path: string
  assertion_negate: boolean
  wait_seconds: number
}

const editForm = ref({
  name: '',
  description: '',
  tags: [] as string[],
  steps: [] as EditStep[],
})

function resultTagType(status: string) {
  if (status === 'passed') return 'success'
  if (status === 'failed') return 'danger'
  if (status === 'error') return 'warning'
  return 'info'
}

function stepIcon(status: string) {
  if (status === 'passed') return '\u2705'
  if (status === 'failed') return '\u274c'
  if (status === 'error') return '\u26a0\ufe0f'
  return '\u23f8'
}

function addStep(type: string) {
  editForm.value.steps.push({
    id: `step-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
    type,
    tool_name: '',
    arguments_json: '{}',
    resource_uri: '',
    prompt_name: '',
    assertion_type: 'status_success',
    assertion_expected: '',
    assertion_path: '',
    assertion_negate: false,
    wait_seconds: 1,
  })
}

function showNewTestDialog() {
  editingId.value = ''
  editForm.value = { name: '', description: '', tags: [], steps: [] }
  editorVisible.value = true
}

function editTest(tc: any) {
  editingId.value = tc.id
  editForm.value = {
    name: tc.name,
    description: tc.description || '',
    tags: [...tc.tags],
    steps: tc.steps.map((s: any) => ({
      id: s.id,
      type: s.type,
      tool_name: s.tool_name || '',
      arguments_json: JSON.stringify(s.arguments || {}),
      resource_uri: s.resource_uri || '',
      prompt_name: s.prompt_name || '',
      assertion_type: s.assertion?.type || 'status_success',
      assertion_expected: s.assertion?.expected ?? '',
      assertion_path: s.assertion?.path || '',
      assertion_negate: s.assertion?.negate || false,
      wait_seconds: s.wait_seconds || 1,
    })),
  }
  editorVisible.value = true
}

async function saveTestCase() {
  const steps = editForm.value.steps.map(s => {
    const step: any = { id: s.id, type: s.type, name: '' }
    if (s.type === 'tool_call') {
      step.tool_name = s.tool_name
      try { step.arguments = JSON.parse(s.arguments_json) } catch { step.arguments = {} }
    }
    if (s.type === 'resource_read') step.resource_uri = s.resource_uri
    if (s.type === 'prompt_get') step.prompt_name = s.prompt_name
    if (s.type === 'assertion') {
      step.assertion = {
        type: s.assertion_type,
        expected: s.assertion_expected || undefined,
        path: s.assertion_path || undefined,
        negate: s.assertion_negate,
      }
    }
    if (s.type === 'wait') step.wait_seconds = s.wait_seconds
    return step
  })

  const data = {
    name: editForm.value.name,
    description: editForm.value.description,
    tags: editForm.value.tags,
    steps,
  }

  if (editingId.value) {
    await testStore.updateTest(editingId.value, data)
  } else {
    await testStore.createTest(data)
  }
  editorVisible.value = false
  ElMessage.success('已保存')
}

async function runTest(id: string) {
  runningId.value = id
  try {
    await testStore.runTest(id)
    selectedResultId.value = id
    ElMessage.success('测试完成')
  } finally {
    runningId.value = ''
  }
}

async function deleteTest(id: string) {
  await ElMessageBox.confirm('确认删除此测试用例？', '确认')
  await testStore.deleteTest(id)
  ElMessage.success('已删除')
}

async function recordFromHistory() {
  const res = await testStore.recordFromHistory()
  if (res.count === 0) {
    ElMessage.info('无调用历史可录制')
    return
  }
  editingId.value = ''
  editForm.value = {
    name: '录制测试',
    description: '从调用历史自动录制',
    tags: ['recorded'],
    steps: res.steps.map(s => ({
      id: s.id,
      type: s.type,
      tool_name: s.tool_name || '',
      arguments_json: JSON.stringify(s.arguments || {}),
      resource_uri: s.resource_uri || '',
      prompt_name: s.prompt_name || '',
      assertion_type: s.assertion?.type || 'status_success',
      assertion_expected: s.assertion?.expected ?? '',
      assertion_path: s.assertion?.path || '',
      assertion_negate: s.assertion?.negate || false,
      wait_seconds: s.wait_seconds || 1,
    })),
  }
  editorVisible.value = true
}

onMounted(() => {
  testStore.loadTests()
})
</script>

<style scoped>
.step-editor {
  padding: 8px;
  margin-bottom: 8px;
  background: #f5f7fa;
  border-radius: 4px;
}
</style>
