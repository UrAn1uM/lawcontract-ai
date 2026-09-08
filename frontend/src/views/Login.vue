<template>
  <div class="login">
    <div class="strip">法律合同智能系统</div>
    <div class="content">
      <h1 class="title">登录</h1>
      <p class="desc">合同审查与生成系统，基于条款库与法规库的混合检索。</p>
      <el-form :model="form" class="form" @keyup.enter="login">
        <el-form-item>
          <el-input v-model="form.username" placeholder="用户名" size="large" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.password" type="password" show-password placeholder="密码" size="large" />
        </el-form-item>
        <el-button type="primary" size="large" class="btn" :loading="loading" @click="login">登 录</el-button>
      </el-form>
      <p class="hint">默认账号 admin / admin123</p>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { login as loginApi } from '../api'
import { useUserStore } from '../stores/user'

const router = useRouter()
const store = useUserStore()
const form = reactive({ username: 'admin', password: 'admin123' })
const loading = ref(false)

async function login() {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    const data = await loginApi(form)
    store.setLogin(data.access_token, form.username)
    ElMessage.success('登录成功')
    router.push('/')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login {
  min-height: 100vh;
  background: #ffffff;
}
.strip {
  background: #1a1a1a;
  color: #ffffff;
  padding: 12px 24px;
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 2px;
}
.content {
  max-width: 420px;
  padding: 60px 24px;
}
.title {
  margin: 0 0 8px;
  font-size: 32px;
  font-weight: 700;
  color: #000000;
  letter-spacing: 2px;
}
.desc {
  margin: 0 0 32px;
  font-size: 14px;
  color: #8A8A8A;
  line-height: 1.6;
}
.form { margin-bottom: 16px; }
.btn {
  width: 100%;
  letter-spacing: 8px;
  font-weight: 500;
}
.hint {
  margin: 0;
  font-size: 12px;
  color: #8A8A8A;
}
</style>
