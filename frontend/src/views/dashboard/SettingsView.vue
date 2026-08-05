<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useAuth } from '../../composables/useAuth'
import { useNotion } from '../../composables/useNotion'
import { useSync } from '../../composables/useSync'

const { state: notion } = useNotion()
const { state: sync, fetchDateProperties, setEnabled, setDueDateProperty } = useSync()
const { state: auth, deleteAccount } = useAuth()

const error = ref(null)

const settings = computed(() => sync.settings)
const enabled = computed(() => Boolean(settings.value?.enabled))
const eligible = computed(() => Boolean(settings.value?.eligible))
const hasDatabase = computed(() => Boolean(notion.connection?.data_source_id))

// The options come from Notion, so they are fetched once the database is known
// rather than on every visit. DashboardLayout has usually loaded the connection
// by the time this page mounts; the watch covers a hard refresh, where the
// connection lands a moment later.
function loadProperties() {
  if (!hasDatabase.value || sync.dateProperties.length) return
  fetchDateProperties().then((result) => {
    if (result.error) error.value = result.error
  })
}

onMounted(loadProperties)
watch(hasDatabase, loadProperties)

const lastRun = computed(() => {
  const at = settings.value?.last_run_at
  return at ? new Date(at).toLocaleString() : 'never'
})

// What the last run did, in the user's terms. auth_error is the only status
// that also turned the switch off, so it has to explain itself.
const statusLine = computed(() => {
  if (sync.pending) return 'Syncing now, this takes a few seconds.'
  switch (settings.value?.last_status) {
    case 'ok':
      return 'Last sync finished normally.'
    case 'error':
      return 'Last sync failed. Calnio tries again on the next run.'
    case 'auth_error':
      return 'A connection was rejected, so syncing was turned off. Reconnect it, then turn syncing back on.'
    default:
      return 'Nothing has synced yet.'
  }
})

async function toggle() {
  error.value = null
  const result = await setEnabled(!enabled.value)
  if (result.error) error.value = result.error
}

async function choose(name) {
  error.value = null
  const result = await setDueDateProperty(name)
  if (result.error) error.value = result.error
}

// Deletion is two steps: the trigger only opens the block, and the confirm
// button stays dead until the signed-in email is typed back.
const confirming = ref(false)
const typedEmail = ref('')
const deleting = ref(false)
const deleteError = ref(null)

const signedInEmail = computed(() => auth.user?.email ?? '')
const canDelete = computed(
  () =>
    signedInEmail.value !== '' &&
    typedEmail.value.trim().toLowerCase() === signedInEmail.value.toLowerCase(),
)

function openDelete() {
  confirming.value = true
  deleteError.value = null
}

function cancelDelete() {
  confirming.value = false
  typedEmail.value = ''
  deleteError.value = null
}

async function confirmDelete() {
  if (!canDelete.value || deleting.value) return
  deleting.value = true
  deleteError.value = null
  const result = await deleteAccount(typedEmail.value.trim())
  if (result.error) {
    deleteError.value = result.error
    deleting.value = false
    return
  }
  // A real navigation, not a router push: useSync, useNotion and
  // useAppleCalendar keep their state at module level, and it would otherwise
  // still be sitting there, describing an account that no longer exists.
  window.location.href = '/'
}
</script>

