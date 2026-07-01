import React, { createContext, useContext, useState, useCallback } from 'react'

interface NotifyContextType {
  lastEvent: any | null
  notify: (event: any) => void
}

const NotifyContext = createContext<NotifyContextType>({ lastEvent: null, notify: () => {} })

export const NotifyProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [lastEvent, setLastEvent] = useState<any>(null)
  const notify = useCallback((event: any) => setLastEvent(event), [])
  return <NotifyContext.Provider value={{ lastEvent, notify }}>{children}</NotifyContext.Provider>
}

export const useNotify = () => useContext(NotifyContext)
