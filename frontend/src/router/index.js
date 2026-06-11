import { createRouter, createWebHistory } from 'vue-router'
import ReportForm from '../views/ReportForm.vue'
import ReportStatus from '../views/ReportStatus.vue'
import AdminDashboard from '../views/AdminDashboard.vue'
import UserAuth from '../views/UserAuth.vue'
import UserReportList from '../views/UserReportList.vue'

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
    },
    {
      path: '/admin',
      name: 'AdminDashboard',
      component: AdminDashboard
    },
    {
      path: '/auth', 
      name: 'UserAuth', 
      component: UserAuth 
    },
    { 
      path: '/my-reports', 
      name: 'UserReportList', 
      component: UserReportList 
    }
  ]
})

export default router
