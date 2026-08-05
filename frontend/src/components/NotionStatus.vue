<script setup>
import { computed, ref } from 'vue'
import { useNotion } from '../composables/useNotion'

const { state, connect, fetchDatabases, selectDatabase, disconnect } = useNotion()

const changing = ref(false)
const picked = ref('')
const error = ref('')
const confirming = ref(false)

// Unlike the calendar list, the database name is stored on the connection, so
// the status reads correctly without touching Notion on page load.
const verified = computed(() => {
  const at = state.connection?.last_verified_at
  return at ? new Date(at).toLocaleString() : '—'
})

async function startChange() {
  error.value = ''
  const { error: err } = await fetchDatabases()
  if (err) {
    error.value = err
    return
  }
  picked.value = state.connection.data_source_id || ''
  changing.value = true
}

async function saveChange() {
  error.value = ''
  const { error: err } = await selectDatabase(picked.value)
  if (err) {
    error.value = err
    return
  }
  changing.value = false
}

async function shareMore() {
  error.value = ''
  const { error: err } = await connect()
  if (err) error.value = err
}

async function confirmDisconnect() {
  error.value = ''
  const { error: err } = await disconnect()
  if (err) error.value = err
  confirming.value = false
}
</script>

<template>
  <div class="status">
    <dl class="datarows">
      <div>
        <dt>Workspace</dt>
        <dd>{{ state.connection.workspace_name || '—' }}</dd>
      </div>
      <div>
        <dt>Database</dt>
        <dd>
          {{ state.connection.data_source_name || state.connection.data_source_id }}
        </dd>
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

      <div class="actions">
        <button
          v-if="state.databases.length"
          class="btn"
          type="button"
          :disabled="state.busy || !picked"
          @click="saveChange"
        >
          {{ state.busy ? 'Saving…' : 'Save' }}
        </button>
        <button
          class="btn plain"
          type="button"
          :disabled="state.busy"
          @click="shareMore"
        >
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
      <div class="actions">
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

    <div v-else class="actions">
      <button class="btn plain" type="button" :disabled="state.busy" @click="startChange">
        {{ state.busy ? 'Loading databases…' : 'Change database' }}
      </button>
      <button class="btn plain" type="button" @click="confirming = true">
        Disconnect
      </button>
    </div>

    <p v-if="error || state.error" class="error">{{ error || state.error }}</p>
  </div>
</template>

<style scoped>
.status {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--app-gap-block);
}

.status > .datarows {
  width: 100%;
}
</style>
