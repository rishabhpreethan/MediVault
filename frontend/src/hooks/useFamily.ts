import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { api } from '../lib/api'
import type { FamilyMember } from '../types'

export function useFamilyMembers() {
  return useQuery<FamilyMember[]>({
    queryKey: ['family'],
    queryFn: async () => {
      const { data } = await api.get('/family')
      return data
    },
  })
}

// Simple module-level state for active member — replaced with proper store in MV-092
let _activeMemberId: string | null = null
const _listeners: Array<() => void> = []

export function useActiveMember(): string | null {
  const [, _forceUpdate] = useState(0)
  return _activeMemberId
}

export function useSetActiveMember() {
  return (memberId: string) => {
    _activeMemberId = memberId
    _listeners.forEach((l) => l())
  }
}
