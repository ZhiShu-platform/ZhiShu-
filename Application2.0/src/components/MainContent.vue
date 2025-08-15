<script>
import DisasterModelSelector from './DisasterModelSelector.vue'
import WildfireDashboard from './WildfireDashboard.vue'
import MapPlaceholder from './GeoServerMap.vue' 
import InteractiveAIChat from './InteractiveAIChat.vue'

export default {
  name: 'MainContent',
  components: {
    DisasterModelSelector,
    WildfireDashboard,
    MapPlaceholder,
    InteractiveAIChat
  },
  props: {
    isLoggedIn: Boolean,
    username: String,
  },
  data() {
    return {
      selectedRegion: null,
      isChatOpen: false, 
      
      disasterModels: [
          { id: 1, name: '野火模型', description: '全球野火监测与预测', featured: true, icon: `<svg viewBox="0 0 100 100"><path d="M50 95C50 95 30 75 30 55C30 35 50 25 50 25C50 25 70 35 70 55C70 75 50 95 50 95ZM50 45C50 45 55 50 55 60C55 70 50 75 50 75C50 75 45 70 45 60C45 50 50 45 50 45Z" fill="#FF9F0A" stroke="#FF453A" stroke-width="3"></path></svg>` },
          { id: 2, name: '地震模型', description: '地震灾害评估与余震预测', featured: false, icon: `<svg viewBox="0 0 100 100"><polyline points="10,50 25,40 35,60 45,30 55,70 65,45 75,55 90,50" fill="none" stroke="#2C7BE5" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"></polyline></svg>` },
          { id: 3, name: '洪水模型', description: '洪水淹没范围与风险评估', featured: false, icon: `<svg viewBox="0 0 100 100"><path d="M10 70 Q 30 50, 50 70 T 90 70 V 90 H 10 Z" fill="#30D158" opacity="0.6"></path><path d="M15 60 Q 35 40, 55 60 T 95 60" fill="none" stroke="#2C7BE5" stroke-width="3"></path></svg>` },
          { id: 4, name: '气象模型', description: '全球气象监测', featured: false, icon: `<svg viewBox="0 0 100 100"><path d="M50,50 m-40,0 a40,40 0 1,0 80,0 a40,40 0 1,0 -80,0" fill="none" stroke="#AF52DE" stroke-width="3"></path><path d="M50,50 m-20,0 a20,20 0 1,0 40,0 a20,20 0 1,0 -40,0" fill="#AF52DE" opacity="0.4"></path></svg>` },
      ],
      specificModels: {
        1: [{ id: 'wf-a', name: 'Cell2Fire' }, { id: 'wf-b', name: 'Climada' }, { id: 'wf-d', name: 'NFDRS4' }],
        2: [{ id: 'eq-a', name: '地震A' }, { id: 'eq-b', name: '地震B' }],
        3: [{ id: 'fl-a', name: 'Lisflood' }, { id: 'fl-b', name: '洪水B' }],
        4: [{ id: 'hu-a', name: 'Aurora' }]
      },
      datasets: [
          { id: 'ds-01', name: 'MODIS 动态火点数据', disasterTypes: ['野火'], description: '来自MODIS传感器的全球热异常数据，对近实时火点监测至关重要。', source: 'NASA FIRMS', updateFrequency: '每3小时', poweredModels: ['wf-a', 'wf-b'] },
          { id: 'ds-02', name: 'USGS ShakeMap', disasterTypes: ['地震'], description: '在重大地震后提供近实时的地面运动和震动强度图。', source: 'USGS', updateFrequency: '事件驱动', poweredModels: ['eq-a', 'eq-b'] },
          { id: 'ds-04', name: 'OpenStreetMap 建筑物', disasterTypes: ['通用'], description: '全球众包的建筑物轮廓数据，是暴露度分析的核心基础。', source: 'OpenStreetMap', updateFrequency: '持续更新', poweredModels: ['eq-b', 'fl-a', 'hu-a'] },
          { id: 'ds-06', name: '全球预报系统 (GFS)', disasterTypes: ['野火', '洪水', '飓风'], description: '全球数值天气预报模型，提供风、温、压等关键气象变量。', source: 'NOAA', updateFrequency: '每6小时', poweredModels: ['wf-a', 'fl-a', 'hu-a'] },
      ],
      
      selectedMainModelId: null,
      selectedSubModel: null,
      analysisMode: null,
      currentHurricaneLayer: null,
    }
  },
  computed: {
    showDashboard() {
      if (!this.isLoggedIn || !this.selectedRegion) return false;

      // 飓风模型 (id: 4) 的显示逻辑
      if (this.selectedMainModelId === 4) {
        // 必须选择了分析模式和具体图层
        return !!(this.analysisMode && this.currentHurricaneLayer);
      }

      // 其他模型的显示逻辑
      if (this.analysisMode === 'multi') return true;
      if (this.analysisMode === 'single' && this.selectedSubModel) return true;
      
      return false;
    },
    drivingDatasets() {
      if (!this.datasets) return [];
      
      if (this.selectedMainModelId === 4) {
        const relevantTypes = ['飓风', '通用'];
        return this.datasets.filter(d => d.disasterTypes.some(type => relevantTypes.includes(type)));
      }

      if (!this.selectedSubModel) return [];
      const modelId = this.selectedSubModel.id;
      if (modelId === 'multi-analysis') {
        const relevantTypes = ['野火', '通用'];
        return this.datasets.filter(d => d.disasterTypes.some(type => relevantTypes.includes(type)));
      }
      return this.datasets.filter(d => d.poweredModels && d.poweredModels.includes(modelId));
    }
  },
  methods: {
    handleRegionSelect(regionName) {
      this.selectedRegion = regionName;
      this.selectedMainModelId = null;
      this.selectedSubModel = null;
      this.analysisMode = null;
      this.isChatOpen = false;
      this.currentHurricaneLayer = null;
    },
    handleSelectModel(model) {
      this.selectedMainModelId = model.id;
      this.selectedSubModel = null;
      this.analysisMode = null;
      this.isChatOpen = false;
      this.currentHurricaneLayer = null;
    },
    // --- 逻辑修正 ---
    handleSelectAnalysisMode(mode) {
      this.analysisMode = mode;
      
      // 对于非飓风模型，当选择“多模型分析”时，这是一个最终步骤，直接触发分析
      if (mode === 'multi' && this.selectedMainModelId !== 4) {
        this.selectedSubModel = { id: 'multi-analysis', name: '多模型综合分析' };
        this.handleStartAnalysis();
      }
    },
    // --- 逻辑修正 ---
    handleSelectSubModel(subModel) {
      this.selectedSubModel = subModel;
      this.handleStartAnalysis();
    },
    // --- 逻辑修正 ---
    handleLayerSelected(layerInfo) {
        this.currentHurricaneLayer = layerInfo;
        // 选择了具体图层是飓风模型的最后一步，触发分析
        if (layerInfo) {
          this.handleStartAnalysis();
        }
    },
    // --- 逻辑修正 ---
    handleStartAnalysis() {
       if (!this.isLoggedIn) {
        this.$emit('show-login');
        return;
      }
      this.isChatOpen = false;
      // 使用 $nextTick 确保 DOM 更新（v-if="showDashboard" 生效）后才滚动
      this.$nextTick(() => {
        const dashboard = document.querySelector('.dashboard-container');
        if (dashboard) {
          dashboard.scrollIntoView({ behavior: 'smooth' });
        }
      });
    },
    openChatWindow() {
        this.isChatOpen = true;
    },
    closeChatWindow() {
        this.isChatOpen = false;
    }
  }
}
</script>

