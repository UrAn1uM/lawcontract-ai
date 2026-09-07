<template>
  <el-container style="height: 100vh">
    <el-aside width="210px" style="background: #1d2b3a">
      <div class="logo">法律合同智能系统</div>
      <el-menu
        :default-active="$route.path"
        router
        background-color="#1d2b3a"
        text-color="#c0c8d0"
        active-text-color="#409eff"
      >
        <el-menu-item index="/dashboard">工作台</el-menu-item>
        <el-menu-item index="/review">合同审查</el-menu-item>
        <el-menu-item index="/generate">合同生成</el-menu-item>
        <el-menu-item index="/compare">条款比对</el-menu-item>
        <el-menu-item index="/chat">智能问答</el-menu-item>
        <el-menu-item index="/knowledge">知识库管理</el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header style="display: flex; align-items: center; justify-content: space-between; background: #fff; border-bottom: 1px solid #e4e7ed">
        <span style="font-weight: 500">{{ $route.meta.title || '' }}</span>
        <div>
          <span style="margin-right: 16px; color: #606266">{{ username }}</span>
          <el-button size="small" @click="logout">退出登录</el-button>
        </div>
      </el-header>
      <el-main style="padding: 0">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'

const router = useRouter()
const store = useUserStore()
const username = computed(() => store.username)

function logout() {
  store.logout()
  router.push('/login')
}
</script>

<style scoped>
.logo {
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  text-align: center;
  padding: 20px 0;
  letter-spacing: 1px;
}
</style>
