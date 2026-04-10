import { useEffect, useRef } from 'react'

const LAST_ACTIVITY_KEY = 'mv_last_activity'
const INACTIVITY_LIMIT_MS = 30 * 24 * 60 * 60 * 1000 // 30 days
const THROTTLE_MS = 60 * 1000 // 1 minute

/**
 * Tracks user activity and calls onExpired() if the session has been
 * inactive for 30 days. Activity is written to localStorage throttled to
 * at most once per minute to avoid excessive writes.
 */
export function useSessionActivity(onExpired: () => void): void {
  const lastWriteRef = useRef<number>(0)
  const onExpiredRef = useRef(onExpired)

  // Keep ref current without causing re-effect
  onExpiredRef.current = onExpired

  useEffect(() => {
    // Check inactivity on mount
    const stored = localStorage.getItem(LAST_ACTIVITY_KEY)
    if (stored !== null) {
      const lastActivity = parseInt(stored, 10)
      if (!isNaN(lastActivity) && Date.now() - lastActivity > INACTIVITY_LIMIT_MS) {
        onExpiredRef.current()
        return
      }
    } else {
      // First visit — record activity now
      localStorage.setItem(LAST_ACTIVITY_KEY, Date.now().toString())
      lastWriteRef.current = Date.now()
    }

    function handleActivity() {
      const now = Date.now()
      if (now - lastWriteRef.current >= THROTTLE_MS) {
        localStorage.setItem(LAST_ACTIVITY_KEY, now.toString())
        lastWriteRef.current = now
      }
    }

    const events: Array<keyof WindowEventMap> = ['mousemove', 'keydown', 'click', 'touchstart']
    events.forEach((event) => window.addEventListener(event, handleActivity, { passive: true }))

    return () => {
      events.forEach((event) => window.removeEventListener(event, handleActivity))
    }
  }, [])
}
