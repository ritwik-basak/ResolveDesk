export default function TypingIndicator() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: '1rem' }}>
      <div className="glass" style={{ borderRadius: '0.25rem 1.25rem 1.25rem 1.25rem', padding: '0.75rem 1rem', display: 'flex', alignItems: 'center', gap: 5 }}>
        <span className="typing-dot" />
        <span className="typing-dot" />
        <span className="typing-dot" />
      </div>
    </div>
  )
}
