<script setup lang="ts">
import { ref, computed, onMounted, markRaw } from 'vue'
import { VueFlow, useVueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'
import '@vue-flow/minimap/dist/style.css'

import StartNode from './nodes/StartNode.vue'
import EndNode from './nodes/EndNode.vue'
import ToolCallNode from './nodes/ToolCallNode.vue'
import ResourceNode from './nodes/ResourceNode.vue'
import PromptNode from './nodes/PromptNode.vue'
import AssertionNode from './nodes/AssertionNode.vue'
import WaitNode from './nodes/WaitNode.vue'
import ConditionNode from './nodes/ConditionNode.vue'
import VariableNode from './nodes/VariableNode.vue'
import LoopNode from './nodes/LoopNode.vue'

import { useWorkflowStore } from '../../stores/workflow'
import type { WorkflowNode, NodeType } from '../../api/workflows'

const nodeTypes = {
  start: markRaw(StartNode),
  end: markRaw(EndNode),
  tool_call: markRaw(ToolCallNode),
  resource_read: markRaw(ResourceNode),
  prompt_get: markRaw(PromptNode),
  assertion: markRaw(AssertionNode),
  wait: markRaw(WaitNode),
  condition: markRaw(ConditionNode),
  variable: markRaw(VariableNode),
  loop: markRaw(LoopNode),
}

const emit = defineEmits<{
  nodeClick: [nodeId: string]
}>()

const workflowStore = useWorkflowStore()
const flowWrapper = ref<HTMLElement>()

const { project, addNodes, onConnect, removeNodes, removeEdges, getSelectedNodes, getSelectedEdges, getNodes: getVfNodes } = useVueFlow('workflow-editor')

const defaultNodeData: Record<string, Record<string, any>> = {
  start: {},
  end: {},
  tool_call: { config_id: '', tool_name: '', arguments: {} },
  resource_read: { config_id: '', uri: '' },
  prompt_get: { config_id: '', name: '', arguments: {} },
  assertion: { assertion: { type: 'status_success' } },
  wait: { seconds: 1 },
  condition: { expression: { variable: '', operator: 'eq', value: '' } },
  variable: { action: 'set', variable_name: '', value_source: 'last_result', value_path: '' },
  loop: { loop_type: 'count', count: 3, max_iterations: 100 },
}

const nodeLabels: Record<string, string> = {
  start: '开始', end: '结束', tool_call: '调用工具', resource_read: '读取资源',
  prompt_get: '获取提示词', assertion: '断言', wait: '等待', condition: '条件判断',
  variable: '变量操作', loop: '循环',
}

const vfNodes = computed(() => {
  if (!workflowStore.currentWorkflow) return []
  return workflowStore.currentWorkflow.nodes.map(n => ({
    id: n.id,
    type: n.type,
    position: n.position,
    data: { ...n.data, label: n.label || nodeLabels[n.type] || n.type },
  }))
})

const vfEdges = computed(() => {
  if (!workflowStore.currentWorkflow) return []
  return workflowStore.currentWorkflow.edges.map(e => ({
    id: e.id,
    source: e.source,
    target: e.target,
    sourceHandle: e.sourceHandle,
    label: e.label,
    data: e.data,
    type: 'smoothstep',
    animated: true,
  }))
})

onConnect((params: any) => {
  if (!workflowStore.currentWorkflow) return
  const edgeId = `e-${params.source}-${params.target}-${Date.now()}`
  const newEdge = {
    id: edgeId,
    source: params.source,
    target: params.target,
    sourceHandle: params.sourceHandle ?? undefined,
  }
  workflowStore.currentWorkflow = {
    ...workflowStore.currentWorkflow,
    edges: [...workflowStore.currentWorkflow.edges, newEdge],
  }
})

function handleDrop(event: DragEvent) {
  event.preventDefault()
  if (!workflowStore.currentWorkflow) return
  const nodeType = event.dataTransfer?.getData('application/vueflow') as NodeType
  if (!nodeType || !(nodeType in defaultNodeData)) return

  const bounds = flowWrapper.value?.getBoundingClientRect()
  if (!bounds) return

  const position = project({
    x: event.clientX - bounds.left,
    y: event.clientY - bounds.top,
  })

  const nodeId = `${nodeType}_${Date.now()}`
  const data = { ...defaultNodeData[nodeType] }
  const label = nodeLabels[nodeType] || nodeType

  const newNode: WorkflowNode = {
    id: nodeId,
    type: nodeType,
    position: { x: position.x, y: position.y },
    label,
    data,
  }

  workflowStore.currentWorkflow = {
    ...workflowStore.currentWorkflow,
    nodes: [...workflowStore.currentWorkflow.nodes, newNode],
  }
}

function handleDragOver(event: DragEvent) {
  event.preventDefault()
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'move'
  }
}

