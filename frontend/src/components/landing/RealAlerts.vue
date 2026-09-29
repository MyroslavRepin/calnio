<script setup>
// The two ways a Notion date can reach a calendar.
const feedLimits = ['Read-only', 'No alerts', 'Slow refresh']
const calnioWins = ['Real iCloud events', 'Alerts on every device', 'Edit from either side']

// The lock screen notifications. The second is dimmer, being the older one.
const alerts = [
  {
    weekday: 'MON',
    date: '5',
    title: 'Ship landing page',
    stamp: 'now',
    detail: 'Today at 10:00 · in 15 minutes',
    faded: false,
  },
  {
    weekday: 'TUE',
    date: '6',
    title: 'Call with designer',
    stamp: '9:00',
    detail: 'Tomorrow at 14:00',
    faded: true,
  },
]
</script>

<template>
  <section class="section">
    <div class="container row alerts">
      <div class="column claim">
        <p class="eyebrow">Not a webcal feed</p>

        <h2 class="headline">Real calendar events.<br />Real alerts.</h2>

        <p class="tagline">
          Calnio writes actual events into your iCloud calendar, so they behave
          like any event you made yourself.
        </p>

        <div class="grid compare">
          <div class="card feeds">
            <h3>Calendar feeds</h3>
            <ul>
              <li v-for="limit in feedLimits" :key="limit">
                <span class="cross" aria-hidden="true">✕</span>{{ limit }}
              </li>
            </ul>
          </div>

          <div class="card ours">
            <h3>Calnio</h3>
            <ul>
              <li v-for="win in calnioWins" :key="win">
                <span class="tick" aria-hidden="true">✓</span>{{ win }}
              </li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Drawn, not photographed: it stays sharp at any width. -->
      <div class="phone" aria-hidden="true">
        <div class="column screen">
          <span class="notch"></span>
          <p class="today">Monday, October 5</p>
          <p class="clock">9:45</p>

          <div v-for="alert in alerts" :key="alert.title" class="row alert" :class="{ faded: alert.faded }">
            <span class="column datemark">
              {{ alert.weekday }}
              <b>{{ alert.date }}</b>
            </span>
            <span class="column alertcopy">
              <span class="row alertname">
                <b>{{ alert.title }}</b>
                <span class="stamp">{{ alert.stamp }}</span>
              </span>
              <span class="alertdetail">{{ alert.detail }}</span>
            </span>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.alerts {
  --gap: clamp(32px, 5vw, 72px);
  align-items: center;
  justify-content: space-between;
}

.claim {
  --gap: clamp(18px, 2vw, 24px);
  flex: 1 1 460px;
}

.claim .tagline {
  max-width: 34ch;
}

.compare {
  --col: 200px;
  --gap: 16px;
  margin-top: clamp(8px, 1.6vw, 20px);
}

.compare .card {
  padding: 22px;
}

.compare h3 {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 14px;
}

.compare ul {
  list-style: none;
  margin: 0;
  padding: 0;
  font-size: 16px;
  line-height: 2;
}

/* The pale card loses the shadow too, and states its limits in grey. */
.card.feeds {
  box-shadow: none;
  border: 1px solid var(--l-line);
}

.feeds h3 {
  color: var(--l-muted);
}

.feeds ul {
  color: #86868b;
}

.card.ours {
  background: var(--l-ink);
  color: #fff;
}

.cross,
.tick {
  display: inline-block;
  width: 1.4em;
}

/* Phone */

.phone {
  flex: 0 1 340px;
  max-width: 340px;
  aspect-ratio: 340 / 700;
  border-radius: 56px;
  background: #1c1c1e;
  padding: 12px;
  box-shadow: 0 40px 80px -30px rgba(0, 0, 0, 0.45);
}

.screen {
  --gap: 0px;
  position: relative;
  height: 100%;
  border-radius: 45px;
  overflow: hidden;
  background: linear-gradient(160deg, #3a4a6b, #1b2233 55%, #0d1018);
  color: #fff;
  padding: 0 14px;
}

.notch {
  position: absolute;
  left: 50%;
  top: 14px;
  transform: translateX(-50%);
  width: 110px;
  height: 32px;
  border-radius: 20px;
  background: #000;
}

.today {
  text-align: center;
  margin-top: 78px;
  font-size: 17px;
  font-weight: 600;
  opacity: 0.85;
}

.clock {
  text-align: center;
  font-size: 88px;
  font-weight: 700;
  letter-spacing: -0.04em;
  line-height: 1;
}

.alert {
  --gap: 12px;
  align-items: flex-start;
  flex-wrap: nowrap;
  border-radius: 22px;
  background: rgba(245, 245, 250, 0.82);
  color: #111;
  padding: 14px 16px;
  margin-top: 16px;
}

.alert:first-of-type {
  margin-top: 56px;
}

.alert.faded {
  background: rgba(245, 245, 250, 0.6);
}

.datemark {
  --gap: 0px;
  width: 38px;
  height: 38px;
  flex: none;
  border-radius: 10px;
  background: #fff;
  align-items: center;
  justify-content: center;
  color: #d33;
  font-size: 11px;
  font-weight: 800;
  line-height: 1;
}

.datemark b {
  color: #111;
  font-size: 17px;
}

.alertcopy {
  --gap: 2px;
  flex: 1;
  min-width: 0;
}

.alertname {
  --gap: 8px;
  flex-wrap: nowrap;
  justify-content: space-between;
  font-size: 14px;
}

.stamp {
  color: #777;
  font-size: 12px;
}

.alertdetail {
  color: #333;
  font-size: 14px;
}

/* Below this the phone stops fitting beside the copy. */
@media (max-width: 900px) {
  .alerts {
    flex-wrap: wrap;
  }

  .claim,
  .phone {
    flex: 1 1 100%;
  }

  .phone {
    margin: 0 auto;
  }
}
</style>
