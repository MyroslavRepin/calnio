import { Composition } from 'remotion'
import { ProductHunt, PRODUCT_HUNT_TOTAL } from './ProductHunt'
import { Setup } from './Setup'
import { TOTAL } from './timeline'

// Two cuts of one video: the landing page plays the phone one under 600px,
// where the desktop cut would shrink the app's text past reading.
export function Root() {
  return (
    <>
      <Composition
        id="SetupDesktop"
        component={Setup}
        durationInFrames={TOTAL}
        fps={30}
        width={1440}
        height={1080}
        defaultProps={{ variant: 'desktop' as const, debug: false }}
      />
      <Composition
        id="SetupPhone"
        component={Setup}
        durationInFrames={TOTAL}
        fps={30}
        width={1080}
        height={1350}
        defaultProps={{ variant: 'phone' as const, debug: false }}
      />
      <Composition
        id="ProductHunt"
        component={ProductHunt}
        durationInFrames={PRODUCT_HUNT_TOTAL}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{ debug: false }}
      />
    </>
  )
}
