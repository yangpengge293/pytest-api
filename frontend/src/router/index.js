import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/cases',
  },
  {
    path: '/cases',
    name: 'CaseList',
    component: () => import('../views/CaseList.vue'),
    meta: { title: '用例管理' },
  },
  {
    path: '/suites',
    name: 'SuiteList',
    component: () => import('../views/SuiteList.vue'),
    meta: { title: '套件管理' },
  },
  {
    path: '/executions',
    name: 'ExecutionList',
    component: () => import('../views/ExecutionList.vue'),
    meta: { title: '执行记录' },
  },
  {
    path: '/executions/:id',
    name: 'ExecutionDetail',
    component: () => import('../views/ExecutionDetail.vue'),
    meta: { title: '执行详情' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
