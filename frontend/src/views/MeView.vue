<script setup>
import { useRouter } from 'vue-router'
import AtmosphereField from '../components/AtmosphereField.vue'
import TheNav from '../components/TheNav.vue'
import { useAuth } from '../composables/useAuth'

// Read-only account page. Everything shown here comes from /auth/me — there is
// no account-mutation endpoint yet, so nothing on this page is editable.
const { state: auth, login, logout } = useAuth()
const router = useRouter()

async function signOut() {
  await logout()
  router.push('/')
}
</script>

<template>
  <div class="page">
    <AtmosphereField variant="short" />

    <TheNav />

    <main class="wrap shell">
      <p v-if="!auth.ready" class="loading">Loading…</p>

      <div v-else-if="!auth.user" class="signedout surface">
        <p class="eyebrow">Not signed in</p>
        <h1 class="title">Log in to see<br />your account.</h1>
        <button class="btn" type="button" @click="login">Continue with Google</button>
      </div>

      <div v-else class="surface">
        <header class="head">
          <p class="eyebrow">Account</p>
          <h1 class="title">{{ auth.user.name || auth.user.email }}</h1>
        </header>

        <dl class="datarows">
          <div>
            <dt>Name</dt>
            <dd>{{ auth.user.name || '—' }}</dd>
          </div>
          <div>
            <dt>Email</dt>
            <dd>{{ auth.user.email }}</dd>
          </div>
          <div>
            <dt>Signed in with</dt>
            <dd>Google</dd>
          </div>
        </dl>

        <div class="actions">
          <router-link class="link-mono quiet" to="/dashboard">
            <span>Dashboard</span>
          </router-link>
          <button class="link-mono quiet" type="button" @click="signOut">
            <span>Log out</span>
          </button>
        </div>
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
  padding-top: clamp(32px, 6vw, 56px);
  padding-bottom: var(--sec-bottom);
}

.head {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-bottom: clamp(28px, 5vw, 40px);
}

.signedout {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: clamp(16px, 2.5vw, 24px);
  max-width: 640px;
}

.surface {
  max-width: 760px;
}

.actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px 24px;
  padding-top: 24px;
}
</style>
