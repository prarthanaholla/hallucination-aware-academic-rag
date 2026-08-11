const QUICK = [
  { icon: '📘', text: 'What is the Python course about and how many credits?' },
  { icon: '🎯', text: 'What are the course outcomes for DBMS?' },
  { icon: '👩‍🏫', text: 'Which faculty work on deep learning?' },
  { icon: '📧', text: 'Who teaches machine learning and what is their email?' },
  { icon: '📅', text: 'When is ISA 1 for odd semester 2025?' },
  { icon: '🎉', text: 'What are all the holidays in Aug-Dec 2025?' },
  { icon: '🔬', text: 'What topics are covered in Unit 2 of the Python course?' },
  { icon: '💳', text: 'How many credits does the Operating Systems course have?' },
]

export default function Sidebar({ onQuickAsk }) {
  return (
    <aside className="w-60 shrink-0 border-r border-black/[0.08] bg-white flex flex-col overflow-y-auto">
      {/* Quick Questions */}
      <div className="p-4 border-b border-black/[0.06]">
        <p className="text-[10px] font-semibold text-[#b0ae a8] uppercase tracking-widest mb-3 text-[#aaa9a3]">
          Quick questions
        </p>
        <div className="flex flex-col gap-1">
          {QUICK.map((q, i) => (
            <button
              key={i}
              onClick={() => onQuickAsk(q.text)}
              className="w-full text-left text-xs text-[#6b6a66] px-2.5 py-2 rounded-lg hover:bg-[#f2f1ee] hover:text-[#1a1917] transition-colors flex gap-2 items-start leading-snug"
            >
              <span className="text-sm shrink-0 mt-px">{q.icon}</span>
              {q.text}
            </button>
          ))}
        </div>
      </div>

      {/* Stats */}
      <div className="p-4 border-b border-black/[0.06]">
        <p className="text-[10px] font-semibold uppercase tracking-widest mb-3 text-[#aaa9a3]">
          Knowledge base
        </p>
        <div className="grid grid-cols-2 gap-2">
          {[
            { n: '55',  l: 'Courses'   },
            { n: '60',  l: 'Faculty'   },
            { n: '43',  l: 'Cal. weeks'},
            { n: '517', l: 'Chunks'    },
          ].map(({ n, l }) => (
            <div key={l} className="bg-[#f8f7f4] rounded-lg p-2.5 text-center">
              <p className="text-lg font-semibold text-[#1a1917]">{n}</p>
              <p className="text-[10px] text-[#9b9790] mt-0.5">{l}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Legend */}
      <div className="p-4">
        <p className="text-[10px] font-semibold uppercase tracking-widest mb-3 text-[#aaa9a3]">
          Verification legend
        </p>
        {[
          { color: 'bg-emerald-100', label: 'Verified',      desc: 'Supported by evidence' },
          { color: 'bg-amber-100',   label: 'Partial',       desc: 'Weak or indirect evidence' },
          { color: 'bg-red-100',     label: 'Hallucinated',  desc: 'No evidence found' },
        ].map(({ color, label, desc }) => (
          <div key={label} className="flex items-start gap-2 mb-2.5 last:mb-0">
            <span className={`${color} w-3 h-3 rounded-sm shrink-0 mt-0.5`} />
            <div>
              <p className="text-xs font-medium text-[#1a1917]">{label}</p>
              <p className="text-[10px] text-[#9b9790]">{desc}</p>
            </div>
          </div>
        ))}
      </div>
    </aside>
  )
}
