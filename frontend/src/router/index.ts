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
      path: '/projects/:projectId/workspace',
      name: 'project-workspace',
      component: () => import('../views/ProjectWorkspaceView.vue'),
      meta: { title: '项目工作台', hiddenSidebar: true },
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
    {
      path: '/mcps',
      name: 'mcps',
      component: () => import('../views/McpView.vue'),
      meta: { title: 'MCP 管理' },
    },
    {
      path: '/skills',
      name: 'skills',
      component: () => import('../views/SkillView.vue'),
      meta: { title: 'Skill 管理' },
    },
  ],
})

router.afterEach((to) => {
  const title = to.meta.title as string | undefined
  document.title = title ? `${title} - ShortDram Studio` : 'ShortDram Studio'
})

export default router
