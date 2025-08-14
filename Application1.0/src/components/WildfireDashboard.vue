<script>
import { defineComponent } from 'vue'
import { Pie, Bar } from 'vue-chartjs'
import { Chart, ArcElement, Tooltip, Legend, BarElement, CategoryScale, LinearScale } from 'chart.js'

Chart.register(ArcElement, Tooltip, Legend, BarElement, CategoryScale, LinearScale)

export default defineComponent({
  name: 'WildfireDashboard',
  components: { Pie, Bar },
  props: {
    selectedModel: Object,
    selectedSubModel: Object,
    analysisMode: String,
    selectedRegion: String,
    allDatasets: Array,
    // --- 步骤 1: 添加新 prop 以接收飓风图层信息 ---
    selectedHurricaneLayer: Object,
  },
  emits: ['open-chat'],
  data() {
    return {
      isLoading: true,
      loadingText: '',
      lossData: {
        labels: ['建筑损坏', '基础设施', '农业损失', '商业中断'],
        datasets: [{ data: [0,0,0,0] }]
      },
      insuranceComparisonData: {
        labels: ['本平台预估', '瑞士再保险', '慕尼黑再保险', 'Aon集团'],
        datasets: [{ data: [0,0,0,0] }]
      },
      pieChartOptions: { responsive: true, maintainAspectRatio: false },
      barChartOptions: { responsive: true, maintainAspectRatio: false, indexAxis: 'y' },
    }
  },
  computed: {
    drivingDatasets() {
      if (!this.allDatasets) return [];
      
      // 如果是飓风模型
      if (this.selectedModel && this.selectedModel.id === 4) {
        const relevantTypes = ['飓风', '通用'];
        return this.allDatasets.filter(d => d.disasterTypes.some(type => relevantTypes.includes(type)));
      }

      // 如果是其他模型
      if (!this.selectedSubModel) return [];
      const modelId = this.selectedSubModel.id;
      if (modelId === 'multi-analysis') {
        const relevantTypes = ['野火', '通用'];
        return this.allDatasets.filter(d => d.disasterTypes.some(type => relevantTypes.includes(type)));
      }
      return this.allDatasets.filter(d => d.poweredModels && d.poweredModels.includes(modelId));
    },
    // --- 步骤 2: 创建计算属性以确定要显示的上下文标题 ---
    contextTitle() {
      if (this.selectedModel && this.selectedModel.id === 4) {
        // 对于飓风模型，我们显示主模型名称和具体图层名称
        if (this.selectedHurricaneLayer) {
            return `${this.selectedModel.name} - ${this.selectedHurricaneLayer.name}`;
        }
        return this.selectedModel.name;
      }
      if (this.selectedSubModel) {
        return this.selectedSubModel.name; // e.g., "野火A (Cell2Fire)"
      }
      return '未知模型';
    },
    // --- 步骤 3.1: 创建一个综合的触发器 ---
    // 这个计算属性是关键。它将“选择子模型”和“选择飓风图层”这两个不同的用户操作
    // 统一成一个单一的、可被监听的“分析触发”信号。
    analysisTrigger() {
      // 如果当前是飓风模型，那么触发器就是被选中的图层
      if (this.selectedModel && this.selectedModel.id === 4) {
        return this.selectedHurricaneLayer;
      }
      // 否则，触发器就是被选中的子模型
      return this.selectedSubModel;
    }
  },
  watch: {
    // --- 步骤 3: 监听这个统一的触发器 ---
    // 当 analysisTrigger 的值发生变化时（即用户完成了最终选择），就调用 startAnalysis 方法。
    analysisTrigger: {
      immediate: true, // 立即执行一次，以处理初始加载
      handler(newTriggerValue) {
        // 只有当触发器有有效值时才开始分析
        if (newTriggerValue) {
          this.startAnalysis(newTriggerValue);
        }
      }
    }
  },
  methods: {
    startAnalysis(trigger) {
      this.isLoading = true;
      let triggerName = '分析';
      
      // 根据触发器的类型（是图层还是子模型）来设置加载文本
      if (this.selectedModel && this.selectedModel.id === 4) {
        triggerName = `飓风图层 (${trigger.name})`;
      } else {
        triggerName = trigger.name;
      }

      this.loadingText = `正在调用 ${triggerName} 模型分析 ${this.selectedRegion} 地区...`;

      // 模拟分析过程
      setTimeout(() => {
        this.isLoading = false;
        this.updateChartData();
      }, 1500);
    },
    updateChartData() {
        // 模拟生成随机图表数据
        this.lossData = {
            labels: ['建筑损坏', '基础设施', '农业损失', '商业中断'],
            datasets: [{
                backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0'],
                data: [45, 25, 15, 15].map(v => Math.max(0, v + (Math.random() - 0.5) * 10))
            }]
        };
        this.insuranceComparisonData = {
            labels: ['本平台预估', '瑞士再保险', '慕尼黑再保险', 'Aon集团'],
            datasets: [{
                label: '预估经济损失 (百万美元)',
                backgroundColor: ['#30D158', '#FF9F0A', '#FFCD56', '#4BC0C0'],
                data: [1250, 1500, 1350, 1420].map(v => Math.max(0, v + (Math.random() - 0.5) * 200))
            }]
        };
    }
  },
})
</script>

