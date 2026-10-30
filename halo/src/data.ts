export type Service = {
  id: string
  name: string
  durationMin: number
  price: number
  blurb: string
}

export type Stylist = {
  slug: string
  name: string
  role: string
  city: string
  bio: string
  photo: string
  accent: string
}

export type Appointment = {
  id: string
  client: string
  serviceId: string
  startsAt: string
  status: 'confirmed' | 'arrived' | 'done'
}

export const stylist: Stylist = {
  slug: 'mara',
  name: 'Mara Lane',
  role: 'Color & cut',
  city: 'Austin',
  bio: 'Soft lived-in color, precise cuts, no drama booking.',
  photo:
    'https://images.unsplash.com/photo-1560066984-138dadb4c035?auto=format&fit=crop&w=1600&q=80',
  accent: '#1F6B5B',
}

export const services: Service[] = [
  {
    id: 'cut',
    name: 'Signature cut',
    durationMin: 60,
    price: 75,
    blurb: 'Wash, cut, style. Your everyday shape.',
  },
  {
    id: 'color',
    name: 'Lived-in color',
    durationMin: 150,
    price: 185,
    blurb: 'Soft dimension, low maintenance grow-out.',
  },
  {
    id: 'blow',
    name: 'Blowout',
    durationMin: 45,
    price: 55,
    blurb: 'Smooth finish for events or a reset.',
  },
]

export const demoAppointments: Appointment[] = [
  {
    id: 'a1',
    client: 'Jess Ortiz',
    serviceId: 'cut',
    startsAt: '09:30',
    status: 'done',
  },
  {
    id: 'a2',
    client: 'Priya Shah',
    serviceId: 'color',
    startsAt: '11:00',
    status: 'arrived',
  },
  {
    id: 'a3',
    client: 'Elena Brooks',
    serviceId: 'blow',
    startsAt: '14:30',
    status: 'confirmed',
  },
  {
    id: 'a4',
    client: 'Sam Rivera',
    serviceId: 'cut',
    startsAt: '16:00',
    status: 'confirmed',
  },
]

export function serviceById(id: string) {
  return services.find((s) => s.id === id)
}

/** Next 7 days of open slots (demo — no real calendar backend). */
export function openDays(count = 7): { date: Date; label: string; slots: string[] }[] {
  const days: { date: Date; label: string; slots: string[] }[] = []
  const start = new Date()
  start.setHours(0, 0, 0, 0)

  for (let i = 1; i <= count + 3 && days.length < count; i++) {
    const d = new Date(start)
    d.setDate(start.getDate() + i)
    if (d.getDay() === 0) continue // closed Sundays
    const label = d.toLocaleDateString(undefined, {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
    })
    const slots =
      d.getDay() === 6
        ? ['10:00', '11:30', '13:00']
        : ['09:30', '11:00', '13:30', '15:00', '16:30']
    days.push({ date: d, label, slots })
  }
  return days
}

const BOOKINGS_KEY = 'halo-demo-bookings'

export type Booking = {
  id: string
  serviceId: string
  dayLabel: string
  slot: string
  name: string
  phone: string
  createdAt: string
}

export function loadBookings(): Booking[] {
  try {
    const raw = localStorage.getItem(BOOKINGS_KEY)
    return raw ? (JSON.parse(raw) as Booking[]) : []
  } catch {
    return []
  }
}

export function saveBooking(booking: Booking) {
  const next = [booking, ...loadBookings()]
  localStorage.setItem(BOOKINGS_KEY, JSON.stringify(next))
  return next
}
