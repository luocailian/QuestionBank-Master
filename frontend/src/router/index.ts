import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/HomeView.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/auth/LoginView.vue'),
      meta: { requiresAuth: false, hideForAuth: true }
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/auth/RegisterView.vue'),
      meta: { requiresAuth: false, hideForAuth: true }
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('@/views/DashboardView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/banks',
      name: 'banks',
      component: () => import('@/views/banks/BankListView.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/banks/:id',
      name: 'bank-detail',
      component: () => import('@/views/banks/BankDetailView.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/banks/:bankId/questions/:questionId',
      name: 'question-detail',
      component: () => import('@/views/questions/QuestionDetailView.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/banks/:bankId/questions/:questionId/edit',
      name: 'question-edit',
      component: () => import('@/views/questions/QuestionEditView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/practice/:bankId',
      name: 'practice',
      component: () => import('@/views/practice/PracticeView.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/practice/:bankId/session',
      name: 'practice-session',
      component: () => import('@/views/practice/PracticeSessionView.vue'),
      meta: { requiresAuth: false }
    },

    {
      path: '/favorites',
      name: 'favorites',
      component: () => import('@/views/user/FavoritesView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('@/views/user/ProfileView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/admin',
      name: 'admin',
      component: () => import('@/views/admin/AdminView.vue'),
      meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
      path: '/admin/banks',
      name: 'admin-banks',
      component: () => import('@/views/admin/BankManageView.vue'),
      meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
      path: '/admin/users',
      name: 'admin-users',
      component: () => import('@/views/admin/UserManageView.vue'),
      meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/views/NotFoundView.vue')
    }
  ]
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  // 检查是否需要登录
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'login', query: { redirect: to.fullPath } })
    return
  }
  
  // 检查是否需要管理员权限
  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    next({ name: 'dashboard' })
    return
  }
  
  // 已登录用户访问登录/注册页面时重定向到仪表板
  if (to.meta.hideForAuth && authStore.isAuthenticated) {
    next({ name: 'dashboard' })
    return
  }
  
  next()
})

export default router
