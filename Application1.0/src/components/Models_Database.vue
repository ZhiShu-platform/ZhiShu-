<template>
    <div class="page-container">
        <div>
            <h3 class="section-title">模型库 (Intelligent Agent Cluster)</h3>
            <p class="section-subtitle">平台集成了多种灾害应急模型，形成协同工作的智能体集群，以应对不同的灾害场景。</p>
            <div class="main-model-tabs">
                <button v-for="(main, idx) in mainModels" :key="main.name" :class="['main-model-btn', {active: activeMainModelIdx === idx}]" @click="activeMainModelIdx = idx">
                    {{ main.name }}
                </button>
            </div>
            <div class="model-grid">
                <template v-for="sub in mainModels[activeMainModelIdx].subs" :key="sub.id">
                    <a v-if="sub.id === 'wf-c'"
                       href="https://www.huaweicloud.com/product/pangu"
                       target="_blank"
                       title="点击跳转到官网"
                       class="model-card-link">
                        <div class="model-card clickable">
                            <div class="model-title">{{ sub.title }}</div>
                            <div class="model-desc">{{ sub.desc }}</div>
                        </div>
                    </a>
                    <div v-else
                         class="model-card"
                         :id="'model-card-' + sub.id"
                         :class="{ 'clickable': sub.id === 'wf-a' }"
                         @click="handleModelCardClick(sub)">
                        <div class="model-title">{{ sub.title }}</div>
                        <div class="model-desc">{{ sub.desc }}</div>
                    </div>
                </template>
                </div>
        </div>

        <DatasetShowcase
            :datasets="datasets"
            :models="mainModels"
            @highlight-model-in-library="highlightModel"
        />
    </div>
</template>

<script>
import DatasetShowcase from './DatasetShowcase.vue';

