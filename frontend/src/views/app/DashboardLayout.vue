<script setup>
import AppHeader from '../../components/app/AppHeader.vue'
import SidebarMenu from '../../components/app/SidebarMenu.vue'
import RecentSyncs from './RecentSyncs.vue'
import { useAppleCalendar } from '../../composables/useAppleCalendar'
import { loadWhenSignedIn, useAuth } from '../../composables/useAuth'
import { useNotion } from '../../composables/useNotion'
import { useSync } from '../../composables/useSync'

// App shell for every /dashboard/* page and /me. Auth branching lives here, so
// every child view can assume a signed-in user.
const authResult = useAuth()
const auth = authResult.state
const login = authResult.login

const appleResult = useAppleCalendar()
const notionResult = useNotion()
const syncResult = useSync()

// The cheap facts every child page needs, loaded once here rather than per view
// because the composable state is shared.
loadWhenSignedIn(appleResult.load, notionResult.load, syncResult.load)
</script>

<template>
  <div class="app-ui">
    <AppHeader v-if="auth.ready && auth.user" />

    <main class="shell">
      <p v-if="!auth.ready" class="loading">Loading…</p>

      <div v-else-if="!auth.user" class="card column panel">
        <h1 class="title">Sign in to Calnio</h1>
        <p class="lead">
          Your dashboard needs an account. Calnio signs you in with Google.
        </p>
        <button class="btn" type="button" @click="login">Continue with Google</button>
      </div>

      <div v-else class="row columns">
        <SidebarMenu />
        <section class="content">
          <router-view />
        </section>
      </div>
    </main>
  </div>
</template>

<style scoped>
.shell {
  max-width: var(--app-width-page);
  margin: 0 auto;
  padding: var(--app-space-5) var(--app-pad-page) var(--app-space-8);
}

/* No breakpoint: the content column asks for min(560px, 100%), so once the two
   columns no longer fit side by side the sidebar wraps onto its own row. */
.columns {
  --gap: var(--app-gap-section);
  align-items: flex-start;
}

.content {
  flex: 999 1 min(560px, 100%);
  min-width: 0;
}
</style>
