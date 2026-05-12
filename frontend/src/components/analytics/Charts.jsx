import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import InfoTooltip from './InfoTooltip'
import SemiGauge from './SemiGauge'

const INTENT_COLORS = { faq: '#6366f1', order: '#10b981', returns: '#f59e0b', chitchat: '#64748b', escalation: '#ef4444' }

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="glass-heavy" style={{ borderRadius: 10, padding: '0.6rem 0.85rem', fontSize: '0.8rem' }}>
      {label && <div style={{ fontWeight: 700, color: '#1e293b', marginBottom: 3 }}>{label}</div>}
      {payload.map(p => (
        <div key={p.name} style={{ color: p.color || '#6366f1', fontWeight: 600 }}>
          {p.name}: {typeof p.value === 'number' && p.value < 2 ? `${(p.value * 100).toFixed(1)}%` : p.value}
        </div>
      ))}
    </div>
  )
}

function ChartHeader({ label, tooltip, tooltipWidth }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginBottom: '0.75rem' }}>
      <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#475569', letterSpacing: '0.05em', textTransform: 'uppercase' }}>{label}</div>
      <InfoTooltip text={tooltip} width={tooltipWidth || 230} />
    </div>
  )
}

export default function Charts({ summary }) {
  if (!summary) return null

  const intentData = Object.entries(summary.intent_breakdown || {})
    .filter(([name]) => name !== 'cache')
    .map(([name, value]) => ({
      name: name.charAt(0).toUpperCase() + name.slice(1),
      value,
      fill: INTENT_COLORS[name] || '#94a3b8',
    }))

  const totalRated      = (summary.feedback_positive || 0) + (summary.feedback_negative || 0)
  const satisfactionPct = totalRated > 0 ? Math.round(((summary.feedback_positive || 0) / totalRated) * 100) : null
  const cachePct        = Math.round((summary.cache_hit_rate || 0) * 100)

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1.6fr 1fr 1fr 1fr', gap: '1rem', marginBottom: '0.75rem' }}>

      {/* Intent breakdown bar chart */}
      <div className="glass" style={{ borderRadius: '1.25rem', padding: '1.25rem' }}>
        <ChartHeader
          label="Intent Breakdown"
          tooltip="Intents classified by the Supervisor agent (Llama-3.3-70B). Routing: faq → FAQ agent, order/returns → tool-calling agents, chitchat → small talk, escalation → abusive messages only."
          tooltipWidth={240}
        />
        {intentData.length > 0 ? (
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={intentData} barSize={28} margin={{ top: 0, right: 0, bottom: 0, left: -20 }}>
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#94a3b8', fontWeight: 600 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(99,102,241,0.04)' }} />
              <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                {intentData.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} style={{ filter: `drop-shadow(0 2px 6px ${entry.fill}55)` }} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div style={{ height: 160, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#cbd5e1', fontSize: '0.82rem' }}>No data yet</div>
        )}
      </div>

      {/* User feedback gauge */}
      <div className="glass" style={{ borderRadius: '1.25rem', padding: '1.25rem', display: 'flex', flexDirection: 'column' }}>
        <ChartHeader
          label="User Feedback"
          tooltip="Thumbs up/down collected on messages. Satisfaction % = positive ÷ (positive + negative). Only explicitly-rated messages are counted."
          tooltipWidth={220}
        />
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <SemiGauge
            pct={satisfactionPct || 0}
            color="#10b981"
            size={155}
            sub={satisfactionPct === null ? 'no ratings yet' : 'satisfaction rate'}
          />
        </div>
      </div>

      {/* Cache hit gauge */}
      <div className="glass" style={{ borderRadius: '1.25rem', padding: '1.25rem', display: 'flex', flexDirection: 'column' }}>
        <ChartHeader
          label="Cache Hit Rate"
          tooltip="Queries served from Redis semantic cache. Threshold: cosine similarity ≥ 0.85 using BGE-base-en-v1.5 embeddings (768-dim). Cache hits skip the LLM entirely — 0 tokens, 0 cost."
          tooltipWidth={230}
        />
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <SemiGauge
            pct={cachePct}
            color="#6366f1"
            size={155}
            sub="of responses cached"
          />
        </div>
      </div>

      {/* Token / LLM usage */}
      <div className="glass" style={{ borderRadius: '1.25rem', padding: '1.25rem', display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: '0.85rem' }}>
        <ChartHeader
          label="LLM Usage"
          tooltip="Three models per message: Gemini 2.5 Flash (supervisor, $0.15/1M) + Groq Llama 3.1 8B (chitchat, $0.06/1M) + Groq Llama 3.3 70B (faq/order/returns, $0.70/1M). Cost = 70B×$0.0000007 + 8B×$0.00000006 + Gemini×$0.00000015."
          tooltipWidth={230}
        />
        <div style={{ textAlign: 'center' }}>
          <div style={{
            fontSize: '2rem', fontWeight: 800, letterSpacing: '-0.02em',
            background: 'linear-gradient(135deg, #8b5cf6, #ec4899)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
          }}>
            {((summary.total_tokens || 0) / 1000).toFixed(1)}K
          </div>
          <div style={{ fontSize: '0.72rem', color: '#94a3b8', fontWeight: 600, marginTop: 2 }}>total tokens used</div>
        </div>
        <div style={{ borderTop: '1px solid rgba(0,0,0,0.06)', paddingTop: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
          {[
            { label: 'Total tokens', value: (summary.total_tokens || 0).toLocaleString() },
            { label: 'Est. cost',    value: `$${(summary.est_cost_usd || 0).toFixed(4)}` },
            { label: 'Per message',  value: summary.total_messages > 0 ? `~${Math.round((summary.total_tokens || 0) / (summary.total_messages || 1))} tok` : '—' },
          ].map(({ label, value }) => (
            <div key={label} style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '0.73rem', color: '#64748b' }}>{label}</span>
              <span style={{ fontSize: '0.73rem', fontWeight: 700, color: '#0f172a' }}>{value}</span>
            </div>
          ))}
        </div>
      </div>

    </div>
  )
}
