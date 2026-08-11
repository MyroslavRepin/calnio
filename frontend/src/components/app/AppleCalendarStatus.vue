<script setup>
import { computed, ref } from 'vue'
import { isReminderCalendar, useAppleCalendar } from '../../composables/useAppleCalendar'
import { formatDateTime } from '../../format'

// Everything this block does goes through the Apple Calendar composable.
const appleResult = useAppleCalendar()
const state = appleResult.state
const fetchCalendars = appleResult.fetchCalendars
const selectCalendar = appleResult.selectCalendar
const disconnect = appleResult.disconnect

// Which of the three views is showing: the plain facts, the calendar picker,
// or the disconnect confirmation.
const changing = ref(false)
const confirming = ref(false)

const picked = ref('')
const error = ref('')

// The backend stores the name alongside the url, picked up the moment a
// calendar is selected. Older rows saved before that existed have none, so
// this session's fetched list (if loaded) and the raw url are the fallbacks.
const calendarName = computed(function () {
  if (state.connection?.calendar_name) {
    return state.connection.calendar_name
  }

  const url = state.connection?.calendar_url

  const match = state.calendars.find(function (calendar) {
    return calendar.url === url
  })

  if (match) {
    return match.name
  } else {
    return url
  }
})

// When the credentials were last checked against iCloud.
const verified = computed(function () {
  return formatDateTime(state.connection?.last_verified_at, '—')
})

// The chosen calendar's full row, looked up by url, so its name is available.
const pickedCalendar = computed(function () {
  return state.calendars.find(function (calendar) {
    return calendar.url === picked.value
  })
})

// Blocks saving a calendar that is really iCloud's Reminders list.
const isReminderPicked = computed(function () {
  return isReminderCalendar(pickedCalendar.value)
})

// Opens the picker. The list is fetched now, not on page load, because iCloud
// is slow to answer it.
async function startChange() {
  error.value = ''

  const result = await fetchCalendars()
  if (result.error) {
    error.value = result.error
    return
  }

  if (state.connection.calendar_url) {
    picked.value = state.connection.calendar_url
  } else {
    picked.value = ''
  }

  changing.value = true
}

async function saveChange() {
  error.value = ''

  const result = await selectCalendar(picked.value)
  if (result.error) {
    error.value = result.error
    return
  }

  changing.value = false
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
        <dt>Apple Account</dt>
        <dd>{{ state.connection.icloud_email }}</dd>
      </div>
      <div>
        <dt>Calendar</dt>
        <dd>{{ calendarName }}</dd>
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
            <span v-if="isReminderCalendar(cal)" class="label attention">Reminders</span>
          </label>
        </li>
      </ul>

      <p v-if="isReminderPicked" class="error">
        {{ pickedCalendar.name }} is a Reminder. Support of reminder is in progress
      </p>

      <div class="row actions">
        <button class="btn" type="button" :disabled="state.busy || !picked || isReminderPicked" @click="saveChange">
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
      <div class="row actions">
        <button class="btn danger" type="button" :disabled="state.busy" @click="confirmDisconnect">
          {{ state.busy ? 'Disconnecting…' : 'Disconnect' }}
        </button>
        <button class="btn plain" type="button" @click="confirming = false">Cancel</button>
      </div>
    </template>

    <div v-else class="row actions">
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
