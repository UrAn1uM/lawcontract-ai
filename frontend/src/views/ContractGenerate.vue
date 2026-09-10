<template>
  <div class="page">
    <div class="split">
      <!-- 左：要素表单 -->
      <section class="block">
        <div class="block-bar">合同要素 · 问答式引导</div>
        <div class="block-body">
          <el-form :model="form" label-position="top" class="form">
            <el-form-item label="合同类型">
              <el-select v-model="form.contract_type" style="width: 100%">
                <el-option v-for="t in types" :key="t" :label="t" :value="t" />
              </el-select>
            </el-form-item>
            <el-form-item label="甲方"><el-input v-model="form.party_a" placeholder="如：XX 科技有限公司" /></el-form-item>
            <el-form-item label="乙方"><el-input v-model="form.party_b" placeholder="如：XX 信息服务有限公司" /></el-form-item>
            <el-form-item label="标的 / 内容"><el-input v-model="form.subject" type="textarea" :rows="2" placeholder="合同标的或服务内容" /></el-form-item>
            <el-form-item label="价款"><el-input v-model="form.amount" placeholder="如：人民币 10 万元" /></el-form-item>
            <el-form-item label="期限"><el-input v-model="form.duration" placeholder="如：2026年1月1日至2026年12月31日" /></el-form-item>
            <el-form-item label="付款方式"><el-input v-model="form.payment_terms" type="textarea" :rows="2" placeholder="如：签订后付 30%，验收后付 70%" /></el-form-item>
            <el-form-item label="特殊约定"><el-input v-model="form.special" type="textarea" :rows="2" placeholder="保密、竞业、知识产权等特殊约定" /></el-form-item>
            <el-button type="primary" :loading="generating" class="full-btn" @click="doGenerate">生成标准合同</el-button>
          </el-form>
        </div>
      </section>

      <!-- 右：生成结果 -->
      <section class="block">
        <div class="block-bar yellow">
          生成结果
          <el-button v-if="result" size="small" class="copy-btn" @click="copyText">复制全文</el-button>
        </div>
        <div class="block-body">
          <el-empty v-if="!result" description="填写左侧要素后点击生成" />
          <template v-else>
            <div class="self-check" :class="{ fail: !result.self_check.passed }">
              <span class="sp-label">自检</span>
              <span class="self-check-text">{{ result.self_check.message }}</span>
            </div>
            <div class="contract-text">{{ result.contract_text }}</div>
          </template>
        </div>
      </section>
    </div>
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

<style scoped>
.page { padding: 0; }

/* 3:5 非对称分栏，紧贴 */
.split {
  display: grid;
  grid-template-columns: 3fr 5fr;
  gap: 0;
  border: var(--sp-line);
}
.split > .block { border: none; }
.split > .block + .block { border-left: var(--sp-line); }

.block-body { padding: 20px; }
.form :deep(.el-form-item) { margin-bottom: 16px; }
.form :deep(.el-form-item__label) {
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--sp-ink-70);
  padding-bottom: 2px;
  line-height: 1.5;
}
.full-btn { width: 100%; margin-top: 4px; }
.copy-btn { margin-left: auto; font-size: 11px; }

/* 自检结果条：整块色块 */
.self-check {
  display: flex;
  align-items: center;
  border: var(--sp-line);
  background: var(--sp-black);
  color: var(--sp-white);
  padding: 10px 14px;
  margin-bottom: 16px;
}
.self-check .sp-label { margin-right: 12px; color: var(--sp-white); }
.self-check.fail { background: var(--sp-yellow); color: var(--sp-black); }
.self-check.fail .sp-label { color: var(--sp-black); }
.self-check-text { font-size: 12.5px; font-weight: 700; }

.contract-text {
  border: var(--sp-line);
  padding: 20px;
  white-space: pre-wrap;
  line-height: 1.9;
  font-size: 13.5px;
  max-height: calc(100vh - 300px);
  overflow-y: auto;
}

@media (max-width: 1100px) {
  .split { grid-template-columns: 1fr; }
  .split > .block + .block { border-left: none; border-top: var(--sp-line); }
}
</style>
