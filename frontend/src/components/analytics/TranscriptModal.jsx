import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, RefreshCw, Bot, User, AlertTriangle } from 'lucide-react'

const AGENT_COLORS = { faq: '#6366f1', order: '#10b981', returns: '#f59e0b', escalation: '#ef4444', chitchat: '#64748b', cache: '#3b82f6' }

export default function TranscriptModal({ session, onClose }) {
  const [data, setData] = useState(null)

  useEffect(() => {
    if (!session) return
    setData(null)
    fetch(`/analytics/session/${session.session_id}`)
      .then(r => r.json())
      .then(setData)
      .catch(() => {})
  }, [session])

  useEffect(() => {
    const handler = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  if (!session) return null

  return (
    <AnimatePresence>
      <motion.div
        key="backdrop"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,0.45)', backdropFilter: 'blur(4px)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1.5rem' }}
      >
        <motion.div
          key="modal"
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          transition={{ type: 'spring', damping: 25 }}
          onClick={e => e.stopPropagation()}
          className="glass-heavy"
          style={{ borderRadius: '1.5rem', width: '100%', maxWidth: 760, maxHeight: '85vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}
        >
          {/* Header */}
          <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid rgba(255,255,255,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#0f172a' }}>Session Transcript</div>
              <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: 2 }}>
                {session.customer_email} · {new Date(session.started_at).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })}
              </div>
            </div>
            <button onClick={onClose} style={{ border: 'none', background: 'rgba(0,0,0,0.06)', borderRadius: 8, padding: '6px 8px', cursor: 'pointer', display: 'flex', color: '#64748b' }}>
              <X size={16} />
            </button>
          </div>

          {/* Body */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 240px', flex: 1, overflow: 'hidden' }}>
            {/* Transcript */}
            <div style={{ overflowY: 'auto', padding: '1.25rem 1.5rem', borderRight: '1px solid rgba(255,255,255,0.5)' }}>
              {!data ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {[...Array(4)].map((_, i) => (
                    <div key={i} style={{ height: 52, background: 'rgba(0,0,0,0.04)', borderRadius: 12, animation: 'pulse 1.5s infinite' }} />
                  ))}
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                  {data.messages?.map(msg => (
                    <div key={msg.message_id}>
                      {/* User message */}
                      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '0.5rem' }}>
                        <div style={{ display: 'flex', alignItems: 'flex-end', gap: 6, maxWidth: '70%' }}>
                          <div style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', color: 'white', borderRadius: '1rem 1rem 0.2rem 1rem', padding: '0.65rem 0.9rem', fontSize: '0.85rem', lineHeight: 1.55 }}>
                            {msg.user_message}
                          </div>
                          <User size={14} color="#94a3b8" style={{ flexShrink: 0, marginBottom: 4 }} />
                        </div>
                      </div>

                      {/* Retry badge */}
                      {msg.retry_attempted && msg.rewritten_query && (
                        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '0.4rem' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 5, background: 'rgba(245,158,11,0.1)', borderRadius: 99, padding: '3px 10px', fontSize: '0.7rem', color: '#92400e', fontWeight: 500 }}>
                            <RefreshCw size={10} /> Rewritten: "{msg.rewritten_query}"
                          </div>
                        </div>
                      )}

                      {/* Agent response */}
                      {msg.agent_response && (
                        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 6, maxWidth: '78%' }}>
                          <div style={{ width: 26, height: 26, borderRadius: 8, background: `${AGENT_COLORS[msg.agent_type] || '#6366f1'}18`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: 2 }}>
                            <Bot size={13} color={AGENT_COLORS[msg.agent_type] || '#6366f1'} />
                          </div>
                          <div>
                            <div style={{ fontSize: '0.65rem', fontWeight: 700, color: AGENT_COLORS[msg.agent_type] || '#6366f1', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 3 }}>
                              {msg.agent_type}
                            </div>
                            <div className="glass" style={{ borderRadius: '0.2rem 1rem 1rem 1rem', padding: '0.65rem 0.9rem', fontSize: '0.84rem', lineHeight: 1.6, color: '#1e293b', whiteSpace: 'pre-wrap' }}>
                              {msg.agent_response}
                            </div>
                            <div style={{ display: 'flex', gap: '0.75rem', marginTop: 4, fontSize: '0.68rem', color: '#94a3b8' }}>
                              {msg.confidence_score != null && <span>conf: <strong style={{ color: '#475569' }}>{(msg.confidence_score*100).toFixed(0)}%</strong></span>}
                              {msg.rag_best_score != null && <span>rag: <strong style={{ color: '#475569' }}>{(msg.rag_best_score*100).toFixed(0)}%</strong></span>}
                              {msg.response_time_ms && <span><strong style={{ color: '#475569' }}>{msg.response_time_ms}ms</strong></span>}
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Escalation marker */}
                      {msg.escalated && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '0.5rem 0.75rem', background: 'rgba(239,68,68,0.07)', borderRadius: 8, marginTop: '0.5rem', fontSize: '0.75rem', color: '#dc2626', fontWeight: 500 }}>
                          <AlertTriangle size={13} /> Escalated — {msg.escalation_reason}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Metadata */}
            <div style={{ overflowY: 'auto', padding: '1.25rem' }}>
              <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.75rem' }}>Session Info</div>
              {[
                { label: 'Status',     value: session.escalated ? '🔴 Escalated' : '🟢 Resolved' },
                { label: 'Messages',   value: session.total_messages || '—' },
                { label: 'Cache hits', value: session.cache_hits || 0 },
                { label: 'Confidence', value: session.avg_confidence ? `${(session.avg_confidence*100).toFixed(0)}%` : '—' },
                { label: 'Started',    value: session.started_at ? new Date(session.started_at).toLocaleTimeString() : '—' },
                { label: 'Ended',      value: session.ended_at ? new Date(session.ended_at).toLocaleTimeString() : 'Active' },
              ].map(({ label, value }) => (
                <div key={label} style={{ marginBottom: '0.65rem' }}>
                  <div style={{ fontSize: '0.68rem', color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase', marginBottom: 2 }}>{label}</div>
                  <div style={{ fontSize: '0.84rem', color: '#1e293b', fontWeight: 600 }}>{value}</div>
                </div>
              ))}
              {session.agents_triggered?.length > 0 && (
                <div style={{ marginTop: '0.75rem' }}>
                  <div style={{ fontSize: '0.68rem', color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase', marginBottom: 5 }}>Agents Used</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                    {session.agents_triggered.map(a => (
                      <span key={a} style={{ fontSize: '0.68rem', fontWeight: 700, padding: '2px 8px', borderRadius: 99, background: `${AGENT_COLORS[a] || '#6366f1'}15`, color: AGENT_COLORS[a] || '#6366f1', textTransform: 'capitalize' }}>
                        {a}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}
