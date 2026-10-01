import { interpolate } from 'remotion'
import { CLICKS, ease, T } from './timeline'
import type { Point, Variant } from './variants'

// Where the pointer is at each beat. Between two stops it glides on the shared
// curve, so it moves like a hand, not like a tween.
function stops(variant: Variant): Array<[number, Point]> {
  const c = variant.cursor
  return [
    [0, c.start],
    [15, c.start],
    [45, c.notion],
    [95, c.notion],
    [124, c.email],
    [176, c.email],
    [200, c.password],
    [214, c.password],
    [240, c.apple],
    [316, c.apple],
    [340, c.tasks],
    [348, c.tasks],
    [370, c.reading],
    [380, c.reading],
    [405, c.start_],
    [458, c.start_],
    [495, c.away],
  ]
}

function position(frame: number, variant: Variant): Point {
  const list = stops(variant)
  for (let index = 0; index < list.length - 1; index++) {
    const [fromFrame, from] = list[index]
    const [toFrame, to] = list[index + 1]
    if (frame >= fromFrame && frame <= toFrame) {
      const amount = interpolate(frame, [fromFrame, toFrame], [0, 1], { easing: ease })
      return [from[0] + (to[0] - from[0]) * amount, from[1] + (to[1] - from[1]) * amount]
    }
  }
  return list[list.length - 1][1]
}

export function Cursor({ frame, variant }: { frame: number; variant: Variant }) {
  const [x, y] = position(frame, variant)
  const clicking = CLICKS.some((at) => frame >= at && frame < at + 5)
  const opacity = interpolate(frame, [T.allDone + 30, T.allDone + 45], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  })

  return <Pointer x={x} y={y} clicking={clicking} opacity={opacity} />
}

// The macOS arrow: black with a white rim, tip at the exact point.
export function Pointer({ x, y, clicking, opacity = 1 }: { x: number; y: number; clicking: boolean; opacity?: number }) {
  return (
    <svg
      viewBox="0 0 24 24"
      width={22}
      height={22}
      style={{
        position: 'absolute',
        left: x,
        top: y,
        opacity,
        transform: `scale(${clicking ? 0.85 : 1})`,
        transformOrigin: '0 0',
        filter: 'drop-shadow(0 1px 1.5px rgba(0,0,0,0.35))',
        pointerEvents: 'none',
        zIndex: 10,
      }}
    >
      <path
        d="M1.5 1.5 L1.5 19 L6 14.8 L9.2 21.8 L12.4 20.4 L9.3 13.6 L15.5 13.6 Z"
        fill="#0a0a0a"
        stroke="#ffffff"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
    </svg>
  )
}
