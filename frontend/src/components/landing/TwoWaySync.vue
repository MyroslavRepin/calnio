<script setup>
// Four edits in Apple Calendar and what each does to the Notion page behind it.
// The chip is the calendar side, the sentence is Notion.
const edits = [
  { chip: '+ New event', tone: 'blue', result: 'Create an event, and a new page appears in Notion.', struck: false },
  { chip: 'Tue → Thu', tone: 'green', result: 'Drag it to another day, and the due date moves.', struck: false },
  { chip: 'Gym → Leg day', tone: 'amber', result: 'Rename it, and the page is renamed.', struck: false },
  { chip: 'Old task', tone: 'pink', result: 'Delete it, and the page goes to the trash.', struck: true },
]
</script>

<template>
  <section class="section">
    <div class="container column twoway">
      <h2 class="headline">Edit in Apple Calendar, and Notion follows.</h2>

      <div class="column edits">
        <div v-for="edit in edits" :key="edit.chip" class="row edit">
          <span class="chipcell">
            <span class="ev" :class="[edit.tone, { struck: edit.struck }]">{{ edit.chip }}</span>
          </span>
          <p>{{ edit.result }}</p>
        </div>
      </div>

      <p class="tagline closing">
        Notion edits reach the calendar too. When both sides changed at once,
        Notion wins. Repeating events and invites are never imported.
      </p>
    </div>
  </section>
</template>

<style scoped>
.twoway {
  --gap: clamp(32px, 4vw, 52px);
}

.edits {
  --gap: 0px;
}

/* Hairline rows: the calendar event on the left, what Notion does beside it. */
.edit {
  --gap: 10px 32px;
  border-top: 1px solid var(--l-line);
  padding: clamp(18px, 2.2vw, 26px) 0;
  font-size: var(--l-text-row);
  font-weight: 600;
  letter-spacing: -0.01em;
}

.edit:last-child {
  border-bottom: 1px solid var(--l-line);
}

.chipcell {
  flex: 0 0 180px;
}

.edit p {
  flex: 1 1 320px;
}

.edit .ev {
  display: inline-block;
  padding: 6px 12px;
  font-size: 14px;
}

.edit .ev.struck {
  text-decoration: line-through;
}

.closing {
  max-width: 52ch;
}
</style>
