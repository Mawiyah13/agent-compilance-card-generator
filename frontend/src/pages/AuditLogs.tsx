import React, { useEffect, useState } from 'react'
import { apiRequest } from '../utils/api'
import { ShieldCheck } from 'lucide-react'

interface AuditItem {
  id: string
  user_id: string
  action: string
  details: Record<string, any>
  ip_address: string | null
  timestamp: string
}

export const AuditLogs: React.FC = () => {
  const [logs, setLogs] = useState<AuditItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchLogs()
  }, [])

  const fetchLogs = async () => {
    try {
      const response = await apiRequest('/audit/')
      if (response.ok) {
        const data = await response.json()
        setLogs(data)
      }
    } catch (err) {
      console.error('Failed to load audit logs:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-border-dark pb-4">
        <h1 className="text-2xl font-bold tracking-tight text-brand-primary flex items-center gap-2">
          <ShieldCheck className="text-brand-accent" size={24} />
          System Audit Trail
        </h1>
        <p className="text-sm text-brand-secondary">
          Immutable logs logging all user activities, card generations, exports, and version overrides.
        </p>
      </div>

      {/* Logs Table */}
      <div className="bg-card-dark border border-border-dark rounded-xl shadow overflow-hidden">
        {loading ? (
          <div className="p-10 text-center text-xs text-brand-muted">Loading audit records...</div>
        ) : logs.length === 0 ? (
          <div className="p-10 text-center text-xs text-brand-muted">No audit trail records found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-[#222] border-b border-border-dark text-brand-muted uppercase font-bold tracking-wider">
                  <th className="py-3 px-6">Timestamp (UTC)</th>
                  <th className="py-3 px-6">Account ID</th>
                  <th className="py-3 px-6">Event Action</th>
                  <th className="py-3 px-6">IP Details</th>
                  <th className="py-3 px-6">Audit Metadata</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-dark font-mono text-[11px]">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-[#2A2A2A] transition-all">
                    <td className="py-3.5 px-6 text-brand-secondary">
                      {new Date(log.timestamp).toISOString().replace('T', ' ').substring(0, 19)}
                    </td>
                    <td className="py-3.5 px-6 text-brand-muted truncate max-w-[120px]" title={log.user_id}>
                      {log.user_id}
                    </td>
                    <td className="py-3.5 px-6 font-bold text-brand-primary">
                      <span className="bg-[#1e1e1e] border border-border-dark px-2 py-0.5 rounded">
                        {log.action}
                      </span>
                    </td>
                    <td className="py-3.5 px-6 text-brand-muted">
                      {log.ip_address || '127.0.0.1'}
                    </td>
                    <td className="py-3.5 px-6 text-brand-secondary text-[10px] max-w-xs truncate" title={JSON.stringify(log.details)}>
                      {JSON.stringify(log.details)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
