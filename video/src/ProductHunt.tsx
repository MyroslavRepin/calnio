import { createContext, useContext, useLayoutEffect, useRef, useState } from 'react'
import type { CSSProperties, ReactNode } from 'react'
import { AbsoluteFill, Easing, interpolate, Sequence, useCurrentFrame } from 'remotion'
import { Pointer } from './Cursor'
import { HeroMockup } from './HeroMockup'
import type { MockEvent, MockRow } from './HeroMockup'
import './landing-copies.css'
import { LockScreen } from './LockScreen'
import { Mark } from './Mark'
import './producthunt.css'
import { Stage } from './Stage'
import { variants } from './variants'

// The Product Hunt video, rebuilt from the landing page itself: the same
// headlines, the hero's table and week, the lock screen and the /welcome page,
// on flat black and flat light grounds. No glow, no blur-in, no count-up, no
// labels above headlines. Between a dark and a light section the next ground
// rises from the bottom; between two of the same, the content crossfades.

const SCENES = {
  intro: { from: 0, length: 100 },
  hero: { from: 100, length: 370 },
  alerts: { from: 470, length: 180 },
  setup: { from: 650, length: 375 },
  indie: { from: 1025, length: 165 },
  end: { from: 1190, length: 120 },
}

export const PRODUCT_HUNT_TOTAL = SCENES.end.from + SCENES.end.length

const WIPE = 15
const curve = Easing.bezier(0.4, 0, 0.2, 1)

export function amount(frame: number, from: number, to: number) {
  return interpolate(frame, [from, to], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: curve,
  })
}

// Content arrives with a short fade and a few pixels of rise. Nothing else.
export function arrive(frame: number, at: number): CSSProperties {
  const shown = amount(frame, at, at + 14)
  return { opacity: shown, transform: `translateY(${(1 - shown) * 10}px)` }
}

// The next section's ground rising from the bottom edge.
function Rise({ color, start }: { color: string; start: number }) {
  const frame = useCurrentFrame()
  const covered = 100 * amount(frame, start, start + WIPE)
  return <AbsoluteFill style={{ background: color, clipPath: `inset(${100 - covered}% 0 0 0)` }} />
}

// The board's size and scale. The video draws 1280x720 at 1.5x; the gallery
// images draw Product Hunt's 1270x760 at 1x or 2x.
export const BoardSize = createContext({ width: 1280, height: 720, scale: 1.5 })

// Every scene but setup is drawn at 1280x720 and scaled to 1920x1080, so the
// landing page's own type sizes and spacing apply unchanged.
export function Board({ dark, fade, children }: { dark: boolean; fade: number; children: ReactNode }) {
  const size = useContext(BoardSize)
  return (
    <AbsoluteFill style={{ background: dark ? '#0a0a0a' : '#f5f5f7' }}>
      <div
        className={'landing-ui board' + (dark ? ' dark' : '')}
        style={{
          width: size.width,
          height: size.height,
          transform: `scale(${size.scale})`,
          transformOrigin: '0 0',
          opacity: fade,
        }}
      >
        {children}
      </div>
    </AbsoluteFill>
  )
}

function Intro() {
  const frame = useCurrentFrame()
  const fade = 1 - amount(frame, 88, 100)
  return (
    <Board dark={true} fade={fade}>
      <h1 className="headline hero introline">
        <span style={{ display: 'block', ...arrive(frame, 6) }}>You plan your week in Notion.</span>
        <span className="dim" style={{ display: 'block', ...arrive(frame, 34) }}>
          Your calendar has no idea.
        </span>
      </h1>
    </Board>
  )
}

