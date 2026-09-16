<script setup>
import { computed, ref } from 'vue'
import { useNotion } from '../../composables/useNotion'
import { formatDateTime } from '../../format'

// Everything this block does goes through the Notion composable. The grant is
// all that lives here now: which databases sync, and where to, is the Syncs
// page's business.
const notionResult = useNotion()
const state = notionResult.state
const connect = notionResult.connect
const disconnect = notionResult.disconnect

const confirming = ref(false)
const error = ref('')

// When the workspace was last checked.
const verified = computed(function () {
  return formatDateTime(state.connection?.last_verified_at, '—')
})

// Notion gives us a workspace name most of the time, but not always.
const workspaceName = computed(function () {
  if (state.connection.workspace_name) {
    return state.connection.workspace_name
  } else {
    return '—'
  }
})

// Whether this grant may write. Notion fixes what an integration may do when
// the user consents, so a grant older than two-way sync reads only, and
// reconnecting is what changes that.
const canWrite = computed(function () {
  if (state.connection && state.connection.can_write) {
    return true
  } else {
    return false
  }
})

// The error to show: the one from this block, otherwise the one the OAuth
// callback left behind.
const message = computed(function () {
  if (error.value) {
    return error.value
  } else {
    return state.error
  }
})

// Sends the user back to Notion's picker so they can tick more databases.
async function shareMore() {
  error.value = ''

  const result = await connect()
  if (result.error) {
    error.value = result.error
  }
}

async function confirmDisconnect() {
  error.value = ''

  const result = await disconnect()
  if (result.error) {
    error.value = result.error
  }

  confirming.value = false
}
</script>

<template>
  <div class="column status">
    <dl class="datarows">
      <div>
        <dt>Workspace</dt>
        <dd>{{ workspaceName }}</dd>
      </div>
      <div>
        <dt>Connected</dt>
        <dd>{{ verified }}</dd>
      </div>
      <div>
        <dt>Access</dt>
        <dd>{{ canWrite ? 'Read and write' : 'Read only' }}</dd>
      </div>
    </dl>

    <p v-if="!canWrite" class="note">
      This connection was made before Calnio could write. Reconnect it with
      Share more databases to turn two-way syncing on.
    </p>

    <template v-if="confirming">
      <p class="body">
        Disconnecting revokes Calnio's access to your Notion workspace and
        removes every sync you set up from it. Pages Calnio wrote stay as they
        are, and events already in your calendars stay too.
      </p>
      <div class="row actions">
        <button
          class="btn danger"
          type="button"
          :disabled="state.busy"
          @click="confirmDisconnect"
        >
          {{ state.busy ? 'Disconnecting…' : 'Disconnect' }}
        </button>
        <button class="btn plain" type="button" @click="confirming = false">Cancel</button>
      </div>
    </template>

    <div v-else class="row actions">
      <button class="btn plain" type="button" :disabled="state.busy" @click="shareMore">
        Share more databases
      </button>
      <button class="btn plain" type="button" @click="confirming = true">
        Disconnect
      </button>
    </div>

    <p v-if="message" class="error">{{ message }}</p>
  </div>
</template>
