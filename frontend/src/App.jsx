import { useState, useEffect } from 'react'
import Sidebar       from './components/Sidebar'
import ChatWindow    from './components/ChatWindow'
import { getHealth } from './api/chat'

export default function App() {
  const [messages,     setMessages]     = useState([])
  const [loading,      setLoading]      = useState(false)
  const [systemStatus, setSystemStatus] = useState(null)
  const [lastVerdict,  setLastVerdict]  = useState(null)

  useEffect(() => {
    getHealth()
      .then(d => setSystemStatus(d))
      .catch(() => setSystemStatus({ status: 'error' }))
  }, [])

  return (
    <div className="flex flex-col h-screen bg-[#f8f7f4]">
      {/* Header */}
      <header className="bg-white border-b border-black/[0.08] px-6 h-14 flex items-center justify-between shrink-0 z-10">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-[#1a1917] rounded-lg flex items-center justify-center">
            <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
          </div>
          <div>
            <p className="text-sm font-semibold text-[#1a1917]">PESU CSE Assistant</p>
            <p className="text-xs text-[#9b9790]">Hallucination-Aware RAG</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {systemStatus && (
            <div className="flex items-center gap-1.5">
              <span className={`w-2 h-2 rounded-full ${systemStatus.status === 'ok' ? 'bg-emerald-500 animate-pulse' : 'bg-red-400'}`} />
              <span className="text-xs text-[#9b9790]">
                {systemStatus.status === 'ok'
                  ? `${systemStatus.chunks_indexed} chunks indexed`
                  : 'offline'}
              </span>
            </div>
          )}
          {lastVerdict && <VerdictBadge verdict={lastVerdict} />}
        </div>
      </header>

      {/* Body */}
      <div className="flex flex-1 min-h-0">
        <Sidebar onQuickAsk={(q) => {
          document.getElementById('chat-input')?.focus()
          document.getElementById('chat-input').value = q
          document.getElementById('chat-input').dispatchEvent(new Event('input', { bubbles: true }))
        }} />
        <ChatWindow
          messages={messages}
          setMessages={setMessages}
          loading={loading}
          setLoading={setLoading}
          onVerdict={setLastVerdict}
        />
      </div>
    </div>
  )
}

function VerdictBadge({ verdict }) {
  const map = {
    TRUSTWORTHY: 'bg-emerald-50 text-emerald-700',
    MIXED:       'bg-amber-50   text-amber-700',
    UNRELIABLE:  'bg-red-50     text-red-700',
  }
  return (
    <span className={`text-xs font-medium px-3 py-1 rounded-full ${map[verdict] || map.MIXED}`}>
      {verdict === 'TRUSTWORTHY' ? 'Trustworthy' : verdict === 'MIXED' ? 'Mixed' : 'Unreliable'}
    </span>
  )
}