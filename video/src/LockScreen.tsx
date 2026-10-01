// The landing page's lock screen (RealAlerts.vue): an older alert waiting, and
// a new one arriving on top of it the way iOS stacks them.

function Alert({ title, stamp, detail, faded }: { title: string; stamp: string; detail: string; faded: boolean }) {
  return (
    <div className={'row alert' + (faded ? ' faded' : '')}>
      <span className="column datemark">
        MON
        <b>5</b>
      </span>
      <span className="column alertcopy">
        <span className="row alertname">
          <b>{title}</b>
          <span className="stamp">{stamp}</span>
        </span>
        <span className="alertdetail">{detail}</span>
      </span>
    </div>
  )
}

export function LockScreen({ arrival }: { arrival: number }) {
  // Until the new alert lands, the older one holds the top slot.
  const slot = 86
  return (
    <div className="phone">
      <div className="column screen">
        <span className="notch"></span>
        <p className="today">Monday, October 5</p>
        <p className="clock">9:45</p>
        <div style={{ opacity: arrival, transform: `translateY(${(1 - arrival) * -24}px)` }}>
          <Alert title="Ship landing page" stamp="now" detail="Today at 10:00 · in 15 minutes" faded={false} />
        </div>
        <div style={{ transform: `translateY(${(1 - arrival) * -slot}px)` }}>
          <Alert title="Call with designer" stamp="15m ago" detail="Today at 10:30 · in 1 hour" faded={true} />
        </div>
      </div>
    </div>
  )
}
