<script setup>
import { computed, ref } from 'vue'
import AppleCalendarSetup from './AppleCalendarSetup.vue'
import { useNotion } from '../../composables/useNotion'
import { useSync } from '../../composables/useSync'

// Sits on top of every dashboard page while rejected credentials keep syncing
// off. Nothing else tells the user: Calnio stops quietly, and their calendar
// just stops getting new tasks. Reconnecting turns syncing back on by itself.
const syncResult = useSync()
const sync = syncResult.state

const notionResult = useNotion()
const notion = notionResult.state
const connectNotion = notionResult.connect

const error = ref('')

// Which grant was rejected: "icloud", "notion", or null when nothing was.
const rejectedBy = computed(function () {
  if (!sync.settings) {
    return null
  }
  return sync.settings.rejected_by
})

// Send the browser to Notion. The callback brings it back with syncing on.
async function reconnectNotion() {
  error.value = ''

  const result = await connectNotion()
  if (result.error) {
    error.value = result.error
  }
}
</script>

<template>
  <section v-if="rejectedBy === 'icloud'" class="card reconnect">
    <div class="card-head">
      <h2>iCloud rejected your app-specific password</h2>
      <span class="label danger">Syncing off</span>
    </div>
    <div class="card-body column reconnectbody">
      <p class="body">
        Calnio turned syncing off, so new tasks are not reaching your calendar.
        This happens when the password is revoked, or when your Apple Account
        password changes, which revokes every app-specific password. Make a new
        one and syncing turns back on.
      </p>
      <AppleCalendarSetup />
    </div>
  </section>

  <section v-else-if="rejectedBy === 'notion'" class="card reconnect">
    <div class="card-head">
      <h2>Notion rejected Calnio's access</h2>
      <span class="label danger">Syncing off</span>
    </div>
    <div class="card-body column reconnectbody">
      <p class="body">
        Calnio turned syncing off, so new tasks are not reaching your calendar.
        This happens when Calnio is removed from your workspace's connections.
        Connect it again and syncing turns back on.
      </p>
      <div class="actions">
        <button class="btn" type="button" :disabled="notion.busy" @click="reconnectNotion">
          Reconnect Notion
        </button>
      </div>
      <p v-if="error" class="error">{{ error }}</p>
    </div>
  </section>
</template>

<style scoped>
.reconnect {
  margin-bottom: var(--app-gap-section);
}

.reconnectbody {
  --gap: var(--app-gap-stack);
}
</style>
