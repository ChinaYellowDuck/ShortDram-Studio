<script setup lang="ts">
import { Refresh } from '@element-plus/icons-vue'
import { onMounted } from 'vue'

import { useAppStore } from '../stores/app'

const store = useAppStore()

onMounted(() => {
  store.refresh()
})

function statusType(status: string | undefined): 'success' | 'danger' | 'warning' | 'info' {
  if (status === 'healthy' || status === 'running') return 'success'
  if (status === 'unhealthy') return 'danger'
  if (status === 'degraded') return 'warning'
  return 'info'
}
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2>工作台</h2>
      <el-button :icon="Refresh" :loading="store.loading" @click="store.refresh()">
        刷新
      </el-button>
    </div>

    <el-alert
      v-if="store.error"
      type="error"
      :closable="false"
      title="后端连接异常"
      :description="store.error"
      style="margin-bottom: 16px"
    />

    <el-row :gutter="16">
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>应用信息</template>
          <el-descriptions :column="1" v-if="store.root">
            <el-descriptions-item label="名称">{{ store.root.name }}</el-descriptions-item>
            <el-descriptions-item label="版本">{{ store.root.version }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="statusType(store.root.status)">{{ store.root.status }}</el-tag>
            </el-descriptions-item>
          </el-descriptions>
          <el-empty v-else description="未获取到应用信息" :image-size="60" />
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>服务健康</template>
          <template v-if="store.health">
            <p>
              总体状态：
              <el-tag :type="statusType(store.health.status)">{{ store.health.status }}</el-tag>
              <span class="env-label">env: {{ store.health.env }}</span>
            </p>
            <el-descriptions :column="1">
              <el-descriptions-item label="PostgreSQL">
                <el-tag :type="statusType(store.health.services.database.status)" size="small">
                  {{ store.health.services.database.status }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="Redis">
                <el-tag :type="statusType(store.health.services.redis.status)" size="small">
                  {{ store.health.services.redis.status }}
                </el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </template>
          <el-empty v-else description="未获取到健康状态" :image-size="60" />
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>LangSmith 追踪</template>
          <template v-if="store.langsmith">
            <p>
              状态：
              <el-tag :type="store.langsmith.enabled ? 'success' : 'info'">
                {{ store.langsmith.enabled ? '已启用' : '未启用' }}
              </el-tag>
            </p>
            <el-descriptions :column="1" v-if="store.langsmith.enabled">
              <el-descriptions-item label="项目">
                {{ store.langsmith.project }}
              </el-descriptions-item>
              <el-descriptions-item label="端点">
                {{ store.langsmith.endpoint }}
              </el-descriptions-item>
            </el-descriptions>
          </template>
          <el-empty v-else description="未获取到 LangSmith 状态" :image-size="60" />
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="hover" style="margin-top: 16px">
      <template #header>快速入口</template>
      <el-space wrap>
        <router-link to="/projects"><el-button>创建短剧项目</el-button></router-link>
        <router-link to="/llm-configs"><el-button>配置 LLM</el-button></router-link>
        <router-link to="/agents"><el-button>测试智能体</el-button></router-link>
        <a href="/docs" target="_blank"><el-button type="primary" plain>后端 API 文档</el-button></a>
      </el-space>
    </el-card>
  </div>
</template>

<style scoped>
.env-label {
  margin-left: 12px;
  color: #909399;
  font-size: 12px;
}
</style>
