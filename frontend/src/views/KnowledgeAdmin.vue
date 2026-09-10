<template>
  <div class="page">
    <section class="block">
      <div class="block-bar">
        知识库管理 · 仅管理员可修改
        <el-button type="warning" :loading="rebuilding" class="rebuild-btn" @click="doRebuild">重建向量索引</el-button>
      </div>

      <div class="tabs">
        <button class="tab" :class="{ on: tab === 'clauses' }" @click="tab = 'clauses'">标准条款库</button>
        <button class="tab" :class="{ on: tab === 'regulations' }" @click="tab = 'regulations'">法规库</button>
      </div>

      <div class="block-body">
        <!-- 标准条款库 -->
        <template v-if="tab === 'clauses'">
          <div class="tool-row">
            <el-button size="small" type="primary" @click="openClause()">新增条款</el-button>
            <span class="tool-count">共 {{ clauses.length }} 条</span>
          </div>
          <el-table :data="clauses" size="small" border class="table">
            <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
            <el-table-column prop="category" label="分类" width="110" />
            <el-table-column label="风险等级" width="110" align="center">
              <template #default="{ row }">
                <span class="risk-tag" :class="riskClass(row.risk_level)">{{ row.risk_level }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="content" label="内容" show-overflow-tooltip />
            <el-table-column label="操作" width="140" align="center">
              <template #default="{ row }">
                <el-button size="small" @click="openClause(row)">编辑</el-button>
                <el-button size="small" type="danger" @click="removeClause(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </template>

        <!-- 法规库 -->
        <template v-else>
          <div class="tool-row">
            <el-button size="small" type="primary" @click="openReg()">新增法规</el-button>
            <span class="tool-count">共 {{ regulations.length }} 条</span>
          </div>
          <el-table :data="regulations" size="small" border class="table">
            <el-table-column prop="name" label="法规" width="160" />
            <el-table-column prop="article_no" label="条文" width="100" />
            <el-table-column prop="jurisdiction" label="辖区" width="90" />
            <el-table-column prop="content" label="内容" show-overflow-tooltip />
            <el-table-column label="操作" width="140" align="center">
              <template #default="{ row }">
                <el-button size="small" @click="openReg(row)">编辑</el-button>
                <el-button size="small" type="danger" @click="removeReg(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </template>
      </div>
    </section>

    <!-- 条款编辑弹窗 -->
    <el-dialog v-model="clauseDialog" :title="clauseForm.id ? '编辑条款' : '新增条款'" width="640px">
      <el-form :model="clauseForm" label-width="80px">
        <el-form-item label="标题"><el-input v-model="clauseForm.title" /></el-form-item>
        <el-form-item label="分类">
          <el-select v-model="clauseForm.category">
            <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="风险等级">
          <el-radio-group v-model="clauseForm.risk_level">
            <el-radio value="高">高</el-radio>
            <el-radio value="中">中</el-radio>
            <el-radio value="低">低</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="内容"><el-input v-model="clauseForm.content" type="textarea" :rows="6" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="clauseDialog = false">取消</el-button>
        <el-button type="primary" @click="saveClause">保存</el-button>
      </template>
    </el-dialog>

    <!-- 法规编辑弹窗 -->
    <el-dialog v-model="regDialog" :title="regForm.id ? '编辑法规' : '新增法规'" width="640px">
      <el-form :model="regForm" label-width="90px">
        <el-form-item label="法规名称"><el-input v-model="regForm.name" placeholder="如：个人信息保护法 / GDPR" /></el-form-item>
        <el-form-item label="条文号"><el-input v-model="regForm.article_no" placeholder="如：第十三条" /></el-form-item>
        <el-form-item label="辖区">
          <el-select v-model="regForm.jurisdiction">
            <el-option label="中国" value="中国" />
            <el-option label="欧盟" value="欧盟" />
          </el-select>
        </el-form-item>
        <el-form-item label="施行日期"><el-input v-model="regForm.effective_date" placeholder="如：2021-11-01" /></el-form-item>
        <el-form-item label="条文内容"><el-input v-model="regForm.content" type="textarea" :rows="6" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="regDialog = false">取消</el-button>
        <el-button type="primary" @click="saveReg">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../api/request'
import { fetchClauses, fetchRegulations, rebuildIndex } from '../api'

const tab = ref('clauses')
const clauses = ref([])
const regulations = ref([])
const rebuilding = ref(false)
const categories = ['违约责任', '付款', '保密', '知识产权', '验收', '争议解决', '不可抗力', '数据合规', '通知送达', '解除终止', '通用']

const clauseDialog = ref(false)
const clauseForm = reactive({ id: null, title: '', category: '通用', risk_level: '中', content: '' })

const regDialog = ref(false)
const regForm = reactive({ id: null, name: '', article_no: '', jurisdiction: '中国', content: '', effective_date: '' })

onMounted(load)

async function load() {
  clauses.value = await fetchClauses()
  regulations.value = await fetchRegulations()
}

function riskClass(level) {
  return { 高: 'is-high', 中: 'is-mid', 低: 'is-low' }[level] || 'is-low'
}

function openClause(row) {
  Object.assign(clauseForm, row || { id: null, title: '', category: '通用', risk_level: '中', content: '' })
  clauseDialog.value = true
}

async function saveClause() {
  const { id, ...data } = clauseForm
  if (id) await request.put(`/knowledge/clauses/${id}`, data)
  else await request.post('/knowledge/clauses', data)
  ElMessage.success('已保存，变更需重建索引后生效')
  clauseDialog.value = false
  load()
}

async function removeClause(row) {
  await ElMessageBox.confirm(`确定删除条款「${row.title}」？`, '提示', { type: 'warning' })
  await request.delete(`/knowledge/clauses/${row.id}`)
  ElMessage.success('已删除')
  load()
}

function openReg(row) {
  Object.assign(regForm, row || { id: null, name: '', article_no: '', jurisdiction: '中国', content: '', effective_date: '' })
  regDialog.value = true
}

async function saveReg() {
  const { id, ...data } = regForm
  if (id) await request.put(`/knowledge/regulations/${id}`, data)
  else await request.post('/knowledge/regulations', data)
  ElMessage.success('已保存，变更需重建索引后生效')
  regDialog.value = false
  load()
}

async function removeReg(row) {
  await ElMessageBox.confirm(`确定删除「${row.name}${row.article_no}」？`, '提示', { type: 'warning' })
  await request.delete(`/knowledge/regulations/${row.id}`)
  ElMessage.success('已删除')
  load()
}

async function doRebuild() {
  rebuilding.value = true
  try {
    const r = await rebuildIndex()
    ElMessage.success(`索引重建完成，共 ${r.indexed} 条（条款 ${r.clauses} + 法规 ${r.regulations}）`)
  } finally {
    rebuilding.value = false
  }
}
</script>

<style scoped>
.page { padding: 0; }
.rebuild-btn { margin-left: auto; }

/* 页签做成色块，紧贴无间距 */
.tabs { display: flex; border-bottom: var(--sp-line); }
.tab {
  border: none;
  border-right: var(--sp-line);
  background: var(--sp-white);
  color: var(--sp-black);
  font-family: inherit;
  font-size: 13px;
  font-weight: 900;
  letter-spacing: 0.12em;
  padding: 13px 28px;
  cursor: pointer;
}
.tab:hover { background: var(--sp-black); color: var(--sp-white); }
.tab.on { background: var(--sp-red); color: var(--sp-black); }

.block-body { padding: 20px; }
.tool-row { display: flex; align-items: center; margin-bottom: 16px; }
.tool-count {
  margin-left: auto;
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 0.18em;
  color: var(--sp-ink-30);
}
.table { width: 100%; }

/* 风险等级：纯色块表示 */
.risk-tag {
  display: inline-block;
  border: var(--sp-hair);
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 0.1em;
  padding: 2px 10px;
}
.risk-tag.is-high { background: var(--sp-red); color: var(--sp-black); }
.risk-tag.is-mid { background: var(--sp-black); color: var(--sp-white); }
.risk-tag.is-low { background: var(--sp-white); color: var(--sp-ink-30); }
</style>
