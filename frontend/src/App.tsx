import React from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAuthStore } from './store/authStore'
import { useNavigationStore } from './store/navigationStore'
import { Sidebar } from './components/Sidebar'
import { Login } from './pages/Login'
import { Dashboard } from './pages/Dashboard'
import { CardEditor } from './pages/CardEditor'
import { CardDetails } from './pages/CardDetails'
import { CardDiff } from './pages/CardDiff'
import { AuditLogs } from './pages/AuditLogs'

const queryClient = new QueryClient()

const AppContent: React.FC = () => {
  const { isAuthenticated } = useAuthStore()
  const { currentPage } = useNavigationStore()

  if (!isAuthenticated) {
    return <Login />
  }

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard />
      case 'editor':
        return <CardEditor />
      case 'details':
        return <CardDetails />
      case 'diff':
        return <CardDiff />
      case 'audit':
        return <AuditLogs />
      case 'login':
        return <Login />
      default:
        return <Dashboard />
    }
  }

  return (
    <div className="min-h-screen bg-bg-dark text-brand-primary flex">
      {/* Sidebar navigation */}
      <Sidebar />

      {/* Main viewport */}
      <main className="flex-1 pl-64 min-h-screen bg-bg-dark">
        <div className="p-8 max-w-7xl mx-auto">
          {renderPage()}
        </div>
      </main>
    </div>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  )
}

export default App
