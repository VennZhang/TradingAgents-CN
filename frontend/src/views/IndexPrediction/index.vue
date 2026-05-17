<template>
  <div class="ip-page">
    <div class="page-header">
      <h2>指数预测分析</h2>
      <p class="subtitle">基于主观预期 + 多智能体分析，预测六大宽基指数走势</p>
    </div>

    <el-row v-if="!pageLoading" :gutter="16" class="ip-main">
      <el-col :span="18" class="ip-form-col">
        <el-card shadow="never">
          <template #header><strong>分析配置</strong></template>

          <!-- 指数选择 -->
          <div class="section-label">选择目标指数</div>
          <div class="index-cards">
            <div
              v-for="idx in indices"
              :key="idx.code"
              class="index-card"
              :class="{ active: selectedIndices.includes(idx.code) }"
              @click="toggleIndex(idx.code)"
            >
              <div class="ic-name">{{ idx.display }}</div>
              <div class="ic-code">{{ idx.code }}</div>
              <div class="ic-tags">
                <el-tag size="small" type="info">{{ idx.market }}</el-tag>
                <el-tag v-if="idx.futures !== '-'" size="small" type="warning">{{ idx.futures }}</el-tag>
              </div>
              <el-icon v-if="selectedIndices.includes(idx.code)" class="ic-check"><CircleCheck /></el-icon>
            </div>
          </div>
          <el-button-group size="small" style="margin-top:8px">
            <el-button @click="selectAllIndices">全选</el-button>
            <el-button @click="selectedIndices = []">清空</el-button>
          </el-button-group>

          <!-- 分析深度 -->
          <div class="section-label" style="margin-top:20px">分析深度</div>
          <div class="depth-selector">
            <div
              v-for="d in depthLevels"
              :key="d.id"
              class="depth-option"
              :class="{ active: selectedDepth === d.name }"
              @click="selectedDepth = d.name"
            >
              <div class="do-icon">{{ d.icon }}</div>
              <div class="do-name">{{ d.name }}</div>
              <div class="do-desc">{{ d.desc }}</div>
              <div class="do-time">{{ d.time }}</div>
            </div>
          </div>

          <!-- 分析师选择 -->
          <div class="section-label" style="margin-top:20px">选择分析师</div>
          <div class="analyst-grid">
            <div
              v-for="a in analysts"
              :key="a.id"
              class="analyst-card"
              :class="{ active: selectedAnalysts.includes(a.id) }"
              @click="toggleAnalyst(a.id)"
            >
              <div class="ac-icon">{{ a.icon }}</div>
              <div class="ac-name">{{ a.name }}</div>
              <div class="ac-desc">{{ a.desc }}</div>
              <el-icon v-if="selectedAnalysts.includes(a.id)" class="ac-check"><CircleCheck /></el-icon>
            </div>
          </div>

          <!-- 预期选择 -->
          <div class="section-label" style="margin-top:20px">选择预期</div>
          <div style="display:flex;align-items:center;gap:8px">
            <el-select v-model="selectedExpectationId" placeholder="选择预期（可选）" clearable style="flex:1">
              <el-option
                v-for="exp in expectations"
                :key="exp._id"
                :label="exp.title"
                :value="exp._id"
              >
                <span>{{ exp.title }}</span>
                <el-tag v-if="exp.is_active" size="small" type="success" style="margin-left:8px">激活</el-tag>
              </el-option>
            </el-select>
            <el-button v-if="selectedExpectationId && !selectedExpectation?.is_active" size="small" @click="quickActivate">⭐ 设为激活</el-button>
            <el-button size="small" @click="$router.push('/expectations')">+ 管理预期</el-button>
          </div>
          <el-card v-if="selectedExpectation" shadow="never" class="expectation-summary" size="small">
            <div v-if="selectedExpectation.content.policy_long_term">
              <strong>长期政策:</strong> {{ selectedExpectation.content.policy_long_term.slice(0, 80) }}...
            </div>
            <div v-if="selectedExpectation.content.economic_phase">
              <strong>经济周期:</strong> {{ selectedExpectation.content.economic_phase }}
            </div>
            <div v-if="selectedExpectation.content.market_trend">
              <strong>市场大势:</strong> {{ selectedExpectation.content.market_trend }}
            </div>
            <div v-if="selectedExpectation.content.sector_views?.length">
              <strong>板块观点:</strong>
              <el-tag v-for="sv in selectedExpectation.content.sector_views" :key="sv.sector_name" size="small" style="margin:2px">
                {{ sv.sector_name }}({{ sv.confidence }})
              </el-tag>
            </div>
          </el-card>
        </el-card>

        <!-- 开始按钮 -->
        <div style="text-align:center;margin-top:16px">
          <el-button
            v-if="analysisState === 'idle'"
            type="primary"
            size="large"
            style="width:280px;height:56px;font-size:16px"
            :disabled="selectedIndices.length === 0 || selectedAnalysts.length < 2"
            @click="startAnalysis"
          >开始智能预测</el-button>

          <el-button
            v-if="analysisState === 'running'"
            type="warning"
            size="large"
            style="width:220px;height:56px;font-size:16px"
            disabled
            :loading="true"
          >分析进行中...</el-button>

          <div v-if="analysisState === 'running'" style="display:flex;gap:8px;justify-content:center;margin-top:8px">
            <el-button type="danger" size="small" @click="cancelCurrentTask">取消分析</el-button>
            <el-button size="small" @click="$router.push('/index-prediction/tasks')">任务管理</el-button>
          </div>

          <div v-if="analysisState === 'completed' || analysisState === 'failed'" style="display:flex;gap:8px;justify-content:center">
            <el-button v-if="showResults" type="info" @click="showResults = false">隐藏结果</el-button>
            <el-button v-else type="success" @click="showResults = true">查看结果</el-button>
            <el-button type="primary" @click="startAnalysis">重新分析</el-button>
          </div>
        </div>
      </el-col>

      <!-- 右侧配置侧栏 -->
      <el-col :span="6" class="ip-sidebar">
        <el-card shadow="never">
          <template #header><strong>AI模型配置</strong></template>
          <el-form label-position="top" size="default">
            <el-form-item label="快速分析模型">
              <el-select v-model="quickModel" placeholder="选择模型" style="width:100%">
                <el-option v-for="m in availableModels" :key="m.model_name" :label="m.model_display_name || m.model_name" :value="m.model_name" />
              </el-select>
            </el-form-item>
            <el-form-item label="深度分析模型">
              <el-select v-model="deepModel" placeholder="选择模型" style="width:100%">
                <el-option v-for="m in availableModels" :key="m.model_name" :label="m.model_display_name || m.model_name" :value="m.model_name" />
              </el-select>
            </el-form-item>
            <el-form-item label="分析日期">
              <el-date-picker v-model="analysisDate" type="date" placeholder="默认今天" style="width:100%" value-format="YYYY-MM-DD" />
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <!-- 进度展示 -->
    <el-card v-if="analysisState === 'running'" class="progress-card" shadow="never">
      <template #header><strong>分析进度</strong></template>
      <el-progress :percentage="progress" :stroke-width="16" :text-inside="true" :color="progressColor" style="margin-bottom:12px" />
      <div v-if="currentStep" class="progress-info">
        <span class="step-name">当前步骤: {{ currentStep }}</span>
        <span v-if="currentStepDesc" class="step-desc"> — {{ currentStepDesc }}</span>
      </div>
      <div v-if="elapsedSeconds > 0" class="time-stats">
        ⏱ 已耗时 {{ formatTime(elapsedSeconds) }}
        <span v-if="estimatedRemaining !== null"> | 预计剩余 {{ formatTime(estimatedRemaining) }}</span>
      </div>
    </el-card>

    <el-card v-if="analysisState === 'running'" class="pipeline-card" shadow="never">
      <template #header><strong>📋 Agent 运行状态</strong></template>
      <div v-if="pipelineStages.length > 0" class="pipeline-grid">
        <div
          v-for="st in pipelineStages"
          :key="st.id"
          class="pipeline-item"
          :class="'pipeline-' + st.status"
        >
          <span class="pi-icon">
            {{ st.status === 'completed' ? '✅' : st.status === 'running' ? '🔄' : '⏳' }}
          </span>
          <span class="pi-name">{{ st.name }}</span>
          <span v-if="st.time" class="pi-time">{{ st.time }}s</span>
        </div>
      </div>
      <div v-else class="pipeline-waiting">
        ⏳ 等待 Agent 状态更新中...
      </div>
    </el-card>

    <!-- 结果展示 -->
    <div v-if="analysisState === 'completed' && showResults && result" class="results-section">
      <el-alert type="warning" :closable="false" style="margin-bottom:16px">
        <template #title>⚠️ 风险提示：本分析结果仅供参考，不构成任何投资建议。指数期货/期权交易具有高风险性，请审慎决策。</template>
      </el-alert>

      <el-card shadow="never" class="decision-card">
        <template #header>
          <strong>📊 综合判断</strong>
          <el-tag type="success" style="float:right">分析完成</el-tag>
        </template>
        <div class="markdown-body" v-html="renderMarkdown(result.final_index_decision || result.index_investment_plan || '')" />
      </el-card>

      <el-tabs type="card" class="report-tabs" v-model="activeTab">
        <el-tab-pane label="最终决策" name="decision">
          <div class="markdown-body" v-html="renderMarkdown(result.final_index_decision || '')" />
        </el-tab-pane>
        <el-tab-pane label="交易计划" name="trading">
          <div class="markdown-body" v-html="renderMarkdown(result.index_trading_plan || '')" />
        </el-tab-pane>
        <el-tab-pane label="指数技术面" name="tech">
          <div class="markdown-body" v-html="renderMarkdown(result.index_technical_report || '')" />
        </el-tab-pane>
        <el-tab-pane label="资金情绪" name="sentiment">
          <div class="markdown-body" v-html="renderMarkdown(result.index_sentiment_report || '')" />
        </el-tab-pane>
        <el-tab-pane label="宏观政策" name="macro">
          <div class="markdown-body" v-html="renderMarkdown(result.macro_policy_report || '')" />
        </el-tab-pane>
        <el-tab-pane label="指数估值" name="valuation">
          <div class="markdown-body" v-html="renderMarkdown(result.index_valuation_report || '')" />
        </el-tab-pane>
        <el-tab-pane label="板块主线" name="sector">
          <div class="markdown-body" v-html="renderMarkdown(result.sector_theme_report || '')" />
        </el-tab-pane>
        <el-tab-pane label="指数影响" name="impact">
          <div class="markdown-body" v-html="renderMarkdown(result.index_impact_report || '')" />
        </el-tab-pane>
      </el-tabs>

      <div style="display:flex;gap:8px;margin-top:12px">
        <el-button @click="$router.push('/index-prediction/history')">查看历史</el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { CircleCheck } from '@element-plus/icons-vue'
