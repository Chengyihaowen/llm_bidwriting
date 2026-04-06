<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { knowledgeApi } from '../../api'

const props = defineProps<{ projectId: number }>()

const files = ref<any[]>([])
const uploading = ref(false)
const parsingId = ref<number | null>(null)
const deletingId = ref<number | null>(null)
const searchQuery = ref('')
const searchTopK = ref(5)
const searching = ref(false)
const searchResult = ref<any>({ provider: 'local', items: [] })

const statusMap: Record<string, { label: string; type: string }> = {
  pending: { label: '待解析', type: 'info' },
  parsing: { label: '解析中', type: 'warning' },
  success: { label: '可检索', type: 'success' },
  failed: { label: '失败', type: 'danger' },
}

async function loadFiles() {
  try {
    const res: any = await knowledgeApi.list(props.projectId)
    files.value = res.data || []
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

async function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  uploading.value = true
  try {
    await knowledgeApi.upload(props.projectId, file)
    ElMessage.success('知识库文件上传成功')
    await loadFiles()
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    uploading.value = false
    input.value = ''
  }
}

async function parseFile(fileId: number) {
  parsingId.value = fileId
  try {
    await knowledgeApi.parse(props.projectId, fileId)
    ElMessage.success('知识库解析完成')
    await loadFiles()
  } catch (e: any) {
    ElMessage.error(e.message)
    await loadFiles()
  } finally {
    parsingId.value = null
  }
}

async function toggleEnabled(row: any, enabled: boolean) {
  try {
    await knowledgeApi.update(props.projectId, row.id, { isEnabled: enabled })
    row.isEnabled = enabled
    ElMessage.success(enabled ? '已启用检索' : '已停用检索')
  } catch (e: any) {
    row.isEnabled = !enabled
    ElMessage.error(e.message)
  }
}

async function removeFile(row: any) {
  try {
    await ElMessageBox.confirm(`确定删除「${row.fileName}」吗？`, '提示', {
      type: 'warning',
    })
  } catch {
    return
  }

  deletingId.value = row.id
  try {
    await knowledgeApi.remove(props.projectId, row.id)
    ElMessage.success('已删除知识库文件')
    await loadFiles()
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    deletingId.value = null
  }
}

async function runSearch() {
  if (!searchQuery.value.trim()) {
    ElMessage.warning('请输入检索内容')
    return
  }
  searching.value = true
  try {
    const res: any = await knowledgeApi.search(props.projectId, {
      query: searchQuery.value,
      topK: searchTopK.value,
    })
    searchResult.value = res.data || { provider: 'local', items: [] }
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    searching.value = false
  }
}

function formatSize(bytes: number) {
  if (!bytes) return '-'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

onMounted(loadFiles)
</script>

<template>
  <div class="panel">
    <div class="panel-header">
      <h2>知识库</h2>
      <p class="desc">上传项目资料后可进行检索，并在正文生成时作为参考上下文。</p>
    </div>

    <div class="panel-body">
      <div class="section-card upload-card">
        <label class="upload-label" :class="{ disabled: uploading || parsingId !== null }">
          <input
            type="file"
            accept=".pdf,.docx,.doc"
            @change="onFileChange"
            :disabled="uploading || parsingId !== null"
            style="display: none"
          />
          <el-icon class="upload-icon"><Upload /></el-icon>
          <span>{{ uploading ? '上传中...' : '点击选择知识库文件（PDF / DOCX）' }}</span>
          <span class="upload-hint">建议上传技术规范、评分办法、企业资料等项目文档</span>
        </label>
      </div>

      <div class="section-card">
        <div class="section-header">
          <h3>知识库文件</h3>
          <el-tag size="small" type="info">{{ files.length }} 个文件</el-tag>
        </div>

        <el-table v-if="files.length" :data="files" size="small">
          <el-table-column label="文件名" min-width="220" prop="fileName" />
          <el-table-column label="大小" width="100">
            <template #default="{ row }">{{ formatSize(row.fileSize) }}</template>
          </el-table-column>
          <el-table-column label="状态" width="110">
            <template #default="{ row }">
              <el-tag :type="statusMap[row.parseStatus]?.type || 'info'" size="small">
                {{ statusMap[row.parseStatus]?.label || row.parseStatus }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="片段数" width="90" prop="chunkCount" />
          <el-table-column label="启用" width="90">
            <template #default="{ row }">
              <el-switch
                :model-value="row.isEnabled"
                :disabled="row.parseStatus !== 'success'"
                @change="(value: boolean) => toggleEnabled(row, value)"
              />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="210">
            <template #default="{ row }">
              <el-button
                v-if="row.parseStatus !== 'success'"
                text
                type="primary"
                :loading="parsingId === row.id"
                @click="parseFile(row.id)"
              >
                {{ row.parseStatus === 'failed' ? '重新解析' : '开始解析' }}
              </el-button>
              <el-button
                text
                type="danger"
                :loading="deletingId === row.id"
                @click="removeFile(row)"
              >删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-empty v-else description="暂无知识库文件，先上传资料开始建立知识库" />
      </div>

      <div class="section-card">
        <div class="section-header">
          <h3>检索测试</h3>
          <el-tag size="small">Provider: {{ searchResult.provider || 'local' }}</el-tag>
        </div>

        <div class="search-bar">
          <el-input v-model="searchQuery" placeholder="例如：评分标准、服务方案、资质要求" clearable />
          <el-select v-model="searchTopK" style="width: 100px">
            <el-option :value="3" label="Top 3" />
            <el-option :value="5" label="Top 5" />
            <el-option :value="8" label="Top 8" />
          </el-select>
          <el-button type="primary" :loading="searching" @click="runSearch">
            {{ searching ? '检索中...' : '预览召回' }}
          </el-button>
        </div>

        <div v-if="searchResult.items?.length" class="result-list">
          <div v-for="(item, index) in searchResult.items" :key="index" class="result-card">
            <div class="result-meta">
              <div>
                <strong>{{ item.source?.fileName }}</strong>
                <span class="meta-sub">片段 #{{ item.source?.chunkNo }}</span>
              </div>
              <el-tag size="small" type="success">得分 {{ item.score }}</el-tag>
            </div>
            <div class="result-content">{{ item.content }}</div>
          </div>
        </div>
        <el-empty v-else description="输入关键词后可预览知识库召回结果" :image-size="80" />
      </div>
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
.panel-body { flex: 1; overflow-y: auto; padding: 24px 32px; }
.section-card {
  background: #fafafa;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.section-header h3 { font-size: 15px; font-weight: 600; }
.upload-label {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  height: 180px;
  border: 2px dashed #cdd8e5;
  border-radius: 18px;
  cursor: pointer;
  transition: all 0.22s;
  color: #64748b;
  background: linear-gradient(180deg, #fbfdff 0%, #f4f8fc 100%);
}
.upload-label:hover { border-color: #409eff; color: #409eff; background: #f0f7ff; }
.upload-label.disabled { cursor: not-allowed; opacity: 0.6; }
.upload-icon { font-size: 44px; }
.upload-hint { font-size: 12px; color: #94a3b8; }
.search-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
.result-list { display: flex; flex-direction: column; gap: 12px; }
.result-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 14px;
}
.result-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.meta-sub { color: #94a3b8; margin-left: 8px; font-size: 12px; }
.result-content {
  white-space: pre-wrap;
  color: #303133;
  line-height: 1.7;
  font-size: 13px;
}
</style>
