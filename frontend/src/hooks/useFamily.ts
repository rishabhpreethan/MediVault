import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import type { FamilyMember } from '../types'

// ── Active member store ────────────────────────────────────────────────────
// Stored in sessionStorage so it survives in-app navigation but resets when
// the tab is closed. A custom DOM event keeps all hook instances in sync.

const STORAGE_KEY = 'mv_active_member_id'
const STORAGE_KEY_NAME = 'mv_active_member_name'
const CHANGE_EVENT = 'mv-member-change'

function readStorage(): string | null {
  return sessionStorage.getItem(STORAGE_KEY)
}

function writeStorage(id: string | null, name?: string) {
  if (id === null) {
    sessionStorage.removeItem(STORAGE_KEY)
    sessionStorage.removeItem(STORAGE_KEY_NAME)
  } else {
    sessionStorage.setItem(STORAGE_KEY, id)
    if (name) {
      sessionStorage.setItem(STORAGE_KEY_NAME, name)
    } else {
      sessionStorage.removeItem(STORAGE_KEY_NAME)
    }
  }
  window.dispatchEvent(new Event(CHANGE_EVENT))
}

/** Returns the explicitly-selected member ID, or null if none is selected. */
export function useActiveMember(): string | null {
  const [id, setId] = useState<string | null>(readStorage)

  useEffect(() => {
    const handler = () => setId(readStorage())
    window.addEventListener(CHANGE_EVENT, handler)
    return () => window.removeEventListener(CHANGE_EVENT, handler)
  }, [])

  return id
}

/** Returns a setter to switch the active member (pass null to reset to SELF). */
export function useSetActiveMember() {
  return (memberId: string | null, name?: string) => writeStorage(memberId, name)
}

/** Returns the display name stored alongside the active member (for cross-user vaults). */
export function useActiveMemberName(): string | null {
  const [name, setName] = useState<string | null>(() => sessionStorage.getItem(STORAGE_KEY_NAME))
  useEffect(() => {
    const handler = () => setName(sessionStorage.getItem(STORAGE_KEY_NAME))
    window.addEventListener(CHANGE_EVENT, handler)
    return () => window.removeEventListener(CHANGE_EVENT, handler)
  }, [])
  return name
}

// ── Family members query ───────────────────────────────────────────────────

export function useFamilyMembers() {
  return useQuery<FamilyMember[]>({
    queryKey: ['family-members'],
    queryFn: async () => {
      const { data } = await api.get('/family/members')
      return data
    },
  })
}

// ── Resolved member ID ─────────────────────────────────────────────────────

/**
 * Resolves the member ID to use for all API calls.
 * Priority: explicitly selected > SELF member > first member.
 * Returns undefined while members are still loading — gate queries with `enabled: !!memberId`.
 */
export function useResolvedMemberId(): string | undefined {
  const activeMemberId = useActiveMember()
  const { data: members } = useFamilyMembers()
  return (
    activeMemberId
    ?? members?.find((m) => m.relationship?.toUpperCase() === 'SELF')?.member_id
    ?? members?.[0]?.member_id
  )
}

/**
 * Returns the full FamilyMember object for the currently active member,
 * and whether they are the primary (SELF) account holder.
 */
export function useActiveMemberDetails(): {
  member: FamilyMember | undefined
  isSelf: boolean
} {
  const memberId = useResolvedMemberId()
  const { data: members } = useFamilyMembers()

  const member = members?.find((m) => m.member_id === memberId)
  const selfMember = members?.find((m) => m.relationship?.toUpperCase() === 'SELF')
  const isSelf = !memberId || memberId === selfMember?.member_id

  return { member, isSelf }
}
