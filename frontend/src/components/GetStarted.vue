<script setup>
import GoogleButton from './GoogleButton.vue'

const steps = [
  {
    n: '01',
    title: 'Get an app-specific password',
    body: 'On appleid.apple.com, generate an app-specific password for iCloud.',
  },
  {
    n: '02',
    title: 'Add it to Calnio',
    body: 'Paste the password in and Calnio connects to your iCloud calendar.',
  },
  {
    n: '03',
    title: 'Connect Notion',
    body: 'Link the database you plan in.',
  },
  {
    n: '04',
    title: 'Set your relations',
    body: "Map the due-date field to your calendar, and that's all.",
  },
]
</script>

<template>
  <section id="dev" class="get">
    <div class="wrap grid">
      <div class="left">
        <p class="eyebrow">Get started</p>
        <h2>Connect once,<br />then forget it.</h2>
        <p class="body">
          No downloads, no server to run. Link your Notion database and your
          iCloud calendar, Calnio does the rest on my machine, on a loop.
        </p>
        <GoogleButton label="Join the beta with Google" />
      </div>

      <ol class="steps">
        <li v-for="s in steps" :key="s.n" class="step">
          <span class="num">{{ s.n }}</span>
          <div class="text">
            <p class="title">{{ s.title }}</p>
            <p class="desc">{{ s.body }}</p>
          </div>
        </li>
      </ol>
    </div>
  </section>
</template>

<style scoped>
.get {
  border-top: 1px solid var(--hairline);
  padding: 96px 0;
}

.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 64px;
  align-items: center;
}

.left {
  display: flex;
  flex-direction: column;
  gap: 24px;
  align-items: flex-start;
}

h2 {
  font-family: var(--font-ui);
  font-size: 40px;
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1.02;
  color: var(--ink);
}

.body {
  font-size: 17px;
  line-height: 1.55;
  color: var(--body);
}

.steps {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
}

.step {
  display: flex;
  gap: 20px;
  padding: 20px 0;
  border-top: 1px solid var(--hairline);
}

.step:last-child {
  border-bottom: 1px solid var(--hairline);
}

.num {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--muted);
  padding-top: 2px;
}

.text {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.title {
  font-size: 16px;
  font-weight: 600;
  color: var(--ink);
}

.desc {
  font-size: 15px;
  line-height: 1.5;
  color: var(--body);
}
</style>