// The hero's week fills in, then two edits show the sync running both ways:
// a date changed in Notion moves the event, an event dragged in Apple Calendar
// moves the Notion date.
export function Hero({ debug }: { debug: boolean }) {
  const frame = useCurrentFrame()

  const swap = amount(frame, 105, 115)
  const gymDrag = amount(frame, 156, 184)
  const callMove = amount(frame, 262, 280)
  const gymMoved = frame >= 200
  const callChanged = frame >= 246

  const rows: MockRow[] = [
    { title: 'Ship landing page', chip: 'Mon, 10:00', highlight: 0 },
    {
      title: 'Call with designer',
      chip: callChanged ? 'Wed, 14:00' : 'Tue, 14:00',
      highlight: callChanged ? 1 - amount(frame, 260, 290) : 0,
      target: 'callchip',
    },
    { title: 'Physics exam', chip: 'Wed, 09:00', highlight: 0 },
    {
      title: 'Gym',
      chip: gymMoved ? 'Fri, 18:00' : 'Thu, 18:00',
      highlight: gymMoved ? 1 - amount(frame, 214, 244) : 0,
    },
  ]

  const lift = frame >= 152 && frame < 188 ? amount(frame, 152, 158) : 1 - amount(frame, 186, 192)
  const events: MockEvent[] = [
    { title: 'Ship landing page', time: '10:00', tone: 'blue', day: 0, hour: 10, appear: amount(frame, 40, 50), lift: 0 },
    {
      title: 'Call with designer',
      time: '14:00',
      tone: 'amber',
      day: 1 + callMove,
      hour: 14,
      appear: amount(frame, 48, 58),
      lift: 0,
    },
    { title: 'Physics exam', time: '09:00', tone: 'pink', day: 2, hour: 9, appear: amount(frame, 56, 66), lift: 0 },
    {
      title: 'Gym',
      time: '18:00',
      tone: 'green',
      day: 3 + gymDrag,
      hour: 18,
      appear: amount(frame, 64, 74),
      lift: frame >= 152 && frame < 192 ? lift : 0,
      target: 'gym',
    },
  ]

  // The pointer: in from the corner, onto Gym, drags it a day right, then
  // across to the Notion chip of the design call.
  const gymAt: [number, number] = [990, 584]
  const fridayAt: [number, number] = [1095, 584]
  const chipAt: [number, number] = [420, 442]
  let pointer: [number, number] = [1240, 700]
  if (frame >= 125) {
    const reach = amount(frame, 125, 150)
    pointer = [1240 + (gymAt[0] - 1240) * reach, 700 + (gymAt[1] - 700) * reach]
  }
  if (frame >= 156) {
    pointer = [gymAt[0] + (fridayAt[0] - gymAt[0]) * gymDrag, gymAt[1]]
  }
  if (frame >= 210) {
    const reach = amount(frame, 210, 240)
    pointer = [fridayAt[0] + (chipAt[0] - fridayAt[0]) * reach, fridayAt[1] + (chipAt[1] - fridayAt[1]) * reach]
  }
  if (frame >= 290) {
    const away = amount(frame, 290, 320)
    pointer = [chipAt[0] + (1240 - chipAt[0]) * away, chipAt[1] + (700 - chipAt[1]) * away]
  }
  const pressed = (frame >= 152 && frame < 186) || (frame >= 244 && frame < 249)

  let caption = ''
  if (frame >= 188) {
    caption = 'Dragged in Apple Calendar. The date in Notion follows.'
  }
  if (frame >= 250) {
    caption = 'Changed in Notion. The event follows in Apple Calendar.'
  }
  const captionStyle = frame < 250 ? arrive(frame, 188) : arrive(frame, 250)

  return (
    <Board dark={true} fade={1}>
      <div className="heroheads">
        <h1 className="headline hero" style={{ opacity: 1 - swap, ...(frame < 20 ? arrive(frame, 0) : {}) }}>
          Notion and Apple Calendar.
          <br />
          <span className="dim">Finally in sync. Both ways.</span>
        </h1>
        <h2 className="headline twowayline" style={arrive(frame, 115)}>
          Edit on either side, and the other follows.
        </h2>
      </div>

      <div className="heromock" style={arrive(frame, 10)}>
        <HeroMockup rows={rows} events={events} />
      </div>

      <p className="caption" style={captionStyle}>
        {caption}
      </p>

      {frame >= 120 && frame < 330 && <Pointer x={pointer[0]} y={pointer[1]} clicking={pressed} />}
      {debug && <Targets />}
    </Board>
  )
}

export function Alerts() {
  const frame = useCurrentFrame()
  const fade = 1 - amount(frame, 170, 180)
  return (
    <Board dark={false} fade={fade}>
      <div className="column alertclaim">
        <h2 className="headline" style={arrive(frame, 0)}>
          Calnio writes real events into iCloud.
        </h2>
        <p className="tagline" style={arrive(frame, 8)}>
          A webcal feed is read-only and stays silent. Calnio's events are ordinary iCloud events: they alert on
          every device, and you can edit them from either side.
        </p>
      </div>
      <div className="alertphone" style={arrive(frame, 10)}>
        <LockScreen arrival={amount(frame, 50, 62)} />
      </div>
    </Board>
  )
}

