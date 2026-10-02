<script setup>
import CalnioMark from '../CalnioMark.vue'
</script>

<template>
  <footer class="footer">
    <div class="container row footerrow">
      <span class="wordmark">
        <span class="plate"><CalnioMark /></span>
        Calnio
      </span>

      <span class="note">
        Free. Hosted on a Raspberry Pi on my desk. Made by
        <a class="author" href="https://myroslavrepin.com" data-umami-event="author_link">Myroslav Repin</a>.
      </span>

      <a class="feedback" href="mailto:myroslavrepin@gmail.com?subject=Calnio%20feedback">
        Tell me what breaks
      </a>
    </div>
  </footer>
</template>

<style scoped>
.footer {
  background: var(--l-bg);
  border-top: 1px solid var(--l-line);
  padding: clamp(28px, 3.4vw, 40px) 0;
  /* Keeps the last row clear of the iOS home indicator. */
  padding-bottom: calc(clamp(28px, 3.4vw, 40px) + env(safe-area-inset-bottom, 0px));
}

.footerrow {
  --gap: var(--app-space-5);
  justify-content: space-between;
}

.plate {
  width: 26px;
  height: 26px;
  flex: none;
}

.wordmark {
  font-size: 17px;
}

.note {
  color: var(--l-muted);
  font-size: 14px;
}

.author {
  color: inherit;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.author:hover {
  color: var(--l-blue);
}

.feedback {
  color: var(--l-blue);
  font-size: 14px;
  font-weight: 600;
}

.feedback:hover {
  text-decoration: underline;
}
</style>
