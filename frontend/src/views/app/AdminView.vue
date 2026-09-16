<script setup>
import { computed, onMounted, ref } from 'vue'
import { useAdmin } from '../../composables/useAdmin'
import { formatDateTime } from '../../format'

// The whole page is one request. It counts every row in the database, so it
// runs when this page opens rather than on the shell's shared load.
const adminResult = useAdmin()
const admin = adminResult.state
const load = adminResult.load

const error = ref(null)

onMounted(async function () {
  const result = await load()
  if (result.error) {
    error.value = result.error
  }
})

// Each section reads its own slice, with an empty stand-in before the answer
// arrives, so the template never reaches through a null.
const totals = computed(function () {
  if (admin.stats) {
    return admin.stats.totals
  } else {
    return {}
  }
})

const syncs = computed(function () {
  if (admin.stats) {
    return admin.stats.syncs
  } else {
    return {}
  }
})

const events = computed(function () {
  if (admin.stats) {
    return admin.stats.events
  } else {
    return {}
  }
})

const funnel = computed(function () {
  if (admin.stats) {
    return admin.stats.funnel
  } else {
    return []
  }
})

const signups = computed(function () {
  if (admin.stats) {
    return admin.stats.signups
  } else {
    return []
  }
})

const people = computed(function () {
  if (admin.stats) {
    return admin.stats.users
  } else {
    return []
  }
})

// The tallest day, so the signup bars have something to be a share of. One is
// the floor, because dividing by zero draws nothing at all.
const busiestDay = computed(function () {
  let most = 1
  signups.value.forEach(function (day) {
    if (day.count > most) {
      most = day.count
    }
  })
  return most
})

// How many people are stuck before the last step that matters, which is the
// number worth acting on.
const notSyncing = computed(function () {
  if (admin.stats) {
    return totals.value.users - totals.value.syncing
  } else {
    return 0
  }
})

// A day of the signup chart, short enough to sit under a bar.
function dayLabel(value) {
  const parts = value.split('-')
  return parts[2] + '/' + parts[1]
}

// The height of one signup bar, as a share of the busiest day.
function dayHeight(count) {
  return Math.round((count * 100) / busiestDay.value) + '%'
}

// A person's last tick, said the way the sync cards say it.
function statusLabel(status) {
  if (status === 'ok') {
    return { text: 'ok', tone: 'success' }
  }
  if (status === 'error') {
    return { text: 'failed', tone: 'danger' }
  }
  if (status === 'auth_error') {
    return { text: 'rejected', tone: 'danger' }
  }
  return { text: 'never run', tone: 'neutral' }
}

// A yes or no column, written out rather than left as true and false.
function yesNo(flag) {
  if (flag) {
    return 'yes'
  } else {
    return 'no'
  }
}

function joinedLabel(value) {
  return formatDateTime(value, '—')
}
</script>

