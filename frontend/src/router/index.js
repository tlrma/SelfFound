import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [],
})

export default router
import ReportForm from '../views/ReportForm.vue'
import ReportStatus from '../views/ReportStatus.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'ReportForm',
      component: ReportForm
    },
    {
      path: '/status/:id',
      name: 'ReportStatus',
      component: ReportStatus
    }
  ]
})

export default router
