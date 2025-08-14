<template>
  <div class="instructions-page">
    <div class="header">
      <h1>模型使用说明</h1>
      <p>本指南旨在帮助您理解和有效使用平台上的灾害模型。</p>
    </div>
    <div class="content">
      <div class="section">
        <h2>下载安装</h2>
        <p></p>
      </div>
      <div class="section">
        <h2>环境搭建</h2>
        <p></p>
      </div>
       <div class="section">
        <h2>输入数据说明</h2>
        <p></p>
      </div>
      <div class="section">
        <h2>使用说明</h2>
        <p></p>
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
      // 导航回上一个访问的页面
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

.section p {
  font-size: 15px;
  line-height: 1.8;
  color: #555;
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
