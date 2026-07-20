<script setup>
import { useAuth } from '../composables/useAuth'

const { state, login, logout } = useAuth()
</script>

<template>
  <nav class="nav">
    <a href="#" class="wordmark">calnio</a>
    <div class="links">
      <a href="#how">How it works</a>

      <template v-if="state.ready && state.user">
        <span class="user">{{ state.user.name || state.user.email }}</span>
        <button type="button" class="linkbtn" @click="logout">Log out</button>
      </template>
      <button v-else type="button" class="linkbtn cta" @click="login">Log in</button>
    </div>
  </nav>
</template>

<style scoped>
.nav {
  max-width: var(--maxw);
  margin: 0 auto;
  padding: 26px var(--pad);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.wordmark {
  font-family: var(--font-ui);
  font-size: 19px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--ink);
}

.links {
  display: flex;
  align-items: center;
  gap: 30px;
  font-size: 14px;
  color: var(--ink);
}

.user {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--muted);
}

.linkbtn {
  font-family: var(--font-ui);
  font-size: 14px;
  color: var(--ink);
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
}

.cta {
  font-weight: 500;
  border-bottom: 1px solid var(--ink);
  padding-bottom: 1px;
}
</style>
