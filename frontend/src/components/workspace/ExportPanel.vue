<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { exportApi } from '../../api'

const props = defineProps<{ projectId: number; project: any }>()

const exports = ref<any[]>([])
const exporting = ref(false)
const form = ref({
  projectName: '',
  tenderNo: '',
  bidderName: '',
  date: '',
})

const statusMap: Record<string, { label: string; type: string }> = {
  pending: { label: '待生成', type: 'info' },
  running: { label: '生成中', type: 'warning' },
  success: { label: '已生成', type: 'success' },
  failed: { label: '生成失败', type: 'danger' },
}

async function loadExports() {
  try {
    const res: any = await exportApi.list(props.projectId)
    exports.value = res.data || []
  } catch {}
}

async function doExport() {
  exporting.value = true
  try {
    const res: any = await exportApi.create(props.projectId, {
      templateName: 'standard-bid-v1',
      coverFields: {
        projectName: form.value.projectName || props.project?.name,
        tenderNo: form.value.tenderNo || props.project?.tenderNo,
        bidderName: form.value.bidderName || props.project?.bidderName,
        date: form.value.date || new Date().toLocaleDateString('zh-CN'),
      },
    })
    ElMessage.success('导出成功')
    await loadExports()
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    exporting.value = false
  }
}

function download(exp: any) {
  window.open(exportApi.downloadUrl(props.projectId, exp.id))
}

onMounted(() => {
  loadExports()
  // 预填封面信息
  form.value.projectName = props.project?.name || ''
  form.value.tenderNo = props.project?.tenderNo || ''
  form.value.bidderName = props.project?.bidderName || ''
})
</script>

<template>
  <div class="panel">
    <div class="panel-header">
      <h2>导出 Word</h2>
      <p class="desc">将标书内容按固定格式导出为 .docx 文件</p>
    </div>

    <div class="panel-body">
      <!-- 封面信息 -->
      <div class="section-card">
        <h3>封面信息</h3>
        <el-form :model="form" label-width="80px" size="default">
          <el-form-item label="项目名称">
            <el-input v-model="form.projectName" :placeholder="project?.name" />
          </el-form-item>
          <el-form-item label="招标编号">
            <el-input v-model="form.tenderNo" :placeholder="project?.tenderNo || '选填'" />
          </el-form-item>
          <el-form-item label="投标单位">
            <el-input v-model="form.bidderName" :placeholder="project?.bidderName || '选填'" />
          </el-form-item>
          <el-form-item label="编制日期">
            <el-input v-model="form.date" :placeholder="new Date().toLocaleDateString('zh-CN')" />
          </el-form-item>
        </el-form>

        <el-button type="primary" size="large" :loading="exporting" @click="doExport">
          <el-icon><Download /></el-icon>
          {{ exporting ? '生成中...' : '生成并下载 Word' }}
        </el-button>
      </div>

      <!-- 历史导出 -->
      <div class="section-card" v-if="exports.length > 0">
        <h3>历史导出记录</h3>
        <el-table :data="exports" size="small">
          <el-table-column label="时间" prop="createdAt" :formatter="(r: any) => new Date(r.createdAt).toLocaleString('zh-CN')" />
          <el-table-column label="状态">
            <template #default="{ row }">
              <el-tag :type="statusMap[row.status]?.type" size="small">
                {{ statusMap[row.status]?.label }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="模板" prop="templateName" />
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button
                v-if="row.status === 'success'"
                text
                type="primary"
                size="small"
                @click="download(row)"
              >下载</el-button>
              <span v-else-if="row.errorMessage" class="error-text">{{ row.errorMessage }}</span>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 格式说明 -->
      <el-alert type="info" title="导出格式说明" :closable="false">
        <template #default>
          <p>• 封面：项目名称、招标编号、投标单位、编制日期</p>
          <p>• 一级章节 → Word 标题1（黑体三号）</p>
          <p>• 二级小节 → Word 标题2（黑体四号）</p>
          <p>• 正文：宋体小四，1.5倍行距</p>
          <p>• 页面：A4，标准页边距</p>
        </template>
      </el-alert>
    </div>
  </div>
</template>

<style scoped>
.panel { height: 100%; display: flex; flex-direction: column; background: #fff; }
.panel-header {
  padding: 20px 32px 16px;
  border-bottom: 1px solid #f0f0f0;
  flex-shrink: 0;
}
.panel-header h2 { font-size: 20px; font-weight: 600; margin-bottom: 4px; }
.desc { color: #909399; font-size: 13px; }
.panel-body { flex: 1; overflow-y: auto; padding: 24px 32px; max-width: 800px; }
.section-card {
  background: #fafafa;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}
.section-card h3 { font-size: 15px; font-weight: 600; margin-bottom: 16px; }
.error-text { color: #f56c6c; font-size: 12px; }
</style>
