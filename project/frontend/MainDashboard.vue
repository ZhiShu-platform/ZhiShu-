<template>
  <div class="main-dashboard">
    <header class="dashboard-header">
      <div class="header-content">
        <h1>智枢应急管理系统</h1>
        <div class="header-subtitle">MCP智能体工作流管理平台</div>
      </div>
      <div class="header-actions">
        <button @click="refreshSystemStatus" :disabled="isRefreshing" class="btn btn-primary">
          {{ isRefreshing ? '刷新中...' : '刷新状态' }}
        </button>
        <div class="system-indicator" :class="{ healthy: systemHealthy }">
          {{ systemHealthy ? '系统正常' : '系统异常' }}
        </div>
      </div>
    </header>

    <nav class="dashboard-nav">
      <button 
        @click="activeTab = 'workflow'" 
        :class="['nav-tab', { active: activeTab === 'workflow' }]"
      >
        📊 工作流管理
      </button>
      <button 
        @click="activeTab = 'chat'" 
        :class="['nav-tab', { active: activeTab === 'chat' }]"
      >
        💬 AI智能分析
      </button>
      <button 
        @click="activeTab = 'monitor'" 
        :class="['nav-tab', { active: activeTab === 'monitor' }]"
      >
        📈 系统监控
      </button>
    </nav>

    <main class="dashboard-content">
      <!-- 工作流管理标签页 -->
      <div v-if="activeTab === 'workflow'" class="tab-content">
        <WorkflowManager />
      </div>

      <!-- AI聊天标签页 -->
      <div v-if="activeTab === 'chat'" class="tab-content">
        <InteractiveAIChat 
          :selectedSubModel="selectedSubModel"
          :selectedRegion="selectedRegion"
          :drivingDatasets="drivingDatasets"
        />
      </div>

      <!-- 系统监控标签页 -->
      <div v-if="activeTab === 'monitor'" class="tab-content">
        <SystemMonitor />
      </div>
    </main>

    <!-- 快速状态栏 -->
    <div class="quick-status-bar">
      <div class="status-item">
        <span class="status-label">MCP服务:</span>
        <span class="status-value">
          {{ systemStatus.service_stats?.running || 0 }}/{{ systemStatus.service_stats?.total || 0 }}
        </span>
      </div>
      <div class="status-item">
        <span class="status-label">工作流:</span>
        <span class="status-value">
          {{ systemStatus.workflow_stats?.running || 0 }}/{{ systemStatus.workflow_stats?.total || 0 }}
        </span>
      </div>
      <div class="status-item">
        <span class="status-label">系统状态:</span>
        <span class="status-value" :class="{ healthy: systemHealthy }">
          {{ systemHealthy ? '正常' : '异常' }}
        </span>
      </div>
      <div class="status-item">
        <span class="status-label">最后更新:</span>
        <span class="status-value">{{ formatTime(systemStatus.timestamp) }}</span>
      </div>
    </div>
  </div>
</template>

<script>
import WorkflowManager from './WorkflowManager.vue'
import InteractiveAIChat from './InteractiveAIChat.vue'
import SystemMonitor from './SystemMonitor.vue'

export default {
  name: 'MainDashboard',
  components: {
    WorkflowManager,
    InteractiveAIChat,
    SystemMonitor
  },
  data() {
    return {
      activeTab: 'workflow',
      isRefreshing: false,
      systemStatus: {
        service_stats: { total: 0, running: 0 },
        workflow_stats: { total: 0, running: 0 },
        timestamp: null
      },
      selectedSubModel: null,
      selectedRegion: null,
      drivingDatasets: []
    }
  },
  
  computed: {
    systemHealthy() {
      return this.systemStatus.service_stats?.running > 0
    }
  },
  
  async mounted() {
    await this.refreshSystemStatus()
    this.startAutoRefresh()
  },
  
  beforeUnmount() {
    if (this.autoRefreshInterval) {
      clearInterval(this.autoRefreshInterval)
    }
  },
  
  methods: {
    async refreshSystemStatus() {
      this.isRefreshing = true
      try {
        const response = await fetch('/api/monitor/status')
        const data = await response.json()
        this.systemStatus = data
      } catch (error) {
        console.error('获取系统状态失败:', error)
      } finally {
        this.isRefreshing = false
      }
    },
    
    startAutoRefresh() {
      this.autoRefreshInterval = setInterval(() => {
        this.refreshSystemStatus()
      }, 30000) // 每30秒刷新一次
    },
    
    formatTime(timestamp) {
      if (!timestamp) return '未知'
      return new Date(timestamp).toLocaleString('zh-CN')
    }
  }
}
</script>

<style scoped>
.main-dashboard {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  flex-direction: column;
}

.dashboard-header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  padding: 20px 30px;
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content h1 {
  margin: 0;
  color: #2c3e50;
  font-size: 28px;
  font-weight: 700;
}

.header-subtitle {
  color: #7f8c8d;
  font-size: 14px;
  margin-top: 5px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 15px;
}

.system-indicator {
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: bold;
  text-transform: uppercase;
}

.system-indicator.healthy {
  background: #d4edda;
  color: #155724;
}

.system-indicator:not(.healthy) {
  background: #f8d7da;
  color: #721c24;
}

.dashboard-nav {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  padding: 0 30px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  display: flex;
  gap: 5px;
}

.nav-tab {
  background: none;
  border: none;
  padding: 15px 25px;
  font-size: 16px;
  color: #7f8c8d;
  cursor: pointer;
  border-bottom: 3px solid transparent;
  transition: all 0.3s ease;
  position: relative;
}

.nav-tab:hover {
  color: #2c3e50;
  background: rgba(255, 255, 255, 0.1);
}

.nav-tab.active {
  color: #667eea;
  border-bottom-color: #667eea;
  background: rgba(102, 126, 234, 0.1);
}

.dashboard-content {
  flex: 1;
  padding: 30px;
  overflow-y: auto;
}

.tab-content {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 15px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  min-height: 600px;
}

.quick-status-bar {
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 10px 30px;
  display: flex;
  justify-content: space-around;
  align-items: center;
  font-size: 14px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-label {
  color: #bdc3c7;
}

.status-value {
  font-weight: bold;
  color: #ecf0f1;
}

.status-value.healthy {
  color: #2ecc71;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s ease;
}

.btn-primary {
  background: #667eea;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #5a6fd8;
  transform: translateY(-1px);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .dashboard-header {
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }
  
  .dashboard-nav {
    flex-wrap: wrap;
    justify-content: center;
  }
  
  .nav-tab {
    padding: 12px 20px;
    font-size: 14px;
  }
  
  .dashboard-content {
    padding: 20px;
  }
  
  .quick-status-bar {
    flex-direction: column;
    gap: 10px;
    text-align: center;
  }
}

/* 动画效果 */
.tab-content {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.nav-tab {
  position: relative;
  overflow: hidden;
}

.nav-tab::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.nav-tab:hover::before {
  left: 100%;
}
</style>
