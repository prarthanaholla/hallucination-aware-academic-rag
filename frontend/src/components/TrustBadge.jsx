export default function TrustBadge({ verdict, score }) {
  const map = {
    TRUSTWORTHY: { bg: 'bg-emerald-50', text: 'text-emerald-700', ring: 'ring-emerald-200', label: 'Trustworthy' },
    MIXED:       { bg: 'bg-amber-50',   text: 'text-amber-700',   ring: 'ring-amber-200',   label: 'Mixed'       },
    UNRELIABLE:  { bg: 'bg-red-50',     text: 'text-red-700',     ring: 'ring-red-200',     label: 'Unreliable'  },
  }
  const s = map[verdict] || map.MIXED

  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full ring-1 ${s.bg} ${s.text} ${s.ring}`}>
      <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
      </svg>
      <span className="text-xs font-semibold">{s.label}</span>
      <span className="text-xs font-mono opacity-70">{score}%</span>
    </div>
  )
}
