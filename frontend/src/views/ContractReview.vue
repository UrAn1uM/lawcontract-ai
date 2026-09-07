<template>
  <div class="page">
    <el-row :gutter="20">
      <!-- 左：合同列表 + 上传 -->
      <el-col :span="8">
        <el-card class="card-box">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span>我的合同</span>
              <el-upload :show-file-list="false" :http-request="doUpload" accept=".docx,.pdf,.txt">
                <el-button type="primary" size="small" :loading="uploading">上传合同</el-button>
              </el-upload>
            </div>
          </template>
          <el-table :data="contracts" size="small" highlight-current-row @current-change="selectContract">
            <el-table-column prop="title" label="标题" show-overflow-tooltip />
            <el-table-column prop="contract_type" label="类型" width="90" />
            <el-table-column label="操作" width="160">
              <template #default="{ row }">
                <el-button size="small" type="primary" :loading="reviewingId === row.id" @click.stop="doReview(row)">风险审查</el-button>
                <el-button size="small" type="warning" :loading="reviewingId === row.id" @click.stop="doCompliance(row)">合规检查</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!contracts.length" description="暂无合同，点击右上角上传" :image-size="60" />
        </el-card>
      </el-col>

      <!-- 右：审查报告 -->
      <el-col :span="16">
        <el-card class="card-box">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span>审查报告</span>
              <el-tag v-if="report" :type="riskTagType(report.overall_risk)" size="large">
                整体风险：{{ report.overall_risk }}
              </el-tag>
            </div>
          </template>

          <el-empty v-if="!report" description="选择合同并点击「风险审查」或「合规检查」" />

          <template v-else>
            <p style="color: #606266">{{ report.summary }}</p>
            <el-table :data="report.items" size="small" border>
              <el-table-column prop="clause_no" label="条款" width="80" />
              <el-table-column label="等级" width="70">
                <template #default="{ row }">
                  <el-tag :type="riskTagType(row.risk_level)" size="small">{{ row.risk_level }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="title" label="风险点" width="180" show-overflow-tooltip />
              <el-table-column prop="description" label="问题描述" show-overflow-tooltip />
              <el-table-column prop="suggestion" label="修改建议" show-overflow-tooltip />
              <el-table-column prop="legal_basis" label="依据" width="160" show-overflow-tooltip />
              <el-table-column type="expand">
                <template #default="{ row }">
                  <div style="padding: 10px">
                    <p><b>问题描述：</b>{{ row.description }}</p>
                    <p><b>修改建议：</b>{{ row.suggestion }}</p>
                    <p><b>法律依据：</b>{{ row.legal_basis }}</p>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </template>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchContracts, uploadContract, reviewContract, complianceCheck } from '../api'

const contracts = ref([])
const report = ref(null)
const uploading = ref(false)
const reviewingId = ref(null)

onMounted(loadContracts)

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

async function doReview(row) {
  reviewingId.value = row.id
  report.value = null
  try {
    report.value = await reviewContract(row.id, 'risk')
    ElMessage.success('风险审查完成')
  } finally {
    reviewingId.value = null
  }
}

async function doCompliance(row) {
  reviewingId.value = row.id
  report.value = null
  try {
    report.value = await complianceCheck(row.id)
    ElMessage.success('合规检查完成')
  } finally {
    reviewingId.value = null
  }
}

function riskTagType(level) {
  return { 高: 'danger', 中: 'warning', 低: 'info', 无风险: 'success' }[level] || 'info'
}
</script>
