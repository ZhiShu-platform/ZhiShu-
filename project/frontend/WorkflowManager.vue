<template>
  <div class="workflow-manager">
    <div class="header">
      <h2>MCP工作流管理系统</h2>
      <div class="header-actions">
        <button @click="refreshAll" :disabled="isRefreshing" class="btn btn-primary">
          {{ isRefreshing ? '刷新中...' : '刷新状态' }}
        </button>
        <button @click="showWorkflowModal = true" class="btn btn-success">
          启动工作流
        </button>
      </div>
    </div>

    <!-- 系统状态概览 -->
    <div class="status-overview">
      <div class="status-card">
        <h3>MCP服务状态</h3>
        <div class="status-grid">
          <div class="status-item" v-for="service in mcpServices" :key="service.name">
            <div class="service-name">{{ service.display_name }}</div>
            <div class="service-status" :class="getStatusClass(service.status)">
              {{ getStatusText(service.status) }}
            </div>
            <div class="service-actions">
              <button 
                @click="controlService(service.name, 'start')" 
                :disabled="service.status === 'running'"
                class="btn btn-sm btn-success"
              >
                启动
              </button>
              <button 
                @click="controlService(service.name, 'stop')" 
                :disabled="service.status === 'stopped'"
                class="btn btn-sm btn-danger"
              >
                停止
              </button>
              <button 
                @click="controlService(service.name, 'restart')" 
                class="btn btn-sm btn-warning"
              >
                重启
              </button>
            </div>
          </div>
        </div>
        <div class="bulk-actions">
          <button @click="startAllServices" class="btn btn-success">启动所有服务</button>
          <button @click="stopAllServices" class="btn btn-danger">停止所有服务</button>
        </div>
      </div>

      <div class="status-card">
        <h3>工作流状态</h3>
        <div class="workflow-stats">
          <div class="stat-item">
            <span class="stat-label">总工作流:</span>
            <span class="stat-value">{{ workflowStats.total }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">运行中:</span>
            <span class="stat-value running">{{ workflowStats.running }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">已完成:</span>
            <span class="stat-value completed">{{ workflowStats.completed }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">失败:</span>
            <span class="stat-value failed">{{ workflowStats.failed }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 工作流实例列表 -->
    <div class="workflow-instances">
      <h3>工作流实例</h3>
      <div class="instances-list">
        <div v-for="instance in workflowInstances" :key="instance.id" class="instance-card">
          <div class="instance-header">
            <span class="instance-name">{{ instance.workflow_name }}</span>
            <span class="instance-status" :class="getWorkflowStatusClass(instance.status)">
              {{ getWorkflowStatusText(instance.status) }}
            </span>
          </div>
          <div class="instance-details">
            <div class="detail-item">
              <span class="label">实例ID:</span>
              <span class="value">{{ instance.id.substring(0, 8) }}...</span>
            </div>
            <div class="detail-item">
              <span class="label">当前步骤:</span>
              <span class="value">{{ instance.current_step || '未开始' }}</span>
            </div>
            <div class="detail-item">
              <span class="label">开始时间:</span>
              <span class="value">{{ formatTime(instance.start_time) }}</span>
            </div>
            <div class="detail-item" v-if="instance.total_execution_time">
              <span class="label">执行时间:</span>
              <span class="value">{{ instance.total_execution_time.toFixed(2) }}s</span>
            </div>
          </div>
          <div class="instance-actions">
            <button 
              @click="viewWorkflowDetails(instance.id)" 
              class="btn btn-sm btn-info"
            >
              查看详情
            </button>
            <button 
              @click="cancelWorkflow(instance.id)" 
              :disabled="instance.status === 'completed' || instance.status === 'failed'"
              class="btn btn-sm btn-warning"
            >
              取消
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 实时监控 -->
    <div class="real-time-monitor">
      <h3>实时监控</h3>
      <div class="monitor-content">
        <div class="log-viewer">
          <div class="log-header">
            <span>系统日志</span>
            <button @click="clearLogs" class="btn btn-sm btn-secondary">清空</button>
          </div>
          <div class="log-content" ref="logContainer">
            <div v-for="log in systemLogs" :key="log.id" class="log-entry" :class="log.level">
              <span class="log-time">{{ formatTime(log.timestamp) }}</span>
              <span class="log-level">{{ log.level.toUpperCase() }}</span>
              <span class="log-message">{{ log.message }}</span>
            </div>
          </div>
        </div>
        
        <div class="websocket-status">
          <div class="ws-indicator" :class="{ connected: websocketConnected }">
            {{ websocketConnected ? 'WebSocket已连接' : 'WebSocket未连接' }}
          </div>
          <div class="active-connections">
            活跃连接: {{ activeConnections }}
          </div>
        </div>
      </div>
    </div>

    <!-- 工作流启动模态框 -->
    <div v-if="showWorkflowModal" class="modal-overlay" @click="showWorkflowModal = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>启动工作流</h3>
          <button @click="showWorkflowModal = false" class="btn-close">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>选择工作流:</label>
            <select v-model="selectedWorkflow" class="form-control">
              <option value="">请选择工作流</option>
              <option v-for="workflow in availableWorkflows" :key="workflow.name" :value="workflow.name">
                {{ workflow.description }}
              </option>
            </select>
          </div>
          
          <div v-if="selectedWorkflow" class="form-group">
            <label>工作流参数:</label>
            <div class="parameters-form">
              <div v-for="(param, key) in getWorkflowParameters(selectedWorkflow)" :key="key" class="param-input">
                <label>{{ param.description || key }}:</label>
                <input 
                  v-model="workflowParams[key]" 
                  :type="getInputType(param.type)"
                  :placeholder="param.description || key"
                  class="form-control"
                />
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="showWorkflowModal = false" class="btn btn-secondary">取消</button>
          <button @click="startWorkflow" :disabled="!selectedWorkflow" class="btn btn-success">
            启动工作流
          </button>
        </div>
      </div>
    </div>

    <!-- 工作流详情模态框 -->
    <div v-if="showDetailsModal" class="modal-overlay" @click="showDetailsModal = false">
      <div class="modal-content large" @click.stop>
        <div class="modal-header">
          <h3>工作流详情</h3>
          <button @click="showDetailsModal = false" class="btn-close">&times;</button>
        </div>
        <div class="modal-body">
          <div v-if="selectedInstance" class="workflow-details">
            <div class="workflow-info">
              <h4>{{ selectedInstance.workflow_name }}</h4>
              <p>状态: {{ getWorkflowStatusText(selectedInstance.status) }}</p>
              <p>开始时间: {{ formatTime(selectedInstance.start_time) }}</p>
              <p v-if="selectedInstance.end_time">结束时间: {{ formatTime(selectedInstance.end_time) }}</p>
            </div>
            
            <div class="workflow-steps">
              <h4>执行步骤</h4>
              <div class="steps-timeline">
                <div v-for="step in selectedInstance.steps" :key="step.id" class="step-item" :class="step.status">
                  <div class="step-header">
                    <span class="step-name">{{ step.name }}</span>
                    <span class="step-status">{{ getStepStatusText(step.status) }}</span>
                  </div>
                  <div class="step-description">{{ step.description }}</div>
                  <div v-if="step.result" class="step-result">
                    <strong>结果:</strong> {{ JSON.stringify(step.result, null, 2) }}
                  </div>
                  <div v-if="step.error" class="step-error">
                    <strong>错误:</strong> {{ step.error }}
                  </div>
                  <div v-if="step.execution_time" class="step-time">
                    执行时间: {{ step.execution_time.toFixed(2) }}s
                  </div>
                </div>
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
  name: 'WorkflowManager',
  data() {
    return {
      mcpServices: [],
      workflowInstances: [],
      workflowStats: {
        total: 0,
        running: 0,
        completed: 0,
        failed: 0
      },
      availableWorkflows: [],
      systemLogs: [],
      websocketConnected: false,
      activeConnections: 0,
      isRefreshing: false,
      showWorkflowModal: false,
      showDetailsModal: false,
      selectedWorkflow: '',
      workflowParams: {},
      selectedInstance: null,
      websocket: null
    }
  },
  
  async mounted() {
    await this.initializeData()
    this.setupWebSocket()
    this.startAutoRefresh()
  },
  
  beforeUnmount() {
    if (this.websocket) {
      this.websocket.close()
    }
    if (this.autoRefreshInterval) {
      clearInterval(this.autoRefreshInterval)
    }
  },
  
  methods: {
    async initializeData() {
      await Promise.all([
        this.fetchMCPServices(),
        this.fetchWorkflowInstances(),
        this.fetchAvailableWorkflows(),
        this.fetchSystemStatus()
      ])
    },
    
    async fetchMCPServices() {
      try {
        const response = await fetch('/api/mcp/services')
        const data = await response.json()
        this.mcpServices = data.services
      } catch (error) {
        this.addLog('ERROR', `获取MCP服务状态失败: ${error.message}`)
      }
    },
    
    async fetchWorkflowInstances() {
      try {
        const response = await fetch('/api/workflows/instances')
        const data = await response.json()
        this.workflowInstances = data.instances
        this.updateWorkflowStats()
      } catch (error) {
        this.addLog('ERROR', `获取工作流实例失败: ${error.message}`)
      }
    },
    
    async fetchAvailableWorkflows() {
      try {
        const response = await fetch('/api/workflows')
        const data = await response.json()
        this.availableWorkflows = data.workflows
      } catch (error) {
        this.addLog('ERROR', `获取可用工作流失败: ${error.message}`)
      }
    },
    
    async fetchSystemStatus() {
      try {
        const response = await fetch('/api/monitor/status')
        const data = await response.json()
        this.activeConnections = data.active_connections
      } catch (error) {
        this.addLog('ERROR', `获取系统状态失败: ${error.message}`)
      }
    },
    
    async controlService(serviceName, action) {
      try {
        const response = await fetch('/api/mcp/services/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ service_name: serviceName, action })
        })
        
        const result = await response.json()
        if (result.success) {
          this.addLog('INFO', result.message)
          await this.fetchMCPServices()
        } else {
          this.addLog('ERROR', `服务控制失败: ${result.message}`)
        }
      } catch (error) {
        this.addLog('ERROR', `服务控制请求失败: ${error.message}`)
      }
    },
    
    async startAllServices() {
      try {
        const response = await fetch('/api/mcp/services/start-all', { method: 'POST' })
        const result = await response.json()
        if (result.success) {
          this.addLog('INFO', result.message)
          await this.fetchMCPServices()
        }
      } catch (error) {
        this.addLog('ERROR', `启动所有服务失败: ${error.message}`)
      }
    },
    
    async stopAllServices() {
      try {
        const response = await fetch('/api/mcp/services/stop-all', { method: 'POST' })
        const result = await response.json()
        if (result.success) {
          this.addLog('INFO', result.message)
          await this.fetchMCPServices()
        }
      } catch (error) {
        this.addLog('ERROR', `停止所有服务失败: ${error.message}`)
      }
    },
    
    async startWorkflow() {
      try {
        const response = await fetch('/api/workflows/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            workflow_name: this.selectedWorkflow,
            parameters: this.workflowParams
          })
        })
        
        const result = await response.json()
        if (result.success) {
          this.addLog('INFO', `工作流启动成功: ${result.instance_id}`)
          this.showWorkflowModal = false
          this.selectedWorkflow = ''
          this.workflowParams = {}
          await this.fetchWorkflowInstances()
        }
      } catch (error) {
        this.addLog('ERROR', `启动工作流失败: ${error.message}`)
      }
    },
    
    async cancelWorkflow(instanceId) {
      try {
        const response = await fetch(`/api/workflows/instances/${instanceId}/cancel`, {
          method: 'POST'
        })
        
        const result = await response.json()
        if (result.success) {
          this.addLog('INFO', result.message)
          await this.fetchWorkflowInstances()
        }
      } catch (error) {
        this.addLog('ERROR', `取消工作流失败: ${error.message}`)
      }
    },
    
    async viewWorkflowDetails(instanceId) {
      try {
        const response = await fetch(`/api/workflows/instances/${instanceId}`)
        const data = await response.json()
        this.selectedInstance = data.instance
        this.showDetailsModal = true
      } catch (error) {
        this.addLog('ERROR', `获取工作流详情失败: ${error.message}`)
      }
    },
    
    setupWebSocket() {
      this.websocket = new WebSocket(`ws://${window.location.host}/ws/workflow`)
      
      this.websocket.onopen = () => {
        this.websocketConnected = true
        this.addLog('INFO', 'WebSocket连接已建立')
      }
      
      this.websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'mcp_call_result') {
            this.addLog('INFO', `MCP调用完成: ${data.data.service}.${data.data.tool}`)
          }
        } catch (error) {
          this.addLog('WARN', `WebSocket消息解析失败: ${error.message}`)
        }
      }
      
      this.websocket.onclose = () => {
        this.websocketConnected = false
        this.addLog('WARN', 'WebSocket连接已断开')
      }
      
      this.websocket.onerror = (error) => {
        this.addLog('ERROR', `WebSocket错误: ${error.message}`)
      }
    },
    
    startAutoRefresh() {
      this.autoRefreshInterval = setInterval(async () => {
        await this.fetchMCPServices()
        await this.fetchWorkflowInstances()
        await this.fetchSystemStatus()
      }, 10000) // 每10秒刷新一次
    },
    
    async refreshAll() {
      this.isRefreshing = true
      try {
        await this.initializeData()
        this.addLog('INFO', '所有数据已刷新')
      } finally {
        this.isRefreshing = false
      }
    },
    
    updateWorkflowStats() {
      this.workflowStats = {
        total: this.workflowInstances.length,
        running: this.workflowInstances.filter(i => i.status === 'running').length,
        completed: this.workflowInstances.filter(i => i.status === 'completed').length,
        failed: this.workflowInstances.filter(i => i.status === 'failed').length
      }
    },
    
    getWorkflowParameters(workflowName) {
      const workflow = this.availableWorkflows.find(w => w.name === workflowName)
      return workflow ? workflow.parameters_schema.properties : {}
    },
    
    getInputType(type) {
      const typeMap = {
        'string': 'text',
        'number': 'number',
        'boolean': 'checkbox',
        'array': 'text'
      }
      return typeMap[type] || 'text'
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
    
    getStepStatusText(status) {
      const textMap = {
        'pending': '等待中',
        'running': '执行中',
        'completed': '已完成',
        'failed': '失败',
        'cancelled': '已取消'
      }
      return textMap[status] || status
    },
    
    formatTime(timestamp) {
      if (!timestamp) return '未知'
      return new Date(timestamp).toLocaleString('zh-CN')
    },
    
    addLog(level, message) {
      const log = {
        id: Date.now(),
        timestamp: new Date().toISOString(),
        level: level.toLowerCase(),
        message
      }
      this.systemLogs.unshift(log)
      
      // 限制日志数量
      if (this.systemLogs.length > 100) {
        this.systemLogs = this.systemLogs.slice(0, 100)
      }
      
      // 自动滚动到底部
      this.$nextTick(() => {
        const container = this.$refs.logContainer
        if (container) {
          container.scrollTop = container.scrollHeight
        }
      })
    },
    
    clearLogs() {
      this.systemLogs = []
    }
  }
}
</script>

