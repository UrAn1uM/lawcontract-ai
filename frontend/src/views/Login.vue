<template>
  <div class="login">
    <div class="sp-guides"><span v-for="i in 12" :key="i"></span></div>

    <!-- 左：海报色块 -->
    <section class="poster">
      <div class="poster-top">
        <span class="poster-mark">西北工业大学 × 四川华迪 · 校企联合实训</span>
      </div>
      <h1 class="poster-title">法律合同<br />智能系统</h1>
      <div class="poster-foot">
        <span class="poster-flow">合同审查 / 生成 / 比对 / 合规检查</span>
        <span class="poster-num">06</span>
      </div>
    </section>

    <!-- 右：登录表单 -->
    <section class="panel">
      <div class="panel-head">
        <span class="panel-title">登录</span>
        <span class="sp-label panel-en">Sign in</span>
      </div>

      <form class="form" @submit.prevent="login">
        <label class="field">
          <span class="sp-label">用户名</span>
          <input v-model="form.username" type="text" placeholder="用户名" autocomplete="username" />
        </label>

        <label class="field">
          <span class="sp-label">密码</span>
          <input v-model="form.password" type="password" placeholder="密码" autocomplete="current-password" />
        </label>

        <button class="submit" type="submit" :disabled="loading">
          {{ loading ? '登录中…' : '登 录' }}
        </button>
      </form>

      <p class="hint">默认账号 admin / admin123</p>
    </section>
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
  position: relative;
  min-height: 100vh;
  display: grid;
  grid-template-columns: 3fr 2fr;
  background: var(--sp-white);
  overflow: hidden;
}

/* ---------- 左：红色海报块 ---------- */
.poster {
  position: relative;
  z-index: 1;
  background: var(--sp-red);
  color: var(--sp-black);
  padding: 40px 44px 34px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.poster-mark { font-size: 11px; font-weight: 900; letter-spacing: 0.2em; }
.poster-title {
  font-size: clamp(52px, 7vw, 104px);
  font-weight: 900;
  line-height: 0.98;
  letter-spacing: -0.04em;
  margin: 0;
}
.poster-foot {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
}
.poster-flow { font-size: 13px; font-weight: 900; letter-spacing: 0.08em; }
.poster-num { font-size: 72px; font-weight: 900; line-height: 1; letter-spacing: -0.04em; }

/* ---------- 右：表单 ---------- */
.panel {
  position: relative;
  z-index: 1;
  background: var(--sp-white);
  border-left: var(--sp-line);
  padding: 40px 48px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.panel-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  border-bottom: var(--sp-line);
  padding-bottom: 14px;
  margin-bottom: 34px;
}
.panel-title { font-size: 34px; font-weight: 900; letter-spacing: -0.02em; }
.panel-en { color: var(--sp-ink-30); }

.form { display: flex; flex-direction: column; }
.field { display: flex; flex-direction: column; margin-bottom: 28px; }
.field .sp-label { color: var(--sp-ink-70); margin-bottom: 6px; }
.field input {
  border: none;
  border-bottom: 4px solid var(--sp-black);
  background: transparent;
  outline: none;
  font-family: inherit;
  font-size: 20px;
  font-weight: 700;
  padding: 6px 2px 10px;
  color: var(--sp-black);
}
.field input::placeholder { color: var(--sp-ink-30); font-weight: 400; }
.field input:focus { border-bottom-color: var(--sp-red); }

.submit {
  margin-top: 8px;
  border: var(--sp-line);
  background: var(--sp-black);
  color: var(--sp-white);
  font-family: inherit;
  font-size: 14px;
  font-weight: 900;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  padding: 18px;
  cursor: pointer;
}
.submit:hover:not(:disabled) { background: var(--sp-red); color: var(--sp-black); }
.submit:disabled { background: var(--sp-gray); border-color: var(--sp-ink-30); color: var(--sp-ink-30); cursor: not-allowed; }

.hint { margin: 22px 0 0; font-size: 12px; color: var(--sp-ink-30); font-weight: 700; letter-spacing: 0.06em; }

@media (max-width: 980px) {
  .login { grid-template-columns: 1fr; }
  .poster { padding: 32px 28px; }
  .panel { border-left: none; border-top: var(--sp-line); padding: 32px 28px; }
}
</style>
