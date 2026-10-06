import { reactive, readonly } from 'vue'
import { send } from './useAuth'

// One shared box, same as every other composable here. Each admin page loads
// its own slice when it opens, never the shell, because every answer counts
// rows across every account.
const state = reactive({
  overview: null,
  users: null,
  user: null, // the one account the detail page shows
  syncs: null,
  sync: null, // the one sync the detail page shows
  runs: null,
  problems: null,
})

// Runs one admin request and keeps the answer under one key of state. The old
// answer stays on screen while a list reloads.
async function loadInto(key, path, failMessage) {
  const result = await send(path, {}, failMessage)
  if (result.error) {
    return { error: result.error }
  }

  state[key] = result.data
  return {}
}

// The overview: headline numbers, charts, funnel and failures.
function loadOverview() {
  return loadInto('overview', '/api/v1/admin/overview', 'could not read the overview')
}

// Every account.
function loadUsers() {
  return loadInto('users', '/api/v1/admin/users', 'could not read the accounts')
}

// One account. Cleared first, so the page never shows the previous person
// while the next one loads.
function loadUser(userId) {
  state.user = null
  return loadInto('user', '/api/v1/admin/users/' + userId, 'could not read that account')
}

// Every sync of every account.
function loadSyncs() {
  return loadInto('syncs', '/api/v1/admin/syncs', 'could not read the syncs')
}

// One sync, cleared first for the same reason as one account.
function loadSync(mappingId) {
  state.sync = null
  return loadInto('sync', '/api/v1/admin/syncs/' + mappingId, 'could not read that sync')
}

// The newest runs. Every filter that has a value goes on the query string,
// an empty one is left off so it does not filter on an empty string.
function loadRuns(filters) {
  const params = new URLSearchParams()
  Object.keys(filters).forEach(function (name) {
    if (filters[name]) {
      params.set(name, filters[name])
    }
  })

  let path = '/api/v1/admin/runs'
  const query = params.toString()
  if (query) {
    path = path + '?' + query
  }
  return loadInto('runs', path, 'could not read the runs')
}

// The newest warnings and errors from the log, from any part of the app.
function loadProblems() {
  return loadInto('problems', '/api/v1/admin/problems', 'could not read the log')
}

export function useAdmin() {
  return {
    state: readonly(state),
    loadOverview,
    loadUsers,
    loadUser,
    loadSyncs,
    loadSync,
    loadRuns,
    loadProblems,
  }
}
