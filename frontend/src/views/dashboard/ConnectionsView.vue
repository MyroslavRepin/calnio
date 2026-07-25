<script setup>
import { computed, ref } from 'vue'
import AppleCalendarSetup from '../../components/AppleCalendarSetup.vue'
import AppleCalendarStatus from '../../components/AppleCalendarStatus.vue'
import ConnectionRow from '../../components/ConnectionRow.vue'
import { useAppleCalendar } from '../../composables/useAppleCalendar'

const { state: apple } = useAppleCalendar()

const connected = computed(() => Boolean(apple.connection))
const configured = computed(() => Boolean(apple.connection?.calendar_url))

// Open by default until setup is finished, so a first-time user lands straight
// in the wizard. Clicking sets an explicit override.
const override = ref(null)
const appleOpen = computed(() =>
  override.value === null ? !configured.value : override.value,
)

const appleStatus = computed(() => {
  if (!apple.ready) return 'checking…'
  if (configured.value) return apple.connection.icloud_email
  if (connected.value) return 'no calendar selected'
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
      name="Apple Calendar"
      :status="appleStatus"
      :action="configured ? 'manage' : 'connect'"
      :open="appleOpen"
      @toggle="override = !appleOpen"
    >
      <p v-if="!apple.ready" class="muted">Loading…</p>
      <AppleCalendarStatus v-else-if="configured" />
      <AppleCalendarSetup v-else />
    </ConnectionRow>

    <ConnectionRow name="Notion" status="managed by calnio during beta" />
  </div>

  <p class="note">
    Notion is connected on Calnio's side during beta — per-workspace Notion
    connections arrive with per-user syncing.
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
