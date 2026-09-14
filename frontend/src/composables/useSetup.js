import { computed } from 'vue'
import { useAppleCalendar } from './useAppleCalendar'
import { useMappings } from './useMappings'
import { useNotion } from './useNotion'

// The three stages of getting Calnio set up: the two grants, then at least one
// sync that can actually run. The dashboard and the welcome page both count them
// and they have to agree, so they are defined once here.
const appleResult = useAppleCalendar()
const apple = appleResult.state

const notionResult = useNotion()
const notion = notionResult.state

const mappingsResult = useMappings()
const mappings = mappingsResult.state

// A sync counts as ready once it has both a date column and a calendar. Whether
// its switch is on is the user's business, not part of setup.
const hasReadySync = computed(function () {
  return mappings.list.some(function (mapping) {
    return mapping.eligible
  })
})

const stages = computed(function () {
  return [
    {
      label: 'Notion workspace connected',
      done: Boolean(notion.connection),
    },
    {
      label: 'iCloud account connected',
      done: Boolean(apple.connection),
    },
    {
      label: 'First sync set up',
      done: hasReadySync.value,
    },
  ]
})

// All three sources have to be loaded before the count means anything.
const ready = computed(function () {
  if (notion.ready && apple.ready && mappings.ready) {
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
