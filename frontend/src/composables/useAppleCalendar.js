import { reactive, readonly } from 'vue'
import { send } from './useAuth'

const BASE = '/api/v1/me/apple-calendar'

const state = reactive({
  ready: false, // first load finished, so the wizard never flashes at a connected user
  connection: null, // { connected, icloud_email, calendar_url, calendar_name, last_verified_at }
  // Listing calendars hits iCloud and is slow, so it never runs on page load.
  calendars: [],
  busy: false,
})

// The stored connection, or null when there is none.
async function load() {
  const result = await send(BASE)

  if (result.data) {
    state.connection = result.data
  } else {
    state.connection = null // a 404 means not connected
  }

  state.ready = true
}

async function connect(icloudEmail, appSpecificPassword) {
  state.busy = true
  const result = await send(
    BASE,
    {
      method: 'PUT',
      json: {
        icloud_email: icloudEmail,
        app_specific_password: appSpecificPassword,
      },
    },
    'could not connect',
    'network error — is the API running?',
  )
  state.busy = false

  if (result.error) {
    return { error: result.error }
  }

  // The connect answer already carries the calendar list, so step 2 of the
  // wizard renders without a second slow round trip to iCloud.
  const body = result.data
  const calendars = body.calendars
  const connection = { ...body }
  delete connection.calendars

  state.connection = connection
  state.calendars = calendars
  return {}
}

async function fetchCalendars() {
  state.busy = true
  const result = await send(BASE + '/calendars', {}, 'could not list calendars')
  state.busy = false

  if (result.error) {
    return { error: result.error }
  }

  state.calendars = result.data
  return {}
}

async function createCalendar(name) {
  state.busy = true
  const result = await send(
    BASE + '/calendars',
    { method: 'POST', json: { name } },
    'could not create the calendar',
  )
  state.busy = false

  if (result.error) {
    return { error: result.error }
  }

  state.calendars = [...state.calendars, result.data]
  return { calendar: result.data }
}

async function selectCalendar(calendarUrl) {
  state.busy = true
  const result = await send(
    BASE + '/calendar',
    { method: 'PUT', json: { calendar_url: calendarUrl } },
    'could not save the calendar',
  )
  state.busy = false

  if (result.error) {
    return { error: result.error }
  }

  state.connection = result.data
  return {}
}

async function disconnect() {
  state.busy = true
  const result = await send(BASE, { method: 'DELETE' }, 'could not disconnect')
  state.busy = false

  // A 404 means it was already gone, which is the outcome we wanted anyway.
  if (result.error && result.status !== 404) {
    return { error: result.error }
  }

  state.connection = null
  state.calendars = []
  return {}
}

// A calendar named like iCloud's Reminders list is not a real calendar and
// cannot take events, so no screen should let it be saved.
export function isReminderCalendar(calendar) {
  if (!calendar) {
    return false
  }

  return calendar.name.toLowerCase().includes('reminder')
}

export function useAppleCalendar() {
  return {
    state: readonly(state),
    load,
    connect,
    fetchCalendars,
    createCalendar,
    selectCalendar,
    disconnect,
  }
}
