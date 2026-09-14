import { reactive, readonly } from 'vue'
import { send } from './useAuth'
import { reloadSync, watchRun } from './useSync'

const BASE = '/api/v1/me/syncs'

const state = reactive({
  ready: false, // first load finished, so no screen flashes an empty list
  list: [], // MappingStatus rows, oldest first, the order the server returns
  // Date columns per mapping id. Each entry is a call out to Notion, so they
  // are fetched one mapping at a time, on demand.
  dateProperties: {},
  busy: false,
})

// Every sync this user has. Cheap, local rows only.
async function load() {
  const result = await send(BASE)

  if (result.data) {
    state.list = result.data
  } else {
    state.list = []
  }

  state.ready = true
}

// Replaces one row in the list, so a screen reading the list sees the change
// without a full reload.
function replace(mapping) {
  const index = state.list.findIndex(function (row) {
    return row.id === mapping.id
  })

  if (index === -1) {
    state.list = [...state.list, mapping]
  } else {
    const next = [...state.list]
    next[index] = mapping
    state.list = next
  }
}

// Starts syncing the given databases. The server infers each date column and
// creates or reuses a calendar, so this one call is the whole setup. It talks to
// Notion and iCloud, so it is the slowest call here.
async function create(dataSourceIds) {
  state.busy = true
  const result = await send(
    BASE,
    { method: 'POST', json: { data_source_ids: dataSourceIds } },
    'could not start syncing',
    'network error — is the API running?',
  )
  state.busy = false

  if (result.error) {
    return { error: result.error }
  }

  result.data.forEach(function (mapping) {
    replace(mapping)
  })

  // Creating a sync turns the master switch on, so the switch the Settings page
  // and the header read has to be re-read.
  await reloadSync()

  return { mappings: result.data }
}

// Sets any of a sync's fields. The server validates each one against Notion or
// iCloud before storing it.
async function update(mappingId, body) {
  state.busy = true
  const result = await send(
    BASE + '/' + mappingId,
    { method: 'PUT', json: body },
    'could not save',
    'network error — is the API running?',
  )
  state.busy = false

  if (result.error) {
    return { error: result.error }
  }

  replace(result.data)
  return {}
}

async function setDateProperty(mappingId, name) {
  return update(mappingId, { due_date_property: name })
}

async function setCalendar(mappingId, calendarUrl) {
  return update(mappingId, { calendar_url: calendarUrl })
}

// Turning a sync on queues a background run, so the page polls for it the same
// way the master switch does.
async function setEnabled(mappingId, enabled) {
  const result = await update(mappingId, { enabled })
  if (result.error) {
    return { error: result.error }
  }

  // Deliberately not awaited: the switch flips now, the run reports later.
  if (enabled) {
    watchRun()
  }

  return {}
}

// Removes a sync and the events it pushed. The server talks to iCloud here, so
// it is slower than the other calls.
async function remove(mappingId) {
  state.busy = true
  const result = await send(
    BASE + '/' + mappingId,
    { method: 'DELETE' },
    'could not remove the sync',
  )
  state.busy = false

  // A 404 means it was already gone, which is the outcome we wanted anyway.
  if (result.error && result.status !== 404) {
    return { error: result.error }
  }

  state.list = state.list.filter(function (row) {
    return row.id !== mappingId
  })
  const next = { ...state.dateProperties }
  delete next[mappingId]
  state.dateProperties = next
  return {}
}

// The date columns on one sync's database. A call out to Notion, so it runs when
// a picker opens rather than on page load.
async function fetchDateProperties(mappingId) {
  state.busy = true
  const result = await send(
    BASE + '/' + mappingId + '/date-properties',
    {},
    'could not read your database columns',
  )
  state.busy = false

  if (result.error) {
    return { error: result.error }
  }

  state.dateProperties = { ...state.dateProperties, [mappingId]: result.data }
  return {}
}

export function useMappings() {
  return {
    state: readonly(state),
    load,
    create,
    setDateProperty,
    setCalendar,
    setEnabled,
    remove,
    fetchDateProperties,
  }
}
