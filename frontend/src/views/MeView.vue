<script setup>
import { computed, onMounted, watch } from 'vue'
import AppleCalendarSetup from '../components/AppleCalendarSetup.vue'
import AppleCalendarStatus from '../components/AppleCalendarStatus.vue'
import TheNav from '../components/TheNav.vue'
import { useAppleCalendar } from '../composables/useAppleCalendar'
import { useAuth } from '../composables/useAuth'

const { state: auth, login } = useAuth()
const { state: apple, load } = useAppleCalendar()

// Setup is finished only when credentials are stored *and* a calendar is picked.
const configured = computed(() => Boolean(apple.connection?.calendar_url))

// App.vue bootstraps auth; wait for a user before asking for their connection,
// otherwise the first call 401s during a page refresh.
function loadIfAuthed() {
  if (auth.ready && auth.user) load()
}

onMounted(loadIfAuthed)
watch(() => [auth.ready, auth.user], loadIfAuthed)
</script>

<template>
  <TheNav />

  <main class="wrap dash">
    <template v-if="!auth.ready">
      <p class="muted">Loading…</p>
    </template>

    <template v-else-if="!auth.user">
      <p class="eyebrow">Not signed in</p>
      <h1>Log in to set up your sync</h1>
      <button class="btn-primary" type="button" @click="login">Continue with Google</button>
    </template>

    <template v-else>
      <header class="head">
        <p class="eyebrow">Setup</p>
        <h1 v-if="configured">Your sync is set up</h1>
        <h1 v-else>Connect Apple Calendar</h1>
        <p class="lede">
          <template v-if="configured">
            Calnio pushes your Notion due dates into this calendar on a schedule.
            Notion stays the source of truth — nothing is written back to it.
          </template>
          <template v-else>
            Two steps, once. After this your Notion due dates show up in Apple
            Calendar on their own.
          </template>
        </p>
      </header>

      <p v-if="!apple.ready" class="muted">Loading…</p>
      <AppleCalendarStatus v-else-if="configured" />
      <AppleCalendarSetup v-else />
    </template>
  </main>
</template>

<style scoped>
.dash {
  padding-top: 48px;
  padding-bottom: 96px;
}

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

.muted {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--muted);
  padding: 40px 0;
  border-top: 1px solid var(--hairline);
}
</style>
