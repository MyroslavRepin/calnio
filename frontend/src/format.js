// A stored timestamp in the reader's own locale. The fallback differs by page:
// a connection says "—", a sync log says "never".
export function formatDateTime(value, fallback) {
  if (!value) {
    return fallback
  }

  return new Date(value).toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  })
}

// A calendar day like 2026-10-06, short enough to sit under a chart bar. Read
// as local midnight, or a reader west of UTC would see the day before.
export function formatDay(value) {
  return new Date(value + 'T00:00:00').toLocaleDateString(undefined, {
    day: 'numeric',
    month: 'short',
  })
}

// A run time in milliseconds, in the unit that reads best.
export function formatDuration(milliseconds, fallback) {
  if (milliseconds === null || milliseconds === undefined) {
    return fallback
  }
  if (milliseconds < 1000) {
    return milliseconds + ' ms'
  }
  if (milliseconds < 60000) {
    return (milliseconds / 1000).toFixed(1) + ' s'
  }
  return Math.round(milliseconds / 60000) + ' min'
}

// What to grep for on the server, handed over ready to paste.
export function grepCommand(term) {
  return 'grep "' + term + '" /srv/calnio/logs/calnio.log'
}
