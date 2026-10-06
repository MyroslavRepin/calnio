<script setup>
import { computed } from 'vue'
import { formatDay } from '../../format'

// days: one object per day from the admin API. series: which numbers of a day
// to stack, bottom first, each { key, name, tone }.
const props = defineProps({
  days: { type: Array, required: true },
  series: { type: Array, required: true },
})

// One day's stacked total, the height the bar reaches.
function dayTotal(day) {
  let total = 0
  props.series.forEach(function (item) {
    total = total + day[item.key]
  })
  return total
}

// The busiest day, so every bar is a share of it. One is the floor, because
// dividing by zero draws nothing at all.
const busiest = computed(function () {
  let most = 1
  props.days.forEach(function (day) {
    const total = dayTotal(day)
    if (total > most) {
      most = total
    }
  })
  return most
})

// A day label under every seventh bar counting back from today, so the
// newest day is always named and the labels never collide.
function showsLabel(index) {
  if ((props.days.length - 1 - index) % 7 === 0) {
    return true
  } else {
    return false
  }
}

// Each bar: its stacked parts as heights, and the numbers behind it for the
// tooltip, since the bars alone carry no figure.
const bars = computed(function () {
  return props.days.map(function (day, index) {
    const words = []
    const parts = props.series.map(function (item) {
      words.push(day[item.key] + ' ' + item.name)
      return {
        key: item.key,
        tone: item.tone,
        height: (day[item.key] * 100) / busiest.value + '%',
      }
    })

    let label = ''
    if (showsLabel(index)) {
      label = formatDay(day.day)
    }

    return {
      day: day.day,
      label: label,
      parts: parts,
      title: formatDay(day.day) + ': ' + words.join(', '),
    }
  })
})

// The legend: every series with its total over the whole chart.
const legend = computed(function () {
  return props.series.map(function (item) {
    let total = 0
    props.days.forEach(function (day) {
      total = total + day[item.key]
    })
    return { key: item.key, tone: item.tone, text: item.name + ' ' + total }
  })
})

// The same totals as one sentence, for a screen reader.
const summary = computed(function () {
  const words = legend.value.map(function (item) {
    return item.text
  })
  return 'Last ' + props.days.length + ' days: ' + words.join(', ')
})
</script>

<template>
  <div class="column daychart">
    <div class="row legend">
      <span v-for="item in legend" :key="item.key" class="label" :class="item.tone">
        {{ item.text }}
      </span>
    </div>

    <div class="row bars" role="img" :aria-label="summary">
      <div v-for="bar in bars" :key="bar.day" class="column barcolumn" :title="bar.title">
        <div class="bartrack">
          <div
            v-for="part in bar.parts"
            :key="part.key"
            class="barpart"
            :class="part.tone"
            :style="{ height: part.height }"
          />
        </div>
        <span class="barday">{{ bar.label }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.daychart {
  --gap: var(--app-gap-stack);
}

.legend {
  --gap: var(--app-gap-inline);
}

/* flex-basis 0 lets thirty columns share the width without ever wrapping. */
.bars {
  --gap: 3px;
  align-items: flex-end;
  flex-wrap: nowrap;
}

.barcolumn {
  --gap: var(--app-space-1);
  flex: 1 1 0;
  min-width: 0;
  align-items: center;
}

/* column-reverse puts the first series at the bottom of the stack. */
.bartrack {
  display: flex;
  flex-direction: column-reverse;
  width: 100%;
  height: 96px;
  border-radius: var(--app-radius-sm);
  background: var(--app-canvas-subtle);
  overflow: hidden;
}

.barpart.accent {
  background: var(--app-accent);
}

.barpart.success {
  background: var(--app-success);
}

.barpart.danger {
  background: var(--app-danger);
}

.barpart.attention {
  background: var(--app-attention);
}

.barpart.neutral {
  background: var(--app-fg-subtle);
}

.barday {
  height: var(--app-text-meta);
  font-size: var(--app-text-meta);
  line-height: 1;
  color: var(--app-fg-subtle);
  white-space: nowrap;
}
</style>
