<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../../composables/useAuth'

const authResult = useAuth()
const state = authResult.state
const login = authResult.login
const logout = authResult.logout

const router = useRouter()

// The shortest honest label for the account link. No avatar here: the header
// inside the app has one, the front door does not need it.
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
  <header class="navbar">
    <div class="row navrow">
      <router-link to="/" class="wordmark">Calnio</router-link>

      <div class="row links">
        <a v-if="$route.name === 'landing'" href="#how">How it works</a>

        <template v-if="state.ready && state.user">
          <router-link to="/dashboard">Dashboard</router-link>
          <router-link to="/me" :title="state.user.email" class="account">
            {{ account }}
          </router-link>
          <button class="btn plain" type="button" @click="signOut">Log out</button>
        </template>

        <button v-else class="btn plain" type="button" @click="login">Log in</button>
      </div>
    </div>
  </header>
</template>

<style scoped>
.navbar {
  border-bottom: 1px solid var(--app-border);
  background: var(--app-canvas);
}

.navrow {
  --gap: var(--app-gap-block);
  justify-content: space-between;
  max-width: var(--app-width-page);
  margin: 0 auto;
  padding: var(--app-space-3) var(--app-pad-page);
}

.links {
  --gap: var(--app-gap-block);
}

.account {
  max-width: 20ch;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
</style>
