<script setup>
import { ref } from 'vue'
import GetStartedButton from './GetStartedButton.vue'

// One row of this list is one Notion page and the calendar event behind it, so
// ticking it in the table has to change both. top and height place the event
// down its day column by the hour it starts.
const items = ref([
  {
    title: 'Ship landing page',
    chip: 'Mon, 10:00',
    weekday: 'Mon',
    date: '5',
    time: '10:00',
    tone: 'blue',
    top: 40,
    height: 72,
    done: false,
    late: false,
  },
  {
    title: 'Call with designer',
    chip: 'Tue, 14:00',
    weekday: 'Tue',
    date: '6',
    time: '14:00',
    tone: 'amber',
    top: 120,
    height: 60,
    done: false,
    late: false,
  },
  {
    title: 'Physics exam',
    chip: 'Wed, 09:00',
    weekday: 'Wed',
    date: '7',
    time: '09:00',
    tone: 'pink',
    top: 12,
    height: 66,
    done: false,
    late: false,
  },
  {
    title: 'Gym',
    chip: 'Thu, 18:00',
    weekday: 'Thu',
    date: '8',
    time: '18:00',
    tone: 'green',
    top: 180,
    height: 54,
    done: false,
    late: true,
  },
  {
    title: 'Fix sync bug',
    chip: 'Fri, 11:00',
    weekday: 'Fri',
    date: '9',
    time: '11:00',
    tone: 'blue',
    top: 60,
    height: 60,
    done: true,
    late: true,
  },
])

// Ticking a task in the table is the whole demonstration: the event beside it
// changes in the same frame, off the same row.
function toggle(item) {
  item.done = !item.done
}
</script>

<template>
  <section class="section dark hero">
    <div class="container column herobody">
      <h1 class="headline hero">
        Notion and Apple Calendar.<br />
        <span class="dim">Finally in sync. Both ways.</span>
      </h1>

      <div class="row herocta">
        <GetStartedButton />
        <p class="tagline freenote">Free. Nothing to install.</p>
      </div>

      <div class="row mockup">
        <div class="card tasks">
          <div class="row tablename">
            <h2>Tasks</h2>
            <span>Tick one</span>
          </div>

          <button
            v-for="item in items"
            :key="item.title"
            type="button"
            class="row task"
            :class="{ done: item.done }"
            :aria-pressed="item.done"
            @click="toggle(item)"
          >
            <span class="checkbox" :class="{ ticked: item.done }"></span>
            <span class="taskname">{{ item.title }}</span>
            <span class="chip">{{ item.chip }}</span>
          </button>
        </div>

        <span class="swap" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="#0a0a0a" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 8h14l-4-4M20 16H6l4 4" />
          </svg>
        </span>

        <div class="card calendar">
          <div class="row calendarname">
            <h2>October</h2>
            <span>Tasks calendar</span>
          </div>

          <div class="week">
            <div v-for="item in items" :key="item.date" class="weekday" :class="{ late: item.late }">
              {{ item.weekday }}<b>{{ item.date }}</b>
            </div>

            <!-- Both loops run over one list, so a day header and the column
                 under it always line up in the grid. -->
            <div v-for="item in items" :key="item.date + 'col'" class="dayrun" :class="{ late: item.late }">
              <span
                class="ev"
                :class="[item.tone, { past: item.done }]"
                :style="{ top: item.top + 'px', height: item.height + 'px' }"
              >
                {{ item.title }}
                <small>{{ item.time }}</small>
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
/* The nav band pays for the space above the headline. */
.hero {
  padding-top: clamp(28px, 4vw, 56px);
}

.herobody {
  --gap: clamp(28px, 4vw, 44px);
}

.herocta {
  --gap: var(--app-space-5);
}

.freenote {
  font-size: 16px;
}

.mockup {
  --gap: clamp(16px, 2vw, 24px);
  align-items: center;
  flex-wrap: nowrap;
}

.tasks,
.calendar {
  flex: 1 1 0;
  min-width: 0;
}

/* The circle between the two cards. An illustration, not a control. */
.swap {
  width: clamp(54px, 5.6vw, 74px);
  height: clamp(54px, 5.6vw, 74px);
  flex: none;
  border-radius: 50%;
  background: #fff;
  display: grid;
  place-items: center;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
}

.swap svg {
  width: 52%;
  height: 52%;
}

/* Task table */

.tasks {
  padding: 22px 24px;
}

.tablename,
.calendarname {
  justify-content: space-between;
  flex-wrap: nowrap;
  margin-bottom: 12px;
}

.tablename h2,
.calendarname h2 {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.tablename span,
.calendarname span {
  color: var(--l-muted);
  font-size: 15px;
  font-weight: 500;
}

/* Each row is a button, so the whole row is the hit area on a phone. */
.task {
  --gap: 12px;
  width: 100%;
  flex-wrap: nowrap;
  padding: 11px 0;
  border: none;
  border-top: 1px solid var(--l-line);
  background: none;
  color: inherit;
  font: inherit;
  font-size: 15px;
  text-align: left;
  cursor: pointer;
}

.task:hover .taskname {
  color: var(--l-muted);
}

.task:focus-visible {
  outline: 2px solid var(--l-blue);
  outline-offset: 2px;
}

.checkbox {
  width: 16px;
  height: 16px;
  flex: none;
  border: 1.8px solid #b8b8bf;
  border-radius: 4px;
  position: relative;
}

.checkbox.ticked {
  background: var(--l-ink);
  border-color: var(--l-ink);
}

/* The tick is drawn, so it never depends on a font. */
.checkbox.ticked::after {
  content: '';
  position: absolute;
  left: 4px;
  top: 1px;
  width: 4px;
  height: 8px;
  border: solid #fff;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.taskname {
  flex: 1;
  font-weight: 500;
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.task.done .taskname {
  color: #a1a1a6;
  text-decoration: line-through;
}

.chip {
  background: #f0f0f3;
  border-radius: 7px;
  padding: 4px 9px;
  color: #46464b;
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
}

/* Week calendar */

.calendar {
  padding: 20px 20px 18px;
}

.week {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 6px;
}

.weekday {
  color: var(--l-muted);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--l-line);
}

.weekday b {
  display: block;
  color: var(--l-ink);
  font-size: 20px;
  letter-spacing: -0.02em;
  text-transform: none;
}

.dayrun {
  position: relative;
  height: 250px;
  border-right: 1px dashed #ececf0;
}

.dayrun:last-child {
  border-right: none;
}

.dayrun .ev {
  position: absolute;
  left: 3px;
  right: 3px;
}

.ev.past {
  opacity: 0.5;
  text-decoration: line-through;
}

/* Below this the two cards cannot sit side by side and stay readable: they
   stack, the swap turns a quarter turn, and the week drops to three days. */
@media (max-width: 900px) {
  .mockup {
    flex-wrap: wrap;
    justify-content: center;
  }

  .tasks,
  .calendar {
    flex: 1 1 100%;
  }

  .swap {
    transform: rotate(90deg);
  }

  .week {
    grid-template-columns: repeat(3, 1fr);
  }

  .weekday.late,
  .dayrun.late {
    display: none;
  }

  .dayrun {
    height: 210px;
  }
}
</style>
