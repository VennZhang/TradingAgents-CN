<template>
  <div class="ipt-page">
    <div class="page-header">
      <h2>指数预测任务管理</h2>
      <el-button size="small" @click="loadTasks">刷新</el-button>
    </div>

    <el-tabs v-model="activeTab" @tab-change="onTabChange" style="margin-bottom:16px">
      <el-tab-pane label="进行中" name="pending" />
      <el-tab-pane label="已完成" name="completed" />
      <el-tab-pane label="失败/取消" name="failed" />
      <el-tab-pane label="全部" name="all" />
    </el-tabs>

    <el-table :data="tasks" v-loading="loading" border stripe size="default">
      <el-table-column prop="task_id" label="任务ID" min-width="180" show-overflow-tooltip />
      <el-table-column label="深度" width="70">
        <template #default="{ row }">{{ row.research_depth || '标准' }}</template>
      </el-table-column>
      <el-table-column label="目标指数" width="150">
        <template #default="{ row }">
          <template v-if="row.target_indices">
            <el-tag v-for="idx in row.target_indices.slice(0,3)" :key="idx" size="small" style="margin:1px">{{ shortIdx(idx) }}</el-tag>
            <span v-if="row.target_indices.length > 3" style="font-size:12px">+{{ row.target_indices.length - 3 }}</span>
          </template>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="进度" width="120">
        <template #default="{ row }">
          <el-progress
            v-if="row.status === 'running'"
            :percentage="row.progress || 0"
            :stroke-width="8"
            :text-inside="true"
          />
          <span v-else-if="row.status === 'completed'">100%</span>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column prop="elapsed_seconds" label="耗时" width="80">
        <template #default="{ row }">{{ row.elapsed_seconds ? row.elapsed_seconds.toFixed(1)+'s' : '-' }}</template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="170">
        <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="240" fixed="right">
        <template #default="{ row }">
          <template v-if="row.status === 'completed'">
            <el-button type="primary" text size="small" @click="viewResult(row)">查看结果</el-button>
            <el-button type="success" text size="small" @click="goRetry(row)">重新分析</el-button>
          </template>
          <template v-else-if="row.status === 'failed'">
            <el-button type="success" text size="small" @click="goRetry(row)">重试</el-button>
          </template>
          <template v-else-if="row.status === 'running' || row.status === 'pending'">
            <el-button type="warning" text size="small" @click="cancelOne(row)">取消</el-button>
            <el-button type="info" text size="small" @click="markFailed(row)">标记失败</el-button>
          </template>
          <el-popconfirm title="确定删除?" @confirm="deleteOne(row)">
            <template #reference>
              <el-button type="danger" text size="small">删除</el-button>
            </template>
          </el-popconfirm>
          <el-button type="primary" text size="small" @click="viewDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-if="total > pageSize"
      v-model:current-page="currentPage"
      :page-size="pageSize"
      :total="total"
      layout="prev, pager, next"
      @current-change="loadTasks"
      style="margin-top:16px;justify-content:center"
    />

    <el-dialog v-model="dialogVisible" title="任务详情" width="80%" top="40px">
      <div v-if="detailContent" class="detail-content">
        <el-tabs>
          <el-tab-pane v-for="(val, key) in detailContent" :key="key" :label="reportLabel(key)">
            <div class="markdown-body" v-html="renderMarkdown(val || '')" />
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { listTasks, getTaskResult, cancelTask, deleteTask, markTaskFailed, retryTask } from '@/api/indexPrediction'
import { marked } from 'marked'
import type { PredictionTask, PredictionResult } from '@/types/indexPrediction'

const router = useRouter()
const tasks = ref<any[]>([])
const loading = ref(false)
const activeTab = ref('pending')
const dialogVisible = ref(false)
const detailContent = ref<any>(null)
const currentPage = ref(1)
const pageSize = 10
const total = ref(0)

