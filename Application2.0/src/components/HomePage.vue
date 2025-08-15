<template>
  <div class="homepage-container">
    <!-- Section 1: Full-screen Hero Banner -->
    <section class="hero-section">
      <!-- Background Images (no change) -->
      <div class="background-container">
        <img
          v-for="(disaster, index) in disasters"
          :key="index"
          :src="disaster.backgroundImage"
          :alt="disaster.title + ' 背景图'"
          class="background-image"
          :class="{ active: activeDisaster === index }"
        />
      </div>

      <!-- Main Content Overlay (no change) -->
      <div class="content-overlay">
        <div class="disaster-titles">
          <ul>
            <li v-for="(disaster, index) in disasters" :key="index" :class="{ active: activeDisaster === index }">
              {{ disaster.title }}
            </li>
          </ul>
        </div>
        <div class="disaster-descriptions">
          <div class="description-container">
              <div v-for="(disaster, index) in disasters" :key="index" class="description-item" :class="{ active: activeDisaster === index }">
                <h3>{{ disaster.title }}</h3>
                <p>{{ disaster.description }}</p>
                <button @click="goToModels">进入模型</button>
              </div>
          </div>
        </div>
      </div>

      <!-- Scroll Down Indicator (no change) -->
      <div class="scroll-down-indicator">
        <span>了解更多</span>
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 5V19M12 19L19 12M12 19L5 12" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>

      <!-- NEW: Vertically Aligned Info Cards -->
      <div class="info-tabs-container">
        <div class="info-card">
          <div class="vertical-title">
            <h2>项目背景</h2>
          </div>
          <div class="expand-content">
            <h3>项目背景</h3>
            <p>智能化应急减灾是应对突发灾害的关键手段，对于提升国家的灾害应对能力具有重要意义。“空-天-地-人-网”等多种技术手段和渠道为智能化应急减灾提供了丰富的数据支撑，有助于完成灾害隐患识别、灾害风险研判和灾情评估等不同的应急任务。然而，现有的应急模型主要面向单模态数据和单一任务，存在多模态数据协同性与系统性分析不足、通用性低和时效性差等问题。</p>
          </div>
        </div>
        <div class="info-card">
          <div class="vertical-title">
            <h2>项目简介</h2>
          </div>
          <div class="expand-content">
            <h3>项目简介</h3>
            <p>智枢多模态应急减灾智能平台，基于哈工大优势学科，深度融合卫星遥感、产业分布、物联网感知、社交媒体等多源异构数据，构建了包括洪水模型，风暴模型，地震模型，野火模型等在内的智能体集群，精确识别灾情、量化评估灾损，实现灾害管理，填补我国巨灾模型多智能体平台的空白。</p>
          </div>
        </div>
      </div>
    </section>

    <!-- The old info-section is now removed -->
  </div>
</template>

<script>
export default {
  name: 'HomePage',
  data() {
    return {
      activeDisaster: 0,
      disasters: [
        { 
          title: '野火', 
          description: '基于多源数据与AI智能体，我们的野火模型能够实时监测全球火点，精确预测火势蔓延趋势，并评估潜在风险，为早期预警和高效资源调配提供关键决策支持。',
          backgroundImage: '/WildFire.png'
        },
        { 
          title: '地震', 
          description: '通过整合地质构造、历史地震数据和实时传感器信息，地震模型可以快速评估震后影响，预测次生灾害风险，并为应急响应和救援行动规划提供科学依据。',
          backgroundImage: '/Earthquake.png'
        },
        { 
          title: '洪水', 
          description: '结合气象预报、卫星遥感和地形数据，洪水模型能精准模拟淹没范围和水深，为防洪工程调度、人员疏散路径规划和灾后损失评估提供动态支持。',
          backgroundImage: '/Flood.png'
        },
        { 
          title: '飓风', 
          description: '我们的飓风模型利用先进的气象算法，预测风暴路径、强度和影响范围。它支持对沿海地区进行风险评估，并辅助制定全面的防灾减灾策略。',
          backgroundImage: '/Hurricane.png'
        }
      ],
      scrollTimeout: null
    };
  },
  mounted() {
    window.addEventListener('wheel', this.handleScroll);
  },
  beforeUnmount() {
    window.removeEventListener('wheel', this.handleScroll);
  },
  methods: {
    handleScroll(event) {
      if (this.scrollTimeout) return;

      if (event.deltaY > 0) {
        this.activeDisaster = (this.activeDisaster + 1) % this.disasters.length;
      } else {
        this.activeDisaster = (this.activeDisaster - 1 + this.disasters.length) % this.disasters.length;
      }

      this.scrollTimeout = setTimeout(() => {
        this.scrollTimeout = null;
      }, 800);
    },
    goToModels() {
      this.$router.push('/models');
    }
  }
};
</script>

