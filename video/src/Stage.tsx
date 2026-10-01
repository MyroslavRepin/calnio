import { useLayoutEffect, useRef, useState } from 'react'
import '../../frontend/src/styles/tokens.css'
import '../../frontend/src/styles/layout.css'
import '../../frontend/src/styles/base.css'
import '../../frontend/src/styles/components.css'
import '../../frontend/src/styles/landing.css'
import './welcome.css'
import './scenes.css'
import { Cursor } from './Cursor'
import { progress, T } from './timeline'
import type { Variant } from './variants'
import { Welcome } from './Welcome'

// How far the welcome page is scrolled: down to the iCloud form while it is
// being filled, to the database list after, and back to the top at the end.
function scrollAt(frame: number, two: number, three: number) {
  if (frame < T.appleDone) {
    return two * progress(frame, T.notionDone + 6, T.notionDone + 30)
  }
  if (frame < T.allDone) {
    return three
  }
  return three * (1 - progress(frame, T.allDone, T.allDone + 20))
}

// The /welcome walkthrough at one frame: the page, its scroll and the pointer,
// drawn at the variant's width and scaled up from its top left corner. Every
// cut of the video draws the setup through this.
export function Stage({ frame, variant, debug }: { frame: number; variant: Variant; debug: boolean }) {
  const stage = useRef<HTMLDivElement>(null)
  const [measured, setMeasured] = useState('')

  // Debug renders print every target's point in the app's own pixels over the
  // frame, which is where the cursor stops in variants.ts come from.
  useLayoutEffect(() => {
    if (!debug || !stage.current) {
      return
    }
    const origin = stage.current.getBoundingClientRect()
    const lines: string[] = []
    stage.current.querySelectorAll('[data-target]').forEach((element) => {
      const box = element.getBoundingClientRect()
      const x = Math.round((box.left - origin.left) / variant.scale + 40)
      const y = Math.round((box.top - origin.top + box.height / 2) / variant.scale)
      lines.push(`${element.getAttribute('data-target')}: [${x}, ${y}]`)
    })
    setMeasured(lines.join('\n'))
  }, [debug, frame, variant.scale])

  const scroll = scrollAt(frame, variant.scroll.two, variant.scroll.three)

  return (
    <div
      ref={stage}
      style={{
        position: 'relative',
        width: variant.width,
        height: variant.height,
        overflow: 'hidden',
        transform: `scale(${variant.scale})`,
        transformOrigin: '0 0',
      }}
    >
      <div style={{ transform: `translateY(${-scroll}px)`, minHeight: '100%' }}>
        <Welcome frame={frame} />
      </div>
      <Cursor frame={frame} variant={variant} />
      {debug && (
        <pre style={{ position: 'absolute', right: 4, top: 4, margin: 0, padding: 6, background: '#ff0', fontSize: 14 }}>
          {measured}
        </pre>
      )}
    </div>
  )
}
