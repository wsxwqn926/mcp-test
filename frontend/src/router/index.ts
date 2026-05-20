import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/connection' },
    { path: '/connection', name: 'connection', component: () => import('../views/ConnectionView.vue') },
    { path: '/tools', name: 'tools', component: () => import('../views/ToolsView.vue') },
    { path: '/resources', name: 'resources', component: () => import('../views/ResourcesView.vue') },
    { path: '/prompts', name: 'prompts', component: () => import('../views/PromptsView.vue') },
    { path: '/messages', name: 'messages', component: () => import('../views/MessagesView.vue') },
    { path: '/tests', name: 'tests', component: () => import('../views/TestRunnerView.vue') },
    { path: '/validator', name: 'validator', component: () => import('../views/ValidatorView.vue') },
    { path: '/performance', name: 'performance', component: () => import('../views/PerformanceView.vue') },
    { path: '/compare', name: 'compare', component: () => import('../views/CompareView.vue') },
  ],
})

export default router
