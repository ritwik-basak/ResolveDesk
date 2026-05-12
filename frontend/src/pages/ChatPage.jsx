import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import EmailScreen from '../components/chat/EmailScreen'
import ChatWindow from '../components/chat/ChatWindow'
import LiveMetrics from '../components/chat/LiveMetrics'

export default function ChatPage() {
  const [email, setEmail] = useState(null)

  return (
    <AnimatePresence mode="wait">
      {!email ? (
        <motion.div
          key="email"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0, y: -16 }}
          transition={{ duration: 0.25, ease: 'easeInOut' }}
        >
          <EmailScreen onStart={setEmail} />
        </motion.div>
      ) : (
        <motion.div
          key="chat"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.2 }}
          style={{ display: 'grid', gridTemplateColumns: '1fr 420px', height: 'calc(100vh - 65px)', overflow: 'hidden' }}
        >
          {/* Chat area — fades up from slightly below */}
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.05, ease: [0.25, 0.46, 0.45, 0.94] }}
            style={{ borderRight: '1px solid rgba(255,255,255,0.6)', overflow: 'hidden' }}
          >
            <ChatWindow email={email} onEnd={() => setEmail(null)} />
          </motion.div>

          {/* Live Metrics — slides in from the right */}
          <motion.div
            initial={{ opacity: 0, x: 420 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.45, delay: 0.1, ease: [0.25, 0.46, 0.45, 0.94] }}
            className="glass"
            style={{ borderLeft: '1px solid rgba(255,255,255,0.5)', overflow: 'hidden' }}
          >
            <LiveMetrics />
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
