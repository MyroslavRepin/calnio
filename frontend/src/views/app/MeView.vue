<script setup>
import { computed } from 'vue'
import { useAuth } from '../../composables/useAuth'

// Rendered inside DashboardLayout, so the header, the sidebar and the
// signed-out branch all belong to the shell and this file is content only.
const authResult = useAuth()
const auth = authResult.state

// The shortest honest label for the signed-in account.
const name = computed(function () {
  if (auth.user?.name) {
    return auth.user.name
  }
  if (auth.user?.email) {
    return auth.user.email
  }
  return ''
})

// Fallback when Google gave us no picture: the first letter, on a grey disc.
const initial = computed(function () {
  const first = name.value[0]

  if (first) {
    return first.toUpperCase()
  } else {
    return '?'
  }
})

// Google does not always give us a display name.
const displayName = computed(function () {
  if (auth.user.name) {
    return auth.user.name
  } else {
    return '—'
  }
})
</script>

<template>
  <header class="row profile">
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
          <dd>{{ displayName }}</dd>
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
  --gap: var(--app-gap-block);
  padding-bottom: var(--app-space-5);
}

.avatar {
  width: var(--app-avatar-lg);
  height: var(--app-avatar-lg);
  flex: 0 0 auto;
}

.fallback {
  font-size: var(--app-text-title);
}

.card-body .note {
  margin-top: var(--app-gap-block);
}
</style>
