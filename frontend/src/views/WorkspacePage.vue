<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { projectApi } from '../api'
import TenderFilePanel from '../components/workspace/TenderFilePanel.vue'
import OutlinePanel from '../components/workspace/OutlinePanel.vue'
import GenerationPanel from '../components/workspace/GenerationPanel.vue'
import ReviewPanel from '../components/workspace/ReviewPanel.vue'
import ExportPanel from '../components/workspace/ExportPanel.vue'
import KnowledgePanel from '../components/workspace/KnowledgePanel.vue'

const route = useRoute()
const router = useRouter()
const projectId = computed(() => Number(route.params.id))

const project = ref<any>(null)
const activeModule = ref('file') // file | outline | knowledge | generation | review | export

const navItems = [
  { key: 'file', label: '招标文件', icon: 'Document' },
  { key: 'outline', label: '目录编辑', icon: 'List' },
  { key: 'knowledge', label: '知识库', icon: 'Collection' },
  { key: 'generation', label: '正文生成', icon: 'Edit' },
  { key: 'review', label: '废标检查', icon: 'Warning' },
  { key: 'export', label: '导出', icon: 'Download' },
]

async function loadProject() {
  try {
    const res: any = await projectApi.get(projectId.value)
    project.value = res.data
  } catch {
    ElMessage.error('项目不存在')
    router.push('/')
  }
}

function refreshProject() {
  loadProject()
}

onMounted(loadProject)
</script>

<template>
  <div class="workspace" v-if="project">
    <!-- 顶部导航栏 -->
    <header class="ws-header">
      <div class="ws-breadcrumb">
        <el-button text @click="router.push('/')">
          <el-icon><ArrowLeft /></el-icon> 返回项目列表
        </el-button>
        <span class="divider">/</span>
        <span class="proj-name">{{ project.name }}</span>
      </div>
      <div class="ws-project-info">
        <el-tag size="small" type="info" v-if="project.bidderName">{{ project.bidderName }}</el-tag>
        <el-tag size="small" v-if="project.tenderNo">{{ project.tenderNo }}</el-tag>
      </div>
    </header>

    <div class="ws-body">
      <!-- 左侧导航 -->
      <nav class="ws-nav">
        <div
          v-for="item in navItems"
          :key="item.key"
          class="nav-item"
          :class="{ active: activeModule === item.key }"
          @click="activeModule = item.key"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </div>
      </nav>

      <!-- 主内容区 -->
      <main class="ws-main">
        <TenderFilePanel
          v-if="activeModule === 'file'"
          :project-id="projectId"
          @parsed="() => { refreshProject(); activeModule = 'outline' }"
        />
        <OutlinePanel
          v-else-if="activeModule === 'outline'"
          :project-id="projectId"
          @saved="() => { refreshProject(); activeModule = 'knowledge' }"
        />
        <KnowledgePanel
          v-else-if="activeModule === 'knowledge'"
          :project-id="projectId"
        />
        <GenerationPanel
          v-else-if="activeModule === 'generation'"
          :project-id="projectId"
        />
        <ReviewPanel
          v-else-if="activeModule === 'review'"
          :project-id="projectId"
        />
        <ExportPanel
          v-else-if="activeModule === 'export'"
          :project-id="projectId"
          :project="project"
        />
      </main>
    </div>
  </div>
  <div v-else class="loading-container">
    <el-skeleton :rows="10" animated />
  </div>
</template>

<style scoped>
.workspace {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: transparent;
}
.ws-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
  padding: 0 24px;
  margin: 16px 16px 0;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(229, 230, 235, 0.9);
  border-radius: 16px;
  backdrop-filter: blur(10px);
  box-shadow: 0 6px 20px rgba(15, 23, 42, 0.05);
  flex-shrink: 0;
}
.ws-breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
}
.divider { color: #c0c4cc; }
.proj-name { font-weight: 700; color: #111827; }
.ws-project-info { display: flex; gap: 8px; }

.ws-body {
  display: flex;
  flex: 1;
  overflow: hidden;
  padding: 16px;
  gap: 16px;
}

.ws-nav {
  width: 108px;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid var(--border-color);
  border-radius: 18px;
  display: flex;
  flex-direction: column;
  padding: 12px 0;
  flex-shrink: 0;
  box-shadow: var(--shadow-card);
}
.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  margin: 0 10px 6px;
  padding: 12px 0;
  border-radius: 14px;
  cursor: pointer;
  font-size: 12px;
  color: #606266;
  transition: all 0.2s;
}
.nav-item:hover { color: #409eff; background: #f3f9ff; }
.nav-item.active {
  color: #409eff;
  background: linear-gradient(180deg, #eef6ff 0%, #e8f3ff 100%);
  font-weight: 600;
  box-shadow: inset 0 0 0 1px rgba(64, 158, 255, 0.16);
}
.nav-item .el-icon { font-size: 20px; }

.ws-main {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  box-shadow: var(--shadow-card);
}

.loading-container {
  padding: 40px;
  max-width: 800px;
  margin: 0 auto;
}
</style>
