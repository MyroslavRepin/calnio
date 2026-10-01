import { interpolateColors } from 'remotion'

// The landing hero's task table and week, the same markup and classes as
// HeroSection.vue. Events sit in one layer over the week rather than inside a
// day column, so one can be dragged from a day to the next.

export type MockEvent = {
  title: string
  time: string
  tone: 'blue' | 'amber' | 'pink' | 'green'
  day: number
  hour: number
  appear: number
  lift: number
  target?: string
}

export type MockRow = {
  title: string
  chip: string
  highlight: number
  target?: string
}

const DAYS = [
  ['Mon', '5'],
  ['Tue', '6'],
  ['Wed', '7'],
  ['Thu', '8'],
  ['Fri', '9'],
]

const FIRST_HOUR = 8
const HOUR = 20

export function HeroMockup({ rows, events }: { rows: MockRow[]; events: MockEvent[] }) {
  return (
    <div className="row mockup">
      <div className="card tasks">
        <div className="row tablename">
          <h2>Tasks</h2>
          <span>Notion</span>
        </div>
        {rows.map((row) => (
          <div key={row.title} className="row task">
            <span className="checkbox"></span>
            <span className="taskname">{row.title}</span>
            <span
              className="chip"
              data-target={row.target}
              style={{
                background: interpolateColors(row.highlight, [0, 1], ['#f0f0f3', '#e6edfb']),
                color: interpolateColors(row.highlight, [0, 1], ['#46464b', '#1e4bb0']),
              }}
            >
              {row.chip}
            </span>
          </div>
        ))}
      </div>

      <span className="swap">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="#0a0a0a"
          strokeWidth="2.4"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M4 8h14l-4-4M20 16H6l4 4" />
        </svg>
      </span>

      <div className="card calendar">
        <div className="row calendarname">
          <h2>October</h2>
          <span>Apple Calendar</span>
        </div>
        <div className="week">
          {DAYS.map(([weekday, date]) => (
            <div key={weekday} className="weekday">
              {weekday}
              <b>{date}</b>
            </div>
          ))}
          {DAYS.map(([weekday]) => (
            <div key={weekday + 'run'} className="dayrun"></div>
          ))}
          <div className="evlayer">
            {events.map((event) => (
              <span
                key={event.title}
                className={'ev ' + event.tone}
                data-target={event.target}
                style={{
                  position: 'absolute',
                  left: `calc((100% - 24px) / 5 * ${event.day} + ${6 * event.day + 3}px)`,
                  width: 'calc((100% - 24px) / 5 - 6px)',
                  top: (event.hour - FIRST_HOUR) * HOUR,
                  height: 56,
                  opacity: event.appear,
                  transform: `translateY(${(1 - event.appear) * 6}px) scale(${1 + event.lift * 0.04})`,
                  boxShadow: `0 ${event.lift * 10}px ${event.lift * 24}px rgba(0, 0, 0, ${event.lift * 0.25})`,
                  zIndex: event.lift > 0 ? 2 : 1,
                }}
              >
                {event.title}
                <small>{event.time}</small>
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
