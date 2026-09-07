<template>
  <div class="page" style="display: flex; align-items: center; justify-content: center; height: 100vh; background: #1d2b3a">
    <el-card style="width: 400px">
      <h2 style="text-align: center; margin-top: 0">智能法律合同<br />审查与生成系统</h2>
      <el-form :model="form" label-width="70px" @keyup.enter="login">
        <el-form-item label="用户名">
          <el-input v-model="form.username" placeholder="admin" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" show-password placeholder="admin123" />
        </el-form-item>
        <el-button type="primary" :loading="loading" style="width: 100%" @click="login">登 录</el-button>
        <p style="color: #909399; font-size: 12px; text-align: center">
          默认账号：admin / admin123（管理员）、demo / demo123
        </p>
      </el-form>
    </el-card>
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
