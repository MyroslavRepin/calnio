<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../../composables/useAuth'

const authResult = useAuth()
const state = authResult.state
const login = authResult.login
const logout = authResult.logout

const router = useRouter()

// The account link is text, not an avatar: the landing design system allows no
// icons and no image chrome, so the shortest honest label wins.
const account = computed(function () {
  if (state.user?.name) {
    return state.user.name
  }
  if (state.user?.email) {
    return state.user.email
  }
  return ''
})

async function signOut() {
  await logout()
  router.push('/')
}
</script>

<template>
  <nav class="nav">
    <div class="wrap row navrow">
      <router-link to="/" class="wordmark">calnio</router-link>

      <div class="row links">
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

.navrow {
  --gap: clamp(16px, 4vw, 40px);
  justify-content: space-between;
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
  --gap: clamp(14px, 3vw, 28px);
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

/* The one nav item carrying weight. The rule sits on a nested span so the 44px
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
