<script setup>
import { ref } from 'vue'
import DeleteAccount from '../../components/app/DeleteAccount.vue'
import SyncSwitch from '../../components/app/SyncSwitch.vue'
import { useSync } from '../../composables/useSync'

const syncResult = useSync()
const sync = syncResult.state

// One error box for the page, at the bottom and outside every card. SyncSwitch
// reports into it; DeleteAccount shows its own, inside its card.
const error = ref(null)
</script>

<template>
  <p v-if="!sync.ready" class="loading">Loading…</p>

  <template v-else>
    <header class="column page-head">
      <h1 class="title">Settings</h1>
      <p class="lead">
        The master switch for every sync. Each sync has its own switch on the
        Syncs page, and both have to be on for it to run.
      </p>
    </header>

    <SyncSwitch @error="error = $event" />
    <DeleteAccount />

    <p v-if="error" class="error pageerror">{{ error }}</p>
  </template>
</template>

<style scoped>
.pageerror {
  margin-top: var(--app-gap-block);
}
</style>
