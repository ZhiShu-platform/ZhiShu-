<template>
  <div class="model-detail-page">
    <div class="page-header">
      <h1>{{ modelDetails.title }}</h1>
      <p class="subtitle">{{ modelDetails.subtitle }}</p>
      <p class="intro">{{ modelDetails.introduction }}</p>
    </div>

    <div class="gallery-grid">
      <div v-for="item in modelDetails.gallery" :key="item.title" class="gallery-item">
        <div class="image-container">
          <img :src="item.src" :alt="item.title" class="gallery-image">
        </div>
        <div class="text-content">
          <h3>{{ item.title }}</h3>
          <p>{{ item.description }}</p>
        </div>
      </div>
    </div>

    <!-- 新增的页脚部分 -->
    <div class="page-footer">
      <a href="https://github.com/CLIMADA-project/climada_python.git" target="_blank" rel="noopener noreferrer" class="footer-btn link-btn">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path></svg>
        <span>访问 CLIMADA on GitHub</span>
      </a>
      <button @click="goToInstructions" class="footer-btn instruction-btn">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"></path><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
        <span>使用说明</span>
      </button>
    </div>

  </div>
</template>

<script>
export default {
  name: 'ModelDetail',
  props: ['id'],
  data() {
    return {
      modelDetails: {
        title: 'CLIMADA模型详情',
        subtitle: 'CLIMADA 野火模块输出分析',
        introduction: '本页面展示了使用 Climada 模型对加州地区进行野火风险分析后，通过 CLIMADA 平台生成的一系列关键可视化结果。这些图表揭示了资产分布、火灾风险、损失趋势以及单次事件的潜在经济影响，为风险评估和应急决策提供了数据支持。',
        gallery: [
          { src: '/california_asset_distribution.png', title: '加州资产价值分布图', description: '此图展示了加州地区资产价值的空间分布情况。颜色越亮（黄色）表示该区域的资产价值密度越高。这对于理解哪些高价值区域暴露在野火风险下至关重要，是计算潜在经济损失的基础。' },
          { src: '/california_wildfire_spatial_distribution.png', title: '加州野火空间分布与暴露点影响', description: '该图叠加了野火发生点（橙色星形）与暴露点（灰色和红色圆点）。红色圆点表示受到野火影响的暴露点。这有助于直观地识别出受野火威胁最严重的具体位置。' },
          { src: '/peak_day_spatial_distribution_2025-01-08.png', title: '损失峰值日空间分布 (2025-01-08)', description: '此图聚焦于模拟的损失最高的一天（2025年1月8日），显示了当天的火点（星形）和受影响的暴露点（红点）。右侧的色条代表亮度温度，有助于分析火灾的强度。' },
          { src: '/wildfire_daily_damage_trend_2025-01-06_to_2025-01-23.png', title: '野火逐日损失趋势图', description: '该折线图展示了在模拟时间段内（1月6日至23日），每日的总损失（蓝色）和直接损失（红色）变化趋势。可以清晰地看到损失在1月8日达到峰值，随后迅速下降，这对于理解灾害事件的时间动态至关重要。' },
          { src: '/wildfire_event_loss_distribution.png', title: '野火事件损失分布直方图', description: '此直方图显示了所有模拟野火事件的损失金额分布。可以看出，大多数事件造成的损失较小，但存在少数极端事件可能导致巨大的经济损失。蓝色虚线标示了损失金额的中位数。' }
        ]
      }
    };
  },
  // 新增 methods
  methods: {
    goToInstructions() {
      this.$router.push('/usage-instructions');
    }
  }
}
</script>

<style scoped>
.model-detail-page {
  padding: 32px;
  max-width: 1200px;
  margin: 0 auto;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

.page-header {
  text-align: center;
  margin-bottom: 48px;
  border-bottom: 1px solid #e0e6ed;
  padding-bottom: 24px;
}

.page-header h1 {
  font-size: 32px;
  font-weight: 700;
  color: #2C7BE5;
}

.page-header .subtitle {
  font-size: 20px;
  color: #555;
  margin-top: 8px;
}

.page-header .intro {
  font-size: 16px;
  color: #6c757d;
  line-height: 1.7;
  max-width: 800px;
  margin: 16px auto 0;
}

.gallery-grid {
  display: grid;
  gap: 48px;
}

.gallery-item {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
  align-items: center;
  background-color: #f8f9fa;
  padding: 24px;
  border-radius: 8px;
  border: 1px solid #e0e6ed;
}

.gallery-item:nth-child(even) {
  direction: rtl; 
}
.gallery-item:nth-child(even) > * {
  direction: ltr; 
}

.image-container {
  text-align: center;
}

.gallery-image {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.1);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.gallery-image:hover {
    transform: scale(1.03);
    box-shadow: 0 12px 32px rgba(0,0,0,0.15);
}

.text-content {
  padding: 0 16px;
}

.text-content h3 {
  font-size: 22px;
  font-weight: 600;
  color: #333;
  margin-bottom: 16px;
}

.text-content p {
  font-size: 15px;
  line-height: 1.8;
  color: #555;
}

/* 新增页脚样式 */
.page-footer {
  margin-top: 48px;
  padding-top: 24px;
  border-top: 1px solid #e0e6ed;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 24px;
}

.footer-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  text-decoration: none;
  transition: all .2s;
  border: 1px solid transparent;
}

.footer-btn svg {
  flex-shrink: 0;
}

.link-btn {
  background-color: #333;
  color: #fff;
  border-color: #333;
}
.link-btn:hover {
  background-color: #000;
  transform: translateY(-2px);
}

.instruction-btn {
  background-color: #2C7BE5;
  color: #fff;
  border-color: #2C7BE5;
}
.instruction-btn:hover {
  background-color: #185fa3;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(44,123,229,0.2);
}


@media (max-width: 992px) {
  .gallery-item,
  .gallery-item:nth-child(even) {
    grid-template-columns: 1fr;
    direction: ltr;
  }
}

@media (max-width: 768px) {
  .page-footer {
    flex-direction: column;
    gap: 16px;
  }
}
</style>
