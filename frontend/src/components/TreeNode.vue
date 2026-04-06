<script setup lang="ts">
interface OutlineNode {
  id?: number
  title: string
  nodeType: string
  promptRequirement: string
  isEnabled: boolean
  orderNo: number
  children: OutlineNode[]
  _key: string
}

const props = defineProps<{
  node: OutlineNode
  nodeList: OutlineNode[]
  selectedKey?: string
}>()

const emit = defineEmits<{
  (e: 'select', node: OutlineNode): void
  (e: 'addChild', node: OutlineNode): void
  (e: 'delete', node: OutlineNode): void
  (e: 'moveUp', list: OutlineNode[], node: OutlineNode): void
  (e: 'moveDown', list: OutlineNode[], node: OutlineNode): void
}>()
</script>

<template>
  <div class="tree-node">
    <div
      class="node-row"
      :class="{ selected: node._key === selectedKey, disabled: !node.isEnabled }"
      @click="emit('select', node)"
    >
      <el-icon class="node-icon">
        <component :is="node.nodeType === 'chapter' ? 'FolderOpened' : 'Document'" />
      </el-icon>
      <span class="node-title">{{ node.title }}</span>
      <div class="node-actions" @click.stop>
        <el-tooltip content="上移">
          <el-button text size="small" @click="emit('moveUp', nodeList, node)">
            <el-icon><ArrowUp /></el-icon>
          </el-button>
        </el-tooltip>
        <el-tooltip content="下移">
          <el-button text size="small" @click="emit('moveDown', nodeList, node)">
            <el-icon><ArrowDown /></el-icon>
          </el-button>
        </el-tooltip>
        <el-tooltip content="添加子节">
          <el-button text size="small" @click="emit('addChild', node)">
            <el-icon><Plus /></el-icon>
          </el-button>
        </el-tooltip>
        <el-tooltip content="删除">
          <el-button text size="small" type="danger" @click="emit('delete', node)">
            <el-icon><Delete /></el-icon>
          </el-button>
        </el-tooltip>
      </div>
    </div>
    <!-- 子节点 -->
    <div class="children" v-if="node.children.length > 0">
      <TreeNode
        v-for="child in node.children"
        :key="child._key"
        :node="child"
        :node-list="node.children"
        :selected-key="selectedKey"
        @select="emit('select', $event)"
        @add-child="emit('addChild', $event)"
        @delete="emit('delete', $event)"
        @move-up="(list, n) => emit('moveUp', list, n)"
        @move-down="(list, n) => emit('moveDown', list, n)"
      />
    </div>
  </div>
</template>

<style scoped>
.tree-node { margin-bottom: 4px; }
.node-row {
  --actions-width: 132px;
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  padding: 9px 10px;
  border-radius: 12px;
  cursor: pointer;
  transition: background 0.15s, box-shadow 0.15s, padding-right 0.15s;
  border: 1px solid transparent;
}
.node-row:hover,
.node-row.selected {
  padding-right: calc(10px + var(--actions-width));
}
.node-row:hover { background: #f7fbff; border-color: #e1efff; }
.node-row.selected {
  background: linear-gradient(180deg, #eef6ff 0%, #e7f2ff 100%);
  color: #409eff;
  border-color: rgba(64, 158, 255, 0.24);
  box-shadow: inset 0 0 0 1px rgba(64, 158, 255, 0.12);
}
.node-row.disabled { opacity: 0.45; }
.node-icon { font-size: 16px; flex-shrink: 0; }
.node-title {
  flex: 1;
  min-width: 0;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.node-actions {
  position: absolute;
  top: 50%;
  right: 10px;
  display: flex;
  align-items: center;
  gap: 2px;
  opacity: 0;
  pointer-events: none;
  transform: translateY(-50%);
  transition: opacity 0.15s;
}
.node-row:hover .node-actions,
.node-row.selected .node-actions {
  opacity: 1;
  pointer-events: auto;
}
.children { padding-left: 20px; border-left: 2px solid #eaf0f6; margin-left: 12px; }
</style>
