<template>
  <div class="review">
    <div class="stage">
      <!-- 页头：左对齐 + 一条细红规则 -->
      <header class="head">
        <span class="head-rule"></span>
        <h1 class="head-title">合同智能审查</h1>
        <p class="head-sub">
          上传合同后逐条识别风险并给出法律依据。工作区只保留本次会话的合同，
          审查报告与生成的合同都保存在「个人中心」。
        </p>
      </header>

      <div class="split">
        <!-- ==================== 左：工作区 ==================== -->
        <section class="pane">
          <div class="pane-bar">
            <span>工作区</span>
            <span class="pane-num">{{ contracts.length }}</span>
          </div>

          <div class="pane-body">
            <el-upload
              :show-file-list="false"
              :http-request="doUpload"
              accept=".docx,.pdf,.txt"
            >
              <button class="upload" :disabled="uploading">
                {{ uploading ? '解析中…' : '上传合同' }}
              </button>
            </el-upload>
            <p class="hint">支持 docx / pdf / txt · 扫描件 PDF 暂不支持</p>

            <div v-if="contracts.length" class="rows">
              <div
                v-for="c in contracts"
                :key="c.id"
                class="row"
                :class="{ on: current && current.id === c.id }"
                @click="select(c)"
              >
                <div class="row-top">
                  <span class="row-title">{{ c.title }}</span>
                  <span class="row-tag" :class="{ done: c.report_count > 0 }">
                    {{ c.report_count > 0 ? '已审查' : '待审查' }}
                  </span>
                </div>
                <div class="row-meta">{{ c.contract_type }} · {{ c.created_at }}</div>
                <div class="row-acts">
                  <button class="mini" :disabled="!!reviewingId" @click.stop="startReview(c, 'risk')">
                    风险审查
                  </button>
                  <button class="mini" :disabled="!!reviewingId" @click.stop="startReview(c, 'compliance')">
                    合规检查
                  </button>
                  <button class="mini ghost" @click.stop="drop(c)">移出</button>
                </div>
              </div>
            </div>

            <p v-else class="empty">
              本次会话暂无合同<br />
              上传后即可开始审查，历史报告在「个人中心」
            </p>
          </div>
        </section>

        <!-- ==================== 右：审查报告 ==================== -->
        <section class="pane">
          <div class="pane-bar">
            <span>审查报告</span>
            <span v-if="displayReport" class="pane-num red">{{ displayReport.overall_risk }}</span>
          </div>

          <div class="pane-body">
            <!-- 审查中：进度 -->
            <div v-if="progress" class="prog">
              <div class="prog-top">
                <span class="sp-label">审查进度</span>
                <span class="prog-pct">{{ progressPercent }}%</span>
              </div>
              <div class="prog-track">
                <div class="prog-fill" :style="{ width: progressPercent + '%' }"></div>
              </div>
              <p class="prog-main">
                正在审查第 {{ progress.done }}/{{ progress.total }} 条
                <template v-if="progress.current">· 当前：{{ progress.current }}</template>
              </p>
              <p class="prog-sub">条款较多时约需 1～3 分钟，可以先去忙别的</p>
            </div>

            <!-- 有报告 -->
            <template v-else-if="displayReport">
              <div class="rep-meta">
                <span class="rep-type">{{ typeText(displayReport.review_type) }}</span>
                <span class="rep-time">{{ displayReport.created_at }}</span>
              </div>
              <p class="rep-sum">{{ displayReport.summary }}</p>

              <el-table :data="displayReport.items" border stripe class="table">
                <el-table-column prop="clause_no" label="条款" width="84" align="center" />
                <el-table-column label="等级" width="84" align="center">
                  <template #default="{ row }">
                    <span class="dot" :class="'lv-' + riskKey(row.risk_level)"></span>{{ row.risk_level }}
                  </template>
                </el-table-column>
                <el-table-column prop="title" label="风险点" min-width="126" show-overflow-tooltip />
                <el-table-column prop="description" label="问题描述" min-width="200" show-overflow-tooltip />
                <el-table-column prop="suggestion" label="修改建议" min-width="170" show-overflow-tooltip />
                <el-table-column prop="legal_basis" label="依据" width="112" show-overflow-tooltip />
              </el-table>

              <div class="rep-foot">
                <span class="rep-note">报告已存入个人中心</span>
                <button class="mini" @click="$router.push('/profile')">前往个人中心</button>
              </div>
            </template>

            <!-- 空态 -->
            <p v-else class="empty">
              选择左侧合同，点击「风险审查」或「合规检查」<br />
              审查完成后报告会实时显示在这里
            </p>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  fetchContracts,
  fetchReports,
  fetchReviewProgress,
  reviewContract,
  uploadContract
} from '../api'
import { useWorkspaceStore } from '../stores/workspace'

const route = useRoute()
const ws = useWorkspaceStore()

const contracts = ref([])
const current = ref(null) // 当前选中的合同
const reports = ref([]) // 当前合同的已存报告
const runningReport = ref(null) // 本次审查刚生成的报告（优先展示）
const progress = ref(null)
const uploading = ref(false)
const reviewingId = ref(null)
let pollTimer = null

