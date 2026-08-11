import { useState } from 'react'
import VerificationCard from './VerificationCard'

export default function MessageBubble({ msg }) {
  if (msg.role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="bg-[#1a1917] text-white text-sm px-4 py-2.5 rounded-2xl rounded-tr-sm max-w-[70%] leading-relaxed">
          {msg.text}
        </div>
      </div>
    )
  }

  if (msg.role === 'error') {
    return (
      <div className="flex justify-start">
        <div className="bg-red-50 border border-red-100 text-red-700 text-sm px-4 py-2.5 rounded-2xl rounded-tl-sm max-w-[80%]">
          ⚠ {msg.text}
        </div>
      </div>
    )
  }

  // bot message with full verification data
  return (
    <div className="flex justify-start w-full">
      <div className="w-full max-w-3xl">
        <VerificationCard data={msg.data} />
      </div>
    </div>
  )
}
