<template>
  <div class="model-detail-page">
    <div class="page-header">
      <h1>Farsite：森林火灾蔓延的模拟利器</h1>
      <p class="subtitle">一个基于物理学的、多维度的火灾蔓延模拟系统</p>
      [cite_start]<p class="intro">Farsite模型由美国林务局开发，能够利用GIS数据，结合气象、地形和植被等多种因素，动态地模拟火灾在三维空间中的蔓延过程，是世界各地森林防火专家、研究人员和规划者不可或缺的工具。[cite: 125]</p>
    </div>

    <div class="content-section">
      <h2>核心工作原理</h2>
      [cite_start]<p>Farsite模型的强大之处在于它将多种科学原理和经验模型巧妙地结合起来，以实现对火灾蔓延过程的精确模拟。其核心工作原理可以概括为以下几个关键点：[cite: 127]</p>
      <ul>
        [cite_start]<li><strong>火灾蔓延的物理基础</strong>：遵循Rothermel经验模型，该模型利用燃料类型、含水率、风速和坡度等变量来计算火灾的蔓延速率。[cite: 128]</li>
        [cite_start]<li><strong>Huygens原理的应用</strong>：创造性地用来模拟火头前锋的“波前”，每个着火的单元都被视为一个新的“点火源”，从而生成随时间变化的、复杂且真实的火头形状。[cite: 129]</li>
        [cite_start]<li><strong>多维度的影响因素</strong>：整合了燃料模型、地形数据（坡度、坡向）、植被覆盖和动态气象数据（风、温、湿）等多层地理数据，形成一个全面的火灾环境。[cite: 130, 131, 132, 133, 134]</li>
      </ul>
    </div>

    <div class="content-section">
        <h2>关键功能与应用</h2>
        <div class="gallery-grid">
            <div class="feature-card">
                <h3>火灾行为预测</h3>
                [cite_start]<p>生成随时间变化的火灾边界图，并输出蔓延速率、火线强度和火焰长度等关键参数，为决策提供直观数据。[cite: 139, 140, 141, 142]</p>
            </div>
            <div class="feature-card">
                <h3>规划火灾管理策略</h3>
                [cite_start]<p>通过模拟评估扑救资源部署、规划隔离带效果或模拟计划烧除，帮助管理者制定更科学的应急方案。[cite: 144, 145, 146, 147]</p>
            </div>
            <div class="feature-card">
                <h3>评估火灾影响</h3>
                [cite_start]<p>广泛应用于火灾生态学研究，评估火灾对植被、土壤、水资源和野生动物栖息地的潜在影响，并进行风险评估。[cite: 149, 150, 151]</p>
            </div>
        </div>
    </div>
    
    <div class="content-section">
      <h2>局限性与发展方向</h2>
      [cite_start]<p>尽管Farsite功能强大，但其模拟结果高度依赖输入数据的质量，并且对火灾物理学（如林冠火）进行了一定简化。[cite: 153, 154, 156] [cite_start]未来，模型将整合更先进的物理模型（如CFD），并利用更高分辨率的实时数据，进行更快速、更精细的模拟。[cite: 157]</p>
    </div>

    <div class="page-footer">
      <a href="https://github.com/mbedward/farsite" target="_blank" rel="noopener noreferrer" class="footer-btn link-btn">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path></svg>
        <span>访问 Farsite on GitHub</span>
      </a>
    </div>

  </div>
</template>

<script>
export default {
  name: 'FarsiteDetail',
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

.gallery-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 24px;
    margin-top: 24px;
}

.feature-card {
    background-color: #f8f9fa;
    padding: 24px;
    border-radius: 8px;
    border: 1px solid #e0e6ed;
}

.feature-card h3 {
    font-size: 18px;
    font-weight: 600;
    margin: 0 0 12px 0;
}

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

.link-btn {
  background-color: #333;
  color: #fff;
  border-color: #333;
}
.link-btn:hover {
  background-color: #000;
  transform: translateY(-2px);
}
</style>