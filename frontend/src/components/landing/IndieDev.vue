<template>
  <section class="section dark indie">
    <div class="container column indiebody">
      <h2 class="headline">I built Calnio for my own tasks, and I use it every day.</h2>

      <!-- The lit phrases carry the facts, the grey ones the reasons. -->
      <p class="story">
        <b>One developer,</b> so bug reports come straight to me.
        <b>Hosted on a Raspberry Pi</b> sitting on my desk.
        <b>Free.</b> Just tell me what breaks.
      </p>
    </div>
  </section>
</template>

<style scoped>
.indiebody {
  --gap: clamp(28px, 4vw, 48px);
}

.story {
  max-width: 34ch;
  color: var(--l-muted-dark);
  font-size: clamp(22px, 2.6vw, 34px);
  font-weight: 600;
  line-height: 1.3;
  letter-spacing: -0.02em;
}

.story b {
  color: #fff;
  font-weight: 600;
}
</style>