export function Setup({ debug }: { debug: boolean }) {
  const frame = useCurrentFrame()
  // The walkthrough runs at one and a half times the landing cut's pace and
  // stops on "You are set up".
  const walkthrough = Math.min(470, Math.max(0, (frame - 24) * 1.5))
  const shown = arrive(frame, 10)

  return (
    <AbsoluteFill className="setupscene">
      <div className="setupcopy">
        <h2 className="setupheadline" style={arrive(frame, 0)}>
          Ticking a database is the whole setup.
        </h2>
        <p className="setupbody" style={arrive(frame, 8)}>
          Connect Notion, paste an Apple app-specific password, tick the databases you want. Calnio finds the
          date column and creates the calendar.
        </p>
      </div>
      <div className="setupwindow" style={shown}>
        <Stage frame={walkthrough} variant={variants.producthunt} debug={debug} />
      </div>
      <Rise color="#0a0a0a" start={SCENES.setup.length - WIPE} />
    </AbsoluteFill>
  )
}

export function Indie() {
  const frame = useCurrentFrame()
  const fade = 1 - amount(frame, 155, 165)
  const facts = [
    { figure: '1', body: 'developer. Bug reports go straight to me.', filled: false },
    { figure: 'π', body: 'Hosted on a Raspberry Pi sitting on my desk.', filled: false },
    { figure: '$0', body: 'Free. Just tell me what breaks.', filled: true },
  ]
  return (
    <Board dark={true} fade={fade}>
      <h2 className="headline indiehead" style={arrive(frame, 0)}>
        I built Calnio for my own tasks, and I use it every day.
      </h2>
      <div className="row indiefacts">
        {facts.map((fact, index) => (
          <div
            key={fact.figure}
            className={'column indiefact' + (fact.filled ? ' filled' : '')}
            style={arrive(frame, 14 + index * 4)}
          >
            <span className="indiefigure">{fact.figure}</span>
            <p>{fact.body}</p>
          </div>
        ))}
      </div>
    </Board>
  )
}

function End() {
  const frame = useCurrentFrame()
  return (
    <Board dark={true} fade={1}>
      <div className="column endbody">
        <span className="endplate" style={arrive(frame, 0)}>
          <Mark plate="#ffffff" glyph="#0a0a0a" />
        </span>
        <p className="endtitle" style={arrive(frame, 6)}>
          Calnio
        </p>
        <p className="endline" style={arrive(frame, 12)}>
          Notion and Apple Calendar, in sync. Both ways.
        </p>
        <p className="endsmall" style={arrive(frame, 20)}>
          Free at calnio.myroslavrepin.com · Now on Product Hunt
        </p>
      </div>
    </Board>
  )
}

// Debug renders print every [data-target] centre in board pixels, which is
// where the pointer stops in Hero come from.
export function Targets() {
  const size = useContext(BoardSize)
  const box = useRef<HTMLPreElement>(null)
  const [text, setText] = useState('')
  useLayoutEffect(() => {
    const board = box.current?.closest('.board')
    if (!board) {
      return
    }
    const origin = board.getBoundingClientRect()
    const lines: string[] = []
    board.querySelectorAll('[data-target]').forEach((element) => {
      const rect = element.getBoundingClientRect()
      const x = Math.round((rect.left - origin.left + rect.width / 2) / size.scale)
      const y = Math.round((rect.top - origin.top + rect.height / 2) / size.scale)
      lines.push(`${element.getAttribute('data-target')}: [${x}, ${y}]`)
    })
    setText(lines.join('\n'))
  })
  return (
    <pre ref={box} className="debugtargets">
      {text}
    </pre>
  )
}

export function ProductHunt({ debug }: { debug: boolean }) {
  return (
    <AbsoluteFill style={{ background: '#0a0a0a' }}>
      <Sequence from={SCENES.intro.from} durationInFrames={SCENES.intro.length}>
        <Intro />
      </Sequence>
      <Sequence from={SCENES.hero.from} durationInFrames={SCENES.hero.length}>
        <Hero debug={debug} />
        <Rise color="#f5f5f7" start={SCENES.hero.length - WIPE} />
      </Sequence>
      <Sequence from={SCENES.alerts.from} durationInFrames={SCENES.alerts.length}>
        <Alerts />
      </Sequence>
      <Sequence from={SCENES.setup.from} durationInFrames={SCENES.setup.length}>
        <Setup debug={debug} />
      </Sequence>
      <Sequence from={SCENES.indie.from} durationInFrames={SCENES.indie.length}>
        <Indie />
      </Sequence>
      <Sequence from={SCENES.end.from} durationInFrames={SCENES.end.length}>
        <End />
      </Sequence>
    </AbsoluteFill>
  )
}