<style scoped>
/* Section 1: Hero Banner Styles (no change) */
.hero-section {
  height: calc(100vh - 64px);
  position: relative;
  overflow: hidden;
  color: #fff;
  display: flex;
  align-items: center;
}
.background-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: #1a1a1a;
}
.background-image {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0; 
  transition: opacity 1.2s ease-in-out; 
  filter: brightness(0.8);
}
.background-image.active {
  opacity: 0.5; 
}
.content-overlay {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 0 8%;
}
.disaster-titles ul {
  list-style: none;
  padding: 0;
  margin: 0;
}
.disaster-titles li {
  font-size: 5.5rem;
  font-weight: 700;
  line-height: 1.2;
  opacity: 0.2;
  transition: opacity 0.5s ease, transform 0.5s ease;
  cursor: default;
  transform: translateX(-10px);
}
.disaster-titles li.active {
  opacity: 1;
  transform: translateX(0);
}
.disaster-descriptions {
  flex-basis: 45%;
  position: relative;
  height: 250px;
}
.description-container {
    position: relative;
    width: 100%;
    height: 100%;
}
.description-item {
  position: absolute;
  top: 0;
  left: 0;
  opacity: 0;
  transform: translateY(20px);
  transition: opacity 0.6s ease-in-out, transform 0.6s ease-in-out;
  visibility: hidden;
}
.description-item.active {
  opacity: 1;
  transform: translateY(0);
  visibility: visible;
}
.description-item h3 {
  font-size: 2.8rem;
  margin-bottom: 1rem;
  font-weight: 600;
}
.description-item p {
  font-size: 1.1rem;
  max-width: 500px;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.9);
}
.description-item button {
  margin-top: 1.5rem;
  padding: 12px 30px;
  background: #2C7BE5;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background .2s, transform 0.2s;
}
.description-item button:hover {
  background: #185fa3;
  transform: translateY(-2px);
}
.scroll-down-indicator {
  position: absolute;
  bottom: 30px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 3;
  color: white;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  opacity: 0.7;
  animation: bounce 2s infinite;
}
@keyframes bounce {
  0%, 20%, 50%, 80%, 100% {
    transform: translate(-50%, 0);
  }
  40% {
    transform: translate(-50%, -15px);
  }
  60% {
    transform: translate(-50%, -5px);
  }
}

/* NEW STYLES for vertical expanding cards */
.info-tabs-container {
  position: absolute;
  top: 50%;
  left: 20px;
  transform: translateY(-50%);
  z-index: 10;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.info-card {
  display: flex;
  align-items: center;
  width: 60px;
  height: 220px;
  background: rgba(0, 0, 0, 0.25);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px); /* For Safari */
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: width 0.5s cubic-bezier(0.23, 1, 0.32, 1), 
              background 0.5s ease;
}

.info-card:hover {
  width: 450px; /* Expanded width */
  background: rgba(0, 0, 0, 0.5);
}

.vertical-title {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 60px; /* Same as collapsed card width */
  height: 100%;
}

.vertical-title h2 {
  writing-mode: vertical-rl;
  transform: rotate(0deg);
  font-size: 18px;
  color: #fff;
  font-weight: 500;
  margin: 0;
  padding: 0;
  white-space: nowrap;
  transition: opacity 0.3s ease;
}

.info-card:hover .vertical-title h2 {
    opacity: 0.5;
}

.expand-content {
  width: 0;
  opacity: 0;
  overflow: hidden;
  color: #fff;
  padding-left: 10px;
  transition: width 0.4s cubic-bezier(0.23, 1, 0.32, 1) 0.1s, 
              opacity 0.3s ease 0.1s;
}

.info-card:hover .expand-content {
  width: calc(450px - 60px - 10px); /* Expanded width - title width - padding */
  opacity: 1;
}

.expand-content h3 {
  font-size: 22px;
  font-weight: 600;
  color: #fff;
  margin: 0 0 12px 0;
  border-bottom: 2px solid #2C7BE5;
  padding-bottom: 8px;
  display: inline-block;
}

.expand-content p {
  font-size: 15px;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.9);
  margin: 0;
}
</style>
