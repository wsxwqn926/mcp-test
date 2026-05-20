<template>
  <div class="page-header">
    <h2>提示词</h2>
  </div>

  <el-row :gutter="16">
    <el-col :span="8">
      <el-card class="section-card">
        <template #header><span>提示词列表</span></template>
        <div class="item-list">
          <div
            v-for="p in prompts"
            :key="p.name"
            :class="['list-item', { active: selectedPrompt === p.name }]"
            @click="selectPrompt(p)"
          >
            <span class="item-name">{{ p.name }}</span>
            <el-tag v-if="p.arguments?.length" size="small" type="info">
              {{ p.arguments.length }} 参数
            </el-tag>
          </div>
          <el-empty v-if="prompts.length === 0" :image-size="40" description="暂无提示词" />
        </div>
      </el-card>
    </el-col>

    <el-col :span="16">
      <el-card v-if="currentPrompt" class="section-card">
        <template #header>
          <div>
            <span style="font-weight: 600">{{ currentPrompt.name }}</span>
            <span v-if="currentPrompt.description" style="display:block;font-size:13px;color:#86909c;margin-top:2px">
              {{ currentPrompt.description }}
            </span>
          </div>
        </template>

        <el-form label-width="120px" size="small">
          <el-form-item
            v-for="arg in currentPrompt.arguments || []"
            :key="arg.name"
            :label="arg.name"
            :required="arg.required"
          >
            <el-input v-model="argValues[arg.name]" :placeholder="arg.description || ''" />
          </el-form-item>
        </el-form>

        <el-button type="primary" @click="getPrompt" :loading="loading">获取提示词</el-button>
      </el-card>

      <el-card v-if="promptResult" class="section-card" style="margin-top: 16px">
        <template #header><span style="font-weight: 600">结果</span></template>
        <div v-for="(msg, i) in promptResult.messages" :key="i" class="prompt-message">
          <el-tag :type="msg.role === 'user' ? '' : 'success'" size="small" style="margin-bottom: 4px">
            {{ msg.role }}
          </el-tag>
          <div class="json-viewer">{{ msg.content }}</div>
        </div>
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { promptsApi, type PromptInfo, type PromptResult } from '../api/prompts'
import { useConnectionStore } from '../stores/connection'

const connStore = useConnectionStore()
const prompts = ref<PromptInfo[]>([])
const selectedPrompt = ref('')
const argValues = ref<Record<string, string>>({})
const loading = ref(false)
const promptResult = ref<PromptResult | null>(null)

const currentPrompt = computed(() => prompts.value.find(p => p.name === selectedPrompt.value) || null)

async function loadPrompts() {
  const res = await promptsApi.list()
  prompts.value = res.prompts
}

function selectPrompt(p: PromptInfo) {
  selectedPrompt.value = p.name
  argValues.value = {}
  promptResult.value = null
}

async function getPrompt() {
  if (!selectedPrompt.value) return
  loading.value = true
  try {
    promptResult.value = await promptsApi.get(selectedPrompt.value, argValues.value)
  } finally {
    loading.value = false
  }
}

watch(() => connStore.isConnected, (v) => {
  if (v) loadPrompts()
}, { immediate: true })
</script>

<style scoped>
.item-list {
  max-height: 500px;
  overflow-y: auto;
}
.list-item {
  padding: 8px 12px;
  cursor: pointer;
  border-radius: 6px;
  margin-bottom: 2px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  transition: background 0.15s;
}
.list-item:hover { background: #f2f3f5; }
.list-item.active { background: #e8f3ff; }
.list-item.active .item-name { color: #409eff; }
.item-name {
  font-size: 13px;
  font-weight: 500;
  color: #1d2129;
}
.prompt-message {
  margin-bottom: 12px;
  padding: 8px;
  background: #f8f9fb;
  border-radius: 6px;
}
</style>