import { getExpectations, activateExpectation } from '@/api/expectations'
import { startPrediction, getTaskStatus, getTaskResult, getIndices, cancelTask, deleteTask } from '@/api/indexPrediction'
import { configApi } from '@/api/config'
import { marked } from 'marked'
import type { Expectation } from '@/types/expectation'
import type { IndexMetadata, PredictionResult, DepthLevel } from '@/types/indexPrediction'

const STORAGE_KEY = 'index_prediction_current_task'
const CACHE_TTL = 30 * 60 * 1000

const expectations = ref<Expectation[]>([])
const indices = ref<IndexMetadata[]>([])
const availableModels = ref<any[]>([])
const selectedIndices = ref<string[]>(['000016.SH', '000300.SH', '000905.SH', '000852.SH', '000688.SH', '399006.SZ'])
const selectedAnalysts = ref<string[]>(['tech', 'sentiment', 'macro', 'valuation'])
const selectedDepth = ref('标准')
const selectedExpectationId = ref('')
const quickModel = ref('qwen-plus')
const deepModel = ref('qwen-max')
const analysisDate = ref('')

const analysisState = ref<'idle' | 'running' | 'completed' | 'failed'>('idle')
const currentTaskId = ref('')
const showResults = ref(false)
const result = ref<PredictionResult | null>(null)
const activeTab = ref('decision')
let stopPollingFlag = false
let wsConnection: WebSocket | null = null

