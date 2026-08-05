<script setup>
import { computed, ref } from 'vue'
import { useAppleCalendar } from '../composables/useAppleCalendar'

const { state, fetchCalendars, selectCalendar, disconnect } = useAppleCalendar()

const changing = ref(false)
const picked = ref('')
const error = ref('')
const confirming = ref(false)

// The calendar list is not fetched on load (it hits iCloud and is slow), so the
// name is only known if this session already loaded it, fall back to the URL.
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
    <dl class="datarows">
      <div>
        <dt>Apple Account</dt>
        <dd>{{ state.connection.icloud_email }}</dd>
      </div>
      <div>
        <dt>Calendar</dt>
        <dd>{{ calendarName || state.connection.calendar_url }}</dd>
      </div>
      <div>
        <dt>Last verified</dt>
        <dd>{{ verified }}</dd>
      </div>
    </dl>

    <template v-if="changing">
      <ul class="picklist">
        <li v-for="cal in state.calendars" :key="cal.url">
          <label>
            <input type="radio" :value="cal.url" v-model="picked" />
            <span>{{ cal.name }}</span>
          </label>
        </li>
      </ul>
      <div class="actions">
        <button
          class="btn"
          type="button"
          :disabled="state.busy || !picked"
          @click="saveChange"
        >
          {{ state.busy ? 'Saving…' : 'Save' }}
        </button>
        <button class="btn plain" type="button" @click="changing = false">Cancel</button>
      </div>
    </template>

    <template v-else-if="confirming">
      <p class="body">
        Disconnecting forgets your app-specific password. Events Calnio already
        wrote stay in your calendar, delete them yourself if you want them gone.
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
        {{ state.busy ? 'Loading calendars…' : 'Change calendar' }}
      </button>
      <button class="btn plain" type="button" @click="confirming = true">
        Disconnect
      </button>
    </div>

    <p v-if="error" class="error">{{ error }}</p>
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
