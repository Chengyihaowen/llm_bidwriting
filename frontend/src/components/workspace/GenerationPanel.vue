<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'
import { outlineApi, chapterApi } from '../../api'

const props = defineProps<{ projectId: number }>()

interface Node {
  id: number
  title: string
  nodeType: string
  promptRequirement?: string
  children: Node[]
  orderNo: number
}

const outlineNodes = ref<Node[]>([])
const selectedNodeId = ref<number | null>(null)
const chapterContent = ref<any>(null)
const editMode = ref(false)
const editContent = ref('')
const generating = ref(false)
const streamText = ref('')
const taskId = ref<number | null>(null)
const useKnowledge = ref(true)
const knowledgeTopK = ref(5)
const retrievalItems = ref<any[]>([])
const retrievalMessage = ref('')
let eventSource: EventSource | null = null
let streamCompleted = false

const selectedNode = computed(() =>
  findNode(outlineNodes.value, selectedNodeId.value)
)

const selectedPromptRequirement = computed(() => selectedNode.value?.promptRequirement || '')

function findNode(nodes: Node[], id: number | null): Node | null {
  if (!id) return null
  for (const n of nodes) {
    if (n.id === id) return n
    const found = findNode(n.children, id)
    if (found) return found
  }
  return null
}

const renderedContent = computed(() => {
  const text = streamText.value || chapterContent.value?.content || ''
  if (!text) return ''
  return marked(text) as string
})

async function loadOutline() {
  try {
    const res: any = await outlineApi.get(props.projectId)
    outlineNodes.value = res.data?.nodes || []
    if (outlineNodes.value.length > 0 && !selectedNodeId.value) {
      const firstChapter = outlineNodes.value.find(n => n.nodeType === 'chapter')
      if (firstChapter) await selectChapter(firstChapter.id)
    }
  } catch {
    ElMessage.error('加载目录失败')
  }
}

async function selectChapter(id: number) {
  if (generating.value) {
    ElMessage.warning('正在生成中，请稍候')
    return
  }
  resetStreamState()
  editMode.value = false
  streamText.value = ''
  retrievalItems.value = []
  retrievalMessage.value = ''
  selectedNodeId.value = id
  await loadChapterContent(id)
}

async function loadChapterContent(nodeId: number) {
  try {
    const res: any = await chapterApi.get(props.projectId, nodeId)
    chapterContent.value = res.data
    editContent.value = res.data?.content || ''
  } catch {}
}

async function startGenerate() {
  if (!selectedNodeId.value) return
  generating.value = true
  streamCompleted = false
  streamText.value = ''
  retrievalItems.value = []
  retrievalMessage.value = ''
  editMode.value = false

  try {
    const res: any = await chapterApi.generate(props.projectId, selectedNodeId.value, {
      useKnowledge: useKnowledge.value,
      knowledgeTopK: knowledgeTopK.value,
    })
    const { taskId: tid, streamUrl } = res.data
    taskId.value = tid

    const fullUrl = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000') + streamUrl
    eventSource = new EventSource(fullUrl)

    eventSource.addEventListener('start', () => {
      streamCompleted = false
      streamText.value = ''
    })

    eventSource.addEventListener('retrieval', (e) => {
      try {
        const data = JSON.parse(e.data)
        retrievalItems.value = data.items || []
        retrievalMessage.value = data.message || ''
      } catch {}
    })

    eventSource.addEventListener('delta', (e) => {
      try {
        const data = JSON.parse(e.data)
        streamText.value += data.text || ''
      } catch {}
    })

    eventSource.addEventListener('complete', async (e) => {
      try {
        const data = JSON.parse(e.data)
        streamCompleted = true
        if (data.success !== false) {
          ElMessage.success('生成完成')
          await loadChapterContent(selectedNodeId.value!)
          if (!chapterContent.value?.content && streamText.value) {
            chapterContent.value = {
              ...(chapterContent.value || {}),
              content: streamText.value,
              status: 'generated',
            }
          }
        }
      } catch {}
      cleanup()
      resetStreamState()
    })

    eventSource.addEventListener('error', (e) => {
      if (streamCompleted) {
        cleanup()
        resetStreamState()
        return
      }
      try {
        const data = JSON.parse((e as any).data || '{}')
        ElMessage.error('生成失败: ' + (data.message || '未知错误'))
      } catch {
        ElMessage.error('生成连接中断')
      }
      cleanup()
      resetStreamState()
    })

    eventSource.onerror = () => {
      if (!generating.value || streamCompleted) {
        return
      }
      ElMessage.error('生成连接中断')
      cleanup()
      resetStreamState()
    }
  } catch (e: any) {
    ElMessage.error(e.message)
    generating.value = false
    resetStreamState()
  }
}

