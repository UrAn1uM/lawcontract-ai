import axios from 'axios'
import { ElMessage } from 'element-plus'

// 统一 axios 实例：自动带 token、统一错误提示
// 超时给 5 分钟——LLM 审查长合同耗时较长
const request = axios.create({
  baseURL: '/api',
  timeout: 300000
})

request.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

request.interceptors.response.use(
  (resp) => resp.data,
  (err) => {
    const detail = err.response?.data?.detail
    const msg = typeof detail === 'string' ? detail : detail?.[0]?.msg || err.message || '请求失败'
    ElMessage.error(msg)
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      if (location.pathname !== '/login') location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default request
