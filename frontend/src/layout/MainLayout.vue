<template>
  <el-container direction="vertical" class="shell">
    <el-header class="topbar">
      <div class="topbar-left">
        <span class="brand">法律合同智能系统</span>
        <el-menu mode="horizontal" :default-active="$route.path" router class="nav" :ellipsis="false">
          <el-menu-item index="/dashboard">工作台</el-menu-item>
          <el-menu-item index="/review">合同审查</el-menu-item>
          <el-menu-item index="/generate">合同生成</el-menu-item>
          <el-menu-item index="/compare">条款比对</el-menu-item>
          <el-menu-item index="/chat">智能问答</el-menu-item>
          <el-menu-item index="/knowledge">知识库管理</el-menu-item>
          <el-menu-item index="/profile">个人中心</el-menu-item>
        </el-menu>
      </div>
      <div class="topbar-right">
        <span class="username">{{ username }}</span>
        <el-button size="small" text @click="logout">退出</el-button>
      </div>
    </el-header>
    <el-main class="main"><router-view /></el-main>
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
.shell { height: 100vh; }

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #ffffff;
  border-bottom: 1px solid #d9d9d9;
  height: 52px;
  padding: 0 24px;
}
.topbar-left { display: flex; align-items: center; height: 100%; }
.brand {
  font-size: 15px;
  font-weight: 700;
  color: #000000;
  letter-spacing: 1px;
  margin-right: 28px;
  padding-right: 28px;
  border-right: 1px solid #d9d9d9;
}

.nav { border-bottom: none; height: 100%; }
.nav :deep(.el-menu-item) {
  height: 52px;
  line-height: 52px;
  font-size: 13px;
  color: #4a4a4a;
  padding: 0 16px;
  border-radius: 0;
  border-bottom: 2px solid transparent;
}
.nav :deep(.el-menu-item:hover) { color: #E2231A; }
.nav :deep(.el-menu-item.is-active) {
  color: #E2231A;
  border-bottom-color: #E2231A;
  font-weight: 500;
}

.topbar-right { display: flex; align-items: center; gap: 12px; }
.username { color: #8A8A8A; font-size: 13px; }

.main { padding: 0; background: #ffffff; }
</style>
