<script setup>
// Four edits in Apple Calendar and what each does to the Notion page behind it.
// The chip is the calendar side, the sentence is Notion.
const edits = [
  { kicker: 'Create it', chip: '+ New event', tone: 'blue', result: 'new page in Notion', struck: false },
  { kicker: 'Drag it', chip: 'Tue → Thu', tone: 'green', result: 'due date moves', struck: false },
  { kicker: 'Rename it', chip: 'Gym → Leg day', tone: 'amber', result: 'page renamed', struck: false },
  { kicker: 'Delete it', chip: 'Old task', tone: 'pink', result: 'page goes to trash', struck: true },
]
</script>

<template>
  <section class="section">
    <div class="container column twoway">
      <div class="column intro">
        <p class="eyebrow">Two-way sync</p>
        <h2 class="headline">Change it anywhere.<br />It changes everywhere.</h2>
      </div>

      <div class="grid edits">
        <div v-for="edit in edits" :key="edit.kicker" class="card edit">
          <p class="kicker">{{ edit.kicker }}</p>
          <p class="row outcome">
            <span class="ev" :class="[edit.tone, { struck: edit.struck }]">{{ edit.chip }}</span>
            <span class="arrow" aria-hidden="true">→</span>
            <span>{{ edit.result }}</span>
          </p>
        </div>
      </div>

      <p class="tagline closing">
        And everything you do in Notion shows up in your calendar, of course.
      </p>
    </div>
  </section>
</template>

<style scoped>
.twoway {
  --gap: clamp(40px, 6vw, 72px);
}

.intro {
  --gap: 16px;
  text-align: center;
}

.edits {
  --col: 320px;
  --gap: 18px;
}

.edit {
  padding: 26px 28px;
}

.outcome {
  --gap: 14px;
  flex-wrap: nowrap;
  margin-top: 12px;
  font-size: var(--l-text-row);
  font-weight: 600;
  letter-spacing: -0.01em;
}

/* Inside a sentence the chip is a word, so it takes a word's padding. */
.outcome .ev {
  flex: none;
  padding: 6px 12px;
  font-size: 0.75em;
}

.outcome .ev.struck {
  text-decoration: line-through;
}

.arrow {
  color: var(--l-muted);
  flex: none;
}

.closing {
  text-align: center;
  font-size: 18px;
}

/* At phone width the chip and its sentence stop fitting on one line. */
@media (max-width: 560px) {
  .outcome {
    flex-wrap: wrap;
  }
}
</style>
