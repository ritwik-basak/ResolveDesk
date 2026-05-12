import { useState, useEffect } from 'react'

function useCountUp(target, duration = 1600) {
  const [val, setVal] = useState(0)
  useEffect(() => {
    if (!target) { setVal(0); return }
    let rafId, startTs = null
    const tick = ts => {
      if (!startTs) startTs = ts
      const p = Math.min((ts - startTs) / duration, 1)
      const e = 1 - Math.pow(1 - p, 2.5)  // ease-out 2.5: at p=0.5 only 82% done, slows from ~80%
      setVal(target * e)
      if (p < 1) rafId = requestAnimationFrame(tick)
    }
    rafId = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(rafId)
  }, [target, duration])
  return val
}

export default function SemiGauge({ pct, color, size = 175, sub, hideLabel = false }) {
  const [displayPct, setDisplayPct] = useState(0)
  const animated = useCountUp(pct || 0, 1200)

  useEffect(() => {
    const t = setTimeout(() => setDisplayPct(pct || 0), 60)
    return () => clearTimeout(t)
  }, [pct])

  const cx      = size / 2
  const r       = size * 0.39
  const sw      = Math.max(9, size * 0.075)
  const cy      = r + sw / 2 + 4           // y of the diameter line
  const pxNum   = Math.round(size * 0.123) // main % number, px
  const pxSub   = Math.round(size * 0.066) // sub label, px

  // Text sits INSIDE the concave area: baseline just above the diameter
  const textY   = cy - Math.round(pxNum * 0.38)
  // Sub label sits just below the diameter (outside the arc, compact)
  const subY    = cy + pxSub + 3
  const H       = sub && !hideLabel
    ? Math.ceil(subY + pxSub * 0.4 + 2)
    : Math.ceil(cy + 6)

  const arcLen  = Math.PI * r
  const filled  = Math.min(Math.max(displayPct, 0), 100)
  const offset  = arcLen * (1 - filled / 100)

  return (
    <svg width={size} height={H} style={{ overflow: 'visible', display: 'block', margin: '0 auto' }}>
      {/* Track */}
      <path
        d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
        fill="none" stroke="rgba(0,0,0,0.08)" strokeWidth={sw} strokeLinecap="round"
      />
      {/* Fill */}
      <path
        d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
        fill="none" stroke={color} strokeWidth={sw} strokeLinecap="round"
        strokeDasharray={arcLen} strokeDashoffset={offset}
        style={{ filter: `drop-shadow(0 0 7px ${color}aa)`, transition: 'stroke-dashoffset 1.6s cubic-bezier(0.25, 0.8, 0.25, 1)' }}
      />
      {/* Percentage — inside the concave area (hidden when used in split-card layout) */}
      {!hideLabel && (
        <text x={cx} y={textY} textAnchor="middle"
          style={{ fontSize: pxNum, fontWeight: 800, fill: '#0f172a', letterSpacing: '-0.025em' }}
        >
          {animated.toFixed(1)}%
        </text>
      )}
      {/* Sub label — compact, just below the diameter */}
      {!hideLabel && sub && (
        <text x={cx} y={subY} textAnchor="middle"
          style={{ fontSize: pxSub, fill: '#94a3b8', fontWeight: 600 }}
        >
          {sub}
        </text>
      )}
    </svg>
  )
}
