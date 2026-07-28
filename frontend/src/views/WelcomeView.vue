<script setup>
import { computed, onMounted, watch } from 'vue'
import AppleCalendarSetup from '../components/AppleCalendarSetup.vue'
import NotionSetup from '../components/NotionSetup.vue'
import { useAppleCalendar } from '../composables/useAppleCalendar'
import { useAuth } from '../composables/useAuth'
import { useNotion } from '../composables/useNotion'

// Full-screen onboarding: the whole setup on one scrolling page, outside the
// dashboard shell so nothing competes with it. The two wizards are the real
// ones from Connections, renumbered 01–04 into a single sequence.
const { state: auth, login } = useAuth()
const { state: apple, load: loadApple } = useAppleCalendar()
const { state: notion, load: loadNotion } = useNotion()

// Same four stages the dashboard counts: a grant stored, then a target picked,
// for each of the two connections.
const stages = computed(() => [
  Boolean(notion.connection),
  Boolean(notion.connection?.data_source_id),
  Boolean(apple.connection),
  Boolean(apple.connection?.calendar_url),
])

const ready = computed(() => notion.ready && apple.ready)
const doneCount = computed(() => stages.value.filter(Boolean).length)
const allDone = computed(() => doneCount.value === stages.value.length)
const percent = computed(() => (doneCount.value / stages.value.length) * 100)

// DashboardLayout loads these for its own children; this page sits outside it,
// so it asks for them itself once a user exists.
function loadIfAuthed() {
  if (!auth.ready || !auth.user) return
  loadApple()
  loadNotion()
}

onMounted(loadIfAuthed)
watch(() => [auth.ready, auth.user], loadIfAuthed)
</script>

<template>
  <div class="page">
    <!-- Sticky progress ---------------------------------------------------->
    <header class="bar">
      <div class="wrap barinner">
        <router-link to="/" class="mark">calnio</router-link>
        <p class="count">
          <template v-if="ready">{{ doneCount }} of {{ stages.length }}</template>
          <template v-else>setup</template>
        </p>
      </div>
      <div class="track" role="presentation">
        <div class="fill" :style="{ width: ready ? `${percent}%` : '0%' }" />
      </div>
    </header>

    <main class="wrap main">
      <p v-if="!auth.ready" class="muted">Loading…</p>

      <!-- Signed out ------------------------------------------------------->
      <section v-else-if="!auth.user" class="hero">
        <p class="eyebrow">Welcome</p>
        <h1>Set up Calnio</h1>
        <p class="lede">Log in first — your setup is stored against your account.</p>
        <button class="btn-primary" type="button" @click="login">
          Continue with Google
        </button>
      </section>

      <template v-else>
        <section class="hero">
          <p class="eyebrow">Welcome</p>
          <h1>{{ allDone ? 'You are all set' : 'Set up Calnio' }}</h1>
          <p class="lede">
            <template v-if="allDone">
              Both connections are in place. Syncing your own workspace switches
              on later in beta — nothing else is needed from you until then.
            </template>
            <template v-else>
              Four steps, once. You are connecting your accounts now — syncing
              your own workspace switches on later in beta, and everything you
              set up here carries over when it does.
            </template>
          </p>

          <router-link v-if="allDone" class="btn-primary" :to="{ name: 'dashboard' }">
            Go to your dashboard
          </router-link>
        </section>

        <p v-if="!ready" class="muted">Loading your connections…</p>

        <template v-else>
          <!-- Steps 01–02 ------------------------------------------------->
          <NotionSetup :numbers="['01', '02']" />

          <!-- Steps 03–04 ------------------------------------------------->
          <AppleCalendarSetup :numbers="['03', '04']">
            <template #help>
              <p class="lede">
                Apple requires an <strong>app-specific password</strong>. Your
                Apple Account password will not work here.
              </p>
              <p class="lede">
                Your Apple Account needs two-factor authentication turned on —
                without it, Apple does not offer app-specific passwords at all.
              </p>

              <ol class="sub">
                <li>
                  Sign in at
                  <a href="https://account.apple.com" target="_blank" rel="noreferrer"
                    >account.apple.com</a
                  >
                </li>
                <li>Open Sign-In and Security → App-Specific Passwords</li>
                <li>Choose Generate an app-specific password</li>
                <li>
                  Name it <span class="mono">Calnio</span>, then copy the
                  <span class="mono">xxxx-xxxx-xxxx-xxxx</span> it shows you
                </li>
              </ol>

              <p class="note">
                Revoking the password at Apple disconnects Calnio immediately.
              </p>
            </template>
          </AppleCalendarSetup>

          <footer class="foot">
            <router-link class="link-mono" :to="{ name: 'dashboard' }">
              {{ allDone ? 'Go to your dashboard' : 'Skip for now' }}
            </router-link>
          </footer>
        </template>
      </template>
    </main>
  </div>
</template>

<style scoped>
.page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #fff;
}

/* Progress ------------------------------------------------------------- */
.bar {
  position: sticky;
  top: 0;
  z-index: 10;
  background: #fff;
}

.barinner {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 24px;
  padding-top: 24px;
  padding-bottom: 20px;
}

.mark {
  font-size: 17px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--ink);
}

.count {
  font-family: var(--font-mono);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  color: var(--muted);
}

.track {
  height: 2px;
  background: var(--hairline);
}

.fill {
  height: 2px;
  background: var(--ink);
  transition: width 240ms ease;
}

/* Content -------------------------------------------------------------- */
.main {
  flex: 1;
  padding-bottom: 96px;
}

.hero {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 16px;
  padding: 72px 0 56px;
  max-width: 640px;
}

h1 {
  font-size: 56px;
  font-weight: 700;
  letter-spacing: -0.04em;
  line-height: 1;
}

.lede {
  font-size: 17px;
  line-height: 1.6;
  color: var(--body);
}

.hero .btn-primary {
  margin-top: 8px;
}

/* Apple instructions, injected into the wizard's slot ------------------- */
.sub {
  list-style: none;
  margin: 0;
  padding: 0;
  counter-reset: substep;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.sub li {
  counter-increment: substep;
  display: grid;
  grid-template-columns: 28px 1fr;
  gap: 12px;
  font-size: 15px;
  line-height: 1.6;
  color: var(--body);
}

.sub li::before {
  content: counter(substep, lower-alpha);
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: 0.16em;
  color: var(--muted);
  padding-top: 4px;
}

.mono {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--ink);
}

.lede strong {
  font-weight: 500;
  color: var(--ink);
}

.note {
  font-size: 13px;
  line-height: 1.6;
  color: var(--muted);
}

.foot {
  display: flex;
  padding: 40px 0 0;
  border-top: 1px solid var(--hairline);
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
  padding: 40px 0;
}

@media (max-width: 720px) {
  h1 {
    font-size: 40px;
    letter-spacing: -0.03em;
  }

  .hero {
    padding: 48px 0 40px;
  }
}
</style>
