import { useCallback, useState } from 'react'

export type Status = 0 | 1 | 2
export type Progress = Record<string, Status>

export const STATUS_LABELS = ['未开始', '学习中', '已掌握'] as const

// Same key as seed/reference.html so progress saved there carries over.
const STORAGE_KEY = 'agent-infra-progress'

function readProgress(): Progress {
  try {
    const parsed: unknown = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}')
    return parsed && typeof parsed === 'object' && !Array.isArray(parsed) ? (parsed as Progress) : {}
  } catch {
    return {}
  }
}

export function useProgress() {
  const [progress, setProgress] = useState<Progress>(readProgress)
  const setStatus = useCallback((slug: string, status: Status) => {
    setProgress((prev) => {
      const next = { ...prev, [slug]: status }
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
      } catch {
        // storage can be unavailable (private mode); progress then lives for this session only
      }
      return next
    })
  }, [])
  return [progress, setStatus] as const
}
