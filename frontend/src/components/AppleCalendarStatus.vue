<script setup>
import { computed, ref } from 'vue'
import { useAppleCalendar } from '../composables/useAppleCalendar'

const { state, fetchCalendars, selectCalendar, disconnect } = useAppleCalendar()

const changing = ref(false)
const picked = ref('')
const error = ref('')
const confirming = ref(false)

// The calendar list is not fetched on load (it hits iCloud and is slow), so the
// name is only known if this session already loaded it — fall back to the URL.
const calendarName = computed(() => {
  const url = state.connection?.calendar_url
  return state.calendars.find((c) => c.url === url)?.name || null
})

const verified = computed(() => {
  const at = state.connection?.last_verified_at
  return at ? new Date(at).toLocaleString() : '—'
})

async function startChange() {
  error.value = ''
  const { error: err } = await fetchCalendars()
  if (err) {
    error.value = err
    return
  }
  picked.value = state.connection.calendar_url || ''
  changing.value = true
}

async function saveChange() {
  error.value = ''
  const { error: err } = await selectCalendar(picked.value)
  if (err) {
    error.value = err
    return
  }
  changing.value = false
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
        <dt>Apple ID</dt>
        <dd>{{ state.connection.icloud_email }}</dd>
      </div>
      <div class="row">
        <dt>Calendar</dt>
        <dd>{{ calendarName || state.connection.calendar_url }}</dd>
      </div>
      <div class="row">
        <dt>Last verified</dt>
        <dd>{{ verified }}</dd>
      </div>
    </dl>

    <template v-if="changing">
      <ul class="calendars">
        <li v-for="cal in state.calendars" :key="cal.url">
          <label>
            <input type="radio" :value="cal.url" v-model="picked" />
            <span>{{ cal.name }}</span>
          </label>
        </li>
      </ul>
      <div class="actions">
        <button
          class="btn-primary"
          type="button"
          :disabled="state.busy || !picked"
          @click="saveChange"
        >
          {{ state.busy ? 'Saving…' : 'Save' }}
        </button>
        <button class="linkbtn" type="button" @click="changing = false">Cancel</button>
      </div>
    </template>

    <template v-else-if="confirming">
      <p class="warn">
        Disconnecting forgets your Apple ID password. Events Calnio already wrote
        stay in your calendar — delete them yourself if you want them gone.
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
        {{ state.busy ? 'Loading calendars…' : 'Change calendar' }}
      </button>
      <button class="linkbtn" type="button" @click="confirming = true">Disconnect</button>
    </div>

    <p v-if="error" class="error">{{ error }}</p>
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

.calendars {
  list-style: none;
  margin: 0;
  padding: 0;
  border-top: 1px solid var(--hairline);
  max-width: 520px;
}

.calendars li {
  border-bottom: 1px solid var(--hairline);
}

.calendars label {
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
