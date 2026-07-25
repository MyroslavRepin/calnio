<script setup>
import { onMounted, watch } from 'vue'
import TheNav from '../../components/TheNav.vue'
import { useAppleCalendar } from '../../composables/useAppleCalendar'
import { useAuth } from '../../composables/useAuth'

// App shell for every /dashboard/* page: top nav, sidebar menu, content.
// Auth branching lives here so child views can assume a signed-in user.
const { state: auth, login } = useAuth()
const { load } = useAppleCalendar()

const menu = [
  { to: { name: 'dashboard' }, label: 'Overview' },
  { to: { name: 'connections' }, label: 'Connections' },
  { to: { name: 'settings' }, label: 'Settings' },
]

// App.vue bootstraps auth; wait for a user before asking for their connection,
// otherwise the first call 401s during a page refresh. Loaded once here rather
// than per child view — the composable state is shared.
function loadIfAuthed() {
  if (auth.ready && auth.user) load()
}

onMounted(loadIfAuthed)
watch(() => [auth.ready, auth.user], loadIfAuthed)
</script>

<template>
  <TheNav />

  <main class="wrap shell">
    <p v-if="!auth.ready" class="muted">Loading…</p>

    <div v-else-if="!auth.user" class="signedout">
      <p class="eyebrow">Not signed in</p>
      <h1>Log in to see your dashboard</h1>
      <button class="btn-primary" type="button" @click="login">
        Continue with Google
      </button>
    </div>

    <div v-else class="grid">
      <aside class="side">
        <p class="eyebrow">Menu</p>
        <nav class="menu">
          <router-link v-for="item in menu" :key="item.label" :to="item.to">
            {{ item.label }}
          </router-link>
        </nav>

        <p class="eyebrow">Account</p>
        <nav class="menu">
          <router-link to="/me">Profile</router-link>
        </nav>
      </aside>

      <section class="content">
        <router-view />
      </section>
    </div>
  </main>
</template>

<style scoped>
.shell {
  padding-top: 40px;
  padding-bottom: 96px;
}

.grid {
  display: grid;
  grid-template-columns: 180px 1fr;
  gap: 48px;
  align-items: start;
  border-top: 1px solid var(--hairline);
  padding-top: 32px;
}

.side {
  display: flex;
  flex-direction: column;
  gap: 12px;
  position: sticky;
  top: 32px;
}

/* Space between the two menu groups, without a divider. */
.side .eyebrow:not(:first-child) {
  padding-top: 20px;
}

.menu {
  display: flex;
  flex-direction: column;
}

.menu a {
  font-size: 15px;
  color: var(--muted);
  padding: 8px 0;
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
  border-left: 1px solid var(--hairline);
  padding-left: 48px;
  min-width: 0;
}

.signedout {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 16px;
  padding-top: 24px;
}

.signedout h1 {
  font-size: 40px;
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1.05;
  padding-bottom: 8px;
}

.muted {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--muted);
  padding: 40px 0;
}

@media (max-width: 720px) {
  .grid {
    grid-template-columns: 1fr;
    gap: 24px;
  }

  .side {
    position: static;
  }

  .menu {
    flex-direction: row;
    gap: 24px;
  }

  .content {
    border-left: none;
    border-top: 1px solid var(--hairline);
    padding-left: 0;
    padding-top: 24px;
  }
}
</style>
