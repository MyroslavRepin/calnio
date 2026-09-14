import { reactive, readonly } from 'vue'
import { send } from './useAuth'

const BASE = '/api/v1/me/sync'

const state = reactive({
  ready: false,
  settings: null, // { enabled, eligible, mapping_count, last_run_at, last_status }
  busy: false,
  pending: false, // a run was queued and has not reported back
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

// Exported as reloadSync too: adding a sync turns the master switch on, so the
// page that did it has to re-read this.
async function load() {
  const result = await send(BASE)

  if (result.data) {
    state.settings = result.data
  } else {
    state.settings = null
  }

  state.ready = true
}

export { load as reloadSync }

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

// Watches a queued run to completion. Stops on a new last_run_at, or on the
// server turning the user off, which is what a rejected credential does.
//
// Exported because a sync's own switch queues the same run, so the Syncs page
// needs to watch it too.
export async function watchRun() {
  let previousRunAt = null
  if (state.settings) {
    previousRunAt = state.settings.last_run_at
  }

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
  const result = await update({ enabled })
  if (result.error) {
    return { error: result.error }
  }

  // Deliberately not awaited: the switch flips now, the run reports later.
  if (enabled) {
    watchRun()
  }

  return {}
}

export function useSync() {
  return {
    state: readonly(state),
    load,
    setEnabled,
  }
}
