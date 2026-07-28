<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth'

const { state, login, logout } = useAuth()
const router = useRouter()

// The account link is text, not an avatar: the design system allows no icons
// and no image chrome, so the shortest honest label the profile gives us wins.
const account = computed(() => state.user?.name || state.user?.email || '')

async function signOut() {
  await logout()
  router.push('/')
}
</script>

<template>
  <nav class="nav">
    <div class="wrap inner">
      <router-link to="/" class="wordmark">calnio</router-link>

      <div class="links">
        <a v-if="$route.name === 'landing'" href="#how">How it works</a>

        <template v-if="state.ready && state.user">
          <router-link
            v-if="!$route.path.startsWith('/dashboard')"
            to="/dashboard"
            class="primary"
          >
            <span>Dashboard</span>
          </router-link>

          <router-link to="/me" class="account" :title="state.user.email">
            {{ account }}
          </router-link>

          <button type="button" @click="signOut">Log out</button>
        </template>

        <button v-else type="button" class="primary" @click="login">
          <span>Log in</span>
        </button>
      </div>
    </div>
  </nav>
</template>

<style scoped>
/* Above the sections, which are above the atmosphere layer. */
.nav {
  position: relative;
  z-index: 2;
}

.inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: clamp(16px, 4vw, 40px);
  flex-wrap: wrap;
  padding-top: 14px;
  padding-bottom: 14px;
}

.wordmark {
  display: inline-flex;
  align-items: center;
  min-height: 44px;
  font-size: 19px;
  font-weight: 700;
  letter-spacing: -0.03em;
  color: var(--ink);
}

.links {
  display: flex;
  align-items: center;
  gap: clamp(14px, 3vw, 28px);
  flex-wrap: wrap;
}

.links a,
.links button {
  display: inline-flex;
  align-items: center;
  min-height: 44px;
  font-family: var(--font-mono);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--link);
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
}

.links a:hover,
.links button:hover {
  color: var(--ink);
}

/* The one nav item carrying weight: ink, rule on a nested span so the 44px
   hit box does not drag the underline away from the text. */
.primary {
  color: var(--ink);
}

.primary > span {
  border-bottom: 1px solid var(--field-line);
  padding-bottom: 3px;
}

.account {
  max-width: 20ch;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
</style>
