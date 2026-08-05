<script setup>
// The blue circles. One page-wide layer, behind everything — a per-section
// layer produces visible rectangular seams, which is exactly what this
// replaced. The layer clips its own children rather than asking the page root
// for `overflow:hidden`, because that would kill the sticky bars above it.
//
// Placement discipline: a circle's saturated band runs to ~76% of its radius,
// so circles live in margins and empty bands and enter as arcs. Text either
// stays on clean white or gets a white surface (.pill, the event chip).
defineProps({
  // 'landing' is the full six-circle score, tuned to the landing page's height.
  // 'short' is the two-arcs-and-a-glow version for the app's shorter pages.
  variant: { type: String, default: 'landing' },
})
</script>

<template>
  <div class="field" :class="variant" aria-hidden="true">
    <div class="circle c1" />
    <div class="circle c2" />

    <template v-if="variant === 'landing'">
      <div class="circle c3" />
      <div class="ring r1" />
      <div class="ring r2" />
    </template>

    <div class="circle glow" />
    <div class="grain" />
  </div>
</template>

<style scoped>
/* Not positioned: the circles hang off the page root (`.page`, which is
   relative) instead of off this element, so nothing clips them and nothing
   asks Chrome for a document-height composited layer. Being the root's first
   child is what keeps them behind every section. */
.field {
  pointer-events: none;
}

/* A radial gradient with a transparent falloff, plus a small blur. The
   transparent stop is what removes any visible edge — never a linear gradient
   rectangle, never a white mask fading a circle out. */
.circle {
  position: absolute;
  border-radius: 50%;
  background: radial-gradient(
    circle at 50% 46%,
    #7df3ff 0%,
    #17a5ff 32%,
    var(--accent, #0b63f6) 58%,
    rgba(11, 99, 246, 0.14) 76%,
    rgba(11, 99, 246, 0) 82%
  );
  filter: blur(14px);
}

.ring {
  position: absolute;
  border-radius: 50%;
}

/* Arc into the hero's lower left. */
.c1 {
  left: -26vw;
  top: clamp(340px, 42vw, 540px);
  width: min(480px, 58vw);
  height: min(480px, 58vw);
  filter: blur(16px);
}

/* Arc from the right, level with the chip band. */
.c2 {
  right: -20vw;
  top: clamp(600px, 72vw, 880px);
  width: min(420px, 50vw);
  height: min(420px, 50vw);
}

/* Small crisp orb. */
.c3 {
  left: -6vw;
  top: clamp(1000px, 102vw, 1300px);
  width: min(200px, 28vw);
  height: min(200px, 28vw);
  filter: blur(10px);
}

.r1 {
  left: -20vw;
  top: clamp(1120px, 116vw, 1480px);
  width: min(720px, 92vw);
  height: min(720px, 92vw);
  border: 1px solid rgba(11, 99, 246, 0.2);
}

.r2 {
  right: -12vw;
  bottom: clamp(260px, 34vw, 420px);
  width: min(280px, 40vw);
  height: min(280px, 40vw);
  border: 1px solid rgba(10, 10, 10, 0.16);
}

/* The big glow under the closing CTA. */
.glow {
  left: 50%;
  transform: translateX(-50%);
  bottom: min(-430px, -58vw);
  width: min(1320px, 160vw);
  height: min(940px, 116vw);
  filter: blur(20px);
}

/* Shorter pages carry far less air than the landing page, so the same circles
   read as decoration fighting the content. Here they keep the gradient but are
   blurred until they have no edge left — a wash behind the page. Content on
   these pages sits on a .surface panel, which is what keeps it readable. */
.short .circle {
  opacity: 0.5;
  filter: blur(80px);
}

.short .c1 {
  left: -34vw;
  top: clamp(140px, 22vw, 260px);
}

.short .c2 {
  right: -30vw;
  top: clamp(420px, 60vw, 640px);
}

.short .glow {
  bottom: min(-620px, -78vw);
  width: min(1100px, 150vw);
  height: min(820px, 104vw);
}

/* Grain is landing-only: over dense rows of small text it reads as dirt. */
.short .grain {
  display: none;
}

/* One continuous grain for the whole page — a per-section overlay seams.
   `overlay` only: a multiply layer greys the white page.

   The SVG is sized and tiled rather than stretched over the whole page: an
   unsized one makes Chrome rasterise a single filter surface the height of the
   document, which it abandons part-way and leaves a hard vertical seam.
   `stitchTiles='stitch'` is what makes the repeat invisible. */
.grain {
  position: absolute;
  inset: 0;
  mix-blend-mode: overlay;
  opacity: 0.38;
  background-image: url("data:image/svg+xml,%3Csvg%20xmlns=%27http://www.w3.org/2000/svg%27%20width=%27200%27%20height=%27200%27%3E%3Cfilter%20id=%27g1%27%3E%3CfeTurbulence%20type=%27fractalNoise%27%20baseFrequency=%270.85%27%20numOctaves=%274%27%20stitchTiles=%27stitch%27/%3E%3C/filter%3E%3Crect%20width=%27100%25%27%20height=%27100%25%27%20filter=%27url%28%23g1%29%27/%3E%3C/svg%3E");
  background-size: 200px 200px;
  background-repeat: repeat;
}
</style>
