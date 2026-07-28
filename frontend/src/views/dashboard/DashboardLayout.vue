<script setup>
import { onMounted, watch } from 'vue'
import AtmosphereField from '../../components/AtmosphereField.vue'
import TheNav from '../../components/TheNav.vue'
import { useAppleCalendar } from '../../composables/useAppleCalendar'
import { useAuth } from '../../composables/useAuth'
import { useNotion } from '../../composables/useNotion'

// App shell for every /dashboard/* page: top nav, sidebar menu, content.
// Auth branching lives here so child views can assume a signed-in user.
const { state: auth, login } = useAuth()
const { load: loadApple } = useAppleCalendar()
const { load: loadNotion } = useNotion()

const menu = [
  { to: { name: 'dashboard' }, label: 'Overview' },
  { to: { name: 'connections' }, label: 'Connections' },
  { to: { name: 'settings' }, label: 'Settings' },
]

// App.vue bootstraps auth; wait for a user before asking for their connections,
// otherwise the first call 401s during a page refresh. Loaded once here rather
// than per child view — the composable state is shared.
function loadIfAuthed() {
  if (!auth.ready || !auth.user) return
  loadApple()
  loadNotion()
}

onMounted(loadIfAuthed)
watch(() => [auth.ready, auth.user], loadIfAuthed)
</script>

<template>
  <div class="page">
    <!-- Washed-out circles behind the page; every block of content rides on a
         .surface panel so nothing small is ever read against blue. -->
    <AtmosphereField variant="short" />

    <TheNav />

    <main class="wrap shell">
      <p v-if="!auth.ready" class="loading">Loading…</p>

      <div v-else-if="!auth.user" class="signedout">
        <p class="eyebrow">Not signed in</p>
        <h1 class="title">Log in to see<br />your dashboard.</h1>
        <button class="btn" type="button" @click="login">Continue with Google</button>
      </div>

      <div v-else class="grid">
        <aside class="side surface">
          <p class="eyebrow">Menu</p>
          <nav class="menu">
            <router-link v-for="item in menu" :key="item.label" :to="item.to">
              {{ item.label }}
            </router-link>
          </nav>

          <p class="eyebrow group">Account</p>
          <nav class="menu">
            <router-link to="/me">Profile</router-link>
          </nav>
        </aside>

        <section class="content surface">
          <router-view />
        </section>
      </div>
    </main>
  </div>
</template>

<style scoped>
.page {
  position: relative;
  min-height: 100vh;
  overflow: clip;
}

.shell {
  position: relative;
  z-index: 1;
  padding-top: clamp(24px, 4vw, 40px);
  padding-bottom: var(--sec-bottom);
}

/* No breakpoint: the content column asks for min(560px, 100%), so once the two
   columns no longer fit side by side the sidebar wraps onto its own row. */
.grid {
  display: flex;
  flex-wrap: wrap;
  gap: clamp(16px, 2vw, 24px);
  align-items: flex-start;
}

.side {
  flex: 1 1 160px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.group {
  padding-top: 20px;
}

.menu {
  display: flex;
  flex-direction: column;
}

.menu a {
  display: inline-flex;
  align-items: center;
  min-height: 44px;
  font-size: 15px;
  color: var(--link);
}

.menu a:hover {
  color: var(--ink);
}

/* Exact-match class: vue-router marks parents active too, which would light
   up Overview on every child route. */
.menu a.router-link-exact-active {
  color: var(--ink);
  font-weight: 500;
}

.content {
  flex: 999 1 min(560px, 100%);
  min-width: 0;
}

.signedout {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: clamp(16px, 2.5vw, 24px);
  padding-top: clamp(32px, 6vw, 64px);
}
</style>