export default {
    name: 'Models_Database',
    components: {
        DatasetShowcase
    },
    data() {
        return {
            mainModels: [
                {
                    name: '野火',
                    subs: [
                        { id: 'wf-a', title: 'Climada', desc: '加州地区的灾损统计和评估' },
                        { id: 'wf-b', title: 'Cell2Fire', desc: '支持实时火势监测与蔓延趋势分析。' },
                        

                    ]
                },
                {
                    name: '地震',
                    subs: [
                        { id: 'eq-a', title: '地震A', desc: '地震烈度分布模拟，支持多场景分析。' },
                        { id: 'eq-b', title: '地震B', desc: '震后损失快速评估与救援建议。' },
                        { id: 'eq-c', title: '地震C', desc: '余震概率分析与风险预警。' },
                        { id: 'eq-d', title: '地震D', desc: '地震历史数据可视化与趋势分析。' }
                    ]
                },
                {
                    name: '洪水',
                    subs: [
                        { id: 'fl-a', title: '洪水A (Lisflood)', desc: '洪水淹没范围预测，适用于多种地形。' },
                        { id: 'fl-b', title: '洪水B', desc: '洪水风险分级与应急响应建议。' },
                        { id: 'fl-c', title: '实时水位监测与预警。' },
                        { id: 'fl-d', title: '历史洪水事件分析与对比。' }
                    ]
                },
                {
                    name: '气象',
                    subs: [
                        { id: 'hu-a', title: 'Aurora', desc: '预测风速，压强，温度等' },
                        { id: 'wf-c', title: 'Pangu', desc: '华为云提供的面向行业的大模型，包含NLP、CV、多模态、预测、科学计算等五类基础和行业大模型' },
                    ]
                }
            ],
            activeMainModelIdx: 0,
            datasets: [
                { id: 'ds-01', name: 'MODIS 动态火点数据', disasterTypes: ['野火'], description: '来自MODIS传感器的全球热异常数据，对近实时火点监测至关重要。', source: 'NASA FIRMS', updateFrequency: '每3小时', resolution: '1公里', poweredModels: ['wf-a', 'wf-b', 'wf-c'] },
                { id: 'ds-02', name: 'USGS ShakeMap', disasterTypes: ['地震'], description: '在重大地震后提供近实时的地面运动和震动强度图。', source: 'USGS', updateFrequency: '事件驱动', resolution: '~1-10公里', poweredModels: ['eq-a', 'eq-b'] },
                { id: 'ds-03', name: '全球洪水监测系统 (GloFAS)', disasterTypes: ['洪水'], description: '提供全球范围内的水文预报和洪水监测，支持早期预警。', source: 'ECMWF/JRC', updateFrequency: '每日', resolution: '0.1度', poweredModels: ['fl-a', 'fl-b'] },
                { id: 'ds-04', name: 'OpenStreetMap 建筑物', disasterTypes: ['通用', '地震', '洪水', '飓风'], description: '全球众包的建筑物轮廓数据，是暴露度分析的核心基础。', source: 'OpenStreetMap', updateFrequency: '持续更新', resolution: 'N/A', poweredModels: ['eq-b', 'fl-d', 'hu-c'] },
                { id: 'ds-05', name: '全球人类居住层 (GHSL)', disasterTypes: ['通用', '野火', '地震', '洪水'], description: '全球高精度人口分布格网数据，用于评估灾害影响范围和人口暴露。', source: 'JRC/GHSL', updateFrequency: '周期性', resolution: '30米 - 1公里', poweredModels: ['wf-d', 'eq-b', 'fl-b', 'hu-c'] },
                { id: 'ds-06', name: '全球预报系统 (GFS)', disasterTypes: ['野火', '洪水', '飓风'], description: '全球数值天气预报模型，提供风、温、压等关键气象变量。', source: 'NOAA', updateFrequency: '每6小时', resolution: '0.25度', poweredModels: ['wf-a', 'fl-a', 'hu-a'] },
                { id: 'ds-07', name: '土地覆盖类型 (CCI-LC)', disasterTypes: ['野火', '洪水'], description: '全球土地覆盖分类数据，用于评估不同地表的火灾风险和洪水径流。', source: 'ESA', updateFrequency: '每年', resolution: '300米', poweredModels: ['wf-a', 'fl-a'] },
                { id: 'ds-08', name: '物联网实时环境感知数据', disasterTypes: ['野火', '洪水'], description: '来自部署在关键区域的传感器网络的实时环境与设施状态数据。', source: '内部物联网平台', updateFrequency: '实时', resolution: '站点级', poweredModels: ['wf-c', 'fl-c'] }
            ]
        }
    },
    methods: {
        // 新增方法：处理模型卡片的点击事件
        handleModelCardClick(subModel) {
            // 只对 ID 为 'wf-a' (Cell2Fire) 的卡片进行导航
            if (subModel.id === 'wf-a') {
                this.$router.push('/model/' + subModel.id);
            }
        },
        highlightModel(modelId) {
            const parentIndex = this.mainModels.findIndex(main => main.subs.some(sub => sub.id === modelId));
            if (parentIndex !== -1) {
                this.activeMainModelIdx = parentIndex;
                this.$nextTick(() => {
                    const el = document.getElementById('model-card-' + modelId);
                    if (el) {
                        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        el.classList.add('highlight');
                        setTimeout(() => {
                            el.classList.remove('highlight');
                        }, 2000);
                    }
                });
            }
        }
    }
}
</script>

<style scoped>
/* 新增样式，确保 a 标签不会改变卡片原有外观 */
.model-card-link {
    text-decoration: none;
    color: inherit;
}

.page-container {
    padding: 32px;
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
.main-model-tabs {
    display: flex;
    gap: 18px;
    margin-bottom: 28px;
}
.main-model-btn {
    background: #f4f8fd;
    border: 1px solid #e0e6ed;
    border-radius: 6px;
    color: #2C7BE5;
    font-size: 17px;
    font-weight: 500;
    padding: 8px 28px;
    cursor: pointer;
    transition: background .2s, color .2s;
}
.main-model-btn.active, .main-model-btn:hover {
    background: #2C7BE5;
    color: #fff;
}
.model-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 24px;
}
.model-card {
    background: #fff;
    border: 1px solid #e0e6ed;
    border-radius: 10px;
    box-shadow: 0 2px 8px rgba(44,123,229,0.06);
    padding: 24px 20px;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    transition: all .3s ease;
}
.model-card:hover {
    box-shadow: 0 4px 16px rgba(44,123,229,0.13);
}
/* 为可点击的卡片添加鼠标手势 */
.model-card.clickable {
    cursor: pointer;
}
/* 为可点击的卡片添加更明显的悬停效果 */
.model-card.clickable:hover {
    border-color: #2C7BE5;
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(44,123,229,0.15);
}
.model-card.highlight {
    box-shadow: 0 0 0 3px rgba(44, 123, 229, 0.5);
    transform: scale(1.02);
}
.model-title {
    font-size: 20px;
    font-weight: bold;
    color: #2C7BE5;
    margin-bottom: 10px;
}
.model-desc {
    font-size: 15px;
    color: #333;
    line-height: 1.7;
}
</style>