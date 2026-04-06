<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { reviewApi } from '../../api'

const props = defineProps<{ projectId: number }>()

const checkResult = ref<any>(null)
const running = ref(false)
const filterLevel = ref<string>('')

const riskConfig: Record<string, { label: string; type: string; color: string }> = {
  high: { label: '高风险', type: 'danger', color: '#f56c6c' },
  medium: { label: '中风险', type: 'warning', color: '#e6a23c' },
  low: { label: '低风险', type: 'info', color: '#909399' },
}

const filteredResults = () => {
  const results = checkResult.value?.results || []
  if (!filterLevel.value) return results
  return results.filter((r: any) => r.riskLevel === filterLevel.value)
}

async function loadCheck() {
  try {
    const res: any = await reviewApi.get(props.projectId)
    checkResult.value = res.data
  } catch {}
}

async function runCheck() {
  running.value = true
  try {
    const res: any = await reviewApi.run(props.projectId)
    checkResult.value = res.data
    ElMessage.success('废标检查完成')
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    running.value = false
  }
}

onMounted(loadCheck)
</script>

<template>
  <div class="panel">
    <div class="panel-header">
      <div>
        <h2>废标项检查</h2>
        <p class="desc">AI 自动检查标书是否覆盖废标条款、资格条款及强制响应项</p>
      </div>
      <el-button type="primary" :loading="running" @click="runCheck">
        {{ running ? '检查中...' : '执行废标检查' }}
      </el-button>
    </div>

    <div class="panel-body">
      <!-- 汇总 -->
      <div v-if="checkResult?.summary" class="summary-row">
        <div class="summary-card high">
          <span class="summary-count">{{ checkResult.summary.high }}</span>
          <span class="summary-label">高风险</span>
        </div>
        <div class="summary-card medium">
          <span class="summary-count">{{ checkResult.summary.medium }}</span>
          <span class="summary-label">中风险</span>
        </div>
        <div class="summary-card low">
          <span class="summary-count">{{ checkResult.summary.low }}</span>
          <span class="summary-label">低风险</span>
        </div>
        <div class="summary-card total">
          <span class="summary-count">
            {{ (checkResult.summary.high || 0) + (checkResult.summary.medium || 0) + (checkResult.summary.low || 0) }}
          </span>
          <span class="summary-label">全部问题</span>
        </div>
      </div>

      <!-- 筛选 -->
      <div v-if="checkResult?.results?.length" class="filter-bar">
        <el-radio-group v-model="filterLevel" size="small">
          <el-radio-button value="">全部</el-radio-button>
          <el-radio-button value="high">高风险</el-radio-button>
          <el-radio-button value="medium">中风险</el-radio-button>
          <el-radio-button value="low">低风险</el-radio-button>
        </el-radio-group>
      </div>

      <!-- 结果列表 -->
      <div class="result-list" v-if="checkResult?.results?.length">
        <div
          v-for="item in filteredResults()"
          :key="item.id"
          class="result-card"
          :class="item.riskLevel"
        >
          <div class="result-header">
            <el-tag :type="riskConfig[item.riskLevel]?.type" size="small">
              {{ riskConfig[item.riskLevel]?.label }}
            </el-tag>
            <span class="result-title">{{ item.title }}</span>
          </div>
          <div class="result-desc">{{ item.description }}</div>
          <div class="result-suggestion" v-if="item.suggestion">
            <el-icon><Aim /></el-icon>
            建议：{{ item.suggestion }}
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <el-empty
        v-if="!checkResult || !checkResult.results?.length"
        description="点击「执行废标检查」进行风险检测"
        :image-size="100"
      />
    </div>
  </div>
</template>

<style scoped>
.panel { height: 100%; display: flex; flex-direction: column; background: #fff; }
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  padding: 20px 32px 16px;
  border-bottom: 1px solid #f0f0f0;
  flex-shrink: 0;
}
.panel-header h2 { font-size: 20px; font-weight: 600; margin-bottom: 4px; }
.desc { color: #909399; font-size: 13px; }
.panel-body { flex: 1; overflow-y: auto; padding: 24px 32px; }

.summary-row {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}
.summary-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid;
}
.summary-card.high { border-color: #fde8e8; background: #fef0f0; }
.summary-card.medium { border-color: #fdf0d3; background: #fdf6ec; }
.summary-card.low { border-color: #e8e8e8; background: #f5f7fa; }
.summary-card.total { border-color: #d9ecff; background: #ecf5ff; }
.summary-count { font-size: 28px; font-weight: 700; }
.summary-card.high .summary-count { color: #f56c6c; }
.summary-card.medium .summary-count { color: #e6a23c; }
.summary-card.low .summary-count { color: #909399; }
.summary-card.total .summary-count { color: #409eff; }
.summary-label { font-size: 12px; color: #606266; margin-top: 4px; }

.filter-bar { margin-bottom: 16px; }

.result-list { display: flex; flex-direction: column; gap: 12px; }
.result-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  border-left-width: 4px;
}
.result-card.high { border-left-color: #f56c6c; }
.result-card.medium { border-left-color: #e6a23c; }
.result-card.low { border-left-color: #909399; }
.result-header { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.result-title { font-size: 15px; font-weight: 500; }
.result-desc { font-size: 14px; color: #303133; line-height: 1.6; margin-bottom: 8px; }
.result-suggestion {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 13px;
  color: #409eff;
  background: #f0f7ff;
  padding: 8px 12px;
  border-radius: 4px;
}
</style>
