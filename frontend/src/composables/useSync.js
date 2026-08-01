import { reactive, readonly } from 'vue'
import { useAuth } from './useAuth'

const BASE = '/api/v1/me/sync'
// The date columns live on the Notion connection, so the picker's options come
// from that router rather than this one.
const DATE_PROPERTIES = '/api/v1/me/notion/date-properties'

const { apiFetch } = useAuth()

const state = reactive({
  ready: false, // first load finished
  settings: null, // { enabled, eligible, due_date_property, last_run_at, last_status } | null
  dateProperties: [], // date columns on the selected database; fetched on demand
  busy: false, // a settings request is in flight
  pending: false, // a run was queued by turning syncing on, and has not reported back
})

// Turning syncing on queues a background run that takes seconds — poll until
// last_run_at moves rather than leaving the page claiming nothing happened.
const POLL_MS = 3000
const POLL_TRIES = 20 // ~60s, then give up and let the page reload tell the story

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

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

async function load() {
  const res = await apiFetch(BASE)
  state.settings = res.ok ? await res.json() : null
  state.ready = true
}

async function fetchDateProperties() {
  state.busy = true
  try {
    const res = await apiFetch(DATE_PROPERTIES)
    if (!res.ok) {
      return { error: await detail(res, 'could not read your database columns') }
    }
    state.dateProperties = await res.json()
    return {}
  } catch {
    return { error: 'network error' }
  } finally {
    state.busy = false
  }
}

async function update(body) {
  state.busy = true
  try {
    const res = await apiFetch(BASE, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!res.ok) return { error: await detail(res, 'could not save') }
    state.settings = await res.json()
    return {}
  } catch {
    return { error: 'network error — is the API running?' }
  } finally {
    state.busy = false
  }
}

// Watches the queued run to completion. Stops on a new last_run_at, or on the
// server turning the user off — which is what a rejected credential does.
async function watchRun(previousRunAt) {
  state.pending = true
  try {
    for (let i = 0; i < POLL_TRIES; i += 1) {
      await sleep(POLL_MS)
      const res = await apiFetch(BASE)
      if (!res.ok) return
      const next = await res.json()
      state.settings = next
      if (next.last_run_at !== previousRunAt || !next.enabled) return
    }
  } finally {
    state.pending = false
  }
}

async function setEnabled(enabled) {
  const previousRunAt = state.settings?.last_run_at ?? null
  const result = await update({ enabled })
  if (result.error) return result
  // Deliberately not awaited: the switch flips now, the run reports later.
  if (enabled) watchRun(previousRunAt)
  return {}
}

async function setDueDateProperty(name) {
  return update({ due_date_property: name })
}

export function useSync() {
  return {
    state: readonly(state),
    load,
    fetchDateProperties,
    setEnabled,
    setDueDateProperty,
  }
}
