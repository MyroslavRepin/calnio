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
    <dl class="rows">
      <div class="row">
        <dt>Workspace</dt>
        <dd>{{ state.connection.workspace_name || '—' }}</dd>
      </div>
      <div class="row">
        <dt>Database</dt>
        <dd>{{ state.connection.data_source_name || state.connection.data_source_id }}</dd>
      </div>
      <div class="row">
        <dt>Connected</dt>
        <dd>{{ verified }}</dd>
      </div>
    </dl>

    <template v-if="changing">
      <ul v-if="state.databases.length" class="databases">
        <li v-for="db in state.databases" :key="db.id">
          <label>
            <input type="radio" :value="db.id" v-model="picked" />
            <span>{{ db.title || 'Untitled' }}</span>
          </label>
        </li>
      </ul>

      <p v-else class="warn">
        No databases are shared with Calnio any more. Re-open Notion's dialog to
        share one.
      </p>

      <div class="actions">
        <button
          v-if="state.databases.length"
          class="btn-primary"
          type="button"
          :disabled="state.busy || !picked"
          @click="saveChange"
        >
          {{ state.busy ? 'Saving…' : 'Save' }}
        </button>
        <button class="linkbtn" type="button" :disabled="state.busy" @click="shareMore">
          Share more databases
        </button>
        <button class="linkbtn" type="button" @click="changing = false">Cancel</button>
      </div>
    </template>

    <template v-else-if="confirming">
      <p class="warn">
        Disconnecting revokes Calnio's access to your Notion workspace and forgets
        which database you picked. Nothing in Notion changes — Calnio only ever
        reads it.
      </p>
      <div class="actions">
        <button
          class="btn-primary"
          type="button"
          :disabled="state.busy"
          @click="confirmDisconnect"
        >
          {{ state.busy ? 'Disconnecting…' : 'Disconnect' }}
        </button>
        <button class="linkbtn" type="button" @click="confirming = false">Cancel</button>
      </div>
    </template>

    <div v-else class="actions">
      <button class="linkbtn" type="button" :disabled="state.busy" @click="startChange">
        {{ state.busy ? 'Loading databases…' : 'Change database' }}
      </button>
      <button class="linkbtn" type="button" @click="confirming = true">Disconnect</button>
    </div>

    <p v-if="error || state.error" class="error">{{ error || state.error }}</p>
  </div>
</template>

<style scoped>
.status {
  display: flex;
  flex-direction: column;
  gap: 28px;
  padding: 40px 0;
  border-top: 1px solid var(--hairline);
}

.rows {
  margin: 0;
  border-top: 1px solid var(--hairline);
  max-width: 640px;
}

.row {
  display: grid;
  grid-template-columns: 160px 1fr;
  gap: 24px;
  padding: 14px 0;
  border-bottom: 1px solid var(--hairline);
}

dt {
  font-family: var(--font-mono);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  color: var(--muted);
}

dd {
  margin: 0;
  font-size: 15px;
  color: var(--ink);
  overflow-wrap: anywhere;
}

.databases {
  list-style: none;
  margin: 0;
  padding: 0;
  border-top: 1px solid var(--hairline);
  max-width: 520px;
}

.databases li {
  border-bottom: 1px solid var(--hairline);
}

.databases label {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 0;
  font-size: 15px;
  cursor: pointer;
}

.actions {
  display: flex;
  align-items: center;
  gap: 24px;
}

.warn {
  font-size: 15px;
  line-height: 1.6;
  color: var(--body);
  max-width: 520px;
}

.linkbtn {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--muted);
  background: none;
  border: none;
  border-bottom: 1px solid var(--hairline);
  padding: 0 0 2px;
  cursor: pointer;
}

.btn-primary:disabled,
.linkbtn:disabled {
  opacity: 0.4;
  cursor: default;
}

.error {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--ink);
}
</style>
