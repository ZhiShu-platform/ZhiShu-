import { createApp } from 'vue'
import MainDashboard from './MainDashboard.vue'
import './styles/globals.css'

// 创建Vue应用实例
const app = createApp(MainDashboard)

// 全局配置
app.config.errorHandler = (err, vm, info) => {
  console.error('Vue错误:', err, info)
}

app.config.warnHandler = (msg, vm, trace) => {
  console.warn('Vue警告:', msg, trace)
}

// 全局过滤器
app.config.globalProperties.$filters = {
  formatTime(timestamp) {
    if (!timestamp) return ''
    const date = new Date(timestamp)
    return date.toLocaleString('zh-CN')
  },
  
  formatDuration(ms) {
    if (!ms) return '0ms'
    if (ms < 1000) return `${ms}ms`
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
    return `${(ms / 60000).toFixed(1)}m`
  },
  
  formatFileSize(bytes) {
    if (!bytes) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }
}

// 挂载应用
app.mount('#app')

// 移除加载动画
document.addEventListener('DOMContentLoaded', () => {
  const loadingContainer = document.querySelector('.loading-container')
  if (loadingContainer) {
    loadingContainer.style.opacity = '0'
    setTimeout(() => {
      loadingContainer.remove()
    }, 300)
  }
})

// 环境检测
if (import.meta.env.DEV) {
  console.log('🚀 智枢应急管理系统前端模块 - 开发模式')
  console.log('📍 后端API地址: http://10.0.3.4:3000')
  console.log('🌐 前端地址: http://localhost:3000')
} else {
  console.log('🚀 智枢应急管理系统前端模块 - 生产模式')
}

// PWA服务工作者注册（如果支持）
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then(registration => {
        console.log('SW注册成功:', registration.scope)
      })
      .catch(error => {
        console.log('SW注册失败:', error)
      })
  })
}

// 网络状态监控
window.addEventListener('online', () => {
  console.log('🌐 网络连接已恢复')
})

window.addEventListener('offline', () => {
  console.log('❌ 网络连接已断开')
})

// 错误边界
window.addEventListener('error', (event) => {
  console.error('全局错误:', event.error)
})

window.addEventListener('unhandledrejection', (event) => {
  console.error('未处理的Promise拒绝:', event.reason)
})
