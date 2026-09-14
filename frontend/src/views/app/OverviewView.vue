<script setup>
import { computed } from 'vue'
import { useAppleCalendar } from '../../composables/useAppleCalendar'
import { useAuth } from '../../composables/useAuth'
import { useMappings } from '../../composables/useMappings'
import { useNotion } from '../../composables/useNotion'
import { useSetup } from '../../composables/useSetup'
import { useSync } from '../../composables/useSync'
import { formatDateTime } from '../../format'

// Read state from every composable this page needs. Nothing here
// fetches or changes anything, it only reads what is already loaded.
const appleResult = useAppleCalendar()
const apple = appleResult.state

const notionResult = useNotion()
const notion = notionResult.state

const mappingsResult = useMappings()
const mappings = mappingsResult.state

const syncResult = useSync()
const sync = syncResult.state

const authResult = useAuth()
const auth = authResult.state

const setupResult = useSetup()
const stages = setupResult.stages
const doneCount = setupResult.doneCount
const allDone = setupResult.allDone
const setupReady = setupResult.ready

// Is the page allowed to render yet? The composables load independently,
// so we wait until they all say they are ready.
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

// Last tick across every sync, formatted for humans.
const lastRun = computed(function () {
  return formatDateTime(sync.settings?.last_run_at, 'never')
})

// Master switch badge (on / off / currently running). This page only
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

// Result of the last tick.
const lastResult = computed(function () {
  const status = sync.settings?.last_status

  if (status === 'ok') {
    return { text: 'Finished normally', tone: 'success' }
  }
  if (status === 'error') {
    return { text: 'A sync failed, retrying on the next run', tone: 'danger' }
  }
  if (status === 'auth_error') {
    return { text: 'A connection was rejected, reconnect it', tone: 'danger' }
  }
  return { text: 'Nothing has run yet', tone: 'neutral' }
})

// The Notion workspace, or a dash when Notion did not give us a name.
const workspaceName = computed(function () {
  if (notion.connection?.workspace_name) {
    return notion.connection.workspace_name
  } else {
    return '—'
  }
})

// One line per sync: which database goes where, and whether it is running. The
// detail lives on the Syncs page, this is the glance.
const summaries = computed(function () {
  return mappings.list.map(function (mapping) {
    let database = mapping.data_source_name
    if (!database) {
      database = mapping.data_source_id
    }

    let calendar = mapping.calendar_name
    if (!calendar) {
      calendar = 'no calendar'
    }

    let state = 'Paused'
    if (!mapping.eligible) {
      state = 'Unfinished'
    } else if (mapping.enabled) {
      state = 'On'
    }

    return { id: mapping.id, database, calendar, state }
  })
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
          The walkthrough takes three steps and covers the app-specific password
          Apple requires.
        </p>
        <router-link class="btn" :to="{ name: 'welcome' }">Continue setup</router-link>
      </div>
    </section>

    <template v-else>
      <section class="card">
        <div class="card-head">
          <h2>Your syncs</h2>
          <router-link :to="{ name: 'syncs' }">Manage</router-link>
        </div>
        <div class="card-body">
          <dl class="datarows">
            <div v-for="summary in summaries" :key="summary.id">
              <dt>{{ summary.database }}</dt>
              <dd>{{ summary.calendar }} · {{ summary.state }}</dd>
            </div>
          </dl>
        </div>
      </section>

      <section class="card">
        <div class="card-head">
          <h2>Last run</h2>
          <span class="label" :class="lastResult.tone">{{ lastResult.text }}</span>
        </div>
        <div class="card-body">
          <dl class="datarows">
            <div>
              <dt>Finished</dt>
              <dd>{{ lastRun }}</dd>
            </div>
            <div>
              <dt>Notion workspace</dt>
              <dd>{{ workspaceName }}</dd>
            </div>
            <div>
              <dt>Apple Account</dt>
              <dd>{{ apple.connection.icloud_email }}</dd>
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
</style>
