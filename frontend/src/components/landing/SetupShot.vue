<script setup>
import { onMounted, ref } from 'vue'

const video = ref(null)

// The walkthrough plays on its own and loops, unless the visitor asked for
// less motion, or the browser refused to autoplay (iOS Low Power Mode does).
// Either way it then waits on its poster with its controls showing.
onMounted(function () {
  const element = video.value
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches

  if (reduced) {
    element.controls = true
    return
  }

  element.play().catch(function () {
    element.controls = true
  })
})
</script>

<template>
  <section class="section">
    <div class="container column setup">
      <div class="column intro">
        <h2 class="headline">To sync Notion with iCloud Calendar, tick a database.</h2>
        <p class="tagline">
          Sign in with Google, connect Notion, add an iCloud app-specific
          password, and tick the databases you want. Calnio finds the date column
          and creates the calendar for you. Two-way is one switch on the same
          card. The <router-link to="/notion-apple-calendar-sync">step-by-step guide</router-link>
          walks through each screen.
        </p>
      </div>

      <!-- Rendered from video/ with Remotion. The phone cut draws the app at
           phone width, so its text stays readable on a small screen. Desktop
           comes first because a browser that ignores media takes the first. -->
      <div class="shot">
        <video
          ref="video"
          muted
          loop
          playsinline
          preload="metadata"
          poster="/setup-poster.jpg"
          aria-label="Setting up Calnio: connect Notion, connect iCloud with an app-specific password, tick two databases, and their events appear in Apple Calendar."
        >
          <source media="(min-width: 601px)" src="/setup.mp4" type="video/mp4" />
          <source src="/setup-phone.mp4" type="video/mp4" />
        </video>
      </div>
    </div>
  </section>
</template>

<style scoped>
.setup {
  --gap: clamp(32px, 4vw, 52px);
}

.intro {
  --gap: 12px;
}

.shot {
  border: 1px solid var(--l-line);
  border-radius: 14px;
  overflow: hidden;
  background: var(--l-bg);
  box-shadow: 0 30px 70px -30px rgba(0, 0, 0, 0.25);
}

/* The box keeps the video's shape before it loads, so nothing jumps. */
.shot video {
  display: block;
  width: 100%;
  aspect-ratio: 4 / 3;
  object-fit: cover;
}

@media (max-width: 600px) {
  .shot video {
    aspect-ratio: 4 / 5;
  }
}
</style>
