<template>
  <div class="dataset-card">
    <div class="card-header">
      <div class="icon-wrapper" v-html="disasterIcon"></div>
      <h4 class="dataset-title">{{ dataset.name }}</h4>
    </div>

    <div class="disaster-tags-container">
        <span v-for="disaster in dataset.disasterTypes" :key="disaster" :class="['disaster-tag', getDisasterClass(disaster)]">
            {{ disaster }}
        </span>
    </div>

    <p class="dataset-description">{{ dataset.description }}</p>

    <div class="metadata-grid">
      <div class="metadata-item">
        <span class="meta-label">来源</span>
        <span class="meta-value">{{ dataset.source }}</span>
      </div>
      <div class="metadata-item">
        <span class="meta-label">更新频率</span>
        <span class="meta-value">{{ dataset.updateFrequency }}</span>
      </div>
      
    </div>

    <div class="model-relations">
      <h5 class="relations-title">驱动模型</h5>
      <div class="tags-container">
        <span v-for="modelId in dataset.poweredModels" :key="modelId" class="model-tag" @click.stop="onModelClick(modelId)">
          {{ getModelName(modelId) }}
        </span>
      </div>
    </div>
    
    <div class="card-footer">
        <button v-if="dataset.id === 'ds-09'" class="details-btn" @click="goToDetails">查看详情</button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DatasetCard',
  props: {
    dataset: {
      type: Object,
      required: true
    },
    models: {
      type: Array,
      required: true
    }
  },
  computed: {
    disasterIcon() {
      const icons = {
        '野火': `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"></path><path d="M12 18c-4.418 0-8-3.582-8-8s3.582-8 8-8 8 3.582 8 8-3.582 8-8 8z" opacity="0.5"></path><path d="M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8z" fill="currentColor"></path></svg>`,
        '地震': `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12h3l3-9 6 18 3-9h3"></path></svg>`,
        '洪水': `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7l4 6-4 6"></path><path d="M10 7l4 6-4 6"></path><path d="M17 7l4 6-4 6"></path></svg>`,
        '飓风': `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 4H3v2l6.29 6.29L3 18v2h18v-2l-6.29-6.29L21 6V4z"></path></svg>`,
        '通用': `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.5 12H18c-.7 2.3-2.1 4.3-4.1 5.9"></path><path d="M2.5 12H6c.7 2.3 2.1 4.3 4.1 5.9"></path><path d="M12 2.5V6c-2.3.7-4.3 2.1-5.9 4.1"></path><path d="M12 21.5V18c-2.3-.7-4.3-2.1-5.9-4.1"></path><path d="M12 2.5V6c2.3.7 4.3 2.1 5.9 4.1"></path><path d="M12 21.5V18c2.3-.7-4.3-2.1-5.9-4.1"></path><path d="M2.5 12H6c-.7-2.3-2.1-4.3-4.1-5.9"></path><path d="M21.5 12H18c.7-2.3 2.1-4.3 4.1-5.9"></path></svg>`
      };
      if (this.dataset.disasterTypes && this.dataset.disasterTypes.length > 0) {
        return icons[this.dataset.disasterTypes[0]] || icons['通用'];
      }
      return icons['通用'];
    }
  },
  methods: {
    // 新增方法，用于跳转到详情页
    goToDetails() {
        if (this.dataset && this.dataset.id) {
            this.$router.push(`/dataset/${this.dataset.id}`);
        }
    },
    getModelName(modelId) {
      for (const mainModel of this.models) {
        const foundSub = mainModel.subs.find(sub => sub.id === modelId);
        if (foundSub) {
          return foundSub.title;
        }
      }
      return modelId; // Fallback
    },
    onModelClick(modelId) {
      this.$emit('model-link-click', modelId);
    },
    getDisasterClass(disasterType) {
      const mapping = {
        '野火': 'wildfire',
        '地震': 'earthquake',
        '洪水': 'flood',
        '飓风': 'hurricane',
        '通用': 'generic'
      };
      return `tag-${mapping[disasterType] || 'generic'}`;
    }
  }
}
</script>

<style scoped>
/* 样式无需改动，保持原样 */
.dataset-card {
  background: #fff;
  border: 1px solid #e0e6ed;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(44,123,229,0.06);
  padding: 20px;
  display: flex;
  flex-direction: column;
  transition: box-shadow .2s, transform .2s;
}
.dataset-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 6px 20px rgba(44,123,229,0.12);
}
.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px; /* 减小间距以容纳标签 */
}
.icon-wrapper {
  color: #2C7BE5;
  flex-shrink: 0;
}
.dataset-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin: 0;
}
.disaster-tags-container {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 12px;
}
.disaster-tag {
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 500;
    color: #fff;
    line-height: 1.4;
}
.tag-wildfire { background-color: #FF9500; }
.tag-earthquake { background-color: #A2845E; }
.tag-flood { background-color: #007AFF; }
.tag-hurricane { background-color: #5856D6; }
.tag-generic { background-color: #8E8E93; }

.dataset-description {
  font-size: 14px;
  color: #555;
  line-height: 1.6;
  flex-grow: 1;
  margin-bottom: 16px;
}
.metadata-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
  border-top: 1px solid #f0f3f7;
  padding-top: 16px;
}
.metadata-item {
  font-size: 13px;
}
.meta-label {
  display: block;
  color: #888;
  margin-bottom: 4px;
}
.meta-value {
  color: #333;
  font-weight: 500;
}
.model-relations {
  margin-bottom: 16px;
}
.relations-title {
  font-size: 14px;
  font-weight: 600;
  color: #2C7BE5;
  margin: 0 0 8px 0;
}
.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.model-tag {
  background-color: #e9f2ff;
  color: #2C7BE5;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color .2s;
}
.model-tag:hover {
  background-color: #d1e3ff;
}
.card-footer {
  margin-top: auto;
  text-align: right;
}
.details-btn {
  background: transparent;
  border: 1px solid #d0d7de;
  color: #2C7BE5;
  padding: 6px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: all .2s;
}
.details-btn:hover {
  background-color: #e9f2ff;
  border-color: #2C7BE5;
}
</style>