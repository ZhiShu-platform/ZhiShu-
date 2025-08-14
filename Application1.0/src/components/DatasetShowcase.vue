<template>
  <div class="dataset-showcase">
    <h3 class="section-title">数据集勘探 (Dataset Exploration)</h3>
    <p class="section-subtitle">探索驱动我们智能体集群的多源异构数据集。点击数据集卡片以了解其详情，或使用筛选器查看特定模型所依赖的数据。</p>

    <!-- 筛选器 -->
    <div class="filters">
      <div class="filter-group">
        <button v-for="disaster in disasterFilters" :key="disaster" 
                :class="['filter-btn', { active: activeDisaster === disaster }]"
                @click="activeDisaster = disaster">
          {{ disaster }}
        </button>
      </div>
      <div class="filter-group">
        <select v-model="selectedModel" class="model-select">
          <option :value="null">按驱动模型筛选</option>
          <option v-for="model in allSubModels" :key="model.id" :value="model.id">
            {{ model.title }}
          </option>
        </select>
        <input type="text" v-model="searchTerm" class="search-input" placeholder="搜索数据集..." />
      </div>
    </div>

    <!-- 数据集网格 -->
    <div class="dataset-grid">
      <DatasetCard v-for="dataset in filteredDatasets" 
                   :key="dataset.id" 
                   :dataset="dataset"
                   :models="models"
                   @model-link-click="highlightModel" />
    </div>
    <div v-if="filteredDatasets.length === 0" class="no-results">
        没有找到匹配的数据集。
    </div>
  </div>
</template>

<script>
import DatasetCard from './DatasetCard.vue';

export default {
  name: 'DatasetShowcase',
  components: { DatasetCard },
  props: {
    datasets: { type: Array, required: true },
    models: { type: Array, required: true }
  },
  data() {
    return {
      activeDisaster: '全部',
      disasterFilters: ['全部', '野火', '地震', '洪水', '飓风', '通用'],
      selectedModel: null,
      searchTerm: ''
    }
  },
  computed: {
    allSubModels() {
      return this.models.flatMap(main => main.subs);
    },
    filteredDatasets() {
      let result = this.datasets;

      // 1. 按灾害类型筛选
      if (this.activeDisaster !== '全部') {
        result = result.filter(d => d.disasterTypes.includes(this.activeDisaster));
      }

      // 2. 按模型筛选
      if (this.selectedModel) {
        result = result.filter(d => d.poweredModels.includes(this.selectedModel));
      }

      // 3. 按搜索词筛选
      if (this.searchTerm.trim()) {
        const lowerSearchTerm = this.searchTerm.toLowerCase();
        result = result.filter(d => 
          d.name.toLowerCase().includes(lowerSearchTerm) ||
          d.description.toLowerCase().includes(lowerSearchTerm) ||
          d.source.toLowerCase().includes(lowerSearchTerm)
        );
      }
      
      return result;
    }
  },
  methods: {
    highlightModel(modelId) {
      this.$emit('highlight-model-in-library', modelId);
    }
  }
}
</script>

<style scoped>
.dataset-showcase {
  margin-top: 48px;
}
.section-title {
  font-size: 24px;
  font-weight: bold;
  color: #2C7BE5;
  margin-bottom: 8px;
}
.section-subtitle {
  font-size: 16px;
  color: #555;
  margin-bottom: 24px;
  max-width: 800px;
}
.filters {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
  flex-wrap: wrap;
  gap: 16px;
}
.filter-group {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
}
.filter-btn {
  background: #f4f8fd;
  border: 1px solid #e0e6ed;
  border-radius: 6px;
  color: #2C7BE5;
  font-size: 15px;
  font-weight: 500;
  padding: 6px 20px;
  cursor: pointer;
  transition: background .2s, color .2s;
}
.filter-btn.active, .filter-btn:hover {
  background: #2C7BE5;
  color: #fff;
}
.model-select, .search-input {
    height: 36px;
    border: 1px solid #e0e6ed;
    border-radius: 6px;
    padding: 0 12px;
    font-size: 15px;
}
.search-input {
    width: 220px;
}
.dataset-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 24px;
}
.no-results {
    padding: 40px;
    text-align: center;
    color: #888;
    background-color: #f8f9fa;
    border-radius: 8px;
    margin-top: 24px;
}
</style>
