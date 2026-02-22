import { Routes, Route, NavLink, useLocation } from 'react-router-dom'
import { Box, LayoutDashboard, PlusCircle, Cpu, Settings } from 'lucide-react'
import Dashboard from './pages/Dashboard'
import NewJob from './pages/NewJob'
import JobDetail from './pages/JobDetail'
import ModelsPage from './pages/ModelsPage'
import SettingsPage from './pages/SettingsPage'
import LandingPage from './pages/LandingPage'

const NAV = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/new', label: 'New Job', icon: PlusCircle },
  { to: '/models', label: 'Models', icon: Cpu },
  { to: '/settings', label: 'Settings', icon: Settings },
]

function Sidebar() {
  return (
    <aside className="fixed left-0 top-0 bottom-0 w-64 bg-surface-light border-r border-border flex flex-col z-10">
      <NavLink to="/" className="flex items-center gap-3 px-6 py-5 border-b border-border hover:bg-surface-lighter transition-colors">
        <Box className="w-7 h-7 text-primary-400" />
        <span className="text-lg font-bold tracking-tight">CAD Builder</span>
      </NavLink>

      <nav className="flex-1 py-4 px-3 space-y-1">
        {NAV.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-primary-600/20 text-primary-300'
                  : 'text-text-muted hover:bg-surface-lighter hover:text-text'
              }`
            }
          >
            <Icon className="w-4.5 h-4.5" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="px-4 py-4 border-t border-border">
        <div className="text-xs text-text-muted">CAD Builder v0.2.0</div>
      </div>
    </aside>
  )
}

function AppShell({ children }) {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="ml-64 flex-1 p-8">{children}</main>
    </div>
  )
}

export default function App() {
  const location = useLocation()

  // Landing page renders without sidebar
  if (location.pathname === '/') {
    return <LandingPage />
  }

  return (
    <AppShell>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/new" element={<NewJob />} />
        <Route path="/jobs/:jobId" element={<JobDetail />} />
        <Route path="/models" element={<ModelsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Routes>
    </AppShell>
  )
}
