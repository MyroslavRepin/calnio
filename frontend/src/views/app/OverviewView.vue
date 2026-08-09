<script setup>
import { computed } from 'vue'
import { useAppleCalendar } from '../../composables/useAppleCalendar'
import { useAuth } from '../../composables/useAuth'
import { useNotion } from '../../composables/useNotion'
import { useSetup } from '../../composables/useSetup'
import { useSync } from '../../composables/useSync'
import { formatDateTime } from '../../format'
import RecentSyncs from './RecentSyncs.vue'

// Read state from every composable this page needs. Nothing here
// fetches or changes anything, it only reads what is already loaded.
const appleResult = useAppleCalendar()
const apple = appleResult.state

const notionResult = useNotion()
const notion = notionResult.state

const syncResult = useSync()
const sync = syncResult.state

const authResult = useAuth()
const auth = authResult.state

const setupResult = useSetup()
const stages = setupResult.stages
const doneCount = setupResult.doneCount
const allDone = setupResult.allDone
const setupReady = setupResult.ready

// Is the page allowed to render yet? Two composables load independently,
// so we wait until both say they are ready.
const ready = computed(function () {
  if (setupReady.value && sync.ready) {
    return true
  } else {
    return false
  }
})

// Greeting text at the top of the page.
const greeting = computed(function () {
  let name = auth.user?.name

  if (!name) {
    name = auth.user?.email
  }
  if (!name) {
    name = ''
  }

  if (name) {
    return 'Hi, ' + name
  } else {
    return 'Overview'
  }
})

// Calendar name for display. The backend stores it alongside the url, so
// this is the normal case. Older rows saved before that existed fall back to
// this session's fetched list, then to the raw url.
const calendarName = computed(function () {
  if (apple.connection?.calendar_name) {
    return apple.connection.calendar_name
  }

  const url = apple.connection?.calendar_url

  if (!url) {
    return '—'
  }

  const match = apple.calendars.find(function (calendar) {
    return calendar.url === url
  })

  if (match) {
    return match.name
  } else {
    return url
  }
})

// Last sync run, formatted for humans.
const lastRun = computed(function () {
  return formatDateTime(sync.settings?.last_run_at, 'never')
})

// Sync status badge (on / off / currently running). This page only
// reports the switch, the switch itself lives in Settings.
const syncLabel = computed(function () {
  if (sync.pending) {
    return { text: 'Syncing now', tone: 'accent' }
  }
  if (sync.settings?.enabled) {
    return { text: 'Sync on', tone: 'success' }
  }
  return { text: 'Sync off', tone: 'neutral' }
})

// Result of the last sync run.
const lastResult = computed(function () {
  const status = sync.settings?.last_status

  if (status === 'ok') {
    return { text: 'Finished normally', tone: 'success' }
  }
  if (status === 'error') {
    return { text: 'Failed, retrying on the next run', tone: 'danger' }
  }
  if (status === 'auth_error') {
    return { text: 'A connection was rejected, reconnect it', tone: 'danger' }
  }
  return { text: 'Nothing has run yet', tone: 'neutral' }
})

// The Notion workspace, or a dash when Notion did not give us a name.
const workspaceName = computed(function () {
  if (notion.connection.workspace_name) {
    return notion.connection.workspace_name
  } else {
    return '—'
  }
})

// The date column the sync reads, or a dash when none is picked yet.
const dueDateColumn = computed(function () {
  if (sync.settings?.due_date_property) {
    return sync.settings.due_date_property
  } else {
    return '—'
  }
})
</script>

<template>
  <p v-if="!ready" class="loading">Loading…</p>

  <template v-else>
    <header class="column page-head">
      <div class="row headline">
        <h1 class="title">{{ greeting }}</h1>
        <span class="label" :class="syncLabel.tone">{{ syncLabel.text }}</span>
      </div>
      <p class="lead">
        Calnio pushes your Notion due dates into Apple Calendar. Notion stays the
        source of truth, nothing is ever written back to it.
      </p>
    </header>

    <!-- Unfinished: point at the walkthrough, do not repeat it here. -->
    <section v-if="!allDone" class="card">
      <div class="card-head">
        <h2>Finish setup</h2>
        <span class="label attention">{{ doneCount }} of {{ stages.length }} done</span>
      </div>
      <div class="card-body">
        <ul class="column checks">
          <li v-for="stage in stages" :key="stage.label" class="row" :class="{ done: stage.done }">
            <span class="checkmark">{{ stage.done ? '✓' : '○' }}</span>
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
              <dd>{{ workspaceName }}</dd>
            </div>
            <div>
              <dt>Database</dt>
              <dd>{{ notion.connection.data_source_name }}</dd>
            </div>
            <div>
              <dt>Due date column</dt>
              <dd>{{ dueDateColumn }}</dd>
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
    </template>
  </template>
</template>

<style scoped>
.column {
  gap: var(--gap)
}

.headline {
  --gap: var(--app-gap-stack);
}

/* Setup checklist. A tick or a ring, no icon set to pull in. */
.checks {
  --gap: var(--app-gap-inline);
  list-style: none;
  margin: 0 0 var(--app-gap-block);
  padding: 0;
}

.checks li {
  --gap: var(--app-gap-inline);
  font-size: var(--app-text-body);
  color: var(--app-fg-muted);
}

.checks li.done {
  color: var(--app-fg);
}

.checkmark {
  width: var(--app-space-4);
  text-align: center;
  color: var(--app-fg-subtle);
}

.checks li.done .checkmark {
  color: var(--app-success);
}

.card-body .body {
  margin-bottom: var(--app-gap-block);
}

.syncoffnote {
  margin-top: var(--app-gap-stack);
}
</style>
