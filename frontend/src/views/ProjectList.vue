<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { projectApi } from '../api'

const router = useRouter()
const projects = ref<any[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const form = ref({ name: '', bidderName: '', tenderTitle: '', tenderNo: '' })
const submitting = ref(false)

const statusMap: Record<string, { label: string; type: string }> = {
  draft: { label: '草稿中', type: 'info' },
  outline_confirmed: { label: '目录已确认', type: 'primary' },
  generating: { label: '生成中', type: 'warning' },
  pending_review: { label: '待复核', type: 'warning' },
  exportable: { label: '可导出', type: 'success' },
  exported: { label: '已导出', type: 'success' },
}

async function loadProjects() {
  loading.value = true
  try {
    const res: any = await projectApi.list()
    projects.value = res.data || []
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

async function createProject() {
  if (!form.value.name.trim()) {
    ElMessage.warning('请输入项目名称')
    return
  }
  submitting.value = true
  try {
    const res: any = await projectApi.create(form.value)
    ElMessage.success('项目创建成功')
    dialogVisible.value = false
    form.value = { name: '', bidderName: '', tenderTitle: '', tenderNo: '' }
    await loadProjects()
    router.push(`/projects/${res.data.id}`)
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    submitting.value = false
  }
}

async function deleteProject(id: number, name: string) {
  try {
    await ElMessageBox.confirm(`确认删除项目「${name}」？此操作不可撤销。`, '警告', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    await projectApi.delete(id)
    ElMessage.success('已删除')
    await loadProjects()
  } catch {}
}

function formatDate(dt: string) {
  if (!dt) return '-'
  return new Date(dt).toLocaleString('zh-CN', { hour12: false })
}

onMounted(loadProjects)
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div class="header-left">
        <h1 class="title">AI 智能标书系统</h1>
        <span class="subtitle">基于大模型的投标文件智能生成平台</span>
      </div>
      <el-button type="primary" size="large" @click="dialogVisible = true">
        <el-icon><Plus /></el-icon> 新建项目
      </el-button>
    </div>

    <div class="project-list" v-loading="loading">
      <el-empty v-if="!loading && projects.length === 0" description="暂无项目，点击右上角新建" />

      <el-card
        v-for="p in projects"
        :key="p.id"
        class="project-card"
        shadow="hover"
        @click="router.push(`/projects/${p.id}`)"
      >
        <div class="card-header">
          <span class="project-name">{{ p.name }}</span>
          <el-tag :type="statusMap[p.status]?.type || 'info'" size="small">
            {{ statusMap[p.status]?.label || p.status }}
          </el-tag>
        </div>
        <div class="card-info">
          <span v-if="p.bidderName">投标单位：{{ p.bidderName }}</span>
          <span v-if="p.tenderTitle">招标项目：{{ p.tenderTitle }}</span>
          <span v-if="p.tenderNo">招标编号：{{ p.tenderNo }}</span>
        </div>
        <div class="card-footer">
          <span class="update-time">更新于 {{ formatDate(p.updatedAt) }}</span>
          <el-button
            type="danger"
            size="small"
            text
            @click.stop="deleteProject(p.id, p.name)"
          >删除</el-button>
        </div>
      </el-card>
    </div>

    <!-- 新建项目弹窗 -->
    <el-dialog v-model="dialogVisible" title="新建标书项目" width="500px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="项目名称" required>
          <el-input v-model="form.name" placeholder="例：某某项目投标文件" />
        </el-form-item>
        <el-form-item label="投标单位">
          <el-input v-model="form.bidderName" placeholder="投标方公司名称" />
        </el-form-item>
        <el-form-item label="招标项目">
          <el-input v-model="form.tenderTitle" placeholder="招标项目名称" />
        </el-form-item>
        <el-form-item label="招标编号">
          <el-input v-model="form.tenderNo" placeholder="招标编号" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="createProject">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.page {
  max-width: 1280px;
  margin: 0 auto;
  padding: 32px 28px 40px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 20px;
  margin-bottom: 28px;
}
.header-left {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.title { font-size: 32px; font-weight: 700; color: #111827; letter-spacing: 0.5px; }
.subtitle { font-size: 14px; color: #6b7280; margin-left: 0; }
.project-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 20px;
}
.project-card {
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
  border-radius: 16px;
}
.project-card:hover {
  transform: translateY(-4px);
  border-color: #bfd8ff;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 14px;
}
.project-name {
  font-size: 17px;
  font-weight: 700;
  color: #1f2937;
  line-height: 1.5;
}
.card-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 13px;
  color: #4b5563;
  margin-bottom: 16px;
  min-height: 72px;
}
.card-info span {
  padding: 8px 10px;
  border-radius: 10px;
  background: #f8fafc;
}
.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #9ca3af;
  padding-top: 8px;
  border-top: 1px solid #eef1f5;
}
.update-time {
  white-space: nowrap;
}
</style>
