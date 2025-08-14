import { createRouter, createWebHistory } from 'vue-router';
import HomePage from '../components/HomePage.vue';
import MainContent from '../components/MainContent.vue';
import Models_Database from '@/components/Models_Database.vue';
import ModelDetail from '@/components/ModelDetail.vue';
// 1. 导入新的使用说明组件
import UsageInstructions from '@/components/UsageInstructions.vue';

const routes = [
  {
    path: '/',
    name: 'Home',
    component: HomePage,
  },
  {
    path: '/models',
    name: 'Models',
    component: MainContent,
  },
  {
    path: '/models-database',
    name: 'Models_Database',
    component: Models_Database,
  },
  {
    path: '/model/:id',
    name: 'ModelDetail',
    component: ModelDetail,
    props: true 
  },
  // 2. 为使用说明页添加新的路由规则
  {
    path: '/usage-instructions',
    name: 'UsageInstructions',
    component: UsageInstructions,
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
