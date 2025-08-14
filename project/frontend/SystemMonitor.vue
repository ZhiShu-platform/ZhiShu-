<template>
  <div class="system-monitor">
    <div class="monitor-header">
      <h2>系统监控仪表板</h2>
      <div class="monitor-actions">
        <button @click="refreshData" :disabled="isRefreshing" class="btn btn-primary">
          {{ isRefreshing ? '刷新中...' : '刷新数据' }}
        </button>
        <button @click="exportData" class="btn btn-success">导出数据</button>
      </div>
    </div>

    <!-- 系统概览卡片 -->
    <div class="overview-cards">
      <div class="overview-card">
        <div class="card-icon">🔧</div>
        <div class="card-content">
          <h3>MCP服务</h3>
          <div class="card-stats">
            <div class="stat">
              <span class="stat-value">{{ systemStatus.service_stats?.total || 0 }}</span>
              <span class="stat-label">总数</span>
            </div>
            <div class="stat">
              <span class="stat-value running">{{ systemStatus.service_stats?.running || 0 }}</span>
              <span class="stat-label">运行中</span>
            </div>
            <div class="stat">
              <span class="stat-value stopped">{{ systemStatus.service_stats?.stopped || 0 }}</span>
              <span class="stat-label">已停止</span>
            </div>
          </div>
        </div>
      </div>

      <div class="overview-card">
        <div class="card-icon">📋</div>
        <div class="card-content">
          <h3>工作流</h3>
          <div class="card-stats">
            <div class="stat">
              <span class="stat-value">{{ systemStatus.workflow_stats?.total || 0 }}</span>
              <span class="stat-label">总数</span>
            </div>
            <div class="stat">
              <span class="stat-value running">{{ systemStatus.workflow_stats?.running || 0 }}</span>
              <span class="stat-label">运行中</span>
            </div>
            <div class="stat">
              <span class="stat-value completed">{{ systemStatus.workflow_stats?.completed || 0 }}</span>
              <span class="stat-label">已完成</span>
            </div>
          </div>
        </div>
      </div>

      <div class="overview-card">
        <div class="card-icon">🌐</div>
        <div class="card-content">
          <h3>网络连接</h3>
          <div class="card-stats">
            <div class="stat">
              <span class="stat-value">{{ systemStatus.active_connections || 0 }}</span>
              <span class="stat-label">活跃连接</span>
            </div>
            <div class="stat">
              <span class="stat-value">{{ websocketStatus }}</span>
              <span class="stat-label">WebSocket</span>
            </div>
          </div>
        </div>
      </div>

      <div class="overview-card">
        <div class="card-icon">⏰</div>
        <div class="card-content">
          <h3>系统状态</h3>
          <div class="card-stats">
            <div class="stat">
              <span class="stat-value" :class="{ healthy: systemHealthy }">
                {{ systemHealthy ? '正常' : '异常' }}
              </span>
              <span class="stat-label">健康状态</span>
            </div>
            <div class="stat">
              <span class="stat-value">{{ uptime }}</span>
              <span class="stat-label">运行时间</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 详细监控信息 -->
    <div class="monitor-sections">
      <!-- MCP服务详细状态 -->
      <div class="monitor-section">
        <h3>MCP服务详细状态</h3>
        <div class="service-details">
          <div v-for="service in mcpServices" :key="service.name" class="service-item">
            <div class="service-info">
              <div class="service-name">{{ service.display_name }}</div>
              <div class="service-meta">
                <span class="service-env">{{ service.conda_env }}</span>
                <span class="service-port">端口: {{ service.port }}</span>
                <span v-if="service.pid" class="service-pid">PID: {{ service.pid }}</span>
              </div>
            </div>
            <div class="service-status" :class="getStatusClass(service.status)">
              {{ getStatusText(service.status) }}
            </div>
            <div v-if="service.error_message" class="service-error">
              {{ service.error_message }}
            </div>
          </div>
        </div>
      </div>

      <!-- 工作流执行历史 -->
      <div class="monitor-section">
        <h3>工作流执行历史</h3>
        <div class="workflow-history">
          <div v-for="instance in recentWorkflows" :key="instance.id" class="workflow-item">
            <div class="workflow-header">
              <span class="workflow-name">{{ instance.workflow_name }}</span>
              <span class="workflow-status" :class="getWorkflowStatusClass(instance.status)">
                {{ getWorkflowStatusText(instance.status) }}
              </span>
            </div>
            <div class="workflow-details">
              <span class="workflow-time">{{ formatTime(instance.start_time) }}</span>
              <span v-if="instance.total_execution_time" class="workflow-duration">
                执行时间: {{ instance.total_execution_time.toFixed(2) }}s
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 系统资源使用 -->
      <div class="monitor-section">
        <h3>系统资源使用</h3>
        <div class="resource-usage">
          <div class="resource-item">
            <div class="resource-label">CPU使用率</div>
            <div class="resource-bar">
              <div class="resource-fill" :style="{ width: cpuUsage + '%' }"></div>
            </div>
            <div class="resource-value">{{ cpuUsage }}%</div>
          </div>
          <div class="resource-item">
            <div class="resource-label">内存使用率</div>
            <div class="resource-bar">
              <div class="resource-fill" :style="{ width: memoryUsage + '%' }"></div>
            </div>
            <div class="resource-value">{{ memoryUsage }}%</div>
          </div>
          <div class="resource-item">
            <div class="resource-label">磁盘使用率</div>
            <div class="resource-bar">
              <div class="resource-fill" :style="{ width: diskUsage + '%' }"></div>
            </div>
            <div class="resource-value">{{ diskUsage }}%</div>
          </div>
        </div>
      </div>

      <!-- 实时日志 -->
      <div class="monitor-section">
        <h3>实时系统日志</h3>
        <div class="log-container">
          <div class="log-controls">
            <button @click="clearLogs" class="btn btn-sm btn-secondary">清空日志</button>
            <button @click="toggleLogAutoScroll" class="btn btn-sm" :class="logAutoScroll ? 'btn-success' : 'btn-warning'">
              {{ logAutoScroll ? '停止自动滚动' : '开始自动滚动' }}
            </button>
          </div>
          <div class="log-viewer" ref="logViewer">
            <div v-for="log in systemLogs" :key="log.id" class="log-entry" :class="log.level">
              <span class="log-timestamp">{{ formatTime(log.timestamp) }}</span>
              <span class="log-level">{{ log.level.toUpperCase() }}</span>
              <span class="log-message">{{ log.message }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 性能图表 -->
    <div class="performance-charts">
      <h3>性能趋势图</h3>
      <div class="charts-grid">
        <div class="chart-container">
          <h4>MCP服务响应时间</h4>
          <div class="chart-placeholder">
            <div class="chart-message">图表功能开发中...</div>
            <div class="chart-data">
              <div v-for="(time, service) in responseTimes" :key="service" class="chart-data-item">
                <span class="data-label">{{ service }}:</span>
                <span class="data-value">{{ time }}ms</span>
              </div>
            </div>
          </div>
        </div>
        
        <div class="chart-container">
          <h4>工作流执行统计</h4>
          <div class="chart-placeholder">
            <div class="chart-message">图表功能开发中...</div>
            <div class="chart-data">
              <div class="chart-data-item">
                <span class="data-label">成功率:</span>
                <span class="data-value">{{ successRate }}%</span>
              </div>
              <div class="chart-data-item">
                <span class="data-label">平均执行时间:</span>
                <span class="data-value">{{ avgExecutionTime }}s</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SystemMonitor',
  data() {
    return {
      isRefreshing: false,
      systemStatus: {},
      mcpServices: [],
      recentWorkflows: [],
      systemLogs: [],
      logAutoScroll: true,
      cpuUsage: 45,
      memoryUsage: 62,
      diskUsage: 78,
      responseTimes: {
        'NFDRS4': 120,
        'LISFLOOD': 180,
        'CLIMADA': 95,
        'Aurora': 150,
        'Cell2Fire': 200
      },
      successRate: 92,
      avgExecutionTime: 8.5,
      uptime: '2天 14小时 32分钟'
    }
  },
  
  computed: {
    systemHealthy() {
      return this.systemStatus.service_stats?.running > 0
    },
    
    websocketStatus() {
      return this.systemStatus.active_connections > 0 ? '已连接' : '未连接'
    }
  },
  
  async mounted() {
    await this.refreshData()
    this.startAutoRefresh()
    this.startLogSimulation()
  },
  
  beforeUnmount() {
    if (this.autoRefreshInterval) {
      clearInterval(this.autoRefreshInterval)
    }
    if (this.logSimulationInterval) {
      clearInterval(this.logSimulationInterval)
    }
  },
  
  methods: {
    async refreshData() {
      this.isRefreshing = true
      try {
        await Promise.all([
          this.fetchSystemStatus(),
          this.fetchMCPServices(),
          this.fetchWorkflowInstances(),
          this.fetchSystemLogs()
        ])
      } catch (error) {
        console.error('刷新数据失败:', error)
      } finally {
        this.isRefreshing = false
      }
    },
    
    async fetchSystemStatus() {
      try {
        const response = await fetch('/api/monitor/status')
        const data = await response.json()
        this.systemStatus = data
      } catch (error) {
        console.error('获取系统状态失败:', error)
      }
    },
    
    async fetchMCPServices() {
      try {
        const response = await fetch('/api/mcp/services')
        const data = await response.json()
        this.mcpServices = data.services
      } catch (error) {
        console.error('获取MCP服务失败:', error)
      }
    },
    
    async fetchWorkflowInstances() {
      try {
        const response = await fetch('/api/workflows/instances')
        const data = await response.json()
        this.recentWorkflows = data.instances.slice(0, 10) // 只显示最近10个
      } catch (error) {
        console.error('获取工作流实例失败:', error)
      }
    },
    
    async fetchSystemLogs() {
      try {
        const response = await fetch('/api/monitor/logs?limit=50')
        const data = await response.json()
        this.systemLogs = data.logs
      } catch (error) {
        console.error('获取系统日志失败:', error)
      }
    },
    
    startAutoRefresh() {
      this.autoRefreshInterval = setInterval(() => {
        this.refreshData()
      }, 30000) // 每30秒刷新一次
    },
    
    startLogSimulation() {
      this.logSimulationInterval = setInterval(() => {
        this.addSimulatedLog()
      }, 5000) // 每5秒添加一条模拟日志
    },
    
    addSimulatedLog() {
      const logLevels = ['INFO', 'WARN', 'ERROR']
      const logMessages = [
        '系统运行正常',
        'MCP服务状态检查完成',
        '工作流执行进度更新',
        '数据库连接正常',
        '网络连接稳定',
        '内存使用率正常',
        '磁盘空间充足'
      ]
      
      const log = {
        id: Date.now(),
        timestamp: new Date().toISOString(),
        level: logLevels[Math.floor(Math.random() * logLevels.length)],
        message: logMessages[Math.floor(Math.random() * logMessages.length)]
      }
      
      this.systemLogs.unshift(log)
      
      // 限制日志数量
      if (this.systemLogs.length > 100) {
        this.systemLogs = this.systemLogs.slice(0, 100)
      }
      
      // 自动滚动
      if (this.logAutoScroll) {
        this.$nextTick(() => {
          const container = this.$refs.logViewer
          if (container) {
            container.scrollTop = container.scrollHeight
          }
        })
      }
    },
    
    exportData() {
      const data = {
        systemStatus: this.systemStatus,
        mcpServices: this.mcpServices,
        recentWorkflows: this.recentWorkflows,
        systemLogs: this.systemLogs,
        exportTime: new Date().toISOString()
      }
      
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `system_monitor_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`
      a.click()
      URL.revokeObjectURL(url)
    },
    
    clearLogs() {
      this.systemLogs = []
    },
    
    toggleLogAutoScroll() {
      this.logAutoScroll = !this.logAutoScroll
    },
    
    getStatusClass(status) {
      const classMap = {
        'running': 'status-running',
        'stopped': 'status-stopped',
        'error': 'status-error',
        'starting': 'status-starting',
        'stopping': 'status-stopping'
      }
      return classMap[status] || 'status-unknown'
    },
    
    getStatusText(status) {
      const textMap = {
        'running': '运行中',
        'stopped': '已停止',
        'error': '错误',
        'starting': '启动中',
        'stopping': '停止中'
      }
      return textMap[status] || status
    },
    
    getWorkflowStatusClass(status) {
      const classMap = {
        'running': 'status-running',
        'completed': 'status-completed',
        'failed': 'status-failed',
        'pending': 'status-pending',
        'cancelled': 'status-cancelled'
      }
      return classMap[status] || 'status-unknown'
    },
    
    getWorkflowStatusText(status) {
      const textMap = {
        'running': '运行中',
        'completed': '已完成',
        'failed': '失败',
        'pending': '等待中',
        'cancelled': '已取消'
      }
      return textMap[status] || status
    },
    
    formatTime(timestamp) {
      if (!timestamp) return '未知'
      return new Date(timestamp).toLocaleString('zh-CN')
    }
  }
}
</script>

