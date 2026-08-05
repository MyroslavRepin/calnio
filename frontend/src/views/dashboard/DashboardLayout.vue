<script setup>
import { onMounted, watch } from 'vue'
import AppHeader from '../../components/AppHeader.vue'
import { useAppleCalendar } from '../../composables/useAppleCalendar'
import { useAuth } from '../../composables/useAuth'
import { useNotion } from '../../composables/useNotion'
import { useSync } from '../../composables/useSync'

// App shell for every /dashboard/* page and /me: header, sidebar menu, content.
// Auth branching lives here so child views can assume a signed-in user.
const { state: auth, login } = useAuth()
const { load: loadApple } = useAppleCalendar()
const { load: loadNotion } = useNotion()
const { load: loadSync } = useSync()

const menu = [
  { to: { name: 'dashboard' }, label: 'Overview' },
  { to: { name: 'connections' }, label: 'Connections' },
  { to: { name: 'settings' }, label: 'Settings' },
]

// App.vue bootstraps auth; wait for a user before asking for their connections,
// otherwise the first call 401s during a page refresh. Loaded once here rather
// than per child view, the composable state is shared.
function loadIfAuthed() {
  if (!auth.ready || !auth.user) return
  loadApple()
  loadNotion()
  loadSync()
}

onMounted(loadIfAuthed)
watch(() => [auth.ready, auth.user], loadIfAuthed)
</script>

<template>
  <div class="app-ui page">
    <AppHeader v-if="auth.ready && auth.user" />

    <main class="shell">
      <p v-if="!auth.ready" class="loading">Loading…</p>

      <div v-else-if="!auth.user" class="signedout card">
        <h1 class="title">Sign in to Calnio</h1>
        <p class="lead">
          Your dashboard needs an account. Calnio signs you in with Google.
        </p>
        <button class="btn" type="button" @click="login">Continue with Google</button>
      </div>

      <div v-else class="grid">
        <aside class="side">
          <nav class="menu">
            <router-link v-for="item in menu" :key="item.label" :to="item.to">
              {{ item.label }}
            </router-link>
          </nav>

          <p class="group">Account</p>
          <nav class="menu">
            <router-link to="/me">Profile</router-link>
          </nav>
        </aside>

        <section class="content">
          <router-view />
        </section>
      </div>
    </main>
  </div>
</template>

<style scoped>
.page {
  min-height: 100vh;
}

.shell {
  max-width: var(--app-width-page);
  margin: 0 auto;
  padding: var(--app-space-5) var(--app-pad-page) var(--app-space-8);
}

/* No breakpoint: the content column asks for min(560px, 100%), so once the two
   columns no longer fit side by side the sidebar wraps onto its own row. */
.grid {
  display: flex;
  flex-wrap: wrap;
  gap: var(--app-gap-section);
  align-items: flex-start;
}

.side {
  flex: 1 1 var(--app-sidebar);
  display: flex;
  flex-direction: column;
  gap: var(--app-space-1);
}

.group {
  padding: var(--app-space-4) var(--app-space-3) var(--app-space-1);
  font-size: var(--app-text-meta);
  font-weight: var(--app-weight-bold);
  color: var(--app-fg-muted);
}

.menu {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.menu a {
  display: flex;
  align-items: center;
  min-height: 36px;
  padding: 6px var(--app-space-3);
  border-radius: var(--app-radius);
  font-size: var(--app-text-body);
  color: var(--app-fg);
}

.menu a:hover {
  background: var(--app-canvas-subtle);
  text-decoration: none;
}

/* Exact-match class: vue-router marks parents active too, which would light
   up Overview on every child route. */
.menu a.router-link-exact-active {
  background: var(--app-canvas-subtle);
  font-weight: var(--app-weight-bold);
}

.content {
  flex: 999 1 min(560px, 100%);
  min-width: 0;
}

.signedout {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--app-gap-block);
  max-width: var(--app-width-panel);
  margin: var(--app-space-7) auto;
  padding: var(--app-space-5);
}
</style>
