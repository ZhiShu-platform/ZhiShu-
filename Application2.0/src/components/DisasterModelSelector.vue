<script>
export default {
  props: {
    models: {
      type: Array,
      required: true
    },
    specificModels: {
      type: Object,
      required: true
    },
    selectedMainModelId: {
      type: [Number, null],
      required: false
    }
  },
  emits: ['select-model', 'select-sub-model', 'select-analysis-mode', 'layer-selected'],
  data() {
    return {
      selectedSubModelId: null,
      selectedAnalysisMode: null,
      selectedLevel: null, 
      selectedLayer: null, 
      // --- 步骤 1: 将单一图层列表拆分为两个 ---
      groundLayers: [
        { id: '10u_pred', name: '距地面10m西东风速', style: 'hurricane_map:hurricane_surface_10u' },
        { id: '10v_pred', name: '距地面10m南北风速', style: 'hurricane_map:hurricane_surface_10v' },
        { id: '2t_pred', name: '距地面2m空气温度', style: 'hurricane_map:hurricane_surface_2t' },
        { id: 'msl_pred', name: '平均海平面气压', style: 'hurricane_map:hurricane_surface_msl' },
      ],
      atmosphereLayers: [
        { id: 'q_air', name: '比湿度', style: 'hurricane_map:hurricane_air_q' },
        { id: 't_air', name: '温度', style: 'hurricane_map:hurricane_air_t' },
        { id: 'u_pred', name: '西东风速', style: 'hurricane_map:hurricane_air_u' },
        { id: 'v_air', name: '南北风速', style: 'hurricane_map:hurricane_air_v' },
        { id: 'z_air', name: '位势高度', style: 'hurricane_map:hurricane_air_z' },
      ]
    }
  },
  computed: {
    selectedModel() {
      if (!this.selectedMainModelId) return null;
      return this.models.find(m => m.id === this.selectedMainModelId);
    },
    subModels() {
      if (this.selectedMainModelId && this.specificModels[this.selectedMainModelId]) {
        return this.specificModels[this.selectedMainModelId];
      }
      return [];
    },
    showHurricaneOptions() {
      if (!this.selectedModel || this.selectedModel.id !== 4) return false;
      const singleModeReady = this.selectedAnalysisMode === 'single' && this.selectedSubModelId;
      const multiModeReady = this.selectedAnalysisMode === 'multi';
      return singleModeReady || multiModeReady;
    },
    // --- 步骤 2: 创建计算属性，根据选择的层次返回对应的图层列表 ---
    availableLayers() {
        if (this.selectedLevel === 'ground') {
            return this.groundLayers;
        }
        if (this.selectedLevel === 'atmosphere') {
            return this.atmosphereLayers;
        }
        return []; // 如果没有选择层次，则返回空数组
    }
  },
  methods: {
    resetHurricaneSelection() {
        this.selectedLevel = null;
        this.selectedLayer = null;
        this.$emit('layer-selected', null);
    },
    handleModelClick(model) {
      this.selectedSubModelId = null;
      this.selectedAnalysisMode = null;
      this.resetHurricaneSelection();
      this.$emit('select-model', model);
      this.$emit('select-analysis-mode', null);
    },
    handleAnalysisModeClick(mode) {
      this.selectedAnalysisMode = mode;
      this.resetHurricaneSelection();
      this.$emit('select-analysis-mode', mode);
      if (mode === 'multi') {
        this.selectedSubModelId = null;
        this.$emit('select-sub-model', { id: 'multi-analysis', name: '多模型综合分析' });
      }
    },
    handleSubModelClick(subModel) {
      this.selectedSubModelId = subModel.id;
      this.resetHurricaneSelection();
      this.$emit('select-sub-model', subModel);
    },
    handleLevelSelect(level) {
        this.selectedLevel = level;
        this.selectedLayer = null;
        this.$emit('layer-selected', null);
    },
    handleLayerSelect(layer) {
        this.selectedLayer = layer.id;
        this.$emit('layer-selected', {
            name: layer.id,
            level: this.selectedLevel,
            style: layer.style,
            opacity: 0.8
        });
    }
  }
}
</script>

