import { Mark } from './Mark'
import type { Variant } from './variants'

// The last few seconds: who made this, in one line.
export function EndCard({ variant }: { variant: Variant }) {
  return (
    <div className="landing-ui column endcard" style={{ width: variant.width, height: variant.height }}>
      <span className="endmark">
        <Mark />
      </span>
      <p className="endname">Calnio</p>
      <p className="endline">Notion and Apple Calendar, in sync.</p>
    </div>
  )
}
