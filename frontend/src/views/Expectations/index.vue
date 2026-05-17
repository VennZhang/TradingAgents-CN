<template>
  <div class="expectations-page">
    <div class="page-header">
      <h2>预期管理</h2>
      <p class="subtitle">管理您的主观宏观预期，作为指数预测的分析前提</p>
    </div>

    <div class="content-layout" v-loading="loading">
      <div class="sidebar">
        <div class="sidebar-header">
          <el-input v-model="searchKeyword" placeholder="搜索预期..." clearable size="small" />
          <el-button type="primary" size="small" @click="createNew" style="margin-top: 8px; width: 100%">
            + 新建预期
          </el-button>
        </div>
        <div class="expectation-list">
          <div
            v-for="item in filteredList"
            :key="item._id"
            class="list-item"
            :class="{ active: selected?._id === item._id }"
            @click="selectItem(item)"
          >
            <div class="item-title">
              {{ item.title }}
              <el-tag v-if="item.is_active" type="success" size="small">激活</el-tag>
            </div>
            <div class="item-date">{{ formatDate(item.updated_at) }}</div>
          </div>
          <el-empty v-if="!filteredList.length" description="暂无预期" />
        </div>
      </div>

      <div class="editor" v-if="selected">
        <div class="editor-toolbar">
          <el-button type="primary" @click="saveExpectation">保存</el-button>
          <el-button @click="copyCurrent">复制</el-button>
          <el-button v-if="!selected.is_active" type="success" @click="activateCurrent">设为激活</el-button>
          <el-popconfirm title="确定删除此预期?" @confirm="deleteCurrent">
            <template #reference>
              <el-button type="danger" text>删除</el-button>
            </template>
          </el-popconfirm>
        </div>

        <el-form :model="form" label-width="130px" label-position="top">
          <el-form-item label="预期标题">
            <el-input v-model="form.title" placeholder="例如：2026年5月宏观预期" />
          </el-form-item>

          <el-divider content-position="left">政策预期</el-divider>
          <el-form-item label="长期政策方向">
            <el-input v-model="form.content.policy_long_term" type="textarea" :rows="2"
              placeholder="例如：十四五→十五五过渡期，国内统一大市场建设..." />
          </el-form-item>
          <el-form-item label="中期宏观政策（最近半年）">
            <el-input v-model="form.content.policy_medium_term" type="textarea" :rows="2"
              placeholder="最近半年最重要的宏观政策..." />
          </el-form-item>
          <el-form-item label="短期政策/事件（最近一月）">
            <el-input v-model="form.content.policy_short_term" type="textarea" :rows="2"
              placeholder="最近一月最重要的政策和事件..." />
          </el-form-item>
          <el-form-item label="流动性判断">
            <el-input v-model="form.content.liquidity_assessment" type="textarea" :rows="2"
              placeholder="MLF续作规模、降准预期..." />
          </el-form-item>

          <el-divider content-position="left">经济与市场判断</el-divider>
          <el-row :gutter="16">
            <el-col :span="8">
              <el-form-item label="经济周期定位">
                <el-select v-model="form.content.economic_phase" placeholder="选择周期阶段" clearable>
                  <el-option label="复苏早期" value="复苏早期" />
                  <el-option label="繁荣期" value="繁荣期" />
                  <el-option label="衰退期" value="衰退期" />
                  <el-option label="混沌期" value="混沌期" />
                  <el-option label="滞胀" value="滞胀" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="市场大势判断">
                <el-select v-model="form.content.market_trend" placeholder="选择市场趋势" clearable>
                  <el-option label="牛市" value="牛市" />
                  <el-option label="熊市" value="熊市" />
                  <el-option label="震荡市" value="震荡市" />
                  <el-option label="结构性行情" value="结构性行情" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item label="周期详细描述">
            <el-input v-model="form.content.cycle_detail" type="textarea" :rows="2" />
          </el-form-item>
          <el-form-item label="市场阶段描述">
            <el-input v-model="form.content.market_phase_detail" type="textarea" :rows="2" />
          </el-form-item>

          <el-divider content-position="left">板块观点</el-divider>
          <el-table :data="form.content.sector_views" border size="small">
            <el-table-column label="板块名称" min-width="140">
              <template #default="{ row, $index }">
                <el-input v-model="row.sector_name" placeholder="如: 新能源" size="small" />
              </template>
            </el-table-column>
            <el-table-column label="观点描述" min-width="260">
              <template #default="{ row }">
                <el-input v-model="row.thesis" placeholder="如: 超跌后具备反弹潜力" size="small" />
              </template>
            </el-table-column>
            <el-table-column label="信心度" width="100">
              <template #default="{ row }">
                <el-select v-model="row.confidence" size="small">
                  <el-option label="高" value="高" />
                  <el-option label="中" value="中" />
                  <el-option label="低" value="低" />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column label="时间维度" width="110">
              <template #default="{ row }">
                <el-select v-model="row.time_horizon" size="small">
                  <el-option label="短期" value="短期" />
                  <el-option label="中期" value="中期" />
                  <el-option label="长期" value="长期" />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="60">
              <template #default="{ $index }">
                <el-button type="danger" text size="small" @click="form.content.sector_views.splice($index, 1)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-button size="small" @click="addSectorView" style="margin-top: 8px">+ 添加板块观点</el-button>

          <el-divider content-position="left">自定义补充</el-divider>
          <div v-for="(section, idx) in form.content.custom_sections" :key="idx" class="custom-section-card">
            <el-input v-model="section.title" placeholder="章节标题" size="small" style="margin-bottom: 4px" />
            <el-input v-model="section.content" type="textarea" :rows="2" placeholder="章节内容" size="small" />
            <el-button type="danger" text size="small" @click="form.content.custom_sections.splice(idx, 1)">删除</el-button>
          </div>
          <el-button size="small" @click="form.content.custom_sections.push({ title: '', content: '' })">
            + 添加自定义章节
          </el-button>
        </el-form>
      </div>

      <el-empty v-else description="请选择或新建一个预期" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getExpectations, getExpectationById, createExpectation, updateExpectation,
  deleteExpectation, activateExpectation, copyExpectation
} from '@/api/expectations'
import type { Expectation, ExpectationContent } from '@/types/expectation'