<template>
  <div class="main-content-layout">
    <div class="map-panel">
      <MapPlaceholder 
        @region-selected="handleRegionSelect"
        :title="selectedRegion ? `当前分析区域: ${selectedRegion}` : '第一步：请在地图上选择分析区域'"
        :hurricaneLayer="currentHurricaneLayer"
      />
      
      <div v-if="showDashboard" class="dashboard-container">
        <div v-if="isChatOpen" class="chat-view-container">
          <InteractiveAIChat
              :selectedSubModel="selectedSubModel"
              :selectedRegion="selectedRegion"
              :drivingDatasets="drivingDatasets"
          />
          <button class="close-chat-btn" @click="closeChatWindow">返回分析仪表盘</button>
        </div>
        <WildfireDashboard 
            v-else
            :selectedModel="disasterModels.find(m => m.id === selectedMainModelId)"
            :selectedSubModel="selectedSubModel"
            :analysisMode="analysisMode"
            :selectedRegion="selectedRegion"
            :all-datasets="datasets"
            :selectedHurricaneLayer="currentHurricaneLayer"
            @open-chat="openChatWindow"
        />
      </div>
    </div>

    <div class="control-panel">
      <div v-if="!selectedRegion" class="control-panel-placeholder">
        <h2>分析控制台</h2>
        <p>请首先在左侧地图上选择一个区域以开始分析。</p>
      </div>
      
      <div v-else class="control-panel-content">
        <h2>分析设置：{{ selectedRegion }}</h2>
        <DisasterModelSelector 
          :models="disasterModels" 
          :specificModels="specificModels"
          :selectedMainModelId="selectedMainModelId"
          @select-model="handleSelectModel" 
          @select-analysis-mode="handleSelectAnalysisMode"
          @select-sub-model="handleSelectSubModel"
          @layer-selected="handleLayerSelected"
        />
      </div>

       <div v-if="selectedMainModelId && !isLoggedIn" class="login-prompt">
          <h3>请登录以运行模型分析</h3>
          <p>登录后即可访问完整的灾害数据分析、AI洞察和应急方案。</p>
          <button @click="$emit('show-login')">立即登录</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.main-content-layout {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
  height: calc(100vh - 64px - 48px);
  padding: 0;
}

.map-panel {
  display: flex;
  flex-direction: column;
  gap: 24px;
  overflow-y: auto;
  padding: 12px;
}

.control-panel {
  background-color: #fff;
  border-left: 1px solid #e0e6ed;
  padding: 24px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.control-panel-placeholder {
  text-align: center;
  margin: auto;
  color: #6c757d;
}
.control-panel-placeholder h2 {
  color: #2C7BE5;
}

.login-prompt {
  text-align: center; 
  padding: 40px 20px; 
  background: #fff3f3; 
  border: 1px solid #dc3545;
  border-radius: 8px; 
  margin-top: 20px;
}
.login-prompt h3 {
  color: #a71d2a;
}
.login-prompt button {
  padding: 10px 20px; 
  font-size: 16px; 
  margin-top: 10px; 
  background: #2C7BE5; 
  color: #fff; 
  border: none; 
  border-radius: 4px; 
  cursor: pointer;
}

.chat-view-container {
    background-color: #f8f9fa;
    border: 1px solid #e0e6ed;
    border-radius: 8px;
    padding: 24px;
    display: flex;
    flex-direction: column;
    height: 100%;
}
.chat-view-container > .ai-chat-panel {
  height: auto;
  flex-grow: 1;
}
.close-chat-btn {
    margin-top: 16px;
    padding: 8px 20px;
    align-self: center;
    background-color: #6c757d;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color .2s;
}
.close-chat-btn:hover {
    background-color: #5a6268;
}
</style>
