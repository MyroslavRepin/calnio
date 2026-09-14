<script setup>
// What the sync actually guarantees. Each card is one promise, stated the way
// the app states a fact: a heading and a sentence, no illustration.
const steps = [
  {
    title: 'Notion is the truth',
    body: 'Calnio recomputes your events from Notion on every run. Change a date there and the calendar follows. Nothing is ever written back to Notion.',
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
    title: 'Last edit wins',
    body: 'Move a due date and the next run updates the event. Delete the page in Notion and the event goes with it.',
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
      Calnio writes one way: Notion to Apple Calendar. Two-way sync does not
      exist yet, and I would rather say so than imply it.
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