<template>
  <p v-if="!admin.ready" class="loading">Loading…</p>

  <template v-else>
    <header class="column page-head">
      <h1 class="title">Admin</h1>
      <p class="lead">
        Every account's numbers, counted fresh on each load. Aggregates only:
        no tokens, no passwords, no page titles.
      </p>
    </header>

    <!-- The headline numbers, the ones worth knowing before anything else. -->
    <section class="card">
      <div class="card-head">
        <h2>People</h2>
        <span class="label accent">{{ totals.users }} total</span>
      </div>
      <div class="card-body">
        <dl class="datarows">
          <div>
            <dt>Signed up in the last 7 days</dt>
            <dd>{{ totals.signed_up_7d }}</dd>
          </div>
          <div>
            <dt>Signed up in the last 30 days</dt>
            <dd>{{ totals.signed_up_30d }}</dd>
          </div>
          <div>
            <dt>Connected Notion</dt>
            <dd>{{ totals.notion_connected }}</dd>
          </div>
          <div>
            <dt>Connected iCloud</dt>
            <dd>{{ totals.icloud_connected }}</dd>
          </div>
          <div>
            <dt>Connected both</dt>
            <dd>{{ totals.both_connected }}</dd>
          </div>
          <div>
            <dt>Syncing right now</dt>
            <dd>{{ totals.syncing }}</dd>
          </div>
          <div>
            <dt>Using two-way</dt>
            <dd>{{ totals.two_way }}</dd>
          </div>
        </dl>
        <p class="note">
          {{ notSyncing }} people signed in and are not syncing. The funnel below
          says where they stopped.
        </p>
      </div>
    </section>

    <!-- Setup as a sequence, so the step that loses people is the one you see. -->
    <section class="card">
      <div class="card-head">
        <h2>Setup funnel</h2>
      </div>
      <div class="card-body column funnel">
        <div v-for="step in funnel" :key="step.name" class="column funnelstep">
          <div class="row funnelnumbers">
            <span class="stepname">{{ step.name }}</span>
            <span class="stepcount">{{ step.count }} · {{ step.share }}%</span>
          </div>
          <div class="sharetrack" role="presentation">
            <div class="sharefill" :style="{ width: step.share + '%' }" />
          </div>
        </div>
      </div>
    </section>

    <!-- Who arrived, and when. Empty days are drawn as empty, not skipped. -->
    <section class="card">
      <div class="card-head">
        <h2>Signups, last 14 days</h2>
      </div>
      <div class="card-body">
        <div class="row daychart">
          <div v-for="day in signups" :key="day.day" class="column daycolumn">
            <span class="daycount">{{ day.count }}</span>
            <div class="daytrack" role="presentation">
              <div class="dayfill" :style="{ height: dayHeight(day.count) }" />
            </div>
            <span class="dayname">{{ dayLabel(day.day) }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- The syncs themselves, and what they have produced. -->
    <section class="card">
      <div class="card-head">
        <h2>Syncs</h2>
        <span class="label neutral">{{ syncs.mappings }} total</span>
      </div>
      <div class="card-body">
        <dl class="datarows">
          <div>
            <dt>Switched on</dt>
            <dd>{{ syncs.enabled }}</dd>
          </div>
          <div>
            <dt>Fully configured</dt>
            <dd>{{ syncs.eligible }}</dd>
          </div>
          <div>
            <dt>Two-way</dt>
            <dd>{{ syncs.two_way }}</dd>
          </div>
          <div>
            <dt>Last run ok</dt>
            <dd>{{ syncs.ok }}</dd>
          </div>
          <div>
            <dt>Last run failed</dt>
            <dd>{{ syncs.error }}</dd>
          </div>
          <div>
            <dt>Credentials rejected</dt>
            <dd>{{ syncs.auth_error }}</dd>
          </div>
          <div>
            <dt>Never run</dt>
            <dd>{{ syncs.never_run }}</dd>
          </div>
          <div>
            <dt>Events Calnio keeps in step</dt>
            <dd>{{ events.linked_events }}</dd>
          </div>
          <div>
            <dt>Notion databases in use</dt>
            <dd>{{ events.databases }}</dd>
          </div>
          <div>
            <dt>Apple calendars written to</dt>
            <dd>{{ events.calendars }}</dd>
          </div>
        </dl>
      </div>
    </section>

    <!-- One row per account. Wide, so it scrolls inside its own box. -->
    <section class="card">
      <div class="card-head">
        <h2>Accounts</h2>
        <span class="label neutral">{{ people.length }}</span>
      </div>
      <div class="card-body">
        <div class="tablebox">
          <table class="accounts">
            <thead>
              <tr>
                <th>Email</th>
                <th>Joined</th>
                <th>Notion</th>
                <th>iCloud</th>
                <th>Syncs</th>
                <th>On</th>
                <th>Two-way</th>
                <th>Events</th>
                <th>Last run</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="person in people" :key="person.id">
                <td>
                  {{ person.email }}
                  <span v-if="person.is_admin" class="label accent">admin</span>
                </td>
                <td>{{ joinedLabel(person.joined) }}</td>
                <td>{{ yesNo(person.notion) }}</td>
                <td>{{ yesNo(person.icloud) }}</td>
                <td>{{ person.mappings }}</td>
                <td>{{ person.enabled_mappings }}</td>
                <td>{{ person.two_way_mappings }}</td>
                <td>{{ person.events }}</td>
                <td>{{ joinedLabel(person.last_run_at) }}</td>
                <td>
                  <span class="label" :class="statusLabel(person.last_status).tone">
                    {{ statusLabel(person.last_status).text }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <p v-if="error" class="error pageerror">{{ error }}</p>
  </template>
</template>

<style scoped>
.card-body > * + * {
  margin-top: var(--app-gap-stack);
}

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

.daychart {
  --gap: var(--app-space-2);
  align-items: flex-end;
}

.daycolumn {
  --gap: var(--app-space-1);
  flex: 1 1 0;
  align-items: center;
}

.daycount {
  font-size: var(--app-text-meta);
  color: var(--app-fg-muted);
}

.daytrack {
  display: flex;
  align-items: flex-end;
  width: 100%;
  height: 72px;
  border-radius: var(--app-radius-sm);
  background: var(--app-canvas-subtle);
}

.dayfill {
  width: 100%;
  min-height: 2px;
  border-radius: var(--app-radius-sm);
  background: var(--app-accent);
}

.dayname {
  font-size: var(--app-text-meta);
  color: var(--app-fg-subtle);
}

/* The table is wider than the page on a laptop, so it scrolls inside the card
   rather than pushing the whole page sideways. */
.tablebox {
  overflow-x: auto;
}

.accounts {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--app-text-body);
  white-space: nowrap;
}

.accounts th {
  padding: var(--app-space-2) var(--app-space-3) var(--app-space-2) 0;
  border-bottom: 1px solid var(--app-border);
  font-size: var(--app-text-meta);
  font-weight: var(--app-weight-bold);
  color: var(--app-fg-muted);
  text-align: left;
}

.accounts td {
  padding: var(--app-space-2) var(--app-space-3) var(--app-space-2) 0;
  border-bottom: 1px solid var(--app-border-subtle);
  color: var(--app-fg);
}

.accounts tr:last-child td {
  border-bottom: none;
}

.pageerror {
  margin-top: var(--app-gap-block);
}
</style>
