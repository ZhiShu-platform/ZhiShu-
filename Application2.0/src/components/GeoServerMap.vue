<template>
  <div class="map-container">
    <h3 v-if="title" class="map-title">{{ title }}</h3>
    <div id="map" class="map-area"></div>
    
    <!-- 默认图例: 当没有选择飓风图层时显示 -->
    <div class="map-overlay legend" v-if="!legendGraphicUrl">
      <h4>图例</h4>
      <div v-if="wmsLayer">
        <!-- This is a fallback, should ideally not be shown -->
        <div class="legend-item">
          <span class="legend-color" style="background: linear-gradient(to right, yellow, orange, red);"></span>
          飓风风险分析
        </div>
      </div>
      <div v-else>
        <div v-for="layer in layersConfig" :key="layer.name" class="legend-item">
          <span class="legend-color" :style="{ backgroundColor: layer.style.fillColor }"></span>
          {{ layer.displayName }}
        </div>
      </div>
    </div>

    <!-- 动态飓风图例 (混合模式) -->
    <div v-if="legendGraphicUrl && !legendError" class="map-overlay geoserver-legend hybrid-legend">
        <!-- 步骤 3: 创建一个容器来组合图片和标签 -->
        <div class="legend-content">
            <!-- GeoServer 生成的图例图片 -->
            <img :src="legendGraphicUrl" alt="图层图例" @error="handleLegendError" />
            <!-- 前端控制的数值标签 -->
            <div v-if="activeLegendValues" class="legend-labels">
                <span class="label-max">{{ activeLegendValues.max }}</span>
                <span class="label-min">{{ activeLegendValues.min }}</span>
            </div>
        </div>
    </div>

    <!-- 图例加载失败时的提示信息 -->
    <div v-if="legendError" class="map-overlay geoserver-legend legend-error-panel">
        <p>图例加载失败</p>
    </div>


    <div class="map-overlay status-panel">
        <h4>图层状态</h4>
        <div v-for="status in layerStatuses" :key="status.name" class="status-item" :class="status.className">
            <strong>{{ status.displayName }}:</strong> {{ status.message }}
        </div>
    </div>

  </div>
</template>

<script>
import L from 'leaflet';
import { reactive } from 'vue';