function handleNodeClick({ node }: { node: any }) {
  emit('nodeClick', node.id)
}

function handleNodesChange(changes: any[]) {
  for (const change of changes) {
    if (change.type === 'remove' && workflowStore.currentWorkflow) {
      const nodeId = change.id
      workflowStore.currentWorkflow = {
        ...workflowStore.currentWorkflow,
        nodes: workflowStore.currentWorkflow.nodes.filter(n => n.id !== nodeId),
        edges: workflowStore.currentWorkflow.edges.filter(e => e.source !== nodeId && e.target !== nodeId),
      }
    }
  }
}

function handleEdgesChange(changes: any[]) {
  for (const change of changes) {
    if (change.type === 'remove' && workflowStore.currentWorkflow) {
      const edgeId = change.id
      workflowStore.currentWorkflow = {
        ...workflowStore.currentWorkflow,
        edges: workflowStore.currentWorkflow.edges.filter(e => e.id !== edgeId),
      }
    }
  }
}

function deleteSelected() {
  const selectedNodes = getSelectedNodes.value
  const selectedEdges = getSelectedEdges.value
  if (selectedEdges.length > 0) {
    removeEdges(selectedEdges)
  }
  if (selectedNodes.length > 0) {
    removeNodes(selectedNodes)
  }
}

function handleEdgeContextMenu(event: any) {
  event.event?.preventDefault?.()
  if (!workflowStore.currentWorkflow) return
  const edgeId = event.edge?.id || event.id
  if (!edgeId) return
  workflowStore.currentWorkflow = {
    ...workflowStore.currentWorkflow,
    edges: workflowStore.currentWorkflow.edges.filter(e => e.id !== edgeId),
  }
}

function handlePaneClick() {
}

function getWorkflowData() {
  if (!workflowStore.currentWorkflow) return { nodes: [], edges: [] }
  const vfPositions = new Map(getVfNodes.value.map(n => [n.id, n.position]))
  const syncedNodes = workflowStore.currentWorkflow.nodes.map(n => ({
    ...n,
    position: vfPositions.get(n.id) ?? n.position,
  }))
  return {
    nodes: syncedNodes,
    edges: workflowStore.currentWorkflow.edges,
  }
}

onMounted(() => {
  const el = flowWrapper.value
  if (el) {
    el.addEventListener('dragover', handleDragOver)
    el.addEventListener('drop', handleDrop)
  }
})

defineExpose({ getWorkflowData })
</script>

<template>
  <div ref="flowWrapper" class="flow-editor">
    <div class="editor-hint">
      💡 选中节点/连线后按 <kbd>Delete</kbd> 删除 | 从节点右侧圆点拖到另一节点左侧圆点连线
    </div>
    <VueFlow
      :nodes="vfNodes"
      :edges="vfEdges"
      :default-edge-options="{ type: 'smoothstep', animated: true }"
      :node-types="nodeTypes as any"
      :nodes-draggable="true"
      :nodes-connectable="true"
      :elements-selectable="true"
      :delete-key-code="'Delete,Backspace'"
      fit-view-on-init
      @node-click="handleNodeClick"
      @connect="(p: any) => onConnect(p)"
      @nodes-change="handleNodesChange"
      @edges-change="handleEdgesChange"
      @edge-context-menu="handleEdgeContextMenu"
      @pane-click="handlePaneClick"
    >
      <Background />
      <Controls />
      <MiniMap />
    </VueFlow>
  </div>
</template>

<style scoped>
.flow-editor {
  flex: 1;
  width: 100%;
  height: 100%;
  position: relative;
}

.editor-hint {
  position: absolute;
  top: 8px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
  background: rgba(255, 255, 255, 0.92);
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 12px;
  color: #606266;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  pointer-events: none;
  white-space: nowrap;
}

.editor-hint kbd {
  background: #f0f2f5;
  border: 1px solid #dcdfe6;
  border-radius: 3px;
  padding: 1px 5px;
  font-size: 11px;
  font-family: inherit;
}
</style>
