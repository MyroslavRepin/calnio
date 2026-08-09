import { onMounted, reactive, readonly, watch } from 'vue'

// Where the API lives. In development Vite runs on :5173 and the API on :8080,
// so requests cross origins and cookies travel by CORS. In production both are
// the same origin, so an empty base keeps every request relative.
const API = import.meta.env.VITE_API_URL ?? ''

// Both tokens live in httpOnly cookies that the browser attaches on its own.
// The JavaScript never holds a token, only the derived UI state below.
const state = reactive({
  user: null, // { id, email, name, picture } or null
  ready: false, // bootstrap finished, so the UI can stop guessing
  error: null, // the ?auth_error= flag the callback bounced back with
})

// The refresh currently in flight, so ten parallel 401s cause one refresh.
let refreshing = null

// Asks the server for a new pair of cookies. Answers true when it worked.
function refresh() {
  if (refreshing) {
    return refreshing
  }

  refreshing = requestRefresh()
  return refreshing
}

async function requestRefresh() {
  try {
    const response = await fetch(API + '/auth/refresh', {
      method: 'POST',
      credentials: 'include',
    })
    return response.ok
  } catch {
    // No network. Treat it as not signed in.
    return false
  } finally {
    refreshing = null
  }
}

// One fetch with the cookies attached. On a 401 it refreshes once and tries
// the same request again.
async function apiFetch(path, options, retried) {
  const response = await fetch(API + path, {
    ...options,
    credentials: 'include',
  })

  if (response.status === 401 && !retried) {
    const refreshed = await refresh()
    if (refreshed) {
      return apiFetch(path, options, true)
    }
  }

  return response
}

// Runs one request and always answers the same shape:
//   { data, status }   when it worked
//   { error, status }  when it did not
// It never throws, so nothing that calls it needs a try/catch. Pass `json` and
// it sets the header and serialises the body for you.
export async function send(path, options, failMessage, networkMessage) {
  if (!options) {
    options = {}
  }
  if (!failMessage) {
    failMessage = 'something went wrong'
  }
  if (!networkMessage) {
    networkMessage = 'network error'
  }

  const request = { ...options }
  if (request.json !== undefined) {
    request.headers = { 'Content-Type': 'application/json' }
    request.body = JSON.stringify(request.json)
    delete request.json
  }

  let response
  try {
    response = await apiFetch(path, request, false)
  } catch {
    return { error: networkMessage }
  }

  // A 204 and a proxy error both leave us without a JSON body.
  let body = null
  try {
    body = await response.json()
  } catch {
    body = null
  }

  if (!response.ok) {
    // The API answers { detail } on every error.
    if (body?.detail) {
      return { error: body.detail, status: response.status }
    } else {
      return { error: failMessage, status: response.status }
    }
  }

  return { data: body, status: response.status }
}

// Runs the given loaders once a signed-in user exists. App.vue bootstraps auth
// after the router has resolved, so a bare onMounted would fire before the user
// is known and every call would come back 401.
export function loadWhenSignedIn(...loaders) {
  function run() {
    if (!state.ready || !state.user) {
      return
    }
    loaders.forEach(function (load) {
      load()
    })
  }

  onMounted(run)
  watch(function () {
    return [state.ready, state.user]
  }, run)
}

// Asks the server who is signed in.
async function fetchMe() {
  const result = await send('/auth/me')

  if (result.data) {
    state.user = result.data
  } else {
    state.user = null
  }
}

// Runs once when the app starts.
async function bootstrap() {
  const params = new URLSearchParams(window.location.search)
  if (params.has('auth_error')) {
    state.error = params.get('auth_error')
    window.history.replaceState({}, '', window.location.pathname)
  }

  await fetchMe()
  state.ready = true
}

// A real navigation, not a fetch: the browser has to follow the redirects to
// Google and back, and that is what sets the first-party state cookie.
function login() {
  window.location.href = API + '/auth/oauth/google/login'
}

async function logout() {
  await send('/auth/logout', { method: 'POST' })
  state.user = null
}

// Irreversible. The typed email is sent so the server can check it too. The
// caller does the redirect, because a full page load is what clears the
// module-level state the other composables hold.
async function deleteAccount(email) {
  const result = await send(
    '/api/v1/me',
    { method: 'DELETE', json: { email } },
    'could not delete your account',
    'could not reach the server',
  )

  if (result.error) {
    return { error: result.error }
  }

  state.user = null
  return {}
}

export function useAuth() {
  return {
    state: readonly(state),
    bootstrap,
    login,
    logout,
    deleteAccount,
  }
}
