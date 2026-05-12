import { useState } from 'react'
import { ThumbsUp, ThumbsDown, RefreshCw } from 'lucide-react'

const AGENT_STYLES = {
  faq:        { label: 'FAQ Agent',   color: '#6366f1', bg: 'rgba(99,102,241,0.1)',  dot: '#6366f1' },
  order:      { label: 'Order Agent', color: '#059669', bg: 'rgba(16,185,129,0.1)',  dot: '#10b981' },
  returns:    { label: 'Returns',     color: '#d97706', bg: 'rgba(245,158,11,0.1)',  dot: '#f59e0b' },
  escalation: { label: 'Escalated',   color: '#dc2626', bg: 'rgba(239,68,68,0.1)',   dot: '#ef4444' },
  chitchat:   { label: 'Chitchat',    color: '#475569', bg: 'rgba(100,116,139,0.1)', dot: '#64748b' },
  cache:      { label: 'Cached',      color: '#2563eb', bg: 'rgba(59,130,246,0.1)',  dot: '#3b82f6' },
}

export default function MessageBubble({ message, onFeedback }) {
  const [feedback, setFeedback] = useState(0)
  const isUser = message.role === 'user'
  const s = AGENT_STYLES[message.agentType] || AGENT_STYLES.faq

  const handleFeedback = (val) => {
    if (feedback !== 0 || !message.messageId) return
    setFeedback(val)
    onFeedback(message.messageId, val)
  }

  if (isUser) {
    return (
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '0.8rem' }}>
        <div style={{
          background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
          color: 'white', borderRadius: '1.25rem 1.25rem 0.25rem 1.25rem',
          padding: '0.75rem 1.1rem', maxWidth: '70%',
          fontSize: '0.9rem', lineHeight: 1.6,
          boxShadow: '0 4px 16px rgba(99,102,241,0.28)',
        }}>
          {message.content}
        </div>
      </div>
    )
  }

  return (
    <div style={{ marginBottom: '1rem', maxWidth: '78%' }}>
      {/* Agent badge row */}
      {message.agentType && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: '0.3rem' }}>
          <div style={{ width: 6, height: 6, borderRadius: '50%', background: s.dot, boxShadow: `0 0 6px ${s.dot}` }} />
          <span style={{ fontSize: '0.7rem', fontWeight: 700, color: s.color, letterSpacing: '0.06em', textTransform: 'uppercase' }}>
            {s.label}
          </span>
        </div>
      )}

      {/* Bubble */}
      <div className={`glass${message.streaming ? ' stream-cursor' : ''}`} style={{
        borderRadius: '0.25rem 1.25rem 1.25rem 1.25rem',
        padding: '0.85rem 1.1rem',
        fontSize: '0.88rem', lineHeight: 1.7, color: '#1e293b',
        whiteSpace: 'pre-wrap',
      }}>
        {message.content}
      </div>

      {/* Retry badge */}
      {message.retryAttempted && message.rewrittenQuery && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: 5, marginTop: '0.35rem',
          background: 'rgba(245,158,11,0.08)', borderRadius: 8,
          padding: '0.3rem 0.7rem', width: 'fit-content',
          fontSize: '0.72rem', color: '#92400e',
        }}>
          <RefreshCw size={11} />
          <span>Rewritten: <em>"{message.rewrittenQuery}"</em></span>
        </div>
      )}

      {/* Feedback */}
      {!message.streaming && message.messageId && message.agentType !== 'escalation' && (
        <div style={{ display: 'flex', gap: 3, marginTop: '0.35rem' }}>
          {[
            { val: 1,  Icon: ThumbsUp,   active: 'rgba(16,185,129,0.15)', activeColor: '#059669', inactiveColor: '#94a3b8' },
            { val: -1, Icon: ThumbsDown, active: 'rgba(239,68,68,0.12)',  activeColor: '#dc2626', inactiveColor: '#94a3b8' },
          ].map(({ val, Icon, active, activeColor, inactiveColor }) => (
            <button key={val} onClick={() => handleFeedback(val)} style={{
              border: '1px solid',
              borderColor: feedback === val ? activeColor : 'rgba(148,163,184,0.35)',
              background: feedback === val ? active : 'rgba(248,250,252,0.8)',
              cursor: feedback !== 0 ? 'default' : 'pointer',
              borderRadius: 6, padding: '4px 8px', transition: 'all 0.15s',
              color: feedback === val ? activeColor : inactiveColor,
              display: 'flex', alignItems: 'center', gap: 3,
              fontSize: '0.7rem', fontWeight: 500,
            }}>
              <Icon size={12} />
              {val === 1 ? 'Helpful' : 'Not helpful'}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
