<template>
  <div class="instructions-page">
    <div class="header">
      <h1>CLIMADA 模型使用说明</h1>
      <p>本指南旨在帮助您理解和有效使用CLIMADA模型进行气候风险评估。</p>
    </div>
    <div class="content">
      <div class="section">
        <h2>简介</h2>
        <p>CLIMADA (CLIMate ADAptation) 是一个免费的开源软件框架，用于气候风险评估和适应方案评估 。它由庞大的科学界共同设计，旨在帮助研究人员、政策制定者和企业分析自然灾害的影响并探索适应策略 。</p>
        <p>CLIMADA分为两部分：核心模块 <strong>climada_python</strong> (用于概率影响、损害计算等) 和花瓣模块 <strong>climada_petals</strong> (用于生成灾害数据，如野火、风暴潮等) 。建议新用户从核心模块及其教程开始 。</p>
      </div>

      <div class="section">
        <h2>环境部署</h2>
        <p>Climada对环境没有复杂的要求 。我们选择将其部署在Conda环境中，并使用Jupyter Notebook运行脚本文件 </p>
      </div>

       <div class="section">
        <h2>输入数据说明</h2>
        <p>要使用Climada进行火灾灾损计算，主要需要三部分输入文件：</p>
        <ul>
            <li><strong>BlackMarble数据集</strong>：夜间灯光数据集，包含了四个名为 `BlackMarble_2016_A1_geo_gray.tif` 的栅格数据文件 。</li>
            <li><strong>GPW全球人口网格数据集</strong>：名为 `gpw-v4-population-count-rev11_2020_30_sec_tif` 的栅格数据文件 。</li>
            <li><strong>FIRMS数据集</strong>：来自NASA的遥感数据集，用于生成起火点。具体文件名为 `fire_archive_M-C61_106125.csv` 。</li>
        </ul>
      </div>

      <div class="section">
        <h2>使用说明</h2>
        <p>1. <strong>安装依赖</strong>：首先需要安装climada核心库和花瓣库。在命令行界面输入： <code>pip install climada_petals</code> 。</p>
        <p>2. <strong>获取数据和脚本</strong>：从以下网盘链接中获取输入数据和运行脚本 `run_climada.ipynb` 。</p>
        <div class="link-box">
            <p><strong>网盘链接</strong>: <a href="https://pan.baidu.com/s/1nKBwmlfDEGO9s7XLLuuL5g?pwd=2025" target="_blank">https://pan.baidu.com/s/1nKBwmlfDEGO9s7XLLuuL5g?pwd=2025</a></p>
            <p><strong>提取码</strong>: 2025</p>
        </div>
        <p>3. <strong>修改路径</strong>：在 `run_climada.ipynb` 脚本中，将所有文件路径更改为您本地的实际存放路径 。</p>
        <p>4. <strong>运行脚本</strong>：运行Jupyter Notebook脚本即可得到所有图形化的输出结果 。</p>
      </div>

       <div class="section">
        <h2>更多信息</h2>
        <p>若用户想要了解更多有关climada的信息，可以阅读官方文档。climada_python的GitHub仓库链接为：</p>
        <div class="link-box">
            <a href="https://github.com/CLIMADA-project/climada_python.git" target="_blank" rel="noopener noreferrer" class="repo-link">
                https://github.com/CLIMADA-project/climada_python.git
            </a>
        </div>
      </div>
    </div>
     <div class="footer-actions">
      <button @click="goBack" class="action-btn">返回上一页</button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'UsageInstructions',
  methods: {
    goBack() {
      this.$router.go(-1);
    }
  }
}
</script>

<style scoped>
.instructions-page {
  padding: 32px;
  max-width: 900px;
  margin: 24px auto;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

.header {
  text-align: center;
  margin-bottom: 40px;
  border-bottom: 1px solid #e0e6ed;
  padding-bottom: 24px;
}

.header h1 {
  font-size: 28px;
  font-weight: 700;
  color: #2C7BE5;
}

.header p {
  font-size: 16px;
  color: #6c757d;
  margin-top: 8px;
}

.content {
  display: grid;
  gap: 28px;
}

.section {
  background-color: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  border-left: 4px solid #2C7BE5;
}

.section h2 {
  font-size: 20px;
  font-weight: 600;
  color: #333;
  margin-bottom: 12px;
}

.section p, .section ul {
  font-size: 15px;
  line-height: 1.8;
  color: #555;
}

.section ul {
    padding-left: 20px;
    margin-top: 10px;
}
.section ul li {
    margin-bottom: 8px;
}
.link-box {
    background-color: #e9ecef;
    padding: 15px;
    border-radius: 6px;
    margin-top: 12px;
    font-family: 'Courier New', Courier, monospace;
}
.repo-link, .link-box a {
    color: #0056b3;
    text-decoration: none;
}
.repo-link:hover, .link-box a:hover {
    text-decoration: underline;
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