<template>
  <div class="wildfire-dashboard">
    <!-- 加载遮罩层 -->
    <div v-if="isLoading" class="loading-overlay">
        <div class="loading-spinner"></div>
        <p>{{ loadingText }}</p>
    </div>
    
    <!-- 分析结果仪表盘 -->
    <div v-else class="dashboard-grid">
      <!-- 左上：分析上下文面板 -->
      <div class="grid-item context-panel">
        <h3>分析上下文</h3>
        <div class="context-section">
          <!-- 步骤 4: 更新模板以动态显示上下文 -->
          <h4>核心模型/图层</h4>
          <p><strong>{{ contextTitle }}</strong></p>
          <p v-if="selectedModel" class="model-description">{{ selectedModel.description }}</p>
          <!-- 如果是飓风模型，额外显示分析层次信息 -->
          <p v-if="selectedHurricaneLayer">分析层次: {{ selectedHurricaneLayer.level === 'ground' ? '地面' : '大气' }}</p>
        </div>
        <div class="context-section">
          <h4>驱动数据集</h4>
          <ul v-if="drivingDatasets.length > 0" class="dataset-list">
            <li v-for="dataset in drivingDatasets" :key="dataset.id">
              <strong>{{ dataset.name }}</strong> (来源: {{ dataset.source }})
            </li>
          </ul>
          <p v-else>无特定数据集信息。</p>
        </div>
      </div>

      <!-- 右上：AI对话入口 -->
      <div class="grid-item ai-chat-prompt">
        <h3>AI协同分析</h3>
        <p>需要更深入的解读或定制化方案？</p>
        <button class="chat-button" @click="$emit('open-chat')">与AI分析师对话</button>
      </div>

      <!-- 下方：图表容器 -->
      <div class="grid-item-span-2">
          <div class="charts-container">
              <div class="chart-card">
                  <h3>灾损评估</h3>
                  <div class="chart-wrapper">
                      <Pie :data="lossData" :options="pieChartOptions" />
                  </div>
              </div>
              <div class.markdown-body>
                  <h3>保险评估对比</h3>
                  <div class="chart-wrapper">
                      <Bar :data="insuranceComparisonData" :options="barChartOptions" />
                  </div>
              </div>
          </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.wildfire-dashboard { position: relative; width: 100%; min-height: 400px; }
.loading-overlay { 
  position: absolute;
  inset: 0;
  background-color: rgba(255,255,255,0.8);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 10;
  border-radius: 8px;
  transition: opacity 0.3s ease;
}
.loading-spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
.dashboard-grid {
    display: grid;
    grid-template-columns: 1fr 1.2fr;
    grid-template-rows: auto auto;
    gap: 24px;
    animation: fadeIn 0.5s ease-in-out;
}
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
.grid-item {
    background-color: #fff;
    border: 1px solid #e0e6ed;
    border-radius: 8px;
    padding: 20px;
    display: flex;
    flex-direction: column;
}
.grid-item-span-2 {
    grid-column: span 2;
}
.charts-container {
    display: grid;
    grid-template-columns: 1fr 1.5fr;
    gap: 24px;
}
.chart-card {
    padding: 16px;
    display: flex;
    flex-direction: column;
}
.chart-wrapper {
    position: relative;
    flex-grow: 1;
    min-height: 250px;
}
h3 {
    margin: 0 0 16px 0;
    color: #2C7BE5;
    border-bottom: 1px solid #e0e6ed;
    padding-bottom: 8px;
}
.context-panel .context-section {
  margin-bottom: 16px;
}
.context-panel .context-section:last-child {
  margin-bottom: 0;
}
.context-panel h4 {
  font-size: 16px;
  font-weight: 500;
  margin: 0 0 8px 0;
  color: #333;
}
.model-description {
  font-size: 14px;
  color: #555;
  margin: 4px 0 0 0;
}
.dataset-list {
  padding-left: 20px;
  margin: 0;
  font-size: 14px;
}
.dataset-list li {
  margin-bottom: 6px;
}
.ai-chat-prompt {
    justify-content: center;
    align-items: center;
    text-align: center;
    background-color: #f8faff;
}
.ai-chat-prompt p {
    color: #555;
    margin-bottom: 16px;
}
.chat-button {
    background-color: #2C7BE5;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 12px 24px;
    font-size: 16px;
    font-weight: 500;
    cursor: pointer;
    transition: all .2s;
}
.chat-button:hover {
    background-color: #185fa3;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(44,123,229,0.2);
}
</style>
