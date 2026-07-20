<script setup>
import { ref, onMounted } from 'vue'
import { useAuth } from '../composables/useAuth'

const { apiFetch } = useAuth()

const status = ref(0)
const data = ref(null)
const loading = ref(true)

onMounted(async () => {
  const res = await apiFetch('/auth/me')
  status.value = res.status
  try {
    data.value = await res.json()
  } catch {
    data.value = { error: 'no JSON body' }
  }
  loading.value = false
})
</script>

<template>
  <section class="me wrap">
    <p class="eyebrow">GET /auth/me</p>
    <p v-if="loading">loading…</p>
    <template v-else>
      <p class="status">HTTP {{ status }}</p>
      <pre>{{ JSON.stringify(data, null, 2) }}</pre>
    </template>
    <router-link to="/" class="back">← back</router-link>
  </section>
</template>

<style scoped>
.me {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-top: 40px;
  padding-bottom: 40px;
}

.status {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--muted);
}

pre {
  font-family: var(--font-code);
  font-size: 14px;
  line-height: 1.6;
  color: #e9e7e1;
  background: #0a0a0a;
  border-radius: 8px;
  padding: 20px;
  overflow-x: auto;
  margin: 0;
}

.back {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--muted);
}
</style>
