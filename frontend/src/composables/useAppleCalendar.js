import { reactive, readonly } from 'vue'
import { useAuth } from './useAuth'

const BASE = '/api/v1/me/apple-calendar'

const { apiFetch } = useAuth()

const state = reactive({
  ready: false, // first load finished (avoids flashing the wizard at a connected user)
  connection: null, // { connected, icloud_email, calendar_url, last_verified_at } | null
  calendars: [], // only populated after a connect or an explicit fetch — the
  // listing hits iCloud and is slow, so it is never loaded on page load
  busy: false, // a request that talks to iCloud is in flight
})

// The API returns { detail } on every error. Fall back to something honest if
// the body is not JSON (proxy error, connection dropped).
async function detail(res, fallback) {
  try {
    const body = await res.json()
    return body.detail || fallback
  } catch {
    return fallback
  }
}

async function load() {
  const res = await apiFetch(BASE)
  state.connection = res.ok ? await res.json() : null // 404 = not connected
  state.ready = true
}

async function connect(icloudEmail, appSpecificPassword) {
  state.busy = true
  try {
    const res = await apiFetch(BASE, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        icloud_email: icloudEmail,
        app_specific_password: appSpecificPassword,
      }),
    })
    if (!res.ok) return { error: await detail(res, 'could not connect') }

    // The connect response carries the calendar list, so step 2 renders
    // without a second (slow) round trip to iCloud.
    const body = await res.json()
    const { calendars, ...connection } = body
    state.connection = connection
    state.calendars = calendars
    return {}
  } catch {
    return { error: 'network error — is the API running?' }
  } finally {
    state.busy = false
  }
}

async function fetchCalendars() {
  state.busy = true
  try {
    const res = await apiFetch(`${BASE}/calendars`)
    if (!res.ok) return { error: await detail(res, 'could not list calendars') }
    state.calendars = await res.json()
    return {}
  } catch {
    return { error: 'network error' }
  } finally {
    state.busy = false
  }
}

async function createCalendar(name) {
  state.busy = true
  try {
    const res = await apiFetch(`${BASE}/calendars`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    })
    if (!res.ok) return { error: await detail(res, 'could not create the calendar') }
    const calendar = await res.json()
    state.calendars = [...state.calendars, calendar]
    return { calendar }
  } catch {
    return { error: 'network error' }
  } finally {
    state.busy = false
  }
}

async function selectCalendar(calendarUrl) {
  state.busy = true
  try {
    const res = await apiFetch(`${BASE}/calendar`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ calendar_url: calendarUrl }),
    })
    if (!res.ok) return { error: await detail(res, 'could not save the calendar') }
    state.connection = await res.json()
    return {}
  } catch {
    return { error: 'network error' }
  } finally {
    state.busy = false
  }
}

async function disconnect() {
  state.busy = true
  try {
    const res = await apiFetch(BASE, { method: 'DELETE' })
    if (!res.ok && res.status !== 404) {
      return { error: await detail(res, 'could not disconnect') }
    }
    state.connection = null
    state.calendars = []
    return {}
  } catch {
    return { error: 'network error' }
  } finally {
    state.busy = false
  }
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