export default {
  name: 'GeoServerMap',
  props: {
    title: String,
    hurricaneLayer: {
        type: Object,
        default: null
    }
  },
  emits: ['region-selected'],
  setup() {
    const layerStatuses = reactive({});
    return { layerStatuses };
  },
  data() {
    return {
      map: null,
      geoServerBaseUrl: '/geoserver/disaster_map/ows',
      hurricaneGeoServerBaseUrl: '/geoserver/hurricane_map/ows',
      wmsLayer: null, 
      wfsLayers: [],
      legendGraphicUrl: null,
      legendError: false,
      // --- 步骤 1: 新增一个用于存储图例数值的数据属性 ---
      activeLegendValues: null,
      // --- 步骤 2: 创建一个只包含数值的数据结构 ---
      legendValueData: {
        '10u_pred': { min: 22, max: -12 },
        '10v_pred': { min: 22, max: -12 },
        '2t_pred': { min: 320, max: 220 },
        'msl_pred': { min: 1050, max: 980 },
        'q_air': { min: 0.0264, max: -0.0001 },
        't_air': { min: 260, max: 140 },
        'u_pred': { min: 120, max: -40 },
        'v_air': { min: 40, max: -40 },
        'z_air': { min: 103500, max: 98000 }
      },
      layersConfig: [
        {
          name: 'california_fires',
          displayName: '加州野火 (实时)',
          tableName: 'disaster_map:current_california_fires',
          style: { radius: 6, fillColor: "#FF4500", color: "#000", weight: 1, opacity: 1, fillOpacity: 0.8 },
          createPopupContent: (feature) => `<strong>火灾事件: ${feature.properties.incidentname || 'N/A'}</strong><br>所在县: ${feature.properties.poocounty || '未知'}`
        },
        {
          name: 'earthquakes',
          displayName: '全球地震',
          tableName: 'disaster_map:global_earthquakes_last_week',
          style: { radius: 5, fillColor: "#FFA500", color: "#000", weight: 1, opacity: 1, fillOpacity: 0.7 },
          createPopupContent: (feature) => `<strong>地点: ${feature.properties.place || 'N/A'}</strong><br>震级: ${feature.properties.mag || '未知'}`
        },
        {
          name: 'hurricanes',
          displayName: '活动飓风',
          tableName: 'disaster_map:active_hurricanes',
          style: { radius: 8, fillColor: "#4169E1", color: "#000", weight: 1, opacity: 1, fillOpacity: 0.8 },
          createPopupContent: (feature) => `<strong>飓风名称: ${feature.properties.stormname || 'N/A'}</strong><br>风速: ${feature.properties.intensity || '未知'} KPH`
        }
      ],
    };
  },
  watch: {
    hurricaneLayer(newLayerInfo) {
        this.updateHurricaneLayer(newLayerInfo);
    }
  },
  mounted() {
    this.initMap();
    this.loadAllLayers();
    this.$emit('region-selected', 'California');
  },
  beforeUnmount() {
    if (this.map) {
      this.map.remove();
    }
  },
  methods: {
    initMap() {
      this.map = L.map('map').setView([30, -50], 3);
      L.tileLayer('http://webrd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=7&x={x}&y={y}&z={z}', {
          subdomains: ['1', '2', '3', '4'],
          attribution: '&copy; <a href="https://www.amap.com/">高德地图</a>'
      }).addTo(this.map);
    },
    loadAllLayers() {
      this.wfsLayers.forEach(layer => this.map.removeLayer(layer));
      this.wfsLayers = [];
      Object.keys(this.layerStatuses).forEach(key => delete this.layerStatuses[key]);

      this.layersConfig.forEach(config => {
        this.loadWfsLayer(config);
      });
    },
    async loadWfsLayer(config) {
      this.layerStatuses[config.name] = { 
          displayName: config.displayName, 
          message: '加载中...',
          className: 'status-loading'
      };

      const params = new URLSearchParams({
        service: 'WFS', version: '1.0.0', request: 'GetFeature',
        typeName: config.tableName, outputFormat: 'application/json', srsName: 'EPSG:4326'
      });
      const wfsUrl = `${this.geoServerBaseUrl}?${params.toString()}`;

      try {
        const response = await fetch(wfsUrl);
        if (!response.ok) throw new Error(`Network response: ${response.statusText}`);
        
        const geojsonData = await response.json();
        if (!geojsonData || !geojsonData.features) throw new Error("Invalid GeoJSON response");
        
        const featureCount = geojsonData.features.length;
        this.layerStatuses[config.name].message = `加载了 ${featureCount} 个要素`;
        this.layerStatuses[config.name].className = featureCount > 0 ? 'status-success' : 'status-empty';

        if (featureCount > 0) {
            const wfsLayer = L.geoJSON(geojsonData, {
              pointToLayer: (feature, latlng) => L.circleMarker(latlng, config.style),
              onEachFeature: (feature, layer) => layer.bindPopup(config.createPopupContent(feature))
            }).addTo(this.map);
            this.wfsLayers.push(wfsLayer);
        }
      } catch (error) {
        console.error(`Error loading ${config.displayName}:`, error);
        this.layerStatuses[config.name].message = '加载失败';
        this.layerStatuses[config.name].className = 'status-error';
      }
    },
    updateHurricaneLayer(layerInfo) {
        if (this.wmsLayer) {
            this.map.removeLayer(this.wmsLayer);
            this.wmsLayer = null;
        }
        
        if (layerInfo && layerInfo.name) {
            this.legendError = false; 
            this.wfsLayers.forEach(layer => this.map.removeLayer(layer));
            this.wfsLayers = [];
            Object.keys(this.layerStatuses).forEach(key => delete this.layerStatuses[key]);

            const wmsLayerName = `hurricane_map:${layerInfo.name}`;
            const wmsStyleName = layerInfo.style;

            this.wmsLayer = L.tileLayer.wms(this.hurricaneGeoServerBaseUrl, {
                layers: wmsLayerName,
                styles: wmsStyleName,
                format: 'image/png',
                transparent: true,
                version: '1.1.0',
                opacity: layerInfo.opacity
            }).addTo(this.map);
            
            const params = new URLSearchParams({
                SERVICE: 'WMS',
                VERSION: '1.1.0',
                REQUEST: 'GetLegendGraphic',
                LAYER: wmsLayerName,
                STYLE: wmsStyleName,
                FORMAT: 'image/png',
                LEGEND_OPTIONS: 'hideEmptyRules:true;forceLabels:off' // 尝试关闭GeoServer的标签
            });
            this.legendGraphicUrl = `${this.hurricaneGeoServerBaseUrl}?${params.toString()}`;
            
            // 查找并设置当前图例的数值
            this.activeLegendValues = this.legendValueData[layerInfo.name] || null;

            this.layerStatuses['hurricane'] = {
                displayName: `飓风图层 (${layerInfo.name})`,
                message: '加载成功',
                className: 'status-success'
            };
        } else {
            this.legendGraphicUrl = null;
            this.activeLegendValues = null;
            this.loadAllLayers();
        }
    },
    handleLegendError() {
      console.error("Failed to load legend graphic from GeoServer.");
      this.legendError = true;
    }
  }
}
</script>

