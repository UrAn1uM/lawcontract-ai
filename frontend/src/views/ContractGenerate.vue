<template>
  <div class="page">
    <el-row :gutter="20">
      <el-col :span="9">
        <el-card class="card-box">
          <template #header><span>合同要素（问答式引导）</span></template>
          <el-form :model="form" label-width="90px">
            <el-form-item label="合同类型">
              <el-select v-model="form.contract_type">
                <el-option v-for="t in types" :key="t" :label="t" :value="t" />
              </el-select>
            </el-form-item>
            <el-form-item label="甲方"><el-input v-model="form.party_a" placeholder="如：XX 科技有限公司" /></el-form-item>
            <el-form-item label="乙方"><el-input v-model="form.party_b" placeholder="如：XX 信息服务有限公司" /></el-form-item>
            <el-form-item label="标的/内容"><el-input v-model="form.subject" type="textarea" :rows="2" placeholder="合同标的或服务内容" /></el-form-item>
            <el-form-item label="价款"><el-input v-model="form.amount" placeholder="如：人民币 10 万元" /></el-form-item>
            <el-form-item label="期限"><el-input v-model="form.duration" placeholder="如：2026年1月1日至2026年12月31日" /></el-form-item>
            <el-form-item label="付款方式"><el-input v-model="form.payment_terms" type="textarea" :rows="2" placeholder="如：签订后付 30%，验收后付 70%" /></el-form-item>
            <el-form-item label="特殊约定"><el-input v-model="form.special" type="textarea" :rows="2" placeholder="保密、竞业、知识产权等特殊约定" /></el-form-item>
            <el-button type="primary" :loading="generating" style="width: 100%" @click="doGenerate">生成标准合同</el-button>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="15">
        <el-card class="card-box">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span>生成结果</span>
              <el-button v-if="result" size="small" @click="copyText">复制全文</el-button>
            </div>
          </template>
          <el-empty v-if="!result" description="填写左侧要素后点击生成" />
          <template v-else>
            <el-alert
              :title="result.self_check.message"
              :type="result.self_check.passed ? 'success' : 'warning'"
              show-icon
              :closable="false"
              style="margin-bottom: 12px"
            />
            <div class="contract-text card-box" style="border: 1px solid #d9d9d9">{{ result.contract_text }}</div>
          </template>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { generateContract } from '../api'

const types = ['服务合同', '采购合同', '软件开发合同', '数据处理协议', '保密协议', '租赁合同', '其他']

const form = reactive({
  contract_type: '服务合同',
  party_a: '',
  party_b: '',
  subject: '',
  amount: '',
  duration: '',
  payment_terms: '',
  special: ''
})

const result = ref(null)
const generating = ref(false)

async function doGenerate() {
  generating.value = true
  try {
    result.value = await generateContract(form)
    ElMessage.success('合同生成完成，已自动保存到"我的合同"')
  } finally {
    generating.value = false
  }
}

async function copyText() {
  await navigator.clipboard.writeText(result.value.contract_text)
  ElMessage.success('已复制到剪贴板')
}
</script>