<style scoped>
.workflow-manager {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 2px solid #e0e0e0;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.status-overview {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
  margin-bottom: 30px;
}

.status-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 15px;
  margin: 20px 0;
}

.status-item {
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 15px;
  background: #f9f9f9;
}

.service-name {
  font-weight: bold;
  margin-bottom: 8px;
}

.service-status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
  margin-bottom: 10px;
  display: inline-block;
}

.status-running { background: #d4edda; color: #155724; }
.status-stopped { background: #f8d7da; color: #721c24; }
.status-error { background: #f8d7da; color: #721c24; }
.status-starting { background: #fff3cd; color: #856404; }
.status-stopping { background: #fff3cd; color: #856404; }

.service-actions {
  display: flex;
  gap: 5px;
}

.bulk-actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.workflow-stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 4px;
}

.stat-value.running { color: #28a745; font-weight: bold; }
.stat-value.completed { color: #17a2b8; font-weight: bold; }
.stat-value.failed { color: #dc3545; font-weight: bold; }

.workflow-instances {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  margin-bottom: 30px;
}

.instances-list {
  display: grid;
  gap: 15px;
}

.instance-card {
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 15px;
  background: #f9f9f9;
}

.instance-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.instance-name {
  font-weight: bold;
  font-size: 16px;
}

.instance-status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
}

.instance-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 10px;
  margin: 15px 0;
}

.detail-item {
  display: flex;
  justify-content: space-between;
}

.label {
  font-weight: bold;
  color: #666;
}

.instance-actions {
  display: flex;
  gap: 10px;
  margin-top: 15px;
}

.real-time-monitor {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.monitor-content {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
}

.log-viewer {
  border: 1px solid #e0e0e0;
  border-radius: 6px;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  background: #f8f9fa;
  border-bottom: 1px solid #e0e0e0;
  font-weight: bold;
}

.log-content {
  height: 300px;
  overflow-y: auto;
  padding: 15px;
  background: #f8f9fa;
  font-family: monospace;
  font-size: 12px;
}

.log-entry {
  margin-bottom: 8px;
  padding: 5px;
  border-radius: 3px;
}

.log-entry.info { background: #d1ecf1; }
.log-entry.warn { background: #fff3cd; }
.log-entry.error { background: #f8d7da; }

.log-time {
  color: #666;
  margin-right: 10px;
}

.log-level {
  font-weight: bold;
  margin-right: 10px;
  min-width: 50px;
  display: inline-block;
}

.websocket-status {
  text-align: center;
  padding: 20px;
}

.ws-indicator {
  padding: 10px;
  border-radius: 6px;
  margin-bottom: 15px;
  font-weight: bold;
}

.ws-indicator.connected {
  background: #d4edda;
  color: #155724;
}

.ws-indicator:not(.connected) {
  background: #f8d7da;
  color: #721c24;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  padding: 20px;
  min-width: 500px;
  max-width: 90vw;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-content.large {
  min-width: 800px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #e0e0e0;
}

.btn-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
}

.modal-body {
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

.form-control {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.parameters-form {
  display: grid;
  gap: 10px;
}

.param-input label {
  font-size: 14px;
  color: #666;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding-top: 15px;
  border-top: 1px solid #e0e0e0;
}

.workflow-details {
  max-height: 600px;
  overflow-y: auto;
}

.workflow-info {
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
}

.workflow-steps {
  margin-top: 20px;
}

.steps-timeline {
  display: grid;
  gap: 15px;
}

.step-item {
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 15px;
  background: #f9f9f9;
}

.step-item.completed {
  border-color: #28a745;
  background: #d4edda;
}

.step-item.running {
  border-color: #ffc107;
  background: #fff3cd;
}

.step-item.failed {
  border-color: #dc3545;
  background: #f8d7da;
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.step-name {
  font-weight: bold;
}

.step-status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
}

.step-description {
  color: #666;
  margin-bottom: 10px;
}

.step-result, .step-error, .step-time {
  margin-top: 8px;
  padding: 8px;
  border-radius: 4px;
  font-size: 12px;
}

.step-result {
  background: #d1ecf1;
  border: 1px solid #bee5eb;
}

.step-error {
  background: #f8d7da;
  border: 1px solid #f5c6cb;
}

.step-time {
  background: #e2e3e5;
  border: 1px solid #d6d8db;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s;
}

.btn-primary { background: #007bff; color: white; }
.btn-success { background: #28a745; color: white; }
.btn-danger { background: #dc3545; color: white; }
.btn-warning { background: #ffc107; color: #212529; }
.btn-info { background: #17a2b8; color: white; }
.btn-secondary { background: #6c757d; color: white; }

.btn-sm {
  padding: 4px 8px;
  font-size: 12px;
}

.btn:hover:not(:disabled) {
  opacity: 0.8;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
