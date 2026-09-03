import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: () => import('../views/DashboardView.vue'),
      meta: { title: '工作台' },
    },
    {
      path: '/projects',
      name: 'projects',
      component: () => import('../views/ProjectsView.vue'),
      meta: { title: '项目管理' },
    },
    {
      path: '/projects/:projectId/script',
      name: 'script-editor',
      component: () => import('../views/ScriptEditorView.vue'),
      meta: { title: '剧本编辑器', hiddenSidebar: true },
    },
    {
      path: '/llm-configs',
      name: 'llm-configs',
      component: () => import('../views/LlmConfigsView.vue'),
      meta: { title: 'LLM 配置' },
    },
    {
      path: '/agents',
      name: 'agents',
      component: () => import('../views/AgentsView.vue'),
      meta: { title: '智能体' },
    },
  ],
})

router.afterEach((to) => {
  const title = to.meta.title as string | undefined
  document.title = title ? `${title} - ShortDram Studio` : 'ShortDram Studio'
})

export default router
