import { useState } from 'react'
import { motion } from 'framer-motion'
import { Search, Filter, ChevronLeft, ChevronRight, FileText } from 'lucide-react'

const PAGE_SIZE = 10

export default function SessionsTable({ sessions, onSelect }) {
  const [search, setSearch]             = useState('')
  const [escalatedFilter, setFilter]    = useState('all')
  const [page, setPage]                 = useState(1)

  const filtered = (sessions || []).filter(s => {
    const matchEmail = !search || s.customer_email?.toLowerCase().includes(search.toLowerCase())
    const esc        = s.live_escalated ?? s.escalated
    const matchEsc   = escalatedFilter === 'all' || (escalatedFilter === 'yes' ? esc : !esc)
    return matchEmail && matchEsc
  })

  const total     = filtered.length
  const pages     = Math.max(1, Math.ceil(total / PAGE_SIZE))
  const paginated = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  const fmt = iso => iso ? new Date(iso).toLocaleString('en-IN', { dateStyle: 'short', timeStyle: 'short' }) : '—'

  return (
    <div className="glass" style={{ borderRadius: '1.25rem', overflow: 'hidden' }}>
      {/* Header */}
      <div style={{ padding: '1.1rem 1.25rem', borderBottom: '1px solid rgba(255,255,255,0.6)', display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
        <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#1e293b', flex: 1 }}>Sessions ({total})</span>
        <div style={{ position: 'relative' }}>
          <Search size={13} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }} />
          <input value={search} onChange={e => { setSearch(e.target.value); setPage(1) }} placeholder="Search email…" className="input-glass" style={{ paddingLeft: '2rem', width: 180, fontSize: '0.78rem', padding: '0.45rem 0.75rem 0.45rem 2rem' }} />
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <Filter size={13} color="#94a3b8" />
          <select value={escalatedFilter} onChange={e => { setFilter(e.target.value); setPage(1) }} className="input-glass" style={{ width: 130, fontSize: '0.78rem', padding: '0.45rem 0.75rem' }}>
            <option value="all">All sessions</option>
            <option value="yes">Escalated</option>
            <option value="no">Not escalated</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid rgba(0,0,0,0.05)' }}>
              {['Email', 'Started', 'Messages', 'Avg Confidence', 'Tokens', 'Cost', 'Status', ''].map(h => (
                <th key={h} style={{ padding: '0.65rem 1rem', textAlign: 'left', fontSize: '0.7rem', fontWeight: 700, color: '#94a3b8', letterSpacing: '0.06em', textTransform: 'uppercase', whiteSpace: 'nowrap' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paginated.length > 0 ? paginated.map((s, i) => {
              const msgCount   = s.live_message_count ?? s.total_messages ?? 0
              const avgConf    = s.live_avg_confidence ?? s.avg_confidence ?? null
              const escalated  = s.live_escalated ?? s.escalated
              const tokens     = s.live_total_tokens ?? 0
              const cost       = s.live_est_cost_usd ?? 0

              return (
                <tr key={s.session_id} style={{ borderBottom: '1px solid rgba(0,0,0,0.04)' }}>
                  <td style={{ padding: '0.75rem 1rem', fontSize: '0.82rem', color: '#1e293b', fontWeight: 500 }}>
                    {s.customer_email || '—'}
                  </td>
                  <td style={{ padding: '0.75rem 1rem', fontSize: '0.78rem', color: '#64748b', whiteSpace: 'nowrap' }}>
                    {fmt(s.started_at)}
                  </td>
                  <td style={{ padding: '0.75rem 1rem', fontSize: '0.82rem', color: '#475569', fontWeight: 600, textAlign: 'center' }}>
                    {msgCount}
                  </td>
                  <td style={{ padding: '0.75rem 1rem' }}>
                    {avgConf != null ? (
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <div style={{ flex: 1, height: 5, background: 'rgba(0,0,0,0.07)', borderRadius: 99, overflow: 'hidden', maxWidth: 55 }}>
                          <div style={{ width: `${Math.round(avgConf * 100)}%`, height: '100%', background: avgConf > 0.75 ? '#10b981' : avgConf > 0.5 ? '#f59e0b' : '#ef4444', borderRadius: 99 }} />
                        </div>
                        <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>{Math.round(avgConf * 100)}%</span>
                      </div>
                    ) : <span style={{ fontSize: '0.75rem', color: '#cbd5e1' }}>—</span>}
                  </td>
                  <td style={{ padding: '0.75rem 1rem', fontSize: '0.78rem', fontWeight: 600, color: '#7c3aed' }}>
                    {tokens > 0 ? tokens.toLocaleString() : '—'}
                  </td>
                  <td style={{ padding: '0.75rem 1rem', fontSize: '0.78rem', fontWeight: 600, color: '#059669' }}>
                    {cost > 0 ? `$${cost.toFixed(5)}` : '—'}
                  </td>
                  <td style={{ padding: '0.75rem 1rem' }}>
                    <span style={{ fontSize: '0.7rem', fontWeight: 700, padding: '3px 10px', borderRadius: 99, background: escalated ? 'rgba(239,68,68,0.1)' : 'rgba(16,185,129,0.1)', color: escalated ? '#dc2626' : '#059669' }}>
                      {escalated ? 'Escalated' : 'Resolved'}
                    </span>
                  </td>
                  <td style={{ padding: '0.75rem 1rem' }}>
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => onSelect(s)}
                      style={{ border: '1px solid rgba(99,102,241,0.3)', background: 'rgba(99,102,241,0.06)', color: '#6366f1', borderRadius: 8, padding: '0.3rem 0.7rem', fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4, whiteSpace: 'nowrap' }}
                    >
                      <FileText size={12} /> Details
                    </motion.button>
                  </td>
                </tr>
              )
            }) : (
              <tr>
                <td colSpan={8} style={{ padding: '2.5rem', textAlign: 'center', color: '#cbd5e1', fontSize: '0.85rem' }}>No sessions found</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {pages > 1 && (
        <div style={{ padding: '0.75rem 1.25rem', borderTop: '1px solid rgba(0,0,0,0.05)', display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 6 }}>
          <button onClick={() => setPage(p => Math.max(1, p-1))} disabled={page === 1} style={{ border: 'none', background: 'transparent', cursor: page === 1 ? 'default' : 'pointer', color: page === 1 ? '#cbd5e1' : '#6366f1', display: 'flex', alignItems: 'center' }}><ChevronLeft size={18} /></button>
          {[...Array(Math.min(5, pages))].map((_, i) => {
            const p = i + 1
            return <button key={p} onClick={() => setPage(p)} style={{ width: 28, height: 28, borderRadius: 6, border: 'none', cursor: 'pointer', fontSize: '0.78rem', fontWeight: 600, background: page === p ? 'linear-gradient(135deg, #6366f1, #8b5cf6)' : 'transparent', color: page === p ? 'white' : '#64748b', transition: 'all 0.15s' }}>{p}</button>
          })}
          <button onClick={() => setPage(p => Math.min(pages, p+1))} disabled={page === pages} style={{ border: 'none', background: 'transparent', cursor: page === pages ? 'default' : 'pointer', color: page === pages ? '#cbd5e1' : '#6366f1', display: 'flex', alignItems: 'center' }}><ChevronRight size={18} /></button>
        </div>
      )}
    </div>
  )
}
