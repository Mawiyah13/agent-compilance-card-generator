import React from 'react'
import { LayoutDashboard, FilePlus2, ShieldAlert, LogOut, User } from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import { useNavigationStore } from '../store/navigationStore'

export const Sidebar: React.FC = () => {
  const { user, logout } = useAuthStore()
  const { currentPage, navigateTo } = useNavigationStore()

  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, roles: ['admin', 'auditor', 'developer'] },
    { id: 'editor', label: 'Compliance Generator', icon: FilePlus2, roles: ['admin', 'developer'] },
    { id: 'audit', label: 'Audit Logs', icon: ShieldAlert, roles: ['admin', 'auditor'] }
  ]

  const filteredMenu = menuItems.filter(item => user && item.roles.includes(user.role))

  return (
    <aside className="w-64 bg-sidebar-dark border-r border-border-dark flex flex-col justify-between h-screen fixed left-0 top-0 text-brand-primary z-10">
      <div>
        {/* Brand */}
        <div className="h-16 flex items-center px-6 border-b border-border-dark">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-brand-accent flex items-center justify-center text-xs font-bold text-bg-dark">AC</div>
            <span className="font-bold tracking-wider text-sm">AI AGENT GOVERN</span>
          </div>
        </div>

        {/* Menu */}
        <nav className="p-4 space-y-1">
          {filteredMenu.map((item) => {
            const Icon = item.icon
            const isActive = currentPage === item.id || (item.id === 'editor' && currentPage === 'details')
            return (
              <button
                key={item.id}
                onClick={() => navigateTo(item.id as any)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-brand-accent text-bg-dark font-semibold'
                    : 'text-brand-secondary hover:text-brand-primary hover:bg-[#2A2A2A]'
                }`}
              >
                <Icon size={18} />
                {item.label}
              </button>
            )
          })}
        </nav>
      </div>

      {/* User profile section */}
      <div className="p-4 border-t border-border-dark space-y-3 bg-[#1A1A1A]">
        {user && (
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-card-dark border border-border-dark flex items-center justify-center text-brand-secondary">
              <User size={18} />
            </div>
            <div className="overflow-hidden">
              <p className="text-xs font-medium truncate">{user.email}</p>
              <span className="inline-block mt-0.5 px-2 py-0.5 text-[10px] uppercase font-bold rounded bg-border-dark text-brand-secondary border border-border-dark">
                {user.role}
              </span>
            </div>
          </div>
        )}
        <button
          onClick={() => {
            logout()
            navigateTo('login')
          }}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 text-xs font-medium rounded-lg text-brand-secondary hover:text-brand-primary hover:bg-brand-critical/20 hover:border-brand-critical/40 border border-transparent transition-all"
        >
          <LogOut size={14} />
          Sign Out
        </button>
      </div>
    </aside>
  )
}
