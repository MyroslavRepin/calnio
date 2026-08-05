<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth'

// Header for the signed-in app only. TheNav stays on the landing page: this one
// is a plain product bar, not part of the marketing design.
const { state, logout } = useAuth()
const router = useRouter()

const name = computed(() => state.user?.name || state.user?.email || '')

// Fallback when Google gave us no picture: the first letter, on a grey disc.
const initial = computed(() => (name.value[0] || '?').toUpperCase())

async function signOut() {
  await logout()
  router.push('/')
}
</script>

<template>
  <header class="bar">
    <div class="inner">
      <router-link to="/" class="wordmark">calnio</router-link>

      <div class="right">
        <router-link to="/me" class="account" :title="state.user?.email">
          <img v-if="state.user?.picture" :src="state.user.picture" alt="" class="avatar" />
          <span v-else class="avatar fallback">{{ initial }}</span>
          <span class="name">{{ name }}</span>
        </router-link>

        <button class="signout" type="button" @click="signOut">Sign out</button>
      </div>
    </div>
  </header>
</template>

<style scoped>
.bar {
  background: var(--app-canvas);
  border-bottom: 1px solid var(--app-border);
}

.inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px 16px;
  max-width: 1280px;
  margin: 0 auto;
  padding: 10px clamp(16px, 4vw, 32px);
}

.wordmark {
  display: inline-flex;
  align-items: center;
  min-height: 32px;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--app-fg);
}

.wordmark:hover {
  text-decoration: none;
}

.right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.account {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 32px;
  color: var(--app-fg);
  font-size: 14px;
}

.account:hover {
  text-decoration: none;
  color: var(--app-accent);
}

.avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 1px solid var(--app-border);
  object-fit: cover;
}

.fallback {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--app-canvas-subtle);
  color: var(--app-fg-muted);
  font-size: 12px;
  font-weight: 600;
}

.name {
  max-width: 22ch;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.signout {
  font-family: inherit;
  font-size: 14px;
  color: var(--app-fg-muted);
  background: none;
  border: none;
  padding: 0;
  min-height: 32px;
  cursor: pointer;
}

.signout:hover {
  color: var(--app-accent);
}
</style>
