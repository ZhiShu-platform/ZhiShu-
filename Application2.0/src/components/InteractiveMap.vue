<template>
  <div class="map-container">
    <h3 class="map-title">请在地图上选择要分析的区域</h3>
    <div class="map-area">
      <!-- This is a simplified SVG map for demonstration. You can replace it with a real map library like Leaflet or OpenLayers. -->
      <svg viewBox="0 0 800 450" class="interactive-svg-map">
        <!-- Background -->
        <rect width="100%" height="100%" fill="#a2d9ff" />

        <!-- A clickable region representing California -->
        <path 
          d="M110 150 C 90 200, 100 250, 120 300 L 150 320 L 180 280 C 190 220, 160 160, 110 150 Z" 
          class="map-region"
          @click="selectRegion('california')"
        />
        <text x="105" y="240" class="map-label">加州地区</text>

        <!-- Placeholder for other regions -->
        <circle cx="400" cy="200" r="50" class="map-region inactive" />
        <text x="375" y="205" class="map-label inactive">其他区域</text>

        <!-- Visual Layers (e.g., Heatmap) shown after analysis -->
        <g v-if="visualLayers.heatmap" class="heatmap-layer">
           <circle cx="130" cy="200" r="40" fill="red" opacity="0.5" />
           <circle cx="150" cy="250" r="25" fill="orange" opacity="0.6" />
        </g>
      </svg>
      <div class="map-legend">
        <div class="legend-item"><span class="legend-color" style="background-color: rgba(255, 0, 0, 0.5);"></span>高风险热点</div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'InteractiveMap',
  props: {
    visualLayers: {
      type: Object,
      default: () => ({ heatmap: false })
    }
  },
  emits: ['region-selected'],
  methods: {
    selectRegion(regionName) {
      this.$emit('region-selected', regionName);
    }
  }
}
</script>

<style scoped>
.map-container {
  padding: 24px;
  background-color: #f8f9fa;
  border-radius: 8px;
  margin-bottom: 24px;
}
.map-title {
  text-align: center;
  color: #2C7BE5;
  margin-bottom: 16px;
}
.map-area {
  position: relative;
  width: 100%;
  height: 0;
  padding-bottom: 56.25%; /* 16:9 Aspect Ratio */
  background-color: #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
}
.interactive-svg-map {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}
.map-region {
  fill: #4caf50;
  stroke: #fff;
  stroke-width: 2;
  cursor: pointer;
  transition: fill 0.2s;
}
.map-region:hover {
  fill: #66bb6a;
}
.map-region.inactive {
    fill: #bdbdbd;
    cursor: not-allowed;
}
.map-label {
  font-size: 16px;
  fill: white;
  font-weight: bold;
  pointer-events: none; /* Makes text non-interactive */
}
.map-label.inactive {
    fill: #616161;
}
.heatmap-layer {
    animation: fadeIn 0.5s ease-in-out;
}
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
.map-legend {
    position: absolute;
    bottom: 10px;
    right: 10px;
    background: rgba(255,255,255,0.8);
    padding: 8px;
    border-radius: 6px;
    font-size: 12px;
}
.legend-item {
    display: flex;
    align-items: center;
}
.legend-color {
    width: 16px;
    height: 16px;
    border-radius: 50%;
    margin-right: 8px;
    border: 1px solid #ccc;
}
</style>
