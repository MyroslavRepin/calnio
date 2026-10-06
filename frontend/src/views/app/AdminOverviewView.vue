<script setup>
import { computed, onMounted, ref } from 'vue'
import DayChart from '../../components/app/DayChart.vue'
import StatusLabel from '../../components/app/StatusLabel.vue'
import { useAdmin } from '../../composables/useAdmin'
import { formatDateTime, formatDay, formatDuration, grepCommand } from '../../format'

// The whole page is one request. It counts every row in the database, so it
// runs when this page opens rather than on the shell's shared load.
const adminResult = useAdmin()
const admin = adminResult.state
const loadOverview = adminResult.loadOverview

const error = ref(null)

onMounted(async function () {
  const result = await loadOverview()
  if (result.error) {
    error.value = result.error
  }
})

// Shorthand for the answer, so the template reads overview.health rather than
// admin.overview.health.
const overview = computed(function () {
  return admin.overview
})

// The series each chart stacks, bottom first.
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
const signupSeries = [{ key: 'signups', name: 'signups', tone: 'accent' }]
const newSyncSeries = [{ key: 'syncs_created', name: 'new syncs', tone: 'success' }]

// The headline numbers, each with what it means in a few words.
const figures = computed(function () {
  const totals = overview.value.totals
  const health = overview.value.health
  return [
    { name: 'Accounts, +' + totals.signed_up_7d + ' this week', value: totals.users },
    { name: 'Syncing right now', value: totals.syncing },
    { name: 'Runs in 24 hours', value: health.runs_24h },
    { name: 'Run success, 24 hours', value: percentLabel(health.success_rate_24h) },
    { name: 'Run success, 7 days', value: percentLabel(health.success_rate_7d) },
    { name: 'Median run, 24 hours', value: formatDuration(health.median_ms_24h, 'no runs') },
    { name: 'Slowest 5% take over', value: formatDuration(health.p95_ms_24h, 'no runs') },
    { name: 'Syncs failing now', value: health.failing },
    { name: 'Syncs not run for 3 ticks', value: health.stale },
    { name: 'Errors logged, 24 hours', value: health.errors_24h },
    { name: 'Warnings logged, 24 hours', value: health.warnings_24h },
  ]
})

// A percentage that may be missing when there was nothing to rate.
function percentLabel(value) {
  if (value === null) {
    return 'no runs'
  } else {
    return value + '%'
  }
}

// How many people are stuck before the last step that matters.
const notSyncing = computed(function () {
  return overview.value.totals.users - overview.value.totals.syncing
})

// The median wait from signing in to a first sync, in hours or days.
const timeToSync = computed(function () {
  const hours = overview.value.activation.median_hours_to_sync
  if (hours === null) {
    return 'nobody has made a sync yet'
  }
  if (hours < 48) {
    return hours + ' hours'
  }
  return Math.round(hours / 24) + ' days'
})

// The largest bucket, so the distribution bars have something to be a share of.
const biggestBucket = computed(function () {
  let most = 1
  overview.value.syncs_per_user.forEach(function (bucket) {
    if (bucket.count > most) {
      most = bucket.count
    }
  })
  return most
})

function bucketWidth(count) {
  return Math.round((count * 100) / biggestBucket.value) + '%'
}

// A cohort cell: the count, and its share of that week's signups.
function cohortCell(count, users) {
  if (users === 0) {
    return '0'
  }
  return count + ' (' + Math.round((count * 100) / users) + '%)'
}

// A failure with no recorded reason predates that column, or crashed before
// anything could be written down.
function failureReason(reason) {
  if (reason) {
    return reason
  } else {
    return 'No reason recorded. Check the log around that time.'
  }
}

function whenLabel(value) {
  return formatDateTime(value, 'never')
}
</script>

