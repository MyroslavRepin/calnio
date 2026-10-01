import { AbsoluteFill, interpolate, useCurrentFrame } from 'remotion'
import { Calendar } from './Calendar'
import { EndCard } from './EndCard'
import { Stage } from './Stage'
import { T } from './timeline'
import { variants } from './variants'

// The landing page cut: the walkthrough, the calendar it fills, the end card.
export function Setup({ variant: name, debug }: { variant: 'desktop' | 'phone'; debug: boolean }) {
  const frame = useCurrentFrame()
  const variant = variants[name]

  const calendarOpacity = interpolate(frame, [T.calendarIn, T.calendarFull], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  })
  const endOpacity = interpolate(frame, [T.endIn, T.endFull], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  })

  return (
    <AbsoluteFill style={{ background: '#f5f5f7' }}>
      {frame < T.calendarFull && <Stage frame={frame} variant={variant} debug={debug} />}

      <div
        style={{
          position: 'absolute',
          inset: 0,
          width: variant.width,
          height: variant.height,
          transform: `scale(${variant.scale})`,
          transformOrigin: '0 0',
        }}
      >
        {frame >= T.calendarIn && frame < T.endFull && (
          <div style={{ position: 'absolute', inset: 0, opacity: calendarOpacity }}>
            <Calendar frame={frame} variant={variant} />
          </div>
        )}

        {frame >= T.endIn && (
          <div style={{ position: 'absolute', inset: 0, opacity: endOpacity }}>
            <EndCard variant={variant} />
          </div>
        )}
      </div>
    </AbsoluteFill>
  )
}
