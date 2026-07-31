import React, { useEffect, useState } from 'react'
import { apiRequest } from '../utils/api'
import { useNavigationStore } from '../store/navigationStore'
import { ArrowLeft, AlertTriangle, Check, Plus, Minus, Settings } from 'lucide-react'

interface DiffField {
  label: string
  v1: string
  v2: string
  changed: boolean
}

interface DiffResponse {
  v1: string
  v2: string
  diff: {
    has_changes: boolean
    reassessment_required: boolean
    reassessment_reasons: string[]
    changes: Record<string, any>
  }
}

export const CardDiff: React.FC = () => {
  const { diffParams, navigateTo } = useNavigationStore()
  const [diffData, setDiffData] = useState<DiffResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchDiff = async () => {
      if (!diffParams) return
      setLoading(true)
      try {
        const response = await apiRequest(
          `/cards/${diffParams.cardId}/diff?v1=${diffParams.v1}&v2=${diffParams.v2}`
        )
        if (response.ok) {
          const data = await response.json()
          setDiffData(data)
        }
      } catch (err) {
        console.error('Failed to load diff:', err)
      } finally {
        setLoading(false)
      }
    }

    if (diffParams) {
      fetchDiff()
    }
  }, [diffParams])

  if (loading) {
    return <div className="p-10 text-center text-xs text-brand-muted">Calculating visual changes...</div>
  }

  if (!diffData || !diffParams) {
    return <div className="p-10 text-center text-xs text-brand-muted">Diff parameters not found.</div>
  }

  const { v1, v2, diff } = diffData
  const changes = diff.changes

  // Split changes
  const textChanges = Object.entries(changes).filter(
    ([key]) => !['llm_info', 'tools', 'data_sources'].includes(key)
  ) as [string, DiffField][]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4 border-b border-border-dark pb-4">
        <button
          onClick={() => navigateTo('details', diffParams.cardId)}
          className="p-1.5 rounded border border-border-dark hover:bg-border-dark text-brand-secondary hover:text-brand-primary transition-all cursor-pointer"
        >
          <ArrowLeft size={16} />
        </button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-brand-primary">Audit Version Diff</h1>
          <p className="text-sm text-brand-secondary">
            Analyzing changes between version <span className="text-brand-accent font-semibold">v{v1}</span> and <span className="text-brand-accent font-semibold">v{v2}</span>
          </p>
        </div>
      </div>

      {/* Compliance Reassessment Callout */}
      {diff.reassessment_required ? (
        <div className="p-5 rounded-xl bg-card-dark border border-brand-accent/50 shadow flex items-start gap-4">
          <AlertTriangle className="text-brand-accent shrink-0 mt-1" size={20} />
          <div className="space-y-2">
            <h3 className="text-sm font-bold text-brand-primary uppercase tracking-wider">
              Automatic Compliance Reassessment Triggered
            </h3>
            <p className="text-xs text-brand-secondary leading-relaxed">
              Critical attributes (model parameters, tool registry permissions, or risk profiles) have evolved. 
              Under Article 13/ISO 42001 regulations, this deployment must undergo auditor sign-off.
            </p>
            <div className="flex flex-wrap gap-2 pt-1">
              {diff.reassessment_reasons.map((reason, idx) => (
                <span
                  key={idx}
                  className="bg-brand-accent/10 border border-brand-accent/30 text-brand-accent px-2 py-0.5 rounded text-[10px] uppercase font-bold"
                >
                  {reason}
                </span>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="p-4 rounded-xl bg-[#202020] border border-border-dark text-brand-secondary text-xs flex items-center gap-2">
          <Check size={16} className="text-brand-accent" />
          No critical reassessment triggers found. Documentation remains under existing certification bounds.
        </div>
      )}

      {/* Changes list */}
      <div className="space-y-6">
        
        {/* Simple text fields */}
        {textChanges.length > 0 && (
          <div className="bg-card-dark border border-border-dark rounded-xl p-6 shadow space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-brand-secondary border-b border-border-dark pb-2">
              Text Attribute Mutations
            </h3>
            
            <div className="space-y-4 divide-y divide-border-dark/60">
              {textChanges.map(([key, field], _idx) => (
                <div key={key} className={`pt-4 first:pt-0`}>
                  <h4 className="text-xs font-bold text-brand-primary mb-2">{field.label}</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <div className="bg-[#1C1C1C] border border-border-dark/40 rounded-lg p-3">
                      <span className="text-[9px] uppercase font-bold text-brand-muted block mb-1">Version v{v1}</span>
                      <p className="text-brand-secondary leading-relaxed">{field.v1 || '—'}</p>
                    </div>
                    <div className="bg-[#2A2215] border border-brand-accent/20 rounded-lg p-3">
                      <span className="text-[9px] uppercase font-bold text-brand-accent block mb-1">Version v{v2} (Updated)</span>
                      <p className="text-brand-primary leading-relaxed font-medium">{field.v2 || '—'}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* LLM Info Diff */}
        {changes.llm_info && (
          <div className="bg-card-dark border border-border-dark rounded-xl p-6 shadow space-y-4">
            <div className="flex items-center gap-2 text-brand-accent border-b border-border-dark pb-2">
              <Settings size={16} />
              <h3 className="text-xs font-bold uppercase tracking-wider text-brand-secondary">
                Model Parameter & Foundation Diff
              </h3>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="text-brand-muted uppercase font-bold border-b border-border-dark">
                    <th className="py-2">Parameter</th>
                    <th className="py-2">V{v1} (Original)</th>
                    <th className="py-2">V{v2} (New)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border-dark">
                  {Object.entries(changes.llm_info.details).map(([param, detail]: any) => (
                    <tr key={param} className="hover:bg-[#2A2A2A]">
                      <td className="py-3 font-semibold capitalize text-brand-secondary">{param.replace('_', ' ')}</td>
                      <td className="py-3 text-brand-muted font-mono">{detail.v1}</td>
                      <td className="py-3 text-brand-accent font-mono font-bold">{detail.v2}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tools Diff */}
        {changes.tools && (
          <div className="bg-card-dark border border-border-dark rounded-xl p-6 shadow space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-brand-secondary border-b border-border-dark pb-2">
              Tool Registry Mutations
            </h3>
            
            <div className="space-y-4">
              {/* Added tools */}
              {changes.tools.added.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-brand-accent flex items-center gap-1.5">
                    <Plus size={14} className="bg-brand-accent text-bg-dark rounded-full p-0.5" />
                    Tools Registered (+{changes.tools.added.length})
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {changes.tools.added.map((t: any, idx: number) => (
                      <div key={idx} className="bg-[#202920] border border-[#2d4d2d] rounded-lg p-3 text-xs">
                        <span className="font-mono font-bold text-brand-primary block">{t.name}</span>
                        <p className="text-brand-secondary mt-1 leading-relaxed text-[11px]">{t.description}</p>
                        <span className="inline-block mt-2 px-1.5 py-0.5 text-[8px] font-bold bg-[#1C2A1C] border border-[#3e683e] text-brand-primary uppercase rounded">
                          Impact: {t.impact_level}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Removed tools */}
              {changes.tools.removed.length > 0 && (
                <div className="space-y-2 pt-2">
                  <h4 className="text-xs font-bold text-brand-critical flex items-center gap-1.5">
                    <Minus size={14} className="bg-brand-critical text-brand-primary rounded-full p-0.5" />
                    Tools Revoked (-{changes.tools.removed.length})
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {changes.tools.removed.map((t: any, idx: number) => (
                      <div key={idx} className="bg-[#2D1F1F] border border-[#522929] rounded-lg p-3 text-xs opacity-70">
                        <span className="font-mono font-bold text-brand-secondary line-through block">{t.name}</span>
                        <p className="text-brand-muted mt-1 leading-relaxed text-[11px]">{t.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Data Sources Diff */}
        {changes.data_sources && (
          <div className="bg-card-dark border border-border-dark rounded-xl p-6 shadow space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-brand-secondary border-b border-border-dark pb-2">
              Data Catalog Changes
            </h3>
            <div className="space-y-3 text-xs">
              {changes.data_sources.added.length > 0 && (
                <div>
                  <span className="font-bold text-brand-accent block mb-1.5">Sources Added</span>
                  <div className="flex flex-wrap gap-2">
                    {changes.data_sources.added.map((s: string, idx: number) => (
                      <span key={idx} className="bg-[#202920] border border-[#2d4d2d] px-2 py-1 rounded text-xs font-medium">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {changes.data_sources.removed.length > 0 && (
                <div className="pt-2">
                  <span className="font-bold text-brand-critical block mb-1.5">Sources Revoked</span>
                  <div className="flex flex-wrap gap-2">
                    {changes.data_sources.removed.map((s: string, idx: number) => (
                      <span key={idx} className="bg-[#2D1F1F] border border-[#522929] px-2 py-1 rounded text-xs font-medium line-through text-brand-secondary">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

      </div>
    </div>
  )
}
