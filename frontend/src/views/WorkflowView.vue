<template>
  <div class="workflow-page">
    <RunToolbar
      @run="onRun"
      @stop="onStop"
      @save="onSave"
      @create="onCreate"
      @delete="onDelete"
      @show-result="onShowResult"
    />

    <div class="workflow-body">
      <div class="flow-canvas">
        <FlowEditor ref="flowEditorRef" @node-click="onNodeClick" />
        <NodeSidebar />
      </div>

      <NodeConfigDrawer
        v-model:visible="drawerVisible"
        :node-id="selectedNodeId"
        @save="onDrawerSave"
      />
    </div>

    <ResultPanel v-model:visible="resultDialogVisible" />
    <RunParamsDialog
      v-model:visible="runParamsVisible"
      @confirm="onRunWithParams"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useWorkflowStore } from '../stores/workflow'
import { useConnectionStore } from '../stores/connection'
import { ElMessage, ElMessageBox } from 'element-plus'
import RunToolbar from '../components/workflow/RunToolbar.vue'
import NodeSidebar from '../components/workflow/NodeSidebar.vue'
import FlowEditor from '../components/workflow/FlowEditor.vue'
import NodeConfigDrawer from '../components/workflow/NodeConfigDrawer.vue'
import ResultPanel from '../components/workflow/ResultPanel.vue'
import RunParamsDialog from '../components/workflow/RunParamsDialog.vue'

const workflowStore = useWorkflowStore()
const connStore = useConnectionStore()

const flowEditorRef = ref()
const drawerVisible = ref(false)
const resultDialogVisible = ref(false)
const runParamsVisible = ref(false)
const selectedNodeId = ref<string | null>(null)

const startNodeInputs = computed(() => {
  if (!workflowStore.currentWorkflow) return []
  const startNode = workflowStore.currentWorkflow.nodes.find(n => n.type === 'start')
  if (!startNode) return []
  return (startNode.data._input_mappings ?? []).filter((m: any) => m.variable_name)
})

async function onRun() {
  const wf = workflowStore.currentWorkflow
  if (!wf) {
    ElMessage.warning('请先选择或创建流程')
    return
  }
  if (!wf.nodes.length) {
    ElMessage.warning('流程中没有节点')
    return
  }
  if (startNodeInputs.value.length > 0) {
    runParamsVisible.value = true
  } else {
    await workflowStore.runWorkflow(wf.id)
  }
}

async function onRunWithParams(variables: Record<string, any>) {
  const wf = workflowStore.currentWorkflow
  if (!wf) return
  await workflowStore.runWorkflow(wf.id, variables)
}

async function onStop() {
  const wf = workflowStore.currentWorkflow
  if (wf) {
    await workflowStore.stopWorkflow(wf.id)
  }
}

async function onSave() {
  const wf = workflowStore.currentWorkflow
  if (!wf) {
    ElMessage.warning('请先选择或创建流程')
    return
  }
  const editorData = flowEditorRef.value?.getWorkflowData()
  if (editorData) {
    await workflowStore.saveWorkflow(wf.id, {
      nodes: editorData.nodes,
      edges: editorData.edges,
    })
    ElMessage.success('已保存')
  }
}

async function onCreate() {
  const { value: name } = await ElMessageBox.prompt('请输入流程名称', '新建流程', {
    confirmButtonText: '创建',
    cancelButtonText: '取消',
    inputValue: '新流程',
  })
  if (name) {
    const startId = `node-${Date.now()}-start`
    const endId = `node-${Date.now()}-end`
    await workflowStore.createWorkflow({
      name,
      nodes: [
        { id: startId, type: 'start', position: { x: 100, y: 200 }, data: {} },
        { id: endId, type: 'end', position: { x: 600, y: 200 }, data: {} },
      ],
      edges: [
        { id: `edge-${Date.now()}`, source: startId, target: endId },
      ],
    })
    ElMessage.success('已创建')
  }
}

function onShowResult() {
  resultDialogVisible.value = true
  workflowStore.resultViewed = true
}

function onNodeClick(nodeId: string) {
  selectedNodeId.value = nodeId
  drawerVisible.value = true
}

function onDrawerSave() {
  drawerVisible.value = false
}

async function onDelete() {
  const wf = workflowStore.currentWorkflow
  if (!wf) return
  await workflowStore.deleteWorkflow(wf.id)
  ElMessage.success('已删除')
}

onMounted(async () => {
  await workflowStore.loadWorkflows()
  await connStore.refreshStatus()
})
</script>

<style scoped>
.workflow-page {
  height: calc(100vh - 48px);
  display: flex;
  flex-direction: column;
  padding: 0 !important;
  margin: -24px -28px;
}

.workflow-body {
  flex: 1;
  display: flex;
  overflow: hidden;
  min-height: 0;
}

.flow-canvas {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
</style>
