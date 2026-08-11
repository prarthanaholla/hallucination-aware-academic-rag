const LABEL_COLOR = {
  VERIFIED:     { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200', icon: '✓' },
  PARTIAL:      { bg: 'bg-amber-50',   text: 'text-amber-700',   border: 'border-amber-200',   icon: '~' },
  HALLUCINATED: { bg: 'bg-red-50',     text: 'text-red-700',     border: 'border-red-200',     icon: '✗' },
}

export default function EvidencePanel({ sentences, focusIdx }) {
  return (
    <div className="border-t border-black/[0.06]">
      <div className="px-5 py-2 bg-[#f8f7f4] border-b border-black/[0.06]">
        <span className="text-[10px] font-semibold uppercase tracking-widest text-[#aaa9a3]">
          Sentence-level verification
        </span>
      </div>

      {sentences.map((s, i) => {
        const c = LABEL_COLOR[s.label] || LABEL_COLOR.PARTIAL
        const isFocused = i === focusIdx

        return (
          <div
            key={i}
            id={`ev-item-${i}`}
            className={`px-5 py-3.5 border-b border-black/[0.05] last:border-0 transition-colors ${
              isFocused ? 'bg-blue-50/40' : 'hover:bg-[#fafaf8]'
            }`}
          >
            <div className="flex gap-3 items-start">
              {/* Icon */}
              <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[11px] font-bold shrink-0 mt-0.5 ${c.bg} ${c.text}`}>
                {c.icon}
              </span>

              <div className="flex-1 min-w-0">
                {/* Sentence */}
                <p className="text-sm font-medium text-[#1a1917] mb-1.5">
                  {s.sentence}
                </p>

                {/* Evidence */}
                {s.evidence ? (
                  <div className={`text-xs font-mono text-[#6b6a66] bg-[#f2f1ee] rounded-lg px-3 py-2 mb-2 leading-relaxed border-l-2 ${c.border}`}>
                    "{s.evidence.slice(0, 260)}{s.evidence.length > 260 ? '...' : ''}"
                  </div>
                ) : (
                  <div className="text-xs italic text-[#c0beba] mb-2">
                    No supporting evidence found in knowledge base.
                  </div>
                )}

                {/* Meta row */}
                <div className="flex items-center gap-2 flex-wrap">
                  <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${c.bg} ${c.text}`}>
                    {s.label.charAt(0) + s.label.slice(1).toLowerCase()}
                  </span>
                  <span className={`text-[11px] font-semibold ${c.text}`}>
                    {Math.round(s.confidence * 100)}% confidence
                  </span>
                  {s.source?.course_code && (
                    <span className="text-[11px] font-mono text-[#aaa9a3]">
                      {s.source.course_code}
                    </span>
                  )}
                  {s.source?.name && (
                    <span className="text-[11px] font-mono text-[#aaa9a3]">
                      {s.source.name}
                    </span>
                  )}
                  {s.source?.session && (
                    <span className="text-[11px] font-mono text-[#aaa9a3]">
                      {s.source.session}
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