const pipelineStages = ref<any[]>([])
const pageLoading = ref(true)

const progress = ref(0)
const currentStep = ref('')
const currentStepDesc = ref('')
const elapsedSeconds = ref(0)
const estimatedRemaining = ref<number | null>(null)

const depthLevels: DepthLevel[] = [
  { id: 1, name: '快速', desc: '1轮辩论', time: '2-5分钟', icon: '⚡' },
  { id: 2, name: '基础', desc: '1轮辩论+记忆', time: '3-6分钟', icon: '📋' },
  { id: 3, name: '标准', desc: '2轮风险', time: '4-8分钟', icon: '🎯' },
  { id: 4, name: '深度', desc: '2+2轮', time: '6-11分钟', icon: '🔬' },
  { id: 5, name: '全面', desc: '3+3轮', time: '8-16分钟', icon: '🏆' },
]

const analysts = [
  { id: 'tech', name: '指数技术面', desc: '趋势/支撑阻力/MACD/布林带', icon: '📊' },
  { id: 'sentiment', name: '资金情绪', desc: '期货持仓/北向资金/ETF/两融', icon: '💰' },
  { id: 'macro', name: '宏观政策', desc: 'CPI/PMI/央行政策/地缘事件', icon: '🏛️' },
  { id: 'valuation', name: '指数估值', desc: 'PE/PB历史分位/板块结构', icon: '📈' },
]

