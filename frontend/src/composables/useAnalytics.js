// Custom events for the self-hosted Umami (analytics.myroslavrepin.com). The
// tracker is a plain <script> in index.html; this file only talks to the global
// it defines.

// What the backend may put in ?event= after an OAuth redirect. Anything else is
// ignored, so a hand-typed URL cannot invent events.
const REDIRECT_EVENTS = ['signup', 'login', 'notion_connected', 'notion_reconnected']

// Sends one event. Never throws: an ad-blocker or a dev build without the
// tracker simply means nothing is recorded.
export function track(name, data) {
  function fire() {
    if (window.umami) {
      window.umami.track(name, data)
    }
  }

  // The tracker is deferred and may not have run yet when the app boots. It is
  // always done by the window load event.
  if (window.umami || document.readyState === 'complete') {
    fire()
  } else {
    window.addEventListener('load', fire, { once: true })
  }
}

// Reads the ?event= flag the backend redirects with, records it once and strips
// it, so a refresh does not count it twice.
export function consumeEventFlag() {
  const params = new URLSearchParams(window.location.search)
  const event = params.get('event')

  if (!event) {
    return
  }

  if (REDIRECT_EVENTS.includes(event)) {
    track(event)
  }

  params.delete('event')
  const query = params.toString()
  if (query) {
    window.history.replaceState({}, '', window.location.pathname + '?' + query)
  } else {
    window.history.replaceState({}, '', window.location.pathname)
  }
}
