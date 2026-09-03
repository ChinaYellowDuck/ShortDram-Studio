<script setup lang="ts">
import {
  ChatDotRound,
  Cpu,
  DataBoard,
  FolderOpened,
  Setting,
} from '@element-plus/icons-vue'
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const activeMenu = computed(() => route.path)
const hideSidebar = computed(() => Boolean(route.meta.hiddenSidebar))
</script>

<template>
  <el-container class="layout">
    <el-aside v-if="!hideSidebar" width="220px" class="sidebar">
      <div class="logo">🎬 ShortDram Studio</div>
      <el-menu :default-active="activeMenu" router class="menu">
        <el-menu-item index="/">
          <el-icon><DataBoard /></el-icon>
          <span>工作台</span>
        </el-menu-item>
        <el-menu-item index="/projects">
          <el-icon><FolderOpened /></el-icon>
          <span>项目管理</span>
        </el-menu-item>
        <el-menu-item index="/agents">
          <el-icon><Cpu /></el-icon>
          <span>智能体</span>
        </el-menu-item>
        <el-menu-item index="/llm-configs">
          <el-icon><Setting /></el-icon>
          <span>LLM 配置</span>
        </el-menu-item>
      </el-menu>
      <div class="sidebar-footer">
        <el-icon><ChatDotRound /></el-icon>
        <span>AI 多智能体短剧平台</span>
      </div>
    </el-aside>
    <el-main class="main">
      <router-view />
    </el-main>
  </el-container>
</template>

<style scoped>
.layout {
  height: 100%;
}

.sidebar {
  display: flex;
  flex-direction: column;
  background-color: #001529;
}

.logo {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.menu {
  flex: 1;
  border-right: none;
  background-color: #001529;
}

.menu :deep(.el-menu-item) {
  color: rgba(255, 255, 255, 0.7);
}

.menu :deep(.el-menu-item:hover) {
  background-color: rgba(255, 255, 255, 0.08);
}

.menu :deep(.el-menu-item.is-active) {
  color: #fff;
  background-color: #409eff;
}

.sidebar-footer {
  padding: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: rgba(255, 255, 255, 0.35);
  font-size: 12px;
}

.main {
  padding: 0;
  overflow-y: auto;
}
</style>
