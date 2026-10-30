import { Link } from 'react-router-dom'

const HERO =
  'https://images.unsplash.com/photo-1521590832167-7bcbfaa6381d?auto=format&fit=crop&w=2000&q=80'

export function Landing() {
  return (
    <div>
      <nav className="site-nav" aria-label="Primary">
        <Link to="/" className="brand">
          Halo
        </Link>
        <div className="nav-links">
          <Link to="/book/mara">Demo booking</Link>
          <Link to="/app" className="nav-cta">
            Stylist view
          </Link>
        </div>
      </nav>

      <header className="hero">
        <div className="hero-media" aria-hidden="true">
          <img src={HERO} alt="" />
        </div>
        <div className="hero-copy">
          <p className="hero-brand rise">Halo</p>
          <h1 className="hero-headline rise rise-delay-1">
            Booking for one chair — not a salon operating system.
          </h1>
          <p className="hero-support rise rise-delay-2">
            Clients pick a service, grab a time, and show up. You stay in the chair.
          </p>
          <div className="cta-row rise rise-delay-3">
            <Link className="btn btn-primary" to="/book/mara">
              Try the booking page
            </Link>
            <Link className="btn btn-ghost" to="/app">
              See today’s board
            </Link>
          </div>
        </div>
      </header>

      <section className="section" id="why">
        <div className="section-inner">
          <p className="section-kicker">Why this exists</p>
          <h2 className="section-title">GlossGenius is great. Most solos don’t need all of it.</h2>
          <p className="section-support">
            Standard runs about $24–28/month before tips and processing. Halo is the thin layer:
            a gorgeous public link, deposits later, reminders later — priced for one person with a
            chair rental.
          </p>

          <div className="compare">
            <article className="compare-panel">
              <h3>Halo</h3>
              <div className="price-line">
                <strong>$12</strong>
                <span>/mo target</span>
              </div>
              <p>Built for booth renters and independent stylists.</p>
              <ul>
                <li>
                  <span />
                  Branded booking page clients actually want to use
                </li>
                <li>
                  <span />
                  Phone-first day board
                </li>
                <li>
                  <span />
                  Deposit + text reminders on the roadmap
                </li>
              </ul>
            </article>
            <article className="compare-panel is-muted">
              <h3>Full beauty OS</h3>
              <div className="price-line">
                <strong>$28+</strong>
                <span>/mo typical</span>
              </div>
              <p>Worth it when you need POS, inventory, payroll, and a team.</p>
              <ul>
                <li>
                  <span />
                  Multi-staff calendars & commissions
                </li>
                <li>
                  <span />
                  Retail, gift cards, memberships
                </li>
                <li>
                  <span />
                  AI receptionist & marketing suites
                </li>
              </ul>
            </article>
          </div>
        </div>
      </section>

      <section className="section" id="how">
        <div className="section-inner">
          <p className="section-kicker">How it works</p>
          <h2 className="section-title">Three taps for them. A quiet day for you.</h2>
          <p className="section-support">
            No client accounts. No app download. Just a link you can text, post, or pin in your bio.
          </p>
          <div className="flow">
            <div className="flow-step">
              <em>01</em>
              <p>Client chooses cut, color, or blowout from your menu.</p>
            </div>
            <div className="flow-step">
              <em>02</em>
              <p>They grab an open slot and leave a name + number.</p>
            </div>
            <div className="flow-step">
              <em>03</em>
              <p>It lands on your today board — ready when they walk in.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="cta-band">
        <div>
          <h2>Put it in front of your stylist.</h2>
          <p>
            This build is a clickable prototype. Next step is a real calendar, Stripe deposits, and
            reminder texts — if she actually wants it.
          </p>
        </div>
        <Link className="btn btn-primary" to="/book/mara">
          Open Mara’s book link
        </Link>
      </section>

      <footer className="site-footer">
        <span>Halo · demo product</span>
        <span>Not affiliated with GlossGenius</span>
      </footer>
    </div>
  )
}
