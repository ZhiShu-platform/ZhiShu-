<script>
import AppHeader from './components/AppHeader.vue'
import LoginRegister from './components/LoginRegister.vue'

export default {
  components: {
    AppHeader,
    LoginRegister
  },
  data() {
    return {
      isLoggedIn: false,
      username: '',
      showLoginDialog: false,
    }
  },
  methods: {
    handleLoginClick() {
      this.showLoginDialog = true;
    },
    handleLogoutClick() {
      this.isLoggedIn = false;
      this.username = '';
      // Redirect to home page on logout
      if (this.$route.path !== '/') {
        this.$router.push('/');
      }
    },
    handleLoginSuccess(payload) {
      this.isLoggedIn = true;
      this.username = payload.username;
      this.showLoginDialog = false;

      // Part 1.1 优化建议:
      // 对于已认证的专业用户，完全绕过 HomePage 的动画展示，
      // 直接将他们引导至一个功能性的、以任务为导向的中央仪表盘。
      this.$router.push('/models');
    },
    handleLoginDialogClose() {
      this.showLoginDialog = false;
    },
  }
}
</script>

<template>
  <div id="app-container">
    <AppHeader 
      :isLoggedIn="isLoggedIn"
      :username="username"
      @login="handleLoginClick"
      @logout="handleLogoutClick"
    />
    
    <main class="main-content-area">
      <router-view 
          :isLoggedIn="isLoggedIn"
          :username="username"
          @show-login="handleLoginClick"
      />
    </main>
    
    <LoginRegister 
      :visible="showLoginDialog" 
      @success="handleLoginSuccess" 
      @close="handleLoginDialogClose" 
    />
  </div>
</template>


<style>
/* 引入 Leaflet 的核心 CSS */
@import "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";

/* 将部分全局样式移至 main.css，这里保留应用布局相关的样式 */
#app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}
.main-content-area {
  flex-grow: 1;
  /* 为内容区域添加通用内边距，可以根据页面需要覆盖 */
  padding: 24px 32px; 
  background-color: #f8f9fa;
}

/* 针对首页，移除内边距使其全屏 */
.homepage-container .main-content-area {
  padding: 0;
}
</style>
