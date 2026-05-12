import { useState } from 'react'
import { motion } from 'framer-motion'
import { Mail, ArrowRight, Zap, Shield, Bot } from 'lucide-react'

export default function EmailScreen({ onStart }) {
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
      setError('Please enter a valid email address')
      return
    }
    onStart(email)
  }

  return (
    <div style={{ minHeight: 'calc(100vh - 65px)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '2rem', position: 'relative', overflow: 'hidden' }}>
      {/* Orb */}
      <motion.div
        animate={{
          scale: [1, 1.07, 1],
          boxShadow: [
            '0 0 60px rgba(99,102,241,0.35), 0 0 120px rgba(139,92,246,0.18)',
            '0 0 90px rgba(139,92,246,0.55), 0 0 180px rgba(99,102,241,0.25)',
            '0 0 60px rgba(99,102,241,0.35), 0 0 120px rgba(139,92,246,0.18)',
          ]
        }}
        transition={{ duration: 3.5, repeat: Infinity, ease: 'easeInOut' }}
        style={{
          width: 110, height: 110, borderRadius: '50%', marginBottom: '2rem',
          background: 'radial-gradient(circle at 35% 30%, #c4b5fd, #6366f1, #3730a3)',
          boxShadow: '0 0 60px rgba(99,102,241,0.35)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}
      >
        <Bot size={36} color="white" strokeWidth={1.5} />
      </motion.div>

      {/* Heading */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }} style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <p style={{ fontSize: '0.9rem', fontWeight: 600, color: '#94a3b8', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
          Welcome to
        </p>
        <h1 style={{
          fontFamily: "'Playfair Display', serif",
          fontWeight: 700, fontStyle: 'italic',
          fontSize: '3.2rem', lineHeight: 1.05, marginBottom: '0.85rem',
          background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
          WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
          letterSpacing: '-0.01em',
        }}>
          ResolveDesk
        </h1>
        <p style={{ color: '#475569', fontSize: '1rem', fontWeight: 500, maxWidth: 400, lineHeight: 1.5 }}>
          Multi-Agent Customer Support System for CartFlow Ecommerce Platform
        </p>
      </motion.div>

      {/* Feature pills */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }} style={{ display: 'flex', gap: '0.75rem', marginBottom: '2.5rem', flexWrap: 'wrap', justifyContent: 'center' }}>
        {[
          { icon: Zap, text: 'Instant answers', color: '#f59e0b' },
          { icon: Shield, text: 'Secure & private', color: '#10b981' },
          { icon: Bot, text: '6 AI agents', color: '#6366f1' },
        ].map(({ icon: Icon, text, color }) => (
          <div key={text} className="glass" style={{ borderRadius: 99, padding: '0.4rem 1rem', display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.82rem', color: '#475569', fontWeight: 500 }}>
            <Icon size={13} color={color} />
            {text}
          </div>
        ))}
      </motion.div>

      {/* Form */}
      <motion.form
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.35 }}
        onSubmit={handleSubmit}
        className="glass-heavy"
        style={{ borderRadius: '1.5rem', padding: '2rem', width: '100%', maxWidth: 420, position: 'relative', zIndex: 1 }}
      >
        <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: '#374151', marginBottom: '0.5rem', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
          Your Email
        </label>
        <div style={{ position: 'relative', marginBottom: error ? '0.5rem' : '1.25rem' }}>
          <Mail size={15} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }} />
          <input
            type="email"
            value={email}
            onChange={(e) => { setEmail(e.target.value); setError('') }}
            placeholder="you@example.com"
            className="input-glass"
            style={{ paddingLeft: '1rem' }}
            autoFocus
          />
        </div>
        {error && <p style={{ color: '#ef4444', fontSize: '0.78rem', marginBottom: '1rem' }}>{error}</p>}
        <button type="submit" className="btn-primary" style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
          Start Chat <ArrowRight size={16} />
        </button>
      </motion.form>
      {/* Bottom wave */}
      <div style={{ position: 'absolute', bottom: 0, left: 0, width: '100%', lineHeight: 0, pointerEvents: 'none', zIndex: 0 }}>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 320" style={{ display: 'block', width: '100%' }}>
          <path fill="#6366f1" fillOpacity="1" d="M0,256L30,256C60,256,120,256,180,224C240,192,300,128,360,112C420,96,480,128,540,165.3C600,203,660,245,720,234.7C780,224,840,160,900,133.3C960,107,1020,117,1080,133.3C1140,149,1200,171,1260,154.7C1320,139,1380,85,1410,58.7L1440,32L1440,320L1410,320C1380,320,1320,320,1260,320C1200,320,1140,320,1080,320C1020,320,960,320,900,320C840,320,780,320,720,320C660,320,600,320,540,320C480,320,420,320,360,320C300,320,240,320,180,320C120,320,60,320,30,320L0,320Z" />
        </svg>
      </div>
    </div>
  )
}
