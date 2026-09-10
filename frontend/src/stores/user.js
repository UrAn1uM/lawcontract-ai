import { defineStore } from 'pinia'
import { useWorkspaceStore } from './workspace'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    username: localStorage.getItem('username') || ''
  }),
  actions: {
    setLogin(token, username) {
      this.token = token
      this.username = username
      localStorage.setItem('token', token)
      localStorage.setItem('username', username)
    },
    logout() {
      this.token = ''
      this.username = ''
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      // 退出即清空审查工作区（已审查的报告与生成的合同仍在「个人中心」）
      useWorkspaceStore().clear()
    }
  }
})