const loading = ref(false)
const searchKeyword = ref('')
const expectations = ref<Expectation[]>([])
const selected = ref<Expectation | null>(null)
const form = ref<Expectation & { content: ExpectationContent }>({
  _id: '', id: '', user_id: '', title: '', is_active: false,
  created_at: '', updated_at: '',
  content: {
    policy_long_term: '', policy_medium_term: '', policy_short_term: '',
    liquidity_assessment: '', economic_phase: '', cycle_detail: '',
    market_trend: '', market_phase_detail: '',
    sector_views: [], custom_sections: []
  }
})

const filteredList = computed(() =>
  expectations.value.filter(e =>
    e.title.toLowerCase().includes(searchKeyword.value.toLowerCase())
  )
)

function formatDate(d: string) {
  return d ? new Date(d).toLocaleDateString('zh-CN') : ''
}

function createNew() {
  form.value = {
    _id: '', id: '', user_id: '', title: '新建预期', is_active: false,
    created_at: '', updated_at: '',
    content: {
      policy_long_term: '', policy_medium_term: '', policy_short_term: '',
      liquidity_assessment: '', economic_phase: '', cycle_detail: '',
      market_trend: '', market_phase_detail: '',
      sector_views: [], custom_sections: []
    }
  }
  selected.value = form.value as any
}

function addSectorView() {
  form.value.content.sector_views.push({
    sector_name: '', thesis: '', confidence: '中', time_horizon: '短期'
  })
}

async function loadList() {
  loading.value = true
  try {
    const data = await getExpectations()
    expectations.value = Array.isArray(data) ? data : ((data as any)?.data || [])
  } catch (e: any) {
    ElMessage.error('加载预期列表失败')
  } finally {
    loading.value = false
  }
}

async function selectItem(item: Expectation) {
  try {
    const data = await getExpectationById(item._id)
    selected.value = data as any
    form.value = JSON.parse(JSON.stringify(data))
  } catch (e) {
    ElMessage.error('加载预期详情失败')
  }
}

async function saveExpectation() {
  try {
    if (form.value._id) {
      await updateExpectation(form.value._id, { title: form.value.title, content: form.value.content })
      ElMessage.success('预期已更新')
    } else {
      const data = await createExpectation({ title: form.value.title, content: form.value.content })
      form.value._id = (data as any)?._id || (data as any)?.id || ''
      ElMessage.success('预期已创建')
    }
    await loadList()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  }
}

async function deleteCurrent() {
  if (!selected.value) return
  try {
    await deleteExpectation(selected.value._id)
    ElMessage.success('预期已删除')
    selected.value = null
    await loadList()
  } catch (e: any) {
    ElMessage.error('删除失败')
  }
}

async function activateCurrent() {
  if (!selected.value) return
  try {
    await activateExpectation(selected.value._id)
    ElMessage.success('已设为激活预期')
    await loadList()
  } catch (e: any) {
    ElMessage.error('激活失败')
  }
}

async function copyCurrent() {
  if (!selected.value) return
  try {
    await copyExpectation(selected.value._id)
    ElMessage.success('已复制')
    await loadList()
  } catch (e: any) {
    ElMessage.error('复制失败')
  }
}

onMounted(() => { loadList() })
</script>

<style scoped lang="scss">
.expectations-page {
  padding: 20px;
  height: calc(100vh - 60px);
  display: flex;
  flex-direction: column;
}
.page-header {
  margin-bottom: 16px;
  h2 { margin: 0 0 4px; font-size: 20px; }
  .subtitle { color: #909399; font-size: 13px; margin: 0; }
}
.content-layout {
  display: flex;
  flex: 1;
  gap: 16px;
  overflow: hidden;
}
.sidebar {
  width: 260px;
  flex-shrink: 0;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.sidebar-header { padding: 12px; border-bottom: 1px solid #ebeef5; }
.expectation-list { flex: 1; overflow-y: auto; padding: 8px; }
.list-item {
  padding: 10px;
  border-radius: 6px;
  cursor: pointer;
  margin-bottom: 4px;
  &:hover { background: #f5f7fa; }
  &.active { background: #ecf5ff; border: 1px solid #b3d8ff; }
  .item-title { display: flex; align-items: center; gap: 6px; font-size: 14px; margin-bottom: 2px; }
  .item-date { font-size: 12px; color: #909399; }
}
.editor {
  flex: 1;
  overflow-y: auto;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 20px;
}
.editor-toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #ebeef5;
}
.custom-section-card {
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 10px;
  margin-bottom: 8px;
}
</style>
