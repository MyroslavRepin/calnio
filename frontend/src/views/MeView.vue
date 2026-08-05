<script setup>
import { computed } from 'vue'
import { useAuth } from '../composables/useAuth'

// Read-only account page, rendered inside DashboardLayout: the header, the
// sidebar and the signed-out branch all belong to the shell, so this file is
// content only. Everything shown comes from /auth/me, there is no
// account-mutation endpoint yet, so nothing here is editable.
const { state: auth } = useAuth()

const name = computed(() => auth.user?.name || auth.user?.email || '')
const initial = computed(() => (name.value[0] || '?').toUpperCase())
</script>

<template>
  <header class="profile">
    <img v-if="auth.user.picture" :src="auth.user.picture" alt="" class="avatar" />
    <span v-else class="avatar fallback">{{ initial }}</span>
    <div>
      <h1 class="title">{{ name }}</h1>
      <p class="lead">{{ auth.user.email }}</p>
    </div>
  </header>

  <section class="card">
    <div class="card-head">
      <h2>Account</h2>
      <router-link :to="{ name: 'dashboard' }">Overview</router-link>
    </div>
    <div class="card-body">
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

      <p class="note">
        Nothing here is editable. Your name, email and picture come from the
        Google account you signed in with. Deleting your account lives in
        <router-link :to="{ name: 'settings' }">Settings</router-link>.
      </p>
    </div>
  </section>
</template>

<style scoped>
.profile {
  display: flex;
  align-items: center;
  gap: var(--app-gap-block);
  padding-bottom: var(--app-space-5);
}

.avatar {
  width: var(--app-avatar-lg);
  height: var(--app-avatar-lg);
  border-radius: var(--app-radius-pill);
  border: 1px solid var(--app-border);
  object-fit: cover;
  flex: 0 0 auto;
}

.fallback {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--app-canvas-subtle);
  color: var(--app-fg-muted);
  font-size: var(--app-text-title);
  font-weight: var(--app-weight-bold);
}

.card-body .note {
  margin-top: var(--app-gap-block);
}
</style>
