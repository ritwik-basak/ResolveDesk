import { useState, useRef, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { Info } from 'lucide-react'

export default function InfoTooltip({ text, width = 230, direction = 'up' }) {
  const [show, setShow] = useState(false)
  const [rect, setRect] = useState(null)
  const ref = useRef(null)

  // Capture fresh coordinates whenever tooltip becomes visible
  useEffect(() => {
    if (show && ref.current) {
      setRect(ref.current.getBoundingClientRect())
    }
  }, [show])

  const down = direction === 'down'

  const tooltipStyle = rect ? {
    position: 'fixed',
    top:       down ? rect.bottom + 10 : rect.top - 10,
    left:      rect.left + rect.width / 2,
    transform: down ? 'translateX(-50%)' : 'translateX(-50%) translateY(-100%)',
    background: '#1e293b', color: '#cbd5e1',
    fontSize: '0.71rem', lineHeight: 1.65,
    padding: '0.7rem 0.95rem', borderRadius: 10,
    width, zIndex: 9999,
    boxShadow: '0 16px 40px rgba(0,0,0,0.32)',
    pointerEvents: 'none', whiteSpace: 'normal',
  } : null

  return (
    <>
      <div
        ref={ref}
        style={{ position: 'relative', display: 'inline-flex', alignItems: 'center', flexShrink: 0 }}
        onMouseEnter={() => setShow(true)}
        onMouseLeave={() => setShow(false)}
      >
        <div style={{
          width: 20, height: 20, borderRadius: '50%',
          background: show ? 'rgba(99,102,241,0.18)' : 'rgba(99,102,241,0.1)',
          border: `1.5px solid ${show ? 'rgba(99,102,241,0.45)' : 'rgba(99,102,241,0.25)'}`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          cursor: 'help', transition: 'all 0.15s',
        }}>
          <Info size={11} color="#6366f1" strokeWidth={2.5} />
        </div>
      </div>

      {show && tooltipStyle && createPortal(
        <div style={tooltipStyle}>
          <div style={{
            position: 'absolute',
            left: '50%', transform: 'translateX(-50%)',
            width: 10, height: 6, background: '#1e293b',
            ...(down
              ? { top: -5,    clipPath: 'polygon(50% 0, 100% 100%, 0 100%)' }
              : { bottom: -5, clipPath: 'polygon(0 0, 100% 0, 50% 100%)' }),
          }} />
          {text}
        </div>,
        document.body
      )}
    </>
  )
}
