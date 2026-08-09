import { reactive, readonly } from 'vue'
import { send } from './useAuth'

const BASE = '/api/v1/me/sync'
// The date columns live on the Notion connection, so the picker's options come
// from that router rather than this one.
const DATE_PROPERTIES = '/api/v1/me/notion/date-properties'

const state = reactive({
  ready: false,
  settings: null, // { enabled, eligible, due_date_property, last_run_at, last_status }
  dateProperties: [], // date columns on the selected database, fetched on demand
  busy: false,
  pending: false, // a run was queued by turning syncing on and has not reported back
})

// Turning syncing on queues a background run that takes seconds. We poll until
// last_run_at moves, rather than leaving the page claiming nothing happened.
const POLL_MS = 3000
const POLL_TRIES = 20 // about 60s, then give up and let the next page load tell the story

function sleep(ms) {
  return new Promise(function (resolve) {
    setTimeout(resolve, ms)
  })
}

async function load() {
  const result = await send(BASE)

  if (result.data) {
    state.settings = result.data
  } else {
    state.settings = null
  }

  state.ready = true
}

async function fetchDateProperties() {
  state.busy = true
  const result = await send(DATE_PROPERTIES, {}, 'could not read your database columns')
  state.busy = false

  if (result.error) {
    return { error: result.error }
  }

  state.dateProperties = result.data
  return {}
}

async function update(body) {
  state.busy = true
  const result = await send(
    BASE,
    { method: 'PUT', json: body },
    'could not save',
    'network error — is the API running?',
  )
  state.busy = false

  if (result.error) {
    return { error: result.error }
  }

  state.settings = result.data
  return {}
}

// Watches the queued run to completion. Stops on a new last_run_at, or on the
// server turning the user off, which is what a rejected credential does.
async function watchRun(previousRunAt) {
  state.pending = true

  try {
    for (let attempt = 0; attempt < POLL_TRIES; attempt += 1) {
      await sleep(POLL_MS)

      const result = await send(BASE)
      if (!result.data) {
        return
      }

      state.settings = result.data

      if (result.data.last_run_at !== previousRunAt) {
        return
      }
      if (!result.data.enabled) {
        return
      }
    }
  } finally {
    state.pending = false
  }
}

async function setEnabled(enabled) {
  let previousRunAt = null
  if (state.settings) {
    previousRunAt = state.settings.last_run_at
  }

  const result = await update({ enabled })
  if (result.error) {
    return { error: result.error }
  }

  // Deliberately not awaited: the switch flips now, the run reports later.
  if (enabled) {
    watchRun(previousRunAt)
  }

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
