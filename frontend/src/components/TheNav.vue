<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth'

const { state, login, logout } = useAuth()
const router = useRouter()

// Google does not always give a picture; fall back to the first letter of
// whatever name we do have.
const initial = computed(() => {
  const source = state.user?.name || state.user?.email || '?'
  return source.trim().charAt(0).toUpperCase()
})

async function signOut() {
  await logout()
  router.push('/')
}
</script>

<template>
  <nav class="nav">
    <router-link to="/" class="wordmark">calnio<span class="dot" aria-hidden="true"></span></router-link>
    <div class="links">
      <a v-if="$route.name === 'landing'" href="#how">How it works</a>

      <template v-if="state.ready && state.user">
        <router-link v-if="!$route.path.startsWith('/dashboard')" to="/dashboard">
          Dashboard
        </router-link>

        <router-link to="/me" class="avatar" :title="state.user.email">
          <img v-if="state.user.picture" :src="state.user.picture" alt="" />
          <span v-else>{{ initial }}</span>
        </router-link>

        <button type="button" class="linkbtn" @click="signOut">Log out</button>
      </template>
      <button v-else type="button" class="linkbtn cta" @click="login">Log in</button>
    </div>
  </nav>
</template>

<style scoped>
.nav {
  max-width: var(--maxw);
  margin: 0 auto;
  padding: 26px var(--pad);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.wordmark {
  font-family: var(--font-ui);
  font-size: 23px;
  font-weight: 800;
  letter-spacing: -0.035em;
  color: var(--ink);
}

.links {
  display: flex;
  align-items: center;
  gap: 30px;
  font-size: 14px;
  color: var(--ink);
}

.avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  overflow: hidden;
  border: 1px solid var(--frame);
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--muted);
}

.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.avatar:hover {
  border-color: var(--ink);
  color: var(--ink);
}

.linkbtn {
  font-family: var(--font-ui);
  font-size: 14px;
  color: var(--ink);
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
}

.cta {
  font-weight: 500;
  border-bottom: 1px solid var(--ink);
  padding-bottom: 1px;
}
</style>
