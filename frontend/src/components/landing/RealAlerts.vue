<script setup>
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
    weekday: 'MON',
    date: '5',
    title: 'Call with designer',
    stamp: '15m ago',
    detail: 'Today at 10:30 · in 1 hour',
    faded: true,
  },
]
</script>

<template>
  <section class="section">
    <div class="container row alerts">
      <div class="column claim">

        <h2 class="headline">Your Notion dates in your iPhone calendar, as real events.</h2>

        <p class="tagline">
          A webcal feed is read-only, stays silent and refreshes when it feels
          like it. Calnio's events are ordinary iCloud events: they alert on
          every device, and you can edit them from either side.
        </p>
        <p class="tagline">
          Each database gets its own calendar. A date without a time becomes an
          all-day event, a date with a time becomes an event at that time, and
          Calnio checks for changes every 15 minutes.
          <router-link to="/notion-icloud-calendar">How it works on an iPhone</router-link>.
        </p>
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
  max-width: 40ch;
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
  font-weight: 700;
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
