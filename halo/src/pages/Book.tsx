import { useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  loadBookings,
  openDays,
  saveBooking,
  serviceById,
  services,
  stylist,
} from '../data'

type Step = 'service' | 'when' | 'details' | 'done'

export function Book() {
  const { slug } = useParams()
  const days = useMemo(() => openDays(), [])
  const [step, setStep] = useState<Step>('service')
  const [serviceId, setServiceId] = useState<string | null>(null)
  const [dayLabel, setDayLabel] = useState<string | null>(null)
  const [slot, setSlot] = useState<string | null>(null)
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')

  const active = slug === stylist.slug ? stylist : stylist
  const service = serviceId ? serviceById(serviceId) : undefined
  const selectedDay = days.find((d) => d.label === dayLabel)

  function onConfirm(e: FormEvent) {
    e.preventDefault()
    if (!serviceId || !dayLabel || !slot || !name.trim() || !phone.trim()) return
    saveBooking({
      id: crypto.randomUUID(),
      serviceId,
      dayLabel,
      slot,
      name: name.trim(),
      phone: phone.trim(),
      createdAt: new Date().toISOString(),
    })
    setStep('done')
  }

  if (step === 'done' && service) {
    return (
      <div className="book-shell">
        <aside className="book-visual">
          <img src={active.photo} alt="" />
          <div className="book-visual-copy">
            <Link to="/" className="brand">
              Halo
            </Link>
            <h1>{active.name}</h1>
            <p>
              {active.role} · {active.city}
            </p>
          </div>
        </aside>
        <main className="book-panel">
          <div className="confirm-state rise">
            <p className="step-label">You’re booked</p>
            <h2>See you {dayLabel}</h2>
            <p>
              {service.name} at {slot}. {active.name} has your number if anything changes.
            </p>
            <div className="cta-row" style={{ marginTop: '0.5rem' }}>
              <Link className="btn btn-ink" to="/app">
                View stylist board
              </Link>
              <Link className="btn btn-ghost" to="/" style={{ color: 'var(--ink)', boxShadow: 'inset 0 0 0 1.5px var(--line)' }}>
                Back to Halo
              </Link>
            </div>
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="book-shell">
      <aside className="book-visual">
        <img src={active.photo} alt="" />
        <div className="book-visual-copy">
          <Link to="/" className="brand">
            Halo
          </Link>
          <h1 className="rise">{active.name}</h1>
          <p className="rise rise-delay-1">
            {active.bio} · {active.city}
          </p>
        </div>
      </aside>

      <main className="book-panel">
        {step === 'service' && (
          <div className="rise">
            <p className="step-label">Step 1 · Service</p>
            <div className="service-list">
              {services.map((s) => (
                <button
                  key={s.id}
                  type="button"
                  className={`choice ${serviceId === s.id ? 'is-selected' : ''}`}
                  onClick={() => setServiceId(s.id)}
                >
                  <strong>{s.name}</strong>
                  <em>{s.blurb}</em>
                  <div className="meta">
                    ${s.price} · {s.durationMin} min
                  </div>
                </button>
              ))}
            </div>
            <button
              type="button"
              className="btn btn-ink"
              disabled={!serviceId}
              onClick={() => setStep('when')}
            >
              Continue
            </button>
          </div>
        )}

        {step === 'when' && (
          <div className="rise">
            <p className="step-label">Step 2 · When</p>
            <div className="day-list">
              {days.map((d) => (
                <button
                  key={d.label}
                  type="button"
                  className={`choice ${dayLabel === d.label ? 'is-selected' : ''}`}
                  onClick={() => {
                    setDayLabel(d.label)
                    setSlot(null)
                  }}
                >
                  <strong>{d.label}</strong>
                </button>
              ))}
            </div>
            {selectedDay && (
              <div className="slot-list">
                {selectedDay.slots.map((t) => (
                  <button
                    key={t}
                    type="button"
                    className={`choice ${slot === t ? 'is-selected' : ''}`}
                    onClick={() => setSlot(t)}
                  >
                    <strong>{t}</strong>
                  </button>
                ))}
              </div>
            )}
            <div className="cta-row">
              <button type="button" className="btn btn-ghost" style={{ color: 'var(--ink)', boxShadow: 'inset 0 0 0 1.5px var(--line)' }} onClick={() => setStep('service')}>
                Back
              </button>
              <button
                type="button"
                className="btn btn-ink"
                disabled={!dayLabel || !slot}
                onClick={() => setStep('details')}
              >
                Continue
              </button>
            </div>
          </div>
        )}

        {step === 'details' && service && (
          <form className="rise" onSubmit={onConfirm}>
            <p className="step-label">Step 3 · Your info</p>
            <p className="summary">
              {service.name}
              <span>
                {dayLabel} · {slot} · ${service.price}
              </span>
            </p>
            <div className="form-grid">
              <div className="field">
                <label htmlFor="name">Name</label>
                <input
                  id="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  autoComplete="name"
                  required
                />
              </div>
              <div className="field">
                <label htmlFor="phone">Mobile</label>
                <input
                  id="phone"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  autoComplete="tel"
                  inputMode="tel"
                  required
                />
              </div>
            </div>
            <div className="cta-row">
              <button type="button" className="btn btn-ghost" style={{ color: 'var(--ink)', boxShadow: 'inset 0 0 0 1.5px var(--line)' }} onClick={() => setStep('when')}>
                Back
              </button>
              <button type="submit" className="btn btn-ink">
                Confirm booking
              </button>
            </div>
            <p className="empty-note">
              Demo only — {loadBookings().length} booking
              {loadBookings().length === 1 ? '' : 's'} saved in this browser.
            </p>
          </form>
        )}
      </main>
    </div>
  )
}
