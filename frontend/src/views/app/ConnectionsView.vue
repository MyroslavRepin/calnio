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

// This page is only about the two grants: the Notion token and the iCloud
// password. Which database goes into which calendar lives on the Syncs page.
const appleConnected = computed(() => {
  return Boolean(apple.connection)
})

const notionConnected = computed(() => {
  return Boolean(notion.connection)
})

// Rows open by default until the grant is stored, so a first-time user lands
// straight in the wizard. Clicking a row sets an explicit override.
const overrides = reactive({ apple: null, notion: null })

const appleOpen = computed(() => {
  if (overrides.apple === null) {
    return !appleConnected.value
  } else {
    return overrides.apple
  }
})

const notionOpen = computed(() => {
  if (overrides.notion === null) {
    return !notionConnected.value
  } else {
    return overrides.notion
  }
})

// The one-line summary in each row's header: who we are connected as.
const appleStatus = computed(() => {
  if (!apple.ready) {
    return { text: 'Checking…', tone: 'neutral' }
  }
  if (appleConnected.value) {
    return { text: apple.connection.icloud_email, tone: 'success' }
  }
  return { text: 'Not connected', tone: 'neutral' }
})

const notionStatus = computed(() => {
  if (!notion.ready) {
    return { text: 'Checking…', tone: 'neutral' }
  }
  if (notionConnected.value) {
    if (notion.connection.workspace_name) {
      return { text: notion.connection.workspace_name, tone: 'success' }
    }
    return { text: 'Connected', tone: 'success' }
  }
  return { text: 'Not connected', tone: 'neutral' }
})
</script>

<template>
  <header class="column page-head">
    <h1 class="title">Connections</h1>
    <p class="lead">
      The two accounts Calnio needs: the Notion workspace it reads, and the
      iCloud account it writes to.
    </p>
  </header>

  <ConnectionRow
    name="Notion"
    :status="notionStatus.text"
    :tone="notionStatus.tone"
    :action="notionConnected ? 'Manage' : 'Connect'"
    :open="notionOpen"
    @toggle="overrides.notion = !notionOpen"
  >
    <p v-if="!notion.ready" class="loading">Loading…</p>
    <NotionStatus v-else-if="notionConnected" />
    <NotionSetup v-else />
  </ConnectionRow>

  <ConnectionRow
    name="Apple Calendar"
    :status="appleStatus.text"
    :tone="appleStatus.tone"
    :action="appleConnected ? 'Manage' : 'Connect'"
    :open="appleOpen"
    @toggle="overrides.apple = !appleOpen"
  >
    <p v-if="!apple.ready" class="loading">Loading…</p>
    <AppleCalendarStatus v-else-if="appleConnected" />
    <AppleCalendarSetup v-else />
  </ConnectionRow>

  <p class="note">
    With both connected, set up what actually syncs on the
    <router-link :to="{ name: 'syncs' }">Syncs</router-link> page.
  </p>
</template>

<style scoped>
.note {
  padding-top: var(--app-space-4);
}
</style>