<template>
  <p v-if="!sync.ready" class="loading">Loading…</p>

  <template v-else>
    <header class="page-head">
      <h1 class="title">Settings</h1>
      <p class="lead">
        Syncing runs in the background and pushes your Notion due dates into
        Apple Calendar. Notion itself is never written to.
      </p>
    </header>

    <section class="card">
      <div class="card-head">
        <h2>Syncing</h2>
        <span class="label" :class="enabled ? 'success' : 'neutral'">
          {{ enabled ? 'On' : 'Off' }}
        </span>
      </div>

      <div class="card-body">
        <button
          class="switch"
          type="button"
          role="switch"
          :aria-checked="enabled"
          :disabled="!eligible || sync.busy"
          @click="toggle"
        >
          <span class="track" :class="{ on: enabled }"><span class="knob"></span></span>
          <span class="switch-label">
            {{ enabled ? 'Syncing is on' : 'Syncing is off' }}
          </span>
        </button>

        <p v-if="!eligible" class="note">
          Connect Notion and Apple Calendar, and pick a due-date column below,
          before turning syncing on.
          <router-link :to="{ name: 'welcome' }">Finish setup</router-link>
        </p>

        <template v-else>
          <p class="note">{{ statusLine }}</p>

          <dl class="datarows">
            <div>
              <dt>Last run</dt>
              <dd>{{ lastRun }}</dd>
            </div>
          </dl>
        </template>
      </div>
    </section>

    <section class="card">
      <div class="card-head">
        <h2>Due date column</h2>
      </div>

      <div class="card-body">
        <p class="body">
          The Notion date property Calnio reads. Only date columns can be chosen,
          every page with a value there becomes an event.
        </p>

        <p v-if="!hasDatabase" class="note">
          Pick a Notion database first.
          <router-link :to="{ name: 'connections' }">Connections</router-link>
        </p>

        <p v-else-if="sync.busy && !sync.dateProperties.length" class="note">
          Reading your database…
        </p>

        <p v-else-if="!sync.dateProperties.length" class="note">
          This database has no date columns, so there is nothing to sync. Add one
          in Notion, then reload this page.
        </p>

        <ul v-else class="picklist">
          <li v-for="name in sync.dateProperties" :key="name">
            <label>
              <input
                type="radio"
                name="due-date-property"
                :value="name"
                :checked="settings?.due_date_property === name"
                :disabled="sync.busy"
                @change="choose(name)"
              />
              <span>{{ name }}</span>
            </label>
          </li>
        </ul>
      </div>
    </section>

    <section class="card danger">
      <div class="card-head">
        <h2>Delete account</h2>
      </div>

      <div class="card-body">
        <template v-if="!confirming">
          <p class="body">
            Removes your account and everything Calnio stores about it. This
            cannot be undone.
          </p>
          <button class="btn danger" type="button" @click="openDelete">
            Delete my account
          </button>
        </template>

        <template v-else>
          <p class="body">
            Deleting your account removes your Google sign-in, your iCloud
            password, your Notion connection and everything Calnio remembers
            about what it synced. Calnio's access to your Notion workspace is
            revoked. Events already in your Apple Calendar are yours, they stay,
            and Calnio can no longer remove them. If you ever sign up again,
            remove those old events first, or Apple Calendar may end up with
            duplicates. This cannot be undone.
          </p>

          <label class="field">
            <span>Type {{ signedInEmail }} to confirm</span>
            <input
              v-model="typedEmail"
              type="email"
              autocomplete="off"
              autocapitalize="none"
              spellcheck="false"
              :disabled="deleting"
            />
          </label>

          <div class="actions">
            <button
              class="btn danger"
              type="button"
              :disabled="!canDelete || deleting"
              @click="confirmDelete"
            >
              {{ deleting ? 'Deleting…' : 'Delete my account' }}
            </button>

            <button
              class="btn plain"
              type="button"
              :disabled="deleting"
              @click="cancelDelete"
            >
              Cancel
            </button>
          </div>

          <p v-if="deleteError" class="error">{{ deleteError }}</p>
        </template>
      </div>
    </section>

    <p v-if="error" class="error spaced">{{ error }}</p>
  </template>
</template>

<style scoped>
.card.danger {
  border-color: var(--app-danger-line);
}

.card.danger .card-head {
  background: var(--app-danger-tint);
  border-bottom-color: var(--app-danger-line);
}

.card-body > * + * {
  margin-top: var(--app-gap-stack);
}

/* Toggle. State is carried by colour and the knob's side, no transition —
   it reads as a control, not as an animation. */
.switch {
  display: inline-flex;
  align-items: center;
  gap: var(--app-space-2);
  padding: 0;
  background: none;
  border: none;
  cursor: pointer;
  font-family: inherit;
  font-size: var(--app-text-body);
  color: var(--app-fg);
}

.switch:disabled {
  opacity: 0.6;
  cursor: default;
}

.track {
  display: inline-flex;
  align-items: center;
  width: 48px;
  height: 28px;
  padding: 3px;
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
  background: var(--app-canvas-subtle);
}

.track.on {
  background: var(--app-accent);
  border-color: var(--app-accent);
}

.knob {
  width: var(--app-marker);
  height: var(--app-marker);
  border-radius: var(--app-radius-sm);
  background: var(--app-canvas);
  border: 1px solid var(--app-border);
}

.track.on .knob {
  margin-left: auto;
  border-color: var(--app-border-emphasis);
}

.switch-label {
  font-weight: var(--app-weight-medium);
}

.spaced {
  margin-top: var(--app-gap-block);
}
</style>
