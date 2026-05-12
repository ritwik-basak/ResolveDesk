import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, LogOut, AlertTriangle, X } from 'lucide-react'
import { v4 as uuidv4 } from 'uuid'
import MessageBubble from './MessageBubble'

const WELCOME = (back = false) => ({
  id: 'welcome', role: 'bot', agentType: 'chitchat', streaming: false,
  content: back
    ? `Welcome back! I remember our conversation. How can I help you today?`
    : `Hi! I'm ResolveDesk, CartFlow's AI support assistant. How can I help you today?`,
})

export default function ChatWindow({ email, onEnd }) {
  // Persist session ID in localStorage — same email resumes the same session
  const [{ sessionId, isResuming }] = useState(() => {
    const key = `rdesk_sid_${email}`
    const existing = localStorage.getItem(key)
    if (existing) return { sessionId: existing, isResuming: true }
    const id = uuidv4()
    localStorage.setItem(key, id)
    return { sessionId: id, isResuming: false }
  })

  const [messages, setMessages] = useState([])
  const [loadingHistory, setLoadingHistory] = useState(isResuming)
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [apiError, setApiError] = useState(null)
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (!isResuming) {
      setMessages([WELCOME(false)])
      return
    }
    // Fetch previous messages for this session
    fetch(`/analytics/session/${sessionId}`)
      .then(r => r.ok ? r.json() : Promise.reject())
      .then(data => {
        const msgs = []
        for (const m of (data.messages || [])) {
          if (m.user_message) msgs.push({ id: uuidv4(), role: 'user', content: m.user_message })
          if (m.agent_response) msgs.push({
            id: uuidv4(), role: 'bot', content: m.agent_response, streaming: false,
            agentType: m.agent_type, escalated: m.escalated,
            cacheHit: m.cache_hit, messageId: m.message_id, feedback: m.feedback || null,
          })
        }
        setMessages(msgs.length > 0 ? [WELCOME(true), ...msgs] : [WELCOME(false)])
      })
      .catch(() => setMessages([WELCOME(false)]))
      .finally(() => setLoadingHistory(false))
  }, [])

  const sendMessage = async (text) => {
    if (!text.trim() || isStreaming) return
    setInput('')
    setIsStreaming(true)

    const userMsg = { id: uuidv4(), role: 'user', content: text }
    const botId = uuidv4()
    const botMsg = { id: botId, role: 'bot', content: '', streaming: true }

    setMessages(prev => [...prev, userMsg, botMsg])

    try {
      const res = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, customer_email: email, message: text }),
      })

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const data = JSON.parse(line.slice(6))
            if (data.type === 'token') {
              setMessages(prev => prev.map(m =>
                m.id === botId ? { ...m, content: m.content + data.content } : m
              ))
            } else if (data.type === 'done') {
              setMessages(prev => prev.map(m =>
                m.id === botId ? {
                  ...m, streaming: false,
                  messageId: data.message_id,
                  agentType: data.agent_type,
                  escalated: data.escalated,
                  cacheHit: data.cache_hit,
                } : m
              ))
            } else if (data.type === 'error') {
              setApiError(data.message)
              setMessages(prev => prev.filter(m => m.id !== botId))
            }
          } catch (_) {}
        }
      }
    } catch (err) {
      setMessages(prev => prev.map(m =>
        m.id === botId ? { ...m, content: 'Sorry, something went wrong. Please try again.', streaming: false } : m
      ))
    } finally {
      setIsStreaming(false)
      inputRef.current?.focus()
    }
  }

  const handleFeedback = async (messageId, value) => {
    try {
      await fetch('/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message_id: messageId, feedback: value }),
      })
    } catch (_) {}
  }

  const handleEnd = async () => {
    localStorage.removeItem(`rdesk_sid_${email}`)
    try { await fetch('/session/end', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: sessionId }) }) } catch (_) {}
    onEnd()
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 65px)' }}>
      {/* Header */}
      <div className="glass" style={{ padding: '0.85rem 1.25rem', borderBottom: '1px solid rgba(255,255,255,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#10b981', boxShadow: '0 0 8px #10b981' }} />
          <div>
            <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#1e293b' }}>CartFlow AI Support</div>
            <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>{email}</div>
          </div>
        </div>
        <button onClick={handleEnd} style={{ border: 'none', background: 'rgba(239,68,68,0.08)', color: '#ef4444', borderRadius: 8, padding: '0.35rem 0.75rem', cursor: 'pointer', fontSize: '0.75rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 4 }}>
          <LogOut size={12} /> End
        </button>
      </div>

      {/* API Error Banner */}
      <AnimatePresence>
        {apiError && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            style={{
              display: 'flex', alignItems: 'flex-start', gap: 10,
              background: 'rgba(239,68,68,0.1)',
              borderBottom: '1px solid rgba(239,68,68,0.25)',
              padding: '0.75rem 1.25rem',
            }}
          >
            <AlertTriangle size={16} color="#dc2626" style={{ flexShrink: 0, marginTop: 1 }} />
            <span style={{ flex: 1, fontSize: '0.8rem', color: '#991b1b', fontWeight: 500, lineHeight: 1.5 }}>
              {apiError}
            </span>
            <button
              onClick={() => setApiError(null)}
              style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 2, color: '#dc2626', flexShrink: 0 }}
            >
              <X size={14} />
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '1.25rem 1.25rem 0.5rem' }}>
        {loadingHistory && (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, padding: '2rem', color: '#94a3b8', fontSize: '0.82rem' }}>
            <div style={{ width: 16, height: 16, border: '2px solid #6366f1', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 0.7s linear infinite' }} />
            Resuming your conversation…
          </div>
        )}
        <AnimatePresence>
          {messages.map(msg => (
            <motion.div key={msg.id} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25 }}>
              <MessageBubble message={msg} onFeedback={handleFeedback} />
            </motion.div>
          ))}
        </AnimatePresence>
        <div ref={bottomRef} />
      </div>

      {/* Sample questions — shown only when chat is empty */}
      {messages.length <= 1 && (
        <div style={{ padding: '0 1.25rem 0.75rem', display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
          {[
            'What is your return policy?',
            'Where is my order ORD-10001?',
            'How long does shipping take?',
            'Can I pay with UPI?',
          ].map(q => (
            <motion.button
              key={q}
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => sendMessage(q)}
              style={{
                border: '1px solid rgba(99,102,241,0.25)',
                background: 'rgba(99,102,241,0.06)',
                color: '#6366f1', borderRadius: 99,
                padding: '0.4rem 0.9rem',
                fontSize: '0.78rem', fontWeight: 600,
                cursor: 'pointer', transition: 'all 0.15s',
              }}
            >
              {q}
            </motion.button>
          ))}
        </div>
      )}

      {/* Input */}
      <div style={{ padding: '0.85rem 1.25rem 1.25rem' }}>
        <div className="glass" style={{ borderRadius: '1.25rem', padding: '0.5rem 0.5rem 0.5rem 1.1rem', display: 'flex', alignItems: 'center', gap: 8 }}>
          <input
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), sendMessage(input))}
            placeholder="Type your message…"
            disabled={isStreaming}
            style={{ flex: 1, border: 'none', background: 'transparent', outline: 'none', fontSize: '0.88rem', color: '#1e293b' }}
          />
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => sendMessage(input)}
            disabled={!input.trim() || isStreaming}
            style={{
              width: 38, height: 38, borderRadius: '0.9rem', border: 'none', cursor: input.trim() && !isStreaming ? 'pointer' : 'default',
              background: input.trim() && !isStreaming ? 'linear-gradient(135deg, #6366f1, #8b5cf6)' : 'rgba(148,163,184,0.2)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              transition: 'all 0.2s', boxShadow: input.trim() && !isStreaming ? '0 4px 12px rgba(99,102,241,0.35)' : 'none',
            }}
          >
            <Send size={15} color={input.trim() && !isStreaming ? 'white' : '#94a3b8'} />
          </motion.button>
        </div>
      </div>
    </div>
  )
}
