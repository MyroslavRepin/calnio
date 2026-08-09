// A stored timestamp in the reader's own locale. The fallback differs by page:
// a connection says "—", a sync log says "never".
export function formatDateTime(value, fallback) {
  if (!value) {
    return fallback
  }

  return new Date(value).toLocaleString()
}
