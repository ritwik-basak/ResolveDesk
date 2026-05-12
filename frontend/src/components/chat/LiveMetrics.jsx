import { useState, useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { TrendingUp, Users, MessageSquare, Zap, Clock, Activity } from 'lucide-react'

const INTENT_COLORS = {
  faq: '#6366f1', order: '#10b981', returns: '#f59e0b',
  chitchat: '#64748b', escalation: '#ef4444', cache: '#3b82f6', unknown: '#94a3b8',
}

function useCountUp(target, duration = 900) {
  const [val, setVal] = useState(0)
  useEffect(() => {
    if (!target) { setVal(0); return }
    let rafId, startTs = null
    const tick = ts => {
      if (!startTs) startTs = ts
      const p = Math.min((ts - startTs) / duration, 1)
      const e = 1 - Math.pow(1 - p, 2.5)  // ease-out 2.5: visible counting until ~80% done
      setVal(target * e)
      if (p < 1) rafId = requestAnimationFrame(tick)
    }
    rafId = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(rafId)
  }, [target, duration])
  return val
}

function Stat({ icon: Icon, label, rawValue = 0, format = v => Math.round(v), color = '#6366f1', sub, tooltip }) {
  const [show, setShow] = useState(false)
  const animated = useCountUp(rawValue)
  return (
    <div className="metric-card" style={{ display: 'flex', alignItems: 'flex-start', gap: 10, position: 'relative' }}
      onMouseEnter={() => tooltip && setShow(true)}
      onMouseLeave={() => setShow(false)}
    >
      <div style={{ width: 34, height: 34, borderRadius: 10, background: `${color}18`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
        <Icon size={16} color={color} />
      </div>
      <div style={{ minWidth: 0 }}>
        <div style={{ fontSize: '0.7rem', color: '#94a3b8', fontWeight: 600, letterSpacing: '0.04em', textTransform: 'uppercase', marginBottom: 1 }}>{label}</div>
        <div style={{ fontSize: '1.15rem', fontWeight: 800, color: '#0f172a', letterSpacing: '-0.02em' }}>{format(animated)}</div>
        {sub && <div style={{ fontSize: '0.68rem', color: '#94a3b8' }}>{sub}</div>}
      </div>
      {show && tooltip && (
        <div style={{
          position: 'absolute', bottom: '110%', left: 0,
          background: '#1e293b', color: '#cbd5e1', fontSize: '0.69rem', lineHeight: 1.6,
          padding: '0.55rem 0.8rem', borderRadius: 8, width: 210, zIndex: 100,
          boxShadow: '0 8px 24px rgba(0,0,0,0.25)', pointerEvents: 'none',
        }}>
          {tooltip}
        </div>
      )}
    </div>
  )
}

function CircleMetric({ label, pct, color, size = 96, tooltip, hideLabel = false }) {
  const [showTip, setShowTip] = useState(false)
  const [displayPct, setDisplayPct] = useState(0)
  const animated = useCountUp(pct || 0, 1000)

  useEffect(() => {
    const t = setTimeout(() => setDisplayPct(pct || 0), 60)
    return () => clearTimeout(t)
  }, [pct])

  const r    = size * 0.36
  const circ = 2 * Math.PI * r
  const val  = Math.min(Math.max(displayPct, 0), 100)
  const dash = circ * (1 - val / 100)

  return (
    <div
      className="metric-card"
      style={{ position: 'relative', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 5, padding: '0.9rem 0.5rem', cursor: 'default' }}
      onMouseEnter={() => setShowTip(true)}
      onMouseLeave={() => setShowTip(false)}
    >
      <svg width={size} height={size} style={{ overflow: 'visible' }}>
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="rgba(0,0,0,0.07)" strokeWidth={7} />
        <circle
          cx={size/2} cy={size/2} r={r}
          fill="none" stroke={color} strokeWidth={7}
          strokeDasharray={circ} strokeDashoffset={dash}
          strokeLinecap="round"
          transform={`rotate(-90 ${size/2} ${size/2})`}
          style={{ filter: `drop-shadow(0 0 4px ${color})`, transition: 'stroke-dashoffset 1.6s cubic-bezier(0.25, 0.8, 0.25, 1)' }}
        />
        <text x={size/2} y={size/2 + 6} textAnchor="middle" style={{ fontSize: '0.95rem', fontWeight: 800, fill: '#0f172a' }}>
          {Math.round(animated)}%
        </text>
      </svg>
      {!hideLabel && (
        <div style={{ fontSize: '0.65rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{label}</div>
      )}

      {/* Tooltip */}
      {showTip && tooltip && (
        <div style={{
          position: 'absolute', bottom: 'calc(100% + 8px)', left: '50%', transform: 'translateX(-50%)',
          background: 'rgba(15,23,42,0.92)', color: '#e2e8f0',
          borderRadius: 10, padding: '0.55rem 0.8rem',
          fontSize: '0.72rem', lineHeight: 1.55,
          width: 200, textAlign: 'center',
          zIndex: 100, backdropFilter: 'blur(12px)',
          boxShadow: '0 8px 24px rgba(0,0,0,0.25)',
          pointerEvents: 'none',
        }}>
          {tooltip}
          <div style={{
            position: 'absolute', top: '100%', left: '50%', transform: 'translateX(-50%)',
            borderLeft: '6px solid transparent', borderRight: '6px solid transparent',
            borderTop: '6px solid rgba(15,23,42,0.92)',
          }} />
        </div>
      )}
    </div>
  )
}

export default function LiveMetrics() {
  const [metrics, setMetrics] = useState(null)
  const [lastUpdated, setLastUpdated] = useState(null)

  const fetch_metrics = async () => {
    try {
      const res = await fetch('/metrics/live')
      const data = await res.json()
      setMetrics(data)
      setLastUpdated(new Date())
    } catch (_) {}
  }

  useEffect(() => {
    fetch_metrics()
    const interval = setInterval(fetch_metrics, 5000)
    return () => clearInterval(interval)
  }, [])

  const pct = (n) => `${(n * 100).toFixed(1)}%`
  const ms = (n) => n > 0 ? `${n}ms` : '—'

  const intents = metrics?.intent_breakdown || {}
  const totalIntent = Object.values(intents).reduce((a, b) => a + b, 0) || 1

  return (
    <div style={{ height: 'calc(100vh - 65px)', overflowY: 'auto', padding: '1.1rem', display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <Activity size={14} color="#6366f1" />
          <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#1e293b', letterSpacing: '0.03em' }}>LIVE METRICS</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
          <motion.div
            animate={{ opacity: [1, 0.3, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
            style={{ width: 6, height: 6, borderRadius: '50%', background: '#10b981' }}
          />
          <span style={{ fontSize: '0.65rem', color: '#94a3b8' }}>
            {lastUpdated ? lastUpdated.toLocaleTimeString() : 'Loading…'}
          </span>
        </div>
      </div>

      <AnimatePresence>
        {metrics ? (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
            {/* Stat grid */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.65rem' }}>
              <Stat icon={Users}         label="Sessions"   rawValue={metrics.total_sessions || 0}         format={v => Math.round(v)}                      color="#6366f1" />
              <Stat icon={MessageSquare} label="Messages"   rawValue={metrics.total_messages || 0}         format={v => Math.round(v)}                      color="#8b5cf6" />
              <Stat icon={Clock}         label="Avg Latency" rawValue={metrics.avg_response_time_ms || 0}   format={v => v > 0 ? `${Math.round(v)}ms` : '—'} color="#f59e0b" />
              <Stat icon={Zap}           label="Retry Rate" rawValue={(metrics.retry_rate || 0) * 100}     format={v => `${Math.round(v)}%`}                color="#f97316"
                tooltip="How often the AI rephrased a question to get a better result. Triggers in the FAQ agent when the RAG reranker score falls below 0.3 — the AI rewrites the query once and retries RAG retrieval before escalating."
              />
            </div>

            {/* Circular metrics */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.65rem' }}>
              <CircleMetric
                label="Confidence" color="#10b981"
                pct={(metrics.avg_confidence || 0) * 100}
                tooltip="Average confidence score across all agent responses today. Higher means the AI was more certain about its answers."
              />
              <CircleMetric
                label="Cache Hit" color="#10b981"
                pct={(metrics.cache_hit_rate || 0) * 100}
                tooltip="Percentage of questions answered instantly from cache. A high cache hit rate means faster responses and lower compute cost."
              />
            </div>


            {/* Intent breakdown */}
            <div className="glass" style={{ borderRadius: '1rem', padding: '0.85rem' }}>
              <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#475569', letterSpacing: '0.04em', textTransform: 'uppercase', marginBottom: '0.65rem' }}>
                Intent Breakdown
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
                {Object.entries(intents).filter(([k]) => k !== 'cache').sort((a, b) => b[1] - a[1]).map(([intent, count]) => (
                  <div key={intent}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
                      <span style={{ fontSize: '0.74rem', fontWeight: 600, color: '#475569', textTransform: 'capitalize' }}>{intent}</span>
                      <span style={{ fontSize: '0.74rem', color: '#94a3b8', fontWeight: 500 }}>{count}</span>
                    </div>
                    <div style={{ height: 5, background: 'rgba(0,0,0,0.06)', borderRadius: 99, overflow: 'hidden' }}>
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${(count / totalIntent) * 100}%` }}
                        transition={{ duration: 0.6, ease: 'easeOut' }}
                        style={{ height: '100%', background: INTENT_COLORS[intent] || '#94a3b8', borderRadius: 99, boxShadow: `0 0 5px ${(INTENT_COLORS[intent] || '#94a3b8')}99` }}
                      />
                    </div>
                  </div>
                ))}
                {Object.keys(intents).length === 0 && (
                  <div style={{ textAlign: 'center', fontSize: '0.78rem', color: '#cbd5e1', padding: '0.5rem 0' }}>No data yet</div>
                )}
              </div>
            </div>

            {/* Feedback Summary */}
            {(() => {
              const pos   = metrics.feedback_positive || 0
              const neg   = metrics.feedback_negative || 0
              const total = pos + neg
              const sat   = total > 0 ? Math.round((pos / total) * 100) : 0
              return (
                <div className="glass" style={{ borderRadius: '1rem', padding: '0.85rem' }}>
                  <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#475569', letterSpacing: '0.04em', textTransform: 'uppercase', marginBottom: '0.75rem' }}>
                    Feedback Summary
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <CircleMetric pct={sat} color="#10b981" size={78} hideLabel />
                    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                      {[
                        { label: 'Total responses',  value: String(total),  color: '#0f172a' },
                        { label: 'Positive',         value: `+${pos}`,      color: '#059669' },
                        { label: 'Negative',         value: `-${neg}`,      color: '#dc2626' },
                        { label: 'Satisfaction',     value: `${sat}%`,      color: '#10b981' },
                      ].map(({ label, value, color }) => (
                        <div key={label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ fontSize: '0.73rem', color: '#64748b' }}>{label}</span>
                          <span style={{ fontSize: '0.73rem', fontWeight: 700, color }}>{value}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )
            })()}
          </motion.div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
            {[...Array(6)].map((_, i) => (
              <div key={i} className="metric-card" style={{ height: 64, background: 'rgba(255,255,255,0.4)' }}>
                <div style={{ height: 10, background: 'rgba(0,0,0,0.06)', borderRadius: 99, width: '60%', marginBottom: 8 }} />
                <div style={{ height: 18, background: 'rgba(0,0,0,0.04)', borderRadius: 99, width: '40%' }} />
              </div>
            ))}
          </div>
        )}
      </AnimatePresence>
    </div>
  )
}
