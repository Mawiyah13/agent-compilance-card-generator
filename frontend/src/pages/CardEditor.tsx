import React, { useEffect, useState } from 'react'
import { apiRequest } from '../utils/api'
import { useNavigationStore } from '../store/navigationStore'
import { ArrowLeft, Save, FileCode, CheckCircle2, RefreshCw } from 'lucide-react'

export const CardEditor: React.FC = () => {
  const { selectedCardId, navigateTo } = useNavigationStore()
  const [name, setName] = useState('')
  const [configText, setConfigText] = useState('')
  const [toolText, setToolText] = useState('')
  const [traceText, setTraceText] = useState('')
  
  const [configFile, setConfigFile] = useState<File | null>(null)
  const [toolFile, setToolFile] = useState<File | null>(null)
  const [traceFile, setTraceFile] = useState<File | null>(null)

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [isEditMode, setIsEditMode] = useState(false)

  useEffect(() => {
    const fetchCardDetails = async () => {
      try {
        const response = await apiRequest(`/cards/${selectedCardId}`)
        if (response.ok) {
          const data = await response.json()
          setName(data.name)
          // Set inputs placeholders
          if (data.current_version) {
            setConfigText(JSON.stringify(data.current_version.config_input || {}, null, 2))
            setToolText(JSON.stringify(data.current_version.tool_manifest_input || {}, null, 2))
            setTraceText(data.current_version.runtime_trace_input || '')
          }
        }
      } catch (err) {
        console.error('Failed to load card details:', err)
      }
    }

    if (selectedCardId) {
      setIsEditMode(true)
      fetchCardDetails()
    }
  }, [selectedCardId])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)
    setLoading(true)

    try {
      const formData = new FormData()
      formData.append('name', name)
      
      // Text inputs
      if (configText) formData.append('config_text', configText)
      if (toolText) formData.append('tool_manifest_text', toolText)
      if (traceText) formData.append('runtime_trace_text', traceText)

      // File inputs
      if (configFile) formData.append('config_file', configFile)
      if (toolFile) formData.append('tool_manifest_file', toolFile)
      if (traceFile) formData.append('runtime_trace_file', traceFile)

      const endpoint = isEditMode ? `/cards/${selectedCardId}` : '/cards'
      const method = isEditMode ? 'PUT' : 'POST'

      const response = await apiRequest(endpoint, {
        method,
        body: formData
        // Note: Headers must NOT contain Content-Type because browser sets multipart boundary
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Failed to process compliance card.')
      }

      const cardResult = await response.json()
      setSuccess(`Compliance card ${isEditMode ? 'updated' : 'created'} successfully. Version bumped to ${cardResult.current_version?.version || '1.0.0'}.`)
      
      setTimeout(() => {
        navigateTo('details', cardResult.id)
      }, 1500)

    } catch (err: any) {
      setError(err.message || 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4 border-b border-border-dark pb-4">
        <button
          onClick={() => navigateTo('dashboard')}
          className="p-1.5 rounded border border-border-dark hover:bg-border-dark text-brand-secondary hover:text-brand-primary transition-all cursor-pointer"
        >
          <ArrowLeft size={16} />
        </button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-brand-primary">
            {isEditMode ? 'Generate Compliance Revision' : 'Create Compliance Card'}
          </h1>
          <p className="text-sm text-brand-secondary">
            Provide system inputs to parse agent behavior, check completeness, and perform audits.
          </p>
        </div>
      </div>

      {/* Message blocks */}
      {error && (
        <div className="p-4 rounded-lg bg-brand-critical/10 border border-brand-critical/30 text-brand-primary text-sm">
          {error}
        </div>
      )}
      {success && (
        <div className="p-4 rounded-lg bg-[#2b2b2b] border border-brand-accent text-brand-accent text-sm flex items-center gap-2">
          <CheckCircle2 size={16} />
          {success}
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="bg-card-dark border border-border-dark rounded-xl p-6 shadow space-y-4">
          <div>
            <label className="block text-xs font-semibold text-brand-secondary uppercase tracking-wider mb-2">
              Agent Deployment Name
            </label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. FinanceAgent-V3-Production"
              className="w-full bg-[#1e1e1e] border border-border-dark rounded-lg py-2.5 px-4 text-sm text-brand-primary focus:border-brand-accent focus:ring-1 focus:ring-brand-accent outline-none transition-all"
            />
          </div>
        </div>

        {/* Inputs Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Card 1: Agent Config */}
          <div className="bg-card-dark border border-border-dark rounded-xl p-5 shadow flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 text-brand-accent mb-4">
                <FileCode size={18} />
                <h3 className="text-sm font-bold uppercase tracking-wider">Agent Config (JSON/YAML)</h3>
              </div>
              <p className="text-xs text-brand-muted mb-4">
                Declares model name, parameters, prompt files, system goals, and incident support contacts.
              </p>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-[10px] uppercase font-bold text-brand-muted mb-1.5">Upload File</label>
                  <input
                    type="file"
                    accept=".json,.yaml,.yml,.txt"
                    onChange={(e) => setConfigFile(e.target.files?.[0] || null)}
                    className="w-full text-xs text-brand-secondary bg-[#1e1e1e] border border-border-dark file:mr-4 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-border-dark file:text-brand-primary file:cursor-pointer hover:file:bg-[#505050] transition-all rounded-lg p-1"
                  />
                </div>
                
                <div>
                  <label className="block text-[10px] uppercase font-bold text-brand-muted mb-1.5">Or Paste Raw Content</label>
                  <textarea
                    value={configText}
                    onChange={(e) => setConfigText(e.target.value)}
                    placeholder='{"model": "gpt-4o", "purpose": "Financial analyzer", "contact": "finance-alerts@company.internal"}'
                    rows={8}
                    className="w-full bg-[#1e1e1e] border border-border-dark rounded-lg p-3 text-xs text-brand-primary font-mono outline-none focus:border-brand-accent transition-all resize-none"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Card 2: Tool Manifest */}
          <div className="bg-card-dark border border-border-dark rounded-xl p-5 shadow flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 text-brand-accent mb-4">
                <FileCode size={18} />
                <h3 className="text-sm font-bold uppercase tracking-wider">Tool Manifest (JSON/YAML)</h3>
              </div>
              <p className="text-xs text-brand-muted mb-4">
                Lists tool signatures, descriptions, scopes, schema arguments, and database access policies.
              </p>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-[10px] uppercase font-bold text-brand-muted mb-1.5">Upload File</label>
                  <input
                    type="file"
                    accept=".json,.yaml,.yml,.txt"
                    onChange={(e) => setToolFile(e.target.files?.[0] || null)}
                    className="w-full text-xs text-brand-secondary bg-[#1e1e1e] border border-border-dark file:mr-4 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-border-dark file:text-brand-primary file:cursor-pointer hover:file:bg-[#505050] transition-all rounded-lg p-1"
                  />
                </div>
                
                <div>
                  <label className="block text-[10px] uppercase font-bold text-brand-muted mb-1.5">Or Paste Raw Content</label>
                  <textarea
                    value={toolText}
                    onChange={(e) => setToolText(e.target.value)}
                    placeholder='{"tools": [{"name": "db_query", "description": "query SQL DB"}]}'
                    rows={8}
                    className="w-full bg-[#1e1e1e] border border-border-dark rounded-lg p-3 text-xs text-brand-primary font-mono outline-none focus:border-brand-accent transition-all resize-none"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Card 3: Runtime Trace */}
          <div className="bg-card-dark border border-border-dark rounded-xl p-5 shadow flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 text-brand-accent mb-4">
                <FileCode size={18} />
                <h3 className="text-sm font-bold uppercase tracking-wider">Runtime Trace (TXT/JSON)</h3>
              </div>
              <p className="text-xs text-brand-muted mb-4">
                Execution trace logs reflecting actual API tools used, human check confirmations, or error events.
              </p>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-[10px] uppercase font-bold text-brand-muted mb-1.5">Upload File</label>
                  <input
                    type="file"
                    accept=".json,.yaml,.yml,.txt,.log"
                    onChange={(e) => setTraceFile(e.target.files?.[0] || null)}
                    className="w-full text-xs text-brand-secondary bg-[#1e1e1e] border border-border-dark file:mr-4 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-border-dark file:text-brand-primary file:cursor-pointer hover:file:bg-[#505050] transition-all rounded-lg p-1"
                  />
                </div>
                
                <div>
                  <label className="block text-[10px] uppercase font-bold text-brand-muted mb-1.5">Or Paste Raw Content</label>
                  <textarea
                    value={traceText}
                    onChange={(e) => setTraceText(e.target.value)}
                    placeholder="[2026-07-30] Initiating financial agent... Invoked db_query... approval granted."
                    rows={8}
                    className="w-full bg-[#1e1e1e] border border-border-dark rounded-lg p-3 text-xs text-brand-primary font-mono outline-none focus:border-brand-accent transition-all resize-none"
                  />
                </div>
              </div>
            </div>
          </div>

        </div>

        {/* Submit */}
        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={() => navigateTo('dashboard')}
            className="px-5 py-2.5 rounded-lg border border-border-dark hover:bg-border-dark font-semibold text-xs text-brand-secondary hover:text-brand-primary cursor-pointer transition-all"
          >
            Cancel
          </button>
          
          <button
            type="submit"
            disabled={loading}
            className="flex items-center gap-2 bg-brand-accent hover:bg-brand-hover text-bg-dark font-bold text-xs px-5 py-2.5 rounded-lg cursor-pointer transition-all disabled:opacity-50"
          >
            {loading ? (
              <RefreshCw className="animate-spin" size={14} />
            ) : (
              <Save size={14} />
            )}
            {loading ? 'Synthesizing Compliance Profile...' : isEditMode ? 'Register New Compliance Version' : 'Compile Compliance Card'}
          </button>
        </div>
      </form>
    </div>
  )
}
