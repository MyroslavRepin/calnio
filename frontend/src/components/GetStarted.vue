<script setup>
import GoogleButton from './GoogleButton.vue'

const steps = [
  {
    n: '01',
    title: 'Log in with Google',
    body: 'Your setup is stored against your account. That is the only thing the login is for.',
  },
  {
    n: '02',
    title: 'Connect Notion',
    body: 'Notion asks which pages Calnio may read. Tick the database that holds your tasks.',
  },
  {
    n: '03',
    title: 'Add an app-specific password',
    body: 'Apple requires one for calendar access. Generate it at account.apple.com and paste it in.',
  },
  {
    n: '04',
    title: 'Pick a calendar',
    body: 'Choose the Apple calendar Calnio writes into, or let it make a new one.',
  },
]
</script>

<template>
  <section id="start" class="section">
    <div class="wrap inner">
      <div class="head">
        <p class="eyebrow">Get started</p>
        <h2 class="title">Connect once,<br />then forget it.</h2>
        <p class="lead">
          No downloads and no server to run. Link Notion and your iCloud
          calendar, and Calnio keeps them in step on a schedule.
        </p>
        <GoogleButton label="Start syncing" />
      </div>

      <ol class="steps">
        <li v-for="s in steps" :key="s.n" class="step">
          <span class="num">{{ s.n }}</span>
          <h3>{{ s.title }}</h3>
          <p class="body">{{ s.body }}</p>
        </li>
      </ol>
    </div>
  </section>
</template>

<style scoped>
#start {
  scroll-margin-top: 24px;
}

.inner {
  display: flex;
  flex-direction: column;
  gap: clamp(40px, 7vw, 72px);
}

.head {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: clamp(16px, 2.5vw, 24px);
}

.steps {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: clamp(28px, 5vw, 44px);
}

.step {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.num {
  font-family: var(--font-mono);
  font-size: clamp(30px, 6vw, 40px);
  font-weight: 500;
  letter-spacing: -0.04em;
  line-height: 1;
  color: var(--accent, #0b63f6);
}

h3 {
  font-size: 17px;
  font-weight: 600;
  color: var(--ink);
}

.body {
  font-size: 14.5px;
  line-height: 1.6;
  color: var(--body);
}
</style>