const selectedExpectation = computed(() =>
  expectations.value.find(e => e._id === selectedExpectationId.value)
)

const progressColor = computed(() => {
  const p = progress.value
  if (p < 30) return '#409eff'
  if (p < 70) return '#e6a23c'
  return '#67c23a'
})

function toggleIndex(code: string) {
  const i = selectedIndices.value.indexOf(code)
  if (i >= 0) selectedIndices.value.splice(i, 1)
  else selectedIndices.value.push(code)
}

function selectAllIndices() {
  selectedIndices.value = indices.value.map(i => i.code)
}

function toggleAnalyst(id: string) {
  const i = selectedAnalysts.value.indexOf(id)
  if (i >= 0) selectedAnalysts.value.splice(i, 1)
  else selectedAnalysts.value.push(id)
}

function formatTime(s: number): string {
  const m = Math.floor(s / 60)
  const sec = Math.floor(s % 60)
  return m > 0 ? `${m}分${sec}秒` : `${sec}秒`
}

function saveCache() {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify({
      taskId: currentTaskId.value,
      timestamp: Date.now(),
      params: {
        expectation_id: selectedExpectationId.value || undefined,
        target_indices: selectedIndices.value,
        research_depth: selectedDepth.value,
        selected_analysts: selectedAnalysts.value,
        quick_analysis_model: quickModel.value || undefined,
        deep_analysis_model: deepModel.value || undefined,
        analysis_date: analysisDate.value || undefined,
      },
    }))
  } catch (e) { /* ignore */ }
}

function loadCache(): any {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const c = JSON.parse(raw)
    if (Date.now() - c.timestamp > CACHE_TTL) {
      sessionStorage.removeItem(STORAGE_KEY)
      return null
    }
    return c
  } catch (e) { sessionStorage.removeItem(STORAGE_KEY); return null }
}

function clearCache() {
  try { sessionStorage.removeItem(STORAGE_KEY) } catch (e) { /* ignore */ }
}

function connectWebSocket(taskId: string) {
  disconnectWebSocket()
  try {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
    const url = `${protocol}//${location.host}/api/index-prediction/ws/index-prediction/${taskId}`
    const ws = new WebSocket(url)
    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        if (msg.type === 'pipeline_status') {
          pipelineStages.value = msg.stages || []
          if (msg.progress !== undefined) progress.value = msg.progress
          if (msg.elapsed_seconds !== undefined) elapsedSeconds.value = msg.elapsed_seconds
        }
      } catch (e) { /* ignore parse errors */ }
    }
    ws.onerror = () => { /* WebSocket error, polling will cover */ }
    wsConnection = ws
  } catch (e) { /* WebSocket not available, polling covers */ }
}

function disconnectWebSocket() {
  if (wsConnection) {
    try { wsConnection.close() } catch (e) { /* ignore */ }
    wsConnection = null
  }
}

const ALL_STAGES = [
  { id: 'tech', name: '指数技术面分析师' },
  { id: 'sentiment', name: '资金情绪分析师' },
  { id: 'macro', name: '宏观政策分析师' },
  { id: 'valuation', name: '指数估值分析师' },
  { id: 'sector', name: '板块主线分析师' },
  { id: 'impact', name: '指数影响分析师' },
  { id: 'debate', name: '多空辩论' },
  { id: 'manager', name: '研究裁判' },
  { id: 'trader', name: '指数交易员' },
  { id: 'risk', name: '风险辩论' },
  { id: 'risk_manager', name: '风险裁判' },
]

