<template>
  <div class="page">
    <div class="card-box chat-area">
      <div class="chat-messages" ref="scrollBox">
        <div v-for="(m, i) in messages" :key="i" class="chat-bubble" :class="m.role">
          {{ m.content }}
        </div>
        <div v-if="thinking" class="chat-bubble assistant" style="color: #909399">正在检索知识库并思考…</div>
      </div>
      <div style="display: flex; gap: 10px; padding-top: 12px; border-top: 1px solid #e4e7ed">
        <el-input
          v-model="input"
          placeholder="例如：数据出境需要满足什么条件？保密条款怎么写？"
          @keyup.enter="send"
        />
        <el-button type="primary" :loading="thinking" @click="send">发送</el-button>
        <el-button @click="messages = []">清空</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { nextTick, ref } from 'vue'
import { sendChat } from '../api'

const messages = ref([])
const input = ref('')
const thinking = ref(false)
const sessionId = ref(null)
const scrollBox = ref(null)

async function send() {
  const text = input.value.trim()
  if (!text || thinking.value) return
  input.value = ''
  messages.value.push({ role: 'user', content: text })
  thinking.value = true
  scrollToBottom()
  try {
    const data = await sendChat(text, sessionId.value)
    sessionId.value = data.session_id
    messages.value.push({ role: 'assistant', content: data.answer })
  } finally {
    thinking.value = false
    scrollToBottom()
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (scrollBox.value) scrollBox.value.scrollTop = scrollBox.value.scrollHeight
  })
}
</script>
