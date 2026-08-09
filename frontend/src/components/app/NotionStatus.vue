<script setup>
import { computed, ref } from 'vue'
import { useNotion } from '../../composables/useNotion'
import { formatDateTime } from '../../format'

// Everything this block does goes through the Notion composable.
const notionResult = useNotion()
const state = notionResult.state
const connect = notionResult.connect
const fetchDatabases = notionResult.fetchDatabases
const selectDatabase = notionResult.selectDatabase
const disconnect = notionResult.disconnect

// Which of the three views is showing: the plain facts, the database picker,
// or the disconnect confirmation.
const changing = ref(false)
const confirming = ref(false)

const picked = ref('')
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

// Prefer the stored database name, fall back to its id.
const databaseName = computed(function () {
  if (state.connection.data_source_name) {
    return state.connection.data_source_name
  } else {
    return state.connection.data_source_id
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

// Opens the picker. The list is fetched now, not on page load, because it is
// a call out to Notion.
async function startChange() {
  error.value = ''

  const result = await fetchDatabases()
  if (result.error) {
    error.value = result.error
    return
  }

  if (state.connection.data_source_id) {
    picked.value = state.connection.data_source_id
  } else {
    picked.value = ''
  }

  changing.value = true
}

async function saveChange() {
  error.value = ''

  const result = await selectDatabase(picked.value)
  if (result.error) {
    error.value = result.error
    return
  }

  changing.value = false
}

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
        <dt>Database</dt>
        <dd>{{ databaseName }}</dd>
      </div>
      <div>
        <dt>Connected</dt>
        <dd>{{ verified }}</dd>
      </div>
    </dl>

    <template v-if="changing">
      <ul v-if="state.databases.length" class="picklist">
        <li v-for="db in state.databases" :key="db.id">
          <label>
            <input type="radio" :value="db.id" v-model="picked" />
            <span>{{ db.title || 'Untitled' }}</span>
          </label>
        </li>
      </ul>

      <p v-else class="body">
        No databases are shared with Calnio any more. Re-open Notion's dialog to
        share one.
      </p>

      <div class="row actions">
        <button
          v-if="state.databases.length"
          class="btn"
          type="button"
          :disabled="state.busy || !picked"
          @click="saveChange"
        >
          {{ state.busy ? 'Saving…' : 'Save' }}
        </button>
        <button class="btn plain" type="button" :disabled="state.busy" @click="shareMore">
          Share more databases
        </button>
        <button class="btn plain" type="button" @click="changing = false">Cancel</button>
      </div>
    </template>

    <template v-else-if="confirming">
      <p class="body">
        Disconnecting revokes Calnio's access to your Notion workspace and
        forgets which database you picked. Nothing in Notion changes, Calnio
        only ever reads it.
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
      <button class="btn plain" type="button" :disabled="state.busy" @click="startChange">
        {{ state.busy ? 'Loading databases…' : 'Change database' }}
      </button>
      <button class="btn plain" type="button" @click="confirming = true">
        Disconnect
      </button>
    </div>

    <p v-if="message" class="error">{{ message }}</p>
  </div>
</template>
