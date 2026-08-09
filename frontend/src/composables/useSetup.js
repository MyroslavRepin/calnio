import { computed } from 'vue'
import { useAppleCalendar } from './useAppleCalendar'
import { useNotion } from './useNotion'

// The four stages of getting Calnio set up: a grant stored, then a target
// picked, for each of the two connections. The dashboard and the welcome page
// both count them and they have to agree, so they are defined once here.
const appleResult = useAppleCalendar()
const apple = appleResult.state

const notionResult = useNotion()
const notion = notionResult.state

const stages = computed(function () {
  return [
    {
      label: 'Notion workspace connected',
      done: Boolean(notion.connection),
    },
    {
      label: 'Notion database chosen',
      done: Boolean(notion.connection?.data_source_id),
    },
    {
      label: 'iCloud account connected',
      done: Boolean(apple.connection),
    },
    {
      label: 'Apple calendar chosen',
      done: Boolean(apple.connection?.calendar_url),
    },
  ]
})

// Both connections have to be loaded before the count means anything.
const ready = computed(function () {
  if (notion.ready && apple.ready) {
    return true
  } else {
    return false
  }
})

const doneCount = computed(function () {
  const finished = stages.value.filter(function (stage) {
    return stage.done
  })
  return finished.length
})

const allDone = computed(function () {
  if (doneCount.value === stages.value.length) {
    return true
  } else {
    return false
  }
})

const percent = computed(function () {
  return (doneCount.value / stages.value.length) * 100
})

export function useSetup() {
  return { stages, ready, doneCount, allDone, percent }
}
