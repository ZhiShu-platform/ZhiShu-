<template>
  <div class="ai-chat-panel">
    <h3>与AI分析师对话</h3>
    <div class="chat-messages" ref="chatMessagesContainer">
      <div v-for="(msg, idx) in messages" :key="idx" class="chat-msg" :class="[msg.sender, { 'error': msg.success === false }]">
        <div class="msg-header">
          <span class="sender-label">{{ msg.sender === 'ai' ? 'AI分析师' : '您' }}</span>
          <span class="timestamp" v-if="msg.timestamp">{{ msg.timestamp }}</span>
        </div>
        <div class="msg-content">
          <div class="msg-text" v-html="formatMessage(msg.text)"></div>
          <div v-if="msg.sessionInfo && msg.sessionInfo.session_id" class="session-info">
            <small>会话ID: {{ msg.sessionInfo.session_id.substring(0, 12) }}...</small>
            <small v-if="msg.sessionInfo.processing_time_ms"> | 处理时间: {{ msg.sessionInfo.processing_time_ms }}ms</small>
          </div>
          <div v-if="msg.processingDetails && msg.processingDetails.processing_steps" class="processing-summary">
            <small>🔄 执行了 {{ msg.processingDetails.processing_steps }} 个处理步骤</small>
            <small v-if="msg.processingDetails.mcp_calls && msg.processingDetails.mcp_calls.length > 0">
              | 🔬 调用了 {{ msg.processingDetails.mcp_calls.reduce((sum, call) => sum + call.total_calls, 0) }} 个外部模型
            </small>
          </div>
        </div>
      </div>
      <div v-if="isTyping" class="chat-msg ai">
        <div class="msg-header">
          <span class="sender-label">AI分析师</span>
        </div>
        <div class="msg-content">
          <span class="typing-indicator">正在分析处理中...</span>
        </div>
      </div>
    </div>
    <div class="chat-input-area">
      <input
        v-model="userInput"
        @keyup.enter="sendMessage"
        placeholder="在此输入您的问题..."
        :disabled="isTyping"
      />
      <button @click="sendMessage" :disabled="!userInput.trim() || isTyping">发送</button>
      <button @click="checkHealth" class="health-btn" :disabled="isCheckingHealth">
        {{ isCheckingHealth ? '检查中...' : '系统状态' }}
      </button>
    </div>
    <div class="ai-disclaimer">
      AI生成的内容仅供参考，请结合实际情况进行决策。
    </div>
  </div>
</template>

<script>
export default {
  name: 'InteractiveAIChat',
  props: {
    selectedSubModel: Object,
    selectedRegion: String,
    drivingDatasets: Array,
  },
  data() {
    return {
      userInput: '',
      isTyping: false,
      isCheckingHealth: false,
      sessionId: null,
      userId: null,
      messages: [
        { 
          sender: 'ai', 
          text: '您好！我是智枢AI分析师。我配备了完整的应急管理处理流程，包括威胁检测、多模型分析（CLIMADA、LISFLOOD等）和智能建议生成。\n\n您可以向我提问关于灾害情况、数据分析或应急响应的任何问题。我会为您提供详细的分析过程和结果。',
          timestamp: new Date().toLocaleString('zh-CN'),
          sessionInfo: null
        }
      ],
    };
  },
  methods: {
    // 滚动条自动滚动到底部
    scrollToBottom() {
      this.$nextTick(() => {
        const container = this.$refs.chatMessagesContainer;
        if (container) {
          container.scrollTop = container.scrollHeight;
        }
      });
    },
    async sendMessage() {
      const userMessage = this.userInput.trim();
      if (!userMessage || this.isTyping) return;

      // 生成用户ID（简单实现，实际应用中应该从登录系统获取）
      if (!this.userId) {
        this.userId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
      }

      // 添加用户消息到界面
      this.messages.push({ 
        sender: 'user', 
        text: userMessage,
        timestamp: new Date().toLocaleString('zh-CN'),
        sessionInfo: null
      });
      this.userInput = '';
      this.isTyping = true;
      this.scrollToBottom();

      try {
        // 准备发送到后端的增强数据
        const requestPayload = {
          question: userMessage,
          context: {
            region: this.selectedRegion,
            model: this.selectedSubModel,
            datasets: this.drivingDatasets.map(d => ({ name: d.name, source: d.source })),
          },
          // 集成会话和用户管理
          session_id: this.sessionId,
          user_id: this.userId,
          // 额外的上下文信息
          frontend_context: {
            component: 'InteractiveAIChat',
            timestamp: new Date().toISOString(),
            browser_info: {
              user_agent: navigator.userAgent,
              language: navigator.language
            }
          }
        };

        console.log('发送请求到后端:', requestPayload);

        // 调用增强的后端 /api/chat 接口
        const response = await fetch('/api/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestPayload),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.message || errorData.reply || '与AI服务通信失败');
        }

        const data = await response.json();
        console.log('收到后端响应:', data);

        // 更新会话ID
        if (data.session_info && data.session_info.session_id) {
          this.sessionId = data.session_info.session_id;
        }

        // 构建AI回复消息，包含丰富的信息
        const aiMessage = {
          sender: 'ai',
          text: data.reply,
          timestamp: new Date().toLocaleString('zh-CN'),
          sessionInfo: data.session_info,
          processingDetails: data.processing_details,
          success: data.success
        };

        this.messages.push(aiMessage);

        // 如果有处理详情，在控制台显示（用于调试）
        if (data.processing_details) {
          console.log('处理详情:', data.processing_details);
        }

      } catch (error) {
        console.error('AI Chat Error:', error);
        
        // 添加详细的错误信息
        const errorMessage = {
          sender: 'ai',
          text: `抱歉，我在处理您的请求时遇到了问题。\n\n错误详情：${error.message}\n\n请稍后重试，或者尝试重新描述您的问题。如果问题持续存在，请联系技术支持。`,
          timestamp: new Date().toLocaleString('zh-CN'),
          sessionInfo: { error: true, session_id: this.sessionId, user_id: this.userId },
          success: false
        };
        
        this.messages.push(errorMessage);
      } finally {
        this.isTyping = false;
        this.scrollToBottom();
      }
    },

    async checkHealth() {
      this.isCheckingHealth = true;
      
      try {
        const response = await fetch('/api/langgraph/health', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          }
        });

        const data = await response.json();
        
        if (data.success) {
          this.messages.push({ 
            sender: 'ai', 
            text: `**系统状态检查结果:**\n✅ LangGraph应急管理系统运行正常\n\n**详细信息:**\n${JSON.stringify(data.langgraph_status, null, 2)}` 
          });
        } else {
          this.messages.push({ 
            sender: 'ai', 
            text: `**系统状态检查结果:**\n❌ LangGraph应急管理系统连接失败\n\n**错误信息:** ${data.message}` 
          });
        }
      } catch (error) {
        console.error('Health Check Error:', error);
        this.messages.push({ 
          sender: 'ai', 
          text: `**系统状态检查结果:**\n❌ 无法连接到LangGraph应急管理系统\n\n**错误信息:** ${error.message}` 
        });
      } finally {
        this.isCheckingHealth = false;
        this.scrollToBottom();
      }
    },

    // 格式化消息文本，支持换行和简单的markdown
    formatMessage(text) {
      if (!text) return '';
      
      return text
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code>$1</code>')
        .replace(/^- (.*?)$/gm, '• $1')
        .replace(/^• (.*?)$/gm, '<li style="margin-left: 20px;">$1</li>');
    }
  },
};
</script>

