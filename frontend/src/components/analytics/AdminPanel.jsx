import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Upload, Trash2, FileText, File, AlertCircle, CheckCircle } from 'lucide-react'

const EXT_COLORS = { pdf: '#ef4444', docx: '#3b82f6', txt: '#64748b', md: '#8b5cf6', pptx: '#f59e0b', csv: '#10b981' }

export default function AdminPanel() {
  const [docs, setDocs] = useState([])
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const [toast, setToast] = useState(null)
  const inputRef = useRef(null)

  const fetchDocs = async () => {
    try {
      const res = await fetch('/ingest/documents')
      const data = await res.json()
      setDocs(data.documents || [])
    } catch (_) {}
  }

  useEffect(() => { fetchDocs() }, [])

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 3000)
  }

  const handleUpload = async (file) => {
    if (!file) return
    const allowed = ['.pdf', '.docx', '.txt', '.md', '.pptx', '.csv']
    const ext = '.' + file.name.split('.').pop().toLowerCase()
    if (!allowed.includes(ext)) {
      showToast(`Unsupported format. Use: ${allowed.join(', ')}`, 'error')
      return
    }
    setUploading(true)
    const form = new FormData()
    form.append('file', file)
    try {
      const res = await fetch('/ingest/upload', { method: 'POST', body: form })
      const data = await res.json()
      if (res.ok) {
        showToast(`Uploaded "${file.name}" — ${data.chunk_count} chunks created`)
        fetchDocs()
      } else {
        showToast(data.detail || 'Upload failed', 'error')
      }
    } catch (e) {
      showToast('Upload failed', 'error')
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (filename) => {
    if (!confirm(`Delete "${filename}"? This will remove it from Pinecone, Supabase, and GCS.`)) return
    try {
      const res = await fetch(`/ingest/delete/${encodeURIComponent(filename)}`, { method: 'DELETE' })
      if (res.ok) {
        showToast(`Deleted "${filename}"`)
        setDocs(prev => prev.filter(d => d.filename !== filename))
      } else {
        showToast('Delete failed', 'error')
      }
    } catch (_) {
      showToast('Delete failed', 'error')
    }
  }

  return (
    <div>
      {/* Toast */}
      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            style={{
              position: 'fixed', top: 80, right: 24, zIndex: 200,
              display: 'flex', alignItems: 'center', gap: 8,
              background: toast.type === 'error' ? 'rgba(239,68,68,0.95)' : 'rgba(16,185,129,0.95)',
              color: 'white', borderRadius: 12, padding: '0.65rem 1rem',
              fontSize: '0.82rem', fontWeight: 600, backdropFilter: 'blur(10px)',
              boxShadow: '0 8px 24px rgba(0,0,0,0.15)',
            }}
          >
            {toast.type === 'error' ? <AlertCircle size={15} /> : <CheckCircle size={15} />}
            {toast.msg}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Upload zone */}
      <div
        className="glass"
        onDragOver={e => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={e => { e.preventDefault(); setDragOver(false); handleUpload(e.dataTransfer.files[0]) }}
        onClick={() => !uploading && inputRef.current?.click()}
        style={{
          borderRadius: '1.25rem', padding: '2.5rem',
          textAlign: 'center', cursor: uploading ? 'wait' : 'pointer',
          border: dragOver ? '2px dashed #6366f1' : '2px dashed rgba(99,102,241,0.25)',
          background: dragOver ? 'rgba(99,102,241,0.05)' : undefined,
          marginBottom: '1.5rem', transition: 'all 0.2s',
        }}
      >
        <input ref={inputRef} type="file" style={{ display: 'none' }} accept=".pdf,.docx,.txt,.md,.pptx,.csv" onChange={e => handleUpload(e.target.files[0])} />
        <div style={{ width: 52, height: 52, borderRadius: 16, background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1rem', boxShadow: '0 8px 24px rgba(99,102,241,0.3)' }}>
          {uploading ? (
            <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}>
              <Upload size={22} color="white" />
            </motion.div>
          ) : <Upload size={22} color="white" />}
        </div>
        <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#1e293b', marginBottom: 4 }}>
          {uploading ? 'Uploading & ingesting…' : 'Drag & drop or click to upload'}
        </div>
        <div style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
          Supported: PDF, DOCX, TXT, MD, PPTX, CSV
        </div>
      </div>

      {/* Documents table */}
      <div className="glass" style={{ borderRadius: '1.25rem', overflow: 'hidden' }}>
        <div style={{ padding: '1rem 1.25rem', borderBottom: '1px solid rgba(255,255,255,0.6)' }}>
          <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#1e293b' }}>Knowledge Base ({docs.length} documents)</span>
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid rgba(0,0,0,0.05)' }}>
              {['Document', 'Type', 'Uploaded', 'Chunks', ''].map(h => (
                <th key={h} style={{ padding: '0.6rem 1.1rem', textAlign: 'left', fontSize: '0.68rem', fontWeight: 700, color: '#94a3b8', letterSpacing: '0.06em', textTransform: 'uppercase' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {docs.length > 0 ? docs.map((doc, i) => (
              <motion.tr key={doc.doc_id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.04 }} style={{ borderBottom: '1px solid rgba(0,0,0,0.04)' }}>
                <td style={{ padding: '0.75rem 1.1rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{ width: 28, height: 28, borderRadius: 8, background: `${EXT_COLORS[doc.file_type] || '#94a3b8'}15`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <FileText size={13} color={EXT_COLORS[doc.file_type] || '#94a3b8'} />
                    </div>
                    <span style={{ fontSize: '0.84rem', fontWeight: 600, color: '#1e293b' }}>{doc.filename}</span>
                  </div>
                </td>
                <td style={{ padding: '0.75rem 1.1rem' }}>
                  <span style={{ fontSize: '0.7rem', fontWeight: 700, padding: '2px 9px', borderRadius: 99, background: `${EXT_COLORS[doc.file_type] || '#94a3b8'}18`, color: EXT_COLORS[doc.file_type] || '#94a3b8', textTransform: 'uppercase' }}>
                    {doc.file_type}
                  </span>
                </td>
                <td style={{ padding: '0.75rem 1.1rem', fontSize: '0.78rem', color: '#64748b' }}>
                  {doc.upload_date ? new Date(doc.upload_date).toLocaleDateString('en-IN') : '—'}
                </td>
                <td style={{ padding: '0.75rem 1.1rem', fontSize: '0.84rem', fontWeight: 700, color: '#6366f1' }}>
                  {doc.chunk_count}
                </td>
                <td style={{ padding: '0.75rem 1.1rem' }}>
                  <button
                    onClick={() => handleDelete(doc.filename)}
                    style={{ border: 'none', background: 'rgba(239,68,68,0.08)', color: '#ef4444', borderRadius: 7, padding: '5px 8px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4, fontSize: '0.75rem', fontWeight: 600, transition: 'all 0.15s' }}
                    onMouseEnter={e => e.currentTarget.style.background = 'rgba(239,68,68,0.15)'}
                    onMouseLeave={e => e.currentTarget.style.background = 'rgba(239,68,68,0.08)'}
                  >
                    <Trash2 size={13} /> Delete
                  </button>
                </td>
              </motion.tr>
            )) : (
              <tr><td colSpan={5} style={{ padding: '2.5rem', textAlign: 'center', color: '#cbd5e1', fontSize: '0.85rem' }}>No documents uploaded yet</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