<template>
  <p v-if="error" class="error">{{ error }}</p>
  <p v-else-if="!overview" class="loading">Loading…</p>

  <template v-else>
    <header class="column page-head">
      <h1 class="title">Admin</h1>
      <p class="lead">
        Every account, counted fresh on each load. Runs are kept for 90 days.
      </p>
    </header>

    <!-- The numbers worth knowing before anything else. -->
    <section class="card">
      <div class="card-head">
        <h2>Right now</h2>
        <router-link :to="{ name: 'admin-errors' }">Errors</router-link>
      </div>
      <div class="card-body grid figures">
        <div v-for="figure in figures" :key="figure.name" class="column">
          <span class="figurevalue">{{ figure.value }}</span>
          <span class="figurename">{{ figure.name }}</span>
        </div>
      </div>
    </section>

    <!-- Every sync run per day. A red day is the one to open the log for. -->
    <section class="card">
      <div class="card-head">
        <h2>Sync runs, 30 days</h2>
        <router-link :to="{ name: 'admin-runs' }">All runs</router-link>
      </div>
      <div class="card-body">
        <DayChart :days="overview.days" :series="runSeries" />
      </div>
    </section>

    <!-- What the runs actually changed, in each direction. -->
    <section class="card">
      <div class="card-head">
        <h2>Work done, 30 days</h2>
      </div>
      <div class="card-body column charts">
        <p class="note">Written into Apple Calendar</p>
        <DayChart :days="overview.days" :series="calendarSeries" />
        <p class="note">Written back into Notion by two-way syncs</p>
        <DayChart :days="overview.days" :series="notionSeries" />
      </div>
    </section>

    <!-- Who arrived, and what they set up. -->
    <section class="card">
      <div class="card-head">
        <h2>Growth, 30 days</h2>
      </div>
      <div class="card-body column charts">
        <DayChart :days="overview.days" :series="signupSeries" />
        <DayChart :days="overview.days" :series="newSyncSeries" />
      </div>
    </section>

    <!-- Setup as a sequence, so the step that loses people is the one you see. -->
    <section class="card">
      <div class="card-head">
        <h2>Setup funnel</h2>
      </div>
      <div class="card-body column funnel">
        <div v-for="step in overview.funnel" :key="step.name" class="column funnelstep">
          <div class="row funnelnumbers">
            <span class="stepname">{{ step.name }}</span>
            <span class="stepcount">{{ step.count }} · {{ step.share }}%</span>
          </div>
          <div class="sharetrack" role="presentation">
            <div class="sharefill" :style="{ width: step.share + '%' }" />
          </div>
        </div>
        <p class="note">
          {{ notSyncing }} people signed in and are not syncing.
        </p>
      </div>
    </section>

    <!-- How fast people get going, and who can use two-way at all. -->
    <section class="card">
      <div class="card-head">
        <h2>Activation</h2>
      </div>
      <div class="card-body">
        <dl class="datarows">
          <div>
            <dt>Median time from sign in to first sync</dt>
            <dd>{{ timeToSync }}</dd>
          </div>
          <div>
            <dt>Made a sync within a day</dt>
            <dd>{{ overview.activation.within_1d }}% of accounts</dd>
          </div>
          <div>
            <dt>Made a sync within a week</dt>
            <dd>{{ overview.activation.within_7d }}% of accounts</dd>
          </div>
          <div>
            <dt>Notion grants that can write</dt>
            <dd>{{ overview.activation.notion_can_write }}</dd>
          </div>
          <div>
            <dt>Read-only grants, must reconnect for two-way</dt>
            <dd>{{ overview.activation.notion_read_only }}</dd>
          </div>
        </dl>
      </div>
    </section>

    <!-- Each signup week on its own row, so a bad week is not averaged away. -->
    <section class="card">
      <div class="card-head">
        <h2>Signup weeks</h2>
      </div>
      <div class="card-body tablebox">
        <table class="datatable">
          <thead>
            <tr>
              <th>Week of</th>
              <th>Signed up</th>
              <th>Notion</th>
              <th>iCloud</th>
              <th>Made a sync</th>
              <th>Syncing now</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="cohort in overview.cohorts" :key="cohort.week">
              <td>{{ formatDay(cohort.week) }}</td>
              <td>{{ cohort.users }}</td>
              <td>{{ cohortCell(cohort.notion, cohort.users) }}</td>
              <td>{{ cohortCell(cohort.icloud, cohort.users) }}</td>
              <td>{{ cohortCell(cohort.with_sync, cohort.users) }}</td>
              <td>{{ cohortCell(cohort.syncing, cohort.users) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- How many databases people sync, which says whether N syncs is used. -->
    <section class="card">
      <div class="card-head">
        <h2>Syncs per account</h2>
      </div>
      <div class="card-body column funnel">
        <div v-for="bucket in overview.syncs_per_user" :key="bucket.name" class="column funnelstep">
          <div class="row funnelnumbers">
            <span class="stepname">{{ bucket.name }}</span>
            <span class="stepcount">{{ bucket.count }}</span>
          </div>
          <div class="sharetrack" role="presentation">
            <div class="sharefill" :style="{ width: bucketWidth(bucket.count) }" />
          </div>
        </div>
      </div>
    </section>

    <!-- The syncs themselves, and what they have produced. -->
    <section class="card">
      <div class="card-head">
        <h2>Syncs</h2>
        <router-link :to="{ name: 'admin-syncs' }">All syncs</router-link>
      </div>
      <div class="card-body">
        <dl class="datarows">
          <div>
            <dt>Syncs</dt>
            <dd>{{ overview.syncs.mappings }}</dd>
          </div>
          <div>
            <dt>Switched on</dt>
            <dd>{{ overview.syncs.enabled }}</dd>
          </div>
          <div>
            <dt>Fully configured</dt>
            <dd>{{ overview.syncs.eligible }}</dd>
          </div>
          <div>
            <dt>Two-way</dt>
            <dd>{{ overview.syncs.two_way }}</dd>
          </div>
          <div>
            <dt>Last run ok</dt>
            <dd>{{ overview.syncs.ok }}</dd>
          </div>
          <div>
            <dt>Last run failed</dt>
            <dd>{{ overview.syncs.error }}</dd>
          </div>
          <div>
            <dt>Credentials rejected</dt>
            <dd>{{ overview.syncs.auth_error }}</dd>
          </div>
          <div>
            <dt>Never run</dt>
            <dd>{{ overview.syncs.never_run }}</dd>
          </div>
          <div>
            <dt>Events Calnio keeps in step</dt>
            <dd>{{ overview.events.linked_events }}</dd>
          </div>
          <div>
            <dt>Notion databases in use</dt>
            <dd>{{ overview.events.databases }}</dd>
          </div>
          <div>
            <dt>Apple calendars written to</dt>
            <dd>{{ overview.events.calendars }}</dd>
          </div>
        </dl>
      </div>
    </section>

    <!-- Why runs failed this week, the commonest reason first. -->
    <section class="card">
      <div class="card-head">
        <h2>Failure reasons, 7 days</h2>
      </div>
      <div class="card-body">
        <p v-if="!overview.run_errors.length" class="note">No run failed this week.</p>
        <div v-else class="tablebox">
          <table class="datatable">
            <thead>
              <tr>
                <th>Reason</th>
                <th>Runs</th>
                <th>Syncs</th>
                <th>Last seen</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="group in overview.run_errors" :key="group.error">
                <td class="reason">{{ group.error }}</td>
                <td>{{ group.runs }}</td>
                <td>{{ group.syncs }}</td>
                <td>{{ whenLabel(group.last_seen) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- What is broken right now, with the reason and the way to chase it. -->
    <section class="card">
      <div class="card-head">
        <h2>Failing syncs</h2>
        <span class="label" :class="overview.failures.length ? 'danger' : 'success'">
          {{ overview.failures.length }}
        </span>
      </div>
      <div class="card-body column failures">
        <p v-if="!overview.failures.length" class="note">
          Nothing is failing. Every sync's last run finished.
        </p>

        <div v-for="failure in overview.failures" :key="failure.mapping_id" class="column failure">
          <div class="row failurehead">
            <router-link :to="{ name: 'admin-sync', query: { id: failure.mapping_id } }">
              {{ failure.database }}
              <span class="ident">#{{ failure.mapping_id }}</span>
            </router-link>
            <StatusLabel :status="failure.status" />
          </div>
          <p class="note">
            <router-link :to="{ name: 'admin-user', query: { id: failure.user_id } }">
              {{ failure.email }}
            </router-link>
            <span class="ident"> #{{ failure.user_id }}</span>
            · {{ whenLabel(failure.last_run_at) }}
          </p>
          <p class="error">{{ failureReason(failure.error) }}</p>
          <code v-if="failure.run_id">{{ grepCommand('run=' + failure.run_id) }}</code>
        </div>
      </div>
    </section>
  </template>
</template>

<style scoped>

.funnel {
  --gap: var(--app-gap-stack);
}

.funnelstep {
  --gap: var(--app-space-1);
}

.funnelnumbers {
  --gap: var(--app-gap-inline);
  justify-content: space-between;
}

.stepname {
  font-size: var(--app-text-body);
  color: var(--app-fg);
}

.stepcount {
  font-size: var(--app-text-meta);
  color: var(--app-fg-muted);
}

.sharetrack {
  width: 100%;
  height: 6px;
  border-radius: var(--app-radius-pill);
  background: var(--app-canvas-subtle);
}

.sharefill {
  height: 6px;
  border-radius: var(--app-radius-pill);
  background: var(--app-accent);
}

.failures {
  --gap: var(--app-gap-block);
}

.failure {
  --gap: var(--app-space-1);
}

.failurehead {
  --gap: var(--app-gap-inline);
  justify-content: space-between;
}
</style>
