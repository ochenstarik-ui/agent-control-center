import { NavLink, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Chat from './pages/Chat'
import Runs from './pages/Runs'
import Memory from './pages/Memory'

export default function App() {
  return (
    <div className="app">
      <nav className="sidebar">
        <h1>Agent Control Center</h1>
        <NavLink to="/">Dashboard</NavLink>
        <NavLink to="/chat">Chat</NavLink>
        <NavLink to="/runs">Runs</NavLink>
        <NavLink to="/memory">Memory</NavLink>
      </nav>
      <main>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/runs" element={<Runs />} />
          <Route path="/memory" element={<Memory />} />
        </Routes>
      </main>
    </div>
  )
}
