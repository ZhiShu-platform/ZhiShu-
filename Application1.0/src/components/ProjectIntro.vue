<template>
  <div class="project-intro">
    <h1>项目背景</h1>
    <p>智能化应急减灾是应对突发灾害的关键手段，对于提升国家的灾害应对能力具有重要意义。“空-天-地-人-网”等多种技术手段和渠道为智能化应急减灾提供了丰富的数据支撑，有助于完成灾害隐患识别、灾害风险研判和灾情评估等不同的应急任务。然而，现有的应急模型主要面向单模态数据和单一任务，存在多模态数据协同性与系统性分析不足、通用性低和时效性差等问题</p>
  </div>
  <div class="project-intro">
    <h1>项目简介</h1>
    <p>智枢多模态应急减灾智能平台，基于哈工大优势学科，深度融合卫星遥感、产业分布、物联网感知、社交媒体等多源异构数据，构建了包括洪水模型，气象模型，地震模型，野火模型等在内的智能体集群，精确识别灾情、量化评估灾损，实现灾害管理，填补我国巨灾模型多智能体平台的空白</p>
  </div>
  
</template>

<script>
export default {
  name: 'ProjectIntro'
}
</script>

<style scoped>
.project-intro {
  padding: 32px;
  max-width: 800px;
  margin: 0 auto;
}
h1 {
  color: var(--primary-color-darker);
  margin-bottom: 16px;
  border-bottom: 2px solid var(--primary-color);
  padding-bottom: 8px;
}
p {
  
  font-size: 16px; 
  line-height: 1.8;
  color: var(--text-color-light);
}
</style> 
