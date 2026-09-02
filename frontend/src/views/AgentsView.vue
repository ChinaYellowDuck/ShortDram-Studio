<script setup lang="ts">
import { ChatLineRound, Promotion } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { onMounted, ref } from 'vue'

import { chatWithHelloAgent, listAgents } from '../api/agents'
import { errorMessage } from '../api/client'
import type { AgentInfo } from '../api/types'

const loading = ref(false)
const agents = ref<AgentInfo[]>([])

const message = ref('')
const sending = ref(false)
interface ChatItem {
  role: 'user' | 'agent' | 'system'
  content: string
}
const chatHistory = ref<ChatItem[]>([])

async function load() {
  loading.value = true
  try {
    agents.value = await listAgents()
  } catch (err) {
    ElMessage.error(errorMessage(err))
  } finally {
    loading.value = false
  }
}

async function send() {
  const text = message.value.trim()
  if (!text || sending.value) return
  chatHistory.value.push({ role: 'user', content: text })
  message.value = ''
  sending.value = true
  try {
    const res = await chatWithHelloAgent(text)
    chatHistory.value.push({
      role: 'agent',
      content: `${res.response}\n（模型：${res.llm_config.provider} / ${res.llm_config.model}）`,
    })
  } catch (err) {
    const msg = errorMessage(err)
    chatHistory.value.push({ role: 'system', content: `调用失败：${msg}` })
  } finally {
    sending.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2>智能体</h2>
    </div>

    <el-row :gutter="16">
      <el-col :span="10">
        <el-card shadow="never" v-loading="loading">
          <template #header>可用智能体</template>
          <el-empty v-if="agents.length === 0" description="暂无可用智能体" :image-size="60" />
          <div v-for="agent in agents" :key="agent.id" class="agent-card">
            <div class="agent-title">
              <el-icon><ChatLineRound /></el-icon>
              <span>{{ agent.name }}</span>
              <el-tag size="small" type="success" style="margin-left: auto">
                {{ agent.status }}
              </el-tag>
            </div>
            <p class="agent-desc">{{ agent.description }}</p>
          </div>
          <el-alert
            type="info"
            :closable="false"
            show-icon
            title="更多智能体开发中"
            description="编剧、角色设计、分镜师、配音导演、视频合成、制片人等智能体将陆续上线。"
            style="margin-top: 12px"
          />
        </el-card>
      </el-col>

      <el-col :span="14">
        <el-card shadow="never">
          <template #header>
            Hello Agent 对话测试
            <span class="chat-hint">需先在「LLM 配置」中创建并设置默认配置</span>
          </template>
          <div class="chat-box">
            <el-empty
              v-if="chatHistory.length === 0"
              description="发送一条消息试试"
              :image-size="60"
            />
            <div
              v-for="(item, index) in chatHistory"
              :key="index"
              class="chat-item"
              :class="item.role"
            >
              <div class="chat-bubble">{{ item.content }}</div>
            </div>
          </div>
          <div class="chat-input">
            <el-input
              v-model="message"
              placeholder="输入消息，回车发送"
              :disabled="sending"
              @keyup.enter="send()"
            />
            <el-button
              type="primary"
              :icon="Promotion"
              :loading="sending"
              @click="send()"
            >
              发送
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.agent-card {
  padding: 12px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  margin-bottom: 12px;
}

.agent-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.agent-desc {
  margin: 8px 0 0;
  color: #909399;
  font-size: 13px;
}

.chat-hint {
  margin-left: 12px;
  font-size: 12px;
  color: #909399;
  font-weight: normal;
}

.chat-box {
  height: 360px;
  overflow-y: auto;
  padding: 8px;
  background-color: #fafafa;
  border-radius: 8px;
}

.chat-item {
  display: flex;
  margin-bottom: 12px;
}

.chat-item.user {
  justify-content: flex-end;
}

.chat-item.agent {
  justify-content: flex-start;
}

.chat-item.system {
  justify-content: center;
}

.chat-bubble {
  max-width: 75%;
  padding: 8px 12px;
  border-radius: 8px;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 14px;
}

.chat-item.user .chat-bubble {
  background-color: #409eff;
  color: #fff;
}

.chat-item.agent .chat-bubble {
  background-color: #fff;
  border: 1px solid #ebeef5;
}

.chat-item.system .chat-bubble {
  background-color: #fef0f0;
  color: #f56c6c;
  font-size: 12px;
}

.chat-input {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}
</style>