function buildFallbackStages(currentStepName: string) {
  const idx = ALL_STAGES.findIndex(s => s.name === currentStepName || currentStepName?.includes(s.name))
  return ALL_STAGES.map((s, i) => ({
    id: s.id,
    name: s.name,
    status: i < idx ? 'completed' : i === idx ? 'running' : 'pending',
    time: 0,
  }))
}

function cancelCurrentTask() {
  if (analysisState.value !== 'running' && analysisState.value !== 'completed') {
    analysisState.value = 'idle'
    return
  }

  stopPollingFlag = true
  disconnectWebSocket()
  const tid = currentTaskId.value

  analysisState.value = 'idle'
  progress.value = 0
  pipelineStages.value = []
  currentTaskId.value = ''
  clearCache()

  if (tid) {
    cancelTask(tid).then(() => {
      ElMessage.success('任务已停止')
    }).catch(() => {
      ElMessage.warning('任务已停止（状态可能未同步到服务器）')
    })
  } else {
    ElMessage.info('已重置分析状态')
  }
}

function renderMarkdown(md: string): string {
  if (!md) return ''
  try { return marked.parse(md) as string } catch { return md.replace(/\n/g, '<br>') }
}

async function loadData() {
  const results = await Promise.allSettled([
    getExpectations(),
    getIndices(),
    configApi.getLLMConfigs(),
  ])

  const expResult = results[0]
  if (expResult.status === 'fulfilled') {
    const data = expResult.value
    expectations.value = Array.isArray(data) ? data : ((data as any)?.data || [])
  }

  const idxResult = results[1]
  if (idxResult.status === 'fulfilled') {
    const data = idxResult.value
    indices.value = Array.isArray(data) ? data : ((data as any)?.data || [])
  }
  if (indices.value.length === 0) {
    indices.value = [
      { code: '000016.SH', display: '上证50', market: '上证', futures: 'IH' },
      { code: '000300.SH', display: '沪深300', market: '中证', futures: 'IF' },
      { code: '000905.SH', display: '中证500', market: '中证', futures: 'IC' },
      { code: '000852.SH', display: '中证1000', market: '中证', futures: 'IM' },
      { code: '000688.SH', display: '科创50', market: '上证', futures: '-' },
      { code: '399006.SZ', display: '创业板指', market: '深证', futures: '-' },
    ]
  }

  const modelResult = results[2]
  if (modelResult.status === 'fulfilled') {
    const models = modelResult.value
    availableModels.value = (Array.isArray(models) ? models : []).filter(
      (m: any) => m.enabled !== false && m.is_active !== false
    )
    if (availableModels.value.length > 0) {
      if (!quickModel.value || !availableModels.value.find((m: any) => m.model_name === quickModel.value)) {
        quickModel.value = availableModels.value[0]?.model_name || 'qwen-plus'
      }
      if (!deepModel.value || !availableModels.value.find((m: any) => m.model_name === deepModel.value)) {
        deepModel.value = availableModels.value[availableModels.value.length - 1]?.model_name || 'qwen-max'
      }
    }
  }

  if (!selectedExpectationId.value && expectations.value.length > 0) {
    const active = expectations.value.find((e: any) => e.is_active)
    if (active) selectedExpectationId.value = active._id
  }
}

async function quickActivate() {
  if (!selectedExpectationId.value) return
  try {
    await activateExpectation(selectedExpectationId.value)
    ElMessage.success('已设为激活预期')
    await loadData()
  } catch (e: any) {
    ElMessage.error('激活失败')
  }
}

async function startAnalysis() {
  if (selectedIndices.value.length === 0) {
    ElMessage.warning('请至少选择一个目标指数')
    return
  }
  if (selectedAnalysts.value.length < 2) {
    ElMessage.warning('请至少选择2个分析师')
    return
  }

  analysisState.value = 'running'
  progress.value = 0
  currentStep.value = ''
  currentStepDesc.value = ''
  elapsedSeconds.value = 0
  estimatedRemaining.value = null
  result.value = null
  showResults.value = false
  pipelineStages.value = []

  try {
    const data = await startPrediction({
      expectation_id: selectedExpectationId.value || undefined,
      target_indices: selectedIndices.value,
      research_depth: selectedDepth.value,
      selected_analysts: selectedAnalysts.value,
      quick_analysis_model: quickModel.value || undefined,
      deep_analysis_model: deepModel.value || undefined,
      analysis_date: analysisDate.value || undefined,
    })
    currentTaskId.value = (data as any)?.task_id || data.task_id
    if (!currentTaskId.value) {
      ElMessage.error('启动分析失败：未获取到任务ID')
      analysisState.value = 'failed'
      return
    }
    console.log('[start] taskId=', currentTaskId.value, 'saving cache, connecting WS')
    connectWebSocket(currentTaskId.value)
    saveCache()
    console.log('[start] starting poll')
    await pollTask()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '启动分析失败')
    analysisState.value = 'failed'
  }
}

