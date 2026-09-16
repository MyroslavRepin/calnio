import { reactive, readonly } from 'vue'
import { send } from './useAuth'

const BASE = '/api/v1/admin/stats'

// One shared box, same as every other composable here. The page is the only
// reader today, but the rule does not change for that.
const state = reactive({
  ready: false, // first load finished, so the page stops saying "Loading"
  stats: null, // the whole answer, or null when it has never loaded
  busy: false,
})

// Everything the dashboard draws, in one request. Loaded on demand, never on
// page load, because it counts every row in the database.
async function load() {
  state.busy = true
  const result = await send(BASE, {}, 'could not read the numbers')
  state.busy = false

  if (result.error) {
    state.ready = true
    return { error: result.error }
  }

  state.stats = result.data
  state.ready = true
  return {}
}

export function useAdmin() {
  return {
    state: readonly(state),
    load,
  }
}
