import React, { useEffect, useState } from 'react'
import { apiRequest } from '../utils/api'
import { useNavigationStore } from '../store/navigationStore'
import { ArrowLeft, Edit2, FileDown, FileJson, CheckCircle, AlertOctagon, Activity } from 'lucide-react'

interface VersionItem {
  id: string
  version: string
  created_at: string
  completeness_score: number
  risk_classification: string
  confidence_score: number
  card_data: {
    purpose: string
    scope: string
    prompt_info: string
    operations: string
    data_access: string
    decision_authority: string
    human_oversight: string
    incident_contact: string
    known_limitations: string[]
    data_sources: string[]
    tool_inventory: Array<{
      name: string
      description: string
      permissions: string[]
      impact_level: string
    }>
    llm_info: {
      provider: string
      model_name: string
      version: string
      temperature: number
    }
  }
}

interface RegulationMapping {
  id: string
  framework: string
  status: string
  details: {
    description: string
    checks: Array<{
      id: string
      title: string
      description: string
      status: string
      evidence: string
      remediation?: string
    }>
  }
}

export const CardDetails: React.FC = () => {
  const { selectedCardId, navigateTo } = useNavigationStore()
  const [card, setCard] = useState<any>(null)
  const [versions, setVersions] = useState<VersionItem[]>([])
  const [selectedVersion, setSelectedVersion] = useState<VersionItem | null>(null)
  const [mappings, setMappings] = useState<RegulationMapping[]>([])
  const [loading, setLoading] = useState(true)
  
  // For version comparison
  const [v1Compare, setV1Compare] = useState('')
  const [v2Compare, setV2Compare] = useState('')

  // ── Pure helper (no state deps) ──────────────────────────────────────────
  const generateInMemoryMappings = (data: any, _completeness: number): RegulationMapping[] => {
    return [
      {
        id: '1',
        framework: 'EU AI Act Art.13',
        status: data.llm_info?.model_name ? 'compliant' : 'non-compliant',
        details: {
          description: 'Transparency and provision of information to users for high-risk AI systems.',
          checks: [
            { id: 'EU-13.1', title: 'Provider Information', description: 'Model type and version details.', status: data.llm_info?.model_name ? 'compliant' : 'non-compliant', evidence: `Model provider: ${data.llm_info?.provider}` },
            { id: 'EU-13.2', title: 'Intended Use Definition', description: 'Purpose and application bounds are declared.', status: data.purpose ? 'compliant' : 'non-compliant', evidence: `Purpose: ${data.purpose}` },
            { id: 'EU-13.3', title: 'Known Limitations Log', description: 'Documentation of limitations and errors.', status: data.known_limitations?.length ? 'compliant' : 'non-compliant', evidence: `Limitations count: ${data.known_limitations?.length}` }
          ]
        }
      },
      {
        id: '2',
        framework: 'NIST AI RMF Govern',
        status: data.decision_authority ? 'compliant' : 'non-compliant',
        details: {
          description: 'NIST Risk Management framework - System governance policies.',
          checks: [
            { id: 'NIST-GOV-1.1', title: 'Decision Boundaries', description: 'Level of delegation and autonomy limits.', status: data.decision_authority ? 'compliant' : 'non-compliant', evidence: `Autonomy level: ${data.decision_authority}` },
            { id: 'NIST-GOV-1.2', title: 'Human Oversight control', description: 'Human approval mechanisms log.', status: data.human_oversight ? 'compliant' : 'non-compliant', evidence: `Oversight: ${data.human_oversight}` },
            { id: 'NIST-GOV-1.3', title: 'Emergency rollbacks', description: 'Support contact for safety events.', status: data.incident_contact ? 'compliant' : 'non-compliant', evidence: `Incident email: ${data.incident_contact}` }
          ]
        }
      },
      {
        id: '3',
        framework: 'ISO/IEC 42001',
        status: data.tool_inventory?.length ? 'compliant' : 'non-compliant',
        details: {
          description: 'Standard for Artificial Intelligence management systems.',
          checks: [
            { id: 'ISO-42001-A.1', title: 'Capabilities Register', description: 'Tools and system extensions.', status: data.tool_inventory?.length ? 'compliant' : 'non-compliant', evidence: `Tools registered: ${data.tool_inventory?.length}` },
            { id: 'ISO-42001-A.2', title: 'Data Resources Curation', description: 'Catalogs databases accessed.', status: data.data_sources?.length ? 'compliant' : 'non-compliant', evidence: `Data sources: ${data.data_sources?.join(', ')}` },
            { id: 'ISO-42001-A.3', title: 'Robustness Metrics', status: 'compliant', description: 'Documentation of risk profiles.', evidence: 'Risk level is documented.' }
          ]
        }
      }
    ]
  }

  const resolveMappings = (versionId: string, cardSnapshot: any, versionsSnapshot: VersionItem[]) => {
    const current = versionsSnapshot.find(v => v.id === versionId)
    if (!current) return
    if (cardSnapshot && cardSnapshot.current_version_id === versionId && cardSnapshot.current_version?.regulation_mappings) {
      setMappings(cardSnapshot.current_version.regulation_mappings)
    } else {
      setMappings(generateInMemoryMappings(current.card_data, current.completeness_score))
    }
  }

  // ── Data loading ──────────────────────────────────────────────────────────
  useEffect(() => {
    if (!selectedCardId) return
    const load = async () => {
      setLoading(true)
      try {
        const cardResp = await apiRequest(`/cards/${selectedCardId}`)
        if (!cardResp.ok) throw new Error('Card details not found')
        const cardData = await cardResp.json()
        setCard(cardData)

        const versionsResp = await apiRequest(`/cards/${selectedCardId}/versions`)
        if (versionsResp.ok) {
          const versionsData = await versionsResp.json()
          setVersions(versionsData)
          const current = versionsData.find((v: any) => v.id === cardData.current_version_id)
          if (current) {
            setSelectedVersion(current)
            setV2Compare(current.version)
            if (versionsData.length > 1) setV1Compare(versionsData[versionsData.length - 1].version)
            resolveMappings(current.id, cardData, versionsData)
          }
        }
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [selectedCardId])

  const handleVersionChange = (versionStr: string) => {
    const found = versions.find(v => v.version === versionStr)
    if (found) {
      setSelectedVersion(found)
      resolveMappings(found.id, card, versions)
    }
  }

  const handleExportPDF = async () => {
    if (!card || !selectedVersion) return
    try {
      const response = await apiRequest(`/cards/${card.id}/export/pdf?version=${selectedVersion.version}`)
      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `compliance_card_${card.name.replace(/\s+/g, '_')}_${selectedVersion.version}.pdf`
        document.body.appendChild(a)
        a.click()
        a.remove()
      }
    } catch (err) {
      console.error(err)
    }
  }

  const handleExportJSON = async () => {
    if (!card || !selectedVersion) return
    try {
      const response = await apiRequest(`/cards/${card.id}/export/json?version=${selectedVersion.version}`)
      if (response.ok) {
        const data = await response.json()
        const jsonString = `data:text/json;charset=utf-8,${encodeURIComponent(JSON.stringify(data, null, 2))}`
        const a = document.createElement('a')
        a.href = jsonString
        a.download = `compliance_card_${card.name.replace(/\s+/g, '_')}_${selectedVersion.version}.json`
        document.body.appendChild(a)
        a.click()
        a.remove()
      }
    } catch (err) {
      console.error(err)
    }
  }

  const handleCompare = () => {
    if (v1Compare && v2Compare) {
      navigateTo('diff', card.id, { cardId: card.id, v1: v1Compare, v2: v2Compare })
    }
  }

  if (loading) {
    return <div className="p-10 text-center text-xs text-brand-muted">Loading card specifications...</div>
  }

  if (!card || !selectedVersion) {
    return <div className="p-10 text-center text-xs text-brand-muted">Compliance card data unavailable.</div>
  }

  const d = selectedVersion.card_data

  return (
    <div className="space-y-6">
      {/* Top Banner actions */}
      <div className="flex flex-col sm:flex-row gap-4 justify-between items-start sm:items-center border-b border-border-dark pb-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigateTo('dashboard')}
            className="p-1.5 rounded border border-border-dark hover:bg-border-dark text-brand-secondary hover:text-brand-primary transition-all cursor-pointer"
          >
            <ArrowLeft size={16} />
          </button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold tracking-tight text-brand-primary">{card.name}</h1>
              <select
                value={selectedVersion.version}
                onChange={(e) => handleVersionChange(e.target.value)}
                className="bg-[#1e1e1e] border border-border-dark text-xs text-brand-accent font-bold px-2 py-1 rounded cursor-pointer"
              >
                {versions.map(v => (
                  <option key={v.id} value={v.version}>v{v.version}</option>
                ))}
              </select>
            </div>
            <p className="text-xs text-brand-secondary mt-0.5">
              Unique ID: {card.id} | Audited on: {new Date(selectedVersion.created_at).toLocaleString()}
            </p>
          </div>
        </div>

        <div className="flex gap-2">
          <button
            onClick={handleExportJSON}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-border-dark hover:bg-border-dark text-xs font-semibold text-brand-secondary hover:text-brand-primary transition-all cursor-pointer"
          >
            <FileJson size={14} />
            Export JSON
          </button>
          <button
            onClick={handleExportPDF}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-border-dark hover:bg-border-dark text-xs font-semibold text-brand-secondary hover:text-brand-primary transition-all cursor-pointer"
          >
            <FileDown size={14} />
            Export PDF
          </button>
          <button
            onClick={() => navigateTo('editor', card.id)}
            className="flex items-center gap-1.5 bg-[#333] hover:bg-brand-accent hover:text-bg-dark border border-border-dark hover:border-transparent px-3 py-2 rounded-lg text-xs font-bold transition-all cursor-pointer"
          >
            <Edit2 size={14} />
            Generate Revision
          </button>
        </div>
      </div>

      {/* Grid: Stats scorecard summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-card-dark border border-border-dark rounded-xl p-5 shadow">
          <span className="text-[10px] uppercase font-bold tracking-wider text-brand-muted block mb-1">Completeness Score</span>
          <div className="flex items-baseline gap-2">
            <span className={`text-2xl font-bold ${selectedVersion.completeness_score >= 80 ? 'text-brand-accent' : 'text-brand-critical'}`}>
              {selectedVersion.completeness_score}%
            </span>
            <div className="w-16 bg-border-dark h-1.5 rounded overflow-hidden">
              <div
                className={`h-full ${selectedVersion.completeness_score >= 80 ? 'bg-brand-accent' : 'bg-brand-critical'}`}
                style={{ width: `${selectedVersion.completeness_score}%` }}
              ></div>
            </div>
          </div>
        </div>

        <div className="bg-card-dark border border-border-dark rounded-xl p-5 shadow">
          <span className="text-[10px] uppercase font-bold tracking-wider text-brand-muted block mb-1">Risk Profile</span>
          <span className={`text-2xl font-bold uppercase ${['high', 'critical'].includes(selectedVersion.risk_classification) ? 'text-brand-critical' : 'text-brand-primary'}`}>
            {selectedVersion.risk_classification}
          </span>
        </div>

        <div className="bg-card-dark border border-border-dark rounded-xl p-5 shadow">
          <span className="text-[10px] uppercase font-bold tracking-wider text-brand-muted block mb-1">Confidence Factor</span>
          <span className="text-2xl font-bold text-brand-highlight">
            {Math.round(selectedVersion.confidence_score * 100)}%
          </span>
        </div>

        <div className="bg-card-dark border border-border-dark rounded-xl p-5 shadow">
          <span className="text-[10px] uppercase font-bold tracking-wider text-brand-muted block mb-1">Foundation Model</span>
          <span className="text-sm font-bold text-brand-primary truncate block mt-1">
            {d.llm_info?.provider} ({d.llm_info?.model_name})
          </span>
        </div>
      </div>

      {/* Main content sections grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Columns 1 & 2: Compliance Card specifications */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Card: Executive specs */}
          <div className="bg-card-dark border border-border-dark rounded-xl p-6 shadow space-y-5">
            <h3 className="text-sm font-bold uppercase tracking-wider text-brand-accent border-b border-border-dark pb-2">
              1. Deployment Specifications & Intent
            </h3>
            
            <div className="space-y-4">
              <div>
                <h4 className="text-xs font-bold text-brand-secondary mb-1">General Purpose</h4>
                <p className="text-xs text-brand-primary leading-relaxed bg-[#202020] border border-border-dark p-3 rounded-lg">
                  {d.purpose}
                </p>
              </div>
              
              <div>
                <h4 className="text-xs font-bold text-brand-secondary mb-1">Allowed Boundaries & Scope</h4>
                <p className="text-xs text-brand-primary leading-relaxed bg-[#202020] border border-border-dark p-3 rounded-lg">
                  {d.scope}
                </p>
              </div>

              <div>
                <h4 className="text-xs font-bold text-brand-secondary mb-1">Operational Instructions & Rules</h4>
                <p className="text-xs text-brand-primary leading-relaxed bg-[#202020] border border-border-dark p-3 rounded-lg">
                  {d.operations}
                </p>
              </div>
            </div>
          </div>

          {/* Card: Access, Authority & Resources */}
          <div className="bg-card-dark border border-border-dark rounded-xl p-6 shadow space-y-5">
            <h3 className="text-sm font-bold uppercase tracking-wider text-brand-accent border-b border-border-dark pb-2">
              2. Data Access & Decision Authority
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-4">
                <div>
                  <h4 className="text-xs font-bold text-brand-secondary mb-1">Data Access Scopes</h4>
                  <p className="text-xs text-brand-primary leading-relaxed bg-[#202020] border border-border-dark p-3 rounded-lg min-h-[80px]">
                    {d.data_access}
                  </p>
                </div>
                
                <div>
                  <h4 className="text-xs font-bold text-brand-secondary mb-1">Decision Delegation</h4>
                  <p className="text-xs text-brand-primary leading-relaxed bg-[#202020] border border-border-dark p-3 rounded-lg min-h-[80px]">
                    {d.decision_authority}
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <h4 className="text-xs font-bold text-brand-secondary mb-1">Human In The Loop Controls</h4>
                  <p className="text-xs text-brand-primary leading-relaxed bg-[#202020] border border-border-dark p-3 rounded-lg min-h-[80px]">
                    {d.human_oversight}
                  </p>
                </div>

                <div>
                  <h4 className="text-xs font-bold text-brand-secondary mb-1">Incident Contact Escalation</h4>
                  <p className="text-xs text-brand-primary leading-relaxed bg-[#202020] border border-border-dark p-3 rounded-lg min-h-[80px] font-mono">
                    {d.incident_contact}
                  </p>
                </div>
              </div>
            </div>
            
            <div>
              <h4 className="text-xs font-bold text-brand-secondary mb-1.5">Catalogs Data Sources</h4>
              <div className="flex flex-wrap gap-2">
                {d.data_sources?.map((s, idx) => (
                  <span key={idx} className="bg-border-dark px-2.5 py-1 rounded text-xs font-medium border border-[#505050]">
                    {s}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Card: Tool Register */}
          <div className="bg-card-dark border border-border-dark rounded-xl shadow overflow-hidden">
            <div className="p-6 border-b border-border-dark">
              <h3 className="text-sm font-bold uppercase tracking-wider text-brand-accent">
                3. Registered Tools Inventory
              </h3>
            </div>
            {d.tool_inventory?.length === 0 ? (
              <div className="p-6 text-center text-xs text-brand-muted">No external tools registered.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-[#222] border-b border-border-dark text-brand-muted uppercase font-bold">
                      <th className="py-2.5 px-5">Tool</th>
                      <th className="py-2.5 px-5">Capabilities & Description</th>
                      <th className="py-2.5 px-5">Impact</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border-dark">
                    {d.tool_inventory?.map((tool, idx) => (
                      <tr key={idx} className="hover:bg-[#2A2A2A]">
                        <td className="py-3 px-5 font-mono text-brand-accent">{tool.name}</td>
                        <td className="py-3 px-5 text-brand-secondary leading-relaxed">{tool.description}</td>
                        <td className="py-3 px-5">
                          <span className={`inline-block px-1.5 py-0.5 text-[9px] uppercase font-bold rounded ${
                            tool.impact_level === 'high' ? 'bg-brand-critical/10 text-brand-critical border border-brand-critical/20' :
                            tool.impact_level === 'medium' ? 'bg-brand-accent/10 text-brand-accent border border-brand-accent/20' :
                            'bg-border-dark text-brand-secondary'
                          }`}>
                            {tool.impact_level}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

        </div>

        {/* Column 3: Regulation checks & Version History */}
        <div className="space-y-6">
          
          {/* Card: Regulation checklists */}
          <div className="bg-card-dark border border-border-dark rounded-xl p-5 shadow space-y-4">
            <h3 className="text-sm font-bold uppercase tracking-wider text-brand-accent border-b border-border-dark pb-2">
              Regulation Mappings
            </h3>
            
            <div className="space-y-5">
              {mappings.map((m, idx) => {
                const isCompliant = m.status === 'compliant'
                return (
                  <div key={idx} className="space-y-2 border-b border-border-dark/60 pb-3 last:border-0 last:pb-0">
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-xs">{m.framework}</span>
                      <span className={`inline-flex items-center gap-1 text-[10px] uppercase font-bold px-2 py-0.5 rounded border ${
                        isCompliant ? 'bg-brand-accent/10 text-brand-accent border-brand-accent/30' : 'bg-brand-critical/10 text-brand-critical border-brand-critical/30'
                      }`}>
                        {m.status}
                      </span>
                    </div>
                    
                    <p className="text-[10px] text-brand-muted italic leading-relaxed">
                      {m.details?.description}
                    </p>
                    
                    <div className="space-y-1.5 mt-2">
                      {m.details?.checks?.map((c: any, cIdx: number) => {
                        const checkPassed = c.status === 'compliant'
                        return (
                          <div key={cIdx} className="bg-[#202020] border border-border-dark/40 rounded p-2 text-[10px] space-y-1">
                            <div className="flex items-center justify-between">
                              <span className="font-semibold text-brand-secondary">{c.id}: {c.title}</span>
                              {checkPassed ? (
                                <CheckCircle size={10} className="text-brand-accent" />
                              ) : (
                                <AlertOctagon size={10} className="text-brand-critical" />
                              )}
                            </div>
                            <p className="text-[9px] text-brand-muted leading-relaxed">{c.description}</p>
                            {!checkPassed && c.remediation && (
                              <p className="text-[9px] text-brand-highlight leading-relaxed pt-0.5">
                                <span className="font-bold text-brand-critical">Remedy:</span> {c.remediation}
                              </p>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Card: Version comparison timeline */}
          {versions.length > 1 && (
            <div className="bg-card-dark border border-border-dark rounded-xl p-5 shadow space-y-4">
              <h3 className="text-sm font-bold uppercase tracking-wider text-brand-accent border-b border-border-dark pb-2">
                Audit Diff Comparison
              </h3>
              
              <p className="text-xs text-brand-muted">
                Compare changes and trigger automatic reassessment reviews.
              </p>
              
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[9px] uppercase font-bold text-brand-muted mb-1">V1 (Base)</label>
                    <select
                      value={v1Compare}
                      onChange={(e) => setV1Compare(e.target.value)}
                      className="w-full bg-[#1e1e1e] border border-border-dark text-xs text-brand-primary py-1.5 px-2 rounded cursor-pointer outline-none focus:border-brand-accent"
                    >
                      {versions.map(v => (
                        <option key={v.id} value={v.version}>v{v.version}</option>
                      ))}
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-[9px] uppercase font-bold text-brand-muted mb-1">V2 (Target)</label>
                    <select
                      value={v2Compare}
                      onChange={(e) => setV2Compare(e.target.value)}
                      className="w-full bg-[#1e1e1e] border border-border-dark text-xs text-brand-primary py-1.5 px-2 rounded cursor-pointer outline-none focus:border-brand-accent"
                    >
                      {versions.map(v => (
                        <option key={v.id} value={v.version}>v{v.version}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <button
                  onClick={handleCompare}
                  disabled={v1Compare === v2Compare}
                  className="w-full bg-[#333] border border-border-dark text-brand-primary hover:bg-brand-accent hover:text-bg-dark py-2 rounded-lg text-xs font-bold transition-all disabled:opacity-50 flex items-center justify-center gap-1.5 cursor-pointer"
                >
                  <Activity size={12} />
                  Calculate Visual Diff
                </button>
              </div>
            </div>
          )}

        </div>

      </div>
    </div>
  )
}