<style scoped>
.system-monitor {
  padding: 20px;
}

.monitor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.monitor-header h2 {
  margin: 0;
  color: #2c3e50;
}

.monitor-actions {
  display: flex;
  gap: 10px;
}

.overview-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.overview-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 20px;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.overview-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
}

.card-icon {
  font-size: 48px;
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 50%;
  color: white;
}

.card-content h3 {
  margin: 0 0 15px 0;
  color: #2c3e50;
  font-size: 18px;
}

.card-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
}

.stat {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 24px;
  font-weight: bold;
  color: #2c3e50;
}

.stat-value.running { color: #28a745; }
.stat-value.stopped { color: #dc3545; }
.stat-value.completed { color: #17a2b8; }
.stat-value.healthy { color: #28a745; }

.stat-label {
  font-size: 12px;
  color: #7f8c8d;
  text-transform: uppercase;
}

.monitor-sections {
  display: grid;
  gap: 30px;
  margin-bottom: 30px;
}

.monitor-section {
  background: white;
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.monitor-section h3 {
  margin: 0 0 20px 0;
  color: #2c3e50;
  font-size: 20px;
  border-bottom: 2px solid #ecf0f1;
  padding-bottom: 10px;
}

.service-details {
  display: grid;
  gap: 15px;
}

.service-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #dee2e6;
}

.service-item:hover {
  background: #e9ecef;
}

.service-info {
  flex: 1;
}

.service-name {
  font-weight: bold;
  color: #2c3e50;
  margin-bottom: 5px;
}

.service-meta {
  display: flex;
  gap: 15px;
  font-size: 12px;
  color: #6c757d;
}

.service-status {
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: bold;
  text-transform: uppercase;
}

.status-running { background: #d4edda; color: #155724; }
.status-stopped { background: #f8d7da; color: #721c24; }
.status-error { background: #f8d7da; color: #721c24; }
.status-starting { background: #fff3cd; color: #856404; }
.status-stopping { background: #fff3cd; color: #856404; }

.service-error {
  color: #dc3545;
  font-size: 12px;
  margin-top: 5px;
}

.workflow-history {
  display: grid;
  gap: 10px;
}

.workflow-item {
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  border-left: 3px solid #dee2e6;
}

.workflow-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.workflow-name {
  font-weight: bold;
  color: #2c3e50;
}

.workflow-status {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: bold;
}

.workflow-details {
  display: flex;
  gap: 15px;
  font-size: 12px;
  color: #6c757d;
}

.resource-usage {
  display: grid;
  gap: 20px;
}

.resource-item {
  display: grid;
  grid-template-columns: 1fr 2fr 80px;
  align-items: center;
  gap: 15px;
}

.resource-label {
  font-weight: bold;
  color: #2c3e50;
}

.resource-bar {
  height: 20px;
  background: #e9ecef;
  border-radius: 10px;
  overflow: hidden;
}

.resource-fill {
  height: 100%;
  background: linear-gradient(90deg, #28a745, #20c997);
  transition: width 0.3s ease;
}

.resource-value {
  font-weight: bold;
  color: #2c3e50;
  text-align: right;
}

.log-container {
  border: 1px solid #e9ecef;
  border-radius: 8px;
  overflow: hidden;
}

.log-controls {
  display: flex;
  gap: 10px;
  padding: 15px;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
}

.log-viewer {
  height: 300px;
  overflow-y: auto;
  padding: 15px;
  background: #f8f9fa;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
}

.log-entry {
  margin-bottom: 8px;
  padding: 8px;
  border-radius: 4px;
  display: flex;
  gap: 15px;
  align-items: center;
}

.log-entry.info { background: #d1ecf1; }
.log-entry.warn { background: #fff3cd; }
.log-entry.error { background: #f8d7da; }

.log-timestamp {
  color: #6c757d;
  min-width: 150px;
}

.log-level {
  font-weight: bold;
  min-width: 60px;
  text-align: center;
}

.log-message {
  flex: 1;
}

.performance-charts {
  background: white;
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.performance-charts h3 {
  margin: 0 0 20px 0;
  color: #2c3e50;
  font-size: 20px;
  border-bottom: 2px solid #ecf0f1;
  padding-bottom: 10px;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 30px;
}

.chart-container h4 {
  margin: 0 0 15px 0;
  color: #495057;
  font-size: 16px;
}

.chart-placeholder {
  background: #f8f9fa;
  border: 2px dashed #dee2e6;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
}

.chart-message {
  color: #6c757d;
  font-size: 16px;
  margin-bottom: 20px;
}

.chart-data {
  display: grid;
  gap: 10px;
}

.chart-data-item {
  display: flex;
  justify-content: space-between;
  padding: 8px;
  background: white;
  border-radius: 4px;
}

.data-label {
  color: #495057;
  font-weight: bold;
}

.data-value {
  color: #28a745;
  font-weight: bold;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s ease;
}

.btn-primary { background: #667eea; color: white; }
.btn-success { background: #28a745; color: white; }
.btn-secondary { background: #6c757d; color: white; }
.btn-warning { background: #ffc107; color: #212529; }

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

.btn:hover:not(:disabled) {
  opacity: 0.8;
  transform: translateY(-1px);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .overview-cards {
    grid-template-columns: 1fr;
  }
  
  .charts-grid {
    grid-template-columns: 1fr;
  }
  
  .resource-item {
    grid-template-columns: 1fr;
    gap: 10px;
  }
  
  .service-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .workflow-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 5px;
  }
}
</style>
