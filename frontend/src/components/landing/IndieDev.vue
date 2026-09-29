<script setup>
// Three facts about who runs this. The last is white: free is the one to read.
const facts = [
  { figure: '1', body: 'developer. Bug reports go straight to me.', filled: false },
  { figure: 'π', body: 'Hosted on a Raspberry Pi sitting on my desk.', filled: false },
  { figure: '$0', body: 'Free. Just tell me what breaks.', filled: true },
]
</script>

<template>
  <section class="section dark indie">
    <div class="container column indiebody">
      <h2 class="headline">
        Built by one indie dev.<br />
        <span class="dim">I use it every single day.</span>
      </h2>

      <div class="grid facts">
        <div v-for="fact in facts" :key="fact.figure" class="column fact" :class="{ filled: fact.filled }">
          <span class="figure">{{ fact.figure }}</span>
          <p class="tagline">{{ fact.body }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.indiebody {
  --gap: clamp(40px, 6vw, 80px);
}

.facts {
  --col: 280px;
  --gap: 18px;
}

/* Outlined on the black ground. Three white cards would fight the headline. */
.fact {
  --gap: 6px;
  border: 1px solid var(--l-line-dark);
  border-radius: var(--l-radius);
  padding: 30px;
}

.fact.filled {
  background: #fff;
  color: var(--l-ink);
  border-color: #fff;
}

.fact.filled p.tagline {
  color: #48484a;
}

.figure {
  font-size: var(--l-text-stat);
  font-weight: 800;
  letter-spacing: -0.04em;
  line-height: 1.1;
}

.fact .tagline {
  font-size: 19px;
}
</style>
