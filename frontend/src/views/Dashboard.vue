<template>
  <div class="page">
    <div class="section-bar">工作台</div>
    <div class="content">
      <p class="intro">欢迎使用法律合同智能系统。首次使用请按以下步骤完成知识库初始化，之后即可使用审查、生成、比对与问答功能。</p>

      <div class="steps">
        <div class="step" v-for="(s, i) in steps" :key="i">
          <div class="num">{{ String(i + 1).padStart(2, '0') }}</div>
          <div class="step-body">
            <div class="step-title">{{ s.title }}</div>
            <div class="step-desc">{{ s.desc }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const steps = [
  { title: '添加条款与法规', desc: '以管理员身份登录，在「知识库管理」录入标准条款与法规条文。' },
  { title: '重建向量索引', desc: '点击「重建向量索引」，让检索引擎加载最新的条款与法规。' },
  { title: '上传合同并审查', desc: '在「合同审查」上传合同，系统将逐条识别风险并给出依据。' }
]
</script>

<style scoped>
.page { padding: 0; }
.section-bar {
  background: #1a1a1a;
  color: #ffffff;
  padding: 10px 24px;
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 1px;
}
.content { padding: 32px 24px; }
.intro {
  margin: 0 0 40px;
  font-size: 14px;
  color: #4a4a4a;
  line-height: 1.8;
  max-width: 640px;
}
.steps { display: flex; flex-direction: column; }
.step {
  display: flex;
  align-items: flex-start;
  padding: 20px 0;
  border-top: 1px solid #d9d9d9;
}
.step:first-child { border-top: none; padding-top: 0; }
.num {
  font-size: 40px;
  font-weight: 700;
  color: #E2231A;
  line-height: 1;
  margin-right: 28px;
  min-width: 64px;
  font-variant-numeric: tabular-nums;
}
.step-title {
  font-size: 16px;
  font-weight: 600;
  color: #000000;
  margin-bottom: 4px;
}
.step-desc { font-size: 13px; color: #8A8A8A; line-height: 1.6; }
</style>
