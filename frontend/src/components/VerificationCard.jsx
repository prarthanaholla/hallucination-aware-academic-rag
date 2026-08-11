import { useState } from 'react'
import EvidencePanel from './EvidencePanel'
import TrustBadge   from './TrustBadge'

const SENTENCE_BG = {
  VERIFIED:     'bg-emerald-100',
  PARTIAL:      'bg-amber-100',
  HALLUCINATED: 'bg-red-100',
}

export default function VerificationCard({ data }) {
  const [showEvidence, setShowEvidence] = useState(false)
  const [focusIdx,     setFocusIdx]     = useState(null)

  const sa         = data.sentence_analysis    || []
  const summary    = data.verification_summary || {}
  const chunks     = data.retrieved_chunks     || []
  const meta       = data.meta                 || {}
  const answerType = data.answer_type          || 'prose'
  const isList     = answerType === 'list'

  const score = Math.round((summary.overall_score || 0) * 100)

  function handleSentenceClick(i) {
    setFocusIdx(i)
    setShowEvidence(true)
    setTimeout(() => {
      document.getElementById(`ev-item-${i}`)
        ?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }, 50)
  }

  // ── LIST ANSWER: render plain text + single verification badge ──
  if (isList && sa.length === 1) {
    const s     = sa[0]
    const label = s.label
    const conf  = Math.round(s.confidence * 100)

    return (
      <div className="bg-white border border-black/[0.08] rounded-2xl rounded-tl-sm overflow-hidden shadow-sm">
        {/* Answer text — plain, no highlighting */}
        <div className="px-5 py-4 text-sm text-[#1a1917] leading-7 whitespace-pre-wrap">
          {data.answer}
        </div>

        {/* Verification strip */}
        <div className="flex items-center gap-3 px-5 py-2.5 bg-[#f8f7f4] border-t border-black/[0.06] flex-wrap">
          <TrustBadge verdict={summary.verdict} score={score} />

          {/* Single label for whole answer */}
          <span className={`inline-flex items-center gap-1.5 text-[11px] font-medium px-2.5 py-1 rounded-full
            ${label === 'VERIFIED'     ? 'bg-emerald-50 text-emerald-700' :
              label === 'PARTIAL'      ? 'bg-amber-50 text-amber-700'     :
                                         'bg-red-50 text-red-700'}`}>
            <span className={`w-1.5 h-1.5 rounded-full
              ${label === 'VERIFIED' ? 'bg-emerald-500' : label === 'PARTIAL' ? 'bg-amber-500' : 'bg-red-500'}`}
            />
            Whole answer {label.toLowerCase()} · {conf}%
          </span>

          <div className="ml-auto flex items-center gap-3">
            {meta.elapsed_s && (
              <span className="text-[10px] text-[#c0beba] font-mono">{meta.elapsed_s}s</span>
            )}
            <button
              onClick={() => setShowEvidence(v => !v)}
              className="text-xs text-[#9b9790] hover:text-[#1a1917] underline underline-offset-2 transition-colors"
            >
              {showEvidence ? 'hide evidence' : 'show evidence'}
            </button>
          </div>
        </div>

        {/* Evidence panel */}
        {showEvidence && <EvidencePanel sentences={sa} focusIdx={focusIdx} />}

        {/* Source chips */}
        {chunks.length > 0 && (
          <div className="px-5 py-2.5 border-t border-black/[0.06] flex gap-2 flex-wrap">
            {chunks.slice(0, 5).map((c, i) => (
              <span key={i} className="text-[10px] font-mono bg-[#f2f1ee] text-[#9b9790] px-2.5 py-1 rounded-full">
                {c.source}/{c.type} · {Math.round((c.score || 0) * 100)}%
              </span>
            ))}
          </div>
        )}
      </div>
    )
  }

  // ── PROSE ANSWER: sentence-level highlighting (original behaviour) ──
  return (
    <div className="bg-white border border-black/[0.08] rounded-2xl rounded-tl-sm overflow-hidden shadow-sm">
      <div className="px-5 py-4 text-sm text-[#1a1917] leading-7">
        {sa.map((s, i) => (
          <span
            key={i}
            className={`sentence-span ${SENTENCE_BG[s.label] || ''} cursor-pointer`}
            title={`${s.label} · ${Math.round(s.confidence * 100)}% — click for evidence`}
            onClick={() => handleSentenceClick(i)}
          >
            {s.sentence}
          </span>
        )).reduce((acc, el, i) => [...acc, el, ' '], [])}
      </div>

      <div className="flex items-center gap-3 px-5 py-2.5 bg-[#f8f7f4] border-t border-black/[0.06] flex-wrap">
        <TrustBadge verdict={summary.verdict} score={score} />

        <div className="flex gap-2">
          {summary.verified_count > 0 && <Pill color="emerald" count={summary.verified_count} label="verified" />}
          {summary.partial_count  > 0 && <Pill color="amber"   count={summary.partial_count}  label="partial"  />}
          {summary.hallucinated_count > 0 && <Pill color="red" count={summary.hallucinated_count} label="hallucinated" />}
        </div>

        <div className="ml-auto flex items-center gap-3">
          {meta.elapsed_s && (
            <span className="text-[10px] text-[#c0beba] font-mono">{meta.elapsed_s}s</span>
          )}
          <button
            onClick={() => setShowEvidence(v => !v)}
            className="text-xs text-[#9b9790] hover:text-[#1a1917] underline underline-offset-2 transition-colors"
          >
            {showEvidence ? 'hide evidence' : 'show evidence'}
          </button>
        </div>
      </div>

      {showEvidence && <EvidencePanel sentences={sa} focusIdx={focusIdx} />}

      {chunks.length > 0 && (
        <div className="px-5 py-2.5 border-t border-black/[0.06] flex gap-2 flex-wrap">
          {chunks.slice(0, 5).map((c, i) => (
            <span key={i} className="text-[10px] font-mono bg-[#f2f1ee] text-[#9b9790] px-2.5 py-1 rounded-full">
              {c.source}/{c.type} · {Math.round((c.score || 0) * 100)}%
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

function Pill({ color, count, label }) {
  const styles = { emerald: 'bg-emerald-50 text-emerald-700', amber: 'bg-amber-50 text-amber-700', red: 'bg-red-50 text-red-700' }
  const dots   = { emerald: 'bg-emerald-500', amber: 'bg-amber-500', red: 'bg-red-500' }
  return (
    <span className={`inline-flex items-center gap-1 text-[11px] font-medium px-2.5 py-0.5 rounded-full ${styles[color]}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${dots[color]}`} />
      {count} {label}
    </span>
  )
}