<template>
  <section>
    <h2>第一步：选择灾害模型</h2>
    <div class="disaster-models">
      <div v-for="model in models" :key="model.id" 
           class="model-card" 
           :class="{ featured: model.featured, selected: selectedModel && selectedModel.id === model.id }"
           @click="handleModelClick(model)">
        <div class="model-icon" v-html="model.icon"></div>
        <div class="model-info">
          <h3>{{ model.name }}</h3>
          <p>{{ model.description }}</p>
        </div>
      </div>
    </div>
    
    <div v-if="selectedModel" class="analysis-mode-panel">
      <h2>第二步：选择分析模式</h2>
      <div class="mode-selection-container">
        <div class="mode-card" :class="{selected: selectedAnalysisMode === 'single'}" @click="handleAnalysisModeClick('single')">
          <div class="mode-title">单模型分析</div>
          <div class="mode-desc">从一个核心模型开始分析，系统将根据情况动态引入其他模型协同。</div>
        </div>
        <div class="mode-card" :class="{selected: selectedAnalysisMode === 'multi'}" @click="handleAnalysisModeClick('multi')">
          <div class="mode-title">多模型分析</div>
          <div class="mode-desc">直接启动多智能体协作模式，从全局视角进行综合分析与推演。</div>
        </div>
      </div>
    </div>

    <div v-if="selectedAnalysisMode === 'single' && subModels.length" class="sub-models-panel">
      <h4>请选择“{{ selectedModel.name }}”智能体集群中的专用分析智能体：</h4>
      <div class="sub-models">
        <div v-for="sub in subModels" :key="sub.id"
             class="sub-model-card"
             :class="{ selected: selectedSubModelId === sub.id }"
             @click="handleSubModelClick(sub)">
          {{ sub.name }}
        </div>
      </div>
    </div>

    <div v-if="showHurricaneOptions" class="analysis-mode-panel">
      <h2>第三步：选择分析层次</h2>
      <div class="mode-selection-container">
        <div class="mode-card" :class="{selected: selectedLevel === 'ground'}" @click="handleLevelSelect('ground')">
          <div class="mode-title">地面</div>
        </div>
        <div class="mode-card" :class="{selected: selectedLevel === 'atmosphere'}" @click="handleLevelSelect('atmosphere')">
          <div class="mode-title">大气</div>
        </div>
      </div>
    </div>

    <div v-if="selectedLevel" class="sub-models-panel">
      <h4>请选择要显示的图层：</h4>
      <div class="sub-models">
        <!-- 步骤 3: 使用新的计算属性 availableLayers 来动态渲染图层按钮 -->
        <div v-for="layer in availableLayers" :key="layer.id"
             class="sub-model-card"
             :class="{ selected: selectedLayer === layer.id }"
             @click="handleLayerSelect(layer)">
          {{ layer.name }}
        </div>
      </div>
    </div>

  </section>
</template>

<style scoped>
h2 {
    color: #2C7BE5;
    margin-bottom: 16px;
}
.analysis-mode-panel {
    margin-top: 24px;
    padding-top: 24px;
    border-top: 1px solid #e0e6ed;
}
.mode-selection-container {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
}
.mode-card {
    background: #fff;
    border: 2px solid #e0e6ed;
    border-radius: 8px;
    padding: 20px;
    cursor: pointer;
    transition: all .2s;
}
.mode-card:hover {
    border-color: #2C7BE5;
    transform: translateY(-4px);
    box-shadow: 0 6px 16px rgba(44,123,229,0.1);
}
.mode-card.selected {
    border-color: #30D158;
    background-color: #f0fff4;
    box-shadow: 0 4px 12px rgba(48,209,88,0.15);
}
.mode-title {
    font-size: 18px;
    font-weight: 600;
    color: #333;
    margin-bottom: 8px;
}
.mode-desc {
    font-size: 14px;
    color: #666;
    line-height: 1.6;
}

.sub-models-panel {
  margin-top: 20px;
}
.sub-models-panel h4 {
    color: #2C7BE5;
    font-weight: 600;
}
.sub-models {
  display: flex;
  flex-wrap: wrap; 
  gap: 16px;
  margin-top: 8px;
}
.sub-model-card {
  padding: 10px 20px;
  border: 1px solid #eee;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  transition: box-shadow .2s, border-color .2s, background-color .2s;
  font-weight: 500;
}
.sub-model-card:hover {
    border-color: #2C7BE5;
}
.sub-model-card.selected {
  border: 2px solid #2C7BE5;
  background: #e9f2ff;
  color: #2C7BE5;
  box-shadow: 0 2px 8px rgba(44,123,229,0.1);
}
.disaster-models {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
}
.model-card {
    background: #fff;
    border: 2px solid transparent;
    border-radius: 8px;
    padding: 20px;
    display: flex;
    align-items: center;
    gap: 16px;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    transition: all .2s;
}
.model-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 6px 16px rgba(0,0,0,0.08);
}
.model-card.featured {
    border-left: 4px solid #FF9F0A;
}
.model-card.selected {
  border: 2px solid #30D158;
  background: #f0fff4;
}
.model-icon {
    flex-shrink: 0;
}
.model-info h3 {
    margin: 0 0 4px 0;
    color: #333;
    font-size: 18px;
}
.model-info p {
    margin: 0;
    color: #666;
    font-size: 14px;
}
</style>
