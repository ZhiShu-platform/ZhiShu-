<template>
  <header>
    <div class="logo">
      <img src="\logo1.png" alt="图片" style="height: 50px; margin-right: 12px; cursor: pointer;">
      <h1 @click="goHome" style="cursor: pointer;margin: 8px 0;">智枢多模态应急减灾智能平台</h1>
      
      <!-- Simplified Navigation -->
      <div class="nav-items">
        <button class="nav-btn" @click="goToModelsDatabase">模型库&数据集</button>
        <button class="nav-btn" @click="goToModels">模型选择</button>
      </div>
    </div>
    
    <div class="user-action">
      <template v-if="isLoggedIn">
        <span class="username">{{ username }}</span>
        <button class="logout-btn" @click="$emit('logout')">退出</button>
      </template>
      <template v-else>
        <button class="login-btn" @click="$emit('login')">登录/注册</button>
      </template>
    </div>
  </header>
</template>

<script>
export default {
  props: {
    isLoggedIn: {
      type: Boolean,
      default: false
    },
    username: {
      type: String,
      default: ''
    }
  },
  emits: ['login', 'logout'],
  methods: {
    goHome() {
      this.$router.push('/');
    },
    goToModels() {
      this.$router.push('/models');
    },
    goToModelsDatabase(){
      this.$router.push('/models-database');
    }
  }
}
</script>

<style scoped>
header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  background: #fff;
  color: #2C7BE5;
  height: 64px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  position: relative;
  z-index: 1000;
}
.logo {
  display: flex;
  align-items: center;
}
.logo-icon {
  width: 36px;
  height: 36px;
  background: #2C7BE5;
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  font-weight: bold;
  margin-right: 12px;
}
.nav-items {
  display: flex;
  align-items: center;
  margin-left: 24px;
}
.nav-btn {
  margin-left: 8px;
  background: transparent;
  color: #333;
  border: none;
  border-radius: 4px;
  padding: 6px 16px;
  cursor: pointer;
  font-size: 15px;
  font-weight: 500;
  transition: color .2s;
}
.nav-btn:hover {
  color: #2C7BE5;
}
.user-action {
  display: flex;
  align-items: center;
  gap: 12px;
}
.login-btn, .logout-btn {
  background: transparent;
  color: #2C7BE5;
  border: 1px solid #2C7BE5;
  border-radius: 4px;
  padding: 6px 16px;
  cursor: pointer;
  font-size: 15px;
  font-weight: 500;
  transition: background .2s, color .2s;
}
.login-btn:hover, .logout-btn:hover {
  background: #2C7BE5;
  color: #fff;
}
.username {
  font-size: 15px;
  font-weight: 500;
}
</style>
