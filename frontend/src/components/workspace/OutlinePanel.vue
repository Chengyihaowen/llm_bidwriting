<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { outlineApi } from '../../api'
import TreeNode from '../TreeNode.vue'

const props = defineProps<{ projectId: number }>()
const emit = defineEmits<{ (e: 'saved'): void }>()

interface OutlineNode {
  id?: number
  title: string
  nodeType: string
  promptRequirement: string
  isEnabled: boolean
  orderNo: number
  children: OutlineNode[]
  _key: string  // 前端唯一key
}

const nodes = ref<OutlineNode[]>([])
const selectedNode = ref<OutlineNode | null>(null)
const saving = ref(false)
let keyCounter = 0

function genKey() { return `node-${++keyCounter}` }

async function loadOutline() {
  try {
    const res: any = await outlineApi.get(props.projectId)
    const raw = res.data?.nodes || []
    nodes.value = raw.map(mapNode)
  } catch (e: any) {
    ElMessage.error('加载目录失败: ' + e.message)
  }
}

function mapNode(n: any): OutlineNode {
  return {
    id: n.id,
    title: n.title,
    nodeType: n.nodeType || 'chapter',
    promptRequirement: n.promptRequirement || '',
    isEnabled: n.isEnabled !== false,
    orderNo: n.orderNo || 0,
    children: (n.children || []).map(mapNode),
    _key: genKey(),
  }
}

function toApiNode(n: OutlineNode, parentId?: number): any {
  return {
    id: n.id,
    title: n.title,
    nodeType: n.nodeType,
    promptRequirement: n.promptRequirement,
    isEnabled: n.isEnabled,
    orderNo: n.orderNo,
    parentId: parentId ?? null,
    children: n.children.map(c => toApiNode(c, n.id)),
  }
}

function selectNode(node: OutlineNode) {
  selectedNode.value = node
}

function addRootNode() {
  const node: OutlineNode = {
    title: '新章节',
    nodeType: 'chapter',
    promptRequirement: '',
    isEnabled: true,
    orderNo: nodes.value.length,
    children: [],
    _key: genKey(),
  }
  nodes.value.push(node)
  selectedNode.value = node
}

function addChildNode(parent: OutlineNode) {
  const child: OutlineNode = {
    title: '新节',
    nodeType: 'section',
    promptRequirement: '',
    isEnabled: true,
    orderNo: parent.children.length,
    children: [],
    _key: genKey(),
  }
  parent.children.push(child)
  selectedNode.value = child
}

function deleteNode(nodeList: OutlineNode[], node: OutlineNode): boolean {
  const idx = nodeList.findIndex(n => n._key === node._key)
  if (idx !== -1) {
    nodeList.splice(idx, 1)
    if (selectedNode.value?._key === node._key) selectedNode.value = null
    return true
  }
  for (const n of nodeList) {
    if (deleteNode(n.children, node)) return true
  }
  return false
}

async function confirmDelete(node: OutlineNode) {
  try {
    await ElMessageBox.confirm(`确认删除「${node.title}」？`, '删除确认', {
      type: 'warning',
      confirmButtonText: '删除',
    })
    deleteNode(nodes.value, node)
  } catch {}
}

function moveUp(nodeList: OutlineNode[], node: OutlineNode) {
  const idx = nodeList.findIndex(n => n._key === node._key)
  if (idx > 0) {
    const current = nodeList[idx]
    const previous = nodeList[idx - 1]
    if (!current || !previous) return
    nodeList[idx - 1] = current
    nodeList[idx] = previous
  }
}

function moveDown(nodeList: OutlineNode[], node: OutlineNode) {
  const idx = nodeList.findIndex(n => n._key === node._key)
  if (idx < nodeList.length - 1) {
    const current = nodeList[idx]
    const next = nodeList[idx + 1]
    if (!current || !next) return
    nodeList[idx + 1] = current
    nodeList[idx] = next
  }
}

async function saveOutline() {
  if (nodes.value.length === 0) {
    ElMessage.warning('目录不能为空')
    return
  }
  saving.value = true
  try {
    const apiNodes = nodes.value.map(n => toApiNode(n))
    await outlineApi.save(props.projectId, apiNodes)
    ElMessage.success('目录已保存')
    await loadOutline()
    emit('saved')
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    saving.value = false
  }
}

onMounted(loadOutline)
</script>

<template>
  <div class="panel">
    <div class="panel-header">
      <h2>目录编辑</h2>
      <el-button type="primary" :loading="saving" @click="saveOutline">保存目录</el-button>
    </div>

    <div class="panel-body">
      <!-- 左侧：目录树 -->
      <div class="tree-pane">
        <div class="tree-toolbar">
          <el-button size="small" @click="addRootNode">
            <el-icon><Plus /></el-icon> 新增章
          </el-button>
        </div>
        <div class="tree-scroll">
          <TreeNode
            v-for="node in nodes"
            :key="node._key"
            :node="node"
            :node-list="nodes"
            :selected-key="selectedNode?._key"
            @select="selectNode"
            @add-child="addChildNode"
            @delete="confirmDelete"
            @move-up="(list, n) => moveUp(list, n)"
            @move-down="(list, n) => moveDown(list, n)"
          />
          <div v-if="nodes.length === 0" class="empty-tree">
            暂无目录，点击「新增章」添加
          </div>
        </div>
      </div>

      <!-- 右侧：配置面板 -->
      <div class="config-pane">
        <div v-if="selectedNode" class="config-content">
          <h3 class="config-title">节点配置</h3>
          <el-form label-width="80px" size="default">
            <el-form-item label="标题">
              <el-input v-model="selectedNode.title" />
            </el-form-item>
            <el-form-item label="节点类型">
              <el-select v-model="selectedNode.nodeType">
                <el-option label="章（一级）" value="chapter" />
                <el-option label="节（二级）" value="section" />
              </el-select>
            </el-form-item>
            <el-form-item label="写作要求">
              <el-input
                v-model="selectedNode.promptRequirement"
                type="textarea"
                :rows="6"
                placeholder="描述本章节的写作要求、重点关注事项..."
              />
            </el-form-item>
            <el-form-item label="是否启用">
              <el-switch v-model="selectedNode.isEnabled" />
            </el-form-item>
          </el-form>
        </div>
        <div v-else class="config-empty">
          <el-empty description="点击左侧节点进行配置" />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.panel { height: 100%; display: flex; flex-direction: column; background: transparent; }
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #eef1f5;
  flex-shrink: 0;
}
.panel-header h2 { font-size: 22px; font-weight: 700; color: #111827; }
.panel-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}
.tree-pane {
  width: 360px;
  border-right: 1px solid #eef1f5;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  background: #fcfdff;
}
.tree-toolbar {
  padding: 14px 16px;
  border-bottom: 1px solid #eef1f5;
  background: rgba(255,255,255,0.8);
}
.tree-scroll { flex: 1; overflow-y: auto; padding: 12px; }
.empty-tree { text-align: center; padding: 40px; color: #c0c4cc; font-size: 13px; }
.config-pane {
  flex: 1;
  padding: 28px;
  overflow-y: auto;
  background: linear-gradient(180deg, #ffffff 0%, #fbfcfe 100%);
}
.config-content {
  max-width: 760px;
  padding: 24px;
  border-radius: 18px;
  background: #ffffff;
  border: 1px solid #edf0f5;
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.05);
}
.config-title { font-size: 18px; font-weight: 700; margin-bottom: 20px; color: #111827; }
.config-empty { display: flex; justify-content: center; align-items: center; height: 200px; }
</style>
