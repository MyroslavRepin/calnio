import { reactive, readonly } from 'vue'

// API origin. Dev: Vite :5173 → API :8080 (cross-origin, cookies via CORS).
// Prod: same origin, so an empty base ('') keeps requests relative.
const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8080'

// Both tokens live in httpOnly cookies the browser sends automatically — the
// JS never holds a token. We only track derived UI state here.
const state = reactive({
  user: null, // { user_id, email, name, picture } | null
  ready: false, // bootstrap finished (avoids UI flicker before we know auth)
  error: null, // last auth error flag (e.g. from ?auth_error=oauth)
})

let refreshing = null // in-flight refresh promise, so parallel 401s share one

async function refresh() {
  // De-dupe: many requests hitting 401 at once trigger a single refresh.
  if (refreshing) return refreshing

  refreshing = (async () => {
    try {
      const res = await fetch(`${API}/auth/refresh`, {
        method: 'POST',
        credentials: 'include',
      })
      return res.ok // server rotated both cookies; nothing to read here
    } catch {
      return false // network error — treat as not-authenticated
    } finally {
      refreshing = null
    }
  })()

  return refreshing
}

// fetch wrapper: sends cookies and transparently refreshes once on a 401.
async function apiFetch(path, options = {}, _retried = false) {
  const res = await fetch(`${API}${path}`, {
    ...options,
    credentials: 'include',
  })

  if (res.status === 401 && !_retried) {
    const ok = await refresh()
    if (ok) return apiFetch(path, options, true)
  }

  return res
}

async function fetchMe() {
  const res = await apiFetch('/auth/me')
  if (res.ok) {
    state.user = await res.json()
    return true
  }
  state.user = null
  return false
}

// Called once on app load: the access cookie (if any) authenticates /auth/me;
// apiFetch auto-refreshes from the refresh cookie when the access one expired.
async function bootstrap() {
  const params = new URLSearchParams(window.location.search)
  if (params.has('auth_error')) {
    state.error = params.get('auth_error')
    window.history.replaceState({}, '', window.location.pathname)
  }

  await fetchMe()
  state.ready = true
}

function login() {
  // Top-level navigation (not fetch): the OAuth redirect flow needs the browser
  // to follow 302s to Google and back, and sets the first-party state cookie.
  window.location.href = `${API}/auth/oauth/google/login`
}

async function logout() {
  try {
    await fetch(`${API}/auth/logout`, { method: 'POST', credentials: 'include' })
  } catch {
    // Ignore network failure — clear local state regardless.
  }
  state.user = null
}

export function useAuth() {
  return {
    state: readonly(state),
    apiFetch,
    bootstrap,
    login,
    logout,
    fetchMe,
  }
}
