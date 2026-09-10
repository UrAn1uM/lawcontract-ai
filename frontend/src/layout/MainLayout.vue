<template>
  <div class="shell">
    <header class="topbar">
      <div class="brand">法律合同<br />智能系统</div>

      <nav class="nav">
        <router-link
          v-for="item in navs"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: $route.path === item.path }"
        >{{ item.title }}</router-link>
      </nav>

      <div class="account">
        <span class="who">{{ username }}</span>
        <button class="quit" @click="logout">退出</button>
      </div>
    </header>

    <main class="main"><router-view /></main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'

const router = useRouter()
const store = useUserStore()
const username = computed(() => store.username)

// 智能问答已并入首页，这里不再单独入口
const navs = [
  { path: '/welcome', title: '首页' },
  { path: '/review', title: '合同审查' },
  { path: '/generate', title: '合同生成' },
  { path: '/compare', title: '条款比对' },
  { path: '/knowledge', title: '知识库管理' },
  { path: '/profile', title: '个人中心' }
]

function logout() {
  store.logout()
  router.push('/login')
}
</script>

<style scoped>
.shell { display: flex; flex-direction: column; height: 100vh; }

.topbar {
  display: flex;
  align-items: stretch;
  height: 58px;
  background: var(--sp-white);
  border-bottom: var(--sp-line);
  flex: none;
}

/* 品牌做成整块黑，海报式压边 */
.brand {
  display: flex;
  align-items: center;
  padding: 0 22px;
  background: var(--sp-black);
  color: var(--sp-white);
  font-size: 13px;
  font-weight: 900;
  line-height: 1.15;
  letter-spacing: 0.1em;
  border-right: var(--sp-line);
  flex: none;
}

.nav { display: flex; flex: 1; min-width: 0; overflow: hidden; }

.nav-item {
  display: flex;
  align-items: center;
  padding: 0 16px;
  border-right: var(--sp-line);
  color: var(--sp-black);
  text-decoration: none;
  font-size: 13px;
  font-weight: 900;
  letter-spacing: 0.06em;
  white-space: nowrap;
}
/* 色块入侵：hover 时整块变黑、文字反白 */
.nav-item:hover { background: var(--sp-black); color: var(--sp-white); }
.nav-item.active { background: var(--sp-red); color: var(--sp-black); }

.account { display: flex; align-items: stretch; border-left: var(--sp-line); flex: none; }
.who {
  display: flex;
  align-items: center;
  padding: 0 14px;
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}
.quit {
  border: none;
  border-left: var(--sp-line);
  background: var(--sp-white);
  color: var(--sp-black);
  font-family: inherit;
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0.14em;
  padding: 0 18px;
  cursor: pointer;
}
.quit:hover { background: var(--sp-red); color: var(--sp-black); }

.main { flex: 1; min-height: 0; overflow: auto; background: var(--sp-white); }
</style>
