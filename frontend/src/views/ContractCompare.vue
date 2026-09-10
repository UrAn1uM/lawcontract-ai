<template>
  <div class="page">
    <!-- 双栏输入：1:1 紧贴 -->
    <div class="split">
      <section class="block">
        <div class="block-bar">版本 A · 我方 / 旧版</div>
        <div class="block-body">
          <el-input v-model="textA" type="textarea" :rows="16" placeholder="粘贴第一份合同全文…" />
        </div>
      </section>
      <section class="block">
        <div class="block-bar">版本 B · 对方 / 新版</div>
        <div class="block-body">
          <el-input v-model="textB" type="textarea" :rows="16" placeholder="粘贴第二份合同全文…" />
        </div>
      </section>
    </div>

    <!-- 操作条：整块按钮，无间距 -->
    <div class="action-bar">
      <button
        class="run-btn"
        :disabled="comparing || !textA || !textB"
        @click="doCompare"
      >{{ comparing ? '比对中…' : '开始比对' }}</button>
      <span class="run-hint">文本层找字面增删改，语义层判断意思是否实质变化</span>
    </div>

    <!-- 比对结果 -->
    <section v-if="result" class="block result-block">
      <div class="block-bar red">比对结果</div>
      <div class="summary-strip">
        <div v-for="(count, type) in result.summary" :key="type" class="summary-cell" :class="cellClass(type)">
          <span class="summary-type">{{ type }}</span>
          <span class="summary-count">{{ count }}</span>
        </div>
      </div>

      <el-table :data="result.diffs" size="small" border class="table">
        <el-table-column label="差异类型" width="110">
          <template #default="{ row }">
            <span class="type-tag" :class="cellClass(row.type)">{{ row.type }}</span>
          </template>
        </el-table-column>
        <el-table-column label="版本 A 条款" min-width="240">
          <template #default="{ row }">
            <b v-if="row.a_no">{{ row.a_no }}</b>
            <div class="cell-text">{{ row.a_content }}</div>
          </template>
        </el-table-column>
        <el-table-column label="版本 B 条款" min-width="240">
          <template #default="{ row }">
            <b v-if="row.b_no">{{ row.b_no }}</b>
            <div class="cell-text">{{ row.b_content }}</div>
          </template>
        </el-table-column>
        <el-table-column label="字面相似度" width="110" align="center">
          <template #default="{ row }">{{ (row.text_similarity * 100).toFixed(0) }}%</template>
        </el-table-column>
        <el-table-column label="语义变化" width="100" align="center">
          <template #default="{ row }">{{ (row.semantic_change * 100).toFixed(0) }}%</template>
        </el-table-column>
      </el-table>

      <p class="note">措辞修改 = 字面变化但语义基本不变；语义修改 = 权利义务发生实质变化，建议重点关注。</p>
    </section>
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

// 用色块而非彩色标签表达差异类型（黑白为主 + 原色）
function cellClass(type) {
  return {
    新增: 'is-add',
    删除: 'is-del',
    语义修改: 'is-semantic',
    措辞修改: 'is-wording',
    未变: 'is-same'
  }[type] || 'is-same'
}
</script>

<style scoped>
.page { padding: 0; }

.split {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0;
  border: var(--sp-line);
}
.split > .block { border: none; }
.split > .block + .block { border-left: var(--sp-line); }
.block-body { padding: 20px; }

/* 操作条 */
.action-bar {
  display: flex;
  align-items: stretch;
  border: var(--sp-line);
  border-top: none;
}
.run-btn {
  border: none;
  border-right: var(--sp-line);
  background: var(--sp-black);
  color: var(--sp-white);
  font-family: inherit;
  font-size: 14px;
  font-weight: 900;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  padding: 18px 40px;
  cursor: pointer;
}
.run-btn:hover:not(:disabled) { background: var(--sp-red); color: var(--sp-black); }
.run-btn:disabled { background: var(--sp-gray); color: var(--sp-ink-30); cursor: not-allowed; }
.run-hint {
  display: flex;
  align-items: center;
  padding: 0 18px;
  font-size: 12px;
  font-weight: 700;
  color: var(--sp-ink-30);
  letter-spacing: 0.04em;
}

.result-block { border-top: none; }

/* 汇总条：每格一个色块 */
.summary-strip { display: flex; border-bottom: var(--sp-line); }
.summary-cell {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  border-right: var(--sp-hair);
  padding: 14px 16px;
}
.summary-cell:last-child { border-right: none; }
.summary-type { font-size: 11px; font-weight: 900; letter-spacing: 0.16em; }
.summary-count { font-size: 30px; font-weight: 900; line-height: 1.1; letter-spacing: -0.03em; }

.is-add { background: var(--sp-red); color: var(--sp-black); }
.is-del { background: var(--sp-black); color: var(--sp-white); }
.is-semantic { background: var(--sp-blue); color: var(--sp-white); }
.is-wording { background: var(--sp-yellow); color: var(--sp-black); }
.is-same { background: var(--sp-white); color: var(--sp-ink-30); }

.type-tag {
  display: inline-block;
  border: var(--sp-hair);
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 0.1em;
  padding: 2px 8px;
}

.table { width: 100%; }
.cell-text { color: var(--sp-ink-70); white-space: pre-wrap; font-size: 12.5px; }
.note { margin: 14px 20px 20px; font-size: 12px; color: var(--sp-ink-30); }

@media (max-width: 1000px) {
  .split { grid-template-columns: 1fr; }
  .split > .block + .block { border-left: none; border-top: var(--sp-line); }
  .summary-strip { flex-wrap: wrap; }
  .summary-cell { flex: 1 0 33.33%; }
}
</style>
