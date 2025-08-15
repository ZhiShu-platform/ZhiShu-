<template>
  <div class="detail-page">
    <div class="page-header">
      <h1>RAWS气象站数据集简介</h1>
      <p class="intro">RAWS (Remote Automatic Weather Stations) 远程自动气象站是美国林务局、内政部土地管理局等机构为了监测和管理野外火灾而建立的网络，为火灾管理、科学研究和日常气象监测提供关键数据。 </p>
    </div>

    <div class="content-section">
      <h2>核心参数</h2>
      <p>每个RAWS气象站都配备了多种传感器，可以每小时甚至更频繁地自动收集并传输一系列重要的气象和环境参数，包括： </p>
      <ul>
        <li><strong>风速和风向</strong>：对火势蔓延至关重要。 </li>
        <li><strong>气温和相对湿度</strong>：直接影响燃料的含水率，进而影响火灾的可燃性。 </li>
        <li><strong>降水量</strong>：记录降雨量，有助于评估区域的干旱程度。 </li>
        <li><strong>太阳辐射</strong>：影响地表温度和燃料含水率。 </li>
        <li><strong>燃料含水率 (Fuel Moisture)</strong>：一些高级RAWS站能直接测量，是预测火灾风险最直接的指标之一。 </li>
      </ul>
      <p>这些数据被广泛应用于火灾行为模拟、火灾危险度评估、烟雾扩散预测以及气候变化研究等领域。 </p>
    </div>

    <div class="content-section">
        <h2>数据获取方式</h2>
        <p>数据可以通过 <a href="https://mesowest.utah.edu/cgi-bin/droman/mesomap.cgi?state=CA&rawsflag=3" target="_blank" rel="noopener noreferrer">MesoWest 网站</a> 获取。  以下是获取步骤：</p>
        
        <div class="step-card">
            <h4>1. 在左边侧边栏选择 "NWS and RAWS"</h4>
            <img src="/raws-step1.png" alt="RAWS数据获取步骤1">
        </div>
        <div class="step-card">
            <h4>2. 在右侧地图中选择你想要选择的站点</h4>
            <img src="/raws-step2.png" alt="RAWS数据获取步骤2">
        </div>
        <div class="step-card">
            <h4>3. 点击你选择的站点，在弹出框中选择 "Download Data"</h4>
            <img src="/raws-step3.png" alt="RAWS数据获取步骤3">
        </div>
        <div class="step-card">
            <h4>4. 在弹出页面中选择你想要的时间范围和数据格式</h4>
            <img src="/raws-step4.png" alt="RAWS数据获取步骤4">
        </div>
    </div>

     <div class="footer-actions">
      <button @click="goBack" class="action-btn">返回上一页</button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'RawsDetail',
  methods: {
    goBack() {
      this.$router.go(-1);
    }
  }
}
</script>

<style scoped>
.detail-page {
  padding: 32px;
  max-width: 900px;
  margin: 24px auto;
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
.page-header .intro {
  font-size: 16px;
  color: #6c757d;
  line-height: 1.7;
  max-width: 800px;
  margin: 16px auto 0;
}
.content-section {
    margin-bottom: 40px;
}
.content-section h2 {
    font-size: 24px;
    color: #333;
    margin-bottom: 16px;
    border-bottom: 2px solid #2C7BE5;
    padding-bottom: 8px;
    display: inline-block;
}
.content-section p, .content-section ul {
    font-size: 16px;
    line-height: 1.8;
    color: #555;
}
.content-section ul {
    padding-left: 20px;
}
.content-section ul li {
    margin-bottom: 8px;
}
.step-card {
    background-color: #f8f9fa;
    padding: 20px;
    border-radius: 8px;
    border: 1px solid #e0e6ed;
    margin-top: 20px;
}
.step-card h4 {
    margin: 0 0 16px 0;
}
.step-card img {
    max-width: 100%;
    border-radius: 4px;
    border: 1px solid #dee2e6;
}
.footer-actions {
  margin-top: 40px;
  text-align: center;
}
.action-btn {
  background-color: #2C7BE5;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 10px 24px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all .2s;
}
.action-btn:hover {
  background-color: #185fa3;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(44,123,229,0.2);
}
</style>