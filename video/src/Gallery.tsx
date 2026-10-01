import { AbsoluteFill, useCurrentFrame } from 'remotion'
import { Pointer } from './Cursor'
import { HeroMockup } from './HeroMockup'
import type { MockEvent, MockRow } from './HeroMockup'
import { Alerts, amount, arrive, Board, BoardSize, Hero, Indie, Setup, Targets } from './ProductHunt'

// Product Hunt gallery images, 1270x760: four stills taken from the video's
// scenes, and one loop of the two-way edit.

export const LOOP_LENGTH = 210

type Point = [number, number]

function between(frame: number, from: number, to: number, start: Point, end: Point): Point {
  const done = amount(frame, from, to)
  return [start[0] + (end[0] - start[0]) * done, start[1] + (end[1] - start[1]) * done]
}

// Gym is dragged a day right in Apple Calendar and the Notion date follows,
// then the Notion date is set back and the event follows. It ends where it
// started, so the loop has no seam.
function TwoWayLoop({ debug }: { debug: boolean }) {
  const frame = useCurrentFrame()

  const rest: Point = [1180, 700]
  const thursday: Point = [982, 586]
  const friday: Point = [1085, 586]
  const chip: Point = [425, 542]

  const drag = amount(frame, 40, 68)
  const back = amount(frame, 164, 182)

  let pointer: Point = between(frame, 10, 35, rest, thursday)
  if (frame >= 40) {
    pointer = between(frame, 40, 68, thursday, friday)
  }
  if (frame >= 118) {
    pointer = between(frame, 118, 146, friday, chip)
  }
  if (frame >= 186) {
    pointer = between(frame, 186, 206, chip, rest)
  }
  const pressed = (frame >= 37 && frame < 70) || (frame >= 150 && frame < 155)

  let chipText = 'Thu, 18:00'
  let highlight = 0
  if (frame >= 84 && frame < 150) {
    chipText = 'Fri, 18:00'
    highlight = 1 - amount(frame, 84, 114)
  }
  if (frame >= 150) {
    highlight = 1 - amount(frame, 150, 180)
  }

  let lift = 0
  if (frame >= 37 && frame < 76) {
    lift = frame < 70 ? amount(frame, 37, 43) : 1 - amount(frame, 70, 76)
  }

  const rows: MockRow[] = [
    { title: 'Ship landing page', chip: 'Mon, 10:00', highlight: 0 },
    { title: 'Call with designer', chip: 'Tue, 14:00', highlight: 0 },
    { title: 'Physics exam', chip: 'Wed, 09:00', highlight: 0 },
    { title: 'Gym', chip: chipText, highlight, target: 'gymchip' },
  ]
  const events: MockEvent[] = [
    { title: 'Ship landing page', time: '10:00', tone: 'blue', day: 0, hour: 10, appear: 1, lift: 0 },
    { title: 'Call with designer', time: '14:00', tone: 'amber', day: 1, hour: 14, appear: 1, lift: 0 },
    { title: 'Physics exam', time: '09:00', tone: 'pink', day: 2, hour: 9, appear: 1, lift: 0 },
    { title: 'Gym', time: '18:00', tone: 'green', day: 3 + drag - back, hour: 18, appear: 1, lift, target: 'gym' },
  ]

  let caption = ''
  let captionStyle = {}
  if (frame >= 72) {
    caption = 'Dragged in Apple Calendar. The date in Notion follows.'
    captionStyle = arrive(frame, 72)
  }
  if (frame >= 152) {
    caption = 'Changed in Notion. The event follows in Apple Calendar.'
    captionStyle = { ...arrive(frame, 152), opacity: amount(frame, 152, 166) * (1 - amount(frame, 192, 206)) }
  }

  return (
    <Board dark={true} fade={1}>
      <div className="heroheads">
        <h2 className="headline twowayline">Edit on either side, and the other follows.</h2>
      </div>
      <div className="heromock">
        <HeroMockup rows={rows} events={events} />
      </div>
      <p className="caption" style={captionStyle}>
        {caption}
      </p>
      <Pointer x={pointer[0]} y={pointer[1]} clicking={pressed} />
      {debug && <Targets />}
    </Board>
  )
}

export function GalleryLoop({ debug }: { debug: boolean }) {
  return (
    <AbsoluteFill style={{ background: '#0a0a0a' }}>
      <BoardSize.Provider value={{ width: 1270, height: 760, scale: 1 }}>
        <TwoWayLoop debug={debug} />
      </BoardSize.Provider>
    </AbsoluteFill>
  )
}

// A video scene at twice the gallery size so it stays sharp. Each still is one
// frame of it, picked with --frame on `remotion still`.
export const STILL_LENGTH = 400

export function GalleryStill({ scene }: { scene: 'hero' | 'alerts' | 'setup' | 'indie' }) {
  if (scene === 'setup') {
    // The setup scene is laid out in 1920px, so it is drawn at the gallery's
    // shape in that width and scaled down to fit.
    return (
      <AbsoluteFill style={{ background: '#f5f5f7' }}>
        <div style={{ position: 'relative', width: 1920, height: 1149, transform: 'scale(1.3229)', transformOrigin: '0 0' }}>
          <Setup debug={false} />
        </div>
      </AbsoluteFill>
    )
  }

  let content = <Indie />
  if (scene === 'hero') {
    content = <Hero debug={false} />
  }
  if (scene === 'alerts') {
    content = <Alerts />
  }

  return (
    <AbsoluteFill style={{ background: scene === 'alerts' ? '#f5f5f7' : '#0a0a0a' }}>
      <BoardSize.Provider value={{ width: 1270, height: 760, scale: 2 }}>
        {content}
      </BoardSize.Provider>
    </AbsoluteFill>
  )
}
