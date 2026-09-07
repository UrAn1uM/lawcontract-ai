<template>
  <div class="page">
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card class="card-box">
          <template #header><span>版本 A（我方 / 旧版）</span></template>
          <el-input v-model="textA" type="textarea" :rows="18" placeholder="粘贴第一份合同全文…" />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="card-box">
          <template #header><span>版本 B（对方 / 新版）</span></template>
          <el-input v-model="textB" type="textarea" :rows="18" placeholder="粘贴第二份合同全文…" />
        </el-card>
      </el-col>
    </el-row>

    <div style="text-align: center; margin: 16px 0">
      <el-button type="primary" :loading="comparing" :disabled="!textA || !textB" @click="doCompare">
        开始比对
      </el-button>
    </div>

    <el-card v-if="result" class="card-box">
      <template #header>
        <div style="display: flex; gap: 10px">
          <el-tag v-for="(count, type) in result.summary" :key="type" :type="tagType(type)">
            {{ type }}：{{ count }}
          </el-tag>
        </div>
      </template>
      <el-table :data="result.diffs" size="small" border>
        <el-table-column label="差异类型" width="90">
          <template #default="{ row }">
            <el-tag :type="tagType(row.type)" size="small">{{ row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="版本 A 条款" min-width="240">
          <template #default="{ row }">
            <b v-if="row.a_no">{{ row.a_no }}</b>
            <div style="color: #606266; white-space: pre-wrap">{{ row.a_content }}</div>
          </template>
        </el-table-column>
        <el-table-column label="版本 B 条款" min-width="240">
          <template #default="{ row }">
            <b v-if="row.b_no">{{ row.b_no }}</b>
            <div style="color: #606266; white-space: pre-wrap">{{ row.b_content }}</div>
          </template>
        </el-table-column>
        <el-table-column label="字面相似度" width="100">
          <template #default="{ row }">{{ (row.text_similarity * 100).toFixed(0) }}%</template>
        </el-table-column>
        <el-table-column label="语义变化" width="90">
          <template #default="{ row }">{{ (row.semantic_change * 100).toFixed(0) }}%</template>
        </el-table-column>
      </el-table>
      <p style="color: #909399; font-size: 12px">
        说明：措辞修改 = 字面变化但语义基本不变；语义修改 = 权利义务发生实质变化，建议重点关注。
      </p>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { compareTexts } from '../api'

const textA = ref('')
const textB = ref('')
const result = ref(null)
const comparing = ref(false)

async function doCompare() {
  comparing.value = true
  try {
    result.value = await compareTexts(textA.value, textB.value)
    ElMessage.success('比对完成')
  } finally {
    comparing.value = false
  }
}

function tagType(type) {
  return { 新增: 'success', 删除: 'danger', 语义修改: 'warning', 措辞修改: 'info', 未变: 'info' }[type] || 'info'
}
</script>
