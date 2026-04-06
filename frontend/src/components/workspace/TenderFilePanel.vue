<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { fileApi } from '../../api'

const props = defineProps<{ projectId: number }>()
const emit = defineEmits<{ (e: 'parsed'): void }>()

const fileInfo = ref<any>(null)
const uploading = ref(false)
const parsing = ref(false)

const parseStatusMap: Record<string, { label: string; type: string }> = {
  pending: { label: '待解析', type: 'info' },
  parsing: { label: '解析中...', type: 'warning' },
  success: { label: '解析成功', type: 'success' },
  failed: { label: '解析失败', type: 'danger' },
}

async function loadFile() {
  try {
    const res: any = await fileApi.get(props.projectId)
    fileInfo.value = res.data
  } catch {}
}

async function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  uploading.value = true
  try {
    await fileApi.upload(props.projectId, file)
    ElMessage.success('上传成功')
    await loadFile()
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    uploading.value = false
    input.value = ''
  }
}

async function startParse() {
  parsing.value = true
  try {
    await fileApi.parse(props.projectId)
    ElMessage.success('解析完成，目录已生成')
    await loadFile()
    emit('parsed')
  } catch (e: any) {
    ElMessage.error(e.message)
    await loadFile()
  } finally {
    parsing.value = false
  }
}

function formatSize(bytes: number) {
  if (!bytes) return '-'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

onMounted(loadFile)
</script>

<template>
  <div class="panel">
    <div class="panel-header">
      <h2>招标文件</h2>
      <p class="desc">上传招标文件（PDF / DOCX），系统将自动解析出标书目录结构。</p>
    </div>

    <div class="panel-body">
      <!-- 上传区域 -->
      <div class="upload-area">
        <label class="upload-label" :class="{ disabled: uploading || parsing }">
          <input
            type="file"
            accept=".pdf,.docx,.doc"
            @change="onFileChange"
            :disabled="uploading || parsing"
            style="display: none"
          />
          <el-icon class="upload-icon"><Upload /></el-icon>
          <span>{{ uploading ? '上传中...' : '点击选择文件（PDF / DOCX）' }}</span>
          <span class="upload-hint">最大支持 50MB</span>
        </label>
      </div>

      <!-- 文件信息 -->
      <div v-if="fileInfo" class="file-info-card">
        <div class="file-meta">
          <el-icon class="file-icon"><Document /></el-icon>
          <div class="file-detail">
            <div class="file-name">{{ fileInfo.fileName }}</div>
            <div class="file-sub">{{ formatSize(fileInfo.fileSize) }} · {{ fileInfo.fileType?.toUpperCase() }}</div>
          </div>
          <el-tag :type="parseStatusMap[fileInfo.parseStatus]?.type || 'info'">
            {{ parseStatusMap[fileInfo.parseStatus]?.label || fileInfo.parseStatus }}
          </el-tag>
        </div>

        <div v-if="fileInfo.parseErrorMessage" class="error-msg">
          <el-alert :title="fileInfo.parseErrorMessage" type="error" show-icon :closable="false" />
        </div>

        <div class="file-actions">
          <el-button
            v-if="fileInfo.parseStatus !== 'success'"
            type="primary"
            :loading="parsing"
            :disabled="uploading"
            @click="startParse"
          >
            {{ parsing ? '解析中，请稍候...' : '开始解析' }}
          </el-button>
          <el-button
            v-if="fileInfo.parseStatus === 'failed'"
            @click="startParse"
            :loading="parsing"
          >重新解析</el-button>
          <el-button
            v-if="fileInfo.parseStatus === 'success'"
            type="success"
            plain
            disabled
          >
            <el-icon><Check /></el-icon> 解析完成
          </el-button>
        </div>
      </div>

      <!-- 解析说明 -->
      <el-alert
        type="info"
        title="解析流程说明"
        :closable="false"
        style="margin-top: 20px"
      >
        <template #default>
          <p>1. 系统提取招标文件文本</p>
          <p>2. 调用AI大模型解析文件结构、评标办法、废标条款</p>
          <p>3. 自动生成标书目录树（可在「目录编辑」中调整）</p>
        </template>
      </el-alert>
    </div>
  </div>
</template>

<style scoped>
.panel { height: 100%; display: flex; flex-direction: column; background: transparent; }
.panel-header { padding: 28px 32px 18px; border-bottom: 1px solid #eef1f5; }
.panel-header h2 { font-size: 22px; font-weight: 700; margin-bottom: 8px; color: #111827; }
.desc { color: #6b7280; font-size: 14px; }
.panel-body { padding: 28px 32px 32px; flex: 1; overflow-y: auto; max-width: 760px; }

.upload-area { margin-bottom: 24px; }
.upload-label {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  height: 190px;
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

.file-info-card {
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  padding: 18px;
  background: #fff;
  box-shadow: 0 6px 20px rgba(15, 23, 42, 0.04);
}
.file-meta {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 14px;
}
.file-icon { font-size: 34px; color: #409eff; }
.file-detail { flex: 1; }
.file-name { font-weight: 600; font-size: 15px; margin-bottom: 4px; color: #1f2937; }
.file-sub { font-size: 12px; color: #94a3b8; }
.error-msg { margin-bottom: 12px; }
.file-actions { display: flex; gap: 10px; }
</style>
