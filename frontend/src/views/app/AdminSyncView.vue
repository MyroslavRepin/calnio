<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import DayChart from '../../components/app/DayChart.vue'
import RunTable from '../../components/app/RunTable.vue'
import StatusLabel from '../../components/app/StatusLabel.vue'
import { useAdmin } from '../../composables/useAdmin'
import { formatDateTime, grepCommand } from '../../format'

const route = useRoute()

const adminResult = useAdmin()
const admin = adminResult.state
const loadSync = adminResult.loadSync

const error = ref(null)

// Loads the sync in the URL, again whenever the id in it changes.
async function load() {
  // Leaving this page changes the route before the view goes away, so a
  // missing id means there is nothing to load.
  if (!route.query.id) {
    return
  }

  error.value = null
  const result = await loadSync(route.query.id)
  if (result.error) {
    error.value = result.error
  }
}

watch(
  function () {
    return route.query.id
  },
  load,
  { immediate: true },
)

const detail = computed(function () {
  return admin.sync
})

const sync = computed(function () {
  return detail.value.sync
})

const runSeries = [
  { key: 'runs_ok', name: 'ok', tone: 'success' },
  { key: 'runs_failed', name: 'failed', tone: 'danger' },
]
const calendarSeries = [
  { key: 'created', name: 'created', tone: 'accent' },
  { key: 'updated', name: 'updated', tone: 'neutral' },
  { key: 'deleted', name: 'deleted', tone: 'attention' },
]
const notionSeries = [
  { key: 'pulled', name: 'pulled', tone: 'accent' },
  { key: 'imported', name: 'imported', tone: 'success' },
  { key: 'trashed', name: 'trashed', tone: 'attention' },
]

// The page title: the database's name, or the id when it has none.
const title = computed(function () {
  if (sync.value.database) {
    return sync.value.database
  } else {
    return 'Sync #' + sync.value.id
  }
})

// The sync's state: unfinished or paused says so before its last run.
const status = computed(function () {
  if (!sync.value.eligible) {
    return 'unfinished'
  }
  if (!sync.value.enabled) {
    return 'paused'
  }
  return sync.value.last_status
})

// Two-way, with the moment it went on, since only newer events are imported.
const twoWay = computed(function () {
  if (!sync.value.two_way) {
    return 'off'
  }
  return 'on since ' + formatDateTime(detail.value.write_back_since, 'unknown')
})

// Imports need a calendar this sync has to itself.
const calendarShare = computed(function () {
  if (detail.value.shares_calendar === 0) {
    return 'no, imports allowed'
  }
  return 'with ' + detail.value.shares_calendar + ' other syncs, imports off'
})

function orUnset(value) {
  if (value) {
    return value
  } else {
    return 'not set'
  }
}

function yesNo(flag) {
  if (flag) {
    return 'yes'
  } else {
    return 'no'
  }
}

function whenLabel(value) {
  return formatDateTime(value, 'never')
}
</script>

<template>
  <p v-if="error" class="error">{{ error }}</p>
  <p v-else-if="!detail" class="loading">Loading…</p>

  <template v-else>
    <header class="column page-head">
      <h1 class="title">{{ title }}</h1>
      <p class="lead">
        Sync <span class="ident">#{{ sync.id }}</span> of
        <router-link :to="{ name: 'admin-user', query: { id: sync.user_id } }">
          {{ sync.email }}
        </router-link>
        <span class="ident"> #{{ sync.user_id }}</span>.
      </p>
    </header>

    <!-- Everything stored about this sync, and how to find its log lines. -->
    <section class="card">
      <div class="card-head">
        <h2>Sync</h2>
        <StatusLabel :status="status" />
      </div>
      <div class="card-body column status">
        <dl class="datarows">
          <div>
            <dt>ID</dt>
            <dd><code>{{ sync.id }}</code></dd>
          </div>
          <div>
            <dt>Notion data source</dt>
            <dd><code>{{ sync.data_source_id }}</code></dd>
          </div>
          <div>
            <dt>Date column</dt>
            <dd>{{ orUnset(sync.date_property) }}</dd>
          </div>
          <div>
            <dt>Apple calendar</dt>
            <dd>{{ orUnset(sync.calendar) }}</dd>
          </div>
          <div>
            <dt>Shares its calendar</dt>
            <dd>{{ calendarShare }}</dd>
          </div>
          <div>
            <dt>Switched on</dt>
            <dd>{{ yesNo(sync.enabled) }}</dd>
          </div>
          <div>
            <dt>Two-way</dt>
            <dd>{{ twoWay }}</dd>
          </div>
          <div>
            <dt>Calendar sync token stored</dt>
            <dd>{{ yesNo(detail.has_sync_token) }}</dd>
          </div>
          <div>
            <dt>Events Calnio keeps in step</dt>
            <dd>{{ sync.events }}</dd>
          </div>
          <div>
            <dt>Created</dt>
            <dd>{{ whenLabel(sync.created_at) }}</dd>
          </div>
          <div>
            <dt>Last run</dt>
            <dd>{{ whenLabel(sync.last_run_at) }}</dd>
          </div>
          <div v-if="sync.last_run_id">
            <dt>Last run id</dt>
            <dd>
              <router-link :to="{ name: 'admin-runs', query: { run_id: sync.last_run_id } }">
                <code>{{ sync.last_run_id }}</code>
              </router-link>
            </dd>
          </div>
        </dl>
        <p v-if="sync.last_error" class="error">{{ sync.last_error }}</p>
        <code>{{ grepCommand('sync=' + sync.id) }}</code>
      </div>
    </section>

    <section class="card">
      <div class="card-head">
        <h2>Runs, 30 days</h2>
        <span class="label neutral">{{ sync.runs_7d }} runs, {{ sync.failed_7d }} failed in 7 days</span>
      </div>
      <div class="card-body">
        <DayChart :days="detail.days" :series="runSeries" />
      </div>
    </section>

    <section class="card">
      <div class="card-head">
        <h2>Work done, 30 days</h2>
      </div>
      <div class="card-body column charts">
        <p class="note">Written into Apple Calendar</p>
        <DayChart :days="detail.days" :series="calendarSeries" />
        <p class="note">Written back into Notion</p>
        <DayChart :days="detail.days" :series="notionSeries" />
      </div>
    </section>

    <section class="card">
      <div class="card-head">
        <h2>Failure reasons, 7 days</h2>
      </div>
      <div class="card-body">
        <p v-if="!detail.run_errors.length" class="note">No run of this sync failed this week.</p>
        <div v-else class="tablebox">
          <table class="datatable">
            <thead>
              <tr>
                <th>Reason</th>
                <th>Runs</th>
                <th>Last seen</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="group in detail.run_errors" :key="group.error">
                <td class="reason">{{ group.error }}</td>
                <td>{{ group.runs }}</td>
                <td>{{ whenLabel(group.last_seen) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <section class="card">
      <div class="card-head">
        <h2>Latest runs</h2>
        <router-link :to="{ name: 'admin-runs', query: { mapping_id: sync.id } }">
          All runs of this sync
        </router-link>
      </div>
      <div class="card-body">
        <RunTable :runs="detail.runs" />
      </div>
    </section>
  </template>
</template>
