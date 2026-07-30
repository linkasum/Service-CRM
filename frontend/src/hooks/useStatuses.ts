import { useState, useEffect } from 'react'
import { getOrderStatuses } from '../api'

export interface StatusItem {
  code: string
  name: string
  color: string
}

export function useStatuses() {
  const [statuses, setStatuses] = useState<StatusItem[]>([])
  const [labels, setLabels] = useState<Record<string, string>>({})

  useEffect(() => {
    getOrderStatuses().then((data: any[]) => {
      setStatuses(data)
      const map: Record<string, string> = {}
      data.forEach((s: any) => { if (s.code) map[s.code] = s.name })
      setLabels(map)
    }).catch(() => {})
  }, [])

  return { statuses, labels }
}
