import { reactive, readonly } from 'vue'
import { send } from './useAuth'

const BASE = '/api/v1/me/notion'
const LOGIN = '/auth/oauth/notion/login'

const state = reactive({
  ready: false, // first load finished, so the wizard never flashes at a connected user
  connection: null, // { connected, workspace_name, data_source_id, data_source_name, last_verified_at }
  databases: [], // only the ones ticked in Notion's picker, fetched on demand
  busy: false,
  error: null, // set when the OAuth dance bounced back with ?notion_error=
})

// Why the dance can fail, in the user's terms. The backend never redirects with
// a flag it did not put here.
const OAUTH_ERRORS = {
  session: 'your session expired while you were in Notion — connect again',
  oauth: 'notion did not finish the authorization',
  token: 'notion sent back an unexpected response — try again',
}

// Reads the failure flag off the URL once and strips it, so a refresh does not
// resurrect the message.
function consumeErrorFlag() {
  const params = new URLSearchParams(window.location.search)
  const flag = params.get('notion_error')

  if (!flag) {
    return
  }

  if (OAUTH_ERRORS[flag]) {
    state.error = OAUTH_ERRORS[flag]
  } else {
    state.error = 'could not connect Notion'
  }

  params.delete('notion_error')
  const query = params.toString()
  if (query) {
    window.history.replaceState({}, '', window.location.pathname + '?' + query)
  } else {
    window.history.replaceState({}, '', window.location.pathname)
  }
}

// The stored connection, or null when there is none.
async function load() {
  consumeErrorFlag()

  const result = await send(BASE)

  if (result.data) {
    state.connection = result.data
  } else {
    state.connection = null // a 404 means not connected
  }

  state.ready = true
}

// Sends the browser to Notion's consent screen.
//
// The authorize URL is fetched rather than linked to, because the endpoint
// needs the access cookie, which lives five minutes, and only apiFetch can
// refresh it. A plain <a href> would fail for anyone who left the dashboard
// open. This doubles as "share more databases": Notion re-prompts and lets the
// user amend what they ticked.
async function connect() {
  state.busy = true
  state.error = null

  const result = await send(
    LOGIN,
    {},
    'could not start the Notion connection',
    'network error — is the API running?',
  )

  if (result.error) {
    state.busy = false
    return { error: result.error }
  }

  // busy stays set on purpose: the button must remain disabled while the
  // browser navigates away.
  window.location.href = result.data.authorize_url
  return {}
}

async function fetchDatabases() {
  state.busy = true
  const result = await send(BASE + '/databases', {}, 'could not list your databases')
  state.busy = false

  if (result.error) {
    return { error: result.error }
  }

  state.databases = result.data
  return {}
}

async function selectDatabase(dataSourceId) {
  state.busy = true
  const result = await send(
    BASE + '/database',
    { method: 'PUT', json: { data_source_id: dataSourceId } },
    'could not save the database',
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
  state.databases = []
  return {}
}

export function useNotion() {
  return {
    state: readonly(state),
    load,
    connect,
    fetchDatabases,
    selectDatabase,
    disconnect,
  }
}
