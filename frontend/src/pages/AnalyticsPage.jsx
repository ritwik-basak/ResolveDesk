import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { BarChart3, FolderOpen, RefreshCw } from 'lucide-react'
import SummaryCards from '../components/analytics/SummaryCards'
import Charts from '../components/analytics/Charts'
import TrendChart from '../components/analytics/TrendChart'
import SessionsTable from '../components/analytics/SessionsTable'
import TranscriptModal from '../components/analytics/TranscriptModal'
import AdminPanel from '../components/analytics/AdminPanel'

export default function AnalyticsPage() {
  const [tab, setTab]                   = useState('overview')
  const [days, setDays]                 = useState(0)
  const [summary, setSummary]           = useState(null)
  const [sessions, setSessions]         = useState([])
  const [trend, setTrend]               = useState([])
  const [selectedSession, setSelectedSession] = useState(null)
  const [loading, setLoading]           = useState(false)
  const [lastRefresh, setLastRefresh]   = useState(null)

  const load = async (d = days) => {
    setLoading(true)
    try {
      const daysParam    = d > 0 ? `?days=${d}` : ''
      const trendDays    = d > 0 ? d : 30
      const [sumRes, sessRes, trendRes] = await Promise.all([
        fetch(`/analytics/summary${daysParam}`),
        fetch('/analytics/sessions?page=1&page_size=100'),
        fetch(`/analytics/trend?days=${trendDays}`),
      ])
      setSummary(await sumRes.json())
      const s = await sessRes.json()
      setSessions(s.sessions || [])
      setTrend(await trendRes.json())
      setLastRefresh(new Date())
    } catch (_) {}
    finally { setLoading(false) }
  }

  useEffect(() => { load(days) }, [days])

  return (
    <div style={{ maxWidth: 1520, margin: '0 auto', padding: '1.75rem 2.5rem' }}>
      {/* Page header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.75rem' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#0f172a', letterSpacing: '-0.02em', marginBottom: 2 }}>Analytics</h1>
          <p style={{ fontSize: '0.82rem', color: '#94a3b8' }}>
            {lastRefresh ? `Last updated ${lastRefresh.toLocaleTimeString()}` : 'Loading…'}
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {/* Time range selector */}
          <div className="glass" style={{ borderRadius: '0.85rem', padding: '0.3rem', display: 'flex', gap: 2 }}>
            {[
              { label: '7d',    value: 7 },
              { label: '30d',   value: 30 },
              { label: '90d',   value: 90 },
              { label: '1y',    value: 365 },
              { label: 'All',   value: 0 },
            ].map(({ label, value }) => (
              <button
                key={value}
                onClick={() => setDays(value)}
                style={{
                  padding: '0.35rem 0.75rem', borderRadius: '0.5rem', border: 'none', cursor: 'pointer',
                  fontSize: '0.78rem', fontWeight: 600, transition: 'all 0.2s',
                  background: days === value ? 'linear-gradient(135deg, #6366f1, #8b5cf6)' : 'transparent',
                  color: days === value ? 'white' : '#64748b',
                  boxShadow: days === value ? '0 4px 12px rgba(99,102,241,0.3)' : 'none',
                }}
              >
                {label}
              </button>
            ))}
          </div>

          {/* Tab switcher */}
          <div className="glass" style={{ borderRadius: '0.85rem', padding: '0.3rem', display: 'flex', gap: 2 }}>
            {[
              { key: 'overview', label: 'Overview', icon: BarChart3 },
              { key: 'admin',    label: 'Documents', icon: FolderOpen },
            ].map(({ key, label, icon: Icon }) => (
              <motion.button
                key={key}
                onClick={() => setTab(key)}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.97 }}
                style={{
                  padding: '0.45rem 1rem', borderRadius: '0.6rem', border: 'none', cursor: 'pointer',
                  display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.82rem', fontWeight: 600,
                  transition: 'all 0.2s',
                  background: tab === key ? 'linear-gradient(135deg, #6366f1, #8b5cf6)' : 'transparent',
                  color: tab === key ? 'white' : '#64748b',
                  boxShadow: tab === key ? '0 4px 12px rgba(99,102,241,0.3)' : 'none',
                }}
              >
                <Icon size={13} /> {label}
              </motion.button>
            ))}
          </div>

          {/* Refresh button */}
          <motion.button
            onClick={() => load(days)}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            style={{ border: 'none', background: 'rgba(99,102,241,0.1)', color: '#6366f1', borderRadius: 10, padding: '0.5rem', cursor: 'pointer', display: 'flex', alignItems: 'center' }}
          >
            <motion.div animate={loading ? { rotate: 360 } : { rotate: 0 }} transition={loading ? { duration: 1, repeat: Infinity, ease: 'linear' } : {}}>
              <RefreshCw size={15} />
            </motion.div>
          </motion.button>
        </div>
      </div>

      <AnimatePresence mode="wait">
        {tab === 'overview' ? (
          <motion.div key="overview" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
            <SummaryCards data={summary} />
            <TrendChart trend={trend} />
            <Charts summary={summary} sessions={sessions} />
            <SessionsTable sessions={sessions} onSelect={setSelectedSession} />
          </motion.div>
        ) : (
          <motion.div key="admin" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
            <AdminPanel />
          </motion.div>
        )}
      </AnimatePresence>

      <TranscriptModal session={selectedSession} onClose={() => setSelectedSession(null)} />
    </div>
  )
}
