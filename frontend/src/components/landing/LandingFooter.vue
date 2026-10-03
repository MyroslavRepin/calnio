<script setup>
import CalnioMark from '../CalnioMark.vue'

// Every public page besides the landing, which the wordmark links to, so each
// page links to all the others and a crawler that lands anywhere finds the rest.
const pages = [
  { to: '/notion-apple-calendar-sync', label: 'Notion Apple Calendar sync guide' },
  { to: '/notion-icloud-calendar', label: 'Notion in your iPhone calendar' },
  { to: '/faq', label: 'FAQ' },
]
</script>

<template>
  <footer class="footer">
    <div class="container column footerbody">
      <div class="row footerrow">
        <router-link to="/" class="wordmark">
          <span class="plate"><CalnioMark /></span>
          Calnio
        </router-link>

        <nav class="row pagelinks" aria-label="Pages">
          <router-link v-for="page in pages" :key="page.to" :to="page.to">{{ page.label }}</router-link>
        </nav>
      </div>

      <div class="row footerrow">
        <span class="note">
          Free. Hosted on a Raspberry Pi on my desk. Made by
          <a class="author" href="https://myroslavrepin.com" data-umami-event="author_link">Myroslav Repin</a>.
        </span>

        <a class="feedback" href="mailto:myroslavrepin@gmail.com?subject=Calnio%20feedback">
          Tell me what breaks
        </a>
      </div>
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

.footerbody {
  --gap: var(--app-space-5);
}

.footerrow {
  --gap: var(--app-space-5);
  justify-content: space-between;
}

.pagelinks {
  --gap: var(--app-space-2) var(--app-space-5);
  font-size: 14px;
  font-weight: 500;
}

.pagelinks a:hover {
  color: var(--l-blue);
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
