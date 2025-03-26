import { createRouter, createWebHistory } from 'vue-router';
import Home from '@/views/Home.vue';
import Analysis from '@/views/Analysis.vue';
import History from '@/views/History.vue';

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/analysis',
    name: 'Analysis',
    component: Analysis
  },
  {
    path: '/analysis/:id',
    name: 'AnalysisDetails',
    component: Analysis,
    props: true
  },
  {
    path: '/history',
    name: 'History',
    component: History
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;
