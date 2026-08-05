import { reactive, readonly } from 'vue'
import { useAuth } from './useAuth'

const BASE = '/api/v1/me/notion'
const LOGIN = '/auth/oauth/notion/login'

const { apiFetch } = useAuth()

const state = reactive({
  ready: false, // first load finished (avoids flashing the wizard at a connected user)
  connection: null, // { connected, workspace_name, workspace_icon, data_source_id, data_source_name, last_verified_at } | null
  databases: [], // only the ones the user ticked in Notion's picker; fetched on demand
  busy: false, // a request that talks to Notion is in flight
  error: null, // set when the OAuth dance bounced back with ?notion_error=
})

// Why the dance can fail, in the user's terms. The backend never redirects with
// a flag it did not put here.
const OAUTH_ERRORS = {
  session: 'your session expired while you were in Notion — connect again',
  oauth: 'notion did not finish the authorization',
  token: 'notion sent back an unexpected response — try again',
}

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

// The callback redirects to /dashboard/connections?notion_error=… on failure.
// Read it once and strip it, so a refresh does not resurrect the message —
// same move useAuth's bootstrap makes with auth_error.
function consumeErrorFlag() {
  const params = new URLSearchParams(window.location.search)
  const flag = params.get('notion_error')
  if (!flag) return

  state.error = OAUTH_ERRORS[flag] || 'could not connect Notion'
  params.delete('notion_error')
  const query = params.toString()
  window.history.replaceState(
    {},
    '',
    window.location.pathname + (query ? `?${query}` : ''),
  )
}

async function load() {
  consumeErrorFlag()
  const res = await apiFetch(BASE)
  state.connection = res.ok ? await res.json() : null // 404 = not connected
  state.ready = true
}

// Sends the browser to Notion's consent screen.
//
// The authorize URL is fetched over apiFetch rather than linked to directly: the
// endpoint needs the access cookie, which lives 5 minutes, and apiFetch is the
// only thing that can refresh it. A plain <a href> would fail for anyone who
// left the dashboard open. Doubles as the "share more databases" action — Notion
// re-prompts and lets the user amend which pages they ticked.
async function connect() {
  state.busy = true
  state.error = null
  try {
    const res = await apiFetch(LOGIN)
    if (!res.ok) {
      state.busy = false
      return { error: await detail(res, 'could not start the Notion connection') }
    }
    const { authorize_url: authorizeUrl } = await res.json()
    // Deliberately leaves busy set — the button stays disabled while the
    // browser navigates away.
    window.location.href = authorizeUrl
    return {}
  } catch {
    state.busy = false
    return { error: 'network error — is the API running?' }
  }
}

async function fetchDatabases() {
  state.busy = true
  try {
    const res = await apiFetch(`${BASE}/databases`)
    if (!res.ok) return { error: await detail(res, 'could not list your databases') }
    state.databases = await res.json()
    return {}
  } catch {
    return { error: 'network error' }
  } finally {
    state.busy = false
  }
}

async function selectDatabase(dataSourceId) {
  state.busy = true
  try {
    const res = await apiFetch(`${BASE}/database`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ data_source_id: dataSourceId }),
    })
    if (!res.ok) return { error: await detail(res, 'could not save the database') }
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
    state.databases = []
    return {}
  } catch {
    return { error: 'network error' }
  } finally {
    state.busy = false
  }
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
