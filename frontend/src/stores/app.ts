import { defineStore } from 'pinia'
import { ref } from 'vue'

import { getHealth, getLangsmithStatus, getRoot } from '../api/health'
import type { HealthStatus, LangsmithStatus, RootInfo } from '../api/types'

/** 全局应用状态：后端服务健康信息 */
export const useAppStore = defineStore('app', () => {
  const root = ref<RootInfo | null>(null)
  const health = ref<HealthStatus | null>(null)
  const langsmith = ref<LangsmithStatus | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function refresh() {
    loading.value = true
    error.value = null
    try {
      const [rootRes, healthRes, langsmithRes] = await Promise.allSettled([
        getRoot(),
        getHealth(),
        getLangsmithStatus(),
      ])
      root.value = rootRes.status === 'fulfilled' ? rootRes.value : null
      health.value = healthRes.status === 'fulfilled' ? healthRes.value : null
      langsmith.value = langsmithRes.status === 'fulfilled' ? langsmithRes.value : null
      if (healthRes.status === 'rejected') error.value = String(healthRes.reason)
    } finally {
      loading.value = false
    }
  }

  return { root, health, langsmith, loading, error, refresh }
})
