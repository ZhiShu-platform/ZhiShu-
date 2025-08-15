// src/main.js
import { createApp } from 'vue';
import App from './App.vue';
import router from './router'; // Import the router
import './assets/main.css'; // Import your new global CSS

const app = createApp(App);

app.use(router); // Tell the app to use the router

app.mount('#app');