const displayReport = computed(() => runningReport.value || reports.value[0] || null)

const progressPercent = computed(() => {
  if (!progress.value || !progress.value.total) return 0
  return Math.round((progress.value.done / progress.value.total) * 100)
})

onMounted(async () => {
  await loadContracts()
  // 从个人中心「去审查」跳过来：把该合同加入工作区并选中
  const qid = Number(route.query.contract)
  if (qid) {
    ws.add(qid)
    await loadContracts()
    const hit = contracts.value.find((c) => c.id === qid)
    if (hit) select(hit)
  }
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})

async function loadContracts() {
  const all = await fetchContracts()
  contracts.value = all.filter((c) => ws.ids.includes(c.id))
}

function select(row) {
  if (!row) return
  current.value = row
  runningReport.value = null
  progress.value = null
  loadReports(row.id)
}

async function loadReports(contractId) {
  try {
    reports.value = await fetchReports(contractId)
  } catch (e) {
    reports.value = []
  }
}

async function doUpload(option) {
  uploading.value = true
  try {
    const fd = new FormData()
    fd.append('file', option.file)
    const res = await uploadContract(fd)
    ws.add(res.id)
    await loadContracts()
    const hit = contracts.value.find((c) => c.id === res.id)
    ElMessage.success('上传并解析成功')
    if (hit) select(hit)
  } finally {
    uploading.value = false
  }
}

function drop(row) {
  ws.remove(row.id)
  if (current.value && current.value.id === row.id) {
    current.value = null
    reports.value = []
    runningReport.value = null
  }
  loadContracts()
}

async function startReview(row, type) {
  reviewingId.value = row.id
  current.value = row
  runningReport.value = null
  reports.value = []
  progress.value = { total: 0, done: 0, current: '', status: 'running' }
  try {
    const { task_id } = await reviewContract(row.id, type)
    pollProgress(task_id, row.id)
  } catch (e) {
    reviewingId.value = null
    progress.value = null
  }
}

function pollProgress(taskId, contractId) {
  if (pollTimer) clearInterval(pollTimer)
  pollTimer = setInterval(async () => {
    try {
      const p = await fetchReviewProgress(taskId)
      progress.value = p
      if (p.status === 'done') {
        stopPoll()
        runningReport.value = p.result
        progress.value = null
        ElMessage.success('审查完成，报告已保存')
        loadContracts()
        loadReports(contractId)
      } else if (p.status === 'error') {
        stopPoll()
        progress.value = null
        ElMessage.error(p.error || '审查失败')
      }
    } catch (e) {
      stopPoll()
      progress.value = null
    }
  }, 1500)
}

function stopPoll() {
  if (pollTimer) clearInterval(pollTimer)
  pollTimer = null
  reviewingId.value = null
}

function riskKey(level) {
  return { 高: 'high', 中: 'mid', 低: 'low', 无风险: 'none' }[level] || 'low'
}

function typeText(t) {
  return t === 'compliance' ? '合规检查' : '风险审查'
}
</script>

<style scoped>
/* 居中收进栅格，两侧留白 */
.review {
  display: flex;
  justify-content: center;
  padding: 44px 40px 60px;
  background: var(--sp-white);
}
.stage { width: 100%; max-width: 1240px; }

/* ---------- 页头 ---------- */
.head { margin-bottom: 30px; }
.head-rule {
  display: block;
  width: 40px;
  height: 3px;
  background: var(--sp-red);
  margin-bottom: 18px;
}
.head-title {
  margin: 0;
  font-size: clamp(24px, 2.6vw, 34px);
  font-weight: 900;
  line-height: 1.2;
  letter-spacing: -0.02em;
}
.head-sub {
  margin: 12px 0 0;
  max-width: 760px;
  font-size: 13.5px;
  line-height: 1.75;
  color: var(--sp-ink-70);
}

/* ---------- 左右分栏：紧贴，靠 2px 边框分隔 ---------- */
.split {
  display: grid;
  grid-template-columns: 4fr 8fr;
  gap: 0;
  border: var(--sp-line);
}
.pane { min-width: 0; background: var(--sp-white); }
.pane + .pane { border-left: var(--sp-line); }

.pane-bar {
  display: flex;
  align-items: center;
  background: var(--sp-black);
  color: var(--sp-white);
  border-bottom: var(--sp-line);
  padding: 10px 16px;
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0.2em;
}
.pane-bar.red { background: var(--sp-red); color: var(--sp-black); }
.pane-num {
  margin-left: 12px;
  border: 1px solid currentColor;
  padding: 1px 8px;
  font-size: 11px;
  letter-spacing: 0.1em;
}
/* 小色块：整块红，作为整页唯一的红色强调 */
.pane-num.red {
  background: var(--sp-red);
  border-color: var(--sp-red);
  color: var(--sp-black);
}
.pane-body { padding: 18px 16px 20px; }

/* 报告表格：压紧行高与内边距，把宽度让给正文列 */
.table :deep(.el-table__cell) { padding: 7px 6px !important; font-size: 12.5px; }
.table :deep(.el-table .cell) { padding: 0 4px; }

