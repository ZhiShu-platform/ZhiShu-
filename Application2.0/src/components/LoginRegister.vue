
<template>
  <div v-if="visible" class="modal-mask">
    <div class="modal-container">
      <h3>{{ isLoginMode ? '登录' : '注册' }}</h3>
      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label>用户名</label>
          <input v-model="username" required />
        </div>
        <div class="form-group">
          <label>密码</label>
          <input type="password" v-model="password" required />
        </div>
        <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
        <div class="form-actions">
          <button type="submit">{{ isLoginMode ? '登录' : '注册' }}</button>
          <button type="button" @click="$emit('close')">取消</button>
        </div>
      </form>
      <div class="switch-mode">
        <span v-if="isLoginMode">还没有账号？<a href="#" @click.prevent="switchMode(false)">注册</a></span>
        <span v-else>已有账号？<a href="#" @click.prevent="switchMode(true)">登录</a></span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    visible: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      isLoginMode: true,
      username: '',
      password: '',
      errorMessage: '' // 用于显示后端返回的错误信息
    }
  },
  methods: {
    async handleSubmit() {
      this.errorMessage = ''; // 重置错误信息

      if (!this.username || !this.password) {
        this.errorMessage = '请输入用户名和密码';
        return;
      }

      const apiUrl = `/api/${this.isLoginMode ? 'login' : 'register'}`;
      
      try {
        const response = await fetch(apiUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            username: this.username,
            password: this.password,
          }),
        });

        const data = await response.json();

        if (!response.ok) {
          // 如果HTTP状态码不是2xx，则抛出错误
          throw new Error(data.message || '操作失败');
        }

        // 注册成功后，提示用户并切换到登录模式
        if (!this.isLoginMode) {
          alert('注册成功！请登录。');
          this.isLoginMode = true;
          this.password = ''; // 清空密码
        } else {
          // 登录成功，触发 success 事件
          this.$emit('success', { username: data.user.username });
        }

      } catch (error) {
        // 显示后端返回的错误信息
        this.errorMessage = error.message;
        console.error('操作失败:', error);
      }
    },
    // 切换模式时清空错误信息
    switchMode(isLogin) {
        this.isLoginMode = isLogin;
        this.errorMessage = '';
        this.username = '';
        this.password = '';
    }
  }
}
</script>

<style scoped>
/* 原有样式 */
.modal-mask {
  position: fixed;
  z-index: 9999;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.25);
  display: flex;
  align-items: center;
  justify-content: center;
}
.modal-container {
  background: #fff;
  border-radius: 8px;
  padding: 32px 28px 18px 28px;
  min-width: 320px;
  box-shadow: 0 4px 24px rgba(44,123,229,0.12);
}
.form-group {
  margin-bottom: 18px;
}
.form-group label {
  display: block;
  margin-bottom: 6px;
  color: #2C7BE5;
  font-weight: 500;
}
.form-group input {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #d0d7de;
  border-radius: 4px;
  font-size: 15px;
}
.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}
.form-actions button {
  padding: 7px 22px;
  border: none;
  border-radius: 4px;
  background: #2C7BE5;
  color: #fff;
  font-size: 15px;
  cursor: pointer;
  transition: background .2s;
}
.form-actions button[type="button"] {
  background: #eee;
  color: #2C7BE5;
}
.form-actions button:hover {
  background: #185fa3;
}
.switch-mode {
  margin-top: 12px;
  text-align: right;
  font-size: 14px;
}
.switch-mode a {
  color: #2C7BE5;
  cursor: pointer;
  text-decoration: underline;
}
/* 新增错误信息样式 */
.error-message {
  color: #FF3B30; /* 红色 */
  font-size: 14px;
  margin-top: 10px;
  text-align: center;
}
</style>