<script setup>
// What the sync actually guarantees. Each card is one promise, stated the way
// the app states a fact: a heading and a sentence, no illustration.
const steps = [
  {
    title: 'Notion is the truth',
    body: 'Calnio recomputes your events from Notion on every run. Change a date there and the calendar follows. If both sides changed at once, Notion wins.',
  },
  {
    title: 'One database, one calendar',
    body: 'Every database you pick writes into its own Apple calendar, so tasks, habits and deadlines stay separable in the Calendar app.',
  },
  {
    title: 'No duplicates, ever',
    body: 'Each Notion page maps to a single calendar event. Events do not pile up between runs, and anything Calnio did not create is left alone.',
  },
  {
    title: 'Two-way when you ask',
    body: 'Off by default, and a switch per database. On, a moved event moves its Notion date, a renamed event renames the page, a new event becomes a new page.',
  },
]
</script>

<template>
  <section id="how" class="column sections">
    <header class="column page-head">
      <h2 class="title">How the sync works</h2>
      <p class="lead">
        Four things worth knowing before you connect anything.
      </p>
    </header>

    <div class="grid steps">
      <article v-for="step in steps" :key="step.title" class="card">
        <div class="card-head">
          <h2>{{ step.title }}</h2>
        </div>
        <div class="card-body">
          <p class="body">{{ step.body }}</p>
        </div>
      </article>
    </div>

    <p class="note">
      Two-way is opt-in, one database at a time, and every sync starts one way.
      Repeating events and invites are left alone: neither fits in a Notion row.
    </p>
  </section>
</template>

<style scoped>
#how {
  scroll-margin-top: var(--app-space-5);
}

.sections {
  --gap: var(--app-gap-block);
}

.steps {
  --col: 260px;
  --gap: var(--app-gap-block);
}

/* Consecutive .card rules space themselves vertically, which fights a grid. */
.steps .card + .card {
  margin-top: 0;
}
</style>
