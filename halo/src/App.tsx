import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { Landing } from './pages/Landing'
import { Book } from './pages/Book'
import { Dashboard } from './pages/Dashboard'
import './App.css'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/book/:slug" element={<Book />} />
        <Route path="/app" element={<Dashboard />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