/* ---------- 上传 ---------- */
.upload {
  width: 100%;
  border: var(--sp-line);
  background: var(--sp-black);
  color: var(--sp-white);
  font-family: inherit;
  font-size: 13px;
  font-weight: 900;
  letter-spacing: 0.2em;
  padding: 12px 0;
  cursor: pointer;
}
.upload:hover:not(:disabled) { background: var(--sp-red); color: var(--sp-black); }
.upload:disabled { background: var(--sp-gray); border-color: var(--sp-ink-30); color: var(--sp-ink-30); cursor: not-allowed; }
.hint {
  margin: 10px 0 0;
  font-size: 11px;
  letter-spacing: 0.06em;
  color: var(--sp-ink-30);
  text-align: center;
}

/* ---------- 合同行 ---------- */
.rows { margin-top: 16px; border-top: var(--sp-hair); }
.row {
  border-bottom: var(--sp-hair);
  padding: 12px 10px;
  cursor: pointer;
}
.row:hover { background: var(--sp-gray); }
/* 色块入侵：选中整块反黑 */
.row.on { background: var(--sp-black); }
.row.on .row-title { color: var(--sp-white); }
.row.on .row-meta { color: rgba(255, 255, 255, 0.6); }
.row.on .row-tag { border-color: var(--sp-white); color: var(--sp-white); }
.row.on .row-tag.done { background: var(--sp-red); color: var(--sp-black); border-color: var(--sp-red); }
.row.on .mini { background: var(--sp-white); color: var(--sp-black); border-color: var(--sp-white); }
.row.on .mini:hover { background: var(--sp-red); border-color: var(--sp-red); }

.row-top { display: flex; align-items: center; justify-content: space-between; }
.row-title {
  font-size: 13.5px;
  font-weight: 900;
  letter-spacing: -0.01em;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-right: 10px;
}
.row-tag {
  flex: none;
  border: var(--sp-hair);
  font-size: 10px;
  font-weight: 900;
  letter-spacing: 0.1em;
  padding: 1px 7px;
  color: var(--sp-ink-30);
}
.row-tag.done { background: var(--sp-black); color: var(--sp-white); }
.row-meta {
  margin-top: 5px;
  font-size: 11px;
  letter-spacing: 0.04em;
  color: var(--sp-ink-30);
}
.row-acts { display: flex; margin-top: 10px; }
.mini {
  border: var(--sp-hair);
  border-right: none;
  background: var(--sp-white);
  color: var(--sp-black);
  font-family: inherit;
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 0.06em;
  padding: 4px 10px;
  cursor: pointer;
}
.mini:last-child { border-right: var(--sp-hair); }
.mini:hover:not(:disabled) { background: var(--sp-black); color: var(--sp-white); }
.mini.ghost { color: var(--sp-ink-30); }
.mini:disabled { color: var(--sp-ink-30); cursor: not-allowed; }

/* ---------- 空态 ---------- */
.empty {
  margin: 26px 0;
  text-align: center;
  font-size: 12.5px;
  line-height: 2;
  letter-spacing: 0.04em;
  color: var(--sp-ink-30);
}

/* ---------- 进度 ---------- */
.prog { padding: 18px 4px 10px; }
.prog-top { display: flex; align-items: baseline; justify-content: space-between; }
.prog-pct { font-size: 44px; font-weight: 900; line-height: 1; letter-spacing: -0.04em; }
.prog-track { height: 20px; border: var(--sp-line); margin-top: 12px; }
.prog-fill { height: 100%; background: var(--sp-red); }
.prog-main { margin: 16px 0 4px; font-size: 13px; font-weight: 900; }
.prog-sub { margin: 0; font-size: 12px; color: var(--sp-ink-30); }

/* ---------- 报告 ---------- */
.rep-meta { display: flex; align-items: center; margin-bottom: 12px; }
.rep-type {
  background: var(--sp-black);
  color: var(--sp-white);
  font-size: 10px;
  font-weight: 900;
  letter-spacing: 0.18em;
  padding: 3px 10px;
}
.rep-time { margin-left: 12px; font-size: 11px; letter-spacing: 0.08em; color: var(--sp-ink-30); }
.rep-sum { margin: 0 0 16px; font-size: 13px; line-height: 1.8; color: var(--sp-ink-70); }
.table { width: 100%; }

.dot { display: inline-block; width: 9px; height: 9px; margin-right: 7px; border: var(--sp-hair); }
.dot.lv-high { background: var(--sp-red); }
.dot.lv-mid { background: var(--sp-black); }
.dot.lv-low { background: var(--sp-ink-30); }
.dot.lv-none { background: var(--sp-white); }

.rep-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 16px;
  padding-top: 14px;
  border-top: var(--sp-hair);
}
.rep-note { font-size: 11px; letter-spacing: 0.08em; color: var(--sp-ink-30); }

@media (max-width: 1100px) {
  .review { padding: 32px 20px 48px; }
  .split { grid-template-columns: 1fr; }
  .pane + .pane { border-left: none; border-top: var(--sp-line); }
}
</style>
