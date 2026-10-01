import { interpolate } from 'remotion'
import { ease, T } from './timeline'
import type { Variant } from './variants'

// The payoff: the week in Apple Calendar once the first run is done. Drawn in
// the landing page's own illustration style, the same chips as the hero, not a
// copy of Apple's app. The two existing calendars are there from the start,
// the two new ones and their events arrive.

const DAYS = ['Mon 5', 'Tue 6', 'Wed 7', 'Thu 8', 'Fri 9']
const LAST_HOUR = 18

type CalendarEvent = {
  title: string
  tone: 'blue' | 'green' | 'amber' | 'pink'
  day: number
  start?: number
  hours?: number
  fresh: boolean
}

const EVENTS: CalendarEvent[] = [
  { title: 'Gym', tone: 'amber', day: 1, start: 17, hours: 1, fresh: false },
  { title: 'Team sync', tone: 'pink', day: 3, start: 10, hours: 1, fresh: false },
  { title: 'Ship site', tone: 'blue', day: 0, start: 10, hours: 1, fresh: true },
  { title: 'Walden', tone: 'green', day: 0, fresh: true },
  { title: 'Design call', tone: 'blue', day: 1, start: 14, hours: 1, fresh: true },
  { title: 'Exam', tone: 'blue', day: 2, start: 9, hours: 1.5, fresh: true },
  { title: 'Dune', tone: 'green', day: 3, fresh: true },
  { title: 'Fix sync bug', tone: 'blue', day: 4, start: 11, hours: 1, fresh: true },
]

const CALENDARS = [
  { name: 'Home', tone: 'amber', fresh: false },
  { name: 'Work', tone: 'pink', fresh: false },
  { name: 'Tasks', tone: 'blue', fresh: true },
  { name: 'Reading list', tone: 'green', fresh: true },
]

// A new item fades and rises a few pixels into place.
function arrival(frame: number, at: number) {
  const amount = interpolate(frame, [at, at + 10], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: ease,
  })
  return { opacity: amount, transform: `translateY(${(1 - amount) * 6}px)` }
}

function hourLabel(hour: number) {
  return String(hour).padStart(2, '0') + ':00'
}

export function Calendar({ frame, variant }: { frame: number; variant: Variant }) {
  const phone = variant.days < 5
  // The phone cut starts the day an hour later so each hour gets more room.
  const firstHour = phone ? 9 : 8
  const hourHeight = phone ? 31 : 46
  const days = DAYS.slice(0, variant.days)
  const shown = EVENTS.filter((event) => event.day < variant.days)
  const firstArrival = T.calendarFull + 24

  let freshIndex = 0
  const timed = shown.map((event) => {
    let style = {}
    if (event.fresh) {
      style = arrival(frame, firstArrival + 6 + freshIndex * 5)
      freshIndex += 1
    }
    return { event, style }
  })

  return (
    <div className={'landing-ui column calscene' + (phone ? ' phone' : '')} style={{ width: variant.width, height: variant.height }}>
      <p className="calcaption">A minute later, in Apple Calendar</p>

      <div className="row calwindow">
        {!phone && (
          <aside className="column calsidebar">
            <p className="calgroup">iCloud</p>
            {CALENDARS.map((calendar, index) => (
              <p
                key={calendar.name}
                className="row calname"
                style={calendar.fresh ? arrival(frame, T.calendarFull + 6 + index * 6) : {}}
              >
                <span className={'calswatch ' + calendar.tone}></span>
                {calendar.name}
              </p>
            ))}
          </aside>
        )}

        <div className="column calmain">
          <h2 className="calmonth">October 2026</h2>

          <div className="calgrid" style={{ gridTemplateColumns: `${phone ? 40 : 44}px repeat(${days.length}, 1fr)` }}>
            <span></span>
            {days.map((day) => (
              <span key={day} className="calday">
                {day}
              </span>
            ))}

            <span className="calhour">all-day</span>
            {days.map((day, dayIndex) => (
              <span key={day + 'allday'} className="calallday">
                {timed
                  .filter((item) => item.event.day === dayIndex && item.event.start === undefined)
                  .map((item) => (
                    <span key={item.event.title} className={'ev ' + item.event.tone} style={item.style}>
                      <span className="evtitle">{item.event.title}</span>
                    </span>
                  ))}
              </span>
            ))}

            <span className="column calhours" style={{ height: (LAST_HOUR - firstHour) * hourHeight }}>
              {Array.from({ length: Math.ceil((LAST_HOUR - firstHour) / 2) }, (_, index) => (
                <span key={index} className="calhour" style={{ height: hourHeight * 2 }}>
                  {hourLabel(firstHour + index * 2)}
                </span>
              ))}
            </span>
            {days.map((day, dayIndex) => (
              <span
                key={day + 'column'}
                className="calcolumn"
                style={{ height: (LAST_HOUR - firstHour) * hourHeight, backgroundSize: `100% ${hourHeight}px` }}
              >
                {timed
                  .filter((item) => item.event.day === dayIndex && item.event.start !== undefined)
                  .map((item) => (
                    <span
                      key={item.event.title}
                      className={'ev ' + item.event.tone}
                      style={{
                        ...item.style,
                        position: 'absolute',
                        left: 3,
                        right: 3,
                        top: ((item.event.start ?? 0) - firstHour) * hourHeight + 1,
                        height: (item.event.hours ?? 1) * hourHeight - 2,
                      }}
                    >
                      <span className="evtitle">{item.event.title}</span>
                      <small>{hourLabel(item.event.start ?? 0)}</small>
                    </span>
                  ))}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