async function pollTask() {
  stopPollingFlag = false
  let failures = 0
  for (let i = 0; i < 300; i++) {
    if (stopPollingFlag) return
    await new Promise(resolve => setTimeout(resolve, 2000))
    if (stopPollingFlag) return
    try {
      const data = await getTaskStatus(currentTaskId.value)
      const status = (data as any)
      failures = 0

      progress.value = status?.progress || 0
      currentStep.value = status?.current_step || ''
      currentStepDesc.value = status?.current_step_description || ''
      elapsedSeconds.value = status?.elapsed_seconds || 0
      estimatedRemaining.value = status?.estimated_remaining_seconds ?? null

      if (status?.current_step) {
        const fallback = buildFallbackStages(status.current_step)
        if (fallback.length > 0) pipelineStages.value = fallback
      }

      if (status?.status === 'completed') {
        analysisState.value = 'completed'
        showResults.value = true
        clearCache()
        disconnectWebSocket()
        await loadResult()
        return
      }
      if (status?.status === 'failed') {
        analysisState.value = 'failed'
        clearCache()
        disconnectWebSocket()
        ElMessage.error('分析失败')
        return
      }
      if (status?.status === 'cancelled') {
        clearCache()
        disconnectWebSocket()
        analysisState.value = 'idle'
        pipelineStages.value = []
        ElMessage.info('任务已取消')
        return
      }
    } catch (e: any) {
      failures++
      if (e?.response?.status === 404 || failures > 5) {
        clearCache()
        disconnectWebSocket()
        analysisState.value = 'idle'
        pipelineStages.value = []
        if (failures > 5) ElMessage.warning('无法连接到分析服务')
        return
      }
    }
  }
  clearCache()
  disconnectWebSocket()
  analysisState.value = 'failed'
  ElMessage.warning('分析超时')
}

async function loadResult() {
  try {
    const data = await getTaskResult(currentTaskId.value)
    if (!data) return
    const r = (data as any)
    const res = r?.result || r?.data || r
    if (res && typeof res === 'object' && Object.keys(res).length > 0) {
      result.value = res
    } else {
      await ElMessageBox.alert('分析完成但结果为空，请查看任务管理中的详情', '提示')
    }
  } catch (e) { /* result may not be ready yet, polling will retry */ }
}

async function clearCurrentResults() {
  result.value = null
  showResults.value = false
  analysisState.value = 'idle'
  progress.value = 0
}

watch(() => quickModel.value, () => selectedDepth.value, () => {
  const depth = selectedDepth.value
  if (depth === '快速') { quickModel.value = 'qwen-turbo'; deepModel.value = 'qwen-plus' }
  else if (depth === '基础') { quickModel.value = 'qwen-plus'; deepModel.value = 'qwen-max' }
  else if (depth === '标准') { quickModel.value = 'qwen-plus'; deepModel.value = 'qwen-max' }
  else if (depth === '深度') { quickModel.value = 'qwen-max'; deepModel.value = 'qwen-max' }
  else { quickModel.value = 'qwen-max'; deepModel.value = 'qwen-max' }
})

onMounted(async () => {
  await loadData()
  const cached = loadCache()
  if (cached && cached.taskId) {
    currentTaskId.value = cached.taskId
    if (cached.params) {
      selectedIndices.value = cached.params.target_indices || selectedIndices.value
      selectedDepth.value = cached.params.research_depth || '标准'
      selectedAnalysts.value = cached.params.selected_analysts || selectedAnalysts.value
      quickModel.value = cached.params.quick_analysis_model || quickModel.value
      deepModel.value = cached.params.deep_analysis_model || deepModel.value
      analysisDate.value = cached.params.analysis_date || ''
      if (cached.params.expectation_id) selectedExpectationId.value = cached.params.expectation_id
    }
    pageLoading.value = false
    analysisState.value = 'running'
    connectWebSocket(cached.taskId)
    await pollTask()
  } else {
    pageLoading.value = false
  }
})