function cleanup() {
  generating.value = false
  eventSource?.close()
  eventSource = null
}

function resetStreamState() {
  streamCompleted = false
  taskId.value = null
}

function stopGenerate() {
  cleanup()
  resetStreamState()
  ElMessage.info('已停止生成')
  if (selectedNodeId.value) loadChapterContent(selectedNodeId.value)
}

function startEdit() {
  editContent.value = chapterContent.value?.content || ''
  editMode.value = true
}

async function saveEdit() {
  if (!selectedNodeId.value) return
  try {
    await chapterApi.save(props.projectId, selectedNodeId.value, editContent.value)
    ElMessage.success('已保存')
    editMode.value = false
    await loadChapterContent(selectedNodeId.value)
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

const statusMap: Record<string, { label: string; type: string }> = {
  not_generated: { label: '未生成', type: 'info' },
  generating: { label: '生成中', type: 'warning' },
  generated: { label: '已生成', type: 'success' },
  manually_edited: { label: '已修改', type: 'primary' },
  failed: { label: '生成失败', type: 'danger' },
}

onMounted(loadOutline)
</script>

<template>
  <div class="panel">
    <!-- 左侧：章节树 -->
    <div class="left-pane">
      <div class="left-header">章节目录</div>
      <div class="chapter-tree">
        <div
          v-for="node in outlineNodes"
          :key="node.id"
          class="chapter-group"
        >
          <div
            class="chapter-item level-1"
            :class="{ active: selectedNodeId === node.id }"
            @click="selectChapter(node.id)"
          >
            <span class="chapter-title">{{ node.title }}</span>
          </div>
          <div
            v-for="child in node.children"
            :key="child.id"
            class="chapter-item level-2"
            :class="{ active: selectedNodeId === child.id }"
            @click="selectChapter(child.id)"
          >
            {{ child.title }}
          </div>
        </div>
        <div v-if="outlineNodes.length === 0" class="empty-tree">
          请先在「目录编辑」中保存目录
        </div>
      </div>
    </div>

    <!-- 中间：编辑器/预览区 -->
    <div class="center-pane">
      <div class="center-header">
        <div class="node-title-bar">
          <span class="cur-title">{{ selectedNode?.title || '请选择章节' }}</span>
          <el-tag
            v-if="chapterContent?.status"
            :type="statusMap[chapterContent.status]?.type"
            size="small"
          >
            {{ statusMap[chapterContent.status]?.label }}
          </el-tag>
        </div>
        <div class="center-actions">
          <template v-if="!editMode">
            <el-button
              v-if="generating"
              type="danger"
              size="small"
              @click="stopGenerate"
            >停止生成</el-button>
            <el-button
              v-else
              type="primary"
              size="small"
              :disabled="!selectedNodeId"
              @click="startGenerate"
            >
              {{ chapterContent?.content ? '重新生成' : '生成本章' }}
            </el-button>
            <el-button
              v-if="chapterContent?.content && !generating"
              size="small"
              @click="startEdit"
            >编辑</el-button>
          </template>
          <template v-else>
            <el-button size="small" @click="editMode = false">取消</el-button>
            <el-button type="primary" size="small" @click="saveEdit">保存</el-button>
          </template>
        </div>
      </div>

      <div class="editor-area">
        <!-- 编辑模式 -->
        <textarea
          v-if="editMode"
          v-model="editContent"
          class="markdown-editor"
          placeholder="在此输入Markdown内容..."
        />
        <!-- 预览模式：流式生成 or 已有内容 -->
        <div v-else class="markdown-preview">
          <div v-if="generating" class="generating-indicator">
            <el-icon class="rotating"><Loading /></el-icon>
            <span>AI 正在生成...</span>
          </div>
          <div
            v-if="renderedContent"
            class="md-content"
            v-html="renderedContent"
          />
          <div v-else-if="!generating" class="empty-content">
            <el-empty description="点击「生成本章」开始生成内容" />
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧：信息面板 -->
    <div class="right-pane">
      <div class="right-section">
        <h4>章节信息</h4>
        <div v-if="selectedNode" class="info-list">
          <div class="info-item">
            <span class="info-label">标题</span>
            <span>{{ selectedNode.title }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">类型</span>
            <span>{{ selectedNode.nodeType === 'chapter' ? '章' : '节' }}</span>
          </div>
          <div v-if="chapterContent?.lastGeneratedAt" class="info-item">
            <span class="info-label">生成时间</span>
            <span>{{ new Date(chapterContent.lastGeneratedAt).toLocaleString('zh-CN') }}</span>
          </div>
          <div v-if="chapterContent?.currentVersionNo" class="info-item">
            <span class="info-label">版本</span>
            <span>v{{ chapterContent.currentVersionNo }}</span>
          </div>
        </div>
      </div>

      <div class="right-section" v-if="selectedNode">
        <h4>写作要求</h4>
        <div class="prompt-text">
          {{ selectedPromptRequirement || '（未设置）' }}
        </div>
      </div>

      <div class="right-section" v-if="selectedNode">
        <h4>知识库联动</h4>
        <div class="kb-actions">
          <div class="kb-row">
            <span class="info-label">使用知识库</span>
            <el-switch v-model="useKnowledge" :disabled="generating" />
          </div>
          <div class="kb-row">
            <span class="info-label">召回数量</span>
            <el-select v-model="knowledgeTopK" size="small" style="width: 100%" :disabled="generating || !useKnowledge">
              <el-option :value="3" label="Top 3" />
              <el-option :value="5" label="Top 5" />
              <el-option :value="8" label="Top 8" />
            </el-select>
          </div>
          <div class="kb-tip">生成时会优先召回当前项目知识库片段，再将结果注入写作上下文。</div>
        </div>
      </div>

      <div class="right-section" v-if="retrievalMessage || retrievalItems.length">
        <h4>知识库命中</h4>
        <div v-if="retrievalMessage" class="prompt-text">{{ retrievalMessage }}</div>
        <div v-if="retrievalItems.length" class="retrieval-list">
          <div
            v-for="(item, index) in retrievalItems"
            :key="index"
            class="retrieval-item"
          >
            <div class="retrieval-head">
              <span class="retrieval-file">{{ item.source?.fileName }}</span>
              <el-tag size="small" type="success">#{{ item.source?.chunkNo }}</el-tag>
            </div>
            <div class="retrieval-text">{{ item.content }}</div>
          </div>
        </div>
      </div>

      <div class="right-section" v-if="chapterContent?.versions?.length">
        <h4>版本历史</h4>
        <div class="version-list">
          <div
            v-for="v in chapterContent.versions"
            :key="v.id"
            class="version-item"
          >
            <span>v{{ v.versionNo }}</span>
            <el-tag size="small" type="info">{{ v.sourceType === 'ai_generated' ? 'AI生成' : '手工编辑' }}</el-tag>
            <span class="version-time">{{ new Date(v.createdAt).toLocaleString('zh-CN') }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.panel {
  height: 100%;
  display: flex;
  overflow: hidden;
}

/* 左侧 */
.left-pane {
  width: 220px;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  background: #fafafa;
}
.left-header {
  padding: 14px 16px;
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  border-bottom: 1px solid #e4e7ed;
}
.chapter-tree { flex: 1; overflow-y: auto; padding: 8px; }
.chapter-item {
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  color: #303133;
  transition: background 0.15s;
  line-height: 1.4;
}
.chapter-item:hover { background: #f0f0f0; }
.chapter-item.active { background: #ecf5ff; color: #409eff; font-weight: 600; }
.chapter-item.level-1 { font-weight: 500; }
.chapter-item.level-2 { padding-left: 24px; color: #606266; font-size: 12px; }
.empty-tree { text-align: center; padding: 40px 16px; color: #c0c4cc; font-size: 13px; }

/* 中间 */
.center-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.center-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  border-bottom: 1px solid #e4e7ed;
  background: #fff;
  flex-shrink: 0;
}
.node-title-bar { display: flex; align-items: center; gap: 10px; }
.cur-title { font-size: 16px; font-weight: 600; }
.center-actions { display: flex; gap: 8px; }

.editor-area { flex: 1; overflow: hidden; position: relative; }
.markdown-editor {
  width: 100%;
  height: 100%;
  padding: 20px;
  border: none;
  outline: none;
  resize: none;
  font-family: 'Consolas', monospace;
  font-size: 14px;
  line-height: 1.7;
  background: #fafafa;
}

.markdown-preview {
  height: 100%;
  overflow-y: auto;
  padding: 24px;
  background: #fff;
}
.generating-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #409eff;
  font-size: 14px;
  margin-bottom: 16px;
}
.rotating { animation: spin 1s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

.md-content :deep(h1) { font-size: 22px; font-weight: 700; margin: 20px 0 12px; }
.md-content :deep(h2) { font-size: 18px; font-weight: 600; margin: 16px 0 10px; }
.md-content :deep(h3) { font-size: 15px; font-weight: 600; margin: 14px 0 8px; }
.md-content :deep(p) { line-height: 1.8; margin-bottom: 10px; color: #303133; }
.md-content :deep(ul), .md-content :deep(ol) { padding-left: 24px; margin-bottom: 10px; }
.md-content :deep(li) { line-height: 1.7; margin-bottom: 4px; }
.md-content :deep(table) { border-collapse: collapse; width: 100%; margin-bottom: 12px; }
.md-content :deep(th), .md-content :deep(td) {
  border: 1px solid #ddd;
  padding: 8px 12px;
  text-align: left;
}
.md-content :deep(th) { background: #f5f7fa; font-weight: 600; }
.md-content :deep(blockquote) {
  border-left: 4px solid #409eff;
  padding-left: 16px;
  color: #606266;
  margin: 12px 0;
}
.md-content :deep(code) { background: #f5f7fa; padding: 2px 6px; border-radius: 3px; font-family: monospace; }
.md-content :deep(pre) { background: #f5f7fa; padding: 12px; border-radius: 6px; overflow-x: auto; margin-bottom: 12px; }
.md-content :deep(hr) { border: none; border-top: 1px solid #e4e7ed; margin: 16px 0; }

.empty-content { display: flex; justify-content: center; align-items: center; height: 300px; }

/* 右侧 */
.right-pane {
  width: 240px;
  border-left: 1px solid #e4e7ed;
  overflow-y: auto;
  padding: 16px;
  background: #fafafa;
  flex-shrink: 0;
}
.right-section { margin-bottom: 24px; }
.right-section h4 { font-size: 13px; font-weight: 600; color: #909399; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.5px; }
.info-list { display: flex; flex-direction: column; gap: 8px; }
.info-item { display: flex; flex-direction: column; gap: 2px; font-size: 13px; }
.info-label { color: #909399; font-size: 12px; }
.prompt-text { font-size: 13px; color: #606266; line-height: 1.6; background: #f5f7fa; padding: 10px; border-radius: 6px; }
.kb-actions { display: flex; flex-direction: column; gap: 10px; }
.kb-row { display: flex; flex-direction: column; gap: 6px; }
.kb-tip { font-size: 12px; color: #909399; line-height: 1.6; }
.retrieval-list { display: flex; flex-direction: column; gap: 8px; }
.retrieval-item { background: #fff; padding: 10px; border-radius: 6px; border: 1px solid #e4e7ed; }
.retrieval-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 6px; }
.retrieval-file { font-size: 12px; font-weight: 600; color: #409eff; }
.retrieval-text { font-size: 12px; line-height: 1.6; color: #606266; white-space: pre-wrap; }
.version-list { display: flex; flex-direction: column; gap: 8px; }
.version-item { display: flex; flex-direction: column; gap: 4px; font-size: 12px; background: #fff; padding: 8px; border-radius: 6px; border: 1px solid #e4e7ed; }
.version-time { color: #c0c4cc; }
</style>
