<script setup>
import { computed, reactive } from 'vue'
import AppleCalendarSetup from '../../components/app/AppleCalendarSetup.vue'
import AppleCalendarStatus from '../../components/app/AppleCalendarStatus.vue'
import ConnectionRow from '../../components/app/ConnectionRow.vue'
import NotionSetup from '../../components/app/NotionSetup.vue'
import NotionStatus from '../../components/app/NotionStatus.vue'
import { useAppleCalendar } from '../../composables/useAppleCalendar'
import { useNotion } from '../../composables/useNotion'

const appleResult = useAppleCalendar()
const apple = appleResult.state

const notionResult = useNotion()
const notion = notionResult.state

// Both connections are two-stage: a stored credential or grant, then the target
// the user picked inside it. "Configured" is the second stage.
const appleConfigured = computed(() => {
  return Boolean(apple.connection?.calendar_url)
})

const notionConfigured = computed(() => {
  return Boolean(notion.connection?.data_source_id)
})

// Rows open by default until their setup is finished, so a first-time user
// lands straight in the wizard. Clicking a row sets an explicit override.
const overrides = reactive({ apple: null, notion: null })

const appleOpen = computed(() => {
  if (overrides.apple === null) {
    return !appleConfigured.value
  } else {
    return overrides.apple
  }
})

const notionOpen = computed(() => {
  if (overrides.notion === null) {
    return !notionConfigured.value
  } else {
    return overrides.notion
  }
})

// The one-line summary in each row's header.
const appleStatus = computed(() => {
  if (!apple.ready) {
    return { text: 'Checking…', tone: 'neutral' }
  }
  if (appleConfigured.value) {
    return { text: apple.connection.icloud_email, tone: 'success' }
  }
  if (apple.connection) {
    return { text: 'No calendar selected', tone: 'attention' }
  }
  return { text: 'Not connected', tone: 'neutral' }
})

const notionStatus = computed(() => {
  if (!notion.ready) {
    return { text: 'Checking…', tone: 'neutral' }
  }
  if (notionConfigured.value) {
    return { text: notion.connection.data_source_name, tone: 'success' }
  }
  if (notion.connection) {
    return { text: 'No database selected', tone: 'attention' }
  }
  return { text: 'Not connected', tone: 'neutral' }
})
</script>

<template>
  <header class="column page-head">
    <h1 class="title">Connections</h1>
    <p class="lead">
      Where Calnio reads your tasks from, and where it writes your events to.
    </p>
  </header>

  <ConnectionRow
    name="Notion"
    :status="notionStatus.text"
    :tone="notionStatus.tone"
    :action="notionConfigured ? 'Manage' : 'Connect'"
    :open="notionOpen"
    @toggle="overrides.notion = !notionOpen"
  >
    <p v-if="!notion.ready" class="loading">Loading…</p>
    <NotionStatus v-else-if="notionConfigured" />
    <NotionSetup v-else />
  </ConnectionRow>

  <ConnectionRow
    name="Apple Calendar"
    :status="appleStatus.text"
    :tone="appleStatus.tone"
    :action="appleConfigured ? 'Manage' : 'Connect'"
    :open="appleOpen"
    @toggle="overrides.apple = !appleOpen"
  >
    <p v-if="!apple.ready" class="loading">Loading…</p>
    <AppleCalendarStatus v-else-if="appleConfigured" />
    <AppleCalendarSetup v-else />
  </ConnectionRow>

  <p class="note">
    Connecting Notion links your workspace and records which database Calnio
    should read. During beta the sync still runs on Calnio's own workspace, so
    your database is not being read yet.
  </p>
</template>

<style scoped>
.note {
  padding-top: var(--app-space-4);
}
</style>
