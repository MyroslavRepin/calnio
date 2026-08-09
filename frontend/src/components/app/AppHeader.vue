<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../../composables/useAuth'

const authResult = useAuth()
const state = authResult.state
const logout = authResult.logout

const router = useRouter()

// The shortest honest label for the signed-in account.
const name = computed(function () {
  if (state.user?.name) {
    return state.user.name
  }
  if (state.user?.email) {
    return state.user.email
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

async function signOut() {
  await logout()
  router.push('/')
}
</script>

<template>
  <header class="bar">
    <div class="row headerrow">
      <router-link to="/" class="wordmark">calnio</router-link>

      <div class="row session">
        <router-link to="/me" class="account" :title="state.user?.email">
          <img v-if="state.user?.picture" :src="state.user.picture" alt="" class="avatar" />
          <span v-else class="avatar fallback">{{ initial }}</span>
          <span class="name">{{ name }}</span>
        </router-link>

        <button class="signout" type="button" @click="signOut">Sign out</button>
      </div>
    </div>
  </header>
</template>

<style scoped>
.bar {
  background: var(--app-canvas);
  border-bottom: 1px solid var(--app-border);
}

.headerrow {
  --gap: var(--app-gap-inline) var(--app-gap-block);
  justify-content: space-between;
  max-width: var(--app-width-page);
  margin: 0 auto;
  padding: 10px var(--app-pad-page);
}

.session {
  --gap: var(--app-gap-block);
}

.account {
  display: inline-flex;
  align-items: center;
  gap: var(--app-gap-inline);
  min-height: var(--app-control-height);
  color: var(--app-fg);
  font-size: var(--app-text-body);
}

.account:hover {
  text-decoration: none;
  color: var(--app-accent);
}

.avatar {
  width: var(--app-avatar);
  height: var(--app-avatar);
}

.fallback {
  font-size: var(--app-text-meta);
}

.name {
  max-width: 22ch;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.signout {
  font-family: inherit;
  font-size: var(--app-text-body);
  color: var(--app-fg-muted);
  background: none;
  border: none;
  padding: 0;
  min-height: var(--app-control-height);
  cursor: pointer;
}

.signout:hover {
  color: var(--app-accent);
}
</style>
