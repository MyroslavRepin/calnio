<script setup>
import { computed, reactive } from 'vue'
import AppleCalendarSetup from '../../components/AppleCalendarSetup.vue'
import AppleCalendarStatus from '../../components/AppleCalendarStatus.vue'
import ConnectionRow from '../../components/ConnectionRow.vue'
import NotionSetup from '../../components/NotionSetup.vue'
import NotionStatus from '../../components/NotionStatus.vue'
import { useAppleCalendar } from '../../composables/useAppleCalendar'
import { useNotion } from '../../composables/useNotion'

const { state: apple } = useAppleCalendar()
const { state: notion } = useNotion()

// Both connections are two-stage: a stored credential/grant, then the target
// the user picked inside it. "Configured" is the second stage.
const appleConfigured = computed(() => Boolean(apple.connection?.calendar_url))
const notionConfigured = computed(() => Boolean(notion.connection?.data_source_id))

// Rows open by default until their setup is finished, so a first-time user
// lands straight in the wizard. Clicking sets an explicit override, per row.
const overrides = reactive({ apple: null, notion: null })

const appleOpen = computed(() =>
  overrides.apple === null ? !appleConfigured.value : overrides.apple,
)
const notionOpen = computed(() =>
  overrides.notion === null ? !notionConfigured.value : overrides.notion,
)

const appleStatus = computed(() => {
  if (!apple.ready) return 'checking…'
  if (appleConfigured.value) return apple.connection.icloud_email
  if (apple.connection) return 'no calendar selected'
  return 'not connected'
})

const notionStatus = computed(() => {
  if (!notion.ready) return 'checking…'
  if (notionConfigured.value) return notion.connection.data_source_name
  if (notion.connection) return 'no database selected'
  return 'not connected'
})
</script>

<template>
  <header class="head">
    <p class="eyebrow">Connections</p>
    <h1>Connections</h1>
    <p class="lede">
      Where Calnio reads your tasks from, and where it writes your events to.
    </p>
  </header>

  <div class="rows">
    <ConnectionRow
      name="Notion"
      :status="notionStatus"
      :action="notionConfigured ? 'manage' : 'connect'"
      :open="notionOpen"
      @toggle="overrides.notion = !notionOpen"
    >
      <p v-if="!notion.ready" class="muted">Loading…</p>
      <NotionStatus v-else-if="notionConfigured" />
      <NotionSetup v-else />
    </ConnectionRow>

    <ConnectionRow
      name="Apple Calendar"
      :status="appleStatus"
      :action="appleConfigured ? 'manage' : 'connect'"
      :open="appleOpen"
      @toggle="overrides.apple = !appleOpen"
    >
      <p v-if="!apple.ready" class="muted">Loading…</p>
      <AppleCalendarStatus v-else-if="appleConfigured" />
      <AppleCalendarSetup v-else />
    </ConnectionRow>
  </div>

  <p class="note">
    Connecting Notion links your workspace and records which database Calnio
    should read. Syncing still runs on Calnio's own workspace during beta — your
    database is not being read yet.
  </p>
</template>

<style scoped>
.head {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-bottom: 32px;
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

.rows {
  border-top: 1px solid var(--hairline);
}

.note {
  font-size: 13px;
  line-height: 1.6;
  color: var(--muted);
  max-width: 520px;
  padding-top: 24px;
}

.muted {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--muted);
  padding: 20px 0;
}
</style>
