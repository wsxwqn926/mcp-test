import { defineStore } from 'pinia'
import { ref } from 'vue'
import { workflowsApi, type Workflow, type WorkflowRunResult, type NodeResult } from '../api/workflows'
import { ElMessage } from 'element-plus'

export const useWorkflowStore = defineStore('workflow', () => {
  const workflows = ref<Record<string, Workflow>>({})
  const currentWorkflow = ref<Workflow | null>(null)
  const runResult = ref<WorkflowRunResult | null>(null)
  const isRunning = ref(false)
  const nodeStatusMap = ref<Record<string, string>>({})
  const resultViewed = ref(false)

  async function loadWorkflows() {
    const res = await workflowsApi.list()
    workflows.value = res.workflows
  }

  async function createWorkflow(data: any) {
    const wf = await workflowsApi.create(data)
    workflows.value[wf.id] = wf
    currentWorkflow.value = wf
    return wf
  }

  async function saveWorkflow(id: string, data: any) {
    const wf = await workflowsApi.update(id, data)
    workflows.value[id] = wf
    if (currentWorkflow.value?.id === id) {
      currentWorkflow.value = wf
    }
    return wf
  }

  async function deleteWorkflow(id: string) {
    await workflowsApi.delete(id)
    delete workflows.value[id]
    if (currentWorkflow.value?.id === id) {
      currentWorkflow.value = null
    }
  }

  async function runWorkflow(id: string, variables?: Record<string, any>) {
    isRunning.value = true
    nodeStatusMap.value = {}
    runResult.value = null
    resultViewed.value = false
    try {
      const result = await workflowsApi.run(id, variables)
      runResult.value = result
      if (result.node_results) {
        for (const [nid, nr] of Object.entries(result.node_results)) {
          nodeStatusMap.value[nid] = (nr as NodeResult).status
        }
      }
      ElMessage.success(result.status === 'passed' ? '流程执行通过' : `流程执行: ${result.status}`)
      return result
    } catch (e: any) {
      ElMessage.error(e?.response?.data?.detail || '执行失败')
      throw e
    } finally {
      isRunning.value = false
    }
  }

  async function stopWorkflow(id: string) {
    await workflowsApi.stop(id)
    isRunning.value = false
  }

  function updateNodeStatus(data: { node_id: string; status: string }) {
    nodeStatusMap.value[data.node_id] = data.status
  }

  function setRunComplete(data: { status: string }) {
    isRunning.value = false
  }

  function clear() {
    currentWorkflow.value = null
    runResult.value = null
    nodeStatusMap.value = {}
    isRunning.value = false
    resultViewed.value = false
  }

  return {
    workflows,
    currentWorkflow,
    runResult,
    isRunning,
    nodeStatusMap,
    resultViewed,
    loadWorkflows,
    createWorkflow,
    saveWorkflow,
    deleteWorkflow,
    runWorkflow,
    stopWorkflow,
    updateNodeStatus,
    setRunComplete,
    clear,
  }
})
