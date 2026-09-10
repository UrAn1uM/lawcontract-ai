import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layout/MainLayout.vue'

const routes = [
  { path: '/login', component: () => import('../views/Login.vue') },
  {
    path: '/',
    component: MainLayout,
    redirect: '/welcome',
    children: [
      { path: 'welcome', component: () => import('../views/Welcome.vue'), meta: { title: '首页' } },
      { path: 'review', component: () => import('../views/ContractReview.vue'), meta: { title: '合同审查' } },
      { path: 'generate', component: () => import('../views/ContractGenerate.vue'), meta: { title: '合同生成' } },
      { path: 'compare', component: () => import('../views/ContractCompare.vue'), meta: { title: '条款比对' } },
      { path: 'knowledge', component: () => import('../views/KnowledgeAdmin.vue'), meta: { title: '知识库管理' } },
      { path: 'profile', component: () => import('../views/Profile.vue'), meta: { title: '个人中心' } }
    ]
  }
]

const router = createRouter({ history: createWebHistory(), routes })

// 登录守卫
router.beforeEach((to) => {
  if (to.path !== '/login' && !localStorage.getItem('token')) return '/login'
})

export default router
