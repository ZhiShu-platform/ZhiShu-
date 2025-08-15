import { createRouter, createWebHistory } from 'vue-router';
import HomePage from '../components/HomePage.vue';
import MainContent from '../components/MainContent.vue';
import Models_Database from '@/components/Models_Database.vue';
import ModelDetail from '@/components/ModelDetail.vue';
import UsageInstructions from '@/components/UsageInstructions.vue';
import FarsiteDetail from '@/components/FarsiteDetail.vue';
// 1. 导入新的RAWS详情组件
import RawsDetail from '@/components/RawsDetail.vue';

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
  {
    path: '/model/wf-farsite',
    name: 'FarsiteDetail',
    component: FarsiteDetail,
  },
  // 2. 为RAWS详情页添加新的路由规则
  {
    path: '/dataset/ds-09', // 使用数据集的唯一ID作为路径
    name: 'RawsDetail',
    component: RawsDetail,
  },
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