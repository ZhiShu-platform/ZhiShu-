<script>
export default {
  props: {
    agencies: {
      type: Array,
      required: true
    }
  },
  emits: ['generate-report', 'contact-agency'],
  data() {
    return {
      chatMessages: [
        { sender: 'ai', text: '这里是智枢AI智能体。我正在实时监测灾害情况，已发现3个高风险区域需要立即关注。请点击相关部门获取我生成的应急方案。' }
      ],
      isGeneratingPlan: false,
    }
  },
  methods: {
    handleAgencyClick(agency) {
      this.$emit('contact-agency', agency);
      this.isGeneratingPlan = true;
      
      // Simulate plan generation delay
      setTimeout(() => {
        let plan = '';
        switch (agency.name) {
          case '消防部门':
            plan = '【消防部门应急方案】\n1. 立即调派救援队伍前往受灾最严重区域。\n2. 加强对12,500英亩火场的分区扑救，优先保护威胁人口约8,700人区域。\n3. 协调疏散3,200人，确保疏散路线畅通。';
            break;
          case '气象部门':
            plan = '【气象部门应急方案】\n1. 实时监测火势蔓延速度（5.2公里/小时），发布高温干燥及风力预警。\n2. 向相关部门推送气象数据，辅助救援决策。';
            break;
          case '医疗部门':
            plan = '【医疗部门应急方案】\n1. 在受影响区域设立临时医疗点，优先救治伤员。\n2. 准备应对大规模人员疏散带来的医疗需求。';
            break;
          case '民政部门':
            plan = '【民政部门应急方案】\n1. 协调安置疏散的3,200人，保障基本生活物资供应。\n2. 开展受灾人口登记和心理疏导。';
            break;
          default:
            plan = 'AI正在为该部门生成专属应急方案...';
        }
        this.chatMessages.push({ sender: 'ai', text: plan });
        this.isGeneratingPlan = false;
      }, 1500);
    }
  }
}
</script>

<template>
  <section>
    <h2>应急决策辅助</h2>
    <div class="decision-tools">
      <div class="report-generator">
        <h2>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M14 2H6C4.9 2 4 2.9 4 4V20C4 21.1 4.9 22 6 22H18C19.1 22 20 21.1 20 20V8L14 2ZM18 20H6V4H13V9H18V20ZM8 15H16V17H8V15ZM8 11H16V13H8V11ZM8 7H13V9H8V7Z" fill="#FF3B30"/>
          </svg>
          一键生成灾害报告
        </h2>
        <div class="report-preview">
          <h4>加州北部火灾简报</h4>
          <ul>
            <li>火势蔓延速度: 每小时5.2公里</li>
            <li>受影响面积: 12,500英亩</li>
            <li>威胁人口: 约8,700人</li>
            <li>已疏散人数: 3,200人</li>
            <li>风险等级: 极高 (红色预警)</li>
          </ul>
        </div>
        <button class="generate-btn" @click="$emit('generate-report')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M17 3H5C3.9 3 3 3.9 3 5V19C3 20.1 3.9 21 5 21H19C20.1 21 21 20.1 21 19V7L17 3ZM19 19H5V5H16.17L19 7.83V19ZM12 12C10.34 12 9 13.34 9 15C9 16.66 10.34 18 12 18C13.66 18 15 16.66 15 15C15 13.34 13.66 12 12 12ZM6 6H15V10H6V6Z" fill="white"/>
          </svg>
          生成完整报告
        </button>
      </div>
      <div class="agency-panel" style="display: flex; flex-direction: row; gap: 24px; align-items: flex-start;">
        <div class="agency-grid" style="flex: 1; min-width: 0; max-width: 260px;">
          <h3 style="margin-top:0;">AI智能体协同作战室</h3>
          
          <div>
            <div v-for="agency in agencies" :key="agency.name" 
                 class="agency-card"
                 @click="handleAgencyClick(agency)"
                 style="margin-bottom: 16px; cursor: pointer; display: flex; align-items: center; gap: 8px; border: 1px solid #eee; border-radius: 6px; padding: 14px 16px; background: #fff; transition: all .2s; font-size: 16px;">
              <div class="agency-icon" v-html="agency.icon"></div>
              <div class="agency-name">{{ agency.name }}</div>
            </div>
          </div>
        </div>
        <div class="ai-emergency-plan" style="flex: 2; min-width: 0; border:1px solid #eee; border-radius:8px; padding:20px; background:#fafbfc;">
          <h4 style="margin: 0 0 12px 0;">AI智能应急方案</h4>
          <div class="chat-messages" style="max-height:300px; overflow-y:auto; margin-bottom:12px;">
            <div v-for="(msg, idx) in chatMessages" :key="idx" :class="['chat-msg', msg.sender]" style="margin-bottom:12px; white-space:pre-line;">
              <span v-if="msg.sender==='ai'" style="color:#FF3B30;font-weight:bold;">智枢AI：</span>
              <span v-else style="color:#2C7BE5;font-weight:bold;">我：</span>
              <span>{{ msg.text }}</span>
            </div>
            <div v-if="isGeneratingPlan" class="chat-msg ai">
                <span style="color:#FF3B30;font-weight:bold;">智枢AI：</span>
                <span>正在生成方案...</span>
            </div>
          </div>
          <div class="ai-plan-footer">
            Powered by LangGraph Multi-Agent Analysis Engine
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.tech-label {
    font-size: 12px;
    color: #888;
    background-color: #f0f0f0;
    padding: 2px 6px;
    border-radius: 4px;
    display: inline-block;
    margin-top: -8px;
    margin-bottom: 16px;
}
.agency-card:hover {
    transform: translateX(4px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}
.ai-plan-footer {
    text-align: right;
    font-size: 11px;
    color: #aaa;
    margin-top: 12px;
    font-style: italic;
}
/* Other styles remain unchanged */
.decision-tools {
    display: grid;
    grid-template-columns: 320px 1fr;
    gap: 24px;
}
</style>