onBeforeUnmount(() => {
  stopPollingFlag = true
  disconnectWebSocket()
})
</script>

<style scoped lang="scss">
.ip-page { padding: 20px; }
.page-header { margin-bottom: 16px; h2 { font-size: 22px; margin: 0 0 4px; } .subtitle { color: #909399; font-size: 13px; margin: 0; } }
.ip-main { margin-bottom: 16px; }
.section-label { font-size: 14px; font-weight: 600; color: #303133; margin-bottom: 8px; padding-bottom: 4px; border-bottom: 1px solid #ebeef5; }

.index-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  .index-card {
    padding: 12px;
    border: 2px solid #e4e7ed;
    border-radius: 8px;
    cursor: pointer;
    position: relative;
    transition: all 0.2s;
    &:hover { border-color: #b3d8ff; }
    &.active { border-color: #409eff; background: #ecf5ff; }
    .ic-name { font-size: 15px; font-weight: 600; }
    .ic-code { font-size: 12px; color: #909399; margin: 4px 0; }
    .ic-tags { display: flex; gap: 4px; }
    .ic-check { position: absolute; top: 6px; right: 6px; color: #409eff; font-size: 20px; }
  }
}

.depth-selector {
  display: flex;
  gap: 8px;
  .depth-option {
    flex: 1;
    padding: 10px 6px;
    border: 2px solid #e4e7ed;
    border-radius: 8px;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s;
    &:hover { border-color: #b3d8ff; }
    &.active { border-color: #409eff; background: #ecf5ff; }
    .do-icon { font-size: 22px; }
    .do-name { font-size: 14px; font-weight: 600; margin-top: 4px; }
    .do-desc { font-size: 11px; color: #909399; }
    .do-time { font-size: 11px; color: #67c23a; }
  }
}

.analyst-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  .analyst-card {
    padding: 12px;
    border: 2px solid #e4e7ed;
    border-radius: 8px;
    cursor: pointer;
    position: relative;
    transition: all 0.2s;
    &:hover { border-color: #b3d8ff; }
    &.active { border-color: #409eff; background: #ecf5ff; }
    .ac-icon { font-size: 20px; }
    .ac-name { font-size: 14px; font-weight: 600; margin: 4px 0; }
    .ac-desc { font-size: 11px; color: #909399; }
    .ac-check { position: absolute; top: 6px; right: 6px; color: #409eff; font-size: 20px; }
  }
}

.ip-sidebar { .el-card { margin-bottom: 0; } }

.expectation-summary {
  margin-top: 8px;
  background: #f5f7fa;
  font-size: 13px;
  :deep(.el-card__body) { padding: 10px 12px; }
  div { margin: 4px 0; }
}

.progress-card { margin-bottom: 16px; }
.progress-info { font-size: 14px; color: #303133; margin-bottom: 8px; .step-name { font-weight: 600; } .step-desc { color: #909399; } }
.time-stats { font-size: 13px; color: #606266; }

.pipeline-card { margin-bottom: 16px; }
.pipeline-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}
.pipeline-item {
  padding: 10px 8px;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  text-align: center;
  font-size: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  transition: all 0.3s;
}
.pipeline-completed {
  border-color: #67c23a;
  background: #f0f9eb;
}
.pipeline-running {
  border-color: #409eff;
  background: #ecf5ff;
  animation: pulse 1.5s infinite;
}
.pipeline-pending {
  border-color: #e4e7ed;
  background: #fafafa;
  opacity: 0.7;
}
.pipeline-item .pi-icon { font-size: 16px; }
.pipeline-item .pi-name { font-weight: 600; color: #303133; }
.pipeline-item .pi-time { color: #909399; font-size: 11px; }
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.65; }
}

.results-section {
  .markdown-body {
    max-height: 600px;
    overflow-y: auto;
    font-size: 14px;
    line-height: 1.6;
    :deep(h1) { font-size: 18px; }
    :deep(h2) { font-size: 16px; }
    :deep(h3) { font-size: 15px; }
  }
  .report-tabs { margin-top: 16px; }
}
</style>
