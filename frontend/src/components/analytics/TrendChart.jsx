import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import InfoTooltip from './InfoTooltip'


const HoverTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: 'white',
      border: '1px solid rgba(0,0,0,0.07)',
      borderRadius: 10,
      padding: '0.65rem 0.95rem',
      boxShadow: '0 8px 28px rgba(0,0,0,0.12)',
      fontSize: '0.78rem',
      minWidth: 130,
    }}>
      <div style={{ fontWeight: 700, color: '#1e293b', marginBottom: 8, fontSize: '0.74rem', letterSpacing: '0.03em' }}>
        {label}
      </div>
      {payload.map(p => (
        <div key={p.name} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
          <div style={{ width: 9, height: 9, borderRadius: '50%', background: p.color, flexShrink: 0 }} />
          <span style={{ color: '#64748b', flex: 1 }}>{p.name}</span>
          <span style={{ color: '#0f172a', fontWeight: 700 }}>{p.value}</span>
        </div>
      ))}
    </div>
  )
}

export default function TrendChart({ trend }) {
  if (!trend) return null

  const fmtDate = d => {
    const parts = d.split('-')
    return `${parseInt(parts[1])}/${parseInt(parts[2])}`
  }

  const data = trend.map(t => ({
    date:      fmtDate(t.date),
    Messages:  t.messages,
    Escalated: t.escalated || 0,
  }))

  const totalMessages  = data.reduce((s, d) => s + d.Messages, 0)
  const totalEscalated = data.reduce((s, d) => s + d.Escalated, 0)
  const escRate        = totalMessages > 0 ? Math.round((totalEscalated / totalMessages) * 100) : 0

  return (
    <div className="glass" style={{ borderRadius: '1.25rem', padding: '1.5rem 1.5rem 1.25rem', marginBottom: '0.75rem' }}>

      {/* Header row */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#1e293b', letterSpacing: '-0.01em' }}>
            Message Volume
          </span>
<InfoTooltip
            text="Daily message count vs escalations over the last 30 days. A wide gap between the two lines means the AI is resolving most queries without human handoff."
            width={255}
          />
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
          {/* Aggregate stat */}
          <div>
            <span style={{ fontSize: '1.05rem', fontWeight: 800, color: '#0f172a', letterSpacing: '-0.02em' }}>
              {totalMessages}
            </span>
            <span style={{ fontSize: '0.71rem', fontWeight: 600, color: '#94a3b8', marginLeft: 5 }}>msgs (30d)</span>
          </div>
          {totalEscalated > 0 && (
            <div style={{ fontSize: '0.72rem', fontWeight: 600, color: '#ef4444' }}>
              {totalEscalated} escalated ({escRate}%)
            </div>
          )}
          {/* Legend */}
          <div style={{ display: 'flex', gap: 14, alignItems: 'center' }}>
            {[
              { label: 'Messages',  color: '#6366f1' },
              { label: 'Escalated', color: '#ef4444' },
            ].map(({ label, color }) => (
              <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                <div style={{ width: 8, height: 8, borderRadius: '50%', background: color }} />
                <span style={{ fontSize: '0.71rem', color: '#64748b', fontWeight: 600 }}>{label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={data} margin={{ top: 5, right: 8, bottom: 0, left: -10 }}>
          <defs>
            <linearGradient id="gradMsg" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#6366f1" stopOpacity={0.25} />
              <stop offset="92%" stopColor="#6366f1" stopOpacity={0.02} />
            </linearGradient>
            <linearGradient id="gradEsc" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#ef4444" stopOpacity={0.22} />
              <stop offset="92%" stopColor="#ef4444" stopOpacity={0.02} />
            </linearGradient>
          </defs>

          <CartesianGrid vertical={false} stroke="rgba(0,0,0,0.045)" />

          <XAxis
            dataKey="date"
            tick={{ fontSize: 11, fill: '#94a3b8', fontWeight: 500 }}
            axisLine={false}
            tickLine={false}
            dy={6}
          />
          <YAxis
            tick={{ fontSize: 10, fill: '#94a3b8' }}
            axisLine={false}
            tickLine={false}
            allowDecimals={false}
          />

          <Tooltip
            content={<HoverTooltip />}
            cursor={{ stroke: 'rgba(99,102,241,0.18)', strokeWidth: 1.5, strokeDasharray: '5 3' }}
          />

          {/* Total messages — background area */}
          <Area
            type="monotone"
            dataKey="Messages"
            stroke="#6366f1"
            strokeWidth={2.2}
            fill="url(#gradMsg)"
            dot={false}
            activeDot={{ r: 5, fill: '#6366f1', stroke: 'white', strokeWidth: 2.5 }}
          />

          {/* Escalated — foreground area */}
          <Area
            type="monotone"
            dataKey="Escalated"
            stroke="#ef4444"
            strokeWidth={2}
            fill="url(#gradEsc)"
            dot={false}
            activeDot={{ r: 5, fill: '#ef4444', stroke: 'white', strokeWidth: 2.5 }}
          />
        </AreaChart>
      </ResponsiveContainer>

    </div>
  )
}
