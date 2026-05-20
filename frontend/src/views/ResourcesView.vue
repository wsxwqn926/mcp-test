<template>
  <div class="page-header">
    <h2>资源浏览</h2>
  </div>

  <el-card class="section-card">
    <el-tabs v-model="activeTab">
      <el-tab-pane label="资源" name="resources">
        <el-table :data="resources" stripe style="width: 100%">
          <el-table-column prop="uri" label="URI" min-width="200" />
          <el-table-column prop="name" label="名称" width="180" />
          <el-table-column prop="mimeType" label="MIME Type" width="160" />
          <el-table-column label="操作" width="220">
            <template #default="{ row }">
              <el-button size="small" @click="readResource(row.uri)">读取</el-button>
              <el-button size="small" type="primary" @click="subscribeResource(row.uri)">订阅</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="resources.length === 0" description="暂无资源" />

        <div v-if="resourceContent" style="margin-top: 16px">
          <div class="section-title">内容</div>
          <div v-for="(c, i) in resourceContent" :key="i">
            <div v-if="c.text" class="json-viewer">{{ formatContent(c.text) }}</div>
            <div v-else-if="c.blob">
              <img v-if="c.mimeType?.startsWith('image/')" :src="`data:${c.mimeType};base64,${c.blob}`" style="max-width: 100%" />
              <div v-else class="json-viewer">[二进制数据: {{ c.mimeType }}]</div>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="模板" name="templates">
        <el-table :data="templates" stripe style="width: 100%">
          <el-table-column prop="uriTemplate" label="URI Template" min-width="250" />
          <el-table-column prop="name" label="名称" width="200" />
          <el-table-column prop="description" label="描述" min-width="200" />
        </el-table>
        <el-empty v-if="templates.length === 0" description="暂无模板" />
      </el-tab-pane>
    </el-tabs>
  </el-card>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { resourcesApi, type ResourceInfo, type ResourceContent } from '../api/resources'
import { useConnectionStore } from '../stores/connection'

const connStore = useConnectionStore()
const activeTab = ref('resources')
const resources = ref<ResourceInfo[]>([])
const templates = ref<any[]>([])
const resourceContent = ref<ResourceContent[] | null>(null)

async function loadResources() {
  const res = await resourcesApi.list()
  resources.value = res.resources
  const tpl = await resourcesApi.templates()
  templates.value = tpl.templates
}

async function readResource(uri: string) {
  const res = await resourcesApi.read(uri)
  resourceContent.value = res.contents
}

async function subscribeResource(uri: string) {
  await resourcesApi.subscribe(uri)
}

function formatContent(text: string): string {
  try {
    return JSON.stringify(JSON.parse(text), null, 2)
  } catch {
    return text
  }
}

watch(() => connStore.isConnected, (v) => {
  if (v) loadResources()
}, { immediate: true })
</script>

<style scoped>
.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #1d2129;
  margin-bottom: 8px;
}
</style>
