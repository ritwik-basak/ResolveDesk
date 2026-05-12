import { useEffect } from 'react'
import { useState } from 'react'
import { motion } from 'framer-motion'
import { Users, MessageSquare, Cpu, Clock } from 'lucide-react'
import InfoTooltip from './InfoTooltip'
import SemiGauge from './SemiGauge'

function useCountUp(target, duration = 1600) {
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

const ALL_CARDS = [
  {
    key: 'total_sessions', type: 'flat', label: 'Total Sessions', icon: Users,
    gradient: ['#6366f1', '#8b5cf6'], format: v => Math.round(v),
    tooltip: 'Unique chat sessions initiated. A new session_id is generated each time a customer starts chatting. Sessions persist across page reloads.',
  },
  {
    key: 'total_messages', type: 'flat', label: 'Total Messages', icon: MessageSquare,
    gradient: ['#3b82f6', '#6366f1'], format: v => Math.round(v),
    tooltip: 'Total user messages processed across all sessions. Each HumanMessage → one row in the messages table.',
  },
  {
    key: 'escalation_rate', type: 'circle', label: 'Escalation Rate',
    gradient: ['#f59e0b', '#ef4444'], pctOf: v => (v || 0) * 100,
    sub: 'messages escalated',
    tooltip: 'How often the AI couldn\'t resolve a query and handed it off. Triggers when the agent\'s confidence drops below 75%, or when rephrasing the question still yields a poor RAG knowledge base match.',
  },
  {
    key: 'avg_confidence', type: 'circle', label: 'Avg Confidence',
    gradient: ['#10b981', '#06b6d4'], pctOf: v => (v || 0) * 100,
    sub: 'agent certainty',
    tooltip: 'Average certainty score across all AI responses. Each agent rates its own answer from 0–1. Scores below 0.75 trigger escalation to a human. Higher is better.',
  },
  {
    key: 'est_cost_usd', type: 'flat', label: 'Est. LLM Cost', icon: Cpu,
    gradient: ['#8b5cf6', '#ec4899'], format: v => `$${v.toFixed(4)}`,
    tooltip: 'Estimated API cost across 3 models — Gemini 2.5 Flash ($0.15/1M tokens) for routing, Llama 3.1 8B ($0.06/1M) for chitchat, Llama 3.3 70B ($0.70/1M) for FAQ/orders/returns. Cached responses cost nothing — no model is called.',
  },
  {
    key: 'avg_response_time_ms', type: 'flat', label: 'Avg Latency', icon: Clock,
    gradient: ['#06b6d4', '#10b981'], format: v => `${Math.round(v)}ms`,
    tooltip: 'Server-side AI processing time per message. Measured from request received to pipeline complete — does not include the time taken to stream words to your screen, so actual time-to-screen is higher. Cache hits are near-instant.',
  },
  {
    key: 'retry_rate', type: 'circle', label: 'Retry Rate',
    gradient: ['#f59e0b', '#f97316'], pctOf: v => (v || 0) * 100,
    sub: 'queries rewritten',
    tooltip: 'How often the AI rephrased a question to get a better result. Triggers in the FAQ agent when the RAG reranker score falls below 0.3 — the AI rewrites the query once and retries RAG retrieval before escalating.',
  },
  {
    key: 'avg_rag_score', type: 'circle', label: 'Avg RAG Score',
    gradient: ['#10b981', '#84cc16'], pctOf: v => (v || 0) * 100,
    sub: 'RAG match quality',
    tooltip: 'Average RAG relevance score of the best knowledge base match, scored by the CrossEncoder reranker (ms-marco-MiniLM-L-12-v2). Reads the query and each retrieved chunk together to judge how well they match. 0 = no match found, 1 = exact match. Only tracked for the FAQ agent, which uses RAG retrieval.',
  },
]

function FlatCard({ card, value, i }) {
  const animated = useCountUp(value ?? 0)
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: i * 0.05 }}
      className="glass"
      style={{ borderRadius: '1.25rem', padding: '1.5rem', position: 'relative', cursor: 'default', display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: '0.65rem' }}
      whileHover={{ y: -3, boxShadow: '0 16px 48px rgba(99,102,241,0.14)' }}
    >
      <div style={{ position: 'absolute', top: -20, right: -20, width: 80, height: 80, borderRadius: '50%', background: `radial-gradient(circle, ${card.gradient[0]}22, transparent 70%)`, filter: 'blur(10px)', pointerEvents: 'none' }} />
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
          <span style={{ fontSize: '0.67rem', fontWeight: 700, color: '#94a3b8', letterSpacing: '0.06em', textTransform: 'uppercase' }}>{card.label}</span>
          <InfoTooltip text={card.tooltip} width={220} direction={i < 4 ? 'down' : 'up'} />
        </div>
        <div style={{ width: 30, height: 30, borderRadius: 9, background: `linear-gradient(135deg, ${card.gradient[0]}, ${card.gradient[1]})`, display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: `0 4px 12px ${card.gradient[0]}44`, flexShrink: 0 }}>
          <card.icon size={14} color="white" />
        </div>
      </div>
      <div style={{ fontSize: '1.75rem', fontWeight: 800, letterSpacing: '-0.03em', background: `linear-gradient(135deg, ${card.gradient[0]}, ${card.gradient[1]})`, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
        {card.format(animated)}
      </div>
    </motion.div>
  )
}

function CircleCard({ card, value, i }) {
  const pct      = card.pctOf(value)
  const animated = useCountUp(pct, 1200)
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: i * 0.05 }}
      className="glass"
      style={{ borderRadius: '1.25rem', padding: '1.25rem', position: 'relative', cursor: 'default', display: 'flex', alignItems: 'center', gap: '0.75rem' }}
      whileHover={{ y: -3, boxShadow: '0 16px 48px rgba(99,102,241,0.14)' }}
    >
      <div style={{ position: 'absolute', top: -20, right: -20, width: 80, height: 80, borderRadius: '50%', background: `radial-gradient(circle, ${card.gradient[0]}22, transparent 70%)`, filter: 'blur(10px)', pointerEvents: 'none' }} />

      {/* Left: label + big number + sub text */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginBottom: '0.35rem' }}>
          <span style={{ fontSize: '0.67rem', fontWeight: 700, color: '#94a3b8', letterSpacing: '0.06em', textTransform: 'uppercase' }}>{card.label}</span>
          <InfoTooltip text={card.tooltip} width={220} direction={i < 4 ? 'down' : 'up'} />
        </div>
        <div style={{ fontSize: '1.75rem', fontWeight: 800, letterSpacing: '-0.03em', background: `linear-gradient(135deg, ${card.gradient[0]}, ${card.gradient[1]})`, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          {animated.toFixed(1)}%
        </div>
        {card.sub && <div style={{ fontSize: '0.72rem', color: '#94a3b8', fontWeight: 500, marginTop: 3 }}>{card.sub}</div>}
      </div>

      {/* Right: arc only, no text inside */}
      <SemiGauge pct={pct} color={card.gradient[0]} size={115} hideLabel />
    </motion.div>
  )
}

export default function SummaryCards({ data }) {
  if (!data) return null
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
      {ALL_CARDS.map((card, i) =>
        card.type === 'circle'
          ? <CircleCard key={card.key} card={card} value={data[card.key] ?? 0} i={i} />
          : <FlatCard   key={card.key} card={card} value={data[card.key] ?? 0} i={i} />
      )}
    </div>
  )
}
