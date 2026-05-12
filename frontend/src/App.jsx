import { useState } from 'react'
import Navbar from './components/Navbar'
import ChatPage from './pages/ChatPage'
import AnalyticsPage from './pages/AnalyticsPage'

function BackgroundBlobs() {
  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
      <div style={{
        position: 'absolute', top: '-10%', left: '-5%',
        width: '500px', height: '500px', borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(99,102,241,0.12) 0%, transparent 70%)',
        filter: 'blur(40px)',
      }} />
      <div style={{
        position: 'absolute', top: '30%', right: '-10%',
        width: '600px', height: '600px', borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(139,92,246,0.1) 0%, transparent 70%)',
        filter: 'blur(60px)',
      }} />
      <div style={{
        position: 'absolute', bottom: '-5%', left: '30%',
        width: '400px', height: '400px', borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(16,185,129,0.08) 0%, transparent 70%)',
        filter: 'blur(50px)',
      }} />
    </div>
  )
}

export default function App() {
  const [page, setPage] = useState('chat')

  return (
    <div className="min-h-screen relative">
      <BackgroundBlobs />
      <Navbar page={page} setPage={setPage} />
      <main className="relative z-10">
        {page === 'chat' ? <ChatPage /> : <AnalyticsPage />}
      </main>
    </div>
  )
}
