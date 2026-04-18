import { useEffect } from 'react'
import { useAppStore } from '@/store/useAppStore'

export function useInitUser(): void {
  const initUser = useAppStore((s) => s.initUser)
  const userId = useAppStore((s) => s.userId)

  useEffect(() => {
    if (!userId) {
      void initUser()
    }
  }, [userId, initUser])
}
