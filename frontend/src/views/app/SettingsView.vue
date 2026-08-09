<script setup>
import { ref } from 'vue'
import DeleteAccount from '../../components/app/DeleteAccount.vue'
import DueDatePicker from '../../components/app/DueDatePicker.vue'
import SyncSwitch from '../../components/app/SyncSwitch.vue'
import { useSync } from '../../composables/useSync'

const syncResult = useSync()
const sync = syncResult.state

// One error box for the page, at the bottom and outside every card. The two
// sync cards report into it; DeleteAccount shows its own, inside its card.
const error = ref(null)
</script>

<template>
  <p v-if="!sync.ready" class="loading">Loading…</p>

  <template v-else>
    <header class="column page-head">
      <h1 class="title">Settings</h1>
      <p class="lead">
        Syncing runs in the background and pushes your Notion due dates into
        Apple Calendar. Notion itself is never written to.
      </p>
    </header>

    <SyncSwitch @error="error = $event" />
    <DueDatePicker @error="error = $event" />
    <DeleteAccount />

    <p v-if="error" class="error pageerror">{{ error }}</p>
  </template>
</template>

<style scoped>
.pageerror {
  margin-top: var(--app-gap-block);
}
</style>
