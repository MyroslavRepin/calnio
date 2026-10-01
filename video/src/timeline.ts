import { Easing, interpolate } from 'remotion'

// Every beat of the video, in frames at 30fps. Each scene reads its state off
// these, so retiming the video means editing this list and nothing else.
export const T = {
  notionPress: 50,
  notionDone: 84,
  emailClick: 128,
  emailTypeStart: 132,
  emailTypeEnd: 168,
  passwordClick: 203,
  passwordPaste: 209,
  applePress: 244,
  appleDone: 290,
  listLoaded: 312,
  tickTasks: 343,
  tickReading: 373,
  startPress: 409,
  allDone: 450,
  calendarIn: 515,
  calendarFull: 535,
  endIn: 695,
  endFull: 715,
}

export const TOTAL = 780

export const CLICKS = [
  T.notionPress,
  T.emailClick,
  T.passwordClick,
  T.applePress,
  T.tickTasks,
  T.tickReading,
  T.startPress,
]

// The one curve every move uses: a gentle ease in and out, never a bounce.
export const ease = Easing.bezier(0.4, 0, 0.2, 1)

// 0 before `from`, 1 after `to`, eased in between.
export function progress(frame: number, from: number, to: number) {
  return interpolate(frame, [from, to], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: ease,
  })
}

// True for the few frames a button looks pushed in.
export function pressed(frame: number, at: number) {
  return frame >= at && frame < at + 5
}
