<template>
  <div class="page">
    <el-row :gutter="20">
      <el-col :span="6" v-for="m in modules" :key="m.path">
        <el-card class="card-box" style="cursor: pointer" @click="$router.push(m.path)">
          <h3 style="margin-top: 0">{{ m.title }}</h3>
          <p style="color: #606266; font-size: 13px; min-height: 40px">{{ m.desc }}</p>
        </el-card>
      </el-col>
    </el-row>
    <el-card class="card-box" style="margin-top: 20px">
      <h3 style="margin-top: 0">快速开始</h3>
      <el-steps :active="3" simple>
        <el-step title="管理员添加条款/法规" />
        <el-step title="重建向量索引" />
        <el-step title="上传合同并审查" />
      </el-steps>
      <p style="color: #909399; font-size: 13px">
        提示：首次使用请先用 admin 登录，在"知识库管理"添加标准条款与法规，点击"重建向量索引"后再使用审查与问答功能。
      </p>
    </el-card>
  </div>
</template>

<script setup>
const modules = [
  { path: '/review', title: '合同智能审查', desc: '上传合同，逐条识别法律风险、权利义务不对等条款，给出修改建议与依据' },
  { path: '/generate', title: '标准合同生成', desc: '填写合同要素，自动生成规范合同文本并自检必备条款' },
  { path: '/compare', title: '条款比对', desc: '两份合同/两个版本的条款级差异比对，区分措辞修改与语义修改' },
  { path: '/chat', title: '智能问答', desc: '自然语言对话，自动检索条款库与法规库回答合同法律问题' }
]
</script>
