import React from 'react'

type Props = {
  connected: boolean
}

export default function StatusBadge({ connected }: Props) {
  const bg = connected ? 'bg-emerald-100 text-emerald-800 border-emerald-200' : 'bg-rose-100 text-rose-800 border-rose-200'
  const dotColor = connected ? 'bg-emerald-500' : 'bg-rose-500'
  const label = connected ? 'Connected' : 'Disconnected'
  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 text-xs font-medium rounded-full border ${bg}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full mr-1.5 ${dotColor}`} />
      {label}
    </span>
  )
}
