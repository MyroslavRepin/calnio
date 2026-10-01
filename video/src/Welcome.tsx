import type { ReactNode } from 'react'
import { Mark } from './Mark'
import { pressed, T } from './timeline'

// The /welcome page at one frame, built from the same markup and classes as
// WelcomeView.vue so the shared stylesheets draw it exactly as the app does.
// Nothing here is interactive: every state is a function of the frame.

const EMAIL = 'you@icloud.com'
const PASSWORD = 'abcd-efgh-ijkl-mnop'

function Step(props: {
  number: string
  title: string
  summary: string
  done: boolean
  open: boolean
  locked: boolean
  children?: ReactNode
}) {
  let marker: string = props.number
  if (props.done) {
    marker = '✓'
  }
  return (
    <section className={'column setupstep' + (props.locked ? ' locked' : '')}>
      <div className="row stepline">
        <span className={'num' + (props.done ? ' done' : '') + (props.open ? ' now' : '')}>{marker}</span>
        <h2 className="steptitle">{props.title}</h2>
        {props.done && <span className="label success">{props.summary}</span>}
        {!props.done && props.locked && <span className="note">Next</span>}
      </div>
      {props.open && <div className="column stepbody">{props.children}</div>}
    </section>
  )
}

export function Welcome({ frame }: { frame: number }) {
  const notionDone = frame >= T.notionDone
  const appleDone = frame >= T.appleDone
  const allDone = frame >= T.allDone

  // The email types itself a letter at a time, the password arrives in one
  // paste, the way people copy it from Apple's page.
  const typed = Math.floor(
    ((frame - T.emailTypeStart) / (T.emailTypeEnd - T.emailTypeStart)) * EMAIL.length,
  )
  const email = EMAIL.slice(0, Math.max(0, Math.min(EMAIL.length, typed)))
  const password = frame >= T.passwordPaste ? PASSWORD : ''

  const ticked: string[] = []
  if (frame >= T.tickTasks) {
    ticked.push('tasks')
  }
  if (frame >= T.tickReading) {
    ticked.push('reading')
  }

  let doneCount = 0
  if (notionDone) {
    doneCount = 1
  }
  if (appleDone) {
    doneCount = 2
  }
  if (allDone) {
    doneCount = 3
  }

  let calendarNote = ''
  if (ticked.length === 1) {
    calendarNote = 'Calnio will use an Apple calendar of the same name, or create it.'
  }
  if (ticked.length === 2) {
    calendarNote = 'Calnio will use 2 Apple calendars of the same names, creating any that do not exist yet.'
  }

  const notionBusy = frame >= T.notionPress + 4 && !notionDone
  const appleBusy = frame >= T.applePress + 4 && !appleDone
  const startBusy = frame >= T.startPress + 4 && !allDone

  return (
    <div className="app-ui column" style={{ minHeight: '100%' }}>
      <header className="topbar">
        <div className="row topbarrow">
          <span className="wordmark">
            <span className="plate">
              <Mark />
            </span>
            Calnio
          </span>
          <p className="note">{doneCount} of 3 done</p>
        </div>
      </header>

      <main className="column main">
        <header className="column page-head">
          <h1 className="title">{allDone ? 'You are set up' : 'Set up Calnio'}</h1>
          <p className="lead">
            {allDone
              ? 'Your Notion dates are in Apple Calendar, and Calnio keeps them there on a schedule. Change anything from your dashboard.'
              : 'Three steps, about two minutes. At the end your Notion dates show up in Apple Calendar as real events.'}
          </p>
          {allDone && <span className="btn">Go to your dashboard</span>}
        </header>

        <div className="card steps">
          <Step number="1" title="Connect Notion" summary="My workspace" done={notionDone} open={!notionDone} locked={false}>
            <div className="column notion">
              <p className="body">
                Notion will ask which pages Calnio may use. Tick every database you might want in your
                calendar, you choose which of them actually syncs in the next step. Calnio cannot see
                anything you do not tick.
              </p>
              <button
                className={'btn' + (pressed(frame, T.notionPress) ? ' pushed' : '')}
                type="button"
                disabled={notionBusy}
                data-target="notion"
              >
                {notionBusy ? 'Opening Notion…' : 'Connect Notion'}
              </button>
              <p className="note">Takes one click. You can revoke it from Notion at any time.</p>
            </div>
          </Step>

          <Step
            number="2"
            title="Connect iCloud"
            summary={EMAIL}
            done={appleDone}
            open={notionDone && !appleDone}
            locked={!notionDone}
          >
            <div className="column apple">
              <p className="body">
                Apple does not offer a sign-in button for calendar access. The only way in is an{' '}
                <strong>app-specific password</strong>, which you generate yourself and can revoke at any
                time. It takes about a minute.
              </p>
              <ol className="column walkthrough">
                <li>
                  Open <a>account.apple.com</a> and sign in
                </li>
                <li>Go to Sign-In and Security, then App-Specific Passwords</li>
                <li>Choose Generate an app-specific password</li>
                <li>
                  Name it <code>Calnio</code> and copy the <code>xxxx-xxxx-xxxx-xxxx</code> it shows
                </li>
              </ol>
              <div className="column credentials">
                <label className="column field">
                  <span>Apple Account email</span>
                  <input
                    className={frame >= T.emailClick && frame < T.passwordClick ? 'focused' : ''}
                    value={email}
                    placeholder="you@icloud.com"
                    readOnly
                    data-target="email"
                  />
                </label>
                <label className="column field">
                  <span>App-specific password</span>
                  <input
                    className={frame >= T.passwordClick && frame < T.applePress ? 'focused' : ''}
                    value={password}
                    placeholder="xxxx-xxxx-xxxx-xxxx"
                    readOnly
                    data-target="password"
                  />
                </label>
                <button
                  className={'btn' + (pressed(frame, T.applePress) ? ' pushed' : '')}
                  type="button"
                  disabled={appleBusy}
                  data-target="apple"
                >
                  {appleBusy ? 'Checking with iCloud…' : 'Connect iCloud'}
                </button>
              </div>
            </div>
          </Step>

          <Step
            number="3"
            title="Pick your databases"
            summary="2 syncs"
            done={allDone}
            open={appleDone && !allDone}
            locked={!appleDone}
          >
            <div className="column addsync">
              {frame < T.listLoaded ? (
                <p className="loading">Reading your Notion databases…</p>
              ) : (
                <>
                  <p className="body">
                    Tick the databases you want in Apple Calendar. Each one gets its own calendar, so you
                    can colour and hide them separately.
                  </p>
                  <ul className="picklist">
                    {[
                      ['tasks', 'Tasks'],
                      ['reading', 'Reading list'],
                      ['content', 'Content calendar'],
                    ].map(([id, title]) => (
                      <li key={id}>
                        <label data-target={id}>
                          <input type="checkbox" checked={ticked.includes(id)} readOnly />
                          <span>{title}</span>
                        </label>
                      </li>
                    ))}
                  </ul>
                  {calendarNote && <p className="note">{calendarNote}</p>}
                  <div className="row actions">
                    <button
                      className={'btn' + (pressed(frame, T.startPress) ? ' pushed' : '')}
                      type="button"
                      disabled={ticked.length === 0 || startBusy}
                      data-target="start"
                    >
                      {startBusy ? 'Setting up…' : 'Start syncing'}
                    </button>
                    <button className="btn plain" type="button">
                      Share more databases
                    </button>
                  </div>
                </>
              )}
            </div>
          </Step>
        </div>

        {!allDone && (
          <footer className="exitrow">
            <a>Finish this later</a>
          </footer>
        )}
      </main>
    </div>
  )
}
