/**
 * MemberSelector — top-right dropdown that lets the user switch between
 * "Me" and any family members linked to the account.
 *
 * Real family-member data arrives in MV-091. Until then, `useFamilyMembers`
 * returns an empty array and the selector is hidden (only "Me" exists).
 *
 * State is kept in a module-level store (same pattern as useFamily.ts) and
 * exposed via the `useSelectedMember()` hook so any component can read it.
 * A proper Zustand/Context store is planned for MV-092.
 */

import { useState, useEffect } from 'react'
import { useFamilyMembers } from '../../hooks/useFamily'
import type { FamilyMember } from '../../types'

// ---------------------------------------------------------------------------
// Module-level selected-member store
// ---------------------------------------------------------------------------

// null means "the authenticated user themselves" (no explicit family-member switch)
let _selectedMemberId: string | null = null
const _subscribers = new Set<() => void>()

function setSelectedMemberId(id: string | null): void {
  _selectedMemberId = id
  _subscribers.forEach((fn) => fn())
}

// ---------------------------------------------------------------------------
// useSelectedMember hook — public API
// ---------------------------------------------------------------------------

export interface SelectedMemberState {
  memberId: string | null
}

/**
 * Returns the currently selected member id.
 * `null` means the authenticated user (self) is selected.
 */
export function useSelectedMember(): SelectedMemberState {
  const [memberId, setMemberId] = useState<string | null>(_selectedMemberId)

  useEffect(() => {
    function onUpdate() {
      setMemberId(_selectedMemberId)
    }
    _subscribers.add(onUpdate)
    return () => {
      _subscribers.delete(onUpdate)
    }
  }, [])

  return { memberId }
}

// ---------------------------------------------------------------------------
// MemberSelector component
// ---------------------------------------------------------------------------

/** Synthetic option representing the authenticated user themselves. */
const SELF_VALUE = '__self__'

export function MemberSelector() {
  const { data: familyMembers = [] } = useFamilyMembers()
  const { memberId: selectedMemberId } = useSelectedMember()

  // Find the self member record if the API already returned it
  const selfMember: FamilyMember | undefined = familyMembers.find((m) => m.is_self)

  // Build option list: "Me" always first, then non-self family members
  const otherMembers: FamilyMember[] = familyMembers.filter((m) => !m.is_self)

  function handleChange(e: React.ChangeEvent<HTMLSelectElement>): void {
    const value = e.target.value
    setSelectedMemberId(value === SELF_VALUE ? null : value)
  }

  const currentValue = selectedMemberId ?? SELF_VALUE

  return (
    <select
      className="text-sm border border-gray-300 rounded-lg px-3 py-1.5 bg-white min-h-[44px] focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
      value={currentValue}
      onChange={handleChange}
      aria-label="Select family member"
    >
      <option value={SELF_VALUE}>
        {selfMember ? `${selfMember.full_name} (Me)` : 'Me'}
      </option>
      {otherMembers.map((m) => (
        <option key={m.member_id} value={m.member_id}>
          {m.full_name}
        </option>
      ))}
    </select>
  )
}
