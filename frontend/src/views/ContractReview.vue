<template>
  <div class="page">
    <el-row :gutter="24">
      <!-- 左：合同列表 -->
      <el-col :span="8">
        <div class="panel">
          <div class="section-bar">我的合同</div>
          <div class="panel-body">
            <el-upload :show-file-list="false" :http-request="doUpload" accept=".docx,.pdf,.txt">
              <el-button type="primary" :loading="uploading" class="full-btn">上传合同</el-button>
            </el-upload>
            <el-table :data="contracts" highlight-current-row @current-change="selectContract" class="table">
              <el-table-column prop="title" label="标题" show-overflow-tooltip />
              <el-table-column label="操作" width="170" align="center">
                <template #default="{ row }">
                  <el-button size="small" link type="primary" :loading="reviewingId === row.id" @click.stop="startReview(row, 'risk')">风险审查</el-button>
                  <el-button size="small" link :loading="reviewingId === row.id" @click.stop="startReview(row, 'compliance')">合规检查</el-button>
                </template>
              </el-table-column>
            </el-table>
            <p v-if="!contracts.length" class="empty">暂无合同，点击上方按钮上传</p>
            <p class="tip">支持 docx / pdf / txt，扫描件 PDF 暂不支持</p>
          </div>
        </div>
      </el-col>

      <!-- 右：审查报告 -->
      <el-col :span="16">
        <div class="panel">
          <div class="section-bar accent">
            审查报告
            <span v-if="report" class="risk-pill">{{ report.overall_risk }}</span>
          </div>
          <div class="panel-body">
            <p v-if="!progress && !report" class="empty">选择左侧合同，点击「风险审查」或「合规检查」</p>

            <!-- 进行中 -->
            <div v-else-if="progress && progress.status === 'running'" class="progress-box">
              <div class="progress-track">
                <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
              </div>
              <p class="progress-text">正在审查第 {{ progress.done }}/{{ progress.total }} 条 · 当前：{{ progress.current || '准备中' }}</p>
              <p class="progress-sub">合同条款较多，预计 1～3 分钟</p>
            </div>

            <!-- 报告 -->
            <template v-else-if="report">
              <p class="summary">{{ report.summary }}</p>
              <el-table :data="report.items" border stripe class="table">
                <el-table-column prop="clause_no" label="条款" width="80" align="center" />
                <el-table-column label="等级" width="70" align="center">
                  <template #default="{ row }">
                    <span class="risk-dot" :class="'lv-' + riskKey(row.risk_level)"></span>{{ row.risk_level }}
                  </template>
                </el-table-column>
                <el-table-column prop="title" label="风险点" width="160" show-overflow-tooltip />
                <el-table-column prop="description" label="问题描述" show-overflow-tooltip />
                <el-table-column prop="suggestion" label="修改建议" show-overflow-tooltip />
                <el-table-column prop="legal_basis" label="依据" width="150" show-overflow-tooltip />
              </el-table>
            </template>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onMounted, ref, computed, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchContracts, uploadContract, reviewContract, fetchReviewProgress } from '../api'

const contracts = ref([])
const report = ref(null)
const progress = ref(null)
const uploading = ref(false)
const reviewingId = ref(null)
let pollTimer = null

const progressPercent = computed(() => {
  if (!progress.value || !progress.value.total) return 0
  return Math.round((progress.value.done / progress.value.total) * 100)
})

onMounted(loadContracts)
onUnmounted(() => { if (pollTimer) clearInterval(pollTimer) })

async function loadContracts() {
  contracts.value = await fetchContracts()
}

function selectContract(row) {
  if (row) report.value = null
}

async function doUpload(option) {
  uploading.value = true
  try {
    const fd = new FormData()
    fd.append('file', option.file)
    await uploadContract(fd)
    ElMessage.success('上传并解析成功')
    loadContracts()
  } finally {
    uploading.value = false
  }
}

async function startReview(row, type) {
  reviewingId.value = row.id
  report.value = null
  progress.value = null
  try {
    const { task_id } = await reviewContract(row.id, type)
    progress.value = { total: 0, done: 0, current: '', status: 'running' }
    pollProgress(task_id)
  } catch (e) {
    reviewingId.value = null
  }
}

function pollProgress(taskId) {
  if (pollTimer) clearInterval(pollTimer)
  pollTimer = setInterval(async () => {
    try {
      const p = await fetchReviewProgress(taskId)
      progress.value = p
      if (p.status === 'done') {
        clearInterval(pollTimer)
        pollTimer = null
        report.value = p.result
        progress.value = null
        reviewingId.value = null
        ElMessage.success('审查完成')
      } else if (p.status === 'error') {
        clearInterval(pollTimer)
        pollTimer = null
        reviewingId.value = null
        progress.value = null
        ElMessage.error(p.error || '审查失败')
      }
    } catch (e) {
      clearInterval(pollTimer)
      pollTimer = null
      reviewingId.value = null
      progress.value = null
    }
  }, 1500)
}

function riskKey(level) {
  return { 高: 'high', 中: 'mid', 低: 'low', 无风险: 'none' }[level] || 'low'
}
</script>

<style scoped>
.page { padding: 0; }
.panel { background: #ffffff; border: 1px solid #d9d9d9; }
.section-bar {
  background: #1a1a1a;
  color: #ffffff;
  padding: 10px 24px;
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 1px;
  display: flex;
  align-items: center;
  gap: 12px;
}
.section-bar.accent { background: #E2231A; }
.risk-pill {
  margin-left: auto;
  background: #ffffff;
  color: #000000;
  font-size: 12px;
  padding: 2px 8px;
  font-weight: 500;
}
.panel-body { padding: 24px; }
.full-btn { width: 100%; margin-bottom: 16px; }
.table { width: 100%; }
.empty { color: #8A8A8A; font-size: 13px; text-align: center; padding: 40px 0; }
.tip { color: #8A8A8A; font-size: 12px; text-align: center; margin: 12px 0 0; }

.progress-box { padding: 40px 24px; }
.progress-track { height: 16px; background: #f0f0f0; position: relative; }
.progress-fill { height: 100%; background: #E2231A; transition: width 0.3s ease; }
.progress-text { margin: 18px 0 4px; font-size: 14px; color: #000000; }
.progress-sub { margin: 0; font-size: 12px; color: #8A8A8A; }

.summary { margin: 0 0 16px; font-size: 14px; color: #4a4a4a; line-height: 1.7; }

/* 风险等级：灰度 + 朱红（Swiss，不用多彩） */
.risk-dot { display: inline-block; width: 8px; height: 8px; margin-right: 6px; }
.risk-dot.lv-high { background: #E2231A; }
.risk-dot.lv-mid { background: #1a1a1a; }
.risk-dot.lv-low { background: #8A8A8A; }
.risk-dot.lv-none { background: #d9d9d9; }
</style>
