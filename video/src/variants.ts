// The two cuts differ only in how wide the app is drawn and where things land
// on screen. Points are in the app's own CSS pixels, measured with
// `--props='{"debug":true}'`, which logs every [data-target] centre.
export type Point = [number, number]

export type Variant = {
  width: number
  height: number
  scale: number
  scroll: { two: number; three: number }
  cursor: {
    start: Point
    notion: Point
    email: Point
    password: Point
    apple: Point
    tasks: Point
    reading: Point
    start_: Point
    away: Point
  }
  days: number
}

export const variants: Record<'desktop' | 'phone' | 'producthunt', Variant> = {
  desktop: {
    width: 960,
    height: 720,
    scale: 1.5,
    scroll: { two: 190, three: 60 },
    cursor: {
      start: [880, 690],
      notion: [209, 341],
      email: [209, 346],
      password: [209, 421],
      apple: [209, 469],
      tasks: [210, 411],
      reading: [210, 452],
      start_: [209, 572],
      away: [880, 690],
    },
    days: 5,
  },
  phone: {
    width: 400,
    height: 500,
    scale: 2.7,
    scroll: { two: 377, three: 263 },
    cursor: {
      start: [370, 480],
      notion: [129, 425],
      email: [129, 327],
      password: [129, 402],
      apple: [129, 450],
      tasks: [130, 271],
      reading: [130, 312],
      start_: [129, 462],
      away: [370, 480],
    },
    days: 3,
  },
  // The window on the right of the Product Hunt cut.
  producthunt: {
    width: 600,
    height: 640,
    scale: 1.5,
    scroll: { two: 100, three: 60 },
    cursor: {
      start: [560, 620],
      notion: [129, 341],
      email: [129, 457],
      password: [129, 532],
      apple: [129, 580],
      tasks: [130, 411],
      reading: [130, 452],
      start_: [129, 588],
      away: [560, 620],
    },
    days: 5,
  },
}
