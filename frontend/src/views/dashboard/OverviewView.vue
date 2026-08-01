<script setup>
import { computed } from 'vue'
import { useAppleCalendar } from '../../composables/useAppleCalendar'
import { useNotion } from '../../composables/useNotion'
import { useSync } from '../../composables/useSync'

const { state: apple } = useAppleCalendar()
const { state: notion } = useNotion()
const { state: sync } = useSync()

// The four setup stages, same definitions the welcome page counts: a grant
// stored, then a target picked, for each connection. The walkthrough itself
// lives on /welcome — this page only reports where you are.
const stages = computed(() => [
  Boolean(notion.connection),
  Boolean(notion.connection?.data_source_id),
  Boolean(apple.connection),
  Boolean(apple.connection?.calendar_url),
])

const ready = computed(() => notion.ready && apple.ready && sync.ready)
const doneCount = computed(() => stages.value.filter(Boolean).length)
const allDone = computed(() => doneCount.value === stages.value.length)

// The calendar list is not fetched on load (it hits iCloud and is slow), so the
// name is only known if this session already loaded it — fall back to the URL.
const calendarName = computed(() => {
  const url = apple.connection?.calendar_url
  if (!url) return '—'
  return apple.calendars.find((c) => c.url === url)?.name || url
})

const lastRun = computed(() => {
  const at = sync.settings?.last_run_at
  return at ? new Date(at).toLocaleString() : '—'
})

// Reporting only — the switch itself lives in Settings, so this never shows a
// second control for the same state.
const syncState = computed(() => {
  if (sync.pending) return 'Syncing now'
  return sync.settings?.enabled ? 'On' : 'Off'
})

const lastResult = computed(() => {
  switch (sync.settings?.last_status) {
    case 'ok':
      return 'Finished normally'
    case 'error':
      return 'Failed — retrying on the next run'
    case 'auth_error':
      return 'A connection was rejected — reconnect it'
    default:
      return '—'
  }
})
</script>

<template>
  <p v-if="!ready" class="loading">Loading…</p>

  <template v-else>
    <header class="head">
      <p class="eyebrow">Overview</p>
      <h1 class="title">{{ allDone ? 'Your sync is set up.' : 'Finish your setup.' }}</h1>
      <p class="lead">
        Calnio pushes your Notion due dates into Apple Calendar. Notion stays the
        source of truth — nothing is ever written back to it.
      </p>
    </header>

    <!-- Unfinished: point at the walkthrough, do not repeat it here. -->
    <section v-if="!allDone" class="block">
      <p class="eyebrow">Setup — {{ doneCount }} of {{ stages.length }}</p>
      <p class="body">
        Nothing is connected end to end yet. The walkthrough takes four steps and
        covers the app-specific password Apple requires.
      </p>
      <router-link class="btn" :to="{ name: 'welcome' }">Continue setup</router-link>
    </section>

    <template v-else>
      <section class="block">
        <p class="eyebrow">Notion</p>
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
            <dt>Pages</dt>
            <dd>—</dd>
          </div>
          <div>
            <dt>With a due date</dt>
            <dd>—</dd>
          </div>
        </dl>
      </section>

      <section class="block">
        <p class="eyebrow">Apple Calendar</p>
        <dl class="datarows">
          <div>
            <dt>Apple Account</dt>
            <dd>{{ apple.connection.icloud_email }}</dd>
          </div>
          <div>
            <dt>Calendar</dt>
            <dd>{{ calendarName }}</dd>
          </div>
          <div>
            <dt>Events synced</dt>
            <dd>—</dd>
          </div>
        </dl>
      </section>

      <section class="block">
        <p class="eyebrow">Sync activity</p>
        <dl class="datarows">
          <div>
            <dt>Syncing</dt>
            <dd>{{ syncState }}</dd>
          </div>
          <div>
            <dt>Due date column</dt>
            <dd>{{ sync.settings?.due_date_property || '—' }}</dd>
          </div>
          <div>
            <dt>Last run</dt>
            <dd>{{ lastRun }}</dd>
          </div>
          <div>
            <dt>Result</dt>
            <dd>{{ lastResult }}</dd>
          </div>
        </dl>

        <p v-if="!sync.settings?.enabled" class="note">
          Syncing is off, so nothing is being pushed to your calendar. Turn it
          on in Settings.
        </p>

        <div class="actions">
          <router-link class="link-mono quiet" :to="{ name: 'settings' }">
            <span>Sync settings</span>
          </router-link>
          <router-link class="link-mono quiet" :to="{ name: 'connections' }">
            <span>Manage connections</span>
          </router-link>
        </div>
      </section>
    </template>
  </template>
</template>

<style scoped>
.head {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-bottom: clamp(28px, 5vw, 40px);
}

.block {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: clamp(16px, 2.5vw, 20px);
  padding: clamp(24px, 4vw, 32px) 0 clamp(28px, 5vw, 40px);
  border-top: 1px solid var(--hairline);
}

.body {
  font-size: 15px;
  line-height: 1.6;
  color: var(--body);
  max-width: 52ch;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 28px;
}
</style>
