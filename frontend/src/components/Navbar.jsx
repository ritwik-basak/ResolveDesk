import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Bot, MessageSquare, BarChart3 } from 'lucide-react'

export default function Navbar({ page, setPage }) {
  const [time, setTime] = useState(new Date())

  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(t)
  }, [])

  return (
    <nav className="glass sticky top-0 z-50 px-6 py-3.5 flex items-center justify-between border-b border-white/60">
      {/* Logo */}
      <div className="flex items-center gap-2.5">
        <div style={{
          width: 34, height: 34, borderRadius: '50%',
          background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: '0 4px 14px rgba(99,102,241,0.4)'
        }}>
          <Bot size={17} color="white" strokeWidth={2} />
        </div>
        <span style={{
          fontFamily: "'Playfair Display', serif",
          fontWeight: 700, fontStyle: 'normal',
          fontSize: '1.35rem', letterSpacing: '-0.01em', lineHeight: 1,
          background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
          WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
        }}>
          ResolveDesk
        </span>
        <span style={{
          fontSize: '0.6rem', fontWeight: 600, color: '#6366f1',
          background: 'rgba(99,102,241,0.1)', borderRadius: 99,
          padding: '2px 8px', letterSpacing: '0.05em'
        }}>BETA</span>
      </div>

      {/* Page Toggle */}
      <div className="glass rounded-xl p-1 flex gap-1">
        {[
          { key: 'chat', label: 'Chat', icon: MessageSquare },
          { key: 'analytics', label: 'Analytics', icon: BarChart3 },
        ].map(({ key, label, icon: Icon }) => (
          <motion.button
            key={key}
            onClick={() => setPage(key)}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.97 }}
            style={{
              padding: '0.45rem 1.1rem',
              borderRadius: '0.6rem',
              fontSize: '0.85rem',
              fontWeight: 600,
              border: 'none',
              cursor: 'pointer',
              display: 'flex', alignItems: 'center', gap: 6,
              transition: 'all 0.2s ease',
              background: page === key
                ? 'linear-gradient(135deg, #6366f1, #8b5cf6)'
                : 'transparent',
              color: page === key ? 'white' : '#64748b',
              boxShadow: page === key ? '0 4px 14px rgba(99,102,241,0.3)' : 'none',
            }}
          >
            <Icon size={14} />
            {label}
          </motion.button>
        ))}
      </div>

      {/* Clock */}
      <div className="glass rounded-xl px-4 py-2 flex items-center gap-2">
        <div style={{ width: 7, height: 7, borderRadius: '50%', background: '#10b981', boxShadow: '0 0 6px #10b981' }} />
        <span style={{ fontFamily: 'monospace', fontSize: '0.82rem', color: '#475569', fontWeight: 500 }}>
          {time.toLocaleTimeString()}
        </span>
      </div>
    </nav>
  )
}
