<script setup>
import { computed } from 'vue'
import { useAppleCalendar } from '../../composables/useAppleCalendar'

const { state: apple } = useAppleCalendar()

// Credentials stored (step 1) vs credentials + a calendar picked (step 2).
const connected = computed(() => Boolean(apple.connection))
const configured = computed(() => Boolean(apple.connection?.calendar_url))
</script>

<template>
  <header class="head">
    <p class="eyebrow">Overview</p>
    <h1>{{ configured ? 'Your sync is set up' : 'Finish your setup' }}</h1>
    <p class="lede">
      Calnio pushes your Notion due dates into Apple Calendar. Notion stays the
      source of truth — nothing is ever written back to it.
    </p>
  </header>

  <p v-if="!apple.ready" class="muted">Loading…</p>

  <template v-else>
    <section class="block">
      <h2 class="eyebrow">Setup</h2>

      <ol class="steps">
        <li class="step">
          <span class="num">01</span>
          <span class="what">Apple Calendar connected</span>
          <span class="state">{{ connected ? 'done' : 'pending' }}</span>
        </li>
        <li class="step">
          <span class="num">02</span>
          <span class="what">Calendar selected</span>
          <span class="state">{{ configured ? 'done' : 'pending' }}</span>
        </li>
      </ol>

      <p class="note">
        <template v-if="configured">
          Setup complete. Syncing your own Notion workspace turns on later in
          beta.
        </template>
        <template v-else>
          Two steps, once.
          <router-link :to="{ name: 'connections' }">Connect Apple Calendar</router-link>
          to finish.
        </template>
      </p>
    </section>

    <section class="block">
      <h2 class="eyebrow">Connections</h2>

      <dl class="rows">
        <div class="row">
          <dt>Apple Calendar</dt>
          <dd v-if="configured">{{ apple.connection.icloud_email }}</dd>
          <dd v-else-if="connected">no calendar selected</dd>
          <dd v-else>not connected</dd>
        </div>
        <div class="row">
          <dt>Notion</dt>
          <dd>managed by calnio during beta</dd>
        </div>
      </dl>

      <router-link class="link-mono" :to="{ name: 'connections' }">
        Manage connections
      </router-link>
    </section>
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

.steps,
.rows {
  list-style: none;
  margin: 0;
  padding: 0;
  border-top: 1px solid var(--hairline);
  width: 100%;
  max-width: 640px;
}

.step {
  display: grid;
  grid-template-columns: 56px 1fr auto;
  gap: 24px;
  align-items: baseline;
  padding: 14px 0;
  border-bottom: 1px solid var(--hairline);
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

.num,
.state {
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--muted);
}

.what {
  font-size: 15px;
  color: var(--ink);
}

.note {
  font-size: 15px;
  line-height: 1.6;
  color: var(--body);
  max-width: 520px;
}

.note a {
  border-bottom: 1px solid var(--hairline);
  color: var(--ink);
}

.link-mono {
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