const IDX_SHORT: Record<string,string> = {
  '000016.SH':'上证50','000300.SH':'沪深300','000905.SH':'中证500',
  '000852.SH':'中证1000','000688.SH':'科创50','399006.SZ':'创业板指'
}

function shortIdx(code: string) { return IDX_SHORT[code] || code }
function formatDate(d: string) { return d ? new Date(d).toLocaleString('zh-CN') : '' }
function renderMarkdown(md: string) { if (!md) return ''; try { return marked.parse(md) as string } catch { return md } }

function statusType(s: string) {
  const m: Record<string, string> = { pending:'info', running:'warning', completed:'success', failed:'danger', cancelled:'info' }
  return m[s] || 'info'
}
function statusText(s: string) {
  const m: Record<string, string> = { pending:'等待中', running:'分析中', completed:'已完成', failed:'失败', cancelled:'已取消' }
  return m[s] || s
}
function reportLabel(key: string) {
  const m: Record<string, string> = {
    final_index_decision:'最终决策', index_trading_plan:'交易计划',
    index_technical_report:'指数技术面', index_sentiment_report:'资金情绪',
    macro_policy_report:'宏观政策', index_valuation_report:'指数估值',
    sector_theme_report:'板块主线', index_impact_report:'指数影响',
    index_investment_plan:'研究结论'
  }
  return m[key] || key
}

async function loadTasks() {
  loading.value = true
  try {
    const status = activeTab.value === 'failed' ? undefined : (activeTab.value === 'all' ? undefined : activeTab.value)
    const apiParams: any = { skip: (currentPage.value - 1) * pageSize, limit: pageSize }
    if (activeTab.value === 'pending') apiParams.status = 'running'
    else if (activeTab.value !== 'all' && activeTab.value !== 'failed') apiParams.status = activeTab.value
    const data = await listTasks(apiParams)
    let list = (data as any)?.tasks || data || []
    if (activeTab.value === 'failed') list = list.filter((t: any) => t.status === 'failed' || t.status === 'cancelled')
    else if (activeTab.value === 'pending') list = list.filter((t: any) => t.status === 'running' || t.status === 'pending')
    tasks.value = list
    total.value = list.length
  } catch (e) {
    ElMessage.error('加载任务列表失败')
  } finally { loading.value = false }
}

function onTabChange() { currentPage.value = 1; loadTasks() }

async function viewResult(row: any) {
  try {
    const data = await getTaskResult(row.task_id)
    detailContent.value = (data as any)?.result || {}
    dialogVisible.value = true
  } catch (e) { ElMessage.error('获取结果失败') }
}

async function viewDetail(row: any) {
  try {
    const data = await getTaskResult(row.task_id)
    detailContent.value = (data as any)?.result || (data as any) || {}
    dialogVisible.value = true
  } catch (e) { ElMessage.error('获取详情失败') }
}

async function cancelOne(row: any) {
  try {
    await cancelTask(row.task_id)
    ElMessage.success('已取消')
    loadTasks()
  } catch (e) { ElMessage.error('取消失败') }
}

async function markFailed(row: any) {
  try {
    await markTaskFailed(row.task_id)
    ElMessage.success('已标记为失败')
    loadTasks()
  } catch (e) { ElMessage.error('操作失败') }
}

async function deleteOne(row: any) {
  try {
    await deleteTask(row.task_id)
    ElMessage.success('已删除')
    loadTasks()
  } catch (e) { ElMessage.error('删除失败') }
}

async function goRetry(row: any) {
  router.push('/index-prediction')
}

onMounted(() => { loadTasks() })
</script>

<style scoped lang="scss">
.ipt-page { padding: 20px; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; h2 { font-size: 20px; margin: 0; } }
.detail-content { max-height: 70vh; overflow-y: auto; }
.markdown-body { font-size: 14px; line-height: 1.6; :deep(h1){font-size:18px} :deep(h2){font-size:16px} }
</style>
