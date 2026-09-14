<script setup>
import GoogleButton from './GoogleButton.vue'

// Three steps, because that is now all it takes. The date column and the
// calendar are worked out for you.
const steps = [
  {
    number: '1',
    title: 'Log in with Google',
    body: 'Your setup is stored against your account. That is the only thing the login is for.',
  },
  {
    number: '2',
    title: 'Connect Notion',
    body: 'Notion asks which pages Calnio may read. Tick every database you want to see in your calendar.',
  },
  {
    number: '3',
    title: 'Add an app-specific password',
    body: 'Apple requires one for calendar access. Generate it at account.apple.com and paste it in.',
  },
]
</script>

<template>
  <section id="start" class="column sections">
    <header class="column page-head">
      <h2 class="title">Connect once, then forget it.</h2>
      <p class="lead">
        Nothing to download and no server to run. Link Notion and your iCloud
        account, tick your databases, and Calnio keeps them in step on a
        schedule.
      </p>
      <GoogleButton label="Start syncing" plain />
    </header>

    <ol class="column steps">
      <li v-for="step in steps" :key="step.number" class="column step">
        <div class="row stephead">
          <span class="num">{{ step.number }}</span>
          <h3>{{ step.title }}</h3>
        </div>
        <p class="body stepbody">{{ step.body }}</p>
      </li>
    </ol>

    <p class="note">
      After that, ticking a database is the whole job: Calnio reads its date
      column and gives it a calendar of the same name. Both are yours to change
      afterwards.
    </p>
  </section>
</template>

<style scoped>
#start {
  scroll-margin-top: var(--app-space-5);
}

.sections {
  --gap: var(--app-gap-block);
}

.steps {
  --gap: var(--app-gap-section);
  list-style: none;
  margin: 0;
  padding: 0;
  max-width: var(--app-measure);
}
</style>
