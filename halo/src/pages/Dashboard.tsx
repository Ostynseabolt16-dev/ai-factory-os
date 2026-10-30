import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import { demoAppointments, loadBookings, serviceById, stylist } from '../data'

export function Dashboard() {
  const todayLabel = useMemo(
    () =>
      new Date().toLocaleDateString(undefined, {
        weekday: 'long',
        month: 'long',
        day: 'numeric',
      }),
    [],
  )

  const localBookings = loadBookings()

  return (
    <div className="dash">
      <div className="dash-top">
        <div>
          <p>
            <span className="live-dot" aria-hidden="true" />
            {stylist.name} · today
          </p>
          <h1>{todayLabel}</h1>
        </div>
        <div className="cta-row">
          <Link className="btn btn-ghost" style={{ color: 'var(--ink)', boxShadow: 'inset 0 0 0 1.5px var(--line)' }} to="/">
            Halo home
          </Link>
          <Link className="btn btn-ink" to="/book/mara">
            Public book link
          </Link>
        </div>
      </div>

      <div className="day-board">
        {demoAppointments.map((appt) => {
          const service = serviceById(appt.serviceId)
          return (
            <article key={appt.id} className="appt rise">
              <time>{appt.startsAt}</time>
              <div>
                <strong>{appt.client}</strong>
                <span>
                  {service?.name} · {service?.durationMin} min
                </span>
              </div>
              <div className={`status is-${appt.status}`}>{appt.status}</div>
            </article>
          )
        })}
      </div>

      {localBookings.length > 0 && (
        <>
          <p className="section-kicker" style={{ marginTop: '2.5rem' }}>
            From the demo book link
          </p>
          <div className="day-board">
            {localBookings.map((b) => {
              const service = serviceById(b.serviceId)
              return (
                <article key={b.id} className="appt">
                  <time>{b.slot}</time>
                  <div>
                    <strong>{b.name}</strong>
                    <span>
                      {service?.name} · {b.dayLabel} · {b.phone}
                    </span>
                  </div>
                  <div className="status">new</div>
                </article>
              )
            })}
          </div>
        </>
      )}

      <p className="empty-note">
        Prototype board — no sync yet. Real Halo would push confirmations here and text clients
        the night before.
      </p>
    </div>
  )
}
