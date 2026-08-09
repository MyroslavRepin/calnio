<script setup>
const pages = [
  { name: 'dashboard', label: 'Overview' },
  { name: 'connections', label: 'Connections' },
  { name: 'settings', label: 'Settings' },
]
</script>

<template>
  <aside class="column sidebar">
    <nav class="column menu">
      <router-link v-for="page in pages" :key="page.name" :to="{ name: page.name }">
        {{ page.label }}
      </router-link>
    </nav>

    <p class="group">Account</p>
    <nav class="column menu">
      <router-link :to="{ name: 'me' }">Profile</router-link>
    </nav>
  </aside>
</template>

<style scoped>
.sidebar {
  --gap: var(--app-space-1);
  flex: 1 1 var(--app-sidebar);
}

.group {
  padding: var(--app-space-4) var(--app-space-3) var(--app-space-1);
  font-size: var(--app-text-meta);
  font-weight: var(--app-weight-bold);
  color: var(--app-fg-muted);
}

.menu {
  --gap: 2px;
}

.menu a {
  display: flex;
  align-items: center;
  min-height: 36px;
  padding: 6px var(--app-space-3);
  border-radius: var(--app-radius);
  font-size: var(--app-text-body);
  color: var(--app-fg);
}

.menu a:hover {
  background: var(--app-canvas-subtle);
  text-decoration: none;
}

/* Exact-match class: vue-router marks parents active too, which would light up
   Overview on every child route. */
.menu a.router-link-exact-active {
  background: var(--app-canvas-subtle);
  font-weight: var(--app-weight-bold);
}
</style>
