import React, { useEffect, useState } from 'react'
import { apiRequest } from '../utils/api'
import { useNavigationStore } from '../store/navigationStore'
import { Search, AlertTriangle, FileCheck, Shield, ChevronRight, FileDown, PlusCircle } from 'lucide-react'
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell, PieChart, Pie } from 'recharts'

interface CardItem {
  id: string
  name: string
  current_version_id: string | null
  created_at: string
  updated_at: string
  current_version?: {
    id: string
    version: string
    completeness_score: number
    risk_classification: string
    confidence_score: number
  }
}

export const Dashboard: React.FC = () => {
  const [cards, setCards] = useState<CardItem[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [riskFilter, setRiskFilter] = useState('all')
  const { navigateTo } = useNavigationStore()

  useEffect(() => {
    fetchCards()
  }, [])

  const fetchCards = async () => {
    try {
      const response = await apiRequest('/cards')
      if (response.ok) {
        const data = await response.json()
        setCards(data)
      } else {
        const errorData = await response.json().catch(() => null)
        console.error('Failed to load cards:', response.status, errorData)
      }
    } catch (err) {
      console.error('Failed to load cards:', err)
    } finally {
      setLoading(false)
    }
  }

  // Filter cards
  const filteredCards = cards.filter((card) => {
    const matchesSearch = card.name.toLowerCase().includes(search.toLowerCase())
    const matchesRisk =
      riskFilter === 'all' ||
      card.current_version?.risk_classification.toLowerCase() === riskFilter.toLowerCase()
    return matchesSearch && matchesRisk
  })

  // Statistics calculation
  const totalAgents = cards.length
  const avgCompleteness =
    cards.length > 0
      ? Math.round(
          cards.reduce((acc, curr) => acc + (curr.current_version?.completeness_score || 0), 0) /
            cards.length
        )
      : 0

  const riskCounts = cards.reduce(
    (acc, curr) => {
      const risk = curr.current_version?.risk_classification || 'low'
      acc[risk] = (acc[risk] || 0) + 1
      return acc
    },
    { low: 0, medium: 0, high: 0, critical: 0 } as Record<string, number>
  )

  const pieData = [
    { name: 'Low', value: riskCounts.low, color: '#B4B4B8' },
    { name: 'Medium', value: riskCounts.medium, color: '#E8C98B' },
    { name: 'High', value: riskCounts.high, color: '#C67C2E' },
    { name: 'Critical', value: riskCounts.critical, color: '#991B1B' }
  ].filter((d) => d.value > 0)

  // Default charts fallback when no data
  const barData = [
    { name: '0-25%', count: cards.filter(c => (c.current_version?.completeness_score || 0) <= 25).length },
    { name: '26-50%', count: cards.filter(c => {
      const s = c.current_version?.completeness_score || 0
      return s > 25 && s <= 50
    }).length },
    { name: '51-75%', count: cards.filter(c => {
      const s = c.current_version?.completeness_score || 0
      return s > 50 && s <= 75
    }).length },
    { name: '76-100%', count: cards.filter(c => (c.current_version?.completeness_score || 0) > 75).length }
  ]

  const handleExportPDF = async (cardId: string, cardName: string, version: string) => {
    try {
      const response = await apiRequest(`/cards/${cardId}/export/pdf?version=${version}`)
      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `compliance_card_${cardName.replace(/\s+/g, '_')}_${version}.pdf`
        document.body.appendChild(a)
        a.click()
        a.remove()
      }
    } catch (err) {
      console.error('Failed to export PDF:', err)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center border-b border-border-dark pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-brand-primary">AI Governance Center</h1>
          <p className="text-sm text-brand-secondary">
            Continuous auditing, risk classification, and compliance card verification.
          </p>
        </div>
        <button
          onClick={() => navigateTo('editor')}
          className="flex items-center gap-2 bg-brand-accent hover:bg-brand-hover text-bg-dark font-bold text-sm px-4 py-2 rounded-lg cursor-pointer transition-all"
        >
          <PlusCircle size={18} />
          Create Compliance Card
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-card-dark border border-border-dark rounded-xl p-5 shadow">
          <div className="flex items-center justify-between text-brand-muted mb-2">
            <span className="text-xs uppercase font-bold tracking-wider">Agents Monitored</span>
            <Shield size={18} className="text-brand-accent" />
          </div>
          <p className="text-3xl font-bold">{totalAgents}</p>
          <p className="text-xs text-brand-muted mt-1">Total active compliance definitions</p>
        </div>

        <div className="bg-card-dark border border-border-dark rounded-xl p-5 shadow">
          <div className="flex items-center justify-between text-brand-muted mb-2">
            <span className="text-xs uppercase font-bold tracking-wider">Average Completeness</span>
            <FileCheck size={18} className="text-brand-accent" />
          </div>
          <div className="flex items-baseline gap-2">
            <p className="text-3xl font-bold">{avgCompleteness}%</p>
            <div className="w-24 bg-border-dark h-2 rounded overflow-hidden">
              <div
                className="bg-brand-accent h-full"
                style={{ width: `${avgCompleteness}%` }}
              ></div>
            </div>
          </div>
          <p className="text-xs text-brand-muted mt-1">Metric for required documentation coverage</p>
        </div>

        <div className="bg-card-dark border border-border-dark rounded-xl p-5 shadow">
          <div className="flex items-center justify-between text-brand-muted mb-2">
            <span className="text-xs uppercase font-bold tracking-wider">High Risk Triggers</span>
            <AlertTriangle size={18} className="text-brand-critical" />
          </div>
          <p className="text-3xl font-bold text-brand-critical">
            {riskCounts.high + riskCounts.critical}
          </p>
          <p className="text-xs text-brand-muted mt-1">High & Critical classifications requiring oversight</p>
        </div>
      </div>

      {/* Charts Grid */}
      {totalAgents > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-card-dark border border-border-dark rounded-xl p-5 shadow">
            <h3 className="text-sm font-bold uppercase tracking-wider text-brand-secondary mb-4">
              Risk Profile Distribution
            </h3>
            <div className="h-60 flex items-center justify-between">
              <div className="w-1/2 h-full">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={pieData}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      innerRadius={45}
                      outerRadius={75}
                      paddingAngle={4}
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="w-1/2 space-y-2.5 pl-6">
                {pieData.map((item, index) => (
                  <div key={index} className="flex items-center gap-3 text-xs">
                    <span
                      className="w-3.5 h-3.5 rounded-full inline-block shrink-0"
                      style={{ backgroundColor: item.color }}
                    ></span>
                    <span className="font-semibold text-brand-secondary w-16">{item.name}</span>
                    <span className="font-bold text-right w-10">{item.value} ({Math.round(item.value / totalAgents * 100)}%)</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="bg-card-dark border border-border-dark rounded-xl p-5 shadow">
            <h3 className="text-sm font-bold uppercase tracking-wider text-brand-secondary mb-4">
              Completeness Score Buckets
            </h3>
            <div className="h-60">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={barData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                  <XAxis dataKey="name" stroke="#71717A" fontSize={11} tickLine={false} />
                  <YAxis stroke="#71717A" fontSize={11} tickLine={false} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#2B2B2B', borderColor: '#404040', color: '#FAFAFA' }}
                  />
                  <Bar dataKey="count" fill="#C67C2E" radius={[4, 4, 0, 0]}>
                    {barData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill="#C67C2E" />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* Main Table Panel */}
      <div className="bg-card-dark border border-border-dark rounded-xl shadow overflow-hidden">
        {/* Table Controls */}
        <div className="p-5 border-b border-border-dark flex flex-col sm:flex-row gap-4 items-center justify-between">
          <div className="relative w-full sm:w-80">
            <Search className="absolute left-3 top-3 text-brand-muted" size={16} />
            <input
              type="text"
              placeholder="Search agent deployments..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-[#1e1e1e] border border-border-dark rounded-lg py-2 pl-9 pr-4 text-xs text-brand-primary outline-none focus:border-brand-accent focus:ring-1 focus:ring-brand-accent transition-all"
            />
          </div>
          
          <div className="flex gap-2.5 w-full sm:w-auto">
            <select
              value={riskFilter}
              onChange={(e) => setRiskFilter(e.target.value)}
              className="bg-[#1e1e1e] border border-border-dark rounded-lg py-2 px-3 text-xs text-brand-primary outline-none cursor-pointer focus:border-brand-accent"
            >
              <option value="all">All Risks</option>
              <option value="low">Low Risk</option>
              <option value="medium">Medium Risk</option>
              <option value="high">High Risk</option>
              <option value="critical">Critical Risk</option>
            </select>
          </div>
        </div>

        {/* Card list */}
        {loading ? (
          <div className="p-10 text-center text-xs text-brand-muted">Loading compliance inventory...</div>
        ) : filteredCards.length === 0 ? (
          <div className="p-10 text-center text-xs text-brand-muted">No compliance cards found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-border-dark bg-[#222222] text-brand-muted uppercase font-bold tracking-wider">
                  <th className="py-3 px-6">Agent Deployment Name</th>
                  <th className="py-3 px-6">Version</th>
                  <th className="py-3 px-6">Risk Category</th>
                  <th className="py-3 px-6">Completeness Score</th>
                  <th className="py-3 px-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-dark">
                {filteredCards.map((card) => {
                  const latest = card.current_version
                  const risk = latest?.risk_classification || 'low'
                  
                  return (
                    <tr key={card.id} className="hover:bg-[#2F2F2F] transition-all">
                      <td className="py-4 px-6 font-bold text-brand-primary">
                        {card.name}
                      </td>
                      <td className="py-4 px-6 text-brand-secondary">
                        v{latest?.version || '1.0.0'}
                      </td>
                      <td className="py-4 px-6">
                        <span
                          className={`inline-block px-2 py-0.5 rounded text-[10px] uppercase font-bold border ${
                            risk === 'critical'
                              ? 'bg-brand-critical/10 text-brand-critical border-brand-critical/30'
                              : risk === 'high'
                              ? 'bg-brand-accent/10 text-brand-accent border-brand-accent/30'
                              : risk === 'medium'
                              ? 'bg-brand-highlight/10 text-brand-highlight border-brand-highlight/30'
                              : 'bg-brand-muted/10 text-brand-muted border-brand-muted/30'
                          }`}
                        >
                          {risk}
                        </span>
                      </td>
                      <td className="py-4 px-6">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold">{latest?.completeness_score || 0}%</span>
                          <div className="w-16 bg-[#1F1F1F] h-1.5 rounded overflow-hidden">
                            <div
                              className={`h-full ${
                                (latest?.completeness_score || 0) >= 80 ? 'bg-brand-accent' : 'bg-brand-critical'
                              }`}
                              style={{ width: `${latest?.completeness_score || 0}%` }}
                            ></div>
                          </div>
                        </div>
                      </td>
                      <td className="py-4 px-6 text-right space-x-2">
                        <button
                          onClick={() => handleExportPDF(card.id, card.name, latest?.version || '1.0.0')}
                          className="p-1.5 rounded border border-border-dark hover:bg-border-dark text-brand-secondary hover:text-brand-primary transition-all cursor-pointer inline-flex items-center"
                          title="Export PDF"
                        >
                          <FileDown size={14} />
                        </button>
                        <button
                          onClick={() => navigateTo('details', card.id)}
                          className="px-3 py-1.5 rounded bg-[#333333] hover:bg-brand-accent hover:text-bg-dark font-medium border border-border-dark hover:border-transparent transition-all cursor-pointer inline-flex items-center gap-1"
                        >
                          Details
                          <ChevronRight size={12} />
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
