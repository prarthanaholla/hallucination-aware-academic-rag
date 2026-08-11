import { useState, useRef, useEffect } from 'react'
import MessageBubble from './MessageBubble'
import { askQuestion } from '../api/chat'

const STEPS = ['Retrieving chunks...', 'Generating answer...', 'Verifying sentences...']

export default function ChatWindow({ messages, setMessages, loading, setLoading, onVerdict }) {
  const [input,    setInput]    = useState('')
  const [step,     setStep]     = useState(0)
  const bottomRef               = useRef(null)
  const inputRef                = useRef(null)
  const stepTimer               = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // expose input element so sidebar quick-ask can set value
  useEffect(() => {
    const el = document.getElementById('chat-input')
    if (el) {
      el.addEventListener('input', (e) => setInput(e.target.value))
    }
  }, [])

  function startStepCycle() {
    setStep(0)
    let i = 0
    stepTimer.current = setInterval(() => {
      i = (i + 1) % STEPS.length
      setStep(i)
    }, 1400)
  }

  function stopStepCycle() {
    if (stepTimer.current) clearInterval(stepTimer.current)
  }

  async function send() {
    const q = input.trim()
    if (!q || loading) return

    setInput('')
    setMessages(prev => [...prev, { role: 'user', text: q }])
    setLoading(true)
    startStepCycle()

    try {
      const data = await askQuestion(q)
      setMessages(prev => [...prev, { role: 'bot', data }])
      onVerdict(data.verification_summary?.verdict)
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'error',
        text: err.response?.data?.detail || 'Server error. Is the backend running?'
      }])
    } finally {
      stopStepCycle()
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
  }

  return (
    <div className="flex-1 flex flex-col min-w-0 min-h-0">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6 flex flex-col gap-5">
        {messages.length === 0 && (
          <div className="flex-1 flex flex-col items-center justify-center text-center py-20">
            <div className="w-14 h-14 bg-white border border-black/[0.08] rounded-2xl flex items-center justify-center text-2xl mb-4 shadow-sm">
              🎓
            </div>
            <p className="text-base font-medium text-[#6b6a66]">Ask anything about PESU CSE</p>
            <p className="text-sm text-[#aaa9a3] mt-1 max-w-xs">
              Courses, faculty, exam dates, holidays — every answer is verified sentence by sentence.
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <MessageBubble key={i} msg={msg} />
        ))}

        {loading && (
          <div className="flex items-center gap-3 bg-white border border-black/[0.08] rounded-2xl rounded-tl-sm px-4 py-3 self-start max-w-xs shadow-sm">
            <div className="flex gap-1">
              {[0,1,2].map(j => (
                <span key={j} className="w-1.5 h-1.5 bg-[#c0beba] rounded-full animate-bounce"
                  style={{ animationDelay: `${j * 0.15}s` }} />
              ))}
            </div>
            <span className="text-xs text-[#9b9790]">{STEPS[step]}</span>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="shrink-0 p-4 border-t border-black/[0.06] bg-white">
        <div className="flex gap-3 items-end bg-[#f8f7f4] border border-black/[0.08] rounded-xl px-4 py-3 focus-within:border-black/20 transition-colors">
          <textarea
            id="chat-input"
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Ask about courses, faculty, exam dates..."
            rows={1}
            className="flex-1 bg-transparent text-sm text-[#1a1917] placeholder:text-[#c0beba] resize-none outline-none leading-relaxed max-h-32"
            style={{ height: 'auto' }}
            onInput={e => {
              e.target.style.height = 'auto'
              e.target.style.height = Math.min(e.target.scrollHeight, 128) + 'px'
            }}
          />
          <button
            onClick={send}
            disabled={!input.trim() || loading}
            className="shrink-0 bg-[#1a1917] text-white text-xs font-medium px-4 py-2 rounded-lg hover:bg-[#2c2b28] disabled:opacity-30 disabled:cursor-not-allowed transition-all flex items-center gap-1.5"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
            </svg>
            Ask
          </button>
        </div>
        <p className="text-[10px] text-[#c0beba] mt-2 text-center">
          Enter to send · Shift+Enter for new line
        </p>
      </div>
    </div>
  )
}
