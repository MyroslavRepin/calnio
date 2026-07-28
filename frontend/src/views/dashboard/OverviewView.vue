<script setup>
import { computed } from 'vue'
import { useAppleCalendar } from '../../composables/useAppleCalendar'
import { useNotion } from '../../composables/useNotion'

const { state: apple } = useAppleCalendar()
const { state: notion } = useNotion()

// The four setup stages, same definitions the welcome page counts: a grant
// stored, then a target picked, for each connection. The walkthrough itself
// lives on /welcome — this page only reports where you are.
const stages = computed(() => [
  Boolean(notion.connection),
  Boolean(notion.connection?.data_source_id),
  Boolean(apple.connection),
  Boolean(apple.connection?.calendar_url),
])

const ready = computed(() => notion.ready && apple.ready)
const doneCount = computed(() => stages.value.filter(Boolean).length)
const allDone = computed(() => doneCount.value === stages.value.length)

// The calendar list is not fetched on load (it hits iCloud and is slow), so the
// name is only known if this session already loaded it — fall back to the URL.
const calendarName = computed(() => {
  const url = apple.connection?.calendar_url
  if (!url) return '—'
  return apple.calendars.find((c) => c.url === url)?.name || url
})
</script>

<template>
  <p v-if="!ready" class="muted">Loading…</p>

  <template v-else>
    <header class="head">
      <p class="eyebrow">Overview</p>
      <h1>{{ allDone ? 'Your sync is set up' : 'Finish your setup' }}</h1>
      <p class="lede">
        Calnio pushes your Notion due dates into Apple Calendar. Notion stays the
        source of truth — nothing is ever written back to it.
      </p>
    </header>

    <!-- Unfinished: point at the walkthrough, do not repeat it here. -->
    <section v-if="!allDone" class="block">
      <h2 class="eyebrow">Setup — {{ doneCount }} of {{ stages.length }}</h2>
      <p class="note">
        Your setup is not finished, so nothing is connected end to end yet. The
        walkthrough takes four steps and covers the app-specific password Apple
        requires.
      </p>
      <router-link class="btn-primary" :to="{ name: 'welcome' }">
        Continue setup
      </router-link>
    </section>

    <template v-else>
      <section class="block">
        <h2 class="eyebrow">Notion</h2>
        <dl class="rows">
          <div class="row">
            <dt>Workspace</dt>
            <dd>{{ notion.connection.workspace_name || '—' }}</dd>
          </div>
          <div class="row">
            <dt>Database</dt>
            <dd>{{ notion.connection.data_source_name }}</dd>
          </div>
          <div class="row">
            <dt>Pages</dt>
            <dd>—</dd>
          </div>
          <div class="row">
            <dt>With a due date</dt>
            <dd>—</dd>
          </div>
        </dl>
      </section>

      <section class="block">
        <h2 class="eyebrow">Apple Calendar</h2>
        <dl class="rows">
          <div class="row">
            <dt>Apple Account</dt>
            <dd>{{ apple.connection.icloud_email }}</dd>
          </div>
          <div class="row">
            <dt>Calendar</dt>
            <dd>{{ calendarName }}</dd>
          </div>
          <div class="row">
            <dt>Events synced</dt>
            <dd>—</dd>
          </div>
        </dl>
      </section>

      <section class="block">
        <h2 class="eyebrow">Sync activity</h2>
        <dl class="rows">
          <div class="row">
            <dt>Last run</dt>
            <dd>—</dd>
          </div>
          <div class="row">
            <dt>Created</dt>
            <dd>—</dd>
          </div>
          <div class="row">
            <dt>Updated</dt>
            <dd>—</dd>
          </div>
          <div class="row">
            <dt>Deleted</dt>
            <dd>—</dd>
          </div>
        </dl>

        <p class="note">
          These numbers switch on when syncing your own workspace does, later in
          beta. Your setup carries over when it lands.
        </p>

        <router-link class="link-mono" :to="{ name: 'connections' }">
          Manage connections
        </router-link>
      </section>
    </template>
  </template>
</template>

<style scoped>
.head {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-bottom: 40px;
  max-width: 640px;
}

h1 {
  font-size: 40px;
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1.05;
}

.lede {
  font-size: 17px;
  line-height: 1.6;
  color: var(--body);
}

.block {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 20px;
  padding: 32px 0 40px;
  border-top: 1px solid var(--hairline);
}

.rows {
  list-style: none;
  margin: 0;
  padding: 0;
  border-top: 1px solid var(--hairline);
  width: 100%;
  max-width: 640px;
}

.row {
  display: grid;
  grid-template-columns: 180px 1fr;
  gap: 24px;
  padding: 14px 0;
  border-bottom: 1px solid var(--hairline);
}

dt {
  font-size: 15px;
  color: var(--ink);
}

dd {
  margin: 0;
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--muted);
  overflow-wrap: anywhere;
}

.note {
  font-size: 15px;
  line-height: 1.6;
  color: var(--body);
  max-width: 520px;
}

.link-mono {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--muted);
  border-bottom: 1px solid var(--hairline);
  padding-bottom: 2px;
}

.link-mono:hover {
  color: var(--ink);
  border-bottom-color: var(--ink);
}

.muted {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--muted);
  padding: 20px 0;
}
</style>
