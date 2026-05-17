<template>
  <div class="history-page">
    <div class="page-header">
      <h2>预测历史</h2>
    </div>

    <el-table :data="tasks" v-loading="loading" border stripe>
      <el-table-column prop="task_id" label="任务ID" min-width="200" show-overflow-tooltip />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.status === 'completed'" type="success">完成</el-tag>
          <el-tag v-else-if="row.status === 'failed'" type="danger">失败</el-tag>
          <el-tag v-else type="warning">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="elapsed_seconds" label="耗时" width="100">
        <template #default="{ row }">
          {{ row.elapsed_seconds ? row.elapsed_seconds.toFixed(1) + 's' : '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column prop="research_depth" label="深度" width="70">
        <template #default="{ row }">
          {{ row.research_depth || '标准' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button
            v-if="row.status === 'completed'"
            type="primary" text size="small"
            @click="viewDetail(row)"
          >查看详情</el-button>
          <el-button
            v-if="row.status === 'completed' || row.status === 'failed'"
            type="success" text size="small"
            @click="goRetry(row)"
          >重新分析</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-if="total > pageSize"
      v-model:current-page="currentPage"
      :page-size="pageSize"
      :total="total"
      layout="prev, pager, next"
      @current-change="loadHistory"
      style="margin-top: 16px; justify-content: center;"
    />

    <el-dialog v-model="dialogVisible" title="预测详情" width="80%" top="40px">
      <div v-if="detailResult" class="detail-content">
        <el-tabs>
          <el-tab-pane label="最终决策">
            <div class="markdown-body" v-html="renderMarkdown(detailResult.final_index_decision || '')" />
          </el-tab-pane>
          <el-tab-pane label="交易计划">
            <div class="markdown-body" v-html="renderMarkdown(detailResult.index_trading_plan || '')" />
          </el-tab-pane>
          <el-tab-pane label="技术面">
            <div class="markdown-body" v-html="renderMarkdown(detailResult.index_technical_report || '')" />
          </el-tab-pane>
          <el-tab-pane label="情绪面">
            <div class="markdown-body" v-html="renderMarkdown(detailResult.index_sentiment_report || '')" />
          </el-tab-pane>
          <el-tab-pane label="宏观政策">
            <div class="markdown-body" v-html="renderMarkdown(detailResult.macro_policy_report || '')" />
          </el-tab-pane>
          <el-tab-pane label="估值">
            <div class="markdown-body" v-html="renderMarkdown(detailResult.index_valuation_report || '')" />
          </el-tab-pane>
          <el-tab-pane label="板块主线">
            <div class="markdown-body" v-html="renderMarkdown(detailResult.sector_theme_report || '')" />
          </el-tab-pane>
          <el-tab-pane label="指数影响">
            <div class="markdown-body" v-html="renderMarkdown(detailResult.index_impact_report || '')" />
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getPredictionHistory, getTaskResult } from '@/api/indexPrediction'
import { useRouter } from 'vue-router'
import { marked } from 'marked'
import type { PredictionTask, PredictionResult } from '@/types/indexPrediction'

const tasks = ref<PredictionTask[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const detailResult = ref<PredictionResult | null>(null)
const currentPage = ref(1)
const pageSize = 10
const total = ref(0)
const router = useRouter()

function goRetry(task: PredictionTask) {
  router.push('/index-prediction')
}

function formatDate(d: string) {
  return d ? new Date(d).toLocaleString('zh-CN') : ''
}

function renderMarkdown(md: string): string {
  if (!md) return ''
  try { return marked.parse(md) as string } catch { return md }
}

async function loadHistory() {
  loading.value = true
  try {
    const data = await getPredictionHistory({ skip: (currentPage.value - 1) * pageSize, limit: pageSize })
    tasks.value = Array.isArray(data) ? data : ((data as any)?.data || [])
    total.value = data?.length || 0
  } catch (e) {
    /* ignore */
  } finally {
    loading.value = false
  }
}

async function viewDetail(task: PredictionTask) {
  try {
    const data = await getTaskResult(task.task_id)
    detailResult.value = (data as any)?.result || null
    dialogVisible.value = true
  } catch (e) {
    /* ignore */
  }
}

onMounted(() => { loadHistory() })
</script>

<style scoped lang="scss">
.history-page { padding: 20px; }
.page-header { margin-bottom: 16px; h2 { font-size: 20px; } }
.detail-content { max-height: 70vh; overflow-y: auto; }
.markdown-body {
  font-size: 14px;
  line-height: 1.6;
  :deep(h1) { font-size: 18px; }
  :deep(h2) { font-size: 16px; }
}
</style>
