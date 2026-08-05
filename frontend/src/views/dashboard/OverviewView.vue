<script setup>
import { computed } from 'vue'
import { useAppleCalendar } from '../../composables/useAppleCalendar'
import { useAuth } from '../../composables/useAuth'
import { useNotion } from '../../composables/useNotion'
import { useSync } from '../../composables/useSync'

const { state: apple } = useAppleCalendar()
const { state: notion } = useNotion()
const { state: sync } = useSync()
const { state: auth } = useAuth()

// The four setup stages, same definitions the welcome page counts: a grant
// stored, then a target picked, for each connection. The walkthrough itself
// lives on /welcome, this page only reports where you are.
const stages = computed(() => [
  { label: 'Notion workspace connected', done: Boolean(notion.connection) },
  { label: 'Notion database chosen', done: Boolean(notion.connection?.data_source_id) },
  { label: 'iCloud account connected', done: Boolean(apple.connection) },
  { label: 'Apple calendar chosen', done: Boolean(apple.connection?.calendar_url) },
])

const ready = computed(() => notion.ready && apple.ready && sync.ready)
const doneCount = computed(() => stages.value.filter((s) => s.done).length)
const allDone = computed(() => doneCount.value === stages.value.length)

const greeting = computed(() => {
  const name = auth.user?.name || auth.user?.email || ''
  return name ? `Hi, ${name}` : 'Overview'
})

// The calendar list is not fetched on load (it hits iCloud and is slow), so the
// name is only known if this session already loaded it, fall back to the URL.
const calendarName = computed(() => {
  const url = apple.connection?.calendar_url
  if (!url) return '—'
  return apple.calendars.find((c) => c.url === url)?.name || url
})

const lastRun = computed(() => {
  const at = sync.settings?.last_run_at
  return at ? new Date(at).toLocaleString() : 'never'
})

// Reporting only, the switch itself lives in Settings, so this never shows a
// second control for the same state.
const syncLabel = computed(() => {
  if (sync.pending) return { text: 'Syncing now', tone: 'accent' }
  if (sync.settings?.enabled) return { text: 'Sync on', tone: 'success' }
  return { text: 'Sync off', tone: 'neutral' }
})

const lastResult = computed(() => {
  switch (sync.settings?.last_status) {
    case 'ok':
      return { text: 'Finished normally', tone: 'success' }
    case 'error':
      return { text: 'Failed, retrying on the next run', tone: 'danger' }
    case 'auth_error':
      return { text: 'A connection was rejected, reconnect it', tone: 'danger' }
    default:
      return { text: 'Nothing has run yet', tone: 'neutral' }
  }
})
</script>

<template>
  <p v-if="!ready" class="loading">Loading…</p>

  <template v-else>
    <header class="page-head">
      <div class="headline">
        <h1 class="title">{{ greeting }}</h1>
        <span class="label" :class="syncLabel.tone">{{ syncLabel.text }}</span>
      </div>
      <p class="lead">
        Calnio pushes your Notion due dates into Apple Calendar. Notion stays the
        source of truth, nothing is ever written back to it.
      </p>
    </header>

    <!-- Unfinished: point at the walkthrough, do not repeat it here. -->
    <section v-if="!allDone" class="card setup">
      <div class="card-head">
        <h2>Finish setup</h2>
        <span class="label attention">{{ doneCount }} of {{ stages.length }} done</span>
      </div>
      <div class="card-body">
        <ul class="checks">
          <li v-for="stage in stages" :key="stage.label" :class="{ done: stage.done }">
            <span class="mark">{{ stage.done ? '✓' : '○' }}</span>
            <span>{{ stage.label }}</span>
          </li>
        </ul>
        <p class="body">
          The walkthrough takes four steps and covers the app-specific password
          Apple requires.
        </p>
        <router-link class="btn" :to="{ name: 'welcome' }">Continue setup</router-link>
      </div>
    </section>

    <template v-else>
      <section class="card">
        <div class="card-head">
          <h2>Notion</h2>
          <router-link :to="{ name: 'connections' }">Manage</router-link>
        </div>
        <div class="card-body">
          <dl class="datarows">
            <div>
              <dt>Workspace</dt>
              <dd>{{ notion.connection.workspace_name || '—' }}</dd>
            </div>
            <div>
              <dt>Database</dt>
              <dd>{{ notion.connection.data_source_name }}</dd>
            </div>
            <div>
              <dt>Due date column</dt>
              <dd>{{ sync.settings?.due_date_property || '—' }}</dd>
            </div>
          </dl>
        </div>
      </section>

      <section class="card">
        <div class="card-head">
          <h2>Apple Calendar</h2>
          <router-link :to="{ name: 'connections' }">Manage</router-link>
        </div>
        <div class="card-body">
          <dl class="datarows">
            <div>
              <dt>Apple Account</dt>
              <dd>{{ apple.connection.icloud_email }}</dd>
            </div>
            <div>
              <dt>Calendar</dt>
              <dd>{{ calendarName }}</dd>
            </div>
          </dl>
        </div>
      </section>

      <section class="card">
        <div class="card-head">
          <h2>Sync activity</h2>
          <router-link :to="{ name: 'settings' }">Sync settings</router-link>
        </div>
        <div class="card-body">
          <dl class="datarows">
            <div>
              <dt>Status</dt>
              <dd>
                <span class="label" :class="syncLabel.tone">{{ syncLabel.text }}</span>
              </dd>
            </div>
            <div>
              <dt>Last run</dt>
              <dd>{{ lastRun }}</dd>
            </div>
            <div>
              <dt>Result</dt>
              <dd>
                <span class="label" :class="lastResult.tone">{{ lastResult.text }}</span>
              </dd>
            </div>
          </dl>

          <p v-if="!sync.settings?.enabled" class="note off">
            Syncing is off, so nothing is being pushed to your calendar. Turn it
            on in Settings.
          </p>
        </div>
      </section>
    </template>
  </template>
</template>

<style scoped>
.headline {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--app-gap-stack);
}
/* Setup checklist. A tick or a ring, no icon set to pull in. */
.checks {
  list-style: none;
  margin: 0 0 var(--app-gap-block);
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--app-gap-inline);
}

.checks li {
  display: flex;
  align-items: center;
  gap: var(--app-gap-inline);
  font-size: var(--app-text-body);
  color: var(--app-fg-muted);
}

.checks li.done {
  color: var(--app-fg);
}

.mark {
  width: var(--app-space-4);
  text-align: center;
  color: var(--app-fg-subtle);
}

.checks li.done .mark {
  color: var(--app-success);
}

.card-body .body {
  margin-bottom: var(--app-gap-block);
}

.off {
  margin-top: var(--app-gap-stack);
}
</style>
