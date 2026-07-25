<script setup>
import { useRouter } from 'vue-router'
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
  <TheNav />

  <main class="wrap page">
    <template v-if="!auth.ready">
      <p class="muted">Loading…</p>
    </template>

    <template v-else-if="!auth.user">
      <p class="eyebrow">Not signed in</p>
      <h1>Log in to see your account</h1>
      <button class="btn-primary signin" type="button" @click="login">
        Continue with Google
      </button>
    </template>

    <template v-else>
      <header class="head">
        <p class="eyebrow">Account</p>
        <h1>{{ auth.user.name || auth.user.email }}</h1>
      </header>

      <dl class="rows">
        <div class="row">
          <dt>Name</dt>
          <dd>{{ auth.user.name || '—' }}</dd>
        </div>
        <div class="row">
          <dt>Email</dt>
          <dd>{{ auth.user.email }}</dd>
        </div>
        <div class="row">
          <dt>Signed in with</dt>
          <dd>Google</dd>
        </div>
      </dl>

      <div class="actions">
        <router-link class="linkbtn" to="/dashboard">Dashboard</router-link>
        <button class="linkbtn" type="button" @click="signOut">Log out</button>
      </div>
    </template>
  </main>
</template>

<style scoped>
.page {
  padding-top: 48px;
  padding-bottom: 96px;
}

.head {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-bottom: 40px;
  max-width: 640px;
}

h1 {
  font-size: 40px;
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1.05;
}

.signin {
  margin-top: 24px;
  align-self: flex-start;
}

.rows {
  margin: 0;
  border-top: 1px solid var(--hairline);
  max-width: 640px;
}

.row {
  display: grid;
  grid-template-columns: 180px 1fr;
  gap: 24px;
  padding: 14px 0;
  border-bottom: 1px solid var(--hairline);
}

dt {
  font-family: var(--font-mono);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  color: var(--muted);
}

dd {
  margin: 0;
  font-size: 15px;
  color: var(--ink);
  overflow-wrap: anywhere;
}

.actions {
  display: flex;
  align-items: center;
  gap: 24px;
  padding-top: 32px;
}

.linkbtn {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--muted);
  background: none;
  border: none;
  border-bottom: 1px solid var(--hairline);
  padding: 0 0 2px;
  cursor: pointer;
}

.linkbtn:hover {
  color: var(--ink);
  border-bottom-color: var(--ink);
}

.muted {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--muted);
  padding: 40px 0;
}
</style>