<style scoped>
/* 样式保持不变 */
.ai-chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #f8f9fa;
  border: 1px solid #e0e6ed;
  border-radius: 8px;
  padding: 16px;
}
h3 {
  margin: 0 0 16px 0;
  color: #2C7BE5;
  border-bottom: 1px solid #e0e6ed;
  padding-bottom: 8px;
}
.chat-messages {
  flex-grow: 1;
  overflow-y: auto;
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.chat-msg {
  padding: 12px 16px;
  border-radius: 8px;
  max-width: 85%;
  line-height: 1.6;
  word-wrap: break-word;
  margin-bottom: 4px;
}
.chat-msg.user {
  background-color: #2C7BE5;
  color: white;
  align-self: flex-end;
}
.chat-msg.ai {
  background-color: #fff;
  border: 1px solid #e0e6ed;
  align-self: flex-start;
}
.chat-msg.error {
  background-color: #fff5f5;
  border-color: #feb2b2;
}
.msg-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.sender-label {
  font-weight: bold;
  font-size: 14px;
}
.timestamp {
  font-size: 11px;
  opacity: 0.7;
  font-style: italic;
}
.msg-content {
  line-height: 1.6;
}
.msg-text {
  white-space: normal;
  word-break: break-word;
}
.session-info, .processing-summary {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid rgba(0,0,0,0.1);
  color: rgba(0,0,0,0.6);
  font-size: 11px;
}
.chat-msg.user .session-info, 
.chat-msg.user .processing-summary {
  border-top-color: rgba(255,255,255,0.3);
  color: rgba(255,255,255,0.8);
}
.msg-text code {
  background-color: rgba(0,0,0,0.1);
  padding: 2px 4px;
  border-radius: 3px;
  font-family: monospace;
}
.chat-msg.user .msg-text code {
  background-color: rgba(255,255,255,0.2);
}
.typing-indicator {
    display: inline-block;
    animation: typing 1s infinite;
}
@keyframes typing {
    0% { content: "."; }
    33% { content: ".."; }
    66% { content: "..."; }
}
.chat-input-area {
  display: flex;
  gap: 8px;
}
.chat-input-area input {
  flex-grow: 1;
  border: 1px solid #ced4da;
  border-radius: 4px;
  padding: 8px 12px;
  font-size: 14px;
}
.chat-input-area button {
  background-color: #2C7BE5;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 8px 16px;
  cursor: pointer;
  transition: background-color .2s;
}
.chat-input-area button:hover {
  background-color: #185fa3;
}
.chat-input-area button:disabled {
  background-color: #a0b3d1;
  cursor: not-allowed;
}
.health-btn {
  background-color: #28a745 !important;
  margin-left: 8px;
}
.health-btn:hover {
  background-color: #218838 !important;
}
.health-btn:disabled {
  background-color: #6c757d !important;
}
.ai-disclaimer {
  font-size: 11px;
  color: #888;
  margin-top: 12px;
  text-align: center;
}
</style>