<style scoped>
.map-container {
  position: relative;
  padding: 24px;
  background-color: #f8f9fa;
  border-radius: 8px;
  text-align: center;
}
.map-title {
  color: #2C7BE5;
  margin-bottom: 16px;
}
.map-area {
  width: 100%;
  height: 500px;
  border-radius: 8px;
  border: 1px solid #ced4da;
  z-index: 1;
}
.map-overlay {
  position: absolute;
  background: rgba(255, 255, 255, 0.85);
  padding: 10px 15px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  z-index: 1000;
  text-align: left;
}
.legend {
  bottom: 40px;
  right: 40px;
}
.status-panel {
  top: 20px;
  right: 20px;
  max-width: 220px;
}
.map-overlay h4 {
  margin: 0 0 10px 0;
  font-size: 14px;
  border-bottom: 1px solid #eee;
  padding-bottom: 5px;
}
.legend-item {
  display: flex;
  align-items: center;
  margin-bottom: 5px;
  font-size: 12px;
}
.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  margin-right: 8px;
  border: 1px solid #ccc;
  flex-shrink: 0;
}
.status-item {
  display: flex;
  align-items: center;
  margin-bottom: 5px;
  font-size: 12px;
}
.status-item strong {
    margin-right: 5px;
}
.status-success { color: #28a745; }
.status-empty { color: #6c757d; }
.status-error { color: #dc3545; font-weight: bold; }
.status-loading { color: #007bff; }

.geoserver-legend {
    bottom: 40px;
    left: 40px;
    padding: 5px;
}
.geoserver-legend img {
    display: block;
    max-width: 200px;
}
.legend-error-panel {
    bottom: 40px;
    left: 40px;
    padding: 10px 15px;
}
.legend-error-panel p {
    margin: 0;
    color: #dc3545;
    font-weight: 500;
    font-size: 13px;
}

/* --- 步骤 4: 为混合图例添加新样式 --- */
.hybrid-legend {
    padding: 0;
    background: transparent;
    box-shadow: none;
}
.legend-content {
    position: relative;
    display: inline-block;
}
.legend-labels {
    position: absolute;
    top: 0;
    left: 100%;
    height: 100%;
    margin-left: 5px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    font-size: 12px;
    font-weight: 500;
    color: #333;
}
.label-max {
    position: absolute;
    top: -5px;
}
.label-min {
    position: absolute;
    bottom: -5px;
}
</